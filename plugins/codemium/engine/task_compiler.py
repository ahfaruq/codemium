#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import state_root, now_iso, write_json
from reasoning_profile import EFFORT_ORDER, HOSTS, resolve_reasoning_profile

DEPTH_RANK = {'FAST': 0, 'NORMAL': 1, 'DEEP': 2, 'CRITICAL': 3}


def classify(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ['security', 'vulnerab', 'authz', 'authorization', 'permission', 'secret', 'injection']):
        return 'SECURITY'
    if any(x in t for x in ['migration', 'migrate', 'schema change', 'database upgrade']):
        return 'MIGRATION'
    if any(x in t for x in ['review', 'audit pr', 'code review']):
        return 'REVIEW'
    if any(x in t for x in ['refactor', 'cleanup architecture', 'simplify code']):
        return 'REFACTOR'
    if any(x in t for x in ['test', 'coverage', 'spec case']) and not any(x in t for x in ['bug', 'fix', 'error', 'fail']):
        return 'TEST'
    if any(x in t for x in ['bug', 'fix', 'error', 'fail', 'broken', 'duplicate', 'stuck', 'wrong', 'tidak', 'kenapa']):
        return 'FIX'
    return 'BUILD'


def risk(text: str, mode: str) -> str:
    t = text.lower()
    if mode in {'SECURITY', 'MIGRATION'} or any(x in t for x in [
        'payment', 'billing', 'delete production', 'destructive', 'auth', 'permission',
        'concurrency', 'race', 'deployment', 'infrastructure', 'production data'
    ]):
        return 'high'
    if mode in {'FIX', 'REFACTOR', 'REVIEW'} or any(x in t for x in ['database', 'api', 'worker', 'queue', 'webhook']):
        return 'medium'
    return 'low'


def minimum_depth(text: str, mode: str, task_risk: str) -> tuple[str, str]:
    t = text.lower()
    critical_terms = [
        'payment', 'billing', 'auth', 'authorization', 'permission', 'secret',
        'migration', 'schema change', 'production data', 'destructive',
        'deployment', 'infrastructure', 'public api breaking', 'breaking api'
    ]
    if mode in {'SECURITY', 'MIGRATION'} or any(x in t for x in critical_terms):
        return 'CRITICAL', 'safety-critical domain'
    if task_risk == 'high' or any(x in t for x in [
        'concurrency', 'race', 'deadlock', 'intermittent', 'flaky',
        'distributed', 'memory leak', 'performance regression'
    ]):
        return 'DEEP', 'high-risk or non-local behavior'
    return 'FAST', 'no safety escalation required'


def auto_depth(text: str, mode: str, task_risk: str) -> tuple[str, str]:
    floor, floor_reason = minimum_depth(text, mode, task_risk)
    if floor in {'CRITICAL', 'DEEP'}:
        return floor, floor_reason
    t = text.lower()
    trivial_terms = ['typo', 'copy text', 'label text', 'css spacing', 'padding', 'margin', 'font size', 'color only']
    if task_risk == 'low' and any(x in t for x in trivial_terms):
        return 'FAST', 'localized low-risk change'
    if any(x in t for x in ['multi-module', 'cross-module', 'websocket', 'queue', 'webhook', 'worker']):
        return 'DEEP', 'cross-boundary behavior'
    return 'NORMAL', 'default project-aware depth'


def resolve_depth(text: str, mode: str, task_risk: str, requested: str = 'auto') -> tuple[str, str]:
    requested = requested.lower().strip()
    if requested == 'auto':
        return auto_depth(text, mode, task_risk)
    requested_map = {'fast': 'FAST', 'deep': 'DEEP', 'critical': 'CRITICAL'}
    if requested not in requested_map:
        raise ValueError('depth must be auto, fast, deep, or critical')
    desired = requested_map[requested]
    floor, floor_reason = minimum_depth(text, mode, task_risk)
    if DEPTH_RANK[desired] < DEPTH_RANK[floor]:
        return floor, f'requested {desired} escalated: {floor_reason}'
    return desired, f'explicit {desired} override'


def compile_task(
    text: str,
    requested_depth: str = 'auto',
    model: str | None = None,
    host_effort: str | None = None,
    host: str | None = None,
) -> dict:
    mode = classify(text)
    r = risk(text, mode)
    depth, depth_reason = resolve_depth(text, mode, r, requested_depth)
    reasoning = resolve_reasoning_profile(depth, model=model, host_effort=host_effort, host=host)
    policy = {
        'FIX': 'root-cause fix; surgical scope; regression evidence',
        'TEST': 'behavior/risk coverage; do not minimize justified cases',
        'REFACTOR': 'behavior preservation; demonstrated complexity only',
        'REVIEW': 'read-only unless explicitly asked to edit',
        'MIGRATION': 'compatibility, data integrity, rollback',
        'SECURITY': 'trust-boundary correctness outranks efficiency',
        'BUILD': 'reuse-first; minimum justified architecture',
    }[mode]
    return {
        'id': 'T' + now_iso().replace('-', '').replace(':', '').replace('T', '')[:14],
        'type': mode,
        'request': text,
        'objective': text.strip(),
        'expected_behavior': 'derive from request/evidence before editing',
        'likely_domain': [],
        'acceptance': [
            'requested behavior is satisfied',
            'relevant verification passes',
            'no unrelated diff',
            'no material unexplained uncertainty',
        ],
        'risk': r,
        'requested_depth': requested_depth.lower(),
        'depth': depth,
        'depth_reason': depth_reason,
        'reasoning': reasoning,
        'change_policy': policy,
        'created_at': now_iso(),
        'working_set': [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--request', required=True)
    ap.add_argument('--depth', choices=['auto', 'fast', 'deep', 'critical'], default='auto')
    ap.add_argument('--host', choices=sorted(HOSTS))
    ap.add_argument('--model')
    ap.add_argument('--host-effort', choices=EFFORT_ORDER)
    ap.add_argument('--no-write', action='store_true')
    ns = ap.parse_args()
    task = compile_task(ns.request, ns.depth, ns.model, ns.host_effort, ns.host)
    root = Path(ns.root).resolve()
    if not ns.no_write:
        p = state_root(root) / 'tasks/active.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        write_json(p, task)
    print(json.dumps(task, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
