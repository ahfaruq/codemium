#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Iterable

EFFORT_ORDER = ['none', 'low', 'medium', 'high', 'xhigh', 'max']
DEPTH_PROFILE = {
    'FAST': {'preferred_effort': 'low', 'minimum_effort': 'low', 'reason': 'latency/token-sensitive localized work'},
    'NORMAL': {'preferred_effort': 'medium', 'minimum_effort': 'low', 'reason': 'balanced project-aware engineering'},
    'DEEP': {'preferred_effort': 'high', 'minimum_effort': 'medium', 'reason': 'complex or cross-boundary reasoning'},
    'CRITICAL': {'preferred_effort': 'xhigh', 'minimum_effort': 'high', 'reason': 'quality-first high-risk engineering'},
}

KNOWN_MODELS = {
    'gpt-5.6': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.6-sol': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.6-terra': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.6-luna': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.3-codex': ['low', 'medium', 'high', 'xhigh'],
    'gpt-5.2-codex': ['low', 'medium', 'high', 'xhigh'],
}


def rank(effort: str) -> int:
    return EFFORT_ORDER.index(effort)


def nearest_supported(target: str, supported: Iterable[str]) -> str | None:
    values = [x for x in supported if x in EFFORT_ORDER]
    if not values:
        return None
    return min(values, key=lambda x: (abs(rank(x) - rank(target)), rank(x)))


def alignment(host_effort: str | None, preferred: str, minimum: str) -> str:
    if not host_effort:
        return 'host_unknown'
    if host_effort not in EFFORT_ORDER:
        return 'host_unknown'
    if rank(host_effort) < rank(minimum):
        return 'host_below_minimum'
    if rank(host_effort) > rank(preferred):
        return 'host_above_preferred'
    if host_effort == preferred:
        return 'aligned'
    return 'host_within_safe_range'


def resolve_reasoning_profile(depth: str, model: str | None = None, host_effort: str | None = None) -> dict:
    depth = depth.upper()
    if depth not in DEPTH_PROFILE:
        raise ValueError(f'unknown depth: {depth}')
    base = DEPTH_PROFILE[depth]
    preferred = base['preferred_effort']
    minimum = base['minimum_effort']
    supported = KNOWN_MODELS.get((model or '').lower())
    model_known = supported is not None
    requested = nearest_supported(preferred, supported) if supported else preferred
    min_supported = nearest_supported(minimum, supported) if supported else minimum
    if supported and requested and min_supported and rank(requested) < rank(min_supported):
        requested = min_supported
    return {
        'depth': depth,
        'model': model,
        'model_capabilities_known': model_known,
        'preferred_effort': requested,
        'minimum_effort': min_supported,
        'host_effort': host_effort,
        'alignment': alignment(host_effort, requested, min_supported),
        'host_control': 'advisory_unless_runtime_confirms_per_task_control',
        'requested_effort': requested,
        'reason': base['reason'],
        'note': 'Do not claim the host effort changed unless the Codex runtime confirms the effective setting.',
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--depth', required=True, choices=['fast', 'normal', 'deep', 'critical'])
    ap.add_argument('--model')
    ap.add_argument('--host-effort', choices=EFFORT_ORDER)
    ap.add_argument('--emit-responses-api', action='store_true')
    ns = ap.parse_args()
    profile = resolve_reasoning_profile(ns.depth, ns.model, ns.host_effort)
    if ns.emit_responses_api:
        profile['responses_api'] = {'reasoning': {'effort': profile['requested_effort']}}
    print(json.dumps(profile, indent=2))


if __name__ == '__main__':
    main()
