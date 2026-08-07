#!/usr/bin/env python3
"""Host-agnostic Codemium core fixture.

No plugin/extension packaging and no host-specific reasoning mapping is tested here.
"""
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
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise AssertionError(f"command failed {p.returncode}: {args}")
    return p.stdout


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src/auth").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "src/auth/session.py").write_text(
            'def refresh_session(token):\n    return {"token": token}\n', encoding="utf-8"
        )
        (root / "tests/test_session.py").write_text(
            'from src.auth.session import refresh_session\n\n'
            'def test_refresh_session():\n'
            '    assert refresh_session("x")["token"] == "x"\n',
            encoding="utf-8",
        )
        run("git", "init", "-q", cwd=root)
        run("git", "config", "user.email", "fixture@example.com", cwd=root)
        run("git", "config", "user.name", "Fixture", cwd=root)
        run("git", "add", ".", cwd=root)
        run("git", "commit", "-qm", "initial", cwd=root)

        run(sys.executable, ENGINE / "project_brain.py", "--root", root, "init")
        state = root / ".codemium"
        assert (state / "PROJECT.md").exists()
        ignore = (state / ".gitignore").read_text(encoding="utf-8")
        for item in ["runtime/", "repository/", "tasks/active.json", "tasks/completed/"]:
            assert item in ignore

        profile = json.loads((state / "model-profile.json").read_text(encoding="utf-8"))
        assert profile["generic_reasoning"]["FAST"]["preferred_class"] == "economy"
        assert profile["generic_reasoning"]["CRITICAL"]["preferred_class"] == "frontier"

        run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root)
        graph = json.loads((state / "repository/graph.json").read_text(encoding="utf-8"))
        assert graph["file_count"] == 2
        assert any("refresh_session" in f["symbols"] for f in graph["files"])

        task = json.loads(run(
            sys.executable, ENGINE / "task_compiler.py", "--root", root,
            "--request", "Fix auth refresh bug that logs users out"
        ))
        assert task["type"] == "FIX"
        assert task["depth"] == "CRITICAL"
        assert task["reasoning"]["host"] == "generic"
        assert task["reasoning"]["reasoning_class"] == "frontier"
        assert task["reasoning"]["preferred_effort"] is None

        ws = json.loads(run(
            sys.executable, ENGINE / "working_set.py", "--root", root,
            "--query", "auth refresh session", "--top", "5"
        ))
        assert any(x["path"] == "src/auth/session.py" for x in ws["files"])

        (root / "src/auth/session.py").write_text(
            'def refresh_session(token):\n'
            '    if not token:\n        raise ValueError("token required")\n'
            '    return {"token": token}\n',
            encoding="utf-8",
        )
        impact = json.loads(run(sys.executable, ENGINE / "impact.py", "--root", root, "--git-diff"))
        assert "src/auth/session.py" in impact["changed_files"]
        assert impact["blast_radius"] == "high"

        miss = json.loads(run(
            sys.executable, ENGINE / "cache.py", "--root", root,
            "check", "--kind", "search", "--key", "refresh_session callers"
        ))
        assert miss["hit"] is False
        run(
            sys.executable, ENGINE / "cache.py", "--root", root,
            "record", "--kind", "search", "--key", "refresh_session callers",
            "--result-ref", "E0001"
        )
        hit = json.loads(run(
            sys.executable, ENGINE / "cache.py", "--root", root,
            "check", "--kind", "search", "--key", "refresh_session callers"
        ))
        assert hit["hit"] is True

    print("PASS: host-agnostic Codemium core fixture")


if __name__ == "__main__":
    main()
