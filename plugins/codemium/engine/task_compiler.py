#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from common import state_root, now_iso, write_json

def classify(text:str)->str:
    t=text.lower()
    if any(x in t for x in ['security','vulnerab','authz','authorization','permission','secret','injection']): return 'SECURITY'
    if any(x in t for x in ['migration','migrate','schema change','database upgrade']): return 'MIGRATION'
    if any(x in t for x in ['review','audit pr','code review']): return 'REVIEW'
    if any(x in t for x in ['refactor','cleanup architecture','simplify code']): return 'REFACTOR'
    if any(x in t for x in ['test','coverage','spec case']) and not any(x in t for x in ['bug','fix','error','fail']): return 'TEST'
    if any(x in t for x in ['bug','fix','error','fail','broken','duplicate','stuck','wrong','tidak','kenapa']): return 'FIX'
    return 'BUILD'

def risk(text:str,mode:str)->str:
    t=text.lower()
    if mode in {'SECURITY','MIGRATION'} or any(x in t for x in ['payment','billing','delete','production','auth','permission','concurrency','race','deployment','infrastructure']): return 'high'
    if mode in {'FIX','REFACTOR','REVIEW'} or any(x in t for x in ['database','api','worker','queue','webhook']): return 'medium'
    return 'low'

def compile_task(text:str)->dict:
    mode=classify(text); r=risk(text,mode)
    policy={'FIX':'root-cause fix; surgical scope; regression evidence','TEST':'behavior/risk coverage; do not minimize justified cases','REFACTOR':'behavior preservation; demonstrated complexity only','REVIEW':'read-only unless explicitly asked to edit','MIGRATION':'compatibility, data integrity, rollback','SECURITY':'trust-boundary correctness outranks efficiency','BUILD':'reuse-first; minimum justified architecture'}[mode]
    return {'id':'T'+now_iso().replace('-','').replace(':','').replace('T','')[:14],'type':mode,'request':text,'objective':text.strip(),'expected_behavior':'derive from request/evidence before editing','likely_domain':[],'acceptance':['requested behavior is satisfied','relevant verification passes','no unrelated diff','no material unexplained uncertainty'],'risk':r,'change_policy':policy,'created_at':now_iso(),'working_set':[]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--request',required=True); ap.add_argument('--no-write',action='store_true')
    ns=ap.parse_args(); task=compile_task(ns.request); root=Path(ns.root).resolve()
    if not ns.no_write:
        p=state_root(root)/'tasks/active.json'; p.parent.mkdir(parents=True,exist_ok=True); write_json(p,task)
    print(json.dumps(task,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
