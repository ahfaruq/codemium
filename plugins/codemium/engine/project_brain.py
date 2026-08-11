#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import append_jsonl, atomic_write, now_iso, read_json, read_jsonl, sha256_bytes, state_root, write_json

REGISTRY = {
    "decision": ("decisions.jsonl", "D"),
    "constraint": ("constraints.jsonl", "C"),
    "interface": ("interfaces.jsonl", "I"),
    "pattern": ("patterns.jsonl", "P"),
    "bug": ("bugs.jsonl", "B"),
}

GENERIC_REASONING = {
    "FAST": {"preferred_class": "economy", "minimum_class": "economy"},
    "NORMAL": {"preferred_class": "balanced", "minimum_class": "economy"},
    "DEEP": {"preferred_class": "strong", "minimum_class": "balanced"},
    "CRITICAL": {"preferred_class": "frontier", "minimum_class": "strong"},
}

CODEX_EFFORT_BY_DEPTH = {
    "FAST": {"preferred_effort": "low", "minimum_effort": "low"},
    "NORMAL": {"preferred_effort": "medium", "minimum_effort": "low"},
    "DEEP": {"preferred_effort": "high", "minimum_effort": "medium"},
    "CRITICAL": {"preferred_effort": "xhigh", "minimum_effort": "high"},
}

HOST_OWNED = {"control": "host_owned_unless_documented_per_task_control"}
TRANSIENT_IGNORE = ["runtime/", "repository/", "tasks/active.json", "tasks/completed/"]
FRESHNESS_STATES = {"FRESH", "NEEDS_REVALIDATION", "SUPERSEDED", "UNKNOWN"}


def default_model_profile() -> dict:
    return {
        "schema_version": 3,
        "roles": {
            "primary": {"capability": "frontier_reasoning", "preferred_model": None},
            "reviewer": {"capability": "frontier_review", "preferred_model": None},
            "worker": {"capability": "strong_coding", "preferred_model": None},
        },
        "generic_reasoning": GENERIC_REASONING,
        "host_profiles": {
            "codex": {"effort_by_depth": CODEX_EFFORT_BY_DEPTH, "control": "advisory_unless_runtime_confirms_per_task_control"},
            "claude-code": dict(HOST_OWNED), "gemini-cli": dict(HOST_OWNED),
            "cursor": dict(HOST_OWNED), "opencode": dict(HOST_OWNED),
        },
        "host_control": {"mutate_global_config": False, "claim_change_only_after_runtime_confirmation": True},
        "note": "Engineering depth is portable. Vendor model/reasoning knobs belong to host adapters and are not proof of benchmarked capability.",
    }


def ensure_model_profile(path: Path) -> None:
    current = read_json(path, {}) if path.exists() else {}
    merged = default_model_profile()
    if isinstance(current, dict):
        if isinstance(current.get("roles"), dict):
            merged["roles"].update(current["roles"])
        if isinstance(current.get("generic_reasoning"), dict):
            merged["generic_reasoning"].update(current["generic_reasoning"])
        if isinstance(current.get("host_profiles"), dict):
            for host, profile in current["host_profiles"].items():
                if isinstance(profile, dict):
                    merged["host_profiles"].setdefault(host, {}).update(profile)
        if isinstance(current.get("reasoning_profiles"), dict):
            merged["host_profiles"]["codex"]["effort_by_depth"].update(current["reasoning_profiles"])
        if isinstance(current.get("host_control"), dict):
            merged["host_control"].update(current["host_control"])
    write_json(path, merged)


def ensure_state_gitignore(path: Path) -> None:
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    normalized = {line.strip() for line in existing if line.strip()}
    additions = [entry for entry in TRANSIENT_IGNORE if entry not in normalized]
    if not additions:
        return
    text = "\n".join(existing)
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n".join(additions) + "\n"
    atomic_write(path, text)


def init(root: Path, emit: bool = True) -> dict:
    s = state_root(root)
    for d in ["architecture", "registry", "repository", "tasks/completed", "runtime/snapshots"]:
        (s / d).mkdir(parents=True, exist_ok=True)
    project = s / "PROJECT.md"
    if not project.exists():
        atomic_write(project, "# Project\n\nDescribe stable product purpose, stack, entry points, and non-negotiable engineering facts here.\n")
    arch = s / "architecture/system.json"
    if not arch.exists():
        write_json(arch, {"schema_version": 1, "updated_at": now_iso(), "boundaries": [], "components": []})
    ensure_model_profile(s / "model-profile.json")
    for fn, _ in REGISTRY.values():
        (s / "registry" / fn).touch(exist_ok=True)
    ensure_state_gitignore(s / ".gitignore")
    result = {"status": "initialized", "state_dir": str(s)}
    if emit:
        print(json.dumps(result, indent=2))
    return result


def next_id(path: Path, prefix: str) -> str:
    n = 0
    for x in read_jsonl(path):
        v = str(x.get("id", ""))
        if v.startswith(prefix):
            try:
                n = max(n, int(v[len(prefix):]))
            except ValueError:
                pass
    return f"{prefix}{n + 1:04d}"


def normalize_entry_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def find_active_duplicate(path: Path, text: str) -> dict | None:
    needle = normalize_entry_text(text)
    for entry in read_jsonl(path):
        if entry.get("status", "ACTIVE") != "ACTIVE":
            continue
        if normalize_entry_text(str(entry.get("text", ""))) == needle:
            return entry
    return None


def hash_path(root: Path, path: str) -> str | None:
    p = (root / path).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return None
    try:
        return sha256_bytes(p.read_bytes())
    except OSError:
        return None


def normalize_evidence(root: Path, evidence, source: str | None = None) -> list[dict]:
    rows: list[dict] = []
    raw_rows = evidence if isinstance(evidence, list) else []
    if not raw_rows and source:
        raw_rows = [{"path": source}]
    for raw in raw_rows:
        if not isinstance(raw, dict):
            continue
        row = {k: raw.get(k) for k in ("path", "symbol", "graph_node_id", "content_hash", "line_start", "line_end") if raw.get(k) not in (None, "")}
        path = row.get("path")
        if path and not row.get("content_hash"):
            current = hash_path(root, str(path))
            if current:
                row["content_hash"] = current
        if row:
            rows.append(row)
    return rows


def entry_freshness(root: Path, entry: dict) -> str:
    if entry.get("status") == "SUPERSEDED" or entry.get("superseded_by"):
        return "SUPERSEDED"
    evidence = entry.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return "UNKNOWN"
    unknown = False
    for ev in evidence:
        if not isinstance(ev, dict):
            unknown = True
            continue
        path = ev.get("path")
        expected = ev.get("content_hash")
        if not path or not expected:
            unknown = True
            continue
        current = hash_path(root, str(path))
        if current is None or current != expected:
            return "NEEDS_REVALIDATION"
    return "UNKNOWN" if unknown else "FRESH"


def registry_entries(root: Path, include_freshness: bool = True) -> list[dict]:
    rows = []
    for kind, (fn, _) in REGISTRY.items():
        for entry in read_jsonl(state_root(root) / "registry" / fn):
            row = dict(entry)
            row.setdefault("kind", kind)
            if include_freshness:
                row["freshness"] = entry_freshness(root, row)
            rows.append(row)
    return rows


def freshness_summary(root: Path) -> dict:
    counts = {s: 0 for s in ["FRESH", "NEEDS_REVALIDATION", "SUPERSEDED", "UNKNOWN"]}
    by_id = {}
    for e in registry_entries(root, include_freshness=True):
        fresh = e["freshness"]
        counts[fresh] = counts.get(fresh, 0) + 1
        if e.get("id"):
            by_id[e["id"]] = fresh
    return {"counts": counts, "entries": by_id}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    atomic_write(path, "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows))


def replace_registry_entry(root: Path, kind: str, entry_id: str, updater) -> dict | None:
    fn, _ = REGISTRY[kind]
    path = state_root(root) / "registry" / fn
    rows = read_jsonl(path)
    updated = None
    for i, row in enumerate(rows):
        if row.get("id") == entry_id:
            rows[i] = updater(dict(row))
            updated = rows[i]
            break
    if updated is not None:
        write_jsonl(path, rows)
    return updated


def add(root: Path, kind: str, text: str, extra: dict) -> dict:
    fn, prefix = REGISTRY[kind]
    path = state_root(root) / "registry" / fn
    source = extra.get("source")
    evidence = normalize_evidence(root, extra.get("evidence"), source)
    entry = {
        "id": next_id(path, prefix), "kind": kind, "text": text, "status": "ACTIVE", "created_at": now_iso(),
        **{k: v for k, v in extra.items() if k != "evidence" and v not in (None, "")},
    }
    if evidence:
        entry["evidence"] = evidence
    append_jsonl(path, entry)
    return entry


def capture(root: Path, entries: list[dict]) -> dict:
    """Persist source-backed durable facts, deduplicating equivalent ACTIVE entries."""
    if not isinstance(entries, list):
        raise ValueError("knowledge entries must be a JSON array")
    added: list[dict] = []
    reused: list[dict] = []
    for raw in entries:
        if not isinstance(raw, dict):
            raise ValueError("each knowledge entry must be an object")
        kind = str(raw.get("kind", "")).strip().lower()
        text = str(raw.get("text", "")).strip()
        if kind not in REGISTRY:
            raise ValueError(f"unknown knowledge kind: {kind!r}")
        if not text:
            raise ValueError("knowledge entry text must not be empty")
        fn, _ = REGISTRY[kind]
        path = state_root(root) / "registry" / fn
        duplicate = find_active_duplicate(path, text)
        normalized = normalize_evidence(root, raw.get("evidence"), raw.get("source"))
        if duplicate:
            if normalized and not duplicate.get("evidence"):
                duplicate = replace_registry_entry(root, kind, duplicate["id"], lambda e: {**e, "evidence": normalized, "evidence_updated_at": now_iso()}) or duplicate
            row = dict(duplicate)
            row["freshness"] = entry_freshness(root, row)
            reused.append(row)
            continue
        extra = {k: raw.get(k) for k in ("why", "source", "risk", "evidence")}
        row = add(root, kind, text, extra)
        row["freshness"] = entry_freshness(root, row)
        added.append(row)
    return {"status": "captured", "added": added, "reused": reused, "counts": {"added": len(added), "reused": len(reused)}}


def revalidate(root: Path, kind: str, entry_id: str, evidence=None) -> dict:
    if kind not in REGISTRY:
        raise ValueError(f"unknown knowledge kind: {kind!r}")
    fn, _ = REGISTRY[kind]
    existing = next((x for x in read_jsonl(state_root(root) / "registry" / fn) if x.get("id") == entry_id), None)
    if not existing:
        raise ValueError(f"knowledge entry not found: {entry_id}")
    normalized = normalize_evidence(root, evidence if evidence is not None else existing.get("evidence"), existing.get("source"))
    for row in normalized:
        if row.get("path"):
            current = hash_path(root, str(row["path"]))
            if current:
                row["content_hash"] = current
    updated = replace_registry_entry(root, kind, entry_id, lambda e: {**e, "evidence": normalized, "revalidated_at": now_iso(), "status": "ACTIVE"})
    assert updated is not None
    result = dict(updated)
    result["freshness"] = entry_freshness(root, result)
    return result


def status(root: Path) -> dict:
    s = state_root(root)
    regs = {k: len(read_jsonl(s / "registry" / fn)) for k, (fn, _) in REGISTRY.items()}
    active = read_json(s / "tasks/active.json", None)
    return {
        "initialized": s.exists(), "root": str(root.resolve()), "registries": regs,
        "freshness": freshness_summary(root), "active_task": active,
        "model_profile": read_json(s / "model-profile.json", None),
    }


def load_json_argument(value: str):
    try:
        candidate = Path(value)
        if len(value) < 4096 and candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return json.loads(value)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    fresh = sub.add_parser("freshness")
    fresh.add_argument("--kind", choices=sorted(REGISTRY))
    fresh.add_argument("--id")
    for kind in REGISTRY:
        p = sub.add_parser("add-" + kind)
        p.add_argument("--text", required=True); p.add_argument("--why"); p.add_argument("--source"); p.add_argument("--risk"); p.add_argument("--evidence")
    c = sub.add_parser("capture"); c.add_argument("--entries", required=True, help="JSON array or path to a JSON file")
    a = sub.add_parser("start-task"); a.add_argument("--contract", required=True, help="JSON string or path")
    done = sub.add_parser("complete-task"); done.add_argument("--knowledge", help="optional JSON array/path of durable knowledge to capture before completion")
    rv = sub.add_parser("revalidate"); rv.add_argument("--kind", required=True, choices=sorted(REGISTRY)); rv.add_argument("--id", required=True); rv.add_argument("--evidence", help="JSON evidence array or path")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    if ns.cmd == "init":
        return init(root)
    if not state_root(root).exists():
        init(root, emit=False)
    if ns.cmd == "status":
        print(json.dumps(status(root), indent=2)); return
    if ns.cmd == "freshness":
        rows = registry_entries(root, include_freshness=True)
        if ns.kind:
            rows = [x for x in rows if x.get("kind") == ns.kind]
        if ns.id:
            rows = [x for x in rows if x.get("id") == ns.id]
        print(json.dumps({"entries": rows, "summary": freshness_summary(root)}, ensure_ascii=False, indent=2)); return
    if ns.cmd.startswith("add-"):
        kind = ns.cmd[4:]
        evidence = load_json_argument(ns.evidence) if ns.evidence else None
        row = add(root, kind, ns.text, {"why": ns.why, "source": ns.source, "risk": ns.risk, "evidence": evidence})
        row["freshness"] = entry_freshness(root, row)
        print(json.dumps(row, indent=2)); return
    if ns.cmd == "capture":
        print(json.dumps(capture(root, load_json_argument(ns.entries)), ensure_ascii=False, indent=2)); return
    if ns.cmd == "revalidate":
        evidence = load_json_argument(ns.evidence) if ns.evidence else None
        print(json.dumps(revalidate(root, ns.kind, ns.id, evidence), ensure_ascii=False, indent=2)); return
    if ns.cmd == "start-task":
        contract = load_json_argument(ns.contract); contract.setdefault("started_at", now_iso())
        write_json(state_root(root) / "tasks/active.json", contract)
        print(json.dumps(contract, ensure_ascii=False, indent=2)); return
    if ns.cmd == "complete-task":
        knowledge = capture(root, load_json_argument(ns.knowledge)) if ns.knowledge else None
        p = state_root(root) / "tasks/active.json"; task = read_json(p, None)
        if not task:
            print(json.dumps({"status": "no-active-task", "knowledge": knowledge}, ensure_ascii=False, indent=2)); return
        task["completed_at"] = now_iso(); tid = task.get("id", "task")
        write_json(state_root(root) / "tasks/completed" / f"{tid}.json", task); p.unlink(missing_ok=True)
        print(json.dumps({"status": "completed", "id": tid, "knowledge": knowledge}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
