#!/usr/bin/env python3
"""Host-agnostic Codemium core fixture for Project Brain + Structural Intelligence."""
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
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); (root / "src/auth").mkdir(parents=True); (root / "tests").mkdir()
        (root / "src/auth/session.py").write_text(
            "class SessionStore:\n    def save(self, token):\n        return token\n\n"
            "def refresh_session(token):\n    store = SessionStore()\n    return store.save(token)\n", encoding="utf-8")
        (root / "src/auth/controller.py").write_text(
            "from src.auth.session import refresh_session\n\ndef handle_refresh(token):\n    return refresh_session(token)\n", encoding="utf-8")
        (root / "src/ui.js").write_text("export function renderCard() { return mountCard(); }\n", encoding="utf-8")
        (root / "tests/test_session.py").write_text(
            "from src.auth.session import refresh_session\n\ndef test_refresh_session():\n    assert refresh_session('x') == 'x'\n", encoding="utf-8")
        run("git", "init", "-q", cwd=root); run("git", "config", "user.email", "fixture@example.com", cwd=root); run("git", "config", "user.name", "Fixture", cwd=root); run("git", "add", ".", cwd=root); run("git", "commit", "-qm", "initial", cwd=root)

        task = json.loads(run(sys.executable, ENGINE / "task_compiler.py", "--root", root, "--request", "Fix auth refresh bug that logs users out"))
        state = root / ".codemium"
        assert (state / "PROJECT.md").exists(); assert task["type"] == "FIX"; assert task["depth"] == "CRITICAL"; assert task["reasoning"]["reasoning_class"] == "frontier"
        ignore = (state / ".gitignore").read_text(encoding="utf-8")
        for item in ["runtime/", "repository/", "tasks/active.json", "tasks/completed/"]: assert item in ignore

        knowledge = json.dumps([
            {"kind": "constraint", "text": "Authentication refresh must preserve the current session boundary.", "source": "src/auth/session.py", "risk": "high"},
            {"kind": "bug", "text": "Missing refresh tokens can log users out unexpectedly.", "source": "src/auth/session.py", "risk": "high"},
        ])
        first_capture = json.loads(run(sys.executable, ENGINE / "project_brain.py", "--root", root, "capture", "--entries", knowledge))
        assert first_capture["counts"] == {"added": 2, "reused": 0}; assert first_capture["added"][0]["evidence"][0]["content_hash"]; assert first_capture["added"][0]["freshness"] == "FRESH"
        second_capture = json.loads(run(sys.executable, ENGINE / "project_brain.py", "--root", root, "capture", "--entries", knowledge)); assert second_capture["counts"] == {"added": 0, "reused": 2}

        first_build = json.loads(run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root))
        graph = json.loads((state / "repository/graph.json").read_text(encoding="utf-8"))
        assert graph["schema_version"] == 2; assert graph["file_count"] == 4; assert graph["node_count"] > graph["file_count"]; assert graph["edge_count"] > 0
        assert graph["coverage"]["python_ast_files"] == 3; assert graph["coverage"]["fallback_files"] == 1
        assert any(e["relation"] == "CALLS" and e["provenance"] == "RESOLVED" for e in graph["edges"]); assert any(e["relation"] == "TESTS" for e in graph["edges"]); assert first_build["incremental"]["parsed"] == 4
        second_build = json.loads(run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root)); assert second_build["incremental"]["parsed"] == 0; assert second_build["incremental"]["unchanged"] == 4

        callers = json.loads(run(sys.executable, ENGINE / "graph_query.py", "--root", root, "callers", "refresh_session")); assert any(x.get("node", {}).get("path") == "src/auth/controller.py" for x in callers)
        structural_task = json.loads(run(sys.executable, ENGINE / "task_compiler.py", "--root", root, "--request", "Fix refresh_session behavior")); assert structural_task["structural_risk"]["seed_nodes"]; assert structural_task["depth"] == "CRITICAL"
        ws = json.loads(run(sys.executable, ENGINE / "working_set.py", "--root", root, "--query", "refresh_session behavior", "--top", "6")); assert ws["graph_assisted"] is True
        selected = {x["path"] for x in ws["files"]}; assert {"src/auth/session.py", "src/auth/controller.py", "tests/test_session.py"}.issubset(selected)
        test_map = json.loads(run(sys.executable, ENGINE / "test_map.py", "build", "--root", root)); assert test_map["relationships"] >= 1
        tests_state = json.loads((state / "repository/tests.json").read_text(encoding="utf-8")); assert tests_state["schema_version"] == 2; assert "tests/test_session.py" in tests_state["mapping"]["src/auth/session.py"]

        (root / "src/auth/session.py").write_text(
            "class SessionStore:\n    def save(self, token):\n        return token\n\n"
            "def refresh_session(token):\n    if not token:\n        raise ValueError('token required')\n    store = SessionStore()\n    return store.save(token)\n", encoding="utf-8")
        impact = json.loads(run(sys.executable, ENGINE / "impact.py", "--root", root, "--git-diff")); assert impact["impact_mode"] == "structural"; assert "src/auth/controller.py" in impact["likely_dependents"]; assert "tests/test_session.py" in impact["related_tests"]; assert impact["blast_radius"] == "high"
        fresh = json.loads(run(sys.executable, ENGINE / "project_brain.py", "--root", root, "freshness")); assert fresh["summary"]["counts"]["NEEDS_REVALIDATION"] == 2
        health = json.loads(run(sys.executable, ENGINE / "health.py", "--root", root)); assert health["repository_graph"]["schema_version"] == 2; assert health["repository_graph"]["fresh_to_worktree"] is False; assert health["project_brain_freshness"]["NEEDS_REVALIDATION"] == 2
        modified_build = json.loads(run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root)); assert modified_build["incremental"]["modified"] == 1; assert modified_build["incremental"]["parsed"] == 1
        revalidated = json.loads(run(sys.executable, ENGINE / "project_brain.py", "--root", root, "revalidate", "--kind", "constraint", "--id", "C0001")); assert revalidated["freshness"] == "FRESH"

        (root / "src/ui.js").unlink(); deleted_build = json.loads(run(sys.executable, ENGINE / "repo_graph.py", "build", "--root", root)); assert deleted_build["incremental"]["deleted"] == 1
        graph_after_delete = json.loads((state / "repository/graph.json").read_text(encoding="utf-8")); assert not any(n.get("path") == "src/ui.js" for n in graph_after_delete["nodes"])

        miss = json.loads(run(sys.executable, ENGINE / "cache.py", "--root", root, "check", "--kind", "search", "--key", "refresh_session callers")); assert miss["hit"] is False
        run(sys.executable, ENGINE / "cache.py", "--root", root, "record", "--kind", "search", "--key", "refresh_session callers", "--result-ref", "E0001")
        hit = json.loads(run(sys.executable, ENGINE / "cache.py", "--root", root, "check", "--kind", "search", "--key", "refresh_session callers")); assert hit["hit"] is True

        fresh_root = root / "fresh-project"; fresh_root.mkdir()
        fresh_capture = json.loads(run(sys.executable, ENGINE / "project_brain.py", "--root", fresh_root, "capture", "--entries", json.dumps([{"kind": "pattern", "text": "Use repository-owned validation helpers."}]))); assert fresh_capture["counts"] == {"added": 1, "reused": 0}; assert (fresh_root / ".codemium/PROJECT.md").exists()

    print("PASS: Codemium core fixture + v0.7 Structural Intelligence & Evidence Bridge")


if __name__ == "__main__":
    main()
