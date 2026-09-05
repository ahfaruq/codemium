#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import now_iso, read_json, state_root, write_json
from graph_query import find_nodes
from project_brain import init as init_project_brain
from reasoning_profile import EFFORT_ORDER, HOSTS, resolve_reasoning_profile

DEPTH_RANK = {"FAST": 0, "NORMAL": 1, "DEEP": 2, "CRITICAL": 3}
UI_RUNTIME_TERMS = [
    "z-index", "z index", "dropdown", "popover", "tooltip", "modal", "drawer",
    "visibility", "stacking context", "animation", "transition", "overlay",
]


def classify(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ["security", "vulnerab", "authz", "authorization", "permission", "secret", "injection"]): return "SECURITY"
    if any(x in t for x in ["migration", "migrate", "schema change", "database upgrade"]): return "MIGRATION"
    if any(x in t for x in ["review", "audit pr", "code review"]): return "REVIEW"
    if any(x in t for x in ["refactor", "cleanup architecture", "simplify code"]): return "REFACTOR"
    if any(x in t for x in ["test", "coverage", "spec case"]) and not any(x in t for x in ["bug", "fix", "error", "fail"]): return "TEST"
    if any(x in t for x in ["bug", "fix", "error", "fail", "broken", "duplicate", "stuck", "wrong", "tidak", "kenapa"]): return "FIX"
    return "BUILD"


def risk(text: str, mode: str) -> str:
    t = text.lower()
    if mode in {"SECURITY", "MIGRATION"} or any(x in t for x in ["payment", "billing", "delete production", "destructive", "auth", "permission", "concurrency", "race", "deployment", "infrastructure", "production data"]): return "high"
    if mode in {"FIX", "REFACTOR", "REVIEW"} or any(x in t for x in ["database", "api", "worker", "queue", "webhook"]): return "medium"
    return "low"


def minimum_depth(text: str, mode: str, task_risk: str) -> tuple[str, str]:
    t = text.lower()
    critical_terms = ["payment", "billing", "auth", "authorization", "permission", "secret", "migration", "schema change", "production data", "destructive", "deployment", "infrastructure", "public api breaking", "breaking api"]
    if mode in {"SECURITY", "MIGRATION"} or any(x in t for x in critical_terms): return "CRITICAL", "safety-critical domain"
    if task_risk == "high" or any(x in t for x in ["concurrency", "race", "deadlock", "intermittent", "flaky", "distributed", "memory leak", "performance regression"]): return "DEEP", "high-risk or non-local behavior"
    return "FAST", "no safety escalation required"


def auto_depth(text: str, mode: str, task_risk: str) -> tuple[str, str]:
    floor, floor_reason = minimum_depth(text, mode, task_risk)
    if floor in {"CRITICAL", "DEEP"}: return floor, floor_reason
    t = text.lower()
    trivial_terms = [
        "typo", "copy text", "label text", "css spacing", "padding", "margin", "font size", "color only",
        "z-index", "z index", "dropdown", "tooltip", "popover", "stacking context",
    ]
    if task_risk == "low" and any(x in t for x in trivial_terms): return "FAST", "localized low-risk change"
    if any(x in t for x in ["multi-module", "cross-module", "websocket", "queue", "webhook", "worker"]): return "DEEP", "cross-boundary behavior"
    return "NORMAL", "default project-aware depth"


def resolve_depth(text: str, mode: str, task_risk: str, requested: str = "auto") -> tuple[str, str]:
    requested = requested.lower().strip()
    if requested == "auto": return auto_depth(text, mode, task_risk)
    requested_map = {"fast": "FAST", "deep": "DEEP", "critical": "CRITICAL"}
    if requested not in requested_map: raise ValueError("depth must be auto, fast, deep, or critical")
    desired = requested_map[requested]
    floor, floor_reason = minimum_depth(text, mode, task_risk)
    if DEPTH_RANK[desired] < DEPTH_RANK[floor]: return floor, f"requested {desired} escalated: {floor_reason}"
    return desired, f"explicit {desired} override"


def execution_policy(text: str, mode: str) -> dict:
    t = text.lower()
    ui_sensitive = any(term in t for term in UI_RUNTIME_TERMS)
    return {
        "enabled": True,
        "evidence_before_mutation": mode in {"FIX", "REVIEW"},
        "contradiction_gate": True,
        "evidence_delta_gate": True,
        "repeat_without_new_evidence": "block",
        "hypothesis_revival_requires_new_evidence": True,
        "ui_stabilization_required": ui_sensitive,
        "action_value_rule": "NEW_EVIDENCE | NECESSARY_MUTATION | REQUIRED_VERIFICATION",
    }


def compile_task(text: str, requested_depth: str = "auto", model: str | None = None, host_effort: str | None = None, host: str | None = None) -> dict:
    mode = classify(text); r = risk(text, mode); depth, depth_reason = resolve_depth(text, mode, r, requested_depth)
    reasoning = resolve_reasoning_profile(depth, model=model, host_effort=host_effort, host=host)
    policy = {
        "FIX": "root-cause fix; evidence before mutation; surgical scope; regression evidence",
        "TEST": "behavior/risk coverage; do not minimize justified cases",
        "REFACTOR": "behavior preservation; demonstrated complexity only",
        "REVIEW": "read-only unless explicitly asked to edit; evidence before mutation",
        "MIGRATION": "compatibility, data integrity, rollback",
        "SECURITY": "trust-boundary correctness outranks efficiency",
        "BUILD": "reuse-first; minimum justified architecture",
    }[mode]
    return {
        "id": "T" + now_iso().replace("-", "").replace(":", "").replace("T", "")[:14], "type": mode,
        "request": text, "objective": text.strip(), "expected_behavior": "derive from request/evidence before editing",
        "likely_domain": [], "acceptance": [
            "requested behavior is satisfied",
            "relevant verification passes",
            "no unrelated diff",
            "no material unexplained uncertainty",
            "repeated investigation either produces material evidence or stops",
        ],
        "risk": r, "requested_depth": requested_depth.lower(), "depth": depth, "depth_reason": depth_reason,
        "reasoning": reasoning, "change_policy": policy, "execution_policy": execution_policy(text, mode),
        "created_at": now_iso(), "working_set": [], "cleanup_set": [],
    }


def apply_structural_escalation(task: dict, root: Path, model: str | None = None, host_effort: str | None = None, host: str | None = None) -> dict:
    graph = read_json(state_root(root) / "repository/graph.json", {})
    if graph.get("schema_version", 0) < 2: return task
    seeds = find_nodes(graph, task["request"], limit=8)
    if not seeds: return task
    seed_ids = {x["id"] for x in seeds}
    high_terms = ["auth", "permission", "security", "payment", "billing", "migration", "secret", "token"]
    critical_surface = any(any(term in str(n.get("path", "")).lower() for term in high_terms) for n in seeds)
    incoming = 0; touched_files = set()
    for edge in graph.get("edges", []):
        if edge.get("target") in seed_ids and edge.get("relation") in {"CALLS", "REFERENCES", "DEPENDS_ON", "IMPORTS"}: incoming += 1
        if edge.get("source") in seed_ids or edge.get("target") in seed_ids:
            if edge.get("source_file"): touched_files.add(edge["source_file"])
    desired = task["depth"]; reason = None
    if critical_surface and DEPTH_RANK[desired] < DEPTH_RANK["CRITICAL"]:
        desired = "CRITICAL"; reason = "structural intelligence reached a safety-critical domain"; task["risk"] = "high"
    elif (incoming >= 8 or len(touched_files) >= 6) and DEPTH_RANK[desired] < DEPTH_RANK["DEEP"]:
        desired = "DEEP"; reason = "structural intelligence found broad dependency impact"
        if task["risk"] == "low": task["risk"] = "medium"
    task["structural_risk"] = {"seed_nodes": [x["id"] for x in seeds], "incoming_relationships": incoming, "related_source_files": len(touched_files), "escalated": bool(reason)}
    if reason:
        task["depth"] = desired; task["depth_reason"] = reason
        task["reasoning"] = resolve_reasoning_profile(desired, model=model, host_effort=host_effort, host=host)
    return task


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--request", required=True)
    ap.add_argument("--depth", choices=["auto", "fast", "deep", "critical"], default="auto"); ap.add_argument("--host", choices=sorted(HOSTS)); ap.add_argument("--model"); ap.add_argument("--host-effort", choices=EFFORT_ORDER); ap.add_argument("--no-write", action="store_true")
    ns = ap.parse_args(); root = Path(ns.root).resolve()
    task = compile_task(ns.request, ns.depth, ns.model, ns.host_effort, ns.host)
    task = apply_structural_escalation(task, root, ns.model, ns.host_effort, ns.host)
    if not ns.no_write:
        if not state_root(root).exists(): init_project_brain(root, emit=False)
        p = state_root(root) / "tasks/active.json"; p.parent.mkdir(parents=True, exist_ok=True); write_json(p, task)
    print(json.dumps(task, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
