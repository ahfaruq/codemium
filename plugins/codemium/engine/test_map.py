#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from common import now_iso, read_json, state_root, write_json

PROV_RANK = {"DIRECT": 3, "RESOLVED": 2, "HEURISTIC": 1}
PROV_SCORE = {"DIRECT": 1.0, "RESOLVED": 0.9, "HEURISTIC": 0.4}


def test_kind(path: str) -> str:
    low = path.lower()
    if any(x in low for x in ["/e2e/", ".e2e.", "playwright", "cypress"]): return "e2e"
    if any(x in low for x in ["/integration/", ".integration.", "contract", "api_test"]): return "integration"
    return "unit"


def legacy_related(src: dict, test: dict) -> int:
    sp = Path(src["path"]); tp = Path(test["path"]); score = 0
    stem = sp.stem.replace(".service", "").replace(".controller", "").replace(".repository", "")
    if stem and stem.lower() in tp.name.lower(): score += 8
    if sp.parent.name and sp.parent.name.lower() in test["path"].lower(): score += 2
    srcparts = {sp.stem.lower(), sp.name.lower(), sp.parent.name.lower()}; imports = " ".join(test.get("imports", [])).lower(); score += sum(3 for p in srcparts if p and p in imports)
    return score


def main() -> None:
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True); b = sub.add_parser("build"); b.add_argument("--root", default="."); ns = ap.parse_args()
    root = Path(ns.root).resolve(); s = state_root(root); graph = read_json(s / "repository/graph.json", {})
    if not graph: raise SystemExit("repository graph missing")
    nodes = {n["id"]: n for n in graph.get("nodes", [])}; relationships: dict[tuple[str, str], dict] = {}

    if graph.get("schema_version", 0) >= 2:
        for edge in graph.get("edges", []):
            if edge.get("relation") != "TESTS": continue
            test_node = nodes.get(edge.get("source"), {}); target_node = nodes.get(edge.get("target"), {}); test_path = test_node.get("path"); src_path = target_node.get("path")
            if not test_path or not src_path or test_path == src_path: continue
            prov = edge.get("provenance", "RESOLVED"); evidence_kind = edge.get("evidence_kind", "structural")
            evidence_bonus = {"call": 0.12, "reference": 0.08, "import": 0.05, "structural": 0.0}.get(evidence_kind, 0.0)
            row = {
                "source": src_path, "test": test_path, "kind": test_kind(test_path), "provenance": prov,
                "confidence": "high" if prov in {"DIRECT", "RESOLVED"} else "low", "relation": "TESTS",
                "target_node": edge.get("target"), "evidence_kind": evidence_kind, "cross_language": bool(edge.get("cross_language")),
                "score": round(min(1.0, PROV_SCORE.get(prov, 0.35) + evidence_bonus), 3),
            }
            key = (src_path, test_path); old = relationships.get(key)
            if not old or row["score"] > old.get("score", 0): relationships[key] = row

    sources = [f for f in graph.get("files", []) if not f.get("is_test")]; tests = [f for f in graph.get("files", []) if f.get("is_test")]
    for src in sources:
        if any(k[0] == src["path"] for k in relationships): continue
        rs = [(legacy_related(src, t), t["path"]) for t in tests]
        for score, test_path in sorted([x for x in rs if x[0] > 0], key=lambda x: (-x[0], x[1]))[:12]:
            relationships[(src["path"], test_path)] = {"source": src["path"], "test": test_path, "kind": test_kind(test_path), "provenance": "HEURISTIC", "confidence": "low", "relation": "TESTS", "evidence_kind": "naming/import fallback", "cross_language": False, "score": round(min(0.39, score / 30), 3)}

    mapping: defaultdict[str, list[str]] = defaultdict(list); provenance_counts: defaultdict[str, int] = defaultdict(int); kind_counts: defaultdict[str, int] = defaultdict(int)
    rows = sorted(relationships.values(), key=lambda x: (x["source"], -x.get("score", 0), x["test"]))
    for row in rows:
        if row["test"] not in mapping[row["source"]]: mapping[row["source"]].append(row["test"])
        provenance_counts[row["provenance"]] += 1; kind_counts[row["kind"]] += 1
    prioritized = sorted(rows, key=lambda x: (-x.get("score", 0), {"unit": 0, "integration": 1, "e2e": 2}.get(x["kind"], 3), x["test"]))
    out = {
        "schema_version": 3, "generated_at": now_iso(), "source_count": len(sources), "test_count": len(tests), "mapped_sources": len(mapping), "mapping": dict(mapping),
        "relationships": rows, "prioritized": prioritized, "provenance_counts": dict(sorted(provenance_counts.items())), "kind_counts": dict(sorted(kind_counts.items())),
        "cross_language_relationships": sum(1 for x in rows if x.get("cross_language")),
    }
    write_json(s / "repository/tests.json", out)
    print(json.dumps({"mapped_sources": len(mapping), "tests": len(tests), "relationships": len(rows), "provenance_counts": out["provenance_counts"], "kind_counts": out["kind_counts"], "cross_language_relationships": out["cross_language_relationships"]}, indent=2))


if __name__ == "__main__": main()
