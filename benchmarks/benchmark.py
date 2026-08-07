#!/usr/bin/env python3
"""Summarize externally captured coding-agent runs without inventing token/cost data."""
from __future__ import annotations
import argparse, json, statistics
from pathlib import Path

KEYS = [
    'input_tokens','reasoning_tokens','output_tokens','total_tokens','cost_usd',
    'tool_calls','unique_files_read','duplicate_reads','loc_changed',
    'unrelated_changed_lines','seconds'
]

def load(path: Path):
    raw=json.loads(path.read_text(encoding='utf-8'))
    if isinstance(raw,list):
        return {},raw
    if isinstance(raw,dict) and isinstance(raw.get('runs'),list):
        return raw.get('meta',{}),raw['runs']
    raise SystemExit('expected run list or {meta,runs}')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('file')
    ns=ap.parse_args()
    meta,rows=load(Path(ns.file))
    groups={}
    for r in rows:
        groups.setdefault(r['system'],[]).append(r)
    out={'meta':meta,'systems':{}}
    for name,rs in groups.items():
        d={'n':len(rs)}
        for key in KEYS:
            vals=[]
            for x in rs:
                v=x.get(key)
                if key=='total_tokens' and not isinstance(v,(int,float)):
                    pieces=[x.get(k) for k in ('input_tokens','reasoning_tokens','output_tokens')]
                    if all(isinstance(p,(int,float)) for p in pieces): v=sum(pieces)
                if isinstance(v,(int,float)): vals.append(v)
            if vals:d[key]=round(statistics.mean(vals),4)
        for key in ('quality_pass','safety_pass'):
            vals=[x.get(key) for x in rs if isinstance(x.get(key),bool)]
            if vals:d[key+'_rate']=round(sum(vals)/len(vals),4)
        out['systems'][name]=d
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
