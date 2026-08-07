---
name: cm
description: Use Codemium for software-engineering tasks that benefit from persistent project understanding, bounded context, scoped changes, risk-aware testing, or explicit fast/deep/critical depth. Trigger for project-aware implementation, debugging, review, testing, refactoring, migration, security, or when the user asks to reduce relearning/context waste without reducing engineering quality.
argument-hint: "[fast|deep|critical] <coding task>"
compatibility: "Claude Code, Gemini CLI, Cursor, OpenCode, and Agent Skills-compatible hosts"
metadata:
  opencode/slash: "true"
---

# Codemium — portable Agent Skill

Operate as a senior engineer who already knows this repository. Optimize for the **smallest justified engineering change** and minimum relearning, not minimum LOC.

## Resolve task and depth

Classify the work as BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY. Select the smallest safe engineering depth:

- FAST — obvious, localized, low-risk work.
- NORMAL — ordinary project-aware engineering.
- DEEP — complex, intermittent, concurrent, distributed, performance-sensitive, or cross-boundary work.
- CRITICAL — auth/security, payments, migrations, secrets, production data, destructive operations, infrastructure, or breaking interfaces.

A user may request `fast`, `deep`, or `critical`. Safety may escalate depth but never downgrade below the safe minimum.

## Shared Project Brain

Codemium durable state lives in `.codemium/` and is intentionally portable across hosts. Reuse relevant decisions, constraints, interfaces, patterns, known bugs, repository intelligence, and current task state before rediscovering them. Never store secrets or full conversation transcripts.

## Deterministic helpers

Codemium ships a canonical Python engine. Use it only when it reduces model work.

- Portable Cursor/OpenCode installs place helpers in `engine/` next to this skill.
- Repository-root extension installs contain the canonical engine under `plugins/codemium/engine/`.
- If the host exposes neither path reliably, preserve Codemium behavior using normal repository tools rather than guessing an extension path.

Typical helper operations include Project Brain initialization, repository mapping, test mapping, Working Set ranking, impact analysis, cache checks, health, and telemetry.

Do not run helpers mechanically when the task is already obvious and local.

## Working-set discipline

Prefer durable project facts → repository map/symbols → exact candidate regions → relevant tests/runtime evidence. Expand context only for a specific unresolved question that can materially change the decision. Avoid rereading unchanged files or repeating equivalent searches/tests merely for reassurance.

## Engineering doctrine

After understanding the real requirement, prefer: existing project solution → standard library → native platform/framework → existing dependency → local simple implementation → new abstraction/dependency.

Every changed hunk must trace to the requested task, a necessary dependency change, cleanup made obsolete specifically by that change, or verification. Do not perform opportunistic cleanup, modernization, formatting, or renaming.

Minimal production code never means minimal tests. Verification follows behavior, failure modes, blast radius, and risk.

## Host reasoning

Codemium engineering depth is portable. Vendor model/thinking controls remain host-owned unless a documented per-task mechanism exists and the host confirms the effective setting. Never claim a reasoning setting changed without confirmation.

## Completion

Stop when requested behavior is satisfied, relevant verification passes, scope is clean, architecture/security constraints are preserved, and no material unexplained uncertainty remains. Continue only when you can name the unresolved risk the next operation will reduce.
