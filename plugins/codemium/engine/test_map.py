#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from common import now_iso, read_json, state_root, write_json

PROV_RANK = {"DIRECT": 3, "RESOLVED": 2, "HEURISTIC": 1}


def legacy_related(src: dict, test: dict) -> int:
    sp = Path(src["path"])
    tp = Path(test["path"])
    score = 0
    stem = sp.stem.replace(".service", "").replace(".controller", "").replace(".repository", "")
    if stem and stem.lower() in tp.name.lower():
        score += 8
    if sp.parent.name and sp.parent.name.lower() in test["path"].lower():
        score += 2
    srcparts = {sp.stem.lower(), sp.name.lower(), sp.parent.name.lower()}
    imports = " ".join(test.get("imports", [])).lower()
    score += sum(3 for p in srcparts if p and p in imports)
    return score


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", default=".")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    s = state_root(root)
    graph = read_json(s / "repository/graph.json", {})
    if not graph:
        raise SystemExit("repository graph missing")

    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    relationships: dict[tuple[str, str], dict] = {}

    if graph.get("schema_version", 0) >= 2:
        for edge in graph.get("edges", []):
            if edge.get("relation") != "TESTS":
                continue
            test_node = nodes.get(edge.get("source"), {})
            target_node = nodes.get(edge.get("target"), {})
            test_path = test_node.get("path")
            src_path = target_node.get("path")
            if not test_path or not src_path or test_path == src_path:
                continue
            key = (src_path, test_path)
            row = {
                "source": src_path, "test": test_path,
                "provenance": edge.get("provenance", "RESOLVED"),
                "relation": "TESTS", "target_node": edge.get("target"),
            }
            old = relationships.get(key)
            if not old or PROV_RANK.get(row["provenance"], 0) > PROV_RANK.get(old["provenance"], 0):
                relationships[key] = row

    sources = [f for f in graph.get("files", []) if not f.get("is_test")]
    tests = [f for f in graph.get("files", []) if f.get("is_test")]
    for src in sources:
        if any(k[0] == src["path"] for k in relationships):
            continue
        rs = [(legacy_related(src, t), t["path"]) for t in tests]
        for score, test_path in sorted([x for x in rs if x[0] > 0], key=lambda x: (-x[0], x[1]))[:12]:
            relationships[(src["path"], test_path)] = {
                "source": src["path"], "test": test_path, "provenance": "HEURISTIC",
                "relation": "TESTS", "score": score,
            }

    mapping: defaultdict[str, list[str]] = defaultdict(list)
    provenance_counts: defaultdict[str, int] = defaultdict(int)
    rows = sorted(relationships.values(), key=lambda x: (x["source"], -PROV_RANK.get(x["provenance"], 0), x["test"]))
    for row in rows:
        if row["test"] not in mapping[row["source"]]:
            mapping[row["source"]].append(row["test"])
        provenance_counts[row["provenance"]] += 1

    out = {
        "schema_version": 2, "generated_at": now_iso(), "source_count": len(sources),
        "test_count": len(tests), "mapped_sources": len(mapping), "mapping": dict(mapping),
        "relationships": rows, "provenance_counts": dict(sorted(provenance_counts.items())),
    }
    write_json(s / "repository/tests.json", out)
    print(json.dumps({
        "mapped_sources": len(mapping), "tests": len(tests), "relationships": len(rows),
        "provenance_counts": out["provenance_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
