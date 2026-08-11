#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from common import read_json, read_jsonl, state_root
from graph_query import bounded_expand, find_nodes


def terms(q: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-zA-Z0-9_./-]{3,}", q.lower())
        if x not in {"this", "that", "with", "from", "untuk", "yang", "dan", "the"}
    }


def lexical_score_file(f: dict, ts: set[str]) -> float:
    path = f["path"].lower()
    syms = " ".join(f.get("symbols", [])).lower()
    imps = " ".join(f.get("imports", [])).lower()
    score = 0.0
    for t in ts:
        if t in path:
            score += 8
        if t in syms:
            score += 6
        if t in imps:
            score += 2
    if f.get("is_test"):
        score *= 0.72
    return score


def task_depth_budget(task: dict) -> int:
    return {"FAST": 1, "NORMAL": 1, "DEEP": 2, "CRITICAL": 2}.get(task.get("depth"), 1)


def relevant_knowledge(state: Path, ts: set[str]) -> list[dict]:
    rows = []
    for kind, fn in [
        ("decision", "decisions.jsonl"), ("constraint", "constraints.jsonl"),
        ("interface", "interfaces.jsonl"), ("pattern", "patterns.jsonl"), ("bug", "bugs.jsonl"),
    ]:
        for e in read_jsonl(state / "registry" / fn):
            if e.get("status", "ACTIVE") != "ACTIVE":
                continue
            blob = json.dumps(e, ensure_ascii=False).lower()
            hits = sum(1 for t in ts if t in blob)
            if hits:
                rows.append({
                    "kind": kind, "id": e.get("id"), "score": hits,
                    "text": e.get("text"), "freshness": e.get("_freshness", e.get("freshness")),
                })
    rows.sort(key=lambda x: (-x["score"], x.get("id") or ""))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--query", required=True)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--max-nodes", type=int, default=60)
    ap.add_argument("--no-write", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    s = state_root(root)
    graph = read_json(s / "repository/graph.json", {})
    if not graph:
        raise SystemExit("repository graph missing; run repo_graph.py build")

    ts = terms(ns.query)
    task = read_json(s / "tasks/active.json", {})
    depth = task_depth_budget(task)
    file_records = {f["path"]: f for f in graph.get("files", [])}
    file_scores: defaultdict[str, float] = defaultdict(float)
    reasons: defaultdict[str, list[dict]] = defaultdict(list)

    for f in graph.get("files", []):
        score = lexical_score_file(f, ts)
        if score > 0:
            file_scores[f["path"]] += score
            reasons[f["path"]].append({"kind": "lexical", "score": round(score, 2)})

    seeds = find_nodes(graph, ns.query, limit=8)
    seed_ids = [x["id"] for x in seeds]
    expanded = bounded_expand(
        graph, seed_ids, depth=depth, max_nodes=ns.max_nodes,
        relations={"DEFINES", "CALLS", "REFERENCES", "IMPORTS", "DEPENDS_ON", "INHERITS", "IMPLEMENTS", "TESTS", "CONTAINS"},
    )
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    for node_id, meta in expanded.items():
        n = nodes.get(node_id, {})
        path = n.get("path")
        if not path or path not in file_records:
            continue
        distance = int(meta.get("distance", 0))
        graph_score = 20.0 if distance == 0 else max(4.0, 14.0 - (distance * 5.0))
        if file_records[path].get("is_test") and distance > 0:
            graph_score += 2.0
        file_scores[path] += graph_score
        reasons[path].append({
            "kind": "graph", "node_id": node_id, "distance": distance,
            "relation": meta.get("relation"), "provenance": meta.get("provenance"), "score": graph_score,
        })

    ranked = sorted(file_scores.items(), key=lambda x: (-x[1], x[0]))
    files = []
    for path, score in ranked[:ns.top]:
        f = file_records[path]
        files.append({
            "path": path, "score": round(score, 2), "symbols": f.get("symbols", [])[:20],
            "is_test": f.get("is_test", False), "parser": f.get("parser"), "reasons": reasons[path][:8],
        })

    knowledge = relevant_knowledge(s, ts)[:12]
    out = {
        "query": ns.query, "graph_schema_version": graph.get("schema_version"),
        "graph_assisted": graph.get("schema_version", 0) >= 2, "expansion_depth": depth,
        "seed_nodes": [{"id": x["id"], "label": x.get("label"), "path": x.get("path")} for x in seeds],
        "files": files, "knowledge": knowledge,
    }
    if not ns.no_write and task:
        task["working_set"] = [x["path"] for x in files]
        task["working_set_evidence"] = {x["path"]: x["reasons"] for x in files}
        task["relevant_knowledge"] = [x["id"] for x in knowledge]
        task["structural_intelligence"] = {
            "graph_schema_version": graph.get("schema_version"), "expansion_depth": depth,
            "seed_nodes": [x["id"] for x in seeds],
        }
        from common import write_json
        write_json(s / "tasks/active.json", task)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
