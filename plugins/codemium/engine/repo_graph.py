#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import posixpath
import re
from collections import Counter, defaultdict
from pathlib import Path

from common import IGNORE_DIRS, git, now_iso, read_json, sha256_bytes, state_root, write_json
from parsers import PARSER_VERSION, parse_source, parser_runtime

GRAPH_SCHEMA_VERSION = 3
MANIFEST_SCHEMA_VERSION = 2
MAX_FILE_BYTES = 2_000_000

EXT_LANG = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".go": "go",
    ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".rb": "ruby", ".php": "php", ".cs": "csharp",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".vue": "vue", ".svelte": "svelte", ".sql": "sql",
}
SOURCE_EXT_RE = re.compile(r"\.(?:[cm]?[jt]sx?|py)$", re.I)
PROVENANCE_RANK = {"DIRECT": 3, "RESOLVED": 2, "HEURISTIC": 1}
DEPENDENCY_RELATIONS = {"CALLS", "REFERENCES", "IMPORTS", "IMPORTS_SYMBOL", "INHERITS", "IMPLEMENTS"}


def is_test(path: str) -> bool:
    s = "/" + path.lower().replace("\\", "/")
    name = Path(s).name
    return (
        any(x in s for x in ["/test/", "/tests/", "/__tests__/"])
        or name.startswith("test_")
        or any(x in name for x in [".test.", ".spec.", "_test."])
    )


def file_id(path: str) -> str: return f"file:{path}"
def module_id(path: str) -> str: return f"module:{path}"
def external_module_id(name: str) -> str: return f"module:external:{name}"
def symbol_id(path: str, qualified: str, kind: str) -> str: return f"symbol:{path}#{qualified}:{kind.lower()}"


def module_name_candidates(path: str) -> set[str]:
    p = Path(path)
    no_suffix = p.with_suffix("").as_posix()
    # foo.d.ts should also be addressable as foo.
    if no_suffix.endswith(".d"):
        no_suffix = no_suffix[:-2]
    out = {no_suffix, no_suffix.replace("/", "."), p.stem}
    if p.stem == "index" or p.name.startswith("__init__."):
        parent = p.parent.as_posix()
        out.update({parent, parent.replace("/", "."), Path(parent).name})
    if no_suffix.startswith("src/"):
        s = no_suffix[4:]
        out.update({s, s.replace("/", ".")})
        if s.endswith("/index"):
            parent = s[:-6].rstrip("/")
            out.update({parent, parent.replace("/", ".")})
    return {x.strip(".") for x in out if x and x != "."}


def import_name_candidates(importer: str, raw_name: str) -> list[str]:
    name = (raw_name or "").strip()
    if not name:
        return []
    variants: list[str] = []
    if name.startswith("."):
        # Python relative imports use leading dots as package levels; JS/TS use ./ and ../ paths.
        if name.startswith("./") or name.startswith("../"):
            joined = posixpath.normpath(posixpath.join(posixpath.dirname(importer), name))
        else:
            level = len(name) - len(name.lstrip("."))
            rest = name[level:].replace(".", "/")
            base = posixpath.dirname(importer)
            for _ in range(max(0, level - 1)):
                base = posixpath.dirname(base)
            joined = posixpath.normpath(posixpath.join(base, rest))
        joined = SOURCE_EXT_RE.sub("", joined)
        variants.extend([joined, joined + "/index", joined.replace("/", ".")])
    else:
        plain = SOURCE_EXT_RE.sub("", name)
        variants.extend([plain, plain.replace(".", "/"), plain.replace("/", ".")])
        if not plain.startswith("src/"):
            variants.extend(["src/" + plain.replace(".", "/"), "src." + plain.replace("/", ".")])
    seen = set()
    return [x for x in variants if x and not (x in seen or seen.add(x))]


def discover_files(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in root.rglob("*"):
        if not p.is_file(): continue
        relp = p.relative_to(root)
        if any(part in IGNORE_DIRS for part in relp.parts): continue
        language = EXT_LANG.get(p.suffix.lower())
        if not language: continue
        try: data = p.read_bytes()
        except OSError: continue
        if len(data) > MAX_FILE_BYTES or b"\x00" in data: continue
        out[relp.as_posix()] = {"path": relp.as_posix(), "language": language, "bytes": len(data), "sha256": sha256_bytes(data), "data": data}
    return out


def old_file_cache(old_graph: dict) -> dict[str, dict]:
    return {f["path"]: f for f in old_graph.get("files", []) if isinstance(f, dict) and f.get("path")}


def extract_files(root: Path, discovered: dict[str, dict], old_graph: dict, old_manifest: dict) -> tuple[list[dict], dict]:
    old_files = old_file_cache(old_graph)
    old_meta = old_manifest.get("files", {}) if isinstance(old_manifest.get("files"), dict) else {}
    files: list[dict] = []
    stats = {"new": 0, "modified": 0, "unchanged": 0, "deleted": 0, "parsed": 0}
    old_paths, current_paths = set(old_files), set(discovered)
    stats["deleted"] = len(old_paths - current_paths)

    for path in sorted(current_paths):
        item = discovered[path]; old = old_files.get(path)
        meta = old_meta.get(path, {}) if isinstance(old_meta.get(path, {}), dict) else {}
        reusable = (
            old and meta.get("sha256") == item["sha256"]
            and meta.get("parser_version") == PARSER_VERSION
            and old_graph.get("schema_version") == GRAPH_SCHEMA_VERSION
            and isinstance(old.get("facts"), dict)
        )
        if reusable:
            rec = dict(old); rec["bytes"] = item["bytes"]; rec["sha256"] = item["sha256"]
            files.append(rec); stats["unchanged"] += 1; continue

        text = item["data"].decode("utf-8", errors="ignore")
        result = parse_source(path, item["language"], text)
        facts = result.facts
        rec = {
            "path": path, "language": item["language"], "bytes": item["bytes"],
            "sha256": item["sha256"], "sha256_short": item["sha256"][:20],
            "symbols": sorted({x["name"] for x in facts.get("symbols", [])})[:250],
            "imports": sorted({x["module"] for x in facts.get("imports", []) if x.get("module")})[:250],
            "is_test": is_test(path), "parser": result.parser, "parser_version": PARSER_VERSION,
            "capabilities": result.capabilities, "parser_metadata": result.metadata, "facts": facts,
        }
        files.append(rec); stats["parsed"] += 1
        stats["modified" if old else "new"] += 1
    return files, stats


def add_edge(edges: list[dict], seen: set[tuple], source: str, target: str, relation: str,
             provenance: str, source_file: str | None = None, line: int | None = None,
             evidence: str | None = None, **extra) -> None:
    key = (source, target, relation, source_file, line)
    if source == target or key in seen: return
    seen.add(key)
    edge = {"source": source, "target": target, "relation": relation, "provenance": provenance}
    if source_file: edge["source_file"] = source_file
    if line: edge["line"] = line
    if evidence: edge["evidence"] = evidence
    edge.update({k: v for k, v in extra.items() if v is not None})
    edges.append(edge)


def build_graph(files: list[dict], head: str | None, stats: dict) -> dict:
    nodes: list[dict] = []; node_by_id: dict[str, dict] = {}; edges: list[dict] = []; seen_edges: set[tuple] = set()
    symbols_by_simple: defaultdict[str, list[str]] = defaultdict(list)
    symbols_by_qualified: defaultdict[str, list[str]] = defaultdict(list)
    symbols_by_path_simple: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    modules_by_name: defaultdict[str, list[str]] = defaultdict(list)
    top_symbols_by_path: defaultdict[str, list[str]] = defaultdict(list)

    def add_node(node: dict) -> None:
        if node["id"] not in node_by_id:
            node_by_id[node["id"]] = node; nodes.append(node)

    for f in files:
        path = f["path"]; fid = file_id(path); mid = module_id(path)
        add_node({"id": fid, "type": "TEST" if f["is_test"] else "FILE", "label": Path(path).name, "path": path, "language": f["language"], "content_hash": f["sha256"], "parser": f["parser"], "capabilities": f["capabilities"]})
        add_node({"id": mid, "type": "MODULE", "label": Path(path).stem, "path": path, "language": f["language"], "external": False})
        add_edge(edges, seen_edges, fid, mid, "CONTAINS", "DIRECT", path)
        for name in module_name_candidates(path): modules_by_name[name].append(mid)
        for sym in f["facts"].get("symbols", []):
            sid = symbol_id(path, sym["qualified_name"], sym["kind"])
            add_node({"id": sid, "type": "SYMBOL", "subtype": sym["kind"], "label": sym["name"], "qualified_name": sym["qualified_name"], "path": path, "language": f["language"], "line_start": sym.get("line_start"), "line_end": sym.get("line_end"), "content_hash": f["sha256"]})
            symbols_by_simple[sym["name"]].append(sid); symbols_by_qualified[sym["qualified_name"]].append(sid); symbols_by_path_simple[(path, sym["name"])].append(sid)
            if "." not in sym["qualified_name"]: top_symbols_by_path[path].append(sid)
            add_edge(edges, seen_edges, mid, sid, "DEFINES", "DIRECT", path, sym.get("line_start"))

    def module_targets(importer: str, name: str) -> list[str]:
        found: list[str] = []
        for candidate in import_name_candidates(importer, name):
            for target in modules_by_name.get(candidate, []):
                if target not in found: found.append(target)
        return found

    # export name -> symbol id, per module. Local symbol names are enough for deterministic ESM resolution.
    exports_by_module: defaultdict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for f in files:
        path = f["path"]; mid = module_id(path)
        for exp in f["facts"].get("exports", []):
            local, exported = exp.get("local"), exp.get("exported")
            if local and exported:
                for sid in symbols_by_path_simple.get((path, local), []): exports_by_module[mid][exported].append(sid)
        for sid in top_symbols_by_path.get(path, []):
            label = node_by_id[sid].get("label")
            if label and sid not in exports_by_module[mid][label]: exports_by_module[mid][label].append(sid)

    bindings_by_path: defaultdict[str, dict[str, dict]] = defaultdict(dict)
    unresolved_imports = 0
    for f in files:
        path = f["path"]; mid = module_id(path)
        for imp in f["facts"].get("imports", []):
            name = imp.get("module") or ""; targets = module_targets(path, name)
            if targets:
                for target in targets:
                    target_node = node_by_id[target]; target_path = target_node.get("path")
                    cross = bool(target_path and node_by_id[mid].get("language") != target_node.get("language"))
                    add_edge(edges, seen_edges, mid, target, "IMPORTS", "RESOLVED", path, imp.get("line"), name, cross_language=cross)
                    if f["is_test"] and target_path and target_path != path:
                        add_edge(edges, seen_edges, file_id(path), file_id(target_path), "TESTS", "RESOLVED", path, imp.get("line"), name, evidence_kind="import")
                alias, imported = imp.get("alias"), imp.get("imported")
                if alias:
                    if imported == "*" or imported is None:
                        bindings_by_path[path][alias] = {"kind": "module", "targets": targets, "import": name}
                    else:
                        candidates = []
                        for target in targets:
                            candidates.extend(exports_by_module[target].get(imported, []))
                            target_path = node_by_id[target].get("path")
                            candidates.extend(symbols_by_path_simple.get((target_path, imported), []))
                        candidates = list(dict.fromkeys(candidates))
                        if imported == "default" and not candidates:
                            top = []
                            for target in targets: top.extend(top_symbols_by_path.get(node_by_id[target].get("path"), []))
                            if len(top) == 1: candidates = top
                        if candidates:
                            bindings_by_path[path][alias] = {"kind": "symbol", "targets": candidates, "import": name, "imported": imported}
                            for sid in candidates:
                                add_edge(edges, seen_edges, mid, sid, "IMPORTS_SYMBOL", "RESOLVED", path, imp.get("line"), f"{name}:{imported}", cross_language=node_by_id[sid].get("language") != f["language"])
                        else:
                            bindings_by_path[path][alias] = {"kind": "module", "targets": targets, "import": name, "imported": imported}
            elif name:
                # Bare package names stay external; unresolved relative imports remain visible but are counted.
                if name.startswith("."):
                    unresolved_imports += 1
                eid = external_module_id(name); add_node({"id": eid, "type": "MODULE", "label": name, "external": True})
                add_edge(edges, seen_edges, mid, eid, "IMPORTS", "DIRECT", path, imp.get("line"), name)

    def resolve_symbol(name: str, current_path: str) -> tuple[str | None, str]:
        parts = name.split("."); root = parts[0]; binding = bindings_by_path.get(current_path, {}).get(root)
        if binding:
            if binding["kind"] == "symbol" and len(parts) == 1 and len(binding["targets"]) == 1:
                return binding["targets"][0], "RESOLVED"
            if binding["kind"] == "module":
                member = parts[-1] if len(parts) > 1 else binding.get("imported")
                if member and member not in {"*", "default", None}:
                    hits = []
                    for mid in binding["targets"]:
                        tp = node_by_id[mid].get("path")
                        hits.extend(symbols_by_path_simple.get((tp, member), [])); hits.extend(exports_by_module[mid].get(member, []))
                    hits = list(dict.fromkeys(hits))
                    if len(hits) == 1: return hits[0], "RESOLVED"
        simple = parts[-1]
        same = symbols_by_path_simple.get((current_path, simple), [])
        if len(same) == 1: return same[0], "RESOLVED"
        exact_q = symbols_by_qualified.get(name, [])
        if len(exact_q) == 1: return exact_q[0], "RESOLVED"
        all_simple = symbols_by_simple.get(simple, [])
        if len(all_simple) == 1: return all_simple[0], "RESOLVED"
        return None, "HEURISTIC"

    unresolved_relationships = unresolved_imports
    for f in files:
        path = f["path"]; is_test_file = f["is_test"]
        for call in f["facts"].get("calls", []):
            target, resolution = resolve_symbol(call["target_name"], path)
            if target:
                provenance = "DIRECT" if call.get("provenance") == "DIRECT" and node_by_id[target].get("path") == path else resolution
                cross = node_by_id[target].get("language") != f["language"]
                add_edge(edges, seen_edges, call["source"], target, "CALLS", provenance, path, call.get("line"), call["target_name"], cross_language=cross)
                if is_test_file and node_by_id[target].get("path") != path:
                    add_edge(edges, seen_edges, file_id(path), target, "TESTS", provenance, path, call.get("line"), call["target_name"], evidence_kind="call", cross_language=cross)
            else: unresolved_relationships += 1
        for ref in f["facts"].get("references", []):
            target, resolution = resolve_symbol(ref["target_name"], path)
            if target:
                cross = node_by_id[target].get("language") != f["language"]
                add_edge(edges, seen_edges, ref["source"], target, "REFERENCES", resolution, path, ref.get("line"), ref["target_name"], cross_language=cross)
                if is_test_file and node_by_id[target].get("path") != path:
                    add_edge(edges, seen_edges, file_id(path), target, "TESTS", resolution, path, ref.get("line"), ref["target_name"], evidence_kind="reference", cross_language=cross)
        for inh in f["facts"].get("inherits", []):
            target, resolution = resolve_symbol(inh["target_name"], path)
            if target:
                add_edge(edges, seen_edges, inh["source"], target, inh.get("relation", "INHERITS"), resolution, path, inh.get("line"), inh["target_name"], cross_language=node_by_id[target].get("language") != f["language"])
            else: unresolved_relationships += 1

    dependency_pairs: dict[tuple[str, str], str] = {}
    cross_dependency: set[tuple[str, str]] = set()
    for edge in list(edges):
        src_node, dst_node = node_by_id.get(edge["source"]), node_by_id.get(edge["target"])
        if not src_node or not dst_node: continue
        sp, tp = src_node.get("path"), dst_node.get("path")
        if not sp or not tp or sp == tp or edge["relation"] not in DEPENDENCY_RELATIONS: continue
        key = (file_id(sp), file_id(tp)); current = dependency_pairs.get(key); prov = edge["provenance"]
        if not current or PROVENANCE_RANK.get(prov, 0) > PROVENANCE_RANK.get(current, 0): dependency_pairs[key] = prov
        if src_node.get("language") != dst_node.get("language"): cross_dependency.add(key)
    for (src, dst), prov in dependency_pairs.items():
        add_edge(edges, seen_edges, src, dst, "DEPENDS_ON", prov, cross_language=(src, dst) in cross_dependency)

    provenance_counts = Counter(e["provenance"] for e in edges); relation_counts = Counter(e["relation"] for e in edges); parser_counts = Counter(f["parser"] for f in files); language_counts = Counter(f["language"] for f in files)
    deep_files = sum(1 for f in files if f.get("parser_metadata", {}).get("deep"))
    cross_edges = sum(1 for e in edges if e.get("cross_language"))
    coverage = {
        "files": len(files), "deep_files": deep_files, "fallback_files": parser_counts.get("fallback-regex", 0),
        "python_ast_files": parser_counts.get("python-ast", 0),
        "tree_sitter_files": sum(v for k, v in parser_counts.items() if k.startswith("tree-sitter-")),
        "parser_counts": dict(sorted(parser_counts.items())), "language_counts": dict(sorted(language_counts.items())),
        "cross_language_edges": cross_edges, "runtime": parser_runtime(),
    }
    return {
        "schema_version": GRAPH_SCHEMA_VERSION, "generated_at": now_iso(), "git_head": head,
        "parser_version": PARSER_VERSION, "file_count": len(files), "node_count": len(nodes), "edge_count": len(edges),
        "files": files, "nodes": nodes, "edges": edges, "coverage": coverage,
        "provenance_counts": dict(sorted(provenance_counts.items())), "relation_counts": dict(sorted(relation_counts.items())),
        "unresolved_relationships": unresolved_relationships, "incremental": stats,
    }


def manifest_for(files: list[dict], head: str | None) -> dict:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION, "graph_schema_version": GRAPH_SCHEMA_VERSION,
        "parser_version": PARSER_VERSION, "generated_at": now_iso(), "git_head": head, "runtime": parser_runtime(),
        "files": {f["path"]: {"sha256": f["sha256"], "parser": f["parser"], "parser_version": f["parser_version"], "capabilities": f.get("capabilities", [])} for f in files},
    }


def scan(root: Path) -> dict:
    s = state_root(root); old_graph = read_json(s / "repository/graph.json", {}); old_manifest = read_json(s / "repository/manifest.json", {})
    files, stats = extract_files(root, discover_files(root), old_graph, old_manifest); head = git(root, "rev-parse", "HEAD")
    graph = build_graph(files, head, stats); write_json(s / "repository/graph.json", graph); write_json(s / "repository/manifest.json", manifest_for(files, head)); return graph


def main() -> None:
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True); b = sub.add_parser("build"); b.add_argument("--root", default="."); b.add_argument("--output")
    ns = ap.parse_args(); root = Path(ns.root).resolve(); graph = scan(root)
    if ns.output: write_json(Path(ns.output), graph)
    print(json.dumps({"output": str(Path(ns.output) if ns.output else state_root(root) / "repository/graph.json"), "schema_version": graph["schema_version"], "file_count": graph["file_count"], "node_count": graph["node_count"], "edge_count": graph["edge_count"], "git_head": graph["git_head"], "incremental": graph["incremental"], "coverage": graph["coverage"]}, indent=2))


if __name__ == "__main__": main()
