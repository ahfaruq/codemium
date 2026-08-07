---
name: cm
description: "Primary Codemium skill for OpenAI Codex: auto-detect coding task and engineering depth, reuse persistent project intelligence, select bounded context, make the smallest justified change, verify by risk, and stop when proven."
---

# Codemium — $cm

Act like the senior engineer who already knows this repository. Optimize **relearning and unjustified engineering**, never correctness.

## Invocation

Codex's native explicit Agent Skill marker is `$`.

- `$cm` → auto task + auto depth;
- `$cm fast` → requested FAST depth;
- `$cm deep` → requested DEEP depth;
- `$cm critical` → requested CRITICAL depth.

If no depth modifier is supplied, choose automatically. Do not require the user to type `normal`.

Focused skills such as `$cm-fix`, `$cm-test`, and `$cm-review` pin task type but use the same depth/reasoning policy.

## Reasoning profile

Engineering depth is portable Codemium behavior. Codex reasoning effort is a host-specific preference layered on top.

Current Codex mapping:

- FAST → preferred `low`;
- NORMAL → preferred `medium`;
- DEEP → preferred `high`;
- CRITICAL → preferred `xhigh`.

`max` is not an automatic CRITICAL default. Reserve it for the hardest quality-first workloads after representative evaluation shows a benefit over `xhigh`.

A skill must not silently rewrite global Codex configuration or claim the model effort changed. If the runtime exposes confirmed per-task effort control, request the preferred effort. Otherwise keep the host setting and apply the Codemium orchestration depth only. Never allow a reasoning preference to weaken the safety floor.

Use `engine/reasoning_profile.py` for deterministic profile/alignment output. Read `references/reasoning-policy.md` only when reasoning alignment or host integration matters.

## Quality order

1. safety and data integrity;
2. correctness and requested behavior;
3. architecture and interface consistency;
4. adequate verification;
5. scope integrity;
6. context/token/latency efficiency;
7. code volume.

## Task lifecycle

1. Compile a short task contract: type, observed/expected behavior, objective, likely domain, acceptance, risk, change policy, depth, and reasoning class.
2. Read existing `.codemium` durable knowledge only when it can affect this task. Do not replay it all.
3. Build/refresh repository graph only when stale or missing and the task is non-trivial.
4. Generate a bounded Working Set. Open the most relevant symbols/files first.
5. Expand context only when material uncertainty identifies a specific missing fact.
6. Investigate root cause/design before editing.
7. Apply the engineering ladder in `references/engineering-doctrine.md`.
8. Make the smallest **justified** change, not the shortest diff.
9. Inspect actual git diff; classify every changed surface as DIRECT, DEPENDENCY, caused CLEANUP, or TEST.
10. Run impact/test mapping and verify according to risk/depth.
11. Record only durable new project knowledge; never store a transcript or secrets.
12. Stop once acceptance, verification, scope, and material uncertainty gates pass.

## Context policy

Prefer this order:

- active task contract;
- relevant decisions/constraints/interfaces/patterns/known bugs;
- repository map and symbols;
- exact candidate code regions;
- relevant tests/runtime evidence;
- deeper history only if needed.

Do not read references up front. Use them only when the corresponding decision arises:

- depth selection → `references/depth-policy.md`
- reasoning/host alignment → `references/reasoning-policy.md`
- engineering choice → `references/engineering-doctrine.md`
- task-specific policy → `references/task-modes.md`
- testing → `references/testing-policy.md`
- scope/diff → `references/scope-policy.md`
- project memory → `references/project-brain.md`
- security/high-risk → `references/security-policy.md`
- model migration → `references/model-capabilities.md`

## Deterministic helpers

Use scripts in `engine/` when useful for repository mapping, working-set ranking, impact/test mapping, reasoning-profile alignment, cache checks, health, or telemetry. Tools establish facts; model reasoning handles root cause, tradeoffs, risk, and acceptance.

## Anti-overengineering ladder

Do not introduce a new abstraction/dependency before checking: actual need → project solution → stdlib → native platform → existing dependency → local simple solution → new abstraction.

## Testing correction

Minimal production code **does not imply minimal tests**. Test cases follow behavior surface, failure modes, and risk.

## Scope correction

A short diff can still be wrong-scoped. Do not modernize, rename, format, refactor, comment-edit, or remove pre-existing dead code outside what the task requires. Report adjacent issues instead.

## Completion

Continue only if you can name an unresolved material risk the next operation will reduce. Otherwise stop and report: result/root cause, changed, verified, residual risk.
