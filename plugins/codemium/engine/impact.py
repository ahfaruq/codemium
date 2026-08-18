#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import git, read_json, state_root
from graph_query import dependents_for_files, dependents_for_nodes

HIGH_TERMS = ["auth", "permission", "security", "payment", "billing", "migration", "infra", "deploy", "secret", "token"]
MED_TERMS = ["api", "worker", "queue", "webhook", "database", "repository", "service"]
HUNK_RE = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@")


def changed_from_git(root: Path) -> list[str]:
    names = set()
    for args in [("diff", "--name-only"), ("diff", "--cached", "--name-only")]:
        out = git(root, *args) or ""; names.update(x for x in out.splitlines() if x)
    return sorted(names)


def changed_line_ranges(root: Path) -> dict[str, list[tuple[int, int]]]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    for args in [("diff", "--unified=0", "--no-color"), ("diff", "--cached", "--unified=0", "--no-color")]:
        out = git(root, *args) or ""; current: str | None = None
        for line in out.splitlines():
            if line.startswith("+++ b/"):
                current = line[6:]; ranges.setdefault(current, [])
            elif line.startswith("+++ /dev/null"):
                current = None
            elif current and line.startswith("@@"):
                m = HUNK_RE.match(line)
                if not m: continue
                start = int(m.group(1)); count = int(m.group(2) or "1")
                if count > 0: ranges[current].append((start, start + count - 1))
    return ranges


def changed_symbol_seeds(graph: dict, paths: list[str], ranges: dict[str, list[tuple[int, int]]]) -> tuple[list[str], list[dict]]:
    seeds: list[str] = []; evidence: list[dict] = []
    symbols_by_path: dict[str, list[dict]] = {}
    for n in graph.get("nodes", []):
        if n.get("type") == "SYMBOL" and n.get("path"): symbols_by_path.setdefault(n["path"], []).append(n)
    for path in paths:
        hits = []
        for n in symbols_by_path.get(path, []):
            a, b = n.get("line_start"), n.get("line_end")
            if not isinstance(a, int) or not isinstance(b, int): continue
            if any(not (end < a or start > b) for start, end in ranges.get(path, [])): hits.append(n)
        if hits:
            for n in hits:
                if n["id"] not in seeds: seeds.append(n["id"])
                evidence.append({"path": path, "node_id": n["id"], "symbol": n.get("qualified_name") or n.get("label"), "line_start": n.get("line_start"), "line_end": n.get("line_end")})
        else:
            fid = f"file:{path}"
            if any(n.get("id") == fid for n in graph.get("nodes", [])): seeds.append(fid)
            evidence.append({"path": path, "node_id": fid, "symbol": None})
    return seeds, evidence


def fallback_dependents(paths: list[str], graph: dict) -> list[dict]:
    changed = set(paths); affected = set()
    for p in paths:
        base = Path(p).stem.lower(); name = Path(p).name.lower()
        for f in graph.get("files", []):
            if f["path"] in changed: continue
            blob = " ".join(f.get("imports", [])).lower()
            if base and (base in blob or name in blob): affected.add(f["path"])
    return [{"path": p, "distance": 1, "score": 0.35, "confidence": "low", "relations": ["IMPORTS"], "provenance": ["HEURISTIC"], "cross_language": False} for p in sorted(affected)]


def _test_kind(path: str) -> str:
    low = path.lower()
    if any(x in low for x in ["/e2e/", ".e2e.", "playwright", "cypress"]): return "e2e"
    if any(x in low for x in ["/integration/", ".integration.", "contract", "api_test"]): return "integration"
    return "unit"


def test_paths(graph: dict, changed: list[str], affected: list[dict]) -> list[dict]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}; changed_set = set(changed); affected_score = {x["path"]: x.get("score", 0.3) for x in affected}; rows: dict[str, dict] = {}
    for e in graph.get("edges", []):
        if e.get("relation") != "TESTS": continue
        test = nodes.get(e["source"], {}); target = nodes.get(e["target"], {}); tp, sp = test.get("path"), target.get("path")
        if not tp or not sp or sp not in changed_set | set(affected_score): continue
        prov = e.get("provenance", "HEURISTIC"); prov_score = {"DIRECT": 1.0, "RESOLVED": 0.9, "HEURISTIC": 0.45}.get(prov, 0.4)
        target_score = 1.0 if sp in changed_set else affected_score.get(sp, 0.3); score = round(prov_score * target_score, 4)
        row = {"path": tp, "kind": _test_kind(tp), "score": score, "confidence": "high" if prov in {"DIRECT", "RESOLVED"} else "low", "provenance": prov, "target_path": sp, "target": e.get("target"), "source_file": e.get("source_file"), "evidence_kind": e.get("evidence_kind"), "cross_language": bool(e.get("cross_language"))}
        if tp not in rows or row["score"] > rows[tp]["score"]: rows[tp] = row
    return sorted(rows.values(), key=lambda x: (-x["score"], {"unit": 0, "integration": 1, "e2e": 2}[x["kind"]], x["path"]))


def risk_for(paths: list[str], affected: list[dict], graph: dict, tests: list[dict]) -> tuple[str, list[str]]:
    text = " ".join(paths + [x["path"] for x in affected]).lower(); reasons = []; risk = "low"
    if any(x in text for x in HIGH_TERMS): risk = "high"; reasons.append("high-risk domain path")
    elif any(x in text for x in MED_TERMS) or len(paths) > 3: risk = "medium"; reasons.append("cross-boundary or multi-file surface")
    high_conf = [x for x in affected if x.get("confidence") == "high" and x.get("score", 0) >= 0.55]
    if len(high_conf) >= 8: risk = "high"; reasons.append(f"{len(high_conf)} high-confidence structural dependents")
    elif len(high_conf) >= 3 and risk == "low": risk = "medium"; reasons.append(f"{len(high_conf)} high-confidence structural dependents")
    if any(x.get("cross_language") and x.get("score", 0) >= 0.5 for x in affected):
        if risk == "low": risk = "medium"
        reasons.append("cross-language dependency boundary")
    if any(x.get("distance", 0) >= 2 and x.get("score", 0) >= 0.4 for x in affected) and risk == "low": risk = "medium"; reasons.append("transitive structural impact")
    if not tests and affected and risk in {"medium", "high"}: reasons.append("no structurally mapped tests for affected surface")
    return risk, list(dict.fromkeys(reasons))


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--git-diff", action="store_true"); ap.add_argument("--files", nargs="*"); ap.add_argument("--max-depth", type=int, default=2); ns = ap.parse_args()
    root = Path(ns.root).resolve(); graph = read_json(state_root(root) / "repository/graph.json", {}); paths = changed_from_git(root) if ns.git_diff or not ns.files else ns.files
    ranges = changed_line_ranges(root) if ns.git_diff or not ns.files else {}
    seed_evidence: list[dict] = []
    if graph.get("schema_version", 0) >= 3:
        seeds, seed_evidence = changed_symbol_seeds(graph, paths, ranges)
        result = dependents_for_nodes(graph, seeds, changed_files=paths, max_depth=ns.max_depth); affected = result.get("affected", []); mode = "symbol-structural" if any(x.get("symbol") for x in seed_evidence) else "structural"
    elif graph.get("schema_version", 0) >= 2:
        affected = dependents_for_files(graph, paths, max_depth=ns.max_depth).get("affected", []); mode = "structural"
    else:
        affected = fallback_dependents(paths, graph); mode = "fallback"
    tests = test_paths(graph, paths, affected) if graph else []; risk, reasons = risk_for(paths, affected, graph, tests)
    test_plan = [{"path": x["path"], "kind": x["kind"], "priority": "P0" if x["score"] >= 0.75 else "P1" if x["score"] >= 0.45 else "P2", "score": x["score"], "confidence": x["confidence"], "target_path": x["target_path"], "evidence_kind": x.get("evidence_kind")} for x in tests[:50]]
    out = {
        "changed_files": paths, "changed_ranges": {k: [list(x) for x in v] for k, v in ranges.items()}, "impact_mode": mode, "seed_evidence": seed_evidence,
        "affected": affected[:100], "likely_dependents": [x["path"] for x in affected[:50]], "cross_language_dependents": [x["path"] for x in affected if x.get("cross_language")][:50],
        "related_tests": [x["path"] for x in tests[:50]], "test_evidence": tests[:50], "test_plan": test_plan,
        "blast_radius": risk, "risk_reasons": reasons, "recommended_verification": {"low": "V2 targeted", "medium": "V3 targeted + subsystem", "high": "V4/V5 as applicable"}[risk],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__": main()
