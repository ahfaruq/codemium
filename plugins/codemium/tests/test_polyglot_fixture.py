#!/usr/bin/env python3
"""Codemium v0.8 Polyglot Intelligence integration fixture."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ENGINE = PLUGIN / "engine"


def run(*args, cwd=None):
    p = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout); print(p.stderr, file=sys.stderr); raise AssertionError(f"command failed {p.returncode}: {args}")
    return p.stdout


def main() -> None:
    # Fail clearly if the dedicated polyglot verifier forgot to install the runtime.
    for mod in ["tree_sitter", "tree_sitter_javascript", "tree_sitter_typescript"]:
        __import__(mod)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td); (root / "src").mkdir(); (root / "tests").mkdir()
        (root / "src/math.ts").write_text(
            "export interface Numeric { value: number }\n"
            "export function add(a: number, b: number): number { return a + b; }\n", encoding="utf-8")
        (root / "src/service.ts").write_text(
            "import { add } from './math';\n"
            "export function total(items: number[]): number { return items.reduce((sum, x) => add(sum, x), 0); }\n", encoding="utf-8")
        (root / "src/view.tsx").write_text(
            "import { total } from './service';\n"
            "export function Summary(props: { items: number[] }) { return <div>{total(props.items)}</div>; }\n", encoding="utf-8")
        (root / "src/legacy.js").write_text(
            "import { add } from './math';\n"
            "export function plusOne(value) { return add(value, 1); }\n", encoding="utf-8")
        (root / "tests/service.test.ts").write_text(
            "import { total } from '../src/service';\n"
            "export function testTotal() { if (total([1, 2, 3]) !== 6) throw new Error('bad total'); }\n", encoding="utf-8")

        run("git", "init", "-q", cwd=root); run("git", "config", "user.email", "fixture@example.com", cwd=root); run("git", "config", "user.name", "Fixture", cwd=root)
        run("git", "add", ".", cwd=root); run("git", "commit", "-qm", "initial", cwd=root)

        built = json.loads(run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root))
        graph = json.loads((root / ".codemium/repository/graph.json").read_text(encoding="utf-8"))
        assert graph["schema_version"] == 3
        assert built["coverage"]["tree_sitter_files"] == 5, built["coverage"]
        assert built["coverage"]["fallback_files"] == 0, built["coverage"]
        parsers = {f["path"]: f["parser"] for f in graph["files"]}
        assert parsers["src/math.ts"] == "tree-sitter-typescript"
        assert parsers["src/view.tsx"] == "tree-sitter-tsx"
        assert parsers["src/legacy.js"] == "tree-sitter-javascript"
        assert graph["coverage"]["cross_language_edges"] > 0

        add_nodes = [n for n in graph["nodes"] if n.get("type") == "SYMBOL" and n.get("path") == "src/math.ts" and n.get("label") == "add"]
        assert len(add_nodes) == 1
        add_id = add_nodes[0]["id"]
        assert any(e["relation"] == "IMPORTS_SYMBOL" and e["target"] == add_id and e.get("source_file") == "src/legacy.js" for e in graph["edges"])
        assert any(e["relation"] == "CALLS" and e["target"] == add_id and e.get("source_file") == "src/legacy.js" and e.get("cross_language") for e in graph["edges"])
        assert any(e["relation"] == "TESTS" and e.get("source_file") == "tests/service.test.ts" for e in graph["edges"])

        callers = json.loads(run(sys.executable, ENGINE / "graph_query.py", "--root", root, "callers", "add"))
        caller_paths = {x.get("node", {}).get("path") for x in callers}
        assert {"src/service.ts", "src/legacy.js"}.issubset(caller_paths), caller_paths

        test_map = json.loads(run(sys.executable, ENGINE / "test_map.py", "build", "--root", root))
        assert test_map["relationships"] >= 1
        tests_state = json.loads((root / ".codemium/repository/tests.json").read_text(encoding="utf-8"))
        assert tests_state["schema_version"] == 3
        assert tests_state["prioritized"]
        assert any(x["test"] == "tests/service.test.ts" and x["confidence"] == "high" for x in tests_state["relationships"])

        (root / "src/math.ts").write_text(
            "export interface Numeric { value: number }\n"
            "export function add(a: number, b: number): number { if (!Number.isFinite(a + b)) throw new Error('invalid'); return a + b; }\n", encoding="utf-8")
        impact = json.loads(run(sys.executable, ENGINE / "impact.py", "--root", root, "--git-diff", "--max-depth", "3"))
        assert impact["impact_mode"] == "symbol-structural", impact
        assert any(x.get("symbol") == "add" for x in impact["seed_evidence"]), impact["seed_evidence"]
        assert "src/service.ts" in impact["likely_dependents"], impact["likely_dependents"]
        assert "src/legacy.js" in impact["likely_dependents"], impact["likely_dependents"]
        assert "src/legacy.js" in impact["cross_language_dependents"], impact["cross_language_dependents"]
        assert "tests/service.test.ts" in impact["related_tests"], impact["related_tests"]
        assert impact["test_plan"] and impact["test_plan"][0]["priority"] in {"P0", "P1"}

    print("PASS: Codemium v0.8 Polyglot Intelligence JS/TS/TSX + cross-language impact/test fixture")


if __name__ == "__main__": main()
