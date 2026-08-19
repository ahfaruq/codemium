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


def write_state(root: Path, task: dict, graph: dict) -> None:
    state = root / ".codemium"
    (state / "tasks").mkdir(parents=True)
    (state / "repository").mkdir()
    (state / "tasks/active.json").write_text(json.dumps(task), encoding="utf-8")
    (state / "repository/graph.json").write_text(json.dumps(graph), encoding="utf-8")


def main() -> None:
    # Introduced/worsened fixture: task scope, cleanup classification, line smells,
    # dependency delta, duplicate implementation, single-use forwarder, adjudication,
    # and untracked source files must all be visible to the gate.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        init_repo(root)
        (root / "src/utils.py").write_text("def normalize_value(x):\n    return x\n", encoding="utf-8")
        (root / "src/service.py").write_text(
            "def process(x):\n    return x\n\n"
            "def pass_through(x):\n    return x\n",
            encoding="utf-8",
        )
        (root / "src/cleanup.py").write_text("OLD_FLAG = True\n", encoding="utf-8")
        (root / "src/unrelated.py").write_text("def untouched():\n    return 1\n", encoding="utf-8")
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
        (root / "src/cleanup.py").write_text("OLD_FLAG = False\n", encoding="utf-8")
        (root / "src/unrelated.py").write_text("def untouched():\n    return 2\n", encoding="utf-8")
        (root / "src/new_helper.py").write_text("def new_helper():\n    return True\n", encoding="utf-8")
        (root / "package.json").write_text(
            json.dumps({"dependencies": {"left-pad": "1.3.0"}}, indent=2) + "\n", encoding="utf-8"
        )

        task = {
            "working_set": ["src/service.py", "package.json"],
            "cleanup_set": ["src/cleanup.py"],
        }
        graph = {
            "files": [
                {"path": "src/service.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
                {"path": "src/utils.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
                {"path": "src/cleanup.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
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
        write_state(root, task, graph)

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
        assert report["changed_files"] == 5, report["surface_classification"]
        assert report["surfaces"]["cleanup"] == 1
        assert report["surface_classification"]["src/cleanup.py"]["class"] == "CLEANUP"
        assert report["surfaces"]["unjustified"] == 2
        assert report["surface_classification"]["src/new_helper.py"]["class"] == "UNJUSTIFIED"
        assert report["scoreable"] is True and report["risk_score"] is not None
        assert report["underengineering_gate"]["status"] == "pass"
        duplicate = next(f for f in report["findings"] if f["rule"] == "DUPLICATE_IMPLEMENTATION")
        forwarder = next(f for f in report["findings"] if f["rule"] == "SINGLE_USE_FORWARDER" and f.get("symbol") == "pass_through")
        assert duplicate["provenance"] == "introduced", duplicate
        assert forwarder["provenance"] == "worsened", forwarder
        assert set(report["finding_provenance"]) == {"introduced", "worsened", "pre_existing", "unknown"}

        decisions = {"schema_version": 1, "decisions": []}
        for finding in report["findings"]:
            if finding["rule"] not in {"UNJUSTIFIED_SCOPE", "UNJUSTIFIED_DEPENDENCY", "DUPLICATE_IMPLEMENTATION"}:
                continue
            evidence_path = finding["path"] if (root / finding["path"]).exists() else "src/service.py"
            decisions["decisions"].append({
                "rule": finding["rule"],
                "path": finding["path"],
                "line": finding.get("line"),
                "symbol": finding.get("symbol"),
                "decision": "JUSTIFIED",
                "reason": "Source and task evidence show this surface is required for the requested behavior.",
                "evidence": [{"kind": "source", "path": evidence_path}],
            })
        p = run(
            sys.executable,
            ENGINE / "slop_guard.py",
            "--root",
            root,
            "--base",
            "HEAD",
            "--adjudications",
            json.dumps(decisions),
            "--json",
        )
        adjudicated = json.loads(p.stdout)
        assert adjudicated["adjudication"]["accepted"] == len(decisions["decisions"]), adjudicated["adjudication"]
        assert all(
            (f.get("adjudication") or {}).get("status") == "accepted"
            for f in adjudicated["findings"]
            if f["rule"] in {"UNJUSTIFIED_SCOPE", "UNJUSTIFIED_DEPENDENCY", "DUPLICATE_IMPLEMENTATION"}
        )
        assert adjudicated["status"] == "review", adjudicated

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

    # Pre-existing structural debt is explicit provenance and does not become a
    # blocker merely because the task touched the existing function.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        init_repo(root)
        (root / "src/a.py").write_text("def same(x):\n    return x\n", encoding="utf-8")
        (root / "src/b.py").write_text("def same(x):\n    return x\n", encoding="utf-8")
        commit(root)
        (root / "src/b.py").write_text("def same(x):\n    return x + 1\n", encoding="utf-8")
        graph = {
            "files": [
                {"path": "src/a.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
                {"path": "src/b.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
            ],
            "nodes": [
                {"id": "s:a:same", "type": "SYMBOL", "subtype": "function", "label": "same", "qualified_name": "same", "path": "src/a.py", "line_start": 1, "line_end": 2},
                {"id": "s:b:same", "type": "SYMBOL", "subtype": "function", "label": "same", "qualified_name": "same", "path": "src/b.py", "line_start": 1, "line_end": 2},
            ],
            "edges": [],
        }
        write_state(root, {"working_set": ["src/b.py"]}, graph)
        p = run(sys.executable, ENGINE / "slop_guard.py", "--root", root, "--base", "HEAD", "--json")
        report = json.loads(p.stdout)
        duplicate = next(f for f in report["findings"] if f["rule"] == "DUPLICATE_IMPLEMENTATION")
        assert duplicate["provenance"] == "pre_existing", duplicate
        assert report["status"] == "pass", report

    # Underengineering fixture spans protected complexity classes. Removing these
    # signals must force review, while adding them is not itself an Anti-Slop failure.
    protected_lines = [
        "authorize(user)",
        "validate(payload)",
        "sanitize(payload)",
        "rate_limit(user)",
        "transaction.begin()",
        "lock.acquire()",
        "idempotency_key = key",
        "retry(request)",
        "migration.apply()",
        "compatibility_shim()",
        "integrity_check()",
        "csrf_check()",
    ]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        init_repo(root)
        before = "def guarded():\n" + "".join(f"    {line}\n" for line in protected_lines) + "    return True\n"
        (root / "src/safety.py").write_text(before, encoding="utf-8")
        commit(root)
        (root / "src/safety.py").write_text("def guarded():\n    return True\n", encoding="utf-8")
        graph = {
            "files": [
                {"path": "src/safety.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}}
            ],
            "nodes": [],
            "edges": [],
        }
        write_state(root, {"working_set": ["src/safety.py"]}, graph)
        p = run(sys.executable, ENGINE / "slop_guard.py", "--root", root, "--base", "HEAD", "--json")
        report = json.loads(p.stdout)
        assert report["underengineering_gate"]["status"] == "review_required", report
        assert len(report["protected_complexity"]["removed"]) >= 10, report["protected_complexity"]
        assert report["status"] == "review", report
        assert report["risk_score"] is None and report["scoreable"] is False

    # Duplicate detection must stay high precision. Same-named methods on unrelated
    # classes are common and must not trigger the blocking duplicate rule.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        init_repo(root)
        (root / "src/a.py").write_text(
            "class A:\n    def save(self, value):\n        return value\n",
            encoding="utf-8",
        )
        (root / "src/b.py").write_text("class B:\n    pass\n", encoding="utf-8")
        commit(root)
        (root / "src/b.py").write_text(
            "class B:\n    def save(self, value):\n        return value\n",
            encoding="utf-8",
        )
        graph = {
            "files": [
                {"path": "src/a.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
                {"path": "src/b.py", "language": "python", "is_test": False, "parser": "python-ast", "capabilities": {"symbols": True}},
            ],
            "nodes": [
                {"id": "s:a:save", "type": "SYMBOL", "subtype": "method", "label": "save", "qualified_name": "A.save", "path": "src/a.py", "line_start": 2, "line_end": 3},
                {"id": "s:b:save", "type": "SYMBOL", "subtype": "method", "label": "save", "qualified_name": "B.save", "path": "src/b.py", "line_start": 2, "line_end": 3},
            ],
            "edges": [],
        }
        write_state(root, {"working_set": ["src/b.py"]}, graph)
        p = run(sys.executable, ENGINE / "slop_guard.py", "--root", root, "--base", "HEAD", "--json")
        report = json.loads(p.stdout)
        duplicate_methods = [f for f in report["findings"] if f["rule"] == "DUPLICATE_IMPLEMENTATION" and f.get("symbol") == "save"]
        assert duplicate_methods == [], duplicate_methods

    print("PASS: Codemium v0.9 Slop Guard provenance + adjudication + cleanup + protected-complexity fixture")


if __name__ == "__main__":
    main()
