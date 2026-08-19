#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ENGINE = PLUGIN / "engine"


def run(*args, cwd=None, ok=True):
    p = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True)
    if ok and p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise AssertionError(f"command failed {p.returncode}: {args}")
    return p


def init_repo(root: Path) -> None:
    run("git", "init", "-q", cwd=root)
    run("git", "config", "user.email", "fixture@example.com", cwd=root)
    run("git", "config", "user.name", "Fixture", cwd=root)


def commit(root: Path, message: str = "initial") -> None:
    run("git", "add", ".", cwd=root)
    run("git", "commit", "-qm", message, cwd=root)


def main() -> None:
    # Introduced-slop fixture: task scope, line-level smells, dependency delta,
    # duplicate implementation, and single-use forwarder must all be evidence-backed.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        init_repo(root)
        (root / "src/utils.py").write_text("def normalize_value(x):\n    return x\n", encoding="utf-8")
        (root / "src/service.py").write_text("def process(x):\n    return x\n", encoding="utf-8")
        (root / "src/unrelated.py").write_text("def untouched():\n    return 1\n", encoding="utf-8")
        (root / "src/security.py").write_text(
            "def validate_token(token):\n    if not token:\n        raise ValueError('token')\n    return token\n",
            encoding="utf-8",
        )
        (root / "package.json").write_text(json.dumps({"dependencies": {}}, indent=2) + "\n", encoding="utf-8")
        commit(root)

        (root / "src/service.py").write_text(
            "from src.utils import normalize_value\n\n"
            "def process(x):\n    return x\n\n"
            "# Increment counter\n"
            "def normalize_value(x):\n    return x\n\n"
            "def pass_through(x):\n    return normalize_value(x)\n\n"
            "print(\"debug\")\n"
            "value = None  # type: ignore\n",
            encoding="utf-8",
        )
        (root / "src/unrelated.py").write_text("def untouched():\n    return 2\n", encoding="utf-8")
        (root / "package.json").write_text(
            json.dumps({"dependencies": {"left-pad": "1.3.0"}}, indent=2) + "\n", encoding="utf-8"
        )

        state = root / ".codemium"
        (state / "tasks").mkdir(parents=True)
        (state / "repository").mkdir()
        (state / "tasks/active.json").write_text(
            json.dumps({"working_set": ["src/service.py", "package.json"]}), encoding="utf-8"
        )
        graph = {
            "files": [
                {"path": "src/service.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
                {"path": "src/utils.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
                {"path": "src/unrelated.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
            ],
            "nodes": [
                {"id": "s:util:norm", "type": "SYMBOL", "subtype": "function", "label": "normalize_value", "qualified_name": "normalize_value", "path": "src/utils.py", "line_start": 1, "line_end": 2},
                {"id": "s:svc:process", "type": "SYMBOL", "subtype": "function", "label": "process", "qualified_name": "process", "path": "src/service.py", "line_start": 3, "line_end": 4},
                {"id": "s:svc:norm", "type": "SYMBOL", "subtype": "function", "label": "normalize_value", "qualified_name": "normalize_value", "path": "src/service.py", "line_start": 7, "line_end": 8},
                {"id": "s:svc:pass", "type": "SYMBOL", "subtype": "function", "label": "pass_through", "qualified_name": "pass_through", "path": "src/service.py", "line_start": 10, "line_end": 11},
                {"id": "s:unrelated", "type": "SYMBOL", "subtype": "function", "label": "untouched", "qualified_name": "untouched", "path": "src/unrelated.py", "line_start": 1, "line_end": 2},
            ],
            "edges": [
                {"source": "s:svc:pass", "target": "s:svc:norm", "relation": "CALLS", "provenance": "RESOLVED"}
            ],
        }
        (state / "repository/graph.json").write_text(json.dumps(graph), encoding="utf-8")

        p = run(sys.executable, ENGINE / "slop_guard.py", "--root", root, "--base", "HEAD", "--json")
        report = json.loads(p.stdout)
        rules = {f["rule"] for f in report["findings"]}
        for rule in [
            "UNJUSTIFIED_SCOPE",
            "DEBUG_RESIDUE",
            "UNJUSTIFIED_TYPE_ESCAPE",
            "NARRATIVE_COMMENT",
            "UNJUSTIFIED_DEPENDENCY",
            "DUPLICATE_IMPLEMENTATION",
            "SINGLE_USE_FORWARDER",
        ]:
            assert rule in rules, (rule, rules)
        assert report["status"] == "fail", report
        assert report["surfaces"]["unjustified"] == 1
        assert report["scoreable"] is True and report["risk_score"] is not None
        assert report["underengineering_gate"]["status"] == "pass"

        strict = run(
            sys.executable,
            ENGINE / "slop_guard.py",
            "--root",
            root,
            "--base",
            "HEAD",
            "--json",
            "--strict",
            ok=False,
        )
        assert strict.returncode == 3, strict.returncode

    # Underengineering fixture: removing protected complexity must force review,
    # and a score must not be fabricated when there are no scoreable added source lines.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        init_repo(root)
        (root / "src/security.py").write_text(
            "def validate_token(token):\n    if not token:\n        raise ValueError('token required')\n    return token\n",
            encoding="utf-8",
        )
        commit(root)
        (root / "src/security.py").write_text("def validate_token(token):\n    return token\n", encoding="utf-8")

        state = root / ".codemium"
        (state / "tasks").mkdir(parents=True)
        (state / "repository").mkdir()
        (state / "tasks/active.json").write_text(json.dumps({"working_set": ["src/security.py"]}), encoding="utf-8")
        graph = {
            "files": [
                {"path": "src/security.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}}
            ],
            "nodes": [],
            "edges": [],
        }
        (state / "repository/graph.json").write_text(json.dumps(graph), encoding="utf-8")

        p = run(sys.executable, ENGINE / "slop_guard.py", "--root", root, "--base", "HEAD", "--json")
        report = json.loads(p.stdout)
        assert report["underengineering_gate"]["status"] == "review_required", report
        assert report["status"] == "review", report
        assert report["risk_score"] is None and report["scoreable"] is False

    print("PASS: Codemium v0.9 Slop Guard deterministic + structural + underengineering fixture")


if __name__ == "__main__":
    main()
