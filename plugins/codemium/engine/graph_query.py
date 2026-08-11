#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path

from common import read_json, state_root

REVERSE_RELATIONS = {
    "CALLS": "CALLED_BY",
    "DEPENDS_ON": "DEPENDENT_OF",
    "IMPORTS": "IMPORTED_BY",
    "REFERENCES": "REFERENCED_BY",
    "INHERITS": "PARENT_OF",
    "IMPLEMENTS": "IMPLEMENTED_BY",
    "TESTS": "TESTED_BY",
}


def load_graph(root: Path) -> dict:
    graph = read_json(state_root(root) / "repository/graph.json", {})
    if not graph:
        raise SystemExit("repository graph missing; run repo_graph.py build")
    return graph


def indices(graph: dict) -> tuple[dict[str, dict], dict[str, list[dict]], dict[str, list[dict]]]:
    nodes = {n["id"]: n for n in graph.get("nodes", []) if n.get("id")}
    out: defaultdict[str, list[dict]] = defaultdict(list)
    inc: defaultdict[str, list[dict]] = defaultdict(list)
    for edge in graph.get("edges", []):
        out[edge["source"]].append(edge)
        inc[edge["target"]].append(edge)
    return nodes, dict(out), dict(inc)


def terms(text: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-zA-Z0-9_./:-]{2,}", text.lower())
        if x not in {"this", "that", "with", "from", "the", "and", "for", "yang", "dan", "untuk"}
    }


def find_nodes(graph: dict, query: str, limit: int = 20) -> list[dict]:
    ts = terms(query)
    ranked: list[tuple[float, dict]] = []
    for n in graph.get("nodes", []):
        blob = " ".join(str(n.get(k, "")) for k in ("label", "qualified_name", "path", "subtype")).lower()
        score = 0.0
        for t in ts:
            if t == str(n.get("label", "")).lower():
                score += 12
            elif t in str(n.get("qualified_name", "")).lower():
                score += 9
            elif t in str(n.get("path", "")).lower():
                score += 7
            elif t in blob:
                score += 3
        if score:
            if n.get("type") == "SYMBOL":
                score += 1
            ranked.append((score, n))
    ranked.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [{**n, "_score": score} for score, n in ranked[:limit]]


def neighbors(graph: dict, node_id: str, relations: set[str] | None = None,
              direction: str = "both") -> list[dict]:
    nodes, out, inc = indices(graph)
    rows: list[dict] = []
    if direction in {"out", "both"}:
        for e in out.get(node_id, []):
            if relations and e["relation"] not in relations:
                continue
            rows.append({"direction": "out", "edge": e, "node": nodes.get(e["target"])})
    if direction in {"in", "both"}:
        for e in inc.get(node_id, []):
            if relations and e["relation"] not in relations:
                continue
            rows.append({"direction": "in", "edge": e, "node": nodes.get(e["source"])})
    return rows


def shortest_path(graph: dict, start: str, goal: str, max_depth: int = 6) -> list[dict]:
    nodes, out, inc = indices(graph)
    if start not in nodes or goal not in nodes:
        return []
    q = deque([(start, [])])
    seen = {start}
    while q:
        current, path = q.popleft()
        if len(path) >= max_depth:
            continue
        links = []
        for e in out.get(current, []):
            links.append((e["target"], e, "out"))
        for e in inc.get(current, []):
            links.append((e["source"], e, "in"))
        for nxt, edge, direction in links:
            if nxt in seen:
                continue
            step = {
                "from": current, "to": nxt,
                "relation": edge["relation"],
                "direction": direction,
                "provenance": edge.get("provenance"),
            }
            next_path = path + [step]
            if nxt == goal:
                return next_path
            seen.add(nxt)
            q.append((nxt, next_path))
    return []


def seed_nodes(graph: dict, query: str, limit: int = 8) -> list[str]:
    return [n["id"] for n in find_nodes(graph, query, limit)]


def bounded_expand(graph: dict, seeds: list[str], depth: int = 1, max_nodes: int = 60,
                   relations: set[str] | None = None) -> dict[str, dict]:
    nodes, out, inc = indices(graph)
    result: dict[str, dict] = {}
    q = deque()
    for seed in seeds:
        if seed in nodes:
            result[seed] = {"distance": 0, "via": None, "relation": None, "provenance": None}
            q.append(seed)
    while q and len(result) < max_nodes:
        current = q.popleft()
        d = result[current]["distance"]
        if d >= depth:
            continue
        links = []
        for e in out.get(current, []):
            if not relations or e["relation"] in relations:
                links.append((e["target"], e, "out"))
        for e in inc.get(current, []):
            if not relations or e["relation"] in relations:
                links.append((e["source"], e, "in"))
        for nxt, edge, direction in links:
            if nxt in result or nxt not in nodes:
                continue
            result[nxt] = {
                "distance": d + 1,
                "via": current,
                "relation": edge["relation"],
                "direction": direction,
                "provenance": edge.get("provenance"),
            }
            if len(result) >= max_nodes:
                break
            q.append(nxt)
    return result


def dependents_for_files(graph: dict, files: list[str], max_depth: int = 2,
                         max_nodes: int = 250) -> dict:
    nodes, out, inc = indices(graph)
    starts = {f"file:{p}" for p in files if f"file:{p}" in nodes}
    q = deque((sid, 0) for sid in starts)
    seen = set(starts)
    affected: dict[str, dict] = {}
    relevant_relations = {"DEPENDS_ON", "CALLS", "REFERENCES", "IMPORTS", "INHERITS", "IMPLEMENTS", "TESTS"}

    while q and len(seen) < max_nodes:
        current, depth = q.popleft()
        if depth >= max_depth:
            continue
        for e in inc.get(current, []):
            if e["relation"] not in relevant_relations:
                continue
            src = e["source"]
            if src in seen:
                continue
            seen.add(src)
            n = nodes.get(src, {})
            path = n.get("path")
            if path and path not in files:
                row = affected.setdefault(path, {
                    "path": path,
                    "distance": depth + 1,
                    "relations": [],
                    "provenance": [],
                })
                row["distance"] = min(row["distance"], depth + 1)
                row["relations"].append(e["relation"])
                row["provenance"].append(e.get("provenance"))
            q.append((src, depth + 1))

        if current.startswith("file:"):
            for e in out.get(current, []):
                if e["relation"] != "CONTAINS":
                    continue
                module = e["target"]
                for de in out.get(module, []):
                    if de["relation"] == "DEFINES" and de["target"] not in seen:
                        seen.add(de["target"])
                        q.appendleft((de["target"], depth))
    return {"affected": sorted(affected.values(), key=lambda x: (x["distance"], x["path"]))}


def tests_for(graph: dict, target_id: str) -> list[dict]:
    nodes, _, inc = indices(graph)
    out = []
    for e in inc.get(target_id, []):
        if e["relation"] == "TESTS":
            n = nodes.get(e["source"], {})
            out.append({
                "path": n.get("path"),
                "node_id": e["source"],
                "provenance": e.get("provenance"),
                "line": e.get("line"),
            })
    return out


def resolve_one(graph: dict, value: str) -> str | None:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    if value in nodes:
        return value
    found = find_nodes(graph, value, 2)
    if not found:
        return None
    return found[0]["id"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find-symbol")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("neighbors")
    p.add_argument("node")
    p.add_argument("--direction", choices=["in", "out", "both"], default="both")
    p.add_argument("--relation", action="append")

    for name in ["callers", "callees", "dependents", "dependencies", "tests-for"]:
        p = sub.add_parser(name)
        p.add_argument("node")

    p = sub.add_parser("path")
    p.add_argument("start")
    p.add_argument("goal")
    p.add_argument("--max-depth", type=int, default=6)

    p = sub.add_parser("impact")
    p.add_argument("files", nargs="+")
    p.add_argument("--max-depth", type=int, default=2)

    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    graph = load_graph(root)

    if ns.cmd == "find-symbol":
        result = find_nodes(graph, ns.query, ns.limit)
    elif ns.cmd == "neighbors":
        node = resolve_one(graph, ns.node)
        result = neighbors(graph, node, set(ns.relation or []), ns.direction) if node else []
    elif ns.cmd in {"callers", "callees", "dependents", "dependencies", "tests-for"}:
        node = resolve_one(graph, ns.node)
        if not node:
            result = []
        elif ns.cmd == "callers":
            result = neighbors(graph, node, {"CALLS"}, "in")
        elif ns.cmd == "callees":
            result = neighbors(graph, node, {"CALLS"}, "out")
        elif ns.cmd == "dependents":
            result = neighbors(graph, node, {"DEPENDS_ON", "IMPORTS", "REFERENCES", "CALLS"}, "in")
        elif ns.cmd == "dependencies":
            result = neighbors(graph, node, {"DEPENDS_ON", "IMPORTS", "REFERENCES", "CALLS"}, "out")
        else:
            result = tests_for(graph, node)
    elif ns.cmd == "path":
        a, b = resolve_one(graph, ns.start), resolve_one(graph, ns.goal)
        result = shortest_path(graph, a, b, ns.max_depth) if a and b else []
    else:
        result = dependents_for_files(graph, ns.files, ns.max_depth)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
