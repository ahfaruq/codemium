#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
DISPATCH = PLUGIN / "hooks" / "project_brain_dispatch.py"
ENGINE = PLUGIN / "engine" / "project_brain.py"


def run(*args: object, cwd: Path | None = None, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise AssertionError(f"command returned {proc.returncode}: {args}")
    return proc


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)


def call_hook(payload: dict[str, object], root: Path) -> dict[str, object] | None:
    proc = run(sys.executable, DISPATCH, cwd=root, stdin=json.dumps(payload))
    text = proc.stdout.strip()
    return json.loads(text) if text else None


def payload(event: str, root: Path, session: str, turn: str, **extra: object) -> dict[str, object]:
    data: dict[str, object] = {
        "session_id": session,
        "turn_id": turn,
        "cwd": str(root),
        "hook_event_name": event,
        "model": "test-model",
        "permission_mode": "default",
    }
    data.update(extra)
    return data


def capture(root: Path, entries: list[dict[str, object]]) -> None:
    run(
        sys.executable,
        ENGINE,
        "--root",
        root,
        "capture",
        "--entries",
        json.dumps(entries),
        cwd=root,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        init_repo(root)
        capture(
            root,
            [
                {
                    "kind": "bug",
                    "text": "User blocking is keyed by seller userId plus visitorId, so a new browser identity can bypass the block.",
                    "source": "src/chat/blocking.ts:42",
                    "risk": "high",
                },
                {
                    "kind": "constraint",
                    "text": "Public chat requires an authenticated Cus.my account session.",
                    "source": "src/chat/route.ts:17",
                },
            ],
        )

        start = call_hook(
            payload(
                "UserPromptSubmit",
                root,
                "session-fast",
                "turn-fast",
                prompt=(
                    "@Codemium berdasarkan hanya Project Brain yang sudah tersimpan, jelaskan apa yang diketahui "
                    "tentang sistem pemblokiran pengguna. Jangan scan ulang repository."
                ),
            ),
            root,
        )
        assert start is not None
        context = str(start["hookSpecificOutput"]["additionalContext"])
        assert "CODEMIUM MEMORY RETRIEVAL MODE" in context
        assert "overrides the normal Codemium engineering lifecycle" in context
        assert "Use minimum reasoning" in context
        assert "visitorId" in context
        assert "Do not classify task/depth" in context
        assert "inspect git" in context
        assert len(context) < 5000

        gates = list((root / ".codemium" / "runtime" / "persistence-gates").glob("*.json"))
        assert len(gates) == 1
        gate_record = json.loads(gates[0].read_text(encoding="utf-8"))
        assert gate_record["status"] == "reused"
        assert gate_record["fast_path"] is True
        assert gate_record["memory_mode"] == "lightweight"
        assert gate_record["retrieval"]["matched"] >= 1
        assert Path(gate_record["project_location"]["canonical_project_root"]).resolve() == root.resolve()
        diagnostics = gate_record["diagnostics"]
        for key in (
            "root_resolve_ms",
            "registry_read_ms",
            "ranking_ms",
            "context_build_ms",
            "context_chars",
            "matched_entries",
            "total_active_entries",
            "prompt_epoch_ms",
            "gate_write_ms",
            "hook_total_ms",
            "canonical_project_root",
            "is_linked_worktree",
            "migration_status",
        ):
            assert key in diagnostics, key
        assert diagnostics["gate_write_ms"] >= 0
        assert diagnostics["hook_total_ms"] >= diagnostics["hook_total_before_gate_ms"]
        assert Path(diagnostics["canonical_project_root"]).resolve() == root.resolve()
        assert diagnostics["is_linked_worktree"] is False

        stop = call_hook(payload("Stop", root, "session-fast", "turn-fast"), root)
        assert stop == {}
        gate_after_stop = json.loads(gates[0].read_text(encoding="utf-8"))
        assert "host_turn_to_stop_ms" in gate_after_stop["diagnostics"]
        assert gate_after_stop["diagnostics"]["host_turn_to_stop_ms"] >= 0

        assert not (root / ".codemium" / "repository" / "graph.json").exists()
        assert not (root / ".codemium" / "tasks" / "active.json").exists()

        miss = call_hook(
            payload(
                "UserPromptSubmit",
                root,
                "session-miss",
                "turn-miss",
                prompt="@Codemium berdasarkan hanya Project Brain, apa yang diketahui tentang sistem pembayaran Stripe? Jangan scan ulang repository.",
            ),
            root,
        )
        assert miss is not None
        miss_context = str(miss["hookSpecificOutput"]["additionalContext"])
        assert "none are relevant" in miss_context
        assert "visitorId" not in miss_context

        normal = call_hook(
            payload(
                "UserPromptSubmit",
                root,
                "session-normal",
                "turn-normal",
                prompt="@Codemium investigate why blocking can be bypassed. Do not modify source code.",
            ),
            root,
        )
        assert normal is not None
        normal_context = str(normal["hookSpecificOutput"]["additionalContext"])
        assert "persistence gate is active" in normal_context.lower()

    print("PASS: Codex Project Brain lightweight retrieval mode")


if __name__ == "__main__":
    main()
