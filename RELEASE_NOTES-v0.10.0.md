# Codemium v0.10.0 — Execution Intelligence

Codemium v0.10.0 adds **Execution Intelligence**: a task-aware control layer for deciding whether the agent's *next action* is worth doing.

The release keeps the existing foundations intact:

- v0.8 **Polyglot Intelligence** answers: **Where should the agent look?**
- v0.9 **Anti-Slop Intelligence** answers: **What actually needs to change?**
- v0.10 **Execution Intelligence** adds: **What should the agent do next, and will that action produce useful information or the solution?**

The core law is:

> **Every action must buy information or produce the solution.**

## Why this release exists

Coding agents can waste large amounts of context, model usage, time, builds, deployments, and browser interaction on loops that do not materially change what is known.

A representative UI failure mode is:

```text
DOM says dropdown is open
→ screenshot is captured before UI stabilizes
→ dropdown is not visible yet
→ agent assumes z-index is wrong
→ code change
→ build/deploy
→ another early observation
→ another change
```

The underlying problem is not necessarily code complexity. It is **investigation waste**: the agent mutates before resolving contradictory evidence and repeats actions without meaningful evidence gain.

v0.10 introduces deterministic execution state and gates specifically for this class of failure.

## Execution Guard

The new canonical helper is:

```sh
python plugins/codemium/engine/execution_guard.py --root . status
```

Execution Guard maintains task-scoped transient ledgers for:

- observations;
- hypotheses;
- actions;
- gate decisions;
- execution-waste telemetry.

Transient execution state belongs under `.codemium/runtime/` and is not Project Brain knowledge.

## Contradiction Gate

Materially conflicting observations block mutation until the contradiction is resolved or explicitly superseded by stronger evidence.

Examples:

- DOM/accessibility state says a menu is open while an unstabilized screenshot appears closed;
- source/config evidence says a value is enabled while a stale runtime probe appears disabled;
- two authoritative runtime probes disagree about the same behavior.

The correct next action is evidence collection or stabilization, not speculative code mutation.

## UI Stabilization Intelligence

For UI/runtime investigations, negative screenshots are not automatically authoritative.

When stronger state evidence indicates the UI transition has started, Codemium should stabilize the observation before treating absence on screen as proof of a CSS/layout defect.

Typical evidence order:

```text
interaction
→ DOM/accessibility state
→ render/animation/network stabilization
→ computed style / geometry / visibility
→ screenshot
```

This directly protects against premature `z-index`, visibility, layout, or animation changes based on an early screenshot.

## Hypothesis Ledger

Hypotheses are explicit execution state rather than invisible repeated guesses.

A hypothesis records its expected evidence and status, such as:

```text
H1: dropdown is hidden behind an overlay
expected evidence: computed stacking order places it below the overlay
result: rejected
```

Once rejected, the same hypothesis must not be retried against unchanged evidence unless new information materially reopens it.

## Evidence Delta Gate

Repeat-sensitive actions are fingerprinted against the relevant evidence and repository state.

When an equivalent action has already been performed and the evidence/repository state is unchanged, Execution Guard blocks the repeat instead of allowing another no-gain loop.

This applies to actions such as:

- repeated browser probes;
- repeated searches/reads with equivalent scope;
- repeated builds;
- repeated deployments;
- repeated hypothesis tests;
- repeated verification that adds no new confidence or required coverage.

There is intentionally **no arbitrary token, action, or time budget**. A difficult bug may require deep investigation. The stopping signal is lack of information gain, not an invented quota.

## Action outcomes

Execution Intelligence classifies performed work into useful outcomes:

```text
NEW_EVIDENCE
NECESSARY_MUTATION
REQUIRED_VERIFICATION
NO_GAIN
```

`NO_GAIN` becomes explicit telemetry rather than silently consuming more model/tool usage.

## Task compiler integration

Task compilation now emits an `execution_policy` describing execution-sensitive behavior, including UI/runtime stabilization where applicable.

Execution Intelligence sits **before mutation** in the normal lifecycle; v0.9 Slop Guard still evaluates the actual diff near completion.

The combined lifecycle is conceptually:

```text
PROJECT BRAIN
→ TASK CONTRACT
→ STRUCTURAL GRAPH / WORKING SET
→ OBSERVE
→ HYPOTHESIS
→ CONTRADICTION + EVIDENCE DELTA GATES
→ MUTATE ONLY WHEN JUSTIFIED
→ VERIFY
→ SLOP GUARD
→ UNDERENGINEERING COUNTER-GATE
→ PERSIST DURABLE KNOWLEDGE
→ DONE
```

## Regression coverage

v0.10 adds a dedicated execution regression fixture covering the dropdown/z-index timing failure:

- DOM reports the dropdown open;
- an early screenshot reports it not visible;
- the contradiction blocks mutation;
- stabilized evidence resolves the conflict;
- a rejected z-index hypothesis cannot be retried without new evidence;
- equivalent repeated build/deploy/probe actions are stopped when the evidence delta is zero.

Core verification now requires the Execution Guard contract and fixture in addition to the existing Project Brain, Polyglot Intelligence, Slop Guard, provenance, calibration, and Underengineering gates.

## Telemetry

Codemium telemetry now exposes execution-oriented signals such as useful actions, blocked repeats, no-gain work, and investigation efficiency proxies without pretending they are host/model token accounting.

No numeric competitive efficiency claim is published for v0.10 from deterministic fixtures alone. Representative measured agent runs remain required before publishing token/cost/time improvement claims.

## Compatibility and safety

v0.10 preserves:

- Project Brain persistence and freshness qualification;
- Structural Graph v3 and cross-language JavaScript/TypeScript/TSX intelligence;
- symbol-aware impact and prioritized test intelligence;
- v0.9 Slop Guard and evidence-backed adjudication;
- the Underengineering Counter-Gate;
- source/runtime/test authority over derived intelligence;
- Codex lifecycle persistence hooks;
- Claude Code, Gemini CLI, Cursor, and OpenCode adapters.

Execution Intelligence does **not** weaken required verification, security review, data-integrity protections, compatibility checks, or high-risk engineering depth.

## Upgrade note

After the GitHub marketplace/plugin source is refreshed, start a new Codex session if plugin inventory is cached. The Codex plugin detail page should report **v0.10.0** and describe Execution Intelligence once the updated marketplace snapshot is loaded.
