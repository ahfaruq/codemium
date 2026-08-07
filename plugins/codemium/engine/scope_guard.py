#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, fnmatch
from pathlib import Path
from common import state_root, read_json, git

def changed(root:Path)->list[str]:
    out=set()
    for args in [('diff','--name-only'),('diff','--cached','--name-only')]:
        s=git(root,*args) or ''; out.update(x for x in s.splitlines() if x)
    return sorted(out)
def allowed(path:str,patterns:list[str])->bool:
    return any(path==p or fnmatch.fnmatch(path,p) or path.startswith(p.rstrip('/')+'/') for p in patterns)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--allow',action='append',default=[]); ap.add_argument('--strict',action='store_true')
    ns=ap.parse_args(); root=Path(ns.root).resolve(); task=read_json(state_root(root)/'tasks/active.json',{}); patterns=list(ns.allow) or list(task.get('working_set',[])); paths=changed(root)
    if not patterns:
        out={'status':'unknown','changed_files':paths,'reason':'no working set/--allow supplied'}; print(json.dumps(out,indent=2)); raise SystemExit(2 if ns.strict else 0)
    violations=[p for p in paths if not allowed(p,patterns)]
    out={'status':'pass' if not violations else 'violation','allowed':patterns,'changed_files':paths,'outside_scope':violations}; print(json.dumps(out,indent=2));
    if violations and ns.strict: raise SystemExit(3)
if __name__=='__main__': main()
