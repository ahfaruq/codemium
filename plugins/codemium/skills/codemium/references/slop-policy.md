# Anti-Slop / Justified Change Policy

Codemium optimizes for the **minimum justified engineering surface**, not minimum LOC, files, abstractions, or dependencies.

## Core rule

Every changed surface must be defensible as one of:

- `DIRECT` — implements requested behavior;
- `DEPENDENCY` — required for a direct change to work safely;
- `CLEANUP` — code made obsolete by this exact change;
- `TEST` — evidence for changed behavior.

`UNJUSTIFIED` is an internal Slop Guard state, never a valid completion state. Before completion it must become justified by evidence or be removed.

## Guard before cleanup

Normal source-changing Codemium tasks should run Slop Guard near completion against the actual task diff. Guard Mode is analysis-first. It must not turn a bounded feature/fix into repository-wide cleanup.

Default scope is:

```text
actual diff
→ changed symbols
→ bounded structural neighbors
→ relevant tests/evidence
```

Pre-existing debt is reported separately when useful but is not automatically part of the task. Completion gates focus on slop introduced or worsened by the current task.

## Evidence order

Use the strongest available evidence:

1. deterministic diff/source facts;
2. Structural Graph v3 evidence;
3. evidence-backed reasoning for ambiguity.

Do not block or remove code because it merely "looks over-engineered." Source remains authoritative.

## Coverage honesty

A Slop Risk score is informational. Never fabricate one when changed-source coverage is insufficient. Report scoreability and analysis coverage explicitly, then degrade to ordinary source review.

## Protected complexity / underengineering gate

Anti-Slop must reject underengineering as well as overengineering. Do not blindly remove or weaken:

- authentication or authorization;
- validation or sanitization;
- rate limiting;
- transactions, locking, rollback, or idempotency;
- retry behavior;
- data-integrity checks;
- migrations or compatibility paths;
- security checks;
- tests.

If simplification touches these surfaces, inspect intent and behavioral evidence before accepting it. When ambiguity remains, preserve the safer implementation.

## Cleanup policy

Safe mechanical cleanup may be automated only at high confidence and low behavioral risk. Abstraction removal, helper consolidation, fallback removal, dependency replacement, public API reduction, compatibility changes, and test changes require review.

After any cleanup:

```text
cleanup
→ affected tests
→ impact-mapped tests
→ actual diff review
→ Slop Guard re-check
```

High-impact simplification should receive a logically separate review pass. The writer must not silently approve its own destructive simplification.

## Dependencies and abstractions

Before accepting a new dependency or abstraction, check:

```text
actual need
→ existing project solution
→ standard library
→ native platform/framework
→ existing dependency
→ simple local implementation
→ new abstraction/dependency
```

A single implementation or single caller is only a signal. Architecture boundaries, public contracts, test seams, lifecycle separation, cross-language boundaries, or explicit project constraints can fully justify an abstraction.

## Completion

A source-changing task may complete when:

- requested behavior is satisfied;
- relevant verification passes;
- no high-confidence introduced blocker remains unexplained;
- every changed surface is justified;
- protected complexity has not been accidentally removed;
- cleanup, if any, has been re-verified;
- persistence/freshness obligations are satisfied.
