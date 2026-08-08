#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROJECT_BRAIN = PLUGIN_ROOT / "engine" / "project_brain.py"
FINAL_STATUSES = {"captured", "reused", "none", "skipped_by_user_constraint", "enforcement_failed"}
ACTIVATION_RE = re.compile(r"(?i)(@codemium\b|\$cm(?:\b|-)|/codemium:cm\b|\bcodemium\b)")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def repository_root(cwd: str | Path) -> Path:
    root = Path(cwd).resolve()
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return Path(proc.stdout.strip()).resolve()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return root


def gate_dir(root: Path) -> Path:
    return root / ".codemium" / "runtime" / "persistence-gates"


def gate_key(session_id: str, turn_id: str) -> str:
    raw = f"{session_id}\0{turn_id}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:32]


def gate_path(root: Path, session_id: str, turn_id: str) -> Path:
    return gate_dir(root) / f"{gate_key(session_id, turn_id)}.json"


def run_project_brain(root: Path, *args: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(PROJECT_BRAIN), "--root", str(root), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        raise RuntimeError(detail[:1000])
    text = proc.stdout.strip()
    if not text:
        return {}
    data = json.loads(text)
    if not isinstance(data, dict):
        raise RuntimeError("Project Brain helper returned a non-object payload")
    return data


def forbids_all_workspace_writes(prompt: str) -> bool:
    text = " ".join(prompt.casefold().split())
    patterns = [
        r"\b(?:read[- ]?only|readonly)\s+(?:workspace|repository|repo|files?)\b",
        r"\b(?:do not|don't|dont|never)\s+(?:modify|change|edit|write|touch|create|delete)\s+(?:any|all)\s+(?:files?|workspace|repository|repo)\b",
        r"\bno\s+(?:file|workspace|repository|repo)\s+changes?\b",
        r"\bjangan\s+(?:ubah|mengubah|edit|menulis|tulis|sentuh|menyentuh|buat|membuat|hapus|menghapus)\s+(?:file|berkas|workspace|repository|repo)(?:\s+(?:apa\s*pun|apapun|mana\s*pun|manapun|semua))?\b",
        r"\bjangan\s+(?:ubah|mengubah)\s+(?:apa\s*pun|apapun)\s+(?:di|dalam)\s+(?:workspace|repo|repository)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def begin_gate(root: Path, session_id: str, turn_id: str) -> dict[str, Any]:
    path = gate_path(root, session_id, turn_id)
    current = read_json(path)
    if current and current.get("status") in FINAL_STATUSES:
        return current
    created_at = current.get("created_at") if current else now_iso()
    gate = {
        "schema_version": 1,
        "session_id": session_id,
        "turn_id": turn_id,
        "status": "pending",
        "stop_attempts": int((current or {}).get("stop_attempts", 0)),
        "created_at": created_at,
        "updated_at": now_iso(),
    }
    atomic_json(path, gate)
    return gate


def latest_pending_gate(root: Path, session_id: str, turn_id: str | None = None) -> tuple[Path, dict[str, Any]] | None:
    if turn_id:
        exact = gate_path(root, session_id, turn_id)
        data = read_json(exact)
        if data and data.get("status") == "pending":
            return exact, data
    directory = gate_dir(root)
    if not directory.exists():
        return None
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    for path in directory.glob("*.json"):
        data = read_json(path)
        if not data or data.get("session_id") != session_id or data.get("status") != "pending":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, path, data))
    if not candidates:
        return None
    _, path, data = max(candidates, key=lambda item: item[0])
    return path, data


def finalize_gate(root: Path, session_id: str, turn_id: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    path = gate_path(root, session_id, turn_id)
    gate = read_json(path)
    if not gate:
        raise ValueError("No pending persistence gate exists for this session/turn")
    if gate.get("status") in FINAL_STATUSES:
        return gate

    if entries:
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"knowledge entry {index + 1} must be an object")
            if not str(entry.get("source", "")).strip():
                raise ValueError(f"knowledge entry {index + 1} must include a source")
        capture = run_project_brain(
            root,
            "capture",
            "--entries",
            json.dumps(entries, ensure_ascii=False),
        )
        counts = capture.get("counts") if isinstance(capture.get("counts"), dict) else {}
        added = int(counts.get("added", 0))
        reused = int(counts.get("reused", 0))
        status = "captured" if added > 0 else "reused" if reused > 0 else "none"
    else:
        capture = {"status": "none", "counts": {"added": 0, "reused": 0}}
        status = "none"

    gate.update(
        {
            "status": status,
            "updated_at": now_iso(),
            "capture": capture,
        }
    )
    atomic_json(path, gate)
    return gate


def finalization_instruction(root: Path, gate: dict[str, Any]) -> str:
    hook = Path(__file__).resolve()
    session_id = str(gate.get("session_id", ""))
    turn_id = str(gate.get("turn_id", ""))
    return (
        "Project Brain persistence is still pending for this task. Before finishing, classify durable knowledge and finalize the gate. "
        "Run the hook helper with the exact pending session/turn IDs. Use an empty JSON array when the task produced no durable project fact; "
        "otherwise pass only durable source-backed decisions, constraints, interfaces, patterns, or known bugs/risks. Do not invent entries.\n\n"
        f'python "{hook}" finalize --root "{root}" --session-id "{session_id}" --turn-id "{turn_id}" --knowledge-json \'[]\'\n\n'
        "For non-empty knowledge, replace [] with a JSON array of objects containing kind, text, source, and optional why/risk. "
        "After the command succeeds, finish the task normally."
    )


def emit(payload: dict[str, Any] | None) -> None:
    if payload:
        print(json.dumps(payload, ensure_ascii=False))


def handle_user_prompt(data: dict[str, Any]) -> None:
    prompt = str(data.get("prompt", ""))
    if not ACTIVATION_RE.search(prompt):
        return

    if forbids_all_workspace_writes(prompt):
        emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": (
                        "The user explicitly prohibited all file/workspace changes. Treat Project Brain persistence as skipped by user constraint. "
                        "Do not create or update .codemium/ and do not claim persistence succeeded."
                    ),
                }
            }
        )
        return

    root = repository_root(str(data.get("cwd") or Path.cwd()))
    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")
    if not session_id or not turn_id:
        emit({"systemMessage": "Codemium Project Brain hook received no session/turn id; persistence enforcement is unavailable for this turn."})
        return

    try:
        run_project_brain(root, "init")
        gate = begin_gate(root, session_id, turn_id)
    except Exception as exc:  # hook must fail visibly rather than block the user's prompt
        emit(
            {
                "systemMessage": f"Codemium Project Brain initialization failed: {str(exc)[:500]}",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "Project Brain persistence is unavailable for this turn. Do not claim that durable knowledge was saved.",
                },
            }
        )
        return

    if gate.get("status") in FINAL_STATUSES:
        return
    hook = Path(__file__).resolve()
    context = (
        "A deterministic Project Brain persistence gate is active for this repository-bound task. Source/product code may remain read-only while .codemium bookkeeping is updated. "
        "Complete the investigation/implementation first. Before your final answer, finalize this exact gate by running:\n\n"
        f'python "{hook}" finalize --root "{root}" --session-id "{session_id}" --turn-id "{turn_id}" --knowledge-json \'[]\'\n\n'
        "Use [] only if no durable project knowledge was learned. Otherwise replace it with a JSON array containing only durable source-backed facts with kind, text, source, and optional why/risk. "
        "The Stop hook will continue the turn if this gate is still pending."
    )
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }
    )


def handle_stop(data: dict[str, Any]) -> None:
    root = repository_root(str(data.get("cwd") or Path.cwd()))
    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")
    if not session_id:
        return

    pending = latest_pending_gate(root, session_id, turn_id or None)
    if not pending:
        return
    path, gate = pending
    attempts = int(gate.get("stop_attempts", 0)) + 1
    gate["stop_attempts"] = attempts
    gate["updated_at"] = now_iso()

    if attempts <= 2:
        atomic_json(path, gate)
        emit({"decision": "block", "reason": finalization_instruction(root, gate)})
        return

    gate["status"] = "enforcement_failed"
    gate["updated_at"] = now_iso()
    gate["failure_reason"] = "Persistence gate remained pending after two Stop continuations."
    atomic_json(path, gate)
    emit(
        {
            "systemMessage": (
                "Codemium Project Brain persistence could not be finalized after two continuation attempts. "
                "The turn is being allowed to stop to avoid a loop; do not treat persistence as successful."
            )
        }
    )


def handle_hook() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        emit({"systemMessage": f"Codemium hook received invalid JSON: {exc}"})
        return
    if not isinstance(payload, dict):
        return
    event = str(payload.get("hook_event_name", ""))
    if event == "UserPromptSubmit":
        handle_user_prompt(payload)
    elif event == "Stop":
        handle_stop(payload)


def cli_finalize(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Finalize a Codemium Project Brain persistence gate")
    parser.add_argument("finalize", nargs="?")
    parser.add_argument("--root", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--knowledge-json", required=True, help="JSON array of durable source-backed knowledge; use [] for none")
    ns = parser.parse_args(argv)
    try:
        entries = json.loads(ns.knowledge_json)
        if not isinstance(entries, list):
            raise ValueError("--knowledge-json must be a JSON array")
        gate = finalize_gate(Path(ns.root).resolve(), ns.session_id, ns.turn_id, entries)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "finalize":
        return cli_finalize(sys.argv[1:])
    handle_hook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
