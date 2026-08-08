#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
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


def rank_entries(prompt: str, entries: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
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


def mark_fast_gate(root: Path, session_id: str, turn_id: str, matched: list[dict[str, Any]]) -> dict[str, Any]:
    current = gate.begin_gate(root, session_id, turn_id)
    status = "reused" if matched else "none"
    current.update(
        {
            "status": status,
            "updated_at": gate.now_iso(),
            "fast_path": True,
            "retrieval": {
                "matched": len(matched),
                "entry_ids": [str(x.get("id", "")) for x in matched if x.get("id")],
            },
            "capture": {
                "status": status,
                "counts": {"added": 0, "reused": len(matched)},
            },
        }
    )
    gate.atomic_json(gate.gate_path(root, session_id, turn_id), current)
    return current


def fast_context(root: Path, matched: list[dict[str, Any]], total: int, writes_allowed: bool) -> str:
    if matched:
        payload = json.dumps([concise_entry(x) for x in matched], ensure_ascii=False, separators=(",", ":"))
        persistence = "The persistence gate is already satisfied as reused." if writes_allowed else "Workspace writes are forbidden, so no persistence gate was written."
        return (
            "CODEMIUM PROJECT BRAIN FAST PATH. Answer directly from the stored Project Brain snapshot below. "
            "Do not run task_compiler, repository graph/working-set helpers, git inspection, repository search, or source-file reads. "
            "Do not rescan the repository unless the user explicitly asks to refresh/verify against source. "
            f"{persistence} Do not create duplicate Project Brain entries for this retrieval-only turn. "
            f"Relevant active entries ({len(matched)} of {total}): {payload}"
        )
    persistence = "The persistence gate is already satisfied as none." if writes_allowed else "Workspace writes are forbidden, so no persistence gate was written."
    availability = (
        "Project Brain contains active entries, but none matched this query."
        if total > 0
        else "Project Brain has no active durable entries yet."
    )
    return (
        f"CODEMIUM PROJECT BRAIN FAST PATH. {availability} "
        "Do not scan the repository or open source files merely to fill the gap; answer that Project Brain does not currently contain the requested knowledge. "
        f"{persistence}"
    )


def handle_user_prompt(data: dict[str, Any]) -> None:
    prompt = str(data.get("prompt", ""))
    if not is_fast_path(prompt):
        gate.handle_user_prompt(data)
        return

    root = gate.repository_root(str(data.get("cwd") or Path.cwd()))
    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")
    writes_allowed = not gate.forbids_all_workspace_writes(prompt)

    try:
        if writes_allowed:
            gate.run_project_brain(root, "init")
        entries = active_entries(root)
        matched = rank_entries(prompt, entries)
        if writes_allowed and session_id and turn_id:
            mark_fast_gate(root, session_id, turn_id, matched)
        context = fast_context(root, matched, len(entries), writes_allowed)
    except Exception as exc:
        gate.emit(
            {
                "systemMessage": f"Codemium Project Brain fast-path retrieval failed: {str(exc)[:500]}",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "Fast-path retrieval failed. Fall back to normal Codemium behavior, but do not claim Project Brain was reused unless verified.",
                },
            }
        )
        return

    gate.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }
    )


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
        gate.handle_stop(payload)


def main() -> int:
    # Keep the existing manual finalizer CLI stable for Stop continuations.
    if len(sys.argv) > 1 and sys.argv[1] == "finalize":
        return gate.cli_finalize(sys.argv[1:])
    handle_hook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
