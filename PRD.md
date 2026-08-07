# Codemium Product Requirements Document

## Mission

Codemium is a persistent coding intelligence layer for Codex that makes an AI agent behave increasingly like an engineer who has worked on the same repository for months: it remembers durable architecture, retrieves only the project slice needed for the current task, changes only justified scope, tests according to risk, and avoids paying repeatedly for unchanged understanding.

## North-star outcome

As project complexity grows, durable project knowledge may grow, but active task context should remain bounded. Correctness, architecture consistency, security, testing adequacy, and scope integrity must remain at or above baseline before token/latency/LOC improvements count as wins.

## Product positioning

Codemium is an independent coding-intelligence product and a direct benchmark competitor to other coding-efficiency approaches.

Its primary competitive benchmark compares:

```text
baseline
vs
caveman
vs
ponytail
vs
codemium
```

Ponytail may inform market comparison, but Codemium must never be positioned as a Ponytail extension, mode, or derivative in product copy.

## User interface

Primary invocation:

```text
@cm
```

Plain `@cm` means automatic task classification, automatic engineering depth, and a derived reasoning profile.

Optional overrides:

```text
@cm fast
@cm deep
@cm critical
```

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

Codemium separates:

1. **Task** — what engineering work is being done.
2. **Depth** — how broadly/deeply the project must be investigated and verified.
3. **Reasoning profile** — how much model reasoning effort is preferred when the host supports it.

Task axis: BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, SECURITY.

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

Codemium derives and records preferred/minimum effort, compares it with known host effort, requests per-task effort only when the runtime exposes a safe confirmed mechanism, otherwise leaves host settings unchanged, never silently rewrites global Codex configuration, and never claims a host-effort change until runtime confirmation.

## Safety floor

A user override may increase depth but cannot reduce the minimum safe depth. `@cm fast` on authentication, payments, migrations, or other critical surfaces must automatically escalate, and the reasoning profile follows the effective depth.

## Core systems

### Project Brain

Stores sanitized durable facts: project charter, architecture, decisions, constraints, interfaces, patterns, known bugs, model capability preferences, and reasoning profile policy. It is not a conversation transcript.

### Repository Intelligence

Builds deterministic maps of files, symbols, imports, and likely tests. Frontier reasoning consumes selected evidence instead of crawling the repository blindly.

### Task Compiler

Transforms user intent into a task contract with task type, objective, scope, expected behavior, acceptance, risk, change policy, requested depth, effective depth, escalation reason, and reasoning profile.

### Working Set Engine

Ranks candidate files and durable knowledge for the task. Context expands only when material uncertainty identifies a specific missing fact.

### Engineering Policy

Uses the ladder:

```text
need
→ existing project solution
→ stdlib
→ native platform
→ existing dependency
→ local simple solution
→ new abstraction
```

The goal is minimum justified engineering, not minimum LOC.

### Scope Guard

Every changed file/hunk must trace to DIRECT, DEPENDENCY, CLEANUP caused by the change, or TEST. Unrelated formatting, modernization, refactoring, naming, comments, and dead-code cleanup are disallowed by default.

### Impact & Test Intelligence

Maps changes to callers, imported dependents, related tests, public surfaces, and risk. Testing depth follows behavior/risk; production minimalism never justifies under-testing.

### Reasoning Profile Engine

Maps effective depth to preferred/minimum effort, validates known model capability labels, and reports host alignment. It is advisory unless the host exposes confirmed per-task control.

### Efficiency Governor

Avoids equivalent reads/searches/tests on unchanged state; uses git/hash identity, bounded working sets, delta reinspection, explicit completion gates, and reasoning effort proportional to task depth when supported.

### Model Capability Layer

Core policies are model-independent. New model generations are promoted only after representative benchmarks meet the quality floor and improve useful efficiency.

## Competitive Benchmark Evidence System

Numbers exists to determine how Codemium performs against alternatives under controlled conditions.

### Required primary arms

A publishable competitive study must contain:

- `baseline` — no optimization skill;
- `caveman` — terse-prose/minimal-control arm;
- `ponytail` — Ponytail;
- `codemium` — Codemium `@cm`.

Codemium-specific depth/reasoning variants are ablations and do not replace the competitor arms.

### Fairness requirements

Every primary arm must use:

- identical task/ticket text;
- identical starting repository commit or fixture;
- identical coding-agent host;
- identical base model and reasoning configuration unless the study explicitly tests reasoning policy;
- identical tools/network/environment/timeout/dependency state;
- isolated fresh runs;
- identical scoring criteria.

Repeated runs are required for credible agentic results; `n >= 4` per arm is recommended.

### Metrics

Lower is better:

- LOC changed;
- total tokens;
- measured cost;
- wall-clock time.

Higher is better:

- quality pass rate;
- safety pass rate.

Diagnostic metrics include tool calls, unique/duplicate reads, unrelated changed lines, tests executed, regressions, and context/cache reuse.

### Quality gate

Resource efficiency is only a win after correctness and safety meet the quality floor.

```text
quality >= comparison floor
safety  >= comparison floor
regressions <= controls
```

### Publication gate

Public competitive results require:

- `meta.kind = measured`;
- all four required arms;
- identical task IDs across all four arms;
- quality and safety values on every competitive run;
- real host token telemetry;
- real cost/billing telemetry when cost is published;
- raw run records retained for auditability.

Synthetic/demo data must be visibly watermarked and cannot pass `--publish`.

### Stable visual identity

The main Numbers chart uses:

- baseline — gray;
- caveman — orange;
- ponytail — green;
- codemium — purple.

This is a comparison visualization, not a statement of lineage.

## Task lifecycle

```text
user request
→ task/depth contract
→ reasoning profile
→ project state lookup
→ working set
→ investigation
→ root cause/design
→ implementation
→ diff inspection
→ impact analysis
→ depth/risk-based verification
→ scope guard
→ durable memory update
→ stop
```

## Success metrics

- correctness and acceptance pass rate >= baseline;
- security and testing adequacy >= baseline;
- architecture consistency >= baseline;
- regression rate <= baseline;
- unrelated changed lines approaches zero;
- duplicate unchanged discovery <10% in MVP, <5% mature;
- active context grows slower than total project knowledge;
- reasoning profiles reduce unnecessary compute without lowering quality;
- host-effort changes are never reported without runtime confirmation;
- benchmark dashboards never present synthetic data as measured performance.

## Non-goals

Codemium is not a minimum-LOC contest, a generic autonomous multi-agent framework, a replacement for CI, or a license to skip tests/security. FAST does not mean careless. CRITICAL does not mean loading the entire repository. A reasoning preference is not permission to rewrite global Codex configuration. A synthetic dashboard is not a performance claim. Competitor references in Numbers exist for controlled comparison, not product identity.
