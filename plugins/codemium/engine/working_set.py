#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from common import state_root, read_json, read_jsonl, write_json

def terms(q:str)->set[str]: return {x for x in re.findall(r'[a-zA-Z0-9_./-]{3,}',q.lower()) if x not in {'this','that','with','from','untuk','yang','dan','the'}}
def score_file(f:dict,ts:set[str])->float:
    path=f['path'].lower(); syms=' '.join(f.get('symbols',[])).lower(); imps=' '.join(f.get('imports',[])).lower(); score=0.0
    for t in ts:
        if t in path: score+=8
        if t in syms: score+=6
        if t in imps: score+=2
    if f.get('is_test'): score*=0.72
    return score

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--query',required=True); ap.add_argument('--top',type=int,default=12); ap.add_argument('--no-write',action='store_true')
    ns=ap.parse_args(); root=Path(ns.root).resolve(); s=state_root(root); graph=read_json(s/'repository/graph.json',{})
    if not graph: raise SystemExit('repository graph missing; run repo_graph.py build')
    ts=terms(ns.query); ranked=[(score_file(f,ts),f) for f in graph.get('files',[])]; ranked=[x for x in ranked if x[0]>0]; ranked.sort(key=lambda x:(-x[0],x[1]['path']))
    files=[{'path':f['path'],'score':round(sc,2),'symbols':f.get('symbols',[])[:20],'is_test':f.get('is_test',False)} for sc,f in ranked[:ns.top]]
    knowledge=[]
    for kind,fn in [('decision','decisions.jsonl'),('constraint','constraints.jsonl'),('interface','interfaces.jsonl'),('pattern','patterns.jsonl'),('bug','bugs.jsonl')]:
        for e in read_jsonl(s/'registry'/fn):
            blob=json.dumps(e,ensure_ascii=False).lower(); hits=sum(1 for t in ts if t in blob)
            if hits: knowledge.append({'kind':kind,'id':e.get('id'),'score':hits,'text':e.get('text')})
    knowledge.sort(key=lambda x:-x['score'])
    out={'query':ns.query,'files':files,'knowledge':knowledge[:12]}
    if not ns.no_write:
        task=read_json(s/'tasks/active.json',{})
        if task:
            task['working_set']=[x['path'] for x in files]; task['relevant_knowledge']=[x['id'] for x in knowledge[:12]]; write_json(s/'tasks/active.json',task)
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
