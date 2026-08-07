# Codemium Product Requirements Document

**Version:** 0.5 architecture revision  
**Product:** Host-agnostic persistent coding intelligence for AI coding agents

## Mission

Codemium makes an AI coding agent behave increasingly like an engineer who has worked on the same repository for months: it remembers durable architecture, retrieves only the project slice required for the current task, changes only justified scope, tests according to risk, and avoids paying repeatedly for unchanged understanding.

Codemium is **not a Codex-only product**. Codex is the reference/stable adapter. Claude Code and Gemini CLI are beta adapters. Future hosts must implement the same Codemium contract rather than fork the product logic.

## North-star outcome

As project complexity grows, durable project knowledge may grow, but active task context should remain bounded. Correctness, architecture consistency, security, testing adequacy, and scope integrity must remain at or above baseline before token/latency/LOC improvements count as wins.

## Product positioning

Codemium is an independent coding-intelligence product. Vendor models and coding-agent hosts are execution environments, not product identity.

The product must remain portable across model generations and coding-agent hosts whenever the host provides sufficient repository/tool access.

## Host architecture

```text
                         CODEMIUM CORE
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
  Project Brain        Engineering Policy      Shared State
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
       Codex Adapter     Claude Adapter    Gemini Adapter
            │                 │                 │
           @cm          /codemium:cm            /cm
```

### Current host status

- OpenAI Codex — stable/reference adapter.
- Claude Code — beta native plugin + Agent Skill + slash command.
- Gemini CLI — beta native extension + context file + custom command.
- Cursor — planned after its current official extension surface is evaluated.
- OpenCode — planned after its current official extension surface is evaluated.

## Adapter contract

Every host adapter must preserve:

1. Task classification: BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, SECURITY.
2. Engineering depth: FAST, NORMAL, DEEP, CRITICAL.
3. Safety floor: explicit user depth may escalate but never force unsafe shallowness.
4. Persistent `.codemium/` project state where workspace access permits it.
5. Bounded working sets and targeted context expansion.
6. Smallest justified engineering change, not minimum LOC.
7. No opportunistic or unrelated edits.
8. Testing and verification based on behavior, blast radius, and risk.
9. Reuse of unchanged deterministic evidence where validity can be proven.
10. Explicit completion and stop conditions.
11. No claim that host/model reasoning changed unless the host confirms it.

Host-specific syntax, model selectors, thinking controls, permissions, hooks, and extension formats belong in adapters, not in core product doctrine.

## User interface

### Codex

```text
@cm
@cm fast
@cm deep
@cm critical
```

Focused Codex skills may include `@cm-fix`, `@cm-test`, `@cm-review`, `@cm-audit`, `@cm-health`, and `@cm-init`.

### Claude Code

The installed `cm` Agent Skill may trigger naturally. Explicit command:

```text
/codemium:cm <task>
/codemium:cm fast <task>
/codemium:cm deep <task>
/codemium:cm critical <task>
```

### Gemini CLI

```text
/cm <task>
/cm fast <task>
/cm deep <task>
/cm critical <task>
```

The user experience should stay as short as each host natively allows.

## Task/depth model

Task axis: BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, SECURITY.

Depth axis:

- FAST — narrow, localized, low-risk work.
- NORMAL — ordinary project-aware engineering.
- DEEP — complex, cross-boundary, distributed, concurrent, performance-sensitive, intermittent, or uncertain work.
- CRITICAL — security/trust boundaries, auth, payments, migrations, secrets, production data, destructive operations, infrastructure/deployment, or breaking public interfaces.

Depth is portable. Vendor reasoning controls are not.

## Host reasoning policy

Codemium core expresses engineering depth and a generic need for more or less reasoning. An adapter may map that need to host-specific controls only when the control is documented, safe, and confirmable.

### Codex reference mapping

Current Codex adapter preference when supported:

- FAST → `low`
- NORMAL → `medium`
- DEEP → `high`
- CRITICAL → `xhigh`

This mapping is advisory unless runtime confirmation proves the effective value changed.

### Claude Code and Gemini CLI

Beta adapters currently apply depth through context breadth, investigation rigor, impact analysis, and verification policy. They do not claim to mutate vendor thinking/model settings.

## Core systems

### Project Brain

Stores sanitized durable facts: project charter, architecture, decisions, constraints, interfaces, patterns, and known bugs. It is not a conversation transcript.

### Repository Intelligence

Builds deterministic maps of files, symbols, imports, dependencies, and likely tests. Frontier reasoning consumes selected evidence instead of crawling the repository blindly.

### Task Compiler

Transforms user intent into a task contract with task type, objective, scope, expected behavior, acceptance criteria, risk, requested depth, effective depth, and escalation reason.

### Working Set Engine

Ranks candidate files and durable knowledge for the task. Context expands only when material uncertainty identifies a specific missing fact.

### Engineering Policy

Use the following solution ladder after understanding the actual requirement:

```text
need
→ existing project solution
→ standard library
→ native platform/framework
→ existing dependency
→ local simple implementation
→ new abstraction/dependency
```

### Scope Guard

Every changed file/hunk must trace to DIRECT task work, a required DEPENDENCY change, CLEANUP made obsolete specifically by the change, or TEST/verification work. Unrelated modernization and cleanup are disallowed by default.

### Impact & Test Intelligence

Map changes to callers, imported dependents, related tests, public surfaces, and risk. Minimal production code never justifies under-testing.

### Efficiency Governor

Avoid equivalent reads/searches/tests on unchanged state; use git/hash identity, bounded working sets, delta reinspection, deterministic reuse, and explicit completion gates.

### Model Capability Layer

Core policies are model-independent. Model generations and host-specific reasoning knobs may be promoted only after representative benchmarks preserve the quality floor.

## Shared project state

All adapters use the same durable project namespace:

```text
.codemium/
```

A project initialized under one host should remain understandable to another supported adapter. Durable state must not contain vendor-specific transient conversation data unless explicitly namespaced as non-portable runtime state.

## Task lifecycle

```text
user request
→ host adapter
→ task/depth contract
→ project state lookup
→ bounded working set
→ investigation
→ root cause/design
→ implementation
→ diff inspection
→ impact analysis
→ risk-based verification
→ scope guard
→ durable memory update
→ stop
```

## Benchmark system

Competitive benchmark infrastructure remains internal/hidden from the public README until measured results are ready. A publishable study must use controlled, identical task/repository/model/environment conditions and pass correctness/safety quality gates before efficiency claims count as wins.

Synthetic data must never be presented as product performance.

## Success metrics

- correctness and acceptance pass rate >= baseline;
- security and testing adequacy >= baseline;
- architecture consistency >= baseline;
- regression rate <= baseline;
- unrelated changed lines approaches zero;
- duplicate unchanged discovery <10% in MVP, <5% mature;
- active context grows materially slower than total project knowledge;
- cross-host `.codemium/` durable state remains compatible;
- host/model changes are never claimed without confirmation;
- no adapter silently diverges from the core engineering contract.

## Non-goals

Codemium is not a minimum-LOC contest, generic autonomous multi-agent framework, replacement for CI, or license to skip tests/security. It is not permanently tied to Codex, Claude, Gemini, or one model family. FAST does not mean careless. CRITICAL does not mean loading the entire repository.
