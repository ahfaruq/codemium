#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import state_root, now_iso, write_json, read_json, append_jsonl, read_jsonl, atomic_write

REGISTRY = {
    'decision': ('decisions.jsonl', 'D'),
    'constraint': ('constraints.jsonl', 'C'),
    'interface': ('interfaces.jsonl', 'I'),
    'pattern': ('patterns.jsonl', 'P'),
    'bug': ('bugs.jsonl', 'B'),
}

DEFAULT_REASONING = {
    'FAST': {'preferred_effort': 'low', 'minimum_effort': 'low'},
    'NORMAL': {'preferred_effort': 'medium', 'minimum_effort': 'low'},
    'DEEP': {'preferred_effort': 'high', 'minimum_effort': 'medium'},
    'CRITICAL': {'preferred_effort': 'xhigh', 'minimum_effort': 'high'},
}


def default_model_profile() -> dict:
    return {
        'schema_version': 2,
        'roles': {
            'primary': {'capability': 'frontier_reasoning', 'preferred_model': None},
            'reviewer': {'capability': 'frontier_review', 'preferred_model': None},
            'worker': {'capability': 'strong_coding', 'preferred_model': None},
        },
        'reasoning_profiles': DEFAULT_REASONING,
        'host_control': {
            'mode': 'advisory_unless_runtime_confirms_per_task_control',
            'mutate_global_config': False,
            'claim_change_only_after_runtime_confirmation': True,
        },
        'note': 'Model names and reasoning profiles are preferences, not proof of benchmarked capability.',
    }


def ensure_model_profile(path: Path) -> None:
    current = read_json(path, {}) if path.exists() else {}
    merged = default_model_profile()
    if isinstance(current, dict):
        if isinstance(current.get('roles'), dict):
            merged['roles'].update(current['roles'])
        if isinstance(current.get('reasoning_profiles'), dict):
            merged['reasoning_profiles'].update(current['reasoning_profiles'])
        if isinstance(current.get('host_control'), dict):
            merged['host_control'].update(current['host_control'])
    write_json(path, merged)


def init(root: Path) -> None:
    s = state_root(root)
    for d in ['architecture', 'registry', 'repository', 'tasks/completed', 'runtime/snapshots']:
        (s / d).mkdir(parents=True, exist_ok=True)
    project = s / 'PROJECT.md'
    if not project.exists():
        atomic_write(project, '# Project\n\nDescribe stable product purpose, stack, entry points, and non-negotiable engineering facts here.\n')
    arch = s / 'architecture/system.json'
    if not arch.exists():
        write_json(arch, {'schema_version': 1, 'updated_at': now_iso(), 'boundaries': [], 'components': []})
    ensure_model_profile(s / 'model-profile.json')
    for fn, _ in REGISTRY.values():
        (s / 'registry' / fn).touch(exist_ok=True)
    gi = s / '.gitignore'
    if not gi.exists():
        atomic_write(gi, 'runtime/\nrepository/\ntasks/completed/\n')
    print(json.dumps({'status': 'initialized', 'state_dir': str(s)}, indent=2))


def next_id(path: Path, prefix: str) -> str:
    n = 0
    for x in read_jsonl(path):
        v = str(x.get('id', ''))
        if v.startswith(prefix):
            try:
                n = max(n, int(v[len(prefix):]))
            except ValueError:
                pass
    return f'{prefix}{n + 1:04d}'


def add(root: Path, kind: str, text: str, extra: dict) -> dict:
    fn, prefix = REGISTRY[kind]
    path = state_root(root) / 'registry' / fn
    entry = {
        'id': next_id(path, prefix),
        'kind': kind,
        'text': text,
        'status': 'ACTIVE',
        'created_at': now_iso(),
        **{k: v for k, v in extra.items() if v not in (None, '')},
    }
    append_jsonl(path, entry)
    return entry


def status(root: Path) -> dict:
    s = state_root(root)
    regs = {k: len(read_jsonl(s / 'registry' / fn)) for k, (fn, _) in REGISTRY.items()}
    active = read_json(s / 'tasks/active.json', None)
    return {
        'initialized': s.exists(),
        'root': str(root.resolve()),
        'registries': regs,
        'active_task': active,
        'model_profile': read_json(s / 'model-profile.json', None),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init')
    sub.add_parser('status')
    for kind in REGISTRY:
        p = sub.add_parser('add-' + kind)
        p.add_argument('--text', required=True)
        p.add_argument('--why')
        p.add_argument('--source')
        p.add_argument('--risk')
    a = sub.add_parser('start-task')
    a.add_argument('--contract', required=True, help='JSON string or path')
    sub.add_parser('complete-task')
    ns = ap.parse_args()
    root = Path(ns.root)
    if ns.cmd == 'init':
        return init(root)
    if not state_root(root).exists():
        init(root)
    if ns.cmd == 'status':
        print(json.dumps(status(root), indent=2))
        return
    if ns.cmd.startswith('add-'):
        kind = ns.cmd[4:]
        print(json.dumps(add(root, kind, ns.text, {'why': ns.why, 'source': ns.source, 'risk': ns.risk}), indent=2))
        return
    if ns.cmd == 'start-task':
        raw = Path(ns.contract).read_text() if Path(ns.contract).exists() else ns.contract
        contract = json.loads(raw)
        contract.setdefault('started_at', now_iso())
        write_json(state_root(root) / 'tasks/active.json', contract)
        print(json.dumps(contract, indent=2))
        return
    if ns.cmd == 'complete-task':
        p = state_root(root) / 'tasks/active.json'
        task = read_json(p, None)
        if not task:
            print(json.dumps({'status': 'no-active-task'}))
            return
        task['completed_at'] = now_iso()
        tid = task.get('id', 'task')
        write_json(state_root(root) / 'tasks/completed' / f'{tid}.json', task)
        p.unlink(missing_ok=True)
        print(json.dumps({'status': 'completed', 'id': tid}, indent=2))


if __name__ == '__main__':
    main()
