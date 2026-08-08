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

GENERIC_REASONING = {
    'FAST': {'preferred_class': 'economy', 'minimum_class': 'economy'},
    'NORMAL': {'preferred_class': 'balanced', 'minimum_class': 'economy'},
    'DEEP': {'preferred_class': 'strong', 'minimum_class': 'balanced'},
    'CRITICAL': {'preferred_class': 'frontier', 'minimum_class': 'strong'},
}

CODEX_EFFORT_BY_DEPTH = {
    'FAST': {'preferred_effort': 'low', 'minimum_effort': 'low'},
    'NORMAL': {'preferred_effort': 'medium', 'minimum_effort': 'low'},
    'DEEP': {'preferred_effort': 'high', 'minimum_effort': 'medium'},
    'CRITICAL': {'preferred_effort': 'xhigh', 'minimum_effort': 'high'},
}

HOST_OWNED = {'control': 'host_owned_unless_documented_per_task_control'}
TRANSIENT_IGNORE = ['runtime/', 'repository/', 'tasks/active.json', 'tasks/completed/']


def default_model_profile() -> dict:
    return {
        'schema_version': 3,
        'roles': {
            'primary': {'capability': 'frontier_reasoning', 'preferred_model': None},
            'reviewer': {'capability': 'frontier_review', 'preferred_model': None},
            'worker': {'capability': 'strong_coding', 'preferred_model': None},
        },
        'generic_reasoning': GENERIC_REASONING,
        'host_profiles': {
            'codex': {
                'effort_by_depth': CODEX_EFFORT_BY_DEPTH,
                'control': 'advisory_unless_runtime_confirms_per_task_control',
            },
            'claude-code': dict(HOST_OWNED),
            'gemini-cli': dict(HOST_OWNED),
            'cursor': dict(HOST_OWNED),
            'opencode': dict(HOST_OWNED),
        },
        'host_control': {
            'mutate_global_config': False,
            'claim_change_only_after_runtime_confirmation': True,
        },
        'note': 'Engineering depth is portable. Vendor model/reasoning knobs belong to host adapters and are not proof of benchmarked capability.',
    }


def ensure_model_profile(path: Path) -> None:
    current = read_json(path, {}) if path.exists() else {}
    merged = default_model_profile()
    if isinstance(current, dict):
        if isinstance(current.get('roles'), dict):
            merged['roles'].update(current['roles'])
        if isinstance(current.get('generic_reasoning'), dict):
            merged['generic_reasoning'].update(current['generic_reasoning'])
        if isinstance(current.get('host_profiles'), dict):
            for host, profile in current['host_profiles'].items():
                if isinstance(profile, dict):
                    merged['host_profiles'].setdefault(host, {}).update(profile)
        # v2 migration: old reasoning_profiles represented the Codex effort mapping.
        if isinstance(current.get('reasoning_profiles'), dict):
            merged['host_profiles']['codex']['effort_by_depth'].update(current['reasoning_profiles'])
        if isinstance(current.get('host_control'), dict):
            merged['host_control'].update(current['host_control'])
    write_json(path, merged)


def ensure_state_gitignore(path: Path) -> None:
    existing = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
    normalized = {line.strip() for line in existing if line.strip()}
    additions = [entry for entry in TRANSIENT_IGNORE if entry not in normalized]
    if not additions:
        return
    text = '\n'.join(existing)
    if text and not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(additions) + '\n'
    atomic_write(path, text)


def init(root: Path, emit: bool = True) -> dict:
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
    ensure_state_gitignore(s / '.gitignore')
    result = {'status': 'initialized', 'state_dir': str(s)}
    if emit:
        print(json.dumps(result, indent=2))
    return result


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


def normalize_entry_text(text: str) -> str:
    return ' '.join(text.split()).casefold()


def find_active_duplicate(path: Path, text: str) -> dict | None:
    needle = normalize_entry_text(text)
    for entry in read_jsonl(path):
        if entry.get('status', 'ACTIVE') != 'ACTIVE':
            continue
        if normalize_entry_text(str(entry.get('text', ''))) == needle:
            return entry
    return None


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


def capture(root: Path, entries: list[dict]) -> dict:
    """Persist a small batch of source-backed durable facts without duplicating active entries."""
    if not isinstance(entries, list):
        raise ValueError('knowledge entries must be a JSON array')
    added: list[dict] = []
    reused: list[dict] = []
    for raw in entries:
        if not isinstance(raw, dict):
            raise ValueError('each knowledge entry must be an object')
        kind = str(raw.get('kind', '')).strip().lower()
        text = str(raw.get('text', '')).strip()
        if kind not in REGISTRY:
            raise ValueError(f'unknown knowledge kind: {kind!r}')
        if not text:
            raise ValueError('knowledge entry text must not be empty')
        fn, _ = REGISTRY[kind]
        path = state_root(root) / 'registry' / fn
        duplicate = find_active_duplicate(path, text)
        if duplicate:
            reused.append(duplicate)
            continue
        extra = {k: raw.get(k) for k in ('why', 'source', 'risk')}
        added.append(add(root, kind, text, extra))
    return {
        'status': 'captured',
        'added': added,
        'reused': reused,
        'counts': {'added': len(added), 'reused': len(reused)},
    }


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


def load_json_argument(value: str):
    try:
        candidate = Path(value)
        if len(value) < 4096 and candidate.exists():
            return json.loads(candidate.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    return json.loads(value)


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
    c = sub.add_parser('capture')
    c.add_argument('--entries', required=True, help='JSON array or path to a JSON file')
    a = sub.add_parser('start-task')
    a.add_argument('--contract', required=True, help='JSON string or path')
    done = sub.add_parser('complete-task')
    done.add_argument('--knowledge', help='optional JSON array/path of durable knowledge to capture before completion')
    ns = ap.parse_args()
    root = Path(ns.root)
    if ns.cmd == 'init':
        return init(root)
    # Normal Codemium operations auto-initialize Project Brain silently. This is
    # the deterministic counterpart to the plugin rule that users should not
    # need a separate $cm-init step before ordinary repository work.
    if not state_root(root).exists():
        init(root, emit=False)
    if ns.cmd == 'status':
        print(json.dumps(status(root), indent=2))
        return
    if ns.cmd.startswith('add-'):
        kind = ns.cmd[4:]
        print(json.dumps(add(root, kind, ns.text, {'why': ns.why, 'source': ns.source, 'risk': ns.risk}), indent=2))
        return
    if ns.cmd == 'capture':
        entries = load_json_argument(ns.entries)
        print(json.dumps(capture(root, entries), ensure_ascii=False, indent=2))
        return
    if ns.cmd == 'start-task':
        contract = load_json_argument(ns.contract)
        contract.setdefault('started_at', now_iso())
        write_json(state_root(root) / 'tasks/active.json', contract)
        print(json.dumps(contract, ensure_ascii=False, indent=2))
        return
    if ns.cmd == 'complete-task':
        knowledge = None
        if ns.knowledge:
            knowledge = capture(root, load_json_argument(ns.knowledge))
        p = state_root(root) / 'tasks/active.json'
        task = read_json(p, None)
        if not task:
            print(json.dumps({'status': 'no-active-task', 'knowledge': knowledge}, ensure_ascii=False, indent=2))
            return
        task['completed_at'] = now_iso()
        tid = task.get('id', 'task')
        write_json(state_root(root) / 'tasks/completed' / f'{tid}.json', task)
        p.unlink(missing_ok=True)
        print(json.dumps({'status': 'completed', 'id': tid, 'knowledge': knowledge}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
