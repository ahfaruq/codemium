# Codemium v0.10 — Execution Intelligence policy

Execution Intelligence controls **how Codemium investigates and acts before the diff exists**.

Anti-Slop Intelligence asks whether changed engineering surface is justified. Execution Intelligence asks whether the investigation itself is justified.

Core law:

> **Every action must buy information or produce the solution.**

A useful action must produce one of:

```text
NEW_EVIDENCE
NECESSARY_MUTATION
REQUIRED_VERIFICATION
```

Anything else is `NO_GAIN` and must not be repeated against the same evidence/repository state.

## 1. Evidence before mutation

For FIX and REVIEW work, do not edit merely because a hypothesis sounds plausible.

Before mutation, distinguish:

```text
OBSERVED   directly measured from source/runtime/tool output
PROVEN     multiple compatible observations or authoritative source/runtime fact
INFERRED   reasonable explanation not yet proven
UNKNOWN    missing fact
```

A source-changing fix should normally have an `OBSERVED` or `PROVEN` basis. An explicit BUILD request can itself justify planned implementation, but implementation still follows repository architecture and scope rules.

## 2. Contradiction Gate

When two material observations disagree about the same claim, the contradiction is a diagnostic event, not permission to edit.

Example:

```text
DOM: dropdown open = true
Accessibility tree: menu active = true
Screenshot at 300 ms: dropdown visible = false
```

Correct response:

```text
CONTRADICTION
→ freeze mutation
→ inspect runtime timing / computed style / geometry / animation
→ obtain a stabilized observation
→ resolve contradiction
→ mutate only if evidence still proves a source defect
```

Do not choose the most visually convincing observation by intuition.

## 3. UI runtime truth order

For UI/browser bugs, screenshots are useful evidence but are often time-sensitive. Prefer a multi-signal runtime check:

```text
interaction
→ DOM/state
→ accessibility state when useful
→ render/network/animation stabilization
→ computed style
→ geometry / bounding rectangle
→ screenshot
```

A negative screenshot captured before stabilization must not by itself justify CSS/DOM mutation.

Typical stabilization evidence can include:

- animation/transition completion;
- awaited render frame(s);
- network idle when network changes the target state;
- stable bounding rectangle;
- stable computed visibility/opacity/display;
- repeated state observation after a justified wait.

Do not add arbitrary sleeps everywhere. Wait only when the runtime has a real asynchronous/render boundary.

## 4. Hypothesis Ledger

Material debugging hypotheses should have:

```text
id
statement
expected evidence
status: OPEN | CONFIRMED | REJECTED
evidence ids
```

A rejected hypothesis cannot be retried against the same evidence fingerprint.

It may be revisited only when new evidence materially changes the case.

Bad:

```text
H1 z-index problem → rejected
edit z-index anyway
build
screenshot
edit z-index again
```

Good:

```text
H1 z-index problem
expected: computed stacking order places menu below overlay
inspect computed styles
result: false
H1 = REJECTED
stop touching z-index unless new evidence appears
```

## 5. Evidence Delta Gate

Codemium tracks a deterministic evidence fingerprint and repository-state fingerprint.

Before repeating an inspection, search, screenshot, build, edit, deployment, or publication action, ask:

```text
What changed since the equivalent previous action?
```

If both are unchanged:

```text
Δ evidence = 0
Δ repository state = 0
```

then an equivalent repeat is blocked.

The correct next move is to change the question, obtain a new signal, or stop.

## 6. Mutation Gate

Before mutation, record the basis:

```text
task
 evidence
architecture
dependency
verification
```

For FIX/REVIEW, evidence-first is the default. For BUILD, the explicit task can justify implementation, but speculative unrelated mutation remains forbidden.

Mutation is blocked when:

- a material evidence contradiction remains unresolved;
- a UI mutation relies on an unstabilized negative screenshot;
- a FIX/REVIEW has no concrete evidence/task/architecture basis;
- the same mutation is being repeated with no evidence or repository-state delta;
- the action depends on a rejected hypothesis and no new evidence appeared.

## 7. Build/deploy discipline

Build and deployment are not debugging probes by default.

A build is justified when source/config/dependency state changed or when a required verification specifically needs a new build.

A deployment is justified when deployment is required to expose or verify behavior that cannot be proven locally/currently.

Never use:

```text
change guess
→ build
→ deploy
→ screenshot
→ repeat
```

as a substitute for root-cause evidence.

Repeated build/deploy with the same evidence and repository-state fingerprint is blocked unless a substantive runtime condition explains why the deterministic state is incomplete. Overrides stay visible in the ledger.

## 8. Action outcomes and waste telemetry

After material actions, classify the result:

```text
NEW_EVIDENCE          investigation produced a new material fact
NECESSARY_MUTATION    required implementation was performed
REQUIRED_VERIFICATION verification needed for correctness/risk was performed
NO_GAIN               action changed neither knowledge nor solution state
```

Execution Intelligence reports:

- action count;
- useful actions;
- waste actions;
- blocked actions;
- hypothesis states;
- unresolved contradictions;
- investigation efficiency.

The efficiency number is descriptive telemetry, not a token quota or engineering-depth limit.

## 9. No arbitrary token/action budget

Do not define rules such as:

```text
FAST may use 5 actions
UI bugs may use 10k tokens
DEEP may use 50k tokens
```

Some one-line defects require deep investigation. Some large tasks are obvious.

The stopping signal is **information gain**, not a fixed budget.

Continue while the next operation can name the material uncertainty it will reduce. Stop or change strategy when it cannot.

## 10. Stop conditions

Stop investigation when all are true:

- requested behavior/root cause is sufficiently proven for the task risk;
- no unresolved material contradiction remains;
- the next repeated action would have zero evidence delta;
- no open hypothesis can name a concrete discriminating test;
- mutation is unnecessary, or the required mutation is already complete;
- required verification is complete.

`NO_GAIN` followed by unchanged evidence is a strong stop/reconsider signal.

## 11. Overrides

The deterministic guard supports a substantive override reason because not every external runtime condition is representable in `.codemium` state.

Overrides must describe a **new condition**, not merely disagreement with the gate.

Acceptable example:

```text
remote preview cache was purged after the previous deploy; repository state is unchanged but runtime deployment state materially changed
```

Bad example:

```text
try again
```

Overrides remain visible as warnings and should be rare.

## 12. Deterministic helper

From a repository-root Codemium install:

```sh
python plugins/codemium/engine/execution_guard.py --root . start
python plugins/codemium/engine/execution_guard.py --root . observe --subject menu --claim open --source dom --value true
python plugins/codemium/engine/execution_guard.py --root . hypothesis --statement "stacking context hides menu" --expected-evidence "computed stacking order is lower"
python plugins/codemium/engine/execution_guard.py --root . gate --action edit --target src/menu.css --mutation --ui --basis evidence
python plugins/codemium/engine/execution_guard.py --root . record --action inspect --target menu --outcome new_evidence
python plugins/codemium/engine/execution_guard.py --root . status
```

Portable installs use `engine/execution_guard.py` next to the skill.

The helper strengthens deterministic bookkeeping. Source/runtime facts remain authoritative.