#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import state_root, read_json, read_jsonl, git

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ns=ap.parse_args(); root=Path(ns.root).resolve(); s=state_root(root)
    graph=read_json(s/'repository/graph.json',{}); head=git(root,'rev-parse','HEAD'); graph_fresh=bool(graph) and (not head or graph.get('git_head')==head)
    bugs=[b for b in read_jsonl(s/'registry/bugs.jsonl') if b.get('status','ACTIVE')=='ACTIVE']; active=read_json(s/'tasks/active.json',None)
    out={'initialized':s.exists(),'repository_graph':{'present':bool(graph),'fresh_to_head':graph_fresh,'files':graph.get('file_count',0)},'active_task':active.get('id') if active else None,'unresolved_known_bugs':len(bugs),'registries':{k:len(read_jsonl(s/'registry'/f'{k}.jsonl')) for k in ['decisions','constraints','interfaces','patterns','bugs']}}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
