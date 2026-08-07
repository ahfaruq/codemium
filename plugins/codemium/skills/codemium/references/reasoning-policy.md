# Codemium Reasoning Policy

Codemium separates **engineering depth** from the Codex host's actual model reasoning setting.

The default profile is intentionally conservative:

| Depth | Preferred effort | Minimum profile |
| --- | --- | --- |
| FAST | low | low |
| NORMAL | medium | low |
| DEEP | high | medium |
| CRITICAL | xhigh | high |

For the GPT-5.6 family these effort values are supported. `max` is available on GPT-5.6, but Codemium does not make it the automatic CRITICAL default. Use `max` only for the hardest quality-first workloads after representative benchmarks show a material gain over `xhigh`.

## Host-control rule

A Codemium skill must not assume it can mutate the active Codex model/reasoning setting.

1. Resolve the task depth.
2. Resolve the preferred reasoning profile.
3. If the runtime exposes safe, confirmed **per-task** reasoning control, request that effort.
4. If it does not, keep the host setting and apply only Codemium's context/tool/verification policy.
5. Never silently edit global Codex configuration to implement a task-local preference.
6. Never say the effort changed unless the host/runtime confirms the effective setting.

Use `engine/reasoning_profile.py` to compare a known host effort with the preferred profile.

Example:

```sh
python <plugin-dir>/engine/reasoning_profile.py \
  --depth fast \
  --model gpt-5.6-sol \
  --host-effort xhigh
```

The result reports `host_above_preferred`: Codemium recommends `low`, but it does not pretend the active `xhigh` host setting was changed.

## Safety alignment

The reasoning profile follows the **effective** depth, not the user's requested word. Therefore:

```text
@cm fast change authentication flow
```

must become:

```text
Depth: CRITICAL
Preferred reasoning: xhigh
```

The token-saving preference never overrides the safety floor.

## Model independence

Do not hard-code behavior around a model name beyond a validated capability registry. If a future model has different effort labels or reaches the same quality at a lower effort, update the registry only after representative evaluation. Preserve the quality floor before optimizing tokens, latency, or cost.
