#!/usr/bin/env python3
"""Fast, host-agnostic Codemium core verification."""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins/codemium/engine"
TESTS = ROOT / "plugins/codemium/tests"

REQUIRED_ENGINE = [
    "common.py", "project_brain.py", "parsers.py", "repo_graph.py", "graph_query.py", "working_set.py", "impact.py",
    "scope_guard.py", "test_map.py", "cache.py", "telemetry.py", "health.py", "reasoning_profile.py", "task_compiler.py",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version: fail("VERSION is empty")
    for name in REQUIRED_ENGINE:
        path = ENGINE / name
        if not path.exists(): fail(f"missing engine/{name}")
        py_compile.compile(str(path), doraise=True)
    fixture = TESTS / "test_core_fixture.py"
    if not fixture.exists(): fail("missing host-agnostic core fixture")
    py_compile.compile(str(fixture), doraise=True)

    brain = (ENGINE / "project_brain.py").read_text(encoding="utf-8")
    for phrase in ["GENERIC_REASONING", "TRANSIENT_IGNORE", "tasks/active.json", "host_profiles", "def capture(", "find_active_duplicate", "init(root, emit=False)", "def entry_freshness(", "NEEDS_REVALIDATION", "def revalidate("]:
        if phrase not in brain: fail(f"Project Brain contract missing: {phrase}")
    parsers = (ENGINE / "parsers.py").read_text(encoding="utf-8")
    for phrase in ["class ParserAdapter", "class PythonAstParser", "class TreeSitterJSTSParser", "class RegexFallbackParser", "fallback-regex", "PARSER_VERSION = \"3\""]:
        if phrase not in parsers: fail(f"parser abstraction contract missing: {phrase}")
    graph = (ENGINE / "repo_graph.py").read_text(encoding="utf-8")
    for phrase in ["GRAPH_SCHEMA_VERSION = 3", "DIRECT", "RESOLVED", "HEURISTIC", "DEPENDS_ON", "TESTS", "IMPORTS_SYMBOL", "cross_language", "bindings_by_path"]:
        if phrase not in graph: fail(f"Polyglot graph contract missing: {phrase}")
    query = (ENGINE / "graph_query.py").read_text(encoding="utf-8")
    for phrase in ["def shortest_path(", "def bounded_expand(", "def dependents_for_nodes(", "def dependents_for_files(", "callers", "tests-for", "IMPORTS_SYMBOL"]:
        if phrase not in query: fail(f"graph query contract missing: {phrase}")
    impact = (ENGINE / "impact.py").read_text(encoding="utf-8")
    for phrase in ["changed_line_ranges", "changed_symbol_seeds", "symbol-structural", "cross_language_dependents", "test_plan"]:
        if phrase not in impact: fail(f"impact intelligence contract missing: {phrase}")
    tests = (ENGINE / "test_map.py").read_text(encoding="utf-8")
    for phrase in ["schema_version\": 3", "prioritized", "confidence", "cross_language_relationships"]:
        if phrase not in tests: fail(f"test intelligence contract missing: {phrase}")
    compiler = (ENGINE / "task_compiler.py").read_text(encoding="utf-8")
    for depth in ["FAST", "NORMAL", "DEEP", "CRITICAL"]:
        if depth not in compiler: fail(f"task compiler depth missing: {depth}")
    if "init_project_brain(root, emit=False)" not in compiler: fail("normal task compilation must auto-initialize Project Brain")
    if "apply_structural_escalation" not in compiler: fail("task compiler must consume structural risk")

    codex_skill = (ROOT / "plugins/codemium/skills/codemium/SKILL.md").read_text(encoding="utf-8")
    for phrase in ["Project Brain persistence contract", "Do **not** require the user to run `$cm-init` first", "Persistence gate", "captured", "skipped by user constraint"]:
        if phrase not in codex_skill: fail(f"Codex persistence behavior missing: {phrase}")

    result = subprocess.run([sys.executable, str(fixture)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout); sys.stderr.write(result.stderr); fail("core fixture failed")
    print(json.dumps({
        "status": "pass", "version": version, "scope": "codemium-core",
        "checked": ["engine syntax", "Project Brain persistence/evidence/freshness", "parser abstraction + deterministic fallback", "Structural Graph v3 + provenance", "incremental graph refresh", "symbol-aware impact/test mapping", "automatic Project Brain initialization/capture", "generic task/depth contract", "host-agnostic v0.8 core fixture"],
    }, indent=2))
    print("PASS: Codemium core integrity")


if __name__ == "__main__": main()
