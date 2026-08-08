#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
HOOK = PLUGIN / "hooks" / "project_brain_gate.py"
ENGINE = PLUGIN / "engine" / "project_brain.py"


def run(*args: object, cwd: Path | None = None, stdin: str | None = None, expect: int = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
    )
    if proc.returncode != expect:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise AssertionError(f"command returned {proc.returncode}, expected {expect}: {args}")
    return proc


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-q", cwd=root)


def hook_payload(event: str, root: Path, session: str, turn: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "session_id": session,
        "turn_id": turn,
        "cwd": str(root),
        "hook_event_name": event,
        "model": "test-model",
        "permission_mode": "default",
    }
    payload.update(extra)
    return payload


def call_hook(payload: dict[str, object], root: Path) -> dict[str, object] | None:
    proc = run(sys.executable, HOOK, cwd=root, stdin=json.dumps(payload))
    text = proc.stdout.strip()
    return json.loads(text) if text else None


def finalize(root: Path, session: str, turn: str, knowledge: list[dict[str, object]]) -> dict[str, object]:
    proc = run(
        sys.executable,
        HOOK,
        "finalize",
        "--root",
        root,
        "--session-id",
        session,
        "--turn-id",
        turn,
        "--knowledge-json",
        json.dumps(knowledge),
        cwd=root,
    )
    return json.loads(proc.stdout)


def brain_status(root: Path) -> dict[str, object]:
    proc = run(sys.executable, ENGINE, "--root", root, "status", cwd=root)
    return json.loads(proc.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # Source-code read-only still allows .codemium state, and the first Stop
        # cannot finish until the turn explicitly finalizes durable knowledge.
        root = base / "repo"
        init_repo(root)
        prompt = hook_payload(
            "UserPromptSubmit",
            root,
            "session-a",
            "turn-a",
            prompt="@Codemium investigate the auth bug. Jangan ubah source code.",
        )
        start = call_hook(prompt, root)
        assert start is not None
        context = start["hookSpecificOutput"]["additionalContext"]
        assert "persistence gate is active" in str(context).lower()
        assert (root / ".codemium" / "PROJECT.md").exists()
        status = brain_status(root)
        assert all(value == 0 for value in status["registries"].values())

        first_stop = call_hook(hook_payload("Stop", root, "session-a", "turn-a"), root)
        assert first_stop is not None and first_stop["decision"] == "block"
        assert "finalize" in str(first_stop["reason"]).lower()

        knowledge = [
            {
                "kind": "bug",
                "text": "The auth block is keyed by visitorId and can be bypassed when a new browser identity is issued.",
                "source": "src/auth/blocking.ts",
                "risk": "medium",
            }
        ]
        captured = finalize(root, "session-a", "turn-a", knowledge)
        assert captured["status"] == "captured"
        assert captured["capture"]["counts"] == {"added": 1, "reused": 0}
        after_capture_stop = call_hook(hook_payload("Stop", root, "session-a", "turn-a"), root)
        assert after_capture_stop is None
        status = brain_status(root)
        assert status["registries"]["bug"] == 1

        # A later Codemium turn can reuse an equivalent durable entry instead of
        # duplicating it, proving that the gate is tied to Project Brain storage.
        call_hook(
            hook_payload(
                "UserPromptSubmit",
                root,
                "session-b",
                "turn-b",
                prompt="@Codemium based on Project Brain, explain the known auth blocking issue.",
            ),
            root,
        )
        reused = finalize(root, "session-b", "turn-b", knowledge)
        assert reused["status"] == "reused"
        assert reused["capture"]["counts"] == {"added": 0, "reused": 1}
        assert brain_status(root)["registries"]["bug"] == 1

        # Explicitly classifying a turn as having no durable knowledge also
        # satisfies the deterministic gate without inventing entries.
        call_hook(
            hook_payload(
                "UserPromptSubmit",
                root,
                "session-c",
                "turn-c",
                prompt="@Codemium tell me whether the current working tree is clean.",
            ),
            root,
        )
        none = finalize(root, "session-c", "turn-c", [])
        assert none["status"] == "none"
        assert call_hook(hook_payload("Stop", root, "session-c", "turn-c"), root) is None

        # An explicit prohibition on every workspace/file write must prevent
        # even Project Brain initialization.
        frozen = base / "frozen"
        init_repo(frozen)
        skipped = call_hook(
            hook_payload(
                "UserPromptSubmit",
                frozen,
                "session-d",
                "turn-d",
                prompt="@Codemium inspect this repo, but do not modify any files or workspace state.",
            ),
            frozen,
        )
        assert skipped is not None
        assert "skipped by user constraint" in str(skipped["hookSpecificOutput"]["additionalContext"])
        assert not (frozen / ".codemium").exists()

        # Merely enabling the plugin must not mutate unrelated Codex turns.
        unrelated = base / "unrelated"
        init_repo(unrelated)
        assert call_hook(
            hook_payload(
                "UserPromptSubmit",
                unrelated,
                "session-e",
                "turn-e",
                prompt="Explain what this repository does.",
            ),
            unrelated,
        ) is None
        assert not (unrelated / ".codemium").exists()

        # The Stop hook retries persistence twice, then fails open visibly rather
        # than creating an infinite continuation loop.
        retry = base / "retry"
        init_repo(retry)
        call_hook(
            hook_payload(
                "UserPromptSubmit",
                retry,
                "session-f",
                "turn-f",
                prompt="@Codemium investigate this repository.",
            ),
            retry,
        )
        assert call_hook(hook_payload("Stop", retry, "session-f", "turn-f"), retry)["decision"] == "block"
        assert call_hook(hook_payload("Stop", retry, "session-f", "turn-f"), retry)["decision"] == "block"
        third = call_hook(hook_payload("Stop", retry, "session-f", "turn-f"), retry)
        assert third is not None and "could not be finalized" in str(third["systemMessage"])
        gate_files = list((retry / ".codemium" / "runtime" / "persistence-gates").glob("*.json"))
        assert len(gate_files) == 1
        gate = json.loads(gate_files[0].read_text(encoding="utf-8"))
        assert gate["status"] == "enforcement_failed"

    print("PASS: Codex lifecycle hook enforces Project Brain persistence")


if __name__ == "__main__":
    main()
