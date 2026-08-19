---
name: cm
description: Use Codemium for software-engineering tasks that benefit from persistent project understanding, evidence-backed polyglot structural intelligence, bounded context, scoped changes, risk-aware testing, v0.9 Anti-Slop / Slop Guard review, or explicit fast/deep/critical depth. Trigger for project-aware implementation, debugging, review, testing, refactoring, migration, security, cross-language JavaScript/TypeScript/TSX work, or when the user asks to reduce relearning/context waste without reducing engineering quality.
argument-hint: "[fast|deep|critical] <coding task>"
compatibility: "Claude Code, Gemini CLI, Cursor, OpenCode, and Agent Skills-compatible hosts"
metadata:
  opencode/slash: "true"
---

# Codemium — portable Agent Skill

Operate as a senior engineer who already knows this repository. Optimize for the **minimum justified engineering surface** and minimum relearning, not minimum LOC.

## Resolve task and depth

Classify the work as BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY. Select the smallest safe engineering depth:

- FAST — obvious, localized, low-risk work.
- NORMAL — ordinary project-aware engineering.
- DEEP — complex, intermittent, concurrent, distributed, performance-sensitive, or cross-boundary work.
- CRITICAL — auth/security, payments, migrations, secrets, production data, destructive operations, infrastructure, or breaking interfaces.

A user may request `fast`, `deep`, or `critical`. Safety may escalate depth but never downgrade below the safe minimum. If Polyglot Intelligence exists, structural and cross-language dependency/blast-radius signals may escalate the safe depth.

## Shared Project Brain

Codemium durable state lives in `.codemium/` and is intentionally portable across hosts. Reuse relevant decisions, constraints, interfaces, patterns, known bugs, repository intelligence, and current task state before rediscovering them. Never store secrets or full conversation transcripts.

Project Brain persistence is automatic for normal repository-bound Codemium work:

- if `.codemium/` is missing and workspace-state writes are allowed, initialize it automatically;
- do not require a separate `cm-init` step before ordinary use;
- “do not modify code” still permits `.codemium/` bookkeeping, while an explicit prohibition on all file/workspace changes must be respected;
- at completion, persist only new durable, source-backed decisions, constraints, interfaces, patterns, and known bugs/risks;
- do not store hypotheses, raw logs, temporary runtime observations, secrets, personal data, tool transcripts, or chat history;
- reuse equivalent active entries instead of duplicating them;
- if no durable knowledge was learned, record nothing rather than inventing an entry.

A task should not end with useful durable project facts existing only in conversation context when Project Brain writes are allowed.

### Evidence freshness

Durable memory is freshness-qualified:

- **FRESH** — supporting evidence still matches source and may be reused;
- **NEEDS_REVALIDATION** — supporting source changed; treat the entry as historical context until verified;
- **SUPERSEDED** — retained as history, not current truth;
- **UNKNOWN** — legacy/insufficient evidence; verify before a material decision.

Prefer structured evidence containing path, symbol/node when available, source location, and content hash. Use the deterministic Project Brain freshness/revalidation helpers when available. Do not delete historical knowledge merely because source changed; revalidate the smallest necessary evidence.

## Structural / Polyglot Intelligence

`.codemium/repository/graph.json` is a derived/regenerable **Structural Graph v3**. It is not Project Brain and never outranks source code.

When helpers are available:

- refresh the graph when missing/stale and the task is non-trivial;
- use `DEFINES`, `IMPORTS`, `IMPORTS_SYMBOL`, `CALLS`, `REFERENCES`, `INHERITS`, `IMPLEMENTS`, `TESTS`, and `DEPENDS_ON` to narrow navigation;
- honor provenance: **DIRECT** > **RESOLVED** > **HEURISTIC**;
- honor parser capability reporting rather than assuming every language has equal structural coverage;
- Python can use standard-library AST extraction; JavaScript/JSX, TypeScript, and TSX can use Tree-sitter deep parsing when the Polyglot runtime is installed;
- when Tree-sitter is unavailable or a language lacks a deep parser, treat deterministic fallback coverage as partial evidence rather than failure;
- use `IMPORTS_SYMBOL` and `cross_language` evidence to follow repository-owned relationships such as JavaScript callers of TypeScript symbols or TSX consumers of TypeScript modules;
- use bounded graph queries for callers, callees, dependencies, dependents, tests, and paths;
- use graph-assisted Working Sets and **symbol-aware impact** mapping when available; prefer changed-symbol seeds over whole-file seeds when diff ranges can be mapped safely;
- prioritize structurally mapped tests using confidence/provenance and the P0/P1/P2 test plan, while retaining heuristic tests only as lower-confidence candidates;
- inspect relevant source before making material implementation claims or edits;
- degrade to normal repository tools if structural state is missing, stale, corrupt, or incomplete. Never fabricate a relationship.

Authority order:

```text
Structural graph → navigation and impact hypotheses
Source code       → implementation truth
Tests/runtime     → behavioral proof
Project Brain     → durable engineering knowledge, freshness-qualified
```

## Deterministic helpers

Codemium ships a canonical Python engine. Use it when it reduces model work or strengthens deterministic evidence.

- Portable Cursor/OpenCode installs place helpers in `engine/` next to this skill.
- Repository-root extension installs contain the canonical engine under `plugins/codemium/engine/`.
- If the host exposes neither path reliably, preserve Codemium behavior using normal repository tools rather than guessing an extension path.

Typical helper operations include Project Brain initialization/capture/freshness, repository Graph v3 refresh/query, parser health, graph-assisted Working Set ranking, symbol-aware impact, prioritized test mapping, **Slop Guard**, cache checks, health, and telemetry. When available, `project_brain.py ... capture --entries <json-or-file>` is the preferred deterministic path for storing a small batch of durable facts.

Do not run expensive helpers mechanically when the task is already obvious and local. Project Brain initialization/capture is different: it is lightweight state management and should happen when persistence is applicable.

## Working-set discipline

Prefer active task contract → relevant freshness-qualified Project Brain facts → task seed symbols/files → bounded structural/cross-language neighbors → exact candidate source regions → relevant prioritized tests/runtime evidence. Expand context only for a specific unresolved question that can materially change the decision. Avoid rereading unchanged files or repeating equivalent searches/tests merely for reassurance.

The graph helps choose what to read; source remains authoritative.

## Engineering doctrine

After understanding the real requirement, prefer: existing project solution → standard library → native platform/framework → existing dependency → local simple implementation → new abstraction/dependency.

Every changed hunk must trace to the requested task, a necessary dependency change, cleanup made obsolete specifically by that change, or verification. Do not perform opportunistic cleanup, modernization, formatting, or renaming. Use structural evidence to explain dependency/test surfaces where available, but do not let graph distance authorize unrelated work.

Minimal production code never means minimal tests. Verification follows behavior, failure modes, blast radius, and risk. Structurally related tests are candidates; confidence, actual source, and runtime/test evidence determine sufficiency.

## Anti-Slop Intelligence — v0.9

For normal source-changing work, run the task-aware **Slop Guard** near completion when `engine/slop_guard.py` is available. The goal is minimum justified engineering, not the smallest diff.

Default Guard Mode is changed-surface-first:

```text
actual task diff
→ changed symbols
→ bounded graph evidence
→ relevant source/tests
```

- Classify changed surfaces as `DIRECT`, `DEPENDENCY`, `CLEANUP`, or `TEST`. An internal `UNJUSTIFIED` surface must be justified with evidence or removed before completion.
- Focus on slop introduced or worsened by the current task; do not convert unrelated historical debt into an unrequested cleanup project.
- Prefer deterministic evidence, then Structural Graph v3 evidence, then evidence-backed reasoning for ambiguity.
- Treat Slop Risk as informational. Honor coverage/scoreability and never fabricate a score when the helper cannot inspect enough of the changed source.
- Resolve high-confidence blockers such as unjustified scope, duplicate implementation, unjustified dependency, or unjustified public API expansion before stopping.
- Run the **Underengineering Counter-Gate** before accepting simplification. Preserve required authentication/authorization, validation/sanitization, rate limiting, transactions/locking/idempotency, retry behavior, data-integrity checks, migration/compatibility paths, security checks, and tests.
- Only low-risk, high-confidence mechanical cleanup may be automatic. Abstraction/fallback/dependency/public-API/compatibility/test changes require review.
- If cleanup changes source, re-run affected and impact-mapped tests, inspect the new actual diff, and run Slop Guard again. High-impact simplification requires a logically separate review pass.

Typical portable invocation:

```sh
python engine/slop_guard.py --root . --json --write-state
```

Use `references/slop-policy.md` when a finding is ambiguous or cleanup could affect architecture/safety.

## Host reasoning

Codemium engineering depth is portable. Vendor model/thinking controls remain host-owned unless a documented per-task mechanism exists and the host confirms the effective setting. Never claim a reasoning setting changed without confirmation.

## Completion

Before stopping, classify Project Brain persistence as **captured**, **reused**, **none**, or **skipped by user constraint**. Revalidate any relevant `NEEDS_REVALIDATION` knowledge before materially relying on it. Then stop when requested behavior is satisfied, relevant verification passes, scope is clean, Slop Guard/justified-surface obligations are resolved, the Underengineering Counter-Gate is satisfied, architecture/security constraints are preserved, persistence/freshness obligations are satisfied, and no material unexplained uncertainty remains. Continue only when you can name the unresolved risk, unjustified surface, underengineering concern, or persistence obligation the next operation will reduce.
