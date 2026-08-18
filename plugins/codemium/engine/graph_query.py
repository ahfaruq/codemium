#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path

from common import read_json, state_root

REVERSE_RELATIONS = {
    "CALLS": "CALLED_BY", "DEPENDS_ON": "DEPENDENT_OF", "IMPORTS": "IMPORTED_BY",
    "IMPORTS_SYMBOL": "SYMBOL_IMPORTED_BY", "REFERENCES": "REFERENCED_BY",
    "INHERITS": "PARENT_OF", "IMPLEMENTS": "IMPLEMENTED_BY", "TESTS": "TESTED_BY",
}
IMPACT_RELATIONS = {"DEPENDS_ON", "CALLS", "REFERENCES", "IMPORTS", "IMPORTS_SYMBOL", "INHERITS", "IMPLEMENTS", "TESTS"}
RELATION_WEIGHT = {"CALLS": 1.0, "IMPORTS_SYMBOL": 0.95, "INHERITS": 0.95, "IMPLEMENTS": 0.95, "REFERENCES": 0.8, "DEPENDS_ON": 0.75, "IMPORTS": 0.7, "TESTS": 0.65}
PROVENANCE_WEIGHT = {"DIRECT": 1.0, "RESOLVED": 0.9, "HEURISTIC": 0.45}


def load_graph(root: Path) -> dict:
    graph = read_json(state_root(root) / "repository/graph.json", {})
    if not graph: raise SystemExit("repository graph missing; run repo_graph.py build")
    return graph


def indices(graph: dict) -> tuple[dict[str, dict], dict[str, list[dict]], dict[str, list[dict]]]:
    nodes = {n["id"]: n for n in graph.get("nodes", []) if n.get("id")}
    out: defaultdict[str, list[dict]] = defaultdict(list); inc: defaultdict[str, list[dict]] = defaultdict(list)
    for edge in graph.get("edges", []): out[edge["source"]].append(edge); inc[edge["target"]].append(edge)
    return nodes, dict(out), dict(inc)


def terms(text: str) -> set[str]:
    return {x for x in re.findall(r"[a-zA-Z0-9_./:-]{2,}", text.lower()) if x not in {"this", "that", "with", "from", "the", "and", "for", "yang", "dan", "untuk"}}


def find_nodes(graph: dict, query: str, limit: int = 20) -> list[dict]:
    ts = terms(query); ranked: list[tuple[float, dict]] = []
    for n in graph.get("nodes", []):
        blob = " ".join(str(n.get(k, "")) for k in ("label", "qualified_name", "path", "subtype", "language")).lower(); score = 0.0
        for t in ts:
            if t == str(n.get("label", "")).lower(): score += 12
            elif t in str(n.get("qualified_name", "")).lower(): score += 9
            elif t in str(n.get("path", "")).lower(): score += 7
            elif t in blob: score += 3
        if score:
            if n.get("type") == "SYMBOL": score += 1
            ranked.append((score, n))
    ranked.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [{**n, "_score": score} for score, n in ranked[:limit]]


def neighbors(graph: dict, node_id: str, relations: set[str] | None = None, direction: str = "both") -> list[dict]:
    nodes, out, inc = indices(graph); rows: list[dict] = []
    if direction in {"out", "both"}:
        for e in out.get(node_id, []):
            if not relations or e["relation"] in relations: rows.append({"direction": "out", "edge": e, "node": nodes.get(e["target"])})
    if direction in {"in", "both"}:
        for e in inc.get(node_id, []):
            if not relations or e["relation"] in relations: rows.append({"direction": "in", "edge": e, "node": nodes.get(e["source"])})
    return rows


def shortest_path(graph: dict, start: str, goal: str, max_depth: int = 6) -> list[dict]:
    nodes, out, inc = indices(graph)
    if start not in nodes or goal not in nodes: return []
    q = deque([(start, [])]); seen = {start}
    while q:
        current, path = q.popleft()
        if len(path) >= max_depth: continue
        links = [(e["target"], e, "out") for e in out.get(current, [])] + [(e["source"], e, "in") for e in inc.get(current, [])]
        for nxt, edge, direction in links:
            if nxt in seen: continue
            step = {"from": current, "to": nxt, "relation": edge["relation"], "direction": direction, "provenance": edge.get("provenance"), "cross_language": bool(edge.get("cross_language"))}
            next_path = path + [step]
            if nxt == goal: return next_path
            seen.add(nxt); q.append((nxt, next_path))
    return []


def seed_nodes(graph: dict, query: str, limit: int = 8) -> list[str]: return [n["id"] for n in find_nodes(graph, query, limit)]


def bounded_expand(graph: dict, seeds: list[str], depth: int = 1, max_nodes: int = 60, relations: set[str] | None = None) -> dict[str, dict]:
    nodes, out, inc = indices(graph); result: dict[str, dict] = {}; q = deque()
    for seed in seeds:
        if seed in nodes: result[seed] = {"distance": 0, "via": None, "relation": None, "provenance": None}; q.append(seed)
    while q and len(result) < max_nodes:
        current = q.popleft(); d = result[current]["distance"]
        if d >= depth: continue
        links = [(e["target"], e, "out") for e in out.get(current, []) if not relations or e["relation"] in relations] + [(e["source"], e, "in") for e in inc.get(current, []) if not relations or e["relation"] in relations]
        for nxt, edge, direction in links:
            if nxt in result or nxt not in nodes: continue
            result[nxt] = {"distance": d + 1, "via": current, "relation": edge["relation"], "direction": direction, "provenance": edge.get("provenance"), "cross_language": bool(edge.get("cross_language"))}
            if len(result) >= max_nodes: break
            q.append(nxt)
    return result


def _confidence(provenance: list[str]) -> str:
    vals = set(x for x in provenance if x)
    if "DIRECT" in vals or ("RESOLVED" in vals and "HEURISTIC" not in vals): return "high"
    if "RESOLVED" in vals: return "medium"
    return "low"


def dependents_for_nodes(graph: dict, seed_ids: list[str], changed_files: list[str] | None = None, max_depth: int = 2, max_nodes: int = 300) -> dict:
    nodes, out, inc = indices(graph); starts = {sid for sid in seed_ids if sid in nodes}; changed = set(changed_files or [])
    q = deque((sid, 0, 1.0) for sid in starts); best_depth = {sid: 0 for sid in starts}; affected: dict[str, dict] = {}; visited = 0
    while q and visited < max_nodes:
        current, depth, path_score = q.popleft(); visited += 1
        if depth >= max_depth: continue
        for e in inc.get(current, []):
            if e["relation"] not in IMPACT_RELATIONS: continue
            src = e["source"]; n = nodes.get(src, {})
            rel_w = RELATION_WEIGHT.get(e["relation"], 0.5); prov_w = PROVENANCE_WEIGHT.get(e.get("provenance"), 0.45)
            next_score = path_score * rel_w * prov_w * (0.82 ** depth); next_depth = depth + 1; path = n.get("path")
            if path and path not in changed:
                row = affected.setdefault(path, {"path": path, "language": n.get("language"), "distance": next_depth, "score": 0.0, "relations": [], "provenance": [], "cross_language": False, "evidence": []})
                row["distance"] = min(row["distance"], next_depth); row["score"] = min(1.0, row["score"] + next_score)
                if e["relation"] not in row["relations"]: row["relations"].append(e["relation"])
                if e.get("provenance") not in row["provenance"]: row["provenance"].append(e.get("provenance"))
                row["cross_language"] = row["cross_language"] or bool(e.get("cross_language"))
                row["evidence"].append({"relation": e["relation"], "provenance": e.get("provenance"), "source_file": e.get("source_file"), "line": e.get("line"), "from": src, "to": current})
            if best_depth.get(src, 999) > next_depth:
                best_depth[src] = next_depth; q.append((src, next_depth, next_score))
        # A file seed expands into its module and symbols at the same logical distance.
        if current.startswith("file:"):
            for e in out.get(current, []):
                if e["relation"] != "CONTAINS": continue
                module = e["target"]
                for de in out.get(module, []):
                    if de["relation"] == "DEFINES" and best_depth.get(de["target"], 999) > depth:
                        best_depth[de["target"]] = depth; q.appendleft((de["target"], depth, path_score))
    rows = list(affected.values())
    for row in rows:
        row["score"] = round(row["score"], 4); row["confidence"] = _confidence(row["provenance"]); row["evidence"] = row["evidence"][:8]
    rows.sort(key=lambda x: (-x["score"], x["distance"], x["path"]))
    return {"affected": rows, "seed_nodes": sorted(starts)}


def dependents_for_files(graph: dict, files: list[str], max_depth: int = 2, max_nodes: int = 300) -> dict:
    return dependents_for_nodes(graph, [f"file:{p}" for p in files], changed_files=files, max_depth=max_depth, max_nodes=max_nodes)


def tests_for(graph: dict, target_id: str) -> list[dict]:
    nodes, _, inc = indices(graph); rows = []
    for e in inc.get(target_id, []):
        if e["relation"] != "TESTS": continue
        n = nodes.get(e["source"], {})
        rows.append({"path": n.get("path"), "node_id": e["source"], "provenance": e.get("provenance"), "line": e.get("line"), "evidence_kind": e.get("evidence_kind"), "cross_language": bool(e.get("cross_language"))})
    rows.sort(key=lambda x: ({"DIRECT": 0, "RESOLVED": 1, "HEURISTIC": 2}.get(x.get("provenance"), 3), x.get("path") or ""))
    return rows


def resolve_one(graph: dict, value: str) -> str | None:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    if value in nodes: return value
    found = find_nodes(graph, value, 2); return found[0]["id"] if found else None


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("find-symbol"); p.add_argument("query"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("neighbors"); p.add_argument("node"); p.add_argument("--direction", choices=["in", "out", "both"], default="both"); p.add_argument("--relation", action="append")
    for name in ["callers", "callees", "dependents", "dependencies", "tests-for"]: p = sub.add_parser(name); p.add_argument("node")
    p = sub.add_parser("path"); p.add_argument("start"); p.add_argument("goal"); p.add_argument("--max-depth", type=int, default=6)
    p = sub.add_parser("impact"); p.add_argument("files", nargs="+"); p.add_argument("--max-depth", type=int, default=2)
    ns = ap.parse_args(); graph = load_graph(Path(ns.root).resolve())
    if ns.cmd == "find-symbol": result = find_nodes(graph, ns.query, ns.limit)
    elif ns.cmd == "neighbors":
        node = resolve_one(graph, ns.node); result = neighbors(graph, node, set(ns.relation or []), ns.direction) if node else []
    elif ns.cmd in {"callers", "callees", "dependents", "dependencies", "tests-for"}:
        node = resolve_one(graph, ns.node)
        if not node: result = []
        elif ns.cmd == "callers": result = neighbors(graph, node, {"CALLS"}, "in")
        elif ns.cmd == "callees": result = neighbors(graph, node, {"CALLS"}, "out")
        elif ns.cmd == "dependents": result = neighbors(graph, node, {"DEPENDS_ON", "IMPORTS", "IMPORTS_SYMBOL", "REFERENCES", "CALLS"}, "in")
        elif ns.cmd == "dependencies": result = neighbors(graph, node, {"DEPENDS_ON", "IMPORTS", "IMPORTS_SYMBOL", "REFERENCES", "CALLS"}, "out")
        else: result = tests_for(graph, node)
    elif ns.cmd == "path":
        a, b = resolve_one(graph, ns.start), resolve_one(graph, ns.goal); result = shortest_path(graph, a, b, ns.max_depth) if a and b else []
    else: result = dependents_for_files(graph, ns.files, ns.max_depth)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
