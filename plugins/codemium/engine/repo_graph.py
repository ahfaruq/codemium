#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from common import IGNORE_DIRS, git, now_iso, read_json, sha256_bytes, state_root, write_json

GRAPH_SCHEMA_VERSION = 2
MANIFEST_SCHEMA_VERSION = 1
PARSER_VERSION = "2"
MAX_FILE_BYTES = 2_000_000

EXT_LANG = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".go": "go",
    ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".rb": "ruby", ".php": "php", ".cs": "csharp",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".vue": "vue", ".svelte": "svelte", ".sql": "sql",
}

SYMBOL_PATTERNS = [
    ("FUNCTION", re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.M)),
    ("CLASS", re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.M)),
    ("FUNCTION", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)),
    ("FUNCTION", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(", re.M)),
    ("FUNCTION", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)", re.M)),
    ("FUNCTION", re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)", re.M)),
    ("CLASS", re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_]\w*)", re.M)),
    ("CLASS", re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:class|interface|record)\s+([A-Za-z_]\w*)", re.M)),
]

IMPORT_PATTERNS = [
    re.compile(r"(?:from|import)\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
    re.compile(r"^\s*from\s+([\w.]+)\s+import", re.M),
    re.compile(r"^\s*import\s+([\w.]+)", re.M),
]

CALL_PATTERN = re.compile(r"(?<![\w$.])([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(")
EXTENDS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)\s+(extends|implements)\s+([A-Za-z_$][\w$]*)")
SKIP_CALL_NAMES = {
    "if", "for", "while", "switch", "catch", "return", "function", "def",
    "class", "typeof", "sizeof", "new",
}


def is_test(path: str) -> bool:
    s = "/" + path.lower().replace("\\", "/")
    name = Path(s).name
    return (
        any(x in s for x in ["/test/", "/tests/", "/__tests__/"])
        or name.startswith("test_")
        or any(x in name for x in [".test.", ".spec.", "_test."])
    )


def file_id(path: str) -> str:
    return f"file:{path}"


def module_id(path: str) -> str:
    return f"module:{path}"


def external_module_id(name: str) -> str:
    return f"module:external:{name}"


def symbol_id(path: str, qualified: str, kind: str) -> str:
    return f"symbol:{path}#{qualified}:{kind.lower()}"


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return None


class PythonExtractor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.stack: list[tuple[str, str]] = []
        self.symbols: list[dict] = []
        self.imports: list[dict] = []
        self.calls: list[dict] = []
        self.inherits: list[dict] = []
        self.references: list[dict] = []

    def _qualify(self, name: str) -> str:
        parents = [x[0] for x in self.stack]
        return ".".join([*parents, name]) if parents else name

    def _owner(self) -> str | None:
        if not self.stack:
            return None
        name, kind = self.stack[-1]
        return symbol_id(self.path, name, kind)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "imported": None,
                "alias": alias.asname,
                "line": getattr(node, "lineno", None),
                "provenance": "DIRECT",
            })

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = ("." * node.level) + (node.module or "")
        for alias in node.names:
            self.imports.append({
                "module": module,
                "imported": alias.name,
                "alias": alias.asname,
                "line": getattr(node, "lineno", None),
                "provenance": "DIRECT",
            })

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        q = self._qualify(node.name)
        item = {
            "name": node.name, "qualified_name": q, "kind": "CLASS",
            "line_start": getattr(node, "lineno", None),
            "line_end": getattr(node, "end_lineno", getattr(node, "lineno", None)),
        }
        self.symbols.append(item)
        for base in node.bases:
            name = dotted_name(base)
            if name:
                self.inherits.append({
                    "source": symbol_id(self.path, q, "CLASS"),
                    "target_name": name,
                    "relation": "INHERITS",
                    "line": getattr(node, "lineno", None),
                    "provenance": "DIRECT",
                })
        self.stack.append((q, "CLASS"))
        self.generic_visit(node)
        self.stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = "METHOD" if self.stack and self.stack[-1][1] == "CLASS" else "FUNCTION"
        q = self._qualify(node.name)
        self.symbols.append({
            "name": node.name, "qualified_name": q, "kind": kind,
            "line_start": getattr(node, "lineno", None),
            "line_end": getattr(node, "end_lineno", getattr(node, "lineno", None)),
        })
        self.stack.append((q, kind))
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func)
        if name:
            self.calls.append({
                "source": self._owner() or module_id(self.path),
                "target_name": name,
                "line": getattr(node, "lineno", None),
                "provenance": "DIRECT",
            })
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and self._owner():
            self.references.append({
                "source": self._owner(),
                "target_name": node.id,
                "line": getattr(node, "lineno", None),
                "provenance": "DIRECT",
            })


def parse_python(path: str, text: str) -> tuple[dict, str, list[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return parse_fallback(path, text, "python")
    ex = PythonExtractor(path)
    ex.visit(tree)
    return ({
        "symbols": ex.symbols,
        "imports": ex.imports,
        "calls": ex.calls,
        "inherits": ex.inherits,
        "references": ex.references,
    }, "python-ast", ["symbols", "imports", "calls", "references", "inherits"])


def parse_fallback(path: str, text: str, language: str) -> tuple[dict, str, list[str]]:
    symbols: list[dict] = []
    seen = set()
    for kind, pat in SYMBOL_PATTERNS:
        for m in pat.finditer(text):
            name = m.group(1)
            key = (name, kind)
            if key in seen:
                continue
            seen.add(key)
            line = text.count("\n", 0, m.start()) + 1
            symbols.append({
                "name": name, "qualified_name": name, "kind": kind,
                "line_start": line, "line_end": line,
            })
    imports: list[dict] = []
    for pat in IMPORT_PATTERNS:
        for m in pat.finditer(text):
            imports.append({
                "module": m.group(1), "imported": None, "alias": None,
                "line": text.count("\n", 0, m.start()) + 1,
                "provenance": "DIRECT",
            })
    calls: list[dict] = []
    for m in CALL_PATTERN.finditer(text):
        name = m.group(1)
        if name.lower() in SKIP_CALL_NAMES:
            continue
        calls.append({
            "source": module_id(path), "target_name": name,
            "line": text.count("\n", 0, m.start()) + 1,
            "provenance": "HEURISTIC",
        })
    inherits: list[dict] = []
    for m in EXTENDS_PATTERN.finditer(text):
        child, keyword, parent = m.groups()
        src = next((symbol_id(path, s["qualified_name"], s["kind"]) for s in symbols if s["name"] == child), module_id(path))
        inherits.append({
            "source": src, "target_name": parent, "relation": "IMPLEMENTS" if keyword == "implements" else "INHERITS",
            "line": text.count("\n", 0, m.start()) + 1,
            "provenance": "HEURISTIC",
        })
    return ({
        "symbols": symbols,
        "imports": imports,
        "calls": calls,
        "inherits": inherits,
        "references": [],
    }, "fallback-regex", ["symbols", "imports", "calls"])


def parse_source(path: str, language: str, text: str) -> tuple[dict, str, list[str]]:
    if language == "python":
        return parse_python(path, text)
    return parse_fallback(path, text, language)


def module_name_candidates(path: str) -> set[str]:
    p = Path(path)
    no_suffix = p.with_suffix("").as_posix()
    out = {no_suffix, no_suffix.replace("/", "."), p.stem}
    if p.name.startswith("__init__."):
        parent = p.parent.as_posix()
        out.add(parent)
        out.add(parent.replace("/", "."))
    if no_suffix.startswith("src/"):
        s = no_suffix[4:]
        out.add(s)
        out.add(s.replace("/", "."))
    return {x.strip(".") for x in out if x}


def discover_files(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        relp = p.relative_to(root)
        if any(part in IGNORE_DIRS for part in relp.parts):
            continue
        language = EXT_LANG.get(p.suffix.lower())
        if not language:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if len(data) > MAX_FILE_BYTES or b"\x00" in data:
            continue
        out[relp.as_posix()] = {
            "path": relp.as_posix(), "language": language,
            "bytes": len(data), "sha256": sha256_bytes(data), "data": data,
        }
    return out


def old_file_cache(old_graph: dict) -> dict[str, dict]:
    return {f["path"]: f for f in old_graph.get("files", []) if isinstance(f, dict) and f.get("path")}


def extract_files(root: Path, discovered: dict[str, dict], old_graph: dict, old_manifest: dict) -> tuple[list[dict], dict]:
    old_files = old_file_cache(old_graph)
    old_meta = old_manifest.get("files", {}) if isinstance(old_manifest.get("files"), dict) else {}
    files: list[dict] = []
    stats = {"new": 0, "modified": 0, "unchanged": 0, "deleted": 0, "parsed": 0}
    old_paths = set(old_files)
    current_paths = set(discovered)
    stats["deleted"] = len(old_paths - current_paths)

    for path in sorted(current_paths):
        item = discovered[path]
        old = old_files.get(path)
        meta = old_meta.get(path, {}) if isinstance(old_meta.get(path, {}), dict) else {}
        reusable = (
            old and meta.get("sha256") == item["sha256"]
            and meta.get("parser_version") == PARSER_VERSION
            and old_graph.get("schema_version") == GRAPH_SCHEMA_VERSION
            and isinstance(old.get("facts"), dict)
        )
        if reusable:
            rec = dict(old)
            rec["bytes"] = item["bytes"]
            rec["sha256"] = item["sha256"]
            files.append(rec)
            stats["unchanged"] += 1
            continue

        text = item["data"].decode("utf-8", errors="ignore")
        facts, parser, capabilities = parse_source(path, item["language"], text)
        rec = {
            "path": path, "language": item["language"], "bytes": item["bytes"],
            "sha256": item["sha256"], "sha256_short": item["sha256"][:20],
            "symbols": sorted({x["name"] for x in facts["symbols"]})[:250],
            "imports": sorted({x["module"] for x in facts["imports"] if x.get("module")})[:250],
            "is_test": is_test(path), "parser": parser, "parser_version": PARSER_VERSION,
            "capabilities": capabilities, "facts": facts,
        }
        files.append(rec)
        stats["parsed"] += 1
        if old:
            stats["modified"] += 1
        else:
            stats["new"] += 1
    return files, stats


def add_edge(edges: list[dict], seen: set[tuple], source: str, target: str, relation: str,
             provenance: str, source_file: str | None = None, line: int | None = None,
             evidence: str | None = None) -> None:
    key = (source, target, relation, source_file, line)
    if source == target or key in seen:
        return
    seen.add(key)
    edge = {"source": source, "target": target, "relation": relation, "provenance": provenance}
    if source_file:
        edge["source_file"] = source_file
    if line:
        edge["line"] = line
    if evidence:
        edge["evidence"] = evidence
    edges.append(edge)


def build_graph(files: list[dict], head: str | None, stats: dict) -> dict:
    nodes: list[dict] = []
    node_by_id: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[tuple] = set()
    symbols_by_simple: defaultdict[str, list[str]] = defaultdict(list)
    symbols_by_qualified: defaultdict[str, list[str]] = defaultdict(list)
    modules_by_name: defaultdict[str, list[str]] = defaultdict(list)

    def add_node(node: dict) -> None:
        if node["id"] not in node_by_id:
            node_by_id[node["id"]] = node
            nodes.append(node)

    for f in files:
        path = f["path"]
        fid = file_id(path)
        mid = module_id(path)
        add_node({
            "id": fid, "type": "TEST" if f["is_test"] else "FILE",
            "label": Path(path).name, "path": path, "language": f["language"],
            "content_hash": f["sha256"], "parser": f["parser"], "capabilities": f["capabilities"],
        })
        add_node({"id": mid, "type": "MODULE", "label": Path(path).stem, "path": path, "language": f["language"], "external": False})
        add_edge(edges, seen_edges, fid, mid, "CONTAINS", "DIRECT", path)
        for name in module_name_candidates(path):
            modules_by_name[name].append(mid)
        for sym in f["facts"].get("symbols", []):
            sid = symbol_id(path, sym["qualified_name"], sym["kind"])
            add_node({
                "id": sid, "type": "SYMBOL", "subtype": sym["kind"], "label": sym["name"],
                "qualified_name": sym["qualified_name"], "path": path,
                "line_start": sym.get("line_start"), "line_end": sym.get("line_end"),
                "content_hash": f["sha256"],
            })
            symbols_by_simple[sym["name"]].append(sid)
            symbols_by_qualified[sym["qualified_name"]].append(sid)
            add_edge(edges, seen_edges, mid, sid, "DEFINES", "DIRECT", path, sym.get("line_start"))

    for f in files:
        path = f["path"]
        mid = module_id(path)
        for imp in f["facts"].get("imports", []):
            name = (imp.get("module") or "").lstrip(".")
            candidates = modules_by_name.get(name, [])
            if not candidates and "." in name:
                candidates = modules_by_name.get(name.replace(".", "/"), [])
            if candidates:
                for target in candidates:
                    add_edge(edges, seen_edges, mid, target, "IMPORTS", "RESOLVED", path, imp.get("line"), name)
            elif name:
                eid = external_module_id(name)
                add_node({"id": eid, "type": "MODULE", "label": name, "external": True})
                add_edge(edges, seen_edges, mid, eid, "IMPORTS", "DIRECT", path, imp.get("line"), name)

    def resolve_symbol(name: str, current_path: str) -> tuple[str | None, str]:
        simple = name.split(".")[-1]
        same = [sid for sid in symbols_by_simple.get(simple, []) if node_by_id[sid].get("path") == current_path]
        if len(same) == 1:
            return same[0], "RESOLVED"
        exact_q = symbols_by_qualified.get(name, [])
        if len(exact_q) == 1:
            return exact_q[0], "RESOLVED"
        all_simple = symbols_by_simple.get(simple, [])
        if len(all_simple) == 1:
            return all_simple[0], "RESOLVED"
        return None, "HEURISTIC"

    unresolved = 0
    for f in files:
        path = f["path"]
        is_test_file = f["is_test"]
        for call in f["facts"].get("calls", []):
            target, resolution = resolve_symbol(call["target_name"], path)
            if target:
                provenance = "DIRECT" if call.get("provenance") == "DIRECT" and node_by_id[target].get("path") == path else resolution
                add_edge(edges, seen_edges, call["source"], target, "CALLS", provenance, path, call.get("line"), call["target_name"])
                if is_test_file and node_by_id[target].get("path") != path:
                    add_edge(edges, seen_edges, file_id(path), target, "TESTS", provenance, path, call.get("line"), call["target_name"])
            else:
                unresolved += 1
        for ref in f["facts"].get("references", []):
            target, resolution = resolve_symbol(ref["target_name"], path)
            if target:
                add_edge(edges, seen_edges, ref["source"], target, "REFERENCES", resolution, path, ref.get("line"), ref["target_name"])
                if is_test_file and node_by_id[target].get("path") != path:
                    add_edge(edges, seen_edges, file_id(path), target, "TESTS", resolution, path, ref.get("line"), ref["target_name"])
        for inh in f["facts"].get("inherits", []):
            target, resolution = resolve_symbol(inh["target_name"], path)
            if target:
                add_edge(edges, seen_edges, inh["source"], target, inh.get("relation", "INHERITS"), resolution, path, inh.get("line"), inh["target_name"])
            else:
                unresolved += 1

    dependency_pairs: dict[tuple[str, str], str] = {}
    provenance_rank = {"DIRECT": 3, "RESOLVED": 2, "HEURISTIC": 1}
    for edge in list(edges):
        src_node = node_by_id.get(edge["source"])
        dst_node = node_by_id.get(edge["target"])
        if not src_node or not dst_node:
            continue
        sp, tp = src_node.get("path"), dst_node.get("path")
        if not sp or not tp or sp == tp:
            continue
        if edge["relation"] not in {"CALLS", "REFERENCES", "IMPORTS", "INHERITS", "IMPLEMENTS"}:
            continue
        key = (file_id(sp), file_id(tp))
        current = dependency_pairs.get(key)
        prov = edge["provenance"]
        if not current or provenance_rank.get(prov, 0) > provenance_rank.get(current, 0):
            dependency_pairs[key] = prov
    for (src, dst), prov in dependency_pairs.items():
        add_edge(edges, seen_edges, src, dst, "DEPENDS_ON", prov)

    provenance_counts = Counter(e["provenance"] for e in edges)
    relation_counts = Counter(e["relation"] for e in edges)
    parser_counts = Counter(f["parser"] for f in files)
    coverage = {
        "files": len(files), "python_ast_files": parser_counts.get("python-ast", 0),
        "fallback_files": parser_counts.get("fallback-regex", 0),
        "parser_counts": dict(sorted(parser_counts.items())),
    }
    return {
        "schema_version": GRAPH_SCHEMA_VERSION, "generated_at": now_iso(), "git_head": head,
        "parser_version": PARSER_VERSION, "file_count": len(files), "node_count": len(nodes),
        "edge_count": len(edges), "files": files, "nodes": nodes, "edges": edges,
        "coverage": coverage, "provenance_counts": dict(sorted(provenance_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "unresolved_relationships": unresolved, "incremental": stats,
    }


def manifest_for(files: list[dict], head: str | None) -> dict:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION, "graph_schema_version": GRAPH_SCHEMA_VERSION,
        "parser_version": PARSER_VERSION, "generated_at": now_iso(), "git_head": head,
        "files": {
            f["path"]: {"sha256": f["sha256"], "parser": f["parser"], "parser_version": f["parser_version"]}
            for f in files
        },
    }


def scan(root: Path) -> dict:
    s = state_root(root)
    old_graph = read_json(s / "repository/graph.json", {})
    old_manifest = read_json(s / "repository/manifest.json", {})
    discovered = discover_files(root)
    files, stats = extract_files(root, discovered, old_graph, old_manifest)
    head = git(root, "rev-parse", "HEAD")
    graph = build_graph(files, head, stats)
    write_json(s / "repository/graph.json", graph)
    write_json(s / "repository/manifest.json", manifest_for(files, head))
    return graph


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", default=".")
    b.add_argument("--output")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    graph = scan(root)
    if ns.output:
        write_json(Path(ns.output), graph)
    print(json.dumps({
        "output": str(Path(ns.output) if ns.output else state_root(root) / "repository/graph.json"),
        "schema_version": graph["schema_version"], "file_count": graph["file_count"],
        "node_count": graph["node_count"], "edge_count": graph["edge_count"],
        "git_head": graph["git_head"], "incremental": graph["incremental"], "coverage": graph["coverage"],
    }, indent=2))


if __name__ == "__main__":
    main()
