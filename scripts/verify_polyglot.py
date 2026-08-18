#!/usr/bin/env python3
"""Verify Codemium v0.8 Polyglot Intelligence with Tree-sitter installed."""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins/codemium/engine"
TEST = ROOT / "plugins/codemium/tests/test_polyglot_fixture.py"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    for mod in ["tree_sitter", "tree_sitter_javascript", "tree_sitter_typescript"]:
        try: __import__(mod)
        except Exception as exc: fail(f"missing polyglot dependency {mod}: {exc}")
    for path in [ENGINE / "parsers.py", ENGINE / "repo_graph.py", ENGINE / "graph_query.py", ENGINE / "impact.py", ENGINE / "test_map.py", TEST]:
        py_compile.compile(str(path), doraise=True)
    parser_text = (ENGINE / "parsers.py").read_text(encoding="utf-8")
    for phrase in ["class ParserAdapter", "class TreeSitterJSTSParser", "tree_sitter_javascript", "tree_sitter_typescript", "language_typescript", "language_tsx", "cross_language_bindings"]:
        if phrase not in parser_text: fail(f"polyglot parser contract missing: {phrase}")
    graph_text = (ENGINE / "repo_graph.py").read_text(encoding="utf-8")
    for phrase in ["GRAPH_SCHEMA_VERSION = 3", "IMPORTS_SYMBOL", "cross_language", "bindings_by_path", "tree_sitter_files"]:
        if phrase not in graph_text: fail(f"cross-language graph contract missing: {phrase}")
    impact_text = (ENGINE / "impact.py").read_text(encoding="utf-8")
    for phrase in ["changed_line_ranges", "changed_symbol_seeds", "cross_language_dependents", "test_plan", "symbol-structural"]:
        if phrase not in impact_text: fail(f"impact intelligence contract missing: {phrase}")
    result = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout); sys.stderr.write(result.stderr); fail("polyglot fixture failed")
    print(json.dumps({"status": "pass", "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(), "scope": "polyglot-intelligence", "checked": ["parser abstraction", "Tree-sitter JavaScript", "Tree-sitter TypeScript", "Tree-sitter TSX", "cross-language import/symbol/call graph", "symbol-aware impact", "prioritized test intelligence"]}, indent=2))
    print("PASS: Codemium v0.8 Polyglot Intelligence")


if __name__ == "__main__": main()
