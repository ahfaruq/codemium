# Codemium Product Requirements Document

## Mission

Codemium is a persistent coding intelligence layer for Codex that makes an AI agent behave increasingly like an engineer who has worked on the same repository for months: it remembers durable architecture, retrieves only the project slice needed for the current task, changes only justified scope, tests according to risk, and avoids paying repeatedly for unchanged understanding.

## North-star outcome

As project complexity grows, durable project knowledge may grow, but active task context should remain bounded. Correctness, architecture consistency, security, testing adequacy, and scope integrity must remain at or above baseline before token/latency/LOC improvements count as wins.

## User interface

The primary invocation is deliberately short:

```text
@cm
```

Plain `@cm` means automatic task classification, automatic engineering depth, and a derived reasoning profile. Optional user overrides are:

```text
@cm fast
@cm deep
@cm critical
```

NORMAL is intentionally not required as a typed mode; it is the ordinary internal default selected by auto mode.

Focused task shortcuts:

```text
@cm-fix
@cm-test
@cm-review
@cm-audit
@cm-health
@cm-init
```

## Three-axis orchestration

Codemium separates three decisions that should not be conflated:

1. **Task** — what engineering work is being done.
2. **Depth** — how broadly/deeply the project must be investigated and verified.
3. **Reasoning profile** — how much model reasoning effort is preferred for the effective depth when the host supports it.

Task axis:

- BUILD
- FIX
- TEST
- REFACTOR
- REVIEW
- MIGRATION
- SECURITY

Depth axis:

- FAST — narrow, localized, low-risk work.
- NORMAL — default project-aware engineering.
- DEEP — complex, cross-boundary, distributed, concurrent, performance-sensitive, or uncertain work.
- CRITICAL — security/trust-boundary, auth, payments, migrations, secrets, production data, destructive operations, infrastructure/deployment, or breaking public interfaces.

Default reasoning profile:

- FAST → preferred `low`, minimum `low`.
- NORMAL → preferred `medium`, minimum `low`.
- DEEP → preferred `high`, minimum `medium`.
- CRITICAL → preferred `xhigh`, minimum `high`.

`max` is not an automatic CRITICAL default. It is reserved for the hardest quality-first workloads after benchmark evidence shows a material gain over `xhigh`.

## Host reasoning control

Codemium must never assume a skill can silently change the active Codex model/reasoning setting.

Requirements:

- derive and record preferred/minimum effort in the task contract;
- compare against current host effort when that value is known;
- request per-task effort only when the runtime exposes a safe confirmed mechanism;
- otherwise leave the host setting unchanged and apply depth through context/tool/verification policy;
- never silently rewrite global Codex configuration for a task-local preference;
- never claim the host effort changed until the runtime confirms the effective value.

Example:

```text
Host: GPT-5.6 Sol / xhigh
Request: @cm fast adjust card padding
```

Expected contract:

```text
Depth: FAST
Preferred reasoning: low
Host alignment: host_above_preferred
```

The task immediately uses FAST orchestration. The host reasoning effort changes only if the runtime supports and confirms the per-task request.

## Safety floor

A user override may increase depth but cannot reduce the minimum safe depth. A request such as `@cm fast` on authentication, payments, migrations, or other critical surfaces must automatically escalate. The reasoning profile follows the **effective** depth after escalation.

Example:

```text
@cm fast change authentication flow
```

must resolve to:

```text
Depth: CRITICAL
Preferred reasoning: xhigh
```

## Core systems

### Project Brain
Stores sanitized durable facts: project charter, architecture, decisions, constraints, interfaces, patterns, known bugs, model capability preferences, and reasoning profile policy. It is not a conversation transcript.

### Repository Intelligence
Builds deterministic maps of files, symbols, imports, and likely tests. Frontier reasoning should consume selected evidence, not crawl the repository blindly.

### Task Compiler
Transforms user intent into a task contract with task type, objective, scope, expected behavior, acceptance, risk, change policy, requested depth, effective depth, escalation reason, and reasoning profile.

### Working Set Engine
Ranks candidate files and durable knowledge for the task. Context expands only when material uncertainty identifies a specific missing fact.

### Engineering Policy
Uses the ladder: need → existing project solution → stdlib → native platform → existing dependency → local simple solution → new abstraction. The goal is minimum justified engineering, not minimum LOC.

### Scope Guard
Every changed file/hunk must trace to DIRECT, DEPENDENCY, CLEANUP caused by the change, or TEST. Unrelated formatting, modernization, refactoring, naming, comments, and dead-code cleanup are disallowed by default.

### Impact & Test Intelligence
Maps changes to callers, imported dependents, related tests, public surfaces, and risk. Testing depth follows behavior/risk; production minimalism never justifies under-testing.

### Reasoning Profile Engine
Maps effective depth to preferred/minimum effort, validates known model capability labels, and reports host alignment. It is advisory unless the host exposes confirmed per-task control.

### Efficiency Governor
Avoids equivalent reads/searches/tests on unchanged state; uses git/hash identity, bounded working sets, delta reinspection, explicit completion gates, and reasoning effort proportional to task depth when supported.

### Model Capability Layer
Core policies are model-independent. New model generations are promoted only after representative benchmarks meet the quality floor and improve useful efficiency. Model capability changes and reasoning labels must be verified before the registry is updated.

## Task lifecycle

User request → task/depth contract → reasoning profile → project state lookup → working set → investigation → root cause/design → implementation → diff inspection → impact analysis → depth/risk-based verification → scope guard → durable memory update → stop.

## Success metrics

- correctness and acceptance pass rate >= baseline;
- security and testing adequacy >= baseline;
- architecture consistency >= baseline;
- regression rate <= baseline;
- unrelated changed lines approaches zero;
- duplicate unchanged discovery <10% in MVP, <5% mature;
- active context grows slower than total project knowledge across long-running project benchmarks;
- reasoning profiles reduce unnecessary compute without lowering the quality floor;
- host-effort changes are never reported without runtime confirmation;
- token savings are reported only from actual host telemetry or clearly labeled proxies.

## Non-goals

Codemium is not a minimum-LOC contest, generic autonomous multi-agent framework, replacement for CI, or license to skip tests/security. FAST does not mean careless. CRITICAL does not mean loading the entire repository. A reasoning preference is not permission to rewrite global Codex configuration. Codemium does not bind permanently to one model generation.
