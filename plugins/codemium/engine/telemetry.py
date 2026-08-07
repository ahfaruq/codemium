#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from common import state_root, read_jsonl

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ns=ap.parse_args(); s=state_root(Path(ns.root).resolve())
    bytes_total=0; files=0
    if s.exists():
        for p in s.rglob('*'):
            if p.is_file():
                try: bytes_total+=p.stat().st_size; files+=1
                except OSError:pass
    cache=read_jsonl(s/'runtime/cache.jsonl'); pairs=[(x.get('kind'),x.get('key'),x.get('state')) for x in cache]; dup=len(pairs)-len(set(pairs))
    out={'state_files':files,'state_bytes':bytes_total,'approx_text_tokens_if_all_loaded':math.ceil(bytes_total/4),'cache_records':len(cache),'duplicate_cache_records_same_state':dup,'note':'Token estimate is a deterministic text-size proxy, not host/model token telemetry. Codemium should not load all state at once.'}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
