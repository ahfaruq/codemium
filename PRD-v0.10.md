# Codemium v0.10 — Execution Intelligence PRD

**Planned release:** v0.10.0  
**Theme:** Execution Intelligence  
**Core component:** Evidence Delta Gate  
**Runtime helper:** Execution Guard  
**Status:** Implementation branch  
**Date:** 2026-09-05

## 1. Release thesis

Codemium already answers two important engineering questions:

- v0.8 Polyglot Intelligence: **Where should the agent look?**
- v0.9 Anti-Slop Intelligence: **What actually needs to change?**

v0.10 adds the missing question:

> **What should the agent do next, and is that action worth doing?**

The goal is the **minimum justified investigation surface** without imposing arbitrary token, action, or time budgets.

Core law:

> **Every action must buy information or produce the solution.**

A useful action produces one of:

```text
NEW_EVIDENCE
NECESSARY_MUTATION
REQUIRED_VERIFICATION
```

Anything else is `NO_GAIN` and must not be repeated against unchanged evidence/repository state.

---

## 2. Problem

Modern coding agents can waste substantial reasoning and tool usage on simple defects even when the repository already contains enough information to resolve the task.

A common failure pattern is:

```text
runtime observation is ambiguous
→ agent forms a plausible hypothesis
→ agent edits before proving it
→ build/deploy
→ observation still appears wrong
→ agent repeats a similar edit/build/deploy cycle
→ later evidence shows the original code was already correct
```

This is not primarily code slop. The final diff may be tiny or even empty.

It is **execution slop**: unnecessary investigation, mutation, verification, build, deployment, or repeated observation that does not materially change the evidence state.

### Representative UI failure

Example:

```text
DOM says dropdown is open
accessibility state says menu is active
screenshot captured ~300 ms after click does not show it
agent assumes z-index defect
multiple build/deploy iterations follow
later screenshot after stabilization shows the dropdown correctly
```

The failure is not that z-index is complicated. The failure is that conflicting observations were treated as permission to mutate rather than as a signal to investigate render timing.

---

## 3. Goals

### G1 — Evidence before mutation

For debugging/review work, source-changing actions should normally follow concrete runtime/source evidence rather than untested intuition.

### G2 — Detect contradictory evidence

When material observations disagree about the same claim, Codemium should freeze mutation until the contradiction is resolved or explicitly overridden with a new material condition.

### G3 — Prevent zero-information loops

Equivalent inspections, searches, screenshots, builds, edits, deployments, or publications should not repeat when both evidence and repository state are unchanged.

### G4 — Track hypotheses explicitly

Material debugging hypotheses should have expected evidence and lifecycle state: `OPEN`, `CONFIRMED`, or `REJECTED`.

### G5 — Protect UI/runtime diagnosis from timing errors

A screenshot captured before a relevant render/animation/network boundary stabilizes must not outrank DOM/runtime truth.

### G6 — Measure waste without imposing arbitrary budgets

Expose useful/waste/blocked actions and investigation efficiency, but do not invent fixed token/action ceilings.

### G7 — Preserve existing Codemium quality guarantees

Execution Intelligence must compose with Project Brain, Structural Graph v3, Working Sets, Impact/Test Intelligence, Scope Guard, Slop Guard, and the Underengineering Counter-Gate.

---

## 4. Non-goals

v0.10 is not:

- a global token limiter;
- a fixed maximum number of tool calls;
- a replacement for model reasoning;
- a browser automation framework;
- a screenshot classifier;
- a CI build cache;
- a deployment orchestrator;
- permission to skip required verification;
- a claim that short investigations are always better;
- a reason to reduce engineering depth below the safety floor.

---

## 5. Product principles

Priority remains:

1. safety and data integrity;
2. correctness and requested behavior;
3. architecture/interface consistency;
4. adequate verification;
5. scope integrity;
6. execution/information efficiency;
7. simplicity and maintainability;
8. context/token/latency efficiency;
9. code volume.

Optimization that weakens a higher-ranked quality dimension is a failure.

---

## 6. Definition of execution slop

Within Codemium:

> **Execution slop is an investigation or action that neither creates material new evidence, performs a necessary mutation, nor supplies required verification.**

Conceptually:

```text
Useful Action = New Evidence OR Necessary Mutation OR Required Verification
Execution Slop = Action - Useful Action
```

This definition is task-relative. Re-running a test after source changes can be required verification. Re-running the exact same test against unchanged source/evidence merely for reassurance may be `NO_GAIN`.

---

## 7. Evidence model

Execution Intelligence distinguishes:

```text
OBSERVED
PROVEN
INFERRED
UNKNOWN
```

### OBSERVED

Direct source/runtime/tool evidence.

Examples:

- DOM attribute/state;
- computed style;
- bounding rectangle;
- source code;
- test output;
- database query result;
- structured API response.

### PROVEN

Sufficient compatible evidence for the task risk, or an authoritative source/runtime fact.

### INFERRED

A plausible explanation that has not yet been discriminated by evidence.

### UNKNOWN

A missing material fact.

Mutation for FIX/REVIEW work should normally be grounded in OBSERVED/PROVEN evidence.

---

## 8. Observation ledger

The deterministic Execution Guard stores observations under:

```text
.codemium/runtime/execution-intelligence.json
```

Observation shape:

```json
{
  "id": "O0001",
  "subject": "profile-dropdown",
  "claim": "open",
  "source": "dom",
  "value": "true",
  "normalized_value": true,
  "stabilized": null,
  "material": true
}
```

Only the latest observation for a `(subject, claim, source)` tuple participates in current contradiction/evidence fingerprinting. Historical observations remain in the ledger.

---

## 9. Contradiction Gate

If latest material observations for the same `(subject, claim)` disagree, the state is contradictory.

Example:

```text
subject = profile-dropdown
claim   = open

DOM         → true
screenshot  → false
```

Mutation is blocked until the contradiction is resolved or a substantive override records a new external condition.

Correct lifecycle:

```text
CONTRADICTION DETECTED
        ↓
FREEZE MUTATION
        ↓
identify discriminating observation
        ↓
collect runtime/source evidence
        ↓
contradiction resolved?
   ├── no → continue evidence gathering
   └── yes
        ↓
mutation still required?
   ├── no → stop
   └── yes → Mutation Gate
```

---

## 10. UI Stabilization Intelligence

For browser/UI tasks, screenshots are time-sensitive observations, not primary state truth.

Preferred order:

```text
interaction
→ DOM/application state
→ accessibility state when useful
→ relevant render/network/animation stabilization
→ computed style
→ geometry
→ screenshot
```

An unstabilized negative screenshot blocks UI mutation.

v0.10 does not mandate arbitrary sleep durations. Stabilization must correspond to a real asynchronous/render boundary.

Examples:

- transition/animation completion;
- awaited frame(s);
- network completion when state is network-driven;
- stable geometry;
- stable computed visibility/opacity/display.

---

## 11. Hypothesis Ledger

Hypothesis schema:

```json
{
  "id": "H001",
  "statement": "dropdown is behind an overlay",
  "expected_evidence": "computed stacking order places menu below overlay",
  "status": "OPEN",
  "evidence_ids": []
}
```

Statuses:

```text
OPEN
CONFIRMED
REJECTED
```

When a hypothesis becomes `REJECTED`, Execution Guard records the current evidence fingerprint.

The same rejected hypothesis cannot be retried against the same fingerprint.

New evidence can permit reconsideration.

---

## 12. Evidence Delta Gate

Execution Guard computes deterministic fingerprints for:

```text
current evidence snapshot
current repository state
```

Before repeat-sensitive actions, it computes an action signature from:

```text
action type
+ target
+ evidence fingerprint
+ repository-state fingerprint
```

Repeat-sensitive actions initially include:

```text
inspect
search
screenshot
build
deploy
publish
mutation
edit
```

If an equivalent action was already recorded with the same signature, the next equivalent action is blocked.

This directly targets loops such as:

```text
same evidence
+ same code
+ same deployment target
→ deploy again
```

---

## 13. Mutation Gate

Mutation actions include:

```text
edit
mutation
build
deploy
publish
migrate
```

The action can record one or more bases:

```text
task
evidence
architecture
dependency
verification
```

Mutation is blocked when:

- a material contradiction remains unresolved;
- a UI mutation depends on an unstabilized negative screenshot;
- FIX/REVIEW work has no concrete evidence/task/architecture basis;
- the same action/target is repeated with zero evidence/repository delta;
- the selected hypothesis was rejected and no new evidence appeared.

A missing explicit basis currently emits a warning rather than becoming a universal blocker, preserving compatibility while the policy is calibrated.

---

## 14. Action result classification

After a material action, record exactly one outcome:

```text
NEW_EVIDENCE
NECESSARY_MUTATION
REQUIRED_VERIFICATION
NO_GAIN
```

### NEW_EVIDENCE

The action materially changed what Codemium knows.

### NECESSARY_MUTATION

The action performed implementation required by the task/evidence/architecture.

### REQUIRED_VERIFICATION

The action supplied verification required by behavior/risk.

### NO_GAIN

The action changed neither knowledge nor solution state.

A `NO_GAIN` action combined with unchanged evidence is a strong stop/reconsider signal.

---

## 15. Waste telemetry

Status report includes:

```json
{
  "actions": 5,
  "useful_actions": 4,
  "waste_actions": 1,
  "blocked_actions": 2,
  "investigation_efficiency": 80.0,
  "stop_recommended": true
}
```

`investigation_efficiency` is descriptive:

```text
useful recorded actions / all recorded actions × 100
```

It is not a quality score and not a completion threshold.

---

## 16. No arbitrary execution budget

v0.10 explicitly rejects policies like:

```text
FAST = max 5 actions
NORMAL = max 15 actions
UI bug = max 10k tokens
```

The correct budget is evidence-driven.

A task may continue as long as the next operation can name a material uncertainty it is expected to reduce or a required solution/verification step it performs.

If the next operation cannot do that, stop or change strategy.

---

## 17. Integration with existing intelligence

### Project Brain

Execution observations are transient and must **not** be promoted wholesale to durable Project Brain memory.

Only durable source-backed decisions/constraints/interfaces/patterns/bugs follow the existing Project Brain capture rules.

### Structural Graph / Working Set

Graph/Working Set intelligence chooses where to inspect. Execution Intelligence decides whether another inspection/action has information value.

### Scope Guard

Scope Guard constrains changed surfaces after mutation. Execution Intelligence attempts to prevent unjustified mutation before it exists.

### Slop Guard

Slop Guard remains the changed-surface Justified Change Gate.

The relationship is:

```text
Execution Intelligence → justify actions before/during work
Slop Guard             → justify engineering surface near completion
```

### Underengineering Counter-Gate

Execution efficiency must never skip required security, data-integrity, compatibility, transaction, concurrency, migration, or test work.

---

## 18. v0.10 lifecycle

```text
PROJECT BRAIN
      ↓
TASK CONTRACT
      ↓
STRUCTURAL GRAPH / WORKING SET
      ↓
EXECUTION GUARD START
      ↓
OBSERVATION GATE
      ↓
CONTRADICTION?
  ├── yes → resolve before mutation
  └── no
      ↓
HYPOTHESIS + DISCRIMINATING TEST
      ↓
EVIDENCE DELTA GATE
      ↓
MUTATION REQUIRED?
  ├── no → VERIFY/STOP
  └── yes
      ↓
MUTATION GATE
      ↓
MINIMUM JUSTIFIED CHANGE
      ↓
VERIFY
      ↓
ACTUAL DIFF
      ↓
IMPACT / TEST INTELLIGENCE
      ↓
SLOP GUARD
      ↓
UNDERENGINEERING COUNTER-GATE
      ↓
PROJECT BRAIN CAPTURE
      ↓
DONE
```

---

## 19. CLI contract

Start against the current active task:

```sh
python plugins/codemium/engine/execution_guard.py --root . start
```

Record observations:

```sh
python plugins/codemium/engine/execution_guard.py --root . observe \
  --subject profile-dropdown \
  --claim open \
  --source dom \
  --value true
```

Record a UI screenshot:

```sh
python plugins/codemium/engine/execution_guard.py --root . observe \
  --subject profile-dropdown \
  --claim open \
  --source screenshot \
  --value false \
  --stabilized no
```

Create/update hypotheses:

```sh
python plugins/codemium/engine/execution_guard.py --root . hypothesis \
  --statement "dropdown is behind overlay" \
  --expected-evidence "computed stacking order is lower"
```

Gate a mutation:

```sh
python plugins/codemium/engine/execution_guard.py --root . gate \
  --action edit \
  --target src/menu.css \
  --mutation \
  --ui \
  --basis evidence
```

Record an action result:

```sh
python plugins/codemium/engine/execution_guard.py --root . record \
  --action inspect \
  --target profile-dropdown \
  --outcome new_evidence
```

Status:

```sh
python plugins/codemium/engine/execution_guard.py --root . status
```

Blocked gates return exit code `2`.

---

## 20. Override policy

A deterministic state snapshot cannot represent every external runtime transition.

A blocked gate may be overridden only with a substantive reason that describes a new material condition.

Good:

```text
remote preview cache was purged after previous deploy; runtime deployment state changed although repository state did not
```

Bad:

```text
try again
```

Overrides remain visible in the gate ledger.

---

## 21. Acceptance criteria

v0.10 core is acceptable when all are true:

1. Execution Guard persists deterministic task-scoped execution state.
2. Contradictory material observations block mutation.
3. Unstabilized negative UI screenshot evidence blocks UI mutation.
4. Rejected hypotheses cannot be retried against unchanged evidence.
5. New evidence permits reconsideration.
6. Equivalent repeat-sensitive actions are blocked when evidence and repository state are unchanged.
7. Build/deploy repeats can be detected using the same mechanism.
8. Action outcomes expose useful/waste telemetry.
9. Existing Anti-Slop and Underengineering behavior remains intact.
10. No arbitrary token/action budget is introduced.
11. Portable hosts receive the same Execution Guard through the existing engine copy mechanism.
12. A regression fixture covers the dropdown/z-index timing failure pattern.

---

## 22. Future work

Deferred beyond the initial v0.10 implementation:

- automatic browser adapter ingestion of DOM/a11y/computed-style observations;
- CI/dashboard visualization of execution waste;
- cross-task aggregate execution telemetry;
- learned calibration of high-value next-observation selection;
- native host interception of build/deploy commands before execution;
- richer runtime-state fingerprints for remote deployments;
- token/cost telemetry when hosts expose trustworthy per-task measurements.

These must remain evidence-gated and privacy-safe.

---

## 23. Release statement

v0.10 extends Codemium from controlling **context and changed code** to controlling the **engineering process itself**.

The intended behavior is simple:

> **Investigate while the investigation is learning. Mutate only when the evidence requires it. Stop when the next action cannot buy new information or complete required work.**