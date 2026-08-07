#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = '.codemium'
IGNORE_DIRS = {'.git','.hg','.svn','node_modules','.next','dist','build','coverage','.venv','venv','vendor','target','__pycache__','.codemium'}

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def state_root(root: str|Path) -> Path:
    return Path(root).resolve()/STATE_DIR

def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def read_json(path: Path, default: Any) -> Any:
    try: return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError: return default

def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n')

def append_jsonl(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(data,ensure_ascii=False,sort_keys=True)+'\n')

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists(): return []
    out=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try: out.append(json.loads(line))
            except json.JSONDecodeError: continue
    return out

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git(root: Path, *args: str) -> str|None:
    try:
        p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=15)
        return p.stdout.strip() if p.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired): return None

def repo_state(root: Path) -> str:
    head=git(root,'rev-parse','HEAD') or 'nogit'
    diff=git(root,'diff','--binary') or ''
    staged=git(root,'diff','--cached','--binary') or ''
    untracked=git(root,'ls-files','--others','--exclude-standard') or ''
    payload='\n'.join([head,diff,staged,untracked]).encode()
    return sha256_bytes(payload)[:20]
