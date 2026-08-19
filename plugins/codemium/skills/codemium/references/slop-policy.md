# Anti-Slop / Justified Change Policy

Codemium optimizes for the **minimum justified engineering surface**, not minimum LOC, files, abstractions, or dependencies.

## Core rule

Every changed surface must be defensible as one of:

- `DIRECT` — implements requested behavior;
- `DEPENDENCY` — required for a direct change to work safely;
- `CLEANUP` — code made obsolete by this exact change;
- `TEST` — evidence for changed behavior.

`UNJUSTIFIED` is an internal Slop Guard state, never a valid completion state. Before completion it must become justified by evidence or be removed.

### CLEANUP is explicit

Do not infer cleanup merely because a changed file looks old or redundant. A cleanup surface must be causally attributable to the current task.

When deterministic task state is available, record caused cleanup paths in `tasks/active.json` as `cleanup_set`, or attach `working_set_evidence` with `kind: cleanup`. Slop Guard then classifies those paths as `CLEANUP` rather than treating them as ordinary direct work or unrelated scope.

This mechanism is not permission for opportunistic cleanup. Pre-existing debt that was not made obsolete by the task remains out of scope.

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

## Finding provenance

Every finding must carry one of:

- `introduced` — the task added the suspicious engineering surface;
- `worsened` — the surface existed, but the task made the relevant anti-slop property worse;
- `pre_existing` — the suspicious property already existed before the task and was not introduced by it;
- `unknown` — available evidence cannot safely determine provenance.

Blocking gates target `introduced` and `worsened` findings. `pre_existing` findings do not become blockers merely because a task touched the same file. `unknown` major findings require review rather than fabricated certainty.

For structural findings, Codemium should compare the changed symbol with the base revision when deterministic source parsing can establish whether the symbol/property already existed. Unsupported or ambiguous cases remain `unknown`.

## Evidence order

Use the strongest available evidence:

1. deterministic diff/source facts;
2. Structural Graph v3 evidence;
3. evidence-backed reasoning for ambiguity.

Do not block or remove code because it merely "looks over-engineered." Source remains authoritative.

## Evidence-backed adjudication

Ambiguous blockers may be explicitly justified, but only with a recorded reason and concrete evidence. Slop Guard accepts adjudications from:

```text
.codemium/runtime/slop-adjudications.json
```

or an explicit CLI argument:

```sh
python plugins/codemium/engine/slop_guard.py \
  --root . \
  --adjudications .codemium/runtime/slop-adjudications.json \
  --json
```

Minimum schema:

```json
{
  "schema_version": 1,
  "decisions": [
    {
      "rule": "UNJUSTIFIED_PUBLIC_API",
      "path": "src/api.ts",
      "line": 42,
      "symbol": "createSession",
      "decision": "JUSTIFIED",
      "reason": "This export is required by the repository-owned public adapter contract.",
      "evidence": [
        {"kind": "source", "path": "src/adapters/public.ts"},
        {"kind": "task", "detail": "acceptance requires the public adapter surface"}
      ]
    }
  ]
}
```

A `JUSTIFIED` decision is accepted only when it matches the finding, contains a substantive reason, and includes valid evidence. Accepted adjudication removes that finding from blocking/risk calculation; it does not delete the finding from the report.

Do not use adjudication as a blanket waiver. Match the exact rule/path and, when available, line/symbol. Invalid or unmatched decisions remain visible in the report.

**Adjudication never bypasses the Underengineering Counter-Gate.** Removing protected security, data-integrity, compatibility, concurrency, or verification logic still requires explicit review and re-verification.

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

## Blocking calibration

Blocking rules are deliberately high precision. Release validation must exercise positive, negative, provenance, adjudication, and protected-complexity cases. The repository calibration corpus lives at `benchmarks/v09-blocking-calibration.json` and is checked by `benchmarks/calibrate_v09_blocking.py`.

That calibration validates gate semantics only. It is **not** a competitive benchmark and must not be published as an agent-performance or efficiency claim.

## Completion

A source-changing task may complete when:

- requested behavior is satisfied;
- relevant verification passes;
- no high-confidence introduced/worsened blocker remains unexplained;
- every changed surface is justified;
- any accepted adjudication is evidence-backed and recorded;
- protected complexity has not been accidentally removed;
- cleanup, if any, has been re-verified;
- persistence/freshness obligations are satisfied.
