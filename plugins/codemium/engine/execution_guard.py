#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from common import now_iso, read_json, repo_state, state_root, write_json

SCHEMA_VERSION = 1
STATE_RELATIVE_PATH = "runtime/execution-intelligence.json"

USEFUL_OUTCOMES = {"NEW_EVIDENCE", "NECESSARY_MUTATION", "REQUIRED_VERIFICATION"}
OUTCOMES = USEFUL_OUTCOMES | {"NO_GAIN"}
MUTATING_ACTIONS = {"edit", "mutation", "build", "deploy", "publish", "migrate"}
REPEAT_SENSITIVE_ACTIONS = {"inspect", "search", "screenshot", "build", "deploy", "publish", "mutation", "edit"}

TRUE_VALUES = {"true", "yes", "1", "open", "visible", "active", "present", "enabled", "ready", "success"}
FALSE_VALUES = {"false", "no", "0", "closed", "hidden", "inactive", "absent", "disabled", "not_ready", "failure"}


def state_path(root: Path) -> Path:
    return state_root(root) / STATE_RELATIVE_PATH


def normalize_value(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().lower().replace(" ", "_")
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return text


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def blank_state(task_id: str = "", task_type: str = "") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "task_type": task_type.upper(),
        "started_at": now_iso(),
        "observations": [],
        "hypotheses": [],
        "actions": [],
        "gate_decisions": [],
    }


def load_state(root: Path) -> dict:
    data = read_json(state_path(root), {})
    if not data:
        return blank_state()
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported execution-intelligence schema: {data.get('schema_version')}")
    for key in ["observations", "hypotheses", "actions", "gate_decisions"]:
        data.setdefault(key, [])
    return data


def save_state(root: Path, state: dict) -> None:
    write_json(state_path(root), state)


def start(root: Path, task_id: str | None = None, task_type: str | None = None) -> dict:
    active = read_json(state_root(root) / "tasks/active.json", {})
    resolved_id = task_id or active.get("id") or ""
    resolved_type = (task_type or active.get("type") or "").upper()
    state = blank_state(resolved_id, resolved_type)
    save_state(root, state)
    return state


def latest_observations(state: dict) -> list[dict]:
    latest: dict[tuple[str, str, str], dict] = {}
    for obs in state.get("observations", []):
        key = (str(obs.get("subject", "")), str(obs.get("claim", "")), str(obs.get("source", "")))
        latest[key] = obs
    return list(latest.values())


def evidence_snapshot(state: dict) -> dict:
    obs = []
    for item in latest_observations(state):
        obs.append(
            {
                "subject": item.get("subject"),
                "claim": item.get("claim"),
                "source": item.get("source"),
                "value": item.get("normalized_value"),
                "stabilized": item.get("stabilized"),
                "material": item.get("material", True),
            }
        )
    obs.sort(key=lambda x: (str(x["subject"]), str(x["claim"]), str(x["source"])))
    hypotheses = [
        {
            "id": h.get("id"),
            "status": h.get("status"),
            "evidence_ids": sorted(h.get("evidence_ids") or []),
        }
        for h in state.get("hypotheses", [])
    ]
    hypotheses.sort(key=lambda x: str(x["id"]))
    return {"observations": obs, "hypotheses": hypotheses}


def evidence_fingerprint(state: dict) -> str:
    return _canonical_digest(evidence_snapshot(state))


def unresolved_contradictions(state: dict) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = {}
    for obs in latest_observations(state):
        if not obs.get("material", True):
            continue
        if obs.get("normalized_value") is None:
            continue
        groups.setdefault((str(obs.get("subject", "")), str(obs.get("claim", ""))), []).append(obs)

    conflicts = []
    for (subject, claim), items in groups.items():
        distinct: dict[str, list[dict]] = {}
        for obs in items:
            value_key = json.dumps(obs.get("normalized_value"), ensure_ascii=False, sort_keys=True)
            distinct.setdefault(value_key, []).append(obs)
        if len(distinct) <= 1:
            continue
        conflicts.append(
            {
                "subject": subject,
                "claim": claim,
                "observations": [
                    {
                        "id": obs.get("id"),
                        "source": obs.get("source"),
                        "value": obs.get("value"),
                        "normalized_value": obs.get("normalized_value"),
                        "stabilized": obs.get("stabilized"),
                    }
                    for obs in items
                ],
            }
        )
    return conflicts


def add_observation(
    root: Path,
    subject: str,
    claim: str,
    source: str,
    value: Any,
    *,
    stabilized: bool | None = None,
    material: bool = True,
    detail: str | None = None,
) -> dict:
    state = load_state(root)
    obs_id = f"O{len(state['observations']) + 1:04d}"
    obs = {
        "id": obs_id,
        "at": now_iso(),
        "subject": subject,
        "claim": claim,
        "source": source.lower(),
        "value": value,
        "normalized_value": normalize_value(value),
        "stabilized": stabilized,
        "material": bool(material),
    }
    if detail:
        obs["detail"] = detail
    state["observations"].append(obs)
    save_state(root, state)
    return {
        "observation": obs,
        "evidence_fingerprint": evidence_fingerprint(state),
        "contradictions": unresolved_contradictions(state),
    }


def find_hypothesis(state: dict, hypothesis_id: str) -> dict | None:
    return next((h for h in state.get("hypotheses", []) if h.get("id") == hypothesis_id), None)


def upsert_hypothesis(
    root: Path,
    *,
    hypothesis_id: str | None,
    statement: str | None,
    expected_evidence: str | None,
    status: str,
    evidence_ids: list[str] | None = None,
) -> dict:
    state = load_state(root)
    normalized_status = status.upper()
    if normalized_status not in {"OPEN", "CONFIRMED", "REJECTED"}:
        raise ValueError("hypothesis status must be OPEN, CONFIRMED, or REJECTED")

    if hypothesis_id:
        item = find_hypothesis(state, hypothesis_id)
    else:
        item = None
        hypothesis_id = f"H{len(state['hypotheses']) + 1:03d}"

    if item is None:
        if not statement:
            raise ValueError("new hypothesis requires --statement")
        item = {
            "id": hypothesis_id,
            "statement": statement,
            "expected_evidence": expected_evidence or "",
            "status": normalized_status,
            "evidence_ids": evidence_ids or [],
            "created_at": now_iso(),
        }
        state["hypotheses"].append(item)
    else:
        if statement:
            item["statement"] = statement
        if expected_evidence is not None:
            item["expected_evidence"] = expected_evidence
        if evidence_ids is not None:
            item["evidence_ids"] = evidence_ids
        item["status"] = normalized_status
        item["updated_at"] = now_iso()

    if normalized_status == "REJECTED":
        item["rejected_evidence_fingerprint"] = evidence_fingerprint(state)
        item["rejected_at"] = now_iso()
    elif normalized_status == "CONFIRMED":
        item["confirmed_at"] = now_iso()

    save_state(root, state)
    return {"hypothesis": item, "evidence_fingerprint": evidence_fingerprint(state)}


def _latest_negative_unstabilized_screenshot(state: dict) -> dict | None:
    shots = [o for o in latest_observations(state) if str(o.get("source", "")).lower() == "screenshot"]
    for obs in reversed(shots):
        if obs.get("normalized_value") is False and obs.get("stabilized") is not True:
            return obs
    return None


def _action_signature(action: str, target: str, evidence_fp: str, repo_fp: str) -> str:
    return _canonical_digest(
        {
            "action": action.lower().strip(),
            "target": target.strip(),
            "evidence": evidence_fp,
            "repo": repo_fp,
        }
    )


def _substantive(text: str | None) -> bool:
    return bool(text and len(text.strip()) >= 12)


def gate_action(
    root: Path,
    *,
    action: str,
    target: str,
    mutation: bool = False,
    ui_sensitive: bool = False,
    basis: list[str] | None = None,
    hypothesis_id: str | None = None,
    override_reason: str | None = None,
) -> dict:
    state = load_state(root)
    action_key = action.lower().strip()
    basis_set = {x.lower().strip() for x in (basis or []) if x.strip()}
    if action_key in MUTATING_ACTIONS:
        mutation = True

    evidence_fp = evidence_fingerprint(state)
    repo_fp = repo_state(root)
    signature = _action_signature(action_key, target, evidence_fp, repo_fp)
    contradictions = unresolved_contradictions(state)
    blockers: list[str] = []
    warnings: list[str] = []

    if mutation and contradictions:
        blockers.append("unresolved material evidence contradiction; investigate runtime/source truth before mutation")

    if ui_sensitive and mutation:
        shot = _latest_negative_unstabilized_screenshot(state)
        if shot is not None:
            blockers.append(
                f"UI mutation is based on an unstabilized negative screenshot ({shot['id']}); wait for render/animation stabilization and re-observe"
            )

    task_type = str(state.get("task_type", "")).upper()
    if mutation and task_type in {"FIX", "REVIEW"}:
        has_evidence = bool(state.get("observations")) or any(
            h.get("status") == "CONFIRMED" for h in state.get("hypotheses", [])
        )
        if not has_evidence and "task" not in basis_set and "architecture" not in basis_set:
            blockers.append("FIX/REVIEW mutation has no concrete evidence basis")

    if mutation and not basis_set:
        warnings.append("mutation has no explicit basis; record task/evidence/architecture/dependency/verification basis")

    if hypothesis_id:
        hypothesis = find_hypothesis(state, hypothesis_id)
        if hypothesis is None:
            blockers.append(f"unknown hypothesis {hypothesis_id}")
        elif hypothesis.get("status") == "REJECTED":
            rejected_fp = hypothesis.get("rejected_evidence_fingerprint")
            if rejected_fp == evidence_fp:
                blockers.append(f"hypothesis {hypothesis_id} was rejected and no new evidence has appeared")

    repeated = [
        a for a in state.get("actions", [])
        if a.get("signature") == signature
    ]
    if action_key in REPEAT_SENSITIVE_ACTIONS and repeated:
        blockers.append("same action/target is being repeated with no evidence or repository-state delta")

    no_gain_repeat = [
        a for a in repeated if a.get("outcome") == "NO_GAIN"
    ]
    if no_gain_repeat:
        blockers.append("previous equivalent action produced no information gain")

    overridden = False
    if blockers and _substantive(override_reason):
        overridden = True
        warnings.extend(f"OVERRIDDEN: {b}" for b in blockers)
        blockers = []

    decision = {
        "id": f"G{len(state['gate_decisions']) + 1:04d}",
        "at": now_iso(),
        "action": action_key,
        "target": target,
        "mutation": mutation,
        "ui_sensitive": ui_sensitive,
        "basis": sorted(basis_set),
        "hypothesis_id": hypothesis_id,
        "evidence_fingerprint": evidence_fp,
        "repo_state": repo_fp,
        "signature": signature,
        "allowed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "overridden": overridden,
    }
    if override_reason:
        decision["override_reason"] = override_reason.strip()
    state["gate_decisions"].append(decision)
    save_state(root, state)
    return {
        **decision,
        "contradictions": contradictions,
        "stop_recommended": bool(blockers),
    }


def record_action(
    root: Path,
    *,
    action: str,
    target: str,
    outcome: str,
    note: str | None = None,
    hypothesis_id: str | None = None,
) -> dict:
    state = load_state(root)
    normalized_outcome = outcome.upper()
    if normalized_outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of: {', '.join(sorted(OUTCOMES))}")

    evidence_fp = evidence_fingerprint(state)
    repo_fp = repo_state(root)
    item = {
        "id": f"A{len(state['actions']) + 1:04d}",
        "at": now_iso(),
        "action": action.lower().strip(),
        "target": target,
        "outcome": normalized_outcome,
        "information_gain": normalized_outcome == "NEW_EVIDENCE",
        "useful": normalized_outcome in USEFUL_OUTCOMES,
        "evidence_fingerprint": evidence_fp,
        "repo_state": repo_fp,
        "signature": _action_signature(action, target, evidence_fp, repo_fp),
    }
    if note:
        item["note"] = note
    if hypothesis_id:
        item["hypothesis_id"] = hypothesis_id
    state["actions"].append(item)
    save_state(root, state)
    return {"action": item, "status": status_report(state)}


def status_report(state: dict) -> dict:
    actions = state.get("actions", [])
    useful = sum(1 for a in actions if a.get("useful"))
    waste = sum(1 for a in actions if a.get("outcome") == "NO_GAIN")
    blocked = sum(1 for g in state.get("gate_decisions", []) if not g.get("allowed"))
    hypotheses = state.get("hypotheses", [])
    last_action = actions[-1] if actions else None
    current_evidence = evidence_fingerprint(state)
    stop_recommended = bool(
        last_action
        and last_action.get("outcome") == "NO_GAIN"
        and last_action.get("evidence_fingerprint") == current_evidence
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": state.get("task_id", ""),
        "task_type": state.get("task_type", ""),
        "observations": len(state.get("observations", [])),
        "hypotheses": {
            "open": sum(1 for h in hypotheses if h.get("status") == "OPEN"),
            "confirmed": sum(1 for h in hypotheses if h.get("status") == "CONFIRMED"),
            "rejected": sum(1 for h in hypotheses if h.get("status") == "REJECTED"),
        },
        "contradictions": unresolved_contradictions(state),
        "actions": len(actions),
        "useful_actions": useful,
        "waste_actions": waste,
        "blocked_actions": blocked,
        "investigation_efficiency": round((useful / len(actions)) * 100, 1) if actions else None,
        "evidence_fingerprint": current_evidence,
        "stop_recommended": stop_recommended,
        "law": "Every action must buy information or produce the solution.",
    }


def _print(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def _parse_stabilized(value: str | None) -> bool | None:
    if value is None:
        return None
    if value == "yes":
        return True
    if value == "no":
        return False
    raise ValueError("stabilized must be yes or no")


def main() -> None:
    ap = argparse.ArgumentParser(description="Codemium v0.10 Execution Intelligence guard")
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="command", required=True)

    start_p = sub.add_parser("start")
    start_p.add_argument("--task-id")
    start_p.add_argument("--task-type")

    obs_p = sub.add_parser("observe")
    obs_p.add_argument("--subject", required=True)
    obs_p.add_argument("--claim", required=True)
    obs_p.add_argument("--source", required=True)
    obs_p.add_argument("--value", required=True)
    obs_p.add_argument("--stabilized", choices=["yes", "no"])
    obs_p.add_argument("--non-material", action="store_true")
    obs_p.add_argument("--detail")

    hyp_p = sub.add_parser("hypothesis")
    hyp_p.add_argument("--id")
    hyp_p.add_argument("--statement")
    hyp_p.add_argument("--expected-evidence")
    hyp_p.add_argument("--status", choices=["open", "confirmed", "rejected"], default="open")
    hyp_p.add_argument("--evidence-id", action="append", default=[])

    gate_p = sub.add_parser("gate")
    gate_p.add_argument("--action", required=True)
    gate_p.add_argument("--target", required=True)
    gate_p.add_argument("--mutation", action="store_true")
    gate_p.add_argument("--ui", action="store_true")
    gate_p.add_argument("--basis", action="append", choices=["task", "evidence", "architecture", "dependency", "verification"], default=[])
    gate_p.add_argument("--hypothesis-id")
    gate_p.add_argument("--override-reason")

    rec_p = sub.add_parser("record")
    rec_p.add_argument("--action", required=True)
    rec_p.add_argument("--target", required=True)
    rec_p.add_argument("--outcome", choices=["new_evidence", "necessary_mutation", "required_verification", "no_gain"], required=True)
    rec_p.add_argument("--note")
    rec_p.add_argument("--hypothesis-id")

    sub.add_parser("status")
    sub.add_parser("reset")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()

    if ns.command == "start":
        _print({"state": start(root, ns.task_id, ns.task_type), "status": status_report(load_state(root))})
    elif ns.command == "observe":
        _print(
            add_observation(
                root,
                ns.subject,
                ns.claim,
                ns.source,
                ns.value,
                stabilized=_parse_stabilized(ns.stabilized),
                material=not ns.non_material,
                detail=ns.detail,
            )
        )
    elif ns.command == "hypothesis":
        _print(
            upsert_hypothesis(
                root,
                hypothesis_id=ns.id,
                statement=ns.statement,
                expected_evidence=ns.expected_evidence,
                status=ns.status,
                evidence_ids=ns.evidence_id if ns.evidence_id else None,
            )
        )
    elif ns.command == "gate":
        result = gate_action(
            root,
            action=ns.action,
            target=ns.target,
            mutation=ns.mutation,
            ui_sensitive=ns.ui,
            basis=ns.basis,
            hypothesis_id=ns.hypothesis_id,
            override_reason=ns.override_reason,
        )
        _print(result)
        raise SystemExit(0 if result["allowed"] else 2)
    elif ns.command == "record":
        _print(
            record_action(
                root,
                action=ns.action,
                target=ns.target,
                outcome=ns.outcome,
                note=ns.note,
                hypothesis_id=ns.hypothesis_id,
            )
        )
    elif ns.command == "status":
        _print(status_report(load_state(root)))
    elif ns.command == "reset":
        path = state_path(root)
        if path.exists():
            path.unlink()
        _print({"status": "reset", "path": str(path)})


if __name__ == "__main__":
    main()
