#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import state_root, read_json, write_json, now_iso

def related(src:dict,test:dict)->int:
    sp=Path(src['path']); tp=Path(test['path']); score=0
    stem=sp.stem.replace('.service','').replace('.controller','').replace('.repository','')
    if stem and stem.lower() in tp.name.lower(): score+=8
    if sp.parent.name and sp.parent.name.lower() in test['path'].lower(): score+=2
    srcparts={sp.stem.lower(),sp.name.lower(),sp.parent.name.lower()}
    imports=' '.join(test.get('imports',[])).lower()
    score+=sum(3 for p in srcparts if p and p in imports)
    return score

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True); b=sub.add_parser('build'); b.add_argument('--root',default='.')
    ns=ap.parse_args(); root=Path(ns.root).resolve(); s=state_root(root); graph=read_json(s/'repository/graph.json',{})
    if not graph: raise SystemExit('repository graph missing')
    sources=[f for f in graph['files'] if not f.get('is_test')]; tests=[f for f in graph['files'] if f.get('is_test')]; mapping={}
    for src in sources:
        rs=[(related(src,t),t['path']) for t in tests]; rs=sorted([x for x in rs if x[0]>0],key=lambda x:(-x[0],x[1]))
        if rs:mapping[src['path']]=[p for _,p in rs[:12]]
    out={'schema_version':1,'generated_at':now_iso(),'source_count':len(sources),'test_count':len(tests),'mapping':mapping}; write_json(s/'repository/tests.json',out); print(json.dumps({'mapped_sources':len(mapping),'tests':len(tests)},indent=2))
if __name__=='__main__': main()
