#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import state_root, read_jsonl, append_jsonl, repo_state, now_iso

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('check'); c.add_argument('--kind',required=True); c.add_argument('--key',required=True)
    r=sub.add_parser('record'); r.add_argument('--kind',required=True); r.add_argument('--key',required=True); r.add_argument('--result-ref',required=True)
    ns=ap.parse_args(); root=Path(ns.root).resolve(); p=state_root(root)/'runtime/cache.jsonl'; state=repo_state(root)
    rows=read_jsonl(p)
    if ns.cmd=='check':
        hit=next((x for x in reversed(rows) if x.get('kind')==ns.kind and x.get('key')==ns.key and x.get('state')==state),None); print(json.dumps({'hit':bool(hit),'state':state,'record':hit},indent=2)); return
    rec={'kind':ns.kind,'key':ns.key,'state':state,'result_ref':ns.result_ref,'created_at':now_iso()}; append_jsonl(p,rec); print(json.dumps(rec,indent=2))
if __name__=='__main__': main()
