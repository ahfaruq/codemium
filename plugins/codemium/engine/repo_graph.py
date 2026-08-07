#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from common import IGNORE_DIRS, state_root, now_iso, sha256_bytes, git, write_json

EXT_LANG={'.py':'python','.js':'javascript','.jsx':'javascript','.ts':'typescript','.tsx':'typescript','.go':'go','.rs':'rust','.java':'java','.kt':'kotlin','.rb':'ruby','.php':'php','.cs':'csharp','.c':'c','.h':'c','.cpp':'cpp','.hpp':'cpp','.vue':'vue','.svelte':'svelte','.sql':'sql'}
SYMBOL_PATTERNS=[
 re.compile(r'^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)',re.M),
 re.compile(r'^\s*class\s+([A-Za-z_]\w*)',re.M),
 re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)',re.M),
 re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(',re.M),
 re.compile(r'^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)',re.M),
 re.compile(r'^\s*(?:pub\s+)?(?:fn|struct|enum|trait)\s+([A-Za-z_]\w*)',re.M),
 re.compile(r'^\s*(?:public\s+|private\s+|protected\s+)?(?:class|interface|record)\s+([A-Za-z_]\w*)',re.M),
]
IMPORT_PATTERNS=[re.compile(r'(?:from|import)\s+["\']([^"\']+)["\']'),re.compile(r'require\(["\']([^"\']+)["\']\)'),re.compile(r'^\s*from\s+([\w.]+)\s+import',re.M),re.compile(r'^\s*import\s+([\w.]+)',re.M)]

def is_test(path:str)->bool:
    s=path.lower(); name=Path(s).name
    return any(x in s for x in ['/test/','/tests/','/__tests__/']) or name.startswith('test_') or any(x in name for x in ['.test.','.spec.','_test.'])

def scan(root:Path)->dict:
    files=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if any(part in IGNORE_DIRS for part in p.relative_to(root).parts): continue
        if p.suffix.lower() not in EXT_LANG: continue
        try:
            data=p.read_bytes()
            if len(data)>2_000_000 or b'\x00' in data: continue
            text=data.decode('utf-8',errors='ignore')
        except OSError: continue
        symbols=[]
        for pat in SYMBOL_PATTERNS:
            symbols.extend(m.group(1) for m in pat.finditer(text))
        imports=[]
        for pat in IMPORT_PATTERNS:
            imports.extend(m.group(1) for m in pat.finditer(text))
        files.append({'path':rel,'language':EXT_LANG[p.suffix.lower()],'bytes':len(data),'sha256':sha256_bytes(data)[:20],'symbols':sorted(set(symbols))[:250],'imports':sorted(set(imports))[:250],'is_test':is_test('/'+rel)})
    head=git(root,'rev-parse','HEAD')
    return {'schema_version':1,'generated_at':now_iso(),'git_head':head,'file_count':len(files),'files':sorted(files,key=lambda x:x['path'])}

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True); b=sub.add_parser('build'); b.add_argument('--root',default='.'); b.add_argument('--output')
    ns=ap.parse_args(); root=Path(ns.root).resolve(); graph=scan(root); out=Path(ns.output) if ns.output else state_root(root)/'repository/graph.json'; write_json(out,graph); print(json.dumps({'output':str(out),'file_count':graph['file_count'],'git_head':graph['git_head']},indent=2))
if __name__=='__main__': main()
