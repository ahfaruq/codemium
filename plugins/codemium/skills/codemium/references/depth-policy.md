# Codemium Depth Policy

Depth controls orchestration rigor: context expansion, investigation breadth, impact analysis, and verification. Codemium also maps the **effective depth** to a preferred reasoning profile, but a skill does not assume it can mutate the host setting.

## AUTO (`@cm`)

Classify task and risk first, then select the smallest depth that preserves the quality floor.

## FAST

Use for obvious, localized, low-risk work such as a small copy/spacing/style correction or another change whose relevant surface is already clear.

Policy: tiny working set, no speculative exploration, no delegation, targeted verification. Preferred reasoning profile: `low`.

FAST never means skip a check that is required to prove behavior.

## NORMAL

Internal default for ordinary feature/fix/refactor work. Project-aware bounded working set, normal root-cause/design reasoning, impact mapping, and sufficient targeted verification.

Preferred reasoning profile: `medium`.

NORMAL is not a required user keyword; plain `@cm` selects it when appropriate.

## DEEP

Use for concurrency/races, intermittent/flaky behavior, distributed or cross-boundary flows, difficult performance issues, multi-module changes, or material uncertainty.

Policy: broader-but-bounded dependency traversal, relevant historical Project Brain retrieval, stronger impact analysis, more verification evidence, optional fresh review when it creates net value.

Preferred reasoning profile: `high`.

## CRITICAL

Use for security/trust boundaries, authentication/authorization, payments/billing, database migrations/schema changes, secrets, production data, destructive operations, deployment/infrastructure, or breaking public interfaces.

Policy: correctness/security/data integrity outrank token efficiency; require explicit impact thinking, rollback/compatibility where relevant, and stronger verification/review. Still do not load unrelated repository context.

Preferred reasoning profile: `xhigh`. Do not use `max` automatically; benchmark it against `xhigh` for the hardest quality-first workloads.

## Overrides and safety floor

`fast`, `deep`, and `critical` are requests. The system may escalate but must never downgrade below the safe minimum. Reasoning preference follows the effective depth after escalation.

Examples:

- `@cm fast` + CSS spacing → FAST + preferred `low`.
- `@cm` + normal feature → NORMAL + preferred `medium`.
- `@cm` + intermittent queue race → DEEP + preferred `high`.
- `@cm fast` + authentication change → CRITICAL + preferred `xhigh`, because safety floor wins.
- `@cm deep` + normal feature → DEEP + preferred `high`, because upward overrides are allowed.

See `reasoning-policy.md` for host-control and alignment rules.
