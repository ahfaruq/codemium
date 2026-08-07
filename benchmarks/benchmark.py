#!/usr/bin/env python3
"""Compare externally captured coding-run metrics without fabricating host token usage."""
import argparse,json,statistics
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('file'); ns=ap.parse_args(); rows=json.loads(Path(ns.file).read_text())
    groups={}
    for r in rows: groups.setdefault(r['system'],[]).append(r)
    out={}
    for name,rs in groups.items():
        d={}
        for key in ['input_tokens','reasoning_tokens','output_tokens','tool_calls','unique_files_read','duplicate_reads','loc_changed','unrelated_changed_lines','seconds']:
            vals=[x[key] for x in rs if isinstance(x.get(key),(int,float))]
            if vals:d[key]=round(statistics.mean(vals),2)
        q=[x.get('quality_pass') for x in rs if isinstance(x.get('quality_pass'),bool)]
        if q:d['quality_pass_rate']=round(sum(q)/len(q),3)
        out[name]=d
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
