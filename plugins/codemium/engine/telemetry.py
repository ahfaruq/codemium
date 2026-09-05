#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from common import read_jsonl, state_root
from execution_guard import load_state as load_execution_state
from execution_guard import state_path as execution_state_path
from execution_guard import status_report as execution_status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    s = state_root(root)

    bytes_total = 0
    files = 0
    if s.exists():
        for p in s.rglob("*"):
            if p.is_file():
                try:
                    bytes_total += p.stat().st_size
                    files += 1
                except OSError:
                    pass

    cache = read_jsonl(s / "runtime/cache.jsonl")
    pairs = [(x.get("kind"), x.get("key"), x.get("state")) for x in cache]
    dup = len(pairs) - len(set(pairs))

    execution = None
    if execution_state_path(root).exists():
        execution = execution_status(load_execution_state(root))

    out = {
        "state_files": files,
        "state_bytes": bytes_total,
        "approx_text_tokens_if_all_loaded": math.ceil(bytes_total / 4),
        "cache_records": len(cache),
        "duplicate_cache_records_same_state": dup,
        "execution_intelligence": execution,
        "note": "Token estimate is a deterministic text-size proxy, not host/model token telemetry. Execution Intelligence reports action usefulness/evidence-delta state when present. Codemium should not load all state at once.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
