# Codemium v0.9.0 — Anti-Slop Intelligence

Codemium v0.9.0 adds a task-aware **Justified Change Gate**, exposed as **Slop Guard**.

The release extends Codemium's existing Project Brain and Polyglot Intelligence with one more completion question:

> **Does every changed engineering surface actually need to exist?**

The target is not minimum LOC. It is the **minimum justified engineering surface**: everything the solution needs, nothing it does not.

## Highlights

### Slop Guard

Normal source-changing Codemium tasks can inspect the actual task diff before completion and classify changed surfaces as:

- `DIRECT`
- `DEPENDENCY`
- `CLEANUP`
- `TEST`
- internal `UNJUSTIFIED`

Untracked files are included when they are safe/readable, while `.codemium/` state is excluded.

### Finding provenance

Anti-Slop findings explicitly distinguish:

- `introduced`
- `worsened`
- `pre_existing`
- `unknown`

High-confidence blocking gates target newly introduced or worsened engineering. Historical debt does not become a blocker merely because the current task touched the same file.

### Evidence-backed justification

Ambiguous findings can be resolved through a narrow, evidence-backed `JUSTIFIED` adjudication. Decisions must match the exact finding and include a substantive reason plus concrete source/task evidence.

Accepted adjudication remains visible in the report and is excluded from blocking/risk calculation. It is not a blanket waiver.

### Underengineering Counter-Gate

Anti-Slop does not equate smaller code with better code. Slop Guard explicitly protects necessary complexity around:

- authentication and authorization;
- validation and sanitization;
- rate limiting;
- transactions, locking, rollback, and idempotency;
- retry behavior;
- data-integrity checks;
- migrations and compatibility paths;
- security checks;
- tests.

Removing protected complexity triggers review instead of silently rewarding simplification.

### Deterministic + structural evidence

Slop Guard combines:

1. deterministic Git/source evidence;
2. Structural Graph v3 evidence from v0.8 Polyglot Intelligence;
3. evidence-backed reasoning only where mechanical evidence cannot settle the decision.

The repository source remains authoritative.

### Coverage honesty

The aggregate Slop Risk score is informational. Codemium reports analysis coverage and does not fabricate a score when the changed source is not sufficiently scoreable.

### Release calibration

v0.9 includes a deterministic release calibration corpus for blocker semantics and false-positive protection. Core CI verifies introduced/worsened blockers, pre-existing debt, evidence-backed justification, ambiguous findings, protected-complexity removal, and clean diffs.

This calibration is **not** a competitive performance benchmark. Codemium does not publish a numeric v0.9 Anti-Slop efficiency/quality improvement claim until representative multi-arm agent runs are measured and retained as evidence.

## New surfaces

- `plugins/codemium/engine/slop_guard.py`
- `plugins/codemium/skills/slop/SKILL.md` (`$cm-slop`)
- `plugins/codemium/skills/codemium/references/slop-policy.md`
- `plugins/codemium/tests/test_slop_guard.py`
- `benchmarks/V09_ANTISLOP_BENCHMARK.md`
- `benchmarks/v09-blocking-calibration.json`
- `benchmarks/calibrate_v09_blocking.py`

## Compatibility

v0.9 preserves the v0.8 foundations:

- Structural Graph v3;
- Python AST extraction;
- optional Tree-sitter JavaScript/JSX/TypeScript/TSX parsing;
- cross-language `IMPORTS_SYMBOL` evidence;
- symbol-aware impact and prioritized test intelligence;
- Project Brain persistence and freshness;
- bounded Working Sets;
- Codex lifecycle persistence hooks;
- Claude Code, Gemini CLI, Cursor, and OpenCode adapters.

## Verification

Release validation includes:

```sh
python scripts/verify_core.py
python -m pip install -r requirements-polyglot.txt
python scripts/verify_polyglot.py
python scripts/verify_codex_plugin.py
python benchmarks/calibrate_v09_blocking.py
```

Full Linux/macOS and Windows host validation remains available through the release verification scripts.

## Product rule

> **Everything the solution needs. Nothing it does not.**

More precisely: Codemium optimizes for the smallest engineering surface that fully preserves required correctness, safety, architecture, compatibility, and behavior.
