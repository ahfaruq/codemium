#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

HOOK_DIR = Path(__file__).resolve().parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

import project_brain_gate as gate

REGISTRY_FILES = {
    "decision": "decisions.jsonl",
    "constraint": "constraints.jsonl",
    "interface": "interfaces.jsonl",
    "pattern": "patterns.jsonl",
    "bug": "bugs.jsonl",
}

PROJECT_BRAIN_RE = re.compile(r"(?i)(project\s+brain|\.codemium|project\s+intelligence)")
FAST_INTENT_RE = re.compile(
    r"(?i)(based\s+(?:only\s+)?on\s+project\s+brain|project\s+brain\s+only|"
    r"berdasarkan\s+(?:hanya\s+)?project\s+brain|project\s+brain\s+saja|"
    r"apa\s+yang\s+(?:sudah\s+)?diketahui|what\s+(?:does|do)\s+.*know|"
    r"do\s+not\s+(?:re)?scan|without\s+(?:re)?scanning|jangan\s+scan\s+ulang|"
    r"jangan\s+(?:melakukan\s+)?scan|stored\s+knowledge|pengetahuan\s+yang\s+(?:sudah\s+)?tersimpan)"
)

STOPWORDS = {
    "a", "about", "apa", "based", "berdasarkan", "brain", "dari", "di", "do", "does",
    "diketahui", "hanya", "ini", "jangan", "knowledge", "me", "on", "only", "project",
    "repository", "repo", "saja", "scan", "stored", "sudah", "tentang", "the", "ulang",
    "what", "yang", "know", "known", "please", "jelaskan", "explain", "codemium",
}

SYNONYMS = {
    "pemblokiran": {"block", "blocking", "blocked", "blocker"},
    "blokir": {"block", "blocking", "blocked"},
    "pengguna": {"user", "buyer", "account"},
    "akun": {"account", "user", "buyer"},
    "percakapan": {"conversation", "chat"},
    "chat": {"conversation", "message"},
    "pesan": {"message", "chat"},
    "browser": {"visitor", "visitorid", "token", "storage", "localstorage"},
    "visitor": {"browser", "visitorid", "token"},
    "blocking": {"block", "blocked", "pemblokiran", "blokir"},
    "blocked": {"block", "blocking", "pemblokiran", "blokir"},
    "user": {"pengguna", "akun", "account", "buyer"},
}

FAST_ENTRY_LIMIT = 6


def elapsed_ms(start_ns: int) -> float:
    return round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def active_entries(root: Path) -> list[dict[str, Any]]:
    registry = root / ".codemium" / "registry"
    out: list[dict[str, Any]] = []
    for kind, filename in REGISTRY_FILES.items():
        for item in read_jsonl(registry / filename):
            if str(item.get("status", "ACTIVE")).upper() != "ACTIVE":
                continue
            normalized = dict(item)
            normalized.setdefault("kind", kind)
            out.append(normalized)
    return out


def tokens(text: str) -> set[str]:
    raw = {x.casefold() for x in re.findall(r"[A-Za-z0-9_.-]+", text)}
    useful = {x for x in raw if len(x) > 2 and x not in STOPWORDS}
    expanded = set(useful)
    for token in list(useful):
        expanded.update(SYNONYMS.get(token, set()))
    return expanded


def rank_entries(prompt: str, entries: list[dict[str, Any]], limit: int = FAST_ENTRY_LIMIT) -> list[dict[str, Any]]:
    query = tokens(prompt)
    if not entries:
        return []
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, entry in enumerate(entries):
        searchable = " ".join(
            str(entry.get(key, ""))
            for key in ("text", "kind", "source", "why", "risk", "id")
        )
        hay = tokens(searchable)
        overlap = query & hay
        score = len(overlap) * 10
        text_cf = str(entry.get("text", "")).casefold()
        for term in query:
            if len(term) >= 5 and term in text_cf:
                score += 2
        if score > 0:
            scored.append((score, -index, entry))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [entry for _, _, entry in scored[:limit]]


def is_fast_path(prompt: str) -> bool:
    return bool(
        gate.ACTIVATION_RE.search(prompt)
        and PROJECT_BRAIN_RE.search(prompt)
        and FAST_INTENT_RE.search(prompt)
    )


def concise_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        key: entry[key]
        for key in ("id", "kind", "text", "source", "why", "risk", "created_at")
        if key in entry and entry[key] not in (None, "")
    }


def mark_fast_gate(
    root: Path,
    session_id: str,
    turn_id: str,
    matched: list[dict[str, Any]],
    *,
    total_entries: int,
    prompt_epoch_ms: int,
    diagnostics: dict[str, Any],
    project_location: dict[str, Any],
) -> dict[str, Any]:
    now = gate.now_iso()
    status = "reused" if matched else "none"
    current = {
        "schema_version": 1,
        "session_id": session_id,
        "turn_id": turn_id,
        "status": status,
        "stop_attempts": 0,
        "created_at": now,
        "updated_at": now,
        "fast_path": True,
        "memory_mode": "lightweight",
        "project_location": project_location,
        "retrieval": {
            "matched": len(matched),
            "total_active": total_entries,
            "entry_ids": [str(x.get("id", "")) for x in matched if x.get("id")],
        },
        "capture": {
            "status": status,
            "counts": {"added": 0, "reused": len(matched)},
        },
        "diagnostics": {
            **diagnostics,
            "prompt_epoch_ms": prompt_epoch_ms,
        },
    }
    gate.atomic_json(gate.gate_path(root, session_id, turn_id), current)
    return current


def fast_context(matched: list[dict[str, Any]], total: int, writes_allowed: bool) -> str:
    persistence = (
        "Persistence is already satisfied as reused; do not write duplicate knowledge."
        if matched and writes_allowed
        else "Persistence is already satisfied as none; do not create knowledge."
        if writes_allowed
        else "Workspace writes are forbidden; do not write Project Brain state."
    )
    if matched:
        payload = json.dumps([concise_entry(x) for x in matched], ensure_ascii=False, separators=(",", ":"))
        return (
            "CODEMIUM MEMORY RETRIEVAL MODE. This mode overrides the normal Codemium engineering lifecycle for this turn. "
            "The SNAPSHOT comes from the canonical Project Brain shared by the Local checkout and linked worktrees. "
            "Use minimum reasoning and answer directly from SNAPSHOT only. Do not classify task/depth, plan, inspect git, search the repository, "
            "read source files, build repository/working-set state, run tests, verify against source, or execute engineering/completion workflows. "
            "Do not infer missing facts. Keep the answer concise unless the user explicitly asks for detail. "
            f"{persistence} SNAPSHOT({len(matched)}/{total})={payload}"
        )
    availability = (
        "Project Brain has active entries, but none are relevant to this query."
        if total > 0
        else "Project Brain has no active durable entries."
    )
    return (
        "CODEMIUM MEMORY RETRIEVAL MODE. This mode overrides the normal Codemium engineering lifecycle for this turn. "
        f"{availability} Answer that the requested knowledge is not currently stored. Do not inspect git, repository files, source code, tests, or tools to fill the gap. "
        f"Use minimum reasoning. {persistence}"
    )


def latest_fast_gate(root: Path, session_id: str, turn_id: str) -> tuple[Path, dict[str, Any]] | None:
    exact = gate.gate_path(root, session_id, turn_id)
    data = gate.read_json(exact)
    if data and data.get("fast_path") is True:
        return exact, data
    return None


def handle_user_prompt(data: dict[str, Any]) -> None:
    prompt = str(data.get("prompt", ""))
    if not is_fast_path(prompt):
        gate.handle_user_prompt(data)
        return

    total_start = time.perf_counter_ns()
    prompt_epoch_ms = int(time.time() * 1000)
    diagnostics: dict[str, Any] = {}
    cwd = str(data.get("cwd") or Path.cwd())
    writes_allowed = not gate.forbids_all_workspace_writes(prompt)

    root_start = time.perf_counter_ns()
    try:
        root, context, migration = gate.prepare_project_root(cwd, writes_allowed=writes_allowed)
    except Exception as exc:
        gate.emit(
            {
                "systemMessage": f"Codemium canonical Project Brain resolution failed: {str(exc)[:500]}",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "Memory retrieval failed. Fall back to normal Codemium behavior, but do not claim Project Brain was reused unless verified.",
                },
            }
        )
        return
    diagnostics["root_resolve_ms"] = elapsed_ms(root_start)
    diagnostics["canonical_project_root"] = str(root)
    diagnostics["runtime_git_root"] = context.get("runtime_git_root")
    diagnostics["is_linked_worktree"] = bool(context.get("is_linked_worktree"))
    diagnostics["migration_status"] = migration.get("status")

    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")

    try:
        read_start = time.perf_counter_ns()
        entries = active_entries(root)
        diagnostics["registry_read_ms"] = elapsed_ms(read_start)

        rank_start = time.perf_counter_ns()
        matched = rank_entries(prompt, entries)
        diagnostics["ranking_ms"] = elapsed_ms(rank_start)

        context_start = time.perf_counter_ns()
        response_context = fast_context(matched, len(entries), writes_allowed)
        diagnostics["context_build_ms"] = elapsed_ms(context_start)
        diagnostics["context_chars"] = len(response_context)
        diagnostics["matched_entries"] = len(matched)
        diagnostics["total_active_entries"] = len(entries)

        gate_start = time.perf_counter_ns()
        if writes_allowed and session_id and turn_id:
            diagnostics["hook_total_before_gate_ms"] = elapsed_ms(total_start)
            project_location = {
                "canonical_project_root": context.get("canonical_project_root"),
                "runtime_git_root": context.get("runtime_git_root"),
                "git_common_dir": context.get("git_common_dir"),
                "is_linked_worktree": bool(context.get("is_linked_worktree")),
                "resolution": context.get("resolution"),
                "migration_status": migration.get("status"),
            }
            record = mark_fast_gate(
                root,
                session_id,
                turn_id,
                matched,
                total_entries=len(entries),
                prompt_epoch_ms=prompt_epoch_ms,
                diagnostics=diagnostics,
                project_location=project_location,
            )
            diagnostics["gate_write_ms"] = elapsed_ms(gate_start)
            diagnostics["hook_total_ms"] = elapsed_ms(total_start)
            record["diagnostics"] = {
                **record.get("diagnostics", {}),
                "gate_write_ms": diagnostics["gate_write_ms"],
                "hook_total_ms": diagnostics["hook_total_ms"],
            }
            record["updated_at"] = gate.now_iso()
            gate.atomic_json(gate.gate_path(root, session_id, turn_id), record)
        else:
            diagnostics["gate_write_ms"] = 0.0
            diagnostics["hook_total_ms"] = elapsed_ms(total_start)
    except Exception as exc:
        gate.emit(
            {
                "systemMessage": f"Codemium Project Brain lightweight retrieval failed: {str(exc)[:500]}",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "Memory retrieval failed. Fall back to normal Codemium behavior, but do not claim Project Brain was reused unless verified.",
                },
            }
        )
        return

    gate.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": response_context,
            }
        }
    )


def handle_stop(data: dict[str, Any]) -> None:
    root = gate.repository_root(str(data.get("cwd") or Path.cwd()))
    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")
    if session_id and turn_id:
        current = latest_fast_gate(root, session_id, turn_id)
        if current:
            path, record = current
            now_ms = int(time.time() * 1000)
            diagnostics = record.get("diagnostics") if isinstance(record.get("diagnostics"), dict) else {}
            prompt_ms = diagnostics.get("prompt_epoch_ms")
            if isinstance(prompt_ms, int):
                diagnostics["host_turn_to_stop_ms"] = max(0, now_ms - prompt_ms)
            diagnostics["stop_epoch_ms"] = now_ms
            record["diagnostics"] = diagnostics
            record["updated_at"] = gate.now_iso()
            gate.atomic_json(path, record)
            gate.emit({})
            return
    gate.handle_stop(data)


def handle_hook() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        gate.emit({"systemMessage": f"Codemium hook received invalid JSON: {exc}"})
        return
    if not isinstance(payload, dict):
        return
    event = str(payload.get("hook_event_name", ""))
    if event == "UserPromptSubmit":
        handle_user_prompt(payload)
    elif event == "Stop":
        handle_stop(payload)


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "finalize":
        return gate.cli_finalize(sys.argv[1:])
    handle_hook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
