#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from common import git, read_json, read_jsonl, sha256_bytes, state_root
from project_brain import freshness_summary


def manifest_worktree_fresh(root: Path, manifest: dict) -> tuple[bool, list[str]]:
    files = manifest.get("files", {}) if isinstance(manifest.get("files"), dict) else {}
    changed = []
    for rel, meta in files.items():
        p = root / rel
        try:
            current = sha256_bytes(p.read_bytes())
        except OSError:
            changed.append(rel)
            continue
        if current != meta.get("sha256"):
            changed.append(rel)
    return not changed, changed[:50]


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ns = ap.parse_args()
    root = Path(ns.root).resolve(); s = state_root(root)
    graph = read_json(s / "repository/graph.json", {}); manifest = read_json(s / "repository/manifest.json", {})
    head = git(root, "rev-parse", "HEAD")
    graph_fresh_to_head = bool(graph) and (not head or graph.get("git_head") == head)
    worktree_fresh, changed_manifest_files = manifest_worktree_fresh(root, manifest) if manifest else (False, [])
    bugs = [b for b in read_jsonl(s / "registry/bugs.jsonl") if b.get("status", "ACTIVE") == "ACTIVE"]
    active = read_json(s / "tasks/active.json", None); freshness = freshness_summary(root) if s.exists() else {"counts": {}}
    provenance = Counter(e.get("provenance", "UNKNOWN") for e in graph.get("edges", [])); parsers = Counter(f.get("parser", "unknown") for f in graph.get("files", [])); capabilities = Counter()
    for f in graph.get("files", []):
        for cap in f.get("capabilities", []): capabilities[cap] += 1
    out = {
        "initialized": s.exists(),
        "repository_graph": {
            "present": bool(graph), "schema_version": graph.get("schema_version"), "fresh_to_head": graph_fresh_to_head,
            "fresh_to_worktree": bool(graph) and worktree_fresh, "changed_since_graph": changed_manifest_files,
            "manifest_present": bool(manifest), "files": graph.get("file_count", 0), "nodes": graph.get("node_count", 0),
            "edges": graph.get("edge_count", 0), "unresolved_relationships": graph.get("unresolved_relationships", 0),
            "parsers": dict(sorted(parsers.items())), "capability_coverage": dict(sorted(capabilities.items())),
            "edge_provenance": dict(sorted(provenance.items())), "incremental": graph.get("incremental", {}),
        },
        "project_brain_freshness": freshness.get("counts", {}), "active_task": active.get("id") if active else None,
        "unresolved_known_bugs": len(bugs),
        "registries": {k: len(read_jsonl(s / "registry" / f"{k}.jsonl")) for k in ["decisions", "constraints", "interfaces", "patterns", "bugs"]},
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
