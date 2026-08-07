# Codemium Product Requirements Document

## Mission

Codemium is a persistent coding intelligence layer for Codex that makes an AI agent behave increasingly like an engineer who has worked on the same repository for months: it remembers durable architecture, retrieves only the project slice needed for the current task, changes only justified scope, tests according to risk, and avoids paying repeatedly for unchanged understanding.

## North-star outcome

As project complexity grows, durable project knowledge may grow, but active task context should remain bounded. Correctness, architecture consistency, security, testing adequacy, and scope integrity must remain at or above baseline before token/latency/LOC improvements count as wins.

## Core systems

### Project Brain
Stores sanitized durable facts: project charter, architecture, decisions, constraints, interfaces, patterns, and known bugs. It is not a conversation transcript.

### Repository Intelligence
Builds deterministic maps of files, symbols, imports, and likely tests. Frontier reasoning should consume selected evidence, not crawl the repository blindly.

### Task Compiler
Transforms user intent into BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY task contracts with objective, scope, expected behavior, acceptance, risk, and change policy.

### Working Set Engine
Ranks candidate files and durable knowledge for the task. Context expands only when material uncertainty identifies a specific missing fact.

### Engineering Policy
Uses the ladder: need → existing project solution → stdlib → native platform → existing dependency → local simple solution → new abstraction. The goal is minimum justified engineering, not minimum LOC.

### Scope Guard
Every changed file/hunk must trace to DIRECT, DEPENDENCY, CLEANUP caused by the change, or TEST. Unrelated formatting, modernization, refactoring, naming, comments, and dead-code cleanup are disallowed by default.

### Impact & Test Intelligence
Maps changes to callers, imported dependents, related tests, public surfaces, and risk. Testing depth follows behavior/risk; production minimalism never justifies under-testing.

### Efficiency Governor
Avoids equivalent reads/searches/tests on unchanged state; uses git/hash identity, bounded working sets, delta reinspection, and explicit completion gates.

### Model Capability Layer
Core policies are model-independent. New model generations are promoted only after representative benchmarks meet the quality floor and improve useful efficiency.

## Task lifecycle

User request → task contract → project state lookup → working set → investigation → root cause/design → implementation → diff inspection → impact analysis → risk-based verification → scope guard → durable memory update → stop.

## Success metrics

- correctness and acceptance pass rate >= baseline;
- security and testing adequacy >= baseline;
- architecture consistency >= baseline;
- regression rate <= baseline;
- unrelated changed lines approaches zero;
- duplicate unchanged discovery <10% in MVP, <5% mature;
- active context grows slower than total project knowledge across long-running project benchmarks;
- token savings are reported only from actual host telemetry or clearly labeled proxies.

## MVP scope

Project Brain, repository map, task compiler, working set, task modes, scope guard, impact mapping, test mapping, read/search cache, stop doctrine, health/telemetry, plugin packaging, verification tests.

## Non-goals

Codemium is not a minimum-LOC contest, generic autonomous multi-agent framework, full AST language server, replacement for CI, or license to skip tests/security. It does not automatically refactor unrelated code and does not bind permanently to one model generation.
