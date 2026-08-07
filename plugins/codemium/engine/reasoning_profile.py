#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Iterable

GENERIC_CLASS_ORDER = ['economy', 'balanced', 'strong', 'frontier']
GENERIC_DEPTH_PROFILE = {
    'FAST': {'preferred_class': 'economy', 'minimum_class': 'economy', 'reason': 'localized low-risk engineering'},
    'NORMAL': {'preferred_class': 'balanced', 'minimum_class': 'economy', 'reason': 'ordinary project-aware engineering'},
    'DEEP': {'preferred_class': 'strong', 'minimum_class': 'balanced', 'reason': 'complex or cross-boundary engineering'},
    'CRITICAL': {'preferred_class': 'frontier', 'minimum_class': 'strong', 'reason': 'quality-first high-risk engineering'},
}

EFFORT_ORDER = ['none', 'low', 'medium', 'high', 'xhigh', 'max']
CODEX_CLASS_TO_EFFORT = {
    'economy': 'low',
    'balanced': 'medium',
    'strong': 'high',
    'frontier': 'xhigh',
}
KNOWN_CODEX_MODELS = {
    'gpt-5.6': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.6-sol': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.6-terra': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.6-luna': ['none', 'low', 'medium', 'high', 'xhigh', 'max'],
    'gpt-5.3-codex': ['low', 'medium', 'high', 'xhigh'],
    'gpt-5.2-codex': ['low', 'medium', 'high', 'xhigh'],
}
HOSTS = {'generic', 'codex', 'claude-code', 'gemini-cli'}


def rank(effort: str) -> int:
    return EFFORT_ORDER.index(effort)


def nearest_supported(target: str, supported: Iterable[str]) -> str | None:
    values = [x for x in supported if x in EFFORT_ORDER]
    if not values:
        return None
    return min(values, key=lambda x: (abs(rank(x) - rank(target)), rank(x)))


def alignment(host_effort: str | None, preferred: str | None, minimum: str | None) -> str:
    if preferred is None or minimum is None:
        return 'host_owned'
    if not host_effort or host_effort not in EFFORT_ORDER:
        return 'host_unknown'
    if rank(host_effort) < rank(minimum):
        return 'host_below_minimum'
    if rank(host_effort) > rank(preferred):
        return 'host_above_preferred'
    if host_effort == preferred:
        return 'aligned'
    return 'host_within_safe_range'


def infer_host(host: str | None, model: str | None) -> str:
    if host:
        normalized = host.lower()
        if normalized not in HOSTS:
            raise ValueError(f'unknown host: {host}')
        return normalized
    m = (model or '').lower()
    if m.startswith('gpt-'):
        return 'codex'
    return 'generic'


def resolve_reasoning_profile(
    depth: str,
    model: str | None = None,
    host_effort: str | None = None,
    host: str | None = None,
) -> dict:
    depth = depth.upper()
    if depth not in GENERIC_DEPTH_PROFILE:
        raise ValueError(f'unknown depth: {depth}')
    base = GENERIC_DEPTH_PROFILE[depth]
    resolved_host = infer_host(host, model)
    preferred_effort = None
    minimum_effort = None
    requested_effort = None
    model_known = False

    if resolved_host == 'codex':
        target = CODEX_CLASS_TO_EFFORT[base['preferred_class']]
        minimum_target = CODEX_CLASS_TO_EFFORT[base['minimum_class']]
        supported = KNOWN_CODEX_MODELS.get((model or '').lower())
        model_known = supported is not None
        preferred_effort = nearest_supported(target, supported) if supported else target
        minimum_effort = nearest_supported(minimum_target, supported) if supported else minimum_target
        if preferred_effort and minimum_effort and rank(preferred_effort) < rank(minimum_effort):
            preferred_effort = minimum_effort
        requested_effort = preferred_effort
        control = 'advisory_unless_runtime_confirms_per_task_control'
        note = 'Do not claim Codex reasoning changed unless the runtime confirms the effective setting.'
    else:
        control = 'host_owned_unless_documented_per_task_control'
        note = 'Engineering depth is portable; vendor reasoning controls remain host-owned unless documented and confirmed.'

    return {
        'depth': depth,
        'reasoning_class': base['preferred_class'],
        'minimum_reasoning_class': base['minimum_class'],
        'host': resolved_host,
        'model': model,
        'model_capabilities_known': model_known,
        'preferred_effort': preferred_effort,
        'minimum_effort': minimum_effort,
        'host_effort': host_effort,
        'alignment': alignment(host_effort, preferred_effort, minimum_effort),
        'host_control': control,
        'requested_effort': requested_effort,
        'reason': base['reason'],
        'note': note,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--depth', required=True, choices=['fast', 'normal', 'deep', 'critical'])
    ap.add_argument('--host', choices=sorted(HOSTS))
    ap.add_argument('--model')
    ap.add_argument('--host-effort', choices=EFFORT_ORDER)
    ap.add_argument('--emit-responses-api', action='store_true')
    ns = ap.parse_args()
    profile = resolve_reasoning_profile(ns.depth, ns.model, ns.host_effort, ns.host)
    if ns.emit_responses_api:
        if profile['host'] != 'codex' or not profile['requested_effort']:
            raise SystemExit('--emit-responses-api is only available for a Codex reasoning profile')
        profile['responses_api'] = {'reasoning': {'effort': profile['requested_effort']}}
    print(json.dumps(profile, indent=2))


if __name__ == '__main__':
    main()
