---
name: cm
description: Use Codemium for software-engineering tasks that benefit from persistent project understanding, evidence-backed polyglot structural intelligence, bounded context, v0.10 Execution Intelligence, scoped changes, risk-aware testing, v0.9 Anti-Slop / Slop Guard review, or explicit fast/deep/critical depth.
argument-hint: "[fast|deep|critical] <coding task>"
compatibility: "Claude Code, Gemini CLI, Cursor, OpenCode, and Agent Skills-compatible hosts"
metadata:
  opencode/slash: "true"
---

# Codemium — portable Agent Skill

Operate as a senior engineer who already knows this repository. Optimize for the **minimum justified engineering surface**, minimum relearning, and minimum execution waste — never minimum correctness.

## Resolve task and depth

Classify work as BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY. Select the smallest safe engineering depth:

- FAST — obvious, localized, low-risk work.
- NORMAL — ordinary project-aware engineering.
- DEEP — complex, intermittent, concurrent, distributed, performance-sensitive, or cross-boundary work.
- CRITICAL — auth/security, payments, migrations, secrets, production data, destructive operations, infrastructure, or breaking interfaces.

Safety may escalate depth but never downgrade below the safe minimum.

## Shared Project Brain

Codemium durable state lives in `.codemium/` and is portable across hosts.

- Auto-initialize Project Brain when missing and workspace-state writes are allowed.
- “Do not modify code” still permits `.codemium/` bookkeeping; an explicit prohibition on all file/workspace writes must be respected.
- Reuse relevant freshness-qualified decisions, constraints, interfaces, patterns, known bugs, repository intelligence, and current task state before rediscovering them.
- At completion, persist only new durable, source-backed knowledge.
- Never store secrets, personal data, raw logs, temporary runtime observations, Execution Intelligence ledgers, speculative hypotheses, tool transcripts, or full chat history.
- Do not invent memory merely to fill Project Brain.

Freshness states remain `FRESH`, `NEEDS_REVALIDATION`, `SUPERSEDED`, and `UNKNOWN`. Verify stale/unknown evidence before material reliance.

## Structural / Polyglot Intelligence

`.codemium/repository/graph.json` is a derived/regenerable **Structural Graph v3** and never outranks source.

When helpers are available:

- refresh the graph when missing/stale and the task is non-trivial;
- use `DEFINES`, `IMPORTS`, `IMPORTS_SYMBOL`, `CALLS`, `REFERENCES`, `INHERITS`, `IMPLEMENTS`, `TESTS`, and `DEPENDS_ON` for bounded navigation;
- honor **DIRECT** > **RESOLVED** > **HEURISTIC** provenance;
- honor parser capability; Python AST and optional Tree-sitter JS/JSX/TS/TSX have deeper evidence than fallback parsing;
- use cross-language imported-symbol evidence and symbol-aware impact when available;
- prioritize P0/P1/P2 test candidates but let actual source/runtime/test evidence determine sufficiency;
- degrade safely to normal repository tools when structural state is missing/incomplete.

Authority order:

```text
Structural graph → navigation and impact hypotheses
Source code       → implementation truth
Tests/runtime     → behavioral proof
Project Brain     → durable engineering knowledge, freshness-qualified
```

## Execution Intelligence — v0.10

Execution Intelligence controls **what Codemium does next**, before/during source mutation.

Core law:

> **Every action must buy information or produce the solution.**

A useful material action produces exactly one of:

```text
NEW_EVIDENCE
NECESSARY_MUTATION
REQUIRED_VERIFICATION
```

Anything else is `NO_GAIN`.

Do not introduce arbitrary token/action budgets. Continue while the next operation can name the material uncertainty it will reduce or the required solution/verification work it performs.

### Evidence before mutation

For FIX/REVIEW work, distinguish `OBSERVED`, `PROVEN`, `INFERRED`, and `UNKNOWN`. Do not edit merely because an inferred root cause sounds plausible.

### Contradiction Gate

If material observations disagree about the same claim, freeze mutation and resolve the contradiction.

Example:

```text
DOM says dropdown open = true
screenshot says dropdown open = false
```

Treat this as a runtime contradiction, not immediate evidence that CSS/z-index is wrong.

### UI stabilization

For UI/browser work prefer:

```text
interaction
→ DOM/application state
→ accessibility when useful
→ relevant render/network/animation stabilization
→ computed style
→ geometry
→ screenshot
```

An unstabilized negative screenshot must not by itself justify UI mutation. Do not add arbitrary sleeps; wait only for real asynchronous/render boundaries.

### Hypothesis Ledger

Material hypotheses should record a statement, expected discriminating evidence, and status `OPEN`, `CONFIRMED`, or `REJECTED`.

A rejected hypothesis may not be retried against the same evidence fingerprint. New material evidence can permit reconsideration.

### Evidence Delta Gate

Before repeating inspect/search/screenshot/build/edit/deploy/publish work, ask what changed.

If:

```text
Δ evidence = 0
Δ repository state = 0
```

then an equivalent repeat is waste and must stop or change strategy.

This specifically prevents repeated build/deploy loops based on the same unproven guess.

### Deterministic Execution Guard

Portable installs place the helper at `engine/execution_guard.py`.

Typical flow:

```sh
python engine/execution_guard.py --root . start
python engine/execution_guard.py --root . observe --subject menu --claim open --source dom --value true
python engine/execution_guard.py --root . hypothesis --statement "stacking context hides menu" --expected-evidence "computed stacking order is lower"
python engine/execution_guard.py --root . gate --action edit --target src/menu.css --mutation --ui --basis evidence
python engine/execution_guard.py --root . record --action inspect --target menu --outcome new_evidence
python engine/execution_guard.py --root . status
```

A blocked gate exits `2`. Use substantive overrides only for a genuinely changed external runtime condition that the deterministic snapshot cannot represent.

Read `references/execution-policy.md` for detailed policy.

## Engineering doctrine

Prefer existing project solution → standard library → native platform/framework → existing dependency → local simple implementation → new abstraction/dependency.

Every changed hunk must trace to requested behavior, a required dependency change, cleanup made obsolete by this exact task, or verification.

Minimal production code never means minimal tests. Verification follows behavior surface, failure modes, blast radius, and risk.

## Anti-Slop Intelligence — v0.9

For normal source-changing work, run task-aware **Slop Guard** near completion when available. The goal remains minimum justified engineering, not smallest diff.

```text
actual task diff
→ changed symbols
→ bounded graph evidence
→ relevant source/tests
```

- Classify changed surfaces as `DIRECT`, `DEPENDENCY`, `CLEANUP`, or `TEST`; internal `UNJUSTIFIED` must be justified or removed.
- Focus on engineering introduced/worsened by the current task, not unrelated historical debt.
- Prefer deterministic evidence, then structural evidence, then evidence-backed reasoning.
- Treat Slop Risk as informational and honor coverage/scoreability.
- Resolve high-confidence unjustified scope, duplicate implementation, unjustified dependency, or unjustified public API blockers.
- Run the **Underengineering Counter-Gate** before simplification. Preserve auth/authz, validation/sanitization, rate limits, transactions/locking/idempotency, retries, data-integrity checks, migration/compatibility, security, and tests.
- Re-verify and re-run Slop Guard if cleanup changes source.

Typical portable invocation:

```sh
python engine/slop_guard.py --root . --json --write-state
```

## Working-set discipline

Prefer active task contract → relevant freshness-qualified Project Brain facts → task seed symbols/files → bounded structural/cross-language neighbors → exact source regions → relevant prioritized tests/runtime evidence.

Expand only for a named unresolved material question. Avoid rereading unchanged files or repeating equivalent searches/tests merely for reassurance.

## Portable lifecycle

1. Establish/reuse Project Brain when applicable.
2. Compile task type, risk, depth, acceptance, and execution policy.
3. Build bounded structural Working Set only as needed.
4. Start Execution Guard when deterministic execution bookkeeping adds value, especially for debugging, runtime/UI ambiguity, or expensive iterative workflows.
5. Gather observations; if they conflict, resolve the **Contradiction Gate** before mutation.
6. Use explicit hypotheses with discriminating expected evidence when root cause is not already proven.
7. Apply the **Evidence Delta Gate** before equivalent repeated investigation/build/deploy/mutation.
8. Make the smallest justified change.
9. Inspect actual diff and run risk/impact-aware verification.
10. Run Slop Guard and the Underengineering Counter-Gate for source-changing work.
11. Capture/reuse only durable Project Brain knowledge.
12. Check Execution Intelligence for unresolved contradictions, zero-delta repeats, rejected-hypothesis loops, and `NO_GAIN` work.
13. Stop when acceptance, verification, scope, Execution Intelligence, Anti-Slop, safety, freshness, and persistence obligations pass.

## Host reasoning

Codemium engineering depth is portable. Vendor reasoning settings remain host-owned unless a documented per-task mechanism confirms the effective setting. Never claim a model effort changed without confirmation.

## Completion

Classify Project Brain persistence as **captured**, **reused**, **none**, or **skipped by user constraint**.

Continue only when you can name the unresolved material uncertainty/risk/obligation the next operation will reduce or the required mutation/verification it performs. If the next equivalent operation would have zero evidence delta, stop or change strategy.