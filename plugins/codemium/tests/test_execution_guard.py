#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ENGINE = PLUGIN / "engine"
GUARD = ENGINE / "execution_guard.py"


def run(*args, cwd=None, ok=True):
    p = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True)
    if ok and p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise AssertionError(f"command failed {p.returncode}: {args}")
    return p


def output(p):
    return json.loads(p.stdout)


def init_repo(root: Path) -> None:
    run("git", "init", "-q", cwd=root)
    run("git", "config", "user.email", "fixture@example.com", cwd=root)
    run("git", "config", "user.name", "Fixture", cwd=root)
    (root / "app.css").write_text(".menu { position: relative; }\n", encoding="utf-8")
    run("git", "add", ".", cwd=root)
    run("git", "commit", "-qm", "initial", cwd=root)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        init_repo(root)
        state = root / ".codemium/tasks"
        state.mkdir(parents=True)
        (state / "active.json").write_text(json.dumps({"id": "T-UI", "type": "FIX"}), encoding="utf-8")

        started = output(run(sys.executable, GUARD, "--root", root, "start"))
        assert started["status"]["task_id"] == "T-UI"
        assert started["status"]["task_type"] == "FIX"

        dom = output(
            run(
                sys.executable,
                GUARD,
                "--root",
                root,
                "observe",
                "--subject",
                "profile-dropdown",
                "--claim",
                "open",
                "--source",
                "dom",
                "--value",
                "true",
            )
        )
        assert dom["contradictions"] == []

        shot = output(
            run(
                sys.executable,
                GUARD,
                "--root",
                root,
                "observe",
                "--subject",
                "profile-dropdown",
                "--claim",
                "open",
                "--source",
                "screenshot",
                "--value",
                "false",
                "--stabilized",
                "no",
            )
        )
        assert shot["contradictions"], shot

        blocked = run(
            sys.executable,
            GUARD,
            "--root",
            root,
            "gate",
            "--action",
            "edit",
            "--target",
            "app.css",
            "--mutation",
            "--ui",
            "--basis",
            "evidence",
            ok=False,
        )
        assert blocked.returncode == 2, blocked.stdout
        blocked_json = output(blocked)
        assert blocked_json["allowed"] is False
        assert any("contradiction" in x for x in blocked_json["blockers"])
        assert any("unstabilized" in x for x in blocked_json["blockers"])

        stable = output(
            run(
                sys.executable,
                GUARD,
                "--root",
                root,
                "observe",
                "--subject",
                "profile-dropdown",
                "--claim",
                "open",
                "--source",
                "screenshot",
                "--value",
                "true",
                "--stabilized",
                "yes",
            )
        )
        assert stable["contradictions"] == []

        allowed = output(
            run(
                sys.executable,
                GUARD,
                "--root",
                root,
                "gate",
                "--action",
                "edit",
                "--target",
                "app.css",
                "--mutation",
                "--ui",
                "--basis",
                "evidence",
            )
        )
        assert allowed["allowed"] is True, allowed

        hypothesis = output(
            run(
                sys.executable,
                GUARD,
                "--root",
                root,
                "hypothesis",
                "--statement",
                "The dropdown is behind a higher stacking context",
                "--expected-evidence",
                "computed z-index is lower than overlay",
                "--status",
                "rejected",
            )
        )
        hid = hypothesis["hypothesis"]["id"]

        rejected = run(
            sys.executable,
            GUARD,
            "--root",
            root,
            "gate",
            "--action",
            "inspect",
            "--target",
            "stacking-context",
            "--hypothesis-id",
            hid,
            ok=False,
        )
        assert rejected.returncode == 2
        assert "rejected" in " ".join(output(rejected)["blockers"])

        run(
            sys.executable,
            GUARD,
            "--root",
            root,
            "observe",
            "--subject",
            "profile-dropdown",
            "--claim",
            "computed-z-index",
            "--source",
            "computed-style",
            "--value",
            "1000",
        )
        revisit = output(
            run(
                sys.executable,
                GUARD,
                "--root",
                root,
                "gate",
                "--action",
                "inspect",
                "--target",
                "stacking-context",
                "--hypothesis-id",
                hid,
            )
        )
        assert revisit["allowed"] is True, revisit

        run(
            sys.executable,
            GUARD,
            "--root",
            root,
            "record",
            "--action",
            "deploy",
            "--target",
            "preview",
            "--outcome",
            "required_verification",
        )
        repeat = run(
            sys.executable,
            GUARD,
            "--root",
            root,
            "gate",
            "--action",
            "deploy",
            "--target",
            "preview",
            ok=False,
        )
        assert repeat.returncode == 2
        assert "no evidence or repository-state delta" in " ".join(output(repeat)["blockers"])

        run(
            sys.executable,
            GUARD,
            "--root",
            root,
            "record",
            "--action",
            "inspect",
            "--target",
            "render-timing",
            "--outcome",
            "no_gain",
        )
        status = output(run(sys.executable, GUARD, "--root", root, "status"))
        assert status["waste_actions"] == 1
        assert status["blocked_actions"] >= 3
        assert status["law"] == "Every action must buy information or produce the solution."

    print("PASS: v0.10 Execution Intelligence fixture")


if __name__ == "__main__":
    main()
