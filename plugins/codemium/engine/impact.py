#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import git, read_json, state_root
from graph_query import dependents_for_files

HIGH_TERMS = ["auth", "permission", "security", "payment", "billing", "migration", "infra", "deploy", "secret", "token"]
MED_TERMS = ["api", "worker", "queue", "webhook", "database", "repository", "service"]


def changed_from_git(root: Path) -> list[str]:
    names = set()
    for args in [("diff", "--name-only"), ("diff", "--cached", "--name-only")]:
        out = git(root, *args) or ""
        names.update(x for x in out.splitlines() if x)
    return sorted(names)


def fallback_dependents(paths: list[str], graph: dict) -> list[dict]:
    changed = set(paths)
    affected = set()
    for p in paths:
        base = Path(p).stem.lower()
        name = Path(p).name.lower()
        for f in graph.get("files", []):
            if f["path"] in changed:
                continue
            blob = " ".join(f.get("imports", [])).lower()
            if base and (base in blob or name in blob):
                affected.add(f["path"])
    return [{"path": p, "distance": 1, "relations": ["IMPORTS"], "provenance": ["HEURISTIC"]} for p in sorted(affected)]


def test_paths(graph: dict, changed: list[str], affected: list[dict]) -> list[dict]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    changed_set = set(changed)
    affected_set = {x["path"] for x in affected}
    rows: dict[str, dict] = {}
    for e in graph.get("edges", []):
        if e.get("relation") != "TESTS":
            continue
        test = nodes.get(e["source"], {})
        target = nodes.get(e["target"], {})
        tp = test.get("path")
        sp = target.get("path")
        if tp and sp and sp in changed_set | affected_set:
            rows[tp] = {
                "path": tp, "provenance": e.get("provenance"), "target": e.get("target"),
                "source_file": e.get("source_file"),
            }
    return sorted(rows.values(), key=lambda x: x["path"])


def risk_for(paths: list[str], affected: list[dict], graph: dict, tests: list[dict]) -> tuple[str, list[str]]:
    text = " ".join(paths + [x["path"] for x in affected]).lower()
    reasons = []
    risk = "low"
    if any(x in text for x in HIGH_TERMS):
        risk = "high"
        reasons.append("high-risk domain path")
    elif any(x in text for x in MED_TERMS) or len(paths) > 3:
        risk = "medium"
        reasons.append("cross-boundary or multi-file surface")

    changed_ids = {f"file:{p}" for p in paths}
    direct_dependents = sum(
        1 for e in graph.get("edges", [])
        if e.get("relation") == "DEPENDS_ON" and e.get("target") in changed_ids
    )
    if direct_dependents >= 8:
        risk = "high"
        reasons.append(f"{direct_dependents} direct structural dependents")
    elif direct_dependents >= 3 and risk == "low":
        risk = "medium"
        reasons.append(f"{direct_dependents} direct structural dependents")
    if any(x.get("distance", 0) >= 2 for x in affected) and risk == "low":
        risk = "medium"
        reasons.append("transitive structural impact")
    if not tests and affected and risk == "medium":
        reasons.append("no structurally mapped tests for affected surface")
    return risk, reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--git-diff", action="store_true")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--max-depth", type=int, default=2)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    graph = read_json(state_root(root) / "repository/graph.json", {})

    paths = changed_from_git(root) if ns.git_diff or not ns.files else ns.files
    if graph.get("schema_version", 0) >= 2:
        affected = dependents_for_files(graph, paths, max_depth=ns.max_depth).get("affected", [])
        mode = "structural"
    else:
        affected = fallback_dependents(paths, graph)
        mode = "fallback"

    tests = test_paths(graph, paths, affected) if graph else []
    risk, reasons = risk_for(paths, affected, graph, tests)
    out = {
        "changed_files": paths, "impact_mode": mode, "affected": affected[:100],
        "likely_dependents": [x["path"] for x in affected[:50]],
        "related_tests": [x["path"] for x in tests[:50]], "test_evidence": tests[:50],
        "blast_radius": risk, "risk_reasons": reasons,
        "recommended_verification": {"low": "V2 targeted", "medium": "V3 targeted + subsystem", "high": "V4/V5 as applicable"}[risk],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
