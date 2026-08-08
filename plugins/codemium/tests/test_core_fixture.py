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

        # A normal written task must initialize Project Brain automatically.
        task = json.loads(run(
            sys.executable, ENGINE / "task_compiler.py", "--root", root,
            "--request", "Fix auth refresh bug that logs users out"
        ))
        state = root / ".codemium"
        assert (state / "PROJECT.md").exists()
        assert task["type"] == "FIX"
        assert task["depth"] == "CRITICAL"
        assert task["reasoning"]["host"] == "generic"
        assert task["reasoning"]["reasoning_class"] == "frontier"
        assert task["reasoning"]["preferred_effort"] is None

        ignore = (state / ".gitignore").read_text(encoding="utf-8")
        for item in ["runtime/", "repository/", "tasks/active.json", "tasks/completed/"]:
            assert item in ignore

        profile = json.loads((state / "model-profile.json").read_text(encoding="utf-8"))
        assert profile["generic_reasoning"]["FAST"]["preferred_class"] == "economy"
        assert profile["generic_reasoning"]["CRITICAL"]["preferred_class"] == "frontier"

        # Batched durable capture must work without a separate init command and
        # must reuse equivalent ACTIVE entries instead of duplicating them.
        knowledge = json.dumps([
            {
                "kind": "constraint",
                "text": "Authentication refresh must preserve the current session boundary.",
                "source": "src/auth/session.py",
                "risk": "high",
            },
            {
                "kind": "bug",
                "text": "Missing refresh tokens can log users out unexpectedly.",
                "source": "src/auth/session.py",
                "risk": "high",
            },
        ])
        first_capture = json.loads(run(
            sys.executable, ENGINE / "project_brain.py", "--root", root,
            "capture", "--entries", knowledge
        ))
        assert first_capture["counts"] == {"added": 2, "reused": 0}
        second_capture = json.loads(run(
            sys.executable, ENGINE / "project_brain.py", "--root", root,
            "capture", "--entries", knowledge
        ))
        assert second_capture["counts"] == {"added": 0, "reused": 2}
        status = json.loads(run(
            sys.executable, ENGINE / "project_brain.py", "--root", root, "status"
        ))
        assert status["initialized"] is True
        assert status["registries"]["constraint"] == 1
        assert status["registries"]["bug"] == 1

        run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root)
        graph = json.loads((state / "repository/graph.json").read_text(encoding="utf-8"))
        assert graph["file_count"] == 2
        assert any("refresh_session" in f["symbols"] for f in graph["files"])

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

        # Capture itself must silently initialize state in a fresh repository.
        fresh = root / "fresh-project"
        fresh.mkdir()
        fresh_capture = json.loads(run(
            sys.executable, ENGINE / "project_brain.py", "--root", fresh,
            "capture", "--entries", json.dumps([
                {"kind": "pattern", "text": "Use repository-owned validation helpers."}
            ])
        ))
        assert fresh_capture["counts"] == {"added": 1, "reused": 0}
        assert (fresh / ".codemium/PROJECT.md").exists()

    print("PASS: host-agnostic Codemium core fixture + automatic Project Brain persistence")


if __name__ == "__main__":
    main()
