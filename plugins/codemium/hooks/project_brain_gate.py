#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
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
CONTINUATION_MARKERS = (
    "Project Brain persistence is still pending for this task.",
    "project_brain_gate.py\" finalize",
    "project_brain_gate.py' finalize",
)
REGISTRY_FILES = {
    "decision": "decisions.jsonl",
    "constraint": "constraints.jsonl",
    "interface": "interfaces.jsonl",
    "pattern": "patterns.jsonl",
    "bug": "bugs.jsonl",
}
DURABLE_STATE_FILES = (
    "PROJECT.md",
    "model-profile.json",
    "architecture/system.json",
)


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def git_output(cwd: str | Path, *args: str, timeout: int = 10) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(Path(cwd).resolve()), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _reported_git_path(value: str | None, base: Path) -> Path | None:
    if not value:
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        return candidate.resolve()
    except OSError:
        return candidate.absolute()


def project_context(cwd: str | Path) -> dict[str, Any]:
    """Resolve one stable Project Brain root across Local and linked worktrees."""
    runtime_cwd = Path(cwd).resolve()
    runtime_git_root = _reported_git_path(
        git_output(runtime_cwd, "rev-parse", "--show-toplevel"), runtime_cwd
    )

    if runtime_git_root is None:
        for candidate in (runtime_cwd, *runtime_cwd.parents):
            if (candidate / ".codemium").exists():
                return {
                    "runtime_cwd": str(runtime_cwd),
                    "runtime_git_root": None,
                    "git_common_dir": None,
                    "canonical_project_root": str(candidate),
                    "is_linked_worktree": False,
                    "resolution": "ancestor_project_brain",
                }
        return {
            "runtime_cwd": str(runtime_cwd),
            "runtime_git_root": None,
            "git_common_dir": None,
            "canonical_project_root": str(runtime_cwd),
            "is_linked_worktree": False,
            "resolution": "cwd_fallback",
        }

    common_raw = git_output(
        runtime_git_root, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    if common_raw is None:
        common_raw = git_output(runtime_git_root, "rev-parse", "--git-common-dir")
    common_dir = _reported_git_path(common_raw, runtime_git_root)

    canonical = runtime_git_root
    resolution = "git_toplevel"
    if common_dir is not None and common_dir.name.casefold() == ".git":
        candidate = common_dir.parent.resolve()
        if candidate.exists():
            canonical = candidate
            resolution = "git_common_dir"

    return {
        "runtime_cwd": str(runtime_cwd),
        "runtime_git_root": str(runtime_git_root),
        "git_common_dir": str(common_dir) if common_dir is not None else None,
        "canonical_project_root": str(canonical),
        "is_linked_worktree": canonical != runtime_git_root,
        "resolution": resolution,
    }


def repository_root(cwd: str | Path) -> Path:
    """Compatibility entry point; returns the canonical project root."""
    return Path(project_context(cwd)["canonical_project_root"]).resolve()


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


def list_worktree_roots(canonical: Path) -> list[Path]:
    """Return every live Git worktree sharing the canonical repository metadata."""
    raw = git_output(canonical, "worktree", "list", "--porcelain")
    if not raw:
        return [canonical]
    roots: list[Path] = []
    for line in raw.splitlines():
        if not line.startswith("worktree "):
            continue
        value = line[len("worktree ") :].strip()
        if not value:
            continue
        try:
            candidate = Path(value).resolve()
        except OSError:
            candidate = Path(value).absolute()
        if candidate not in roots:
            roots.append(candidate)
    if canonical not in roots:
        roots.insert(0, canonical)
    return roots


def _capture_entries_from_legacy(source: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    registry = source / ".codemium" / "registry"
    for kind, filename in REGISTRY_FILES.items():
        for raw in read_jsonl(registry / filename):
            if str(raw.get("status", "ACTIVE")).upper() != "ACTIVE":
                continue
            text = str(raw.get("text", "")).strip()
            if not text:
                continue
            entry: dict[str, Any] = {"kind": str(raw.get("kind") or kind), "text": text}
            for key in ("why", "source", "risk"):
                if raw.get(key) not in (None, ""):
                    entry[key] = raw[key]
            entries.append(entry)
    return entries


def _legacy_source_stamp(source: Path) -> int:
    state = source / ".codemium"
    paths = [state / rel for rel in DURABLE_STATE_FILES]
    paths.extend(state / "registry" / filename for filename in REGISTRY_FILES.values())
    stamp = 0
    for path in paths:
        try:
            stamp = max(stamp, path.stat().st_mtime_ns)
        except OSError:
            continue
    return stamp


def _legacy_sources(context: dict[str, Any], canonical: Path) -> list[Path]:
    """Discover legacy brains in every linked worktree, not only this turn's cwd."""
    candidates = list_worktree_roots(canonical)
    runtime_root = context.get("runtime_git_root")
    if runtime_root:
        candidate = Path(str(runtime_root)).resolve()
        if candidate not in candidates:
            candidates.append(candidate)
    sources: list[Path] = []
    for candidate in candidates:
        if candidate == canonical:
            continue
        if (candidate / ".codemium").exists() and candidate not in sources:
            sources.append(candidate)
    return sources


def _copy_durable_metadata(source: Path, target: Path) -> int:
    copied = 0
    for relative in DURABLE_STATE_FILES:
        src = source / ".codemium" / relative
        dst = target / ".codemium" / relative
        if not src.exists() or not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied


def migrate_legacy_project_brain(source: Path, target: Path, target_preexisting: bool) -> dict[str, Any]:
    """Compatibility helper for migrating one legacy worktree brain."""
    return migrate_legacy_project_brains([source], target, target_preexisting)


def migrate_legacy_project_brains(
    sources: list[Path],
    target: Path,
    target_preexisting: bool,
    previous_stamps: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Merge durable memory from all linked worktrees into one canonical brain."""
    previous_stamps = previous_stamps or {}
    valid: list[tuple[Path, int]] = []
    for source in sources:
        if source == target or not (source / ".codemium").exists():
            continue
        stamp = _legacy_source_stamp(source)
        if stamp <= int(previous_stamps.get(str(source), -1)):
            continue
        valid.append((source, stamp))

    if not valid:
        return {
            "status": "not_needed",
            "sources": [],
            "target": str(target),
            "source_stamps": {},
            "added": 0,
            "reused": 0,
        }

    # Prefer the freshest legacy brain as the source for human-maintained project metadata.
    freshest = max(valid, key=lambda item: item[1])[0]
    metadata_copied = 0 if target_preexisting else _copy_durable_metadata(freshest, target)

    entries: list[dict[str, Any]] = []
    source_stamps: dict[str, int] = {}
    for source, stamp in valid:
        entries.extend(_capture_entries_from_legacy(source))
        source_stamps[str(source)] = stamp

    added = 0
    reused = 0
    if entries:
        result = run_project_brain(
            target, "capture", "--entries", json.dumps(entries, ensure_ascii=False)
        )
        counts = result.get("counts") if isinstance(result.get("counts"), dict) else {}
        added = int(counts.get("added", 0))
        reused = int(counts.get("reused", 0))

    return {
        "status": "merged_all",
        "sources": [str(source) for source, _ in valid],
        "target": str(target),
        "metadata_source": str(freshest),
        "metadata_files_copied": metadata_copied,
        "source_stamps": source_stamps,
        "added": added,
        "reused": reused,
    }


def write_project_location(root: Path, context: dict[str, Any], migration: dict[str, Any]) -> None:
    path = root / ".codemium" / "runtime" / "project-location.json"
    existing = read_json(path) or {}
    observed = existing.get("observed_runtime_git_roots")
    observed_roots = [str(x) for x in observed] if isinstance(observed, list) else []
    runtime_git_root = context.get("runtime_git_root")
    if runtime_git_root and str(runtime_git_root) not in observed_roots:
        observed_roots.append(str(runtime_git_root))

    migrated = existing.get("migrated_source_stamps")
    migrated_stamps: dict[str, int] = {}
    if isinstance(migrated, dict):
        for key, value in migrated.items():
            try:
                migrated_stamps[str(key)] = int(value)
            except (TypeError, ValueError):
                continue
    incoming = migration.get("source_stamps")
    if isinstance(incoming, dict):
        for key, value in incoming.items():
            try:
                migrated_stamps[str(key)] = int(value)
            except (TypeError, ValueError):
                continue

    payload = {
        "schema_version": 2,
        "canonical_project_root": context.get("canonical_project_root"),
        "git_common_dir": context.get("git_common_dir"),
        "last_runtime_cwd": context.get("runtime_cwd"),
        "last_runtime_git_root": context.get("runtime_git_root"),
        "is_linked_worktree": bool(context.get("is_linked_worktree")),
        "resolution": context.get("resolution"),
        "observed_runtime_git_roots": observed_roots[-50:],
        "migrated_source_stamps": migrated_stamps,
        "last_migration": migration,
        "updated_at": now_iso(),
    }
    atomic_json(path, payload)


def prepare_project_root(cwd: str | Path, writes_allowed: bool = True) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Resolve canonical root and consolidate durable memory from all linked worktrees."""
    context = project_context(cwd)
    root = Path(str(context["canonical_project_root"])).resolve()
    if not writes_allowed:
        return root, context, {"status": "skipped_read_only"}

    target_preexisting = (root / ".codemium").exists()
    run_project_brain(root, "init")
    location = read_json(root / ".codemium" / "runtime" / "project-location.json") or {}
    previous_stamps_raw = location.get("migrated_source_stamps")
    previous_stamps = previous_stamps_raw if isinstance(previous_stamps_raw, dict) else {}
    sources = _legacy_sources(context, root)
    migration = migrate_legacy_project_brains(
        sources, root, target_preexisting, previous_stamps=previous_stamps
    )
    write_project_location(root, context, migration)
    return root, context, migration


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


def is_persistence_continuation(prompt: str) -> bool:
    return any(marker.casefold() in prompt.casefold() for marker in CONTINUATION_MARKERS)


def begin_gate(root: Path, session_id: str, turn_id: str) -> dict[str, Any]:
    path = gate_path(root, session_id, turn_id)
    current = read_json(path)
    if current and current.get("status") in FINAL_STATUSES:
        return current
    created_at = current.get("created_at") if current else now_iso()
    record = {
        "schema_version": 1,
        "session_id": session_id,
        "turn_id": turn_id,
        "status": "pending",
        "stop_attempts": int((current or {}).get("stop_attempts", 0)),
        "created_at": created_at,
        "updated_at": now_iso(),
    }
    atomic_json(path, record)
    return record


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
    record = read_json(path)
    if not record:
        raise ValueError("No pending persistence gate exists for this session/turn")
    if record.get("status") in FINAL_STATUSES:
        return record

    if entries:
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"knowledge entry {index + 1} must be an object")
            if not str(entry.get("source", "")).strip():
                raise ValueError(f"knowledge entry {index + 1} must include a source")
        capture = run_project_brain(
            root, "capture", "--entries", json.dumps(entries, ensure_ascii=False)
        )
        counts = capture.get("counts") if isinstance(capture.get("counts"), dict) else {}
        added = int(counts.get("added", 0))
        reused = int(counts.get("reused", 0))
        status = "captured" if added > 0 else "reused" if reused > 0 else "none"
    else:
        capture = {"status": "none", "counts": {"added": 0, "reused": 0}}
        status = "none"

    record.update({"status": status, "updated_at": now_iso(), "capture": capture})
    atomic_json(path, record)
    return record


def empty_finalize_command(root: Path, record: dict[str, Any]) -> str:
    hook = Path(__file__).resolve()
    session_id = str(record.get("session_id", ""))
    turn_id = str(record.get("turn_id", ""))
    return (
        f'python "{hook}" finalize --root "{root}" --session-id "{session_id}" '
        f'--turn-id "{turn_id}" --knowledge-json "[]"'
    )


def finalization_instruction(root: Path, record: dict[str, Any]) -> str:
    return (
        "Project Brain persistence is still pending for this task. Before finishing, classify durable knowledge and finalize the gate. "
        "Use an empty JSON array when the task produced no durable project fact; otherwise pass only durable source-backed decisions, "
        "constraints, interfaces, patterns, or known bugs/risks. Do not invent entries.\n\n"
        f"{empty_finalize_command(root, record)}\n\n"
        "For non-empty knowledge, replace [] with a JSON array of objects containing kind, text, source, and optional why/risk. "
        "After the command succeeds, finish the task normally."
    )


def emit(payload: dict[str, Any] | None) -> None:
    if payload is not None:
        print(json.dumps(payload, ensure_ascii=False))


def handle_user_prompt(data: dict[str, Any]) -> None:
    prompt = str(data.get("prompt", ""))
    cwd = str(data.get("cwd") or Path.cwd())
    root = repository_root(cwd)
    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")

    if session_id and is_persistence_continuation(prompt):
        pending = latest_pending_gate(root, session_id)
        if pending:
            _, record = pending
            emit({
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": finalization_instruction(root, record),
                }
            })
        return

    if not ACTIVATION_RE.search(prompt):
        return

    if forbids_all_workspace_writes(prompt):
        emit({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "The user explicitly prohibited all file/workspace changes. Treat Project Brain persistence as skipped by user constraint. "
                    "Do not create or update .codemium/ and do not claim persistence succeeded."
                ),
            }
        })
        return

    if not session_id or not turn_id:
        emit({"systemMessage": "Codemium Project Brain hook received no session/turn id; persistence enforcement is unavailable for this turn."})
        return

    try:
        root, context, migration = prepare_project_root(cwd, writes_allowed=True)
        record = begin_gate(root, session_id, turn_id)
        record["project_location"] = {
            "canonical_project_root": context.get("canonical_project_root"),
            "runtime_git_root": context.get("runtime_git_root"),
            "git_common_dir": context.get("git_common_dir"),
            "is_linked_worktree": bool(context.get("is_linked_worktree")),
            "migration_status": migration.get("status"),
            "migration_sources": migration.get("sources", []),
        }
        atomic_json(gate_path(root, session_id, turn_id), record)
    except Exception as exc:
        emit({
            "systemMessage": f"Codemium Project Brain initialization failed: {str(exc)[:500]}",
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "Project Brain persistence is unavailable for this turn. Do not claim that durable knowledge was saved.",
            },
        })
        return

    if record.get("status") in FINAL_STATUSES:
        return
    context_text = (
        "A deterministic Project Brain persistence gate is active at the canonical project root, shared across Local and linked worktrees. "
        "Source/product code may remain read-only while .codemium bookkeeping is updated. Complete the investigation/implementation first. "
        "Before your final answer, finalize this exact gate. If no durable project knowledge was learned, run:\n\n"
        f"{empty_finalize_command(root, record)}\n\n"
        "If durable knowledge was learned, replace [] with a JSON array containing only durable source-backed facts with kind, text, source, and optional why/risk. "
        "The Stop hook will continue the turn if this gate is still pending."
    )
    emit({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context_text,
        }
    })


def handle_stop(data: dict[str, Any]) -> None:
    root = repository_root(str(data.get("cwd") or Path.cwd()))
    session_id = str(data.get("session_id") or "")
    turn_id = str(data.get("turn_id") or "")
    if not session_id:
        emit({})
        return

    pending = latest_pending_gate(root, session_id, turn_id or None)
    if not pending:
        emit({})
        return
    path, record = pending
    attempts = int(record.get("stop_attempts", 0)) + 1
    record["stop_attempts"] = attempts
    record["stop_hook_active"] = bool(data.get("stop_hook_active", False))
    record["updated_at"] = now_iso()

    if attempts <= 2:
        atomic_json(path, record)
        emit({"decision": "block", "reason": finalization_instruction(root, record)})
        return

    record["status"] = "enforcement_failed"
    record["updated_at"] = now_iso()
    record["failure_reason"] = "Persistence gate remained pending after two Stop continuations."
    atomic_json(path, record)
    emit({
        "systemMessage": (
            "Codemium Project Brain persistence could not be finalized after two continuation attempts. "
            "The turn is being allowed to stop to avoid a loop; do not treat persistence as successful."
        )
    })


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
        record = finalize_gate(Path(ns.root).resolve(), ns.session_id, ns.turn_id, entries)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "finalize":
        return cli_finalize(sys.argv[1:])
    handle_hook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
