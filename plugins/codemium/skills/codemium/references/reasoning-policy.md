# Codemium Reasoning Policy

Codemium separates **portable engineering depth** from vendor-specific model reasoning controls.

## Portable core classes

| Depth | Preferred reasoning class | Minimum class |
| --- | --- | --- |
| FAST | economy | economy |
| NORMAL | balanced | economy |
| DEEP | strong | balanced |
| CRITICAL | frontier | strong |

These classes describe how much engineering reasoning/context rigor a task deserves. They are part of Codemium core and do not assume a model vendor.

## Codex adapter mapping

The current Codex adapter maps the portable classes to a preferred GPT reasoning effort when supported:

| Depth | Preferred Codex effort | Minimum Codex effort |
| --- | --- | --- |
| FAST | low | low |
| NORMAL | medium | low |
| DEEP | high | medium |
| CRITICAL | xhigh | high |

For GPT-5.6, `max` is available but is not the automatic CRITICAL default. Reserve it for the hardest quality-first workloads after representative evaluation shows a material gain over `xhigh`.

## Claude Code and Gemini CLI

The beta adapters currently apply reasoning class through engineering behavior: working-set breadth, investigation depth, impact analysis, and verification strength. They do not claim to change Claude/Gemini thinking or model controls.

## Host-control rule

1. Resolve effective engineering depth after the safety floor.
2. Resolve the portable reasoning class.
3. Let the host adapter map that class only if a documented host control exists.
4. Request a host-specific effort only when the runtime exposes safe, confirmed per-task control.
5. Otherwise keep host settings unchanged and apply Codemium's context/tool/verification policy.
6. Never silently edit global host configuration for a task-local preference.
7. Never claim model/thinking effort changed unless the host confirms the effective setting.

Use `engine/reasoning_profile.py` for deterministic portable and host-specific output.

Codex example:

```sh
python <plugin-dir>/engine/reasoning_profile.py \
  --depth fast \
  --host codex \
  --model gpt-5.6-sol \
  --host-effort xhigh
```

Claude example:

```sh
python <plugin-dir>/engine/reasoning_profile.py \
  --depth deep \
  --host claude-code
```

The Claude result keeps the portable `strong` class but leaves vendor effort unset/host-owned.

## Safety alignment

The profile follows the **effective** depth, not merely the user's requested word. A FAST request on authentication may escalate to CRITICAL; the portable reasoning class therefore becomes `frontier`, and the Codex adapter would prefer `xhigh` if applicable.

## Model and host independence

Do not hard-code Codemium core around a model name, vendor effort label, or host syntax. Capability registries and adapter mappings may change only after current host/model behavior is verified. Preserve the quality floor before optimizing tokens, latency, or cost.
