#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path

from common import git, read_json, state_root


def changed(root: Path) -> list[str]:
    out = set()
    for args in [("diff", "--name-only"), ("diff", "--cached", "--name-only")]:
        s = git(root, *args) or ""; out.update(x for x in s.splitlines() if x)
    return sorted(out)


def allowed(path: str, patterns: list[str]) -> bool:
    return any(path == p or fnmatch.fnmatch(path, p) or path.startswith(p.rstrip("/") + "/") for p in patterns)


def classify_change(path: str, task: dict, graph: dict) -> dict:
    graph_file = next((f for f in graph.get("files", []) if f.get("path") == path), {})
    if graph_file.get("is_test"):
        return {"class": "TEST", "reason": "structurally or task-selected verification file"}
    evidence = task.get("working_set_evidence", {}).get(path, [])
    graph_reasons = [x for x in evidence if x.get("kind") == "graph"]
    if graph_reasons:
        min_distance = min(int(x.get("distance", 99)) for x in graph_reasons)
        if min_distance == 0:
            return {"class": "DIRECT", "reason": "task seed matched structural entity"}
        best = min(graph_reasons, key=lambda x: int(x.get("distance", 99)))
        return {"class": "DEPENDENCY", "reason": f"structural {best.get('relation') or 'relationship'} at distance {best.get('distance')}", "provenance": best.get("provenance")}
    return {"class": "DIRECT", "reason": "included in bounded task working set"}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--allow", action="append", default=[]); ap.add_argument("--strict", action="store_true")
    ns = ap.parse_args(); root = Path(ns.root).resolve(); s = state_root(root)
    task = read_json(s / "tasks/active.json", {}); graph = read_json(s / "repository/graph.json", {})
    patterns = list(ns.allow) or list(task.get("working_set", [])); paths = changed(root)
    if not patterns:
        out = {"status": "unknown", "changed_files": paths, "reason": "no working set/--allow supplied"}; print(json.dumps(out, indent=2)); raise SystemExit(2 if ns.strict else 0)
    violations = [p for p in paths if not allowed(p, patterns)]
    explanations = {p: ({"class": "OUTSIDE_SCOPE", "reason": "not attributable to current working set"} if p in violations else classify_change(p, task, graph)) for p in paths}
    out = {"status": "pass" if not violations else "violation", "allowed": patterns, "changed_files": paths, "change_explanations": explanations, "outside_scope": violations}
    print(json.dumps(out, indent=2))
    if violations and ns.strict: raise SystemExit(3)


if __name__ == "__main__":
    main()
