#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import state_root, read_json, git

def changed_from_git(root:Path)->list[str]:
    names=set()
    for args in [('diff','--name-only'),('diff','--cached','--name-only')]:
        out=git(root,*args) or ''; names.update(x for x in out.splitlines() if x)
    return sorted(names)

def risk_for(paths:list[str])->str:
    text=' '.join(paths).lower()
    high=['auth','permission','security','payment','billing','migration','infra','deploy','secret','token']
    med=['api','worker','queue','webhook','database','repository','service']
    if any(x in text for x in high):return 'high'
    if any(x in text for x in med) or len(paths)>3:return 'medium'
    return 'low'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--git-diff',action='store_true'); ap.add_argument('--files',nargs='*')
    ns=ap.parse_args(); root=Path(ns.root).resolve(); s=state_root(root); graph=read_json(s/'repository/graph.json',{}); tests=read_json(s/'repository/tests.json',{}).get('mapping',{})
    paths=changed_from_git(root) if ns.git_diff or not ns.files else ns.files
    changed=set(paths); affected=set(); reltests=set()
    for p in paths:
        reltests.update(tests.get(p,[])); base=Path(p).stem.lower(); name=Path(p).name.lower()
        for f in graph.get('files',[]):
            if f['path'] in changed:continue
            blob=' '.join(f.get('imports',[])).lower()
            if base and (base in blob or name in blob): affected.add(f['path'])
    risk=risk_for(paths+list(affected))
    out={'changed_files':paths,'likely_dependents':sorted(affected)[:50],'related_tests':sorted(reltests)[:50],'blast_radius':risk,'recommended_verification':{'low':'V2 targeted','medium':'V3 targeted + subsystem','high':'V4/V5 as applicable'}[risk]}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
