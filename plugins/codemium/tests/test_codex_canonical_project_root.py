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


def call_hook(payload: dict[str, object], cwd: Path) -> dict[str, object] | None:
    proc = run(sys.executable, DISPATCH, cwd=cwd, stdin=json.dumps(payload))
    text = proc.stdout.strip()
    return json.loads(text) if text else None


def payload(event: str, cwd: Path, session: str, turn: str, **extra: object) -> dict[str, object]:
    data: dict[str, object] = {
        "session_id": session,
        "turn_id": turn,
        "cwd": str(cwd),
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


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        local = temp / "local"
        worktree = temp / "managed-worktree"
        local.mkdir()

        run("git", "init", "-q", cwd=local)
        run("git", "config", "user.email", "codemium@example.invalid", cwd=local)
        run("git", "config", "user.name", "Codemium Test", cwd=local)
        (local / "README.md").write_text("fixture\n", encoding="utf-8")
        run("git", "add", "README.md", cwd=local)
        run("git", "commit", "-q", "-m", "fixture", cwd=local)
        run("git", "worktree", "add", "--detach", str(worktree), "HEAD", cwd=local)

        # Emulate memory created by v0.6.4 inside a disposable Codex worktree.
        capture(
            worktree,
            [
                {
                    "kind": "bug",
                    "text": "Blocking is keyed by seller plus visitorId, so a new browser identity can bypass it.",
                    "source": "src/chat/blocking.ts:42",
                    "risk": "high",
                }
            ],
        )
        assert (worktree / ".codemium").exists()
        assert not (local / ".codemium").exists()

        memory = call_hook(
            payload(
                "UserPromptSubmit",
                worktree,
                "session-memory",
                "turn-memory",
                prompt=(
                    "@Codemium berdasarkan hanya Project Brain yang sudah tersimpan, jelaskan apa yang diketahui "
                    "tentang sistem pemblokiran pengguna. Jangan scan ulang repository. Jangan ubah source code."
                ),
            ),
            worktree,
        )
        assert memory is not None
        context = str(memory["hookSpecificOutput"]["additionalContext"])
        assert "CODEMIUM MEMORY RETRIEVAL MODE" in context
        assert "visitorId" in context

        # The legacy worktree brain must be migrated to the Local checkout and
        # all new transient state must be anchored there.
        assert (local / ".codemium").exists()
        canonical_bugs = read_jsonl(local / ".codemium" / "registry" / "bugs.jsonl")
        assert any("visitorId" in str(item.get("text", "")) for item in canonical_bugs)
        canonical_gates = list((local / ".codemium" / "runtime" / "persistence-gates").glob("*.json"))
        assert len(canonical_gates) == 1
        memory_gate = json.loads(canonical_gates[0].read_text(encoding="utf-8"))
        location = memory_gate["project_location"]
        assert Path(location["canonical_project_root"]).resolve() == local.resolve()
        assert Path(location["runtime_git_root"]).resolve() == worktree.resolve()
        assert location["is_linked_worktree"] is True
        assert location["migration_status"] in {"copied", "merged"}

        location_file = json.loads(
            (local / ".codemium" / "runtime" / "project-location.json").read_text(encoding="utf-8")
        )
        assert Path(location_file["canonical_project_root"]).resolve() == local.resolve()
        assert Path(location_file["last_runtime_git_root"]).resolve() == worktree.resolve()
        assert location_file["is_linked_worktree"] is True

        # A normal engineering task from the same worktree must open its pending
        # persistence gate in the same canonical Local Project Brain.
        normal = call_hook(
            payload(
                "UserPromptSubmit",
                worktree,
                "session-normal",
                "turn-normal",
                prompt="@Codemium investigate blocking. Do not modify source code.",
            ),
            worktree,
        )
        assert normal is not None
        normal_context = str(normal["hookSpecificOutput"]["additionalContext"])
        assert "canonical project root" in normal_context
        gates_after = list((local / ".codemium" / "runtime" / "persistence-gates").glob("*.json"))
        assert len(gates_after) == 2

        # A Local retrieval reuses the exact same durable brain without creating
        # a second Project Brain tree. Use an explicit stored identifier here so
        # this assertion tests root sharing rather than bilingual ranking quality.
        local_memory = call_hook(
            payload(
                "UserPromptSubmit",
                local,
                "session-local",
                "turn-local",
                prompt=(
                    "@Codemium berdasarkan hanya Project Brain yang sudah tersimpan, jelaskan apa yang diketahui "
                    "tentang visitorId dan browser blocking. Jangan scan ulang repository."
                ),
            ),
            local,
        )
        assert local_memory is not None
        assert "visitorId" in str(local_memory["hookSpecificOutput"]["additionalContext"])

    print("PASS: canonical Project Brain root across Local and linked worktree")


if __name__ == "__main__":
    main()
