#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from common import git, read_json, state_root, write_json

SCHEMA_VERSION = 1
SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
TEST_MARKERS = ("/test/", "/tests/", "/__tests__/", ".test.", ".spec.")
MAX_UNTRACKED_BYTES = 2_000_000
BLOCKING_RULES = {
    "UNJUSTIFIED_SCOPE",
    "DUPLICATE_IMPLEMENTATION",
    "UNJUSTIFIED_DEPENDENCY",
    "UNJUSTIFIED_PUBLIC_API",
}
SEVERITY_WEIGHT = {"BLOCKER": 25, "MAJOR": 12, "MINOR": 4, "INFO": 1}
PROTECTED_RE = re.compile(
    r"\b(auth(?:entication|orization)?|permission|role|validat(?:e|ion)|saniti[sz](?:e|ation)|"
    r"rate.?limit|transaction|rollback|lock(?:ing)?|idempoten(?:t|cy)|retry|migration|compatib(?:ility|le)|"
    r"integrity|csrf|xss|encrypt(?:ion|ed)?|decrypt(?:ion|ed)?|signature|nonce|secret|token)\b",
    re.I,
)
DEBUG_STRONG_RE = re.compile(r"\b(?:debugger\s*;?|breakpoint\s*\(|pdb\.set_trace\s*\(|console\.(?:debug|trace)\s*\()")
DEBUG_WEAK_RE = re.compile(r"\b(?:console\.log\s*\(|print\s*\()")
TYPE_ESCAPE_RE = re.compile(r"(?:#\s*type:\s*ignore|@ts-ignore|@ts-nocheck|\bas\s+any\b|:\s*any\b)")
PUBLIC_API_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\b|__all__\s*=)")
BROAD_EXCEPTION_RE = re.compile(r"\b(?:except\s+(?:Exception|BaseException)\b|catch\s*\([^)]*\)\s*\{?)")
NARRATIVE_COMMENT_RE = re.compile(
    r"^\s*(?:#|//)\s*(?:increment|decrement|set|return|check|initialize|initialise|create|call|loop|iterate|"
    r"assign|update|delete|remove|add|convert|parse|format|sort|filter|map|open|close|read|write)\b",
    re.I,
)


@dataclass
class DiffFile:
    path: str
    old_path: str | None = None
    status: str = "modified"
    added: list[tuple[int, str]] = field(default_factory=list)
    removed: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class Finding:
    rule: str
    path: str
    severity: str
    confidence: float
    evidence_class: str
    autofix: str
    reason: str
    introduced: str = "introduced"
    line: int | None = None
    symbol: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out = {
            "rule": self.rule,
            "path": self.path,
            "introduced": self.introduced,
            "severity": self.severity,
            "confidence": round(self.confidence, 2),
            "evidence_class": self.evidence_class,
            "autofix": self.autofix,
            "reason": self.reason,
            "evidence": self.evidence,
        }
        if self.line is not None:
            out["line"] = self.line
        if self.symbol:
            out["symbol"] = self.symbol
        return out


def _is_test_path(path: str) -> bool:
    s = "/" + path.lower().replace("\\", "/")
    name = Path(path).name.lower()
    return any(x in s for x in TEST_MARKERS) or name.startswith("test_") or name.endswith("_test.py")


def _allowed(path: str, patterns: list[str]) -> bool:
    return any(path == p or fnmatch.fnmatch(path, p) or path.startswith(p.rstrip("/") + "/") for p in patterns)


def resolve_diff_scope(root: Path, base: str | None, head: str | None, task: dict) -> dict[str, str]:
    requested_base = base or task.get("git_base") or task.get("base_ref")
    if requested_base and git(root, "rev-parse", "--verify", requested_base):
        resolved_base = requested_base
        source = "explicit" if base else "task"
    else:
        upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
        merge_base = git(root, "merge-base", "HEAD", upstream) if upstream else None
        if merge_base:
            resolved_base, source = merge_base, "upstream-merge-base"
        else:
            resolved_base, source = "HEAD", "head-fallback"
    resolved_head = head or "WORKTREE"
    if resolved_head != "WORKTREE" and not git(root, "rev-parse", "--verify", resolved_head):
        resolved_head = "WORKTREE"
    return {"base": resolved_base, "head": resolved_head, "source": source}


def get_diff(root: Path, scope: dict[str, str]) -> str:
    base, head = scope["base"], scope["head"]
    if head == "WORKTREE":
        return git(root, "diff", "--no-ext-diff", "--unified=0", "--no-color", base, "--") or ""
    return git(root, "diff", "--no-ext-diff", "--unified=0", "--no-color", f"{base}..{head}", "--") or ""


def parse_diff(text: str) -> dict[str, DiffFile]:
    files: dict[str, DiffFile] = {}
    current: DiffFile | None = None
    old_line = new_line = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*?) b/(.*)$", raw)
            if not m:
                current = None
                continue
            old_path, path = m.group(1), m.group(2)
            current = DiffFile(path=path, old_path=old_path)
            files[path] = current
            continue
        if current is None:
            continue
        if raw.startswith("new file mode"):
            current.status = "added"
            continue
        if raw.startswith("deleted file mode"):
            current.status = "deleted"
            continue
        if raw.startswith("rename from "):
            current.old_path = raw[len("rename from "):]
            current.status = "renamed"
            continue
        if raw.startswith("rename to "):
            newp = raw[len("rename to "):]
            if newp != current.path:
                files.pop(current.path, None)
                current.path = newp
                files[newp] = current
            current.status = "renamed"
            continue
        if raw.startswith("@@"):
            m = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw)
            if m:
                old_line, new_line = int(m.group(1)), int(m.group(3))
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            current.added.append((new_line, raw[1:]))
            new_line += 1
            continue
        if raw.startswith("-"):
            current.removed.append((old_line, raw[1:]))
            old_line += 1
            continue
        if raw.startswith(" "):
            old_line += 1
            new_line += 1
    return files


def untracked_diff_files(root: Path) -> dict[str, DiffFile]:
    """Represent safe, readable untracked files as added diff surfaces.

    `git diff` does not include untracked files, but a newly generated source/config
    file is exactly the kind of surface Slop Guard must not miss. Codemium's own
    state remains excluded even when a repository has not yet ignored `.codemium/`.
    """
    raw = git(root, "ls-files", "--others", "--exclude-standard") or ""
    out: dict[str, DiffFile] = {}
    for rel in raw.splitlines():
        path = rel.strip().replace("\\", "/")
        if not path or path == ".codemium" or path.startswith(".codemium/"):
            continue
        full = root / path
        try:
            data = full.read_bytes()
        except OSError:
            continue
        if len(data) > MAX_UNTRACKED_BYTES or b"\x00" in data:
            continue
        text = data.decode("utf-8", errors="ignore")
        out[path] = DiffFile(
            path=path,
            old_path=None,
            status="added",
            added=[(line_no, line) for line_no, line in enumerate(text.splitlines(), start=1)],
        )
    return out


def _task_scope(task: dict) -> list[str]:
    patterns = list(task.get("working_set") or [])
    for p in (task.get("working_set_evidence") or {}).keys():
        if p not in patterns:
            patterns.append(p)
    return patterns


def classify_surface(path: str, task: dict, graph: dict) -> dict[str, Any]:
    graph_file = next((f for f in graph.get("files", []) if f.get("path") == path), {})
    if graph_file.get("is_test") or _is_test_path(path):
        return {"class": "TEST", "reason": "verification/test surface"}
    patterns = _task_scope(task)
    if patterns and not _allowed(path, patterns):
        return {"class": "UNJUSTIFIED", "reason": "changed path is outside the active task working set"}
    evidence = (task.get("working_set_evidence") or {}).get(path, [])
    graph_reasons = [x for x in evidence if x.get("kind") == "graph"]
    if graph_reasons:
        best = min(graph_reasons, key=lambda x: int(x.get("distance", 99)))
        distance = int(best.get("distance", 99))
        if distance == 0:
            return {"class": "DIRECT", "reason": "task seed matched structural entity"}
        return {
            "class": "DEPENDENCY",
            "reason": f"structural {best.get('relation') or 'relationship'} at distance {distance}",
            "provenance": best.get("provenance"),
        }
    if patterns:
        return {"class": "DIRECT", "reason": "included in the active task working set"}
    return {"class": "DIRECT", "reason": "standalone review target; no active working-set constraint"}


def graph_indexes(graph: dict) -> dict[str, Any]:
    nodes = {n.get("id"): n for n in graph.get("nodes", []) if n.get("id")}
    symbols_by_path: defaultdict[str, list[dict]] = defaultdict(list)
    symbols_by_label: defaultdict[str, list[dict]] = defaultdict(list)
    inbound: Counter[str] = Counter()
    implementations: Counter[str] = Counter()
    for n in nodes.values():
        if n.get("type") == "SYMBOL" and n.get("path"):
            symbols_by_path[n["path"]].append(n)
            symbols_by_label[str(n.get("label") or "")].append(n)
    for e in graph.get("edges", []):
        target = e.get("target")
        relation = e.get("relation")
        if target and relation in {"CALLS", "REFERENCES", "IMPORTS_SYMBOL", "IMPLEMENTS", "INHERITS"}:
            inbound[target] += 1
        if target and relation == "IMPLEMENTS":
            implementations[target] += 1
    return {
        "nodes": nodes,
        "symbols_by_path": symbols_by_path,
        "symbols_by_label": symbols_by_label,
        "inbound": inbound,
        "implementations": implementations,
    }


def _intersects_added(symbol: dict, diff_file: DiffFile) -> bool:
    start, end = symbol.get("line_start"), symbol.get("line_end")
    if not isinstance(start, int):
        return False
    end = end if isinstance(end, int) and end >= start else start
    return any(start <= line <= end for line, _ in diff_file.added)


def _python_forwarders(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or len(node.body) != 1:
            continue
        stmt = node.body[0]
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
            out.add(node.name)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            out.add(node.name)
    return out


def detect_line_findings(diff_files: dict[str, DiffFile]) -> list[Finding]:
    findings: list[Finding] = []
    for path, df in diff_files.items():
        test_path = _is_test_path(path)
        for line, text in df.added:
            if DEBUG_STRONG_RE.search(text):
                findings.append(Finding("DEBUG_RESIDUE", path, "MAJOR", 0.99, "DETERMINISTIC", "SAFE_MECHANICAL", "debugger/breakpoint residue was added", line=line, evidence={"line": text.strip()}))
            elif DEBUG_WEAK_RE.search(text) and not test_path:
                findings.append(Finding("DEBUG_RESIDUE", path, "MINOR", 0.78, "DETERMINISTIC", "REVIEW_REQUIRED", "console/print output was added to production code", line=line, evidence={"line": text.strip()}))
            if TYPE_ESCAPE_RE.search(text) and not test_path:
                findings.append(Finding("UNJUSTIFIED_TYPE_ESCAPE", path, "MAJOR", 0.91, "DETERMINISTIC", "REVIEW_REQUIRED", "type-system escape hatch was added", line=line, evidence={"line": text.strip()}))
            if NARRATIVE_COMMENT_RE.search(text) and len(text.strip()) <= 100 and not test_path:
                findings.append(Finding("NARRATIVE_COMMENT", path, "MINOR", 0.66, "DETERMINISTIC", "SAFE_MECHANICAL", "comment appears to narrate an obvious operation rather than record rationale", line=line, evidence={"line": text.strip()}))
            if PUBLIC_API_RE.search(text) and not test_path:
                findings.append(Finding("UNJUSTIFIED_PUBLIC_API", path, "MINOR", 0.72, "DETERMINISTIC", "REVIEW_REQUIRED", "public/exported API surface was added and requires task-level justification", line=line, evidence={"line": text.strip()}))
            if BROAD_EXCEPTION_RE.search(text) and not test_path:
                nearby = [t for ln, t in df.added if line < ln <= line + 5]
                if any(re.search(r"\b(return|continue|pass|default|fallback)\b", t, re.I) for t in nearby):
                    findings.append(Finding("SPECULATIVE_FALLBACK", path, "MAJOR", 0.76, "DETERMINISTIC", "REVIEW_REQUIRED", "broad exception path with fallback-like behavior was added", line=line, evidence={"line": text.strip(), "nearby_added": [x.strip() for x in nearby[:5]]}))
    return findings


def _load_json_at_ref(root: Path, ref: str, path: str) -> dict:
    raw = git(root, "show", f"{ref}:{path}")
    if raw is None:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def detect_dependency_findings(root: Path, scope: dict[str, str], diff_files: dict[str, DiffFile]) -> list[Finding]:
    findings: list[Finding] = []
    if "package.json" in diff_files and (root / "package.json").exists():
        before = _load_json_at_ref(root, scope["base"], "package.json")
        try:
            after = json.loads((root / "package.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            after = {}
        sections = ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
        for section in sections:
            old = before.get(section, {}) if isinstance(before.get(section), dict) else {}
            new = after.get(section, {}) if isinstance(after.get(section), dict) else {}
            for name in sorted(set(new) - set(old)):
                findings.append(Finding(
                    "UNJUSTIFIED_DEPENDENCY", "package.json", "MAJOR", 0.98, "DETERMINISTIC", "REVIEW_REQUIRED",
                    f"new {section} entry requires evidence that project/stdlib/native capability cannot satisfy the task",
                    evidence={"dependency": name, "version": new.get(name), "section": section},
                ))
    for path, df in diff_files.items():
        name = Path(path).name.lower()
        if name.startswith("requirements") and name.endswith(".txt"):
            for line, text in df.added:
                dep = text.strip()
                if dep and not dep.startswith(("#", "-", "git+", "http://", "https://")):
                    findings.append(Finding("UNJUSTIFIED_DEPENDENCY", path, "MAJOR", 0.92, "DETERMINISTIC", "REVIEW_REQUIRED", "new Python dependency entry requires necessity evidence", line=line, evidence={"dependency": dep}))
        elif name in {"go.mod", "cargo.toml", "gemfile"}:
            for line, text in df.added:
                stripped = text.strip()
                if stripped and not stripped.startswith(("#", "//", "[")):
                    findings.append(Finding("UNJUSTIFIED_DEPENDENCY", path, "MINOR", 0.68, "DETERMINISTIC", "REVIEW_REQUIRED", "dependency-manifest addition requires review", line=line, evidence={"line": stripped}))
    return findings


def detect_structural_findings(root: Path, graph: dict, idx: dict[str, Any], diff_files: dict[str, DiffFile]) -> list[Finding]:
    findings: list[Finding] = []
    for path, df in diff_files.items():
        symbols = [s for s in idx["symbols_by_path"].get(path, []) if _intersects_added(s, df)]
        if not symbols:
            continue
        py_forwarders = _python_forwarders(root / path) if Path(path).suffix.lower() == ".py" else set()
        for sym in symbols:
            sid = sym.get("id")
            label = str(sym.get("label") or "")
            subtype = str(sym.get("subtype") or "").lower()
            qualified = str(sym.get("qualified_name") or label)
            inbound = int(idx["inbound"].get(sid, 0))
            peers = [x for x in idx["symbols_by_label"].get(label, []) if x.get("id") != sid and x.get("path") != path and str(x.get("subtype") or "").lower() == subtype]
            # Same-named methods/classes are routine across unrelated types and are too
            # noisy for a blocking duplicate signal. Reserve the high-confidence gate
            # for top-level functions, then require source review before consolidation.
            is_top_level_function = subtype == "function" and "." not in qualified
            if label and peers and is_top_level_function:
                function_peers = [p for p in peers if "." not in str(p.get("qualified_name") or p.get("label") or "")]
                if function_peers:
                    findings.append(Finding(
                        "DUPLICATE_IMPLEMENTATION", path, "MAJOR", 0.9, "STRUCTURAL", "REVIEW_REQUIRED",
                        "a newly changed top-level function shares the same repository-level function name with an existing implementation; inspect reuse before accepting duplication",
                        line=sym.get("line_start"), symbol=label,
                        evidence={"existing": [{"path": p.get("path"), "symbol": p.get("qualified_name") or p.get("label")} for p in function_peers[:5]], "inbound": inbound},
                    ))
            if subtype in {"function", "method"} and label in py_forwarders and inbound <= 1:
                findings.append(Finding(
                    "SINGLE_USE_FORWARDER", path, "MINOR", 0.89, "STRUCTURAL", "REVIEW_REQUIRED",
                    "single-statement forwarding function has at most one inbound structural consumer",
                    line=sym.get("line_start"), symbol=label, evidence={"inbound_consumers": inbound},
                ))
            if inbound == 0 and subtype in {"function", "method", "class", "interface"} and not label.startswith("test"):
                findings.append(Finding(
                    "NEW_DEAD_CODE", path, "MINOR", 0.64, "STRUCTURAL", "REVIEW_REQUIRED",
                    "newly changed symbol has no inbound structural consumer; entrypoint/reflection use must be ruled out before removal",
                    line=sym.get("line_start"), symbol=label, evidence={"inbound_consumers": 0},
                ))
            if subtype in {"class", "interface"} and inbound <= 1 and int(idx["implementations"].get(sid, 0)) <= 1:
                findings.append(Finding(
                    "GRATUITOUS_ABSTRACTION", path, "MINOR", 0.67, "STRUCTURAL", "REVIEW_REQUIRED",
                    "new abstraction has limited structural consumers/implementations and needs architecture justification",
                    line=sym.get("line_start"), symbol=label,
                    evidence={"inbound_consumers": inbound, "implementations": int(idx["implementations"].get(sid, 0))},
                ))
        if df.status == "added":
            code_lines = [t for _, t in df.added if t.strip() and not t.lstrip().startswith(("#", "//"))]
            inbound_total = sum(int(idx["inbound"].get(s.get("id"), 0)) for s in symbols)
            if len(symbols) <= 1 and len(code_lines) <= 10 and inbound_total <= 1 and not _is_test_path(path):
                findings.append(Finding(
                    "UNNECESSARY_FILE", path, "MINOR", 0.7, "STRUCTURAL", "REVIEW_REQUIRED",
                    "new small file contains at most one changed symbol and little structural reuse evidence",
                    evidence={"changed_symbols": len(symbols), "code_lines": len(code_lines), "inbound_consumers": inbound_total},
                ))
    return findings


def detect_scope_findings(classifications: dict[str, dict[str, Any]]) -> list[Finding]:
    out = []
    for path, info in classifications.items():
        if info.get("class") == "UNJUSTIFIED":
            out.append(Finding("UNJUSTIFIED_SCOPE", path, "MAJOR", 0.99, "DETERMINISTIC", "REVIEW_REQUIRED", info.get("reason") or "changed surface is not justified by active task scope"))
    return out


def protected_complexity(diff_files: dict[str, DiffFile]) -> dict[str, Any]:
    added, removed = [], []
    for path, df in diff_files.items():
        for line, text in df.added:
            if PROTECTED_RE.search(text):
                added.append({"path": path, "line": line, "text": text.strip()})
        for line, text in df.removed:
            if PROTECTED_RE.search(text):
                removed.append({"path": path, "line": line, "text": text.strip()})
    return {
        "added": added[:50],
        "removed": removed[:50],
        "underengineering_gate": {
            "status": "review_required" if removed else "pass",
            "reason": "protected-complexity lines were removed; verify behavior/security/data-integrity intent" if removed else "no protected-complexity removal signal detected",
        },
    }


def coverage(graph: dict, diff_files: dict[str, DiffFile]) -> dict[str, Any]:
    graph_files = {f.get("path"): f for f in graph.get("files", []) if f.get("path")}
    source_added = analyzable_added = 0
    changed_source_files = structurally_covered = 0
    for path, df in diff_files.items():
        if Path(path).suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        changed_source_files += 1
        source_added += len(df.added)
        rec = graph_files.get(path)
        if rec:
            structurally_covered += 1
            caps = rec.get("capabilities") or {}
            if rec.get("parser") in {"python-ast", "tree-sitter-javascript", "tree-sitter-typescript", "tree-sitter-tsx"} or caps.get("symbols"):
                analyzable_added += len(df.added)
    changed_line_coverage = 1.0 if source_added == 0 else analyzable_added / source_added
    structural_coverage = 1.0 if changed_source_files == 0 else structurally_covered / changed_source_files
    scoreable = source_added > 0 and changed_line_coverage >= 0.5 and structural_coverage >= 0.5
    return {
        "changed_lines": round(changed_line_coverage, 3),
        "structural": round(structural_coverage, 3),
        "source_added_lines": source_added,
        "changed_source_files": changed_source_files,
        "scoreable": scoreable,
    }


def risk_score(findings: list[Finding], scoreable: bool) -> int | None:
    if not scoreable:
        return None
    total = 0.0
    for f in findings:
        if f.introduced not in {"introduced", "worsened"}:
            continue
        total += SEVERITY_WEIGHT.get(f.severity, 1) * f.confidence
    return min(100, int(round(total)))


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen = set()
    out = []
    for f in findings:
        key = (f.rule, f.path, f.line, f.symbol, f.reason)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def verdict(findings: list[Finding], protected: dict[str, Any]) -> str:
    for f in findings:
        if f.introduced in {"introduced", "worsened"} and f.confidence >= 0.85 and (f.severity == "BLOCKER" or f.rule in BLOCKING_RULES):
            return "fail"
    if protected["underengineering_gate"]["status"] != "pass":
        return "review"
    if any(f.severity == "MAJOR" and f.confidence >= 0.6 for f in findings):
        return "review"
    return "pass"


def analyze(root: Path, base: str | None = None, head: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    state = state_root(root)
    task = read_json(state / "tasks/active.json", {})
    graph = read_json(state / "repository/graph.json", {})
    scope = resolve_diff_scope(root, base, head, task)
    diff_files = parse_diff(get_diff(root, scope))
    if scope["head"] == "WORKTREE":
        for path, diff_file in untracked_diff_files(root).items():
            diff_files.setdefault(path, diff_file)
    classifications = {path: classify_surface(path, task, graph) for path in sorted(diff_files)}
    idx = graph_indexes(graph)
    findings = []
    findings.extend(detect_scope_findings(classifications))
    findings.extend(detect_line_findings(diff_files))
    findings.extend(detect_dependency_findings(root, scope, diff_files))
    findings.extend(detect_structural_findings(root, graph, idx, diff_files))
    findings = dedupe_findings(findings)
    protected = protected_complexity(diff_files)
    cov = coverage(graph, diff_files)
    status = verdict(findings, protected)
    classes = Counter(x.get("class") for x in classifications.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "scope": scope,
        "risk_score": risk_score(findings, bool(cov["scoreable"])),
        "scoreable": bool(cov["scoreable"]),
        "coverage": {k: v for k, v in cov.items() if k != "scoreable"},
        "changed_files": len(diff_files),
        "surfaces": {
            "direct": classes.get("DIRECT", 0),
            "dependency": classes.get("DEPENDENCY", 0),
            "cleanup": classes.get("CLEANUP", 0),
            "test": classes.get("TEST", 0),
            "unjustified": classes.get("UNJUSTIFIED", 0),
        },
        "surface_classification": classifications,
        "findings": [f.as_dict() for f in findings],
        "protected_complexity": protected,
        "underengineering_gate": protected["underengineering_gate"],
    }


def human_report(report: dict[str, Any]) -> str:
    score = report.get("risk_score")
    score_text = f"{score}/100" if score is not None else "N/A (insufficient scoreable coverage)"
    lines = [
        "CODEMIUM SLOP GUARD",
        "",
        f"Scope: {report['scope']['base']} -> {report['scope']['head']} ({report['scope']['source']})",
        f"Changed files: {report['changed_files']}",
        f"Slop Risk: {score_text}",
        f"Coverage: changed-lines {report['coverage']['changed_lines']:.0%}, structural {report['coverage']['structural']:.0%}",
        f"Status: {report['status'].upper()}",
        "",
        "Surfaces: " + ", ".join(f"{k}={v}" for k, v in report["surfaces"].items()),
        f"Underengineering gate: {report['underengineering_gate']['status'].upper()}",
    ]
    findings = report.get("findings", [])
    if findings:
        lines.extend(["", "Introduced findings:"])
        for f in findings:
            loc = f"{f['path']}:{f['line']}" if f.get("line") else f["path"]
            symbol = f" [{f['symbol']}]" if f.get("symbol") else ""
            lines.append(f"- {f['severity']} {f['rule']} @ {loc}{symbol} ({f['confidence']:.0%})")
    else:
        lines.extend(["", "Introduced findings: none"])
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Codemium v0.9 task-aware Anti-Slop / Justified Change Gate")
    ap.add_argument("--root", default=".")
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write-state", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ns = ap.parse_args()
    report = analyze(Path(ns.root), ns.base, ns.head)
    if ns.write_state:
        write_json(state_root(Path(ns.root)) / "runtime/slop-report.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False) if ns.json else human_report(report))
    if ns.strict and report["status"] != "pass":
        raise SystemExit(3 if report["status"] == "fail" else 2)


if __name__ == "__main__":
    main()
