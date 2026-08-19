# Codemium v0.9 Anti-Slop Benchmark

This benchmark evaluates whether Codemium v0.9 prevents **new unjustified engineering** without removing complexity required for correctness or safety.

The benchmark deliberately measures both error directions:

1. **missed slop** — unnecessary engineering introduced and not prevented;
2. **over-simplification** — necessary engineering incorrectly removed, blocked, or discouraged.

Correctness and safety are gating metrics. No Anti-Slop efficiency claim is valid when either regresses.

## Arms

Use the same repository state, ticket, host, model/reasoning configuration, tools, dependency state, timeout policy, evaluator, and acceptance criteria for every arm.

- `baseline` — coding agent without Codemium;
- `codemium_v08` — Codemium v0.8 behavior without Slop Guard;
- `codemium_v09_guard` — Codemium v0.9 with Justified Change Gate.

Optional ablation:

- `codemium_v09_deterministic` — deterministic/structural findings without reasoned adjudication;
- `codemium_v09_hybrid` — full deterministic + structural + reasoned adjudication.

Runs must be isolated so one arm cannot inherit conversation, filesystem, Project Brain, or tool state from another arm.

## Task classes

At minimum include:

### 1. Localized bug fix

A small behavior change with a naturally small implementation. Penalize unnecessary helpers, abstractions, configuration, dependencies, unrelated refactors, and debug residue.

### 2. Existing-capability reuse

The repository already contains a suitable helper or abstraction. Measure whether the agent reuses it or creates a duplicate implementation.

### 3. Feature implementation

A task that legitimately needs several changed surfaces. This prevents the benchmark from rewarding minimum LOC regardless of engineering need.

### 4. Security-sensitive change

Authentication/authorization/validation or another trust-boundary task. Slop Guard must not delete required defensive logic merely to simplify the diff.

### 5. Data-integrity / transaction change

A task requiring transaction, locking, idempotency, rollback, or integrity behavior. Necessary complexity must survive Anti-Slop review.

### 6. Compatibility task

A documented compatibility requirement where a shim/fallback is legitimate. This tests false-positive protection for compatibility code.

### 7. Legacy repository

The target file contains unrelated historical debt. Codemium should prevent new slop without turning the task into broad cleanup.

### 8. Cross-language task

A JavaScript/TypeScript/TSX change with graph-backed imported-symbol/dependent/test relationships. This exercises v0.8 Polyglot Intelligence as Anti-Slop evidence.

## Required per-run evidence

Record at minimum:

- `task_id`;
- `system` / arm;
- repository start commit;
- final diff or commit reference;
- quality/correctness result;
- safety result;
- tests/checks executed;
- regression findings;
- files changed;
- LOC changed;
- unrelated changed lines;
- new dependencies;
- new public API surfaces;
- duplicate implementations introduced;
- unnecessary abstractions introduced;
- Slop Guard findings by rule/severity/confidence;
- false-positive findings;
- necessary complexity incorrectly removed or blocked;
- Slop Guard wall-clock overhead;
- Slop Guard token overhead when observable;
- analysis coverage and scoreability.

## Primary outcome rules

A v0.9 run is not better merely because it changes fewer lines.

A successful Anti-Slop result must satisfy all of:

1. requested behavior passes;
2. safety/data-integrity floor is preserved;
3. no regression is introduced;
4. introduced unjustified engineering is lower than or equal to the comparison arm;
5. necessary complexity is not incorrectly removed;
6. task scope remains bounded.

## False-positive calibration

Blocking rules are high-precision gates. Before release, calibrate them using both positive and negative fixtures.

Positive examples should include:

- unrelated diff;
- duplicate implementation;
- unnecessary dependency;
- single-use forwarding helper;
- debug residue;
- type-system escape;
- speculative fallback;
- gratuitous abstraction.

Protection examples should include legitimate:

- authentication/authorization checks;
- validation/sanitization;
- transactions/locking/idempotency;
- retry behavior;
- migration/compatibility paths;
- public API contracts;
- test seams;
- multiple-implementation interfaces.

A false-positive blocker is considered more harmful than a missed cosmetic finding.

## Deterministic fixture

`plugins/codemium/tests/test_slop_guard.py` is the release-regression fixture for the engine. It proves:

- task-scope violations are detected;
- added debugger/type/comment signals are reported;
- package dependency deltas are detected;
- Graph v3 evidence can identify a duplicate implementation and single-use forwarder;
- strict mode fails on high-confidence blocking findings;
- protected-complexity removal triggers the Underengineering Counter-Gate;
- no risk score is fabricated when scoreable source coverage is insufficient.

This fixture validates engine mechanics. It is **not** a substitute for measured multi-arm coding-agent runs.

## Publication gate

Do not publish numeric performance/efficiency claims for v0.9 until representative multi-arm runs satisfy the fairness contract and the raw evidence is retained. If correctness or safety regresses, efficiency results are non-publishable regardless of LOC/token/time improvements.
