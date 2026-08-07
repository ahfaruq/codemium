#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import state_root, now_iso, write_json, read_json, append_jsonl, read_jsonl, atomic_write

REGISTRY={'decision':('decisions.jsonl','D'),'constraint':('constraints.jsonl','C'),'interface':('interfaces.jsonl','I'),'pattern':('patterns.jsonl','P'),'bug':('bugs.jsonl','B')}

def init(root: Path) -> None:
    s=state_root(root)
    for d in ['architecture','registry','repository','tasks/completed','runtime/snapshots']:(s/d).mkdir(parents=True,exist_ok=True)
    project=s/'PROJECT.md'
    if not project.exists(): atomic_write(project,'# Project\n\nDescribe stable product purpose, stack, entry points, and non-negotiable engineering facts here.\n')
    arch=s/'architecture/system.json'
    if not arch.exists(): write_json(arch,{'schema_version':1,'updated_at':now_iso(),'boundaries':[],'components':[]})
    model=s/'model-profile.json'
    if not model.exists(): write_json(model,{'schema_version':1,'roles':{'primary':{'capability':'frontier_reasoning','preferred_model':None},'reviewer':{'capability':'frontier_review','preferred_model':None},'worker':{'capability':'strong_coding','preferred_model':None}},'note':'Model names are preferences, not proof of benchmarked capability.'})
    for fn,_ in REGISTRY.values(): (s/'registry'/fn).touch(exist_ok=True)
    gi=s/'.gitignore'
    if not gi.exists(): atomic_write(gi,'runtime/\nrepository/\ntasks/completed/\n')
    print(json.dumps({'status':'initialized','state_dir':str(s)},indent=2))

def next_id(path: Path,prefix: str)->str:
    n=0
    for x in read_jsonl(path):
        v=str(x.get('id',''))
        if v.startswith(prefix):
            try:n=max(n,int(v[len(prefix):]))
            except ValueError:pass
    return f'{prefix}{n+1:04d}'

def add(root:Path,kind:str,text:str,extra:dict)->dict:
    fn,prefix=REGISTRY[kind]; path=state_root(root)/'registry'/fn
    entry={'id':next_id(path,prefix),'kind':kind,'text':text,'status':'ACTIVE','created_at':now_iso(),**{k:v for k,v in extra.items() if v not in (None,'')}}
    append_jsonl(path,entry); return entry

def status(root:Path)->dict:
    s=state_root(root)
    regs={k:len(read_jsonl(s/'registry'/fn)) for k,(fn,_) in REGISTRY.items()}
    active=read_json(s/'tasks/active.json',None)
    return {'initialized':s.exists(),'root':str(root.resolve()),'registries':regs,'active_task':active}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init'); sub.add_parser('status')
    for kind in REGISTRY:
        p=sub.add_parser('add-'+kind); p.add_argument('--text',required=True); p.add_argument('--why'); p.add_argument('--source'); p.add_argument('--risk')
    a=sub.add_parser('start-task'); a.add_argument('--contract',required=True,help='JSON string or path')
    sub.add_parser('complete-task')
    ns=ap.parse_args(); root=Path(ns.root)
    if ns.cmd=='init': return init(root)
    if not state_root(root).exists(): init(root)
    if ns.cmd=='status': print(json.dumps(status(root),indent=2)); return
    if ns.cmd.startswith('add-'):
        kind=ns.cmd[4:]; print(json.dumps(add(root,kind,ns.text,{'why':ns.why,'source':ns.source,'risk':ns.risk}),indent=2)); return
    if ns.cmd=='start-task':
        raw=Path(ns.contract).read_text() if Path(ns.contract).exists() else ns.contract
        contract=json.loads(raw); contract.setdefault('started_at',now_iso()); write_json(state_root(root)/'tasks/active.json',contract); print(json.dumps(contract,indent=2)); return
    if ns.cmd=='complete-task':
        p=state_root(root)/'tasks/active.json'; task=read_json(p,None)
        if not task: print(json.dumps({'status':'no-active-task'})); return
        task['completed_at']=now_iso(); tid=task.get('id','task'); write_json(state_root(root)/'tasks/completed'/f'{tid}.json',task); p.unlink(missing_ok=True); print(json.dumps({'status':'completed','id':tid},indent=2))
if __name__=='__main__': main()
