# Codemium v0.9 — Anti-Slop Intelligence PRD

**Release:** v0.9.0  
**Theme:** Anti-Slop Intelligence  
**Core component:** Justified Change Gate  
**Public name:** Slop Guard  
**Status:** Proposed implementation  
**Date:** 2026-08-19

## 1. Release thesis

Codemium v0.8 answers an important engineering question:

> **Where should the agent look?**

Codemium v0.9 adds the next question:

> **What actually needs to change?**

The goal is not minimum LOC, minimum files, or minimum abstractions. The goal is the **minimum justified engineering surface**: every changed surface should have a defensible relationship to requested behavior, correctness, safety, architecture, dependency requirements, compatibility, or verification.

Codemium v0.9 therefore introduces **Anti-Slop Intelligence** through a task-aware **Justified Change Gate** exposed publicly as **Slop Guard**.

The core rule is:

> **Everything the solution needs. Nothing it does not.**

This must reject both over-engineering and under-engineering. Simplicity never outranks correctness, safety, data integrity, compatibility, or required architecture.

---

## 2. Research-informed design

Before defining v0.9, the design was compared against several public anti-slop / code-quality agent approaches, including:

- `scanaislop/aislop` — deterministic rules, diff-scoped analysis, scoreability/coverage, CI-oriented reporting;
- `Yeachan-Heo/oh-my-claudecode` `ai-slop-cleaner` — deletion-first cleanup, regression protection, bounded cleanup scope;
- `peteromallet/desloppify` — mechanical detectors combined with model reasoning for subjective architecture/code-health concerns;
- `dkneeland/agentic-guardrails` — separation of hardening, deduplication, slop cleanup, and quality gates;
- `garrytan/gstack` review guidance — explicit checks for both over-engineering and under-engineering.

The resulting v0.9 design intentionally does **not** copy a generic linter architecture. Codemium already has Task Contract, Project Brain, Structural Graph v3, Working Set, impact intelligence, test intelligence, and Scope Guard. Slop Guard should use those assets to answer a stronger question than a pattern scanner:

> **Did this task require this change?**

Key decisions from the survey:

1. **Changed-surface-first, not repository-wide cleanup by default.**
2. **Deterministic evidence first; model reasoning only for ambiguity.**
3. **Separate Guard Mode from Cleanup Mode.**
4. **Separate newly introduced slop from pre-existing debt.**
5. **Report analysis coverage and never fabricate a score when coverage is insufficient.**
6. **Do not use arbitrary complexity budgets by FAST/NORMAL/DEEP.**
7. **Add an Underengineering Counter-Gate so simplification cannot silently remove necessary engineering.**
8. **Any cleanup that changes behavior-relevant code must be re-verified.**
9. **High-impact cleanup must receive a logically separate review pass.**

---

## 3. Problem

Coding agents can produce implementations that compile, pass tests, and satisfy the immediate prompt while unnecessarily increasing repository complexity.

Common patterns include:

- single-use forwarding wrappers;
- gratuitous interfaces or service layers;
- duplicate helpers;
- speculative fallbacks;
- redundant validation;
- unnecessary configuration;
- dependencies added for trivial capability;
- unrelated refactors or formatting;
- narrative comments or redundant docstrings;
- debug residue;
- unjustified public APIs;
- compatibility layers with no supported-version evidence;
- type-system escape hatches;
- tests that add little behavioral confidence.

A generic linter can catch some mechanical cases. Codemium can do better because it has task and repository context.

v0.9 must determine whether a changed surface is **justified engineering**, not merely whether it matches a suspicious textual pattern.

---

## 4. Product principles

Priority remains:

1. safety and data integrity;
2. correctness and requested behavior;
3. architecture and interface consistency;
4. adequate verification;
5. scope integrity;
6. simplicity and maintainability;
7. context/token/latency efficiency;
8. code volume.

Anti-Slop Intelligence must never encourage code golf.

A 100-line implementation may be fully justified. A 10-line implementation may be dangerously incomplete.

---

## 5. Goals

### G1 — Prevent new unjustified complexity

A normal Codemium task should not leave behind engineering surface that cannot be justified by the task or repository architecture.

### G2 — Detect introduced and worsened slop

The completion gate should primarily evaluate what the current task introduced or made worse, rather than turning every task into legacy cleanup.

### G3 — Evidence-backed findings

Every material finding must include concrete evidence from the diff, source, graph, project knowledge, or tests.

### G4 — Bounded analysis

Normal Guard Mode should analyze the actual diff, changed symbols, bounded structural neighbors, and relevant tests. It must not blindly scan the whole repository.

### G5 — Safe cleanup

When cleanup is justified, Codemium should simplify only the relevant changed surface and re-run appropriate verification.

### G6 — Protect necessary complexity

Security checks, transactions, idempotency, concurrency controls, compatibility paths, public contracts, and other legitimate complexity must not be removed because they look verbose.

### G7 — Machine-readable output

Slop Guard should produce deterministic structured output suitable for tests, future CI integration, and benchmark analysis.

---

## 6. Non-goals

v0.9 is not:

- a replacement for Ruff, ESLint, Clippy, TypeScript, SonarQube, Semgrep, or compiler/type-checker tooling;
- a formatting system;
- a repository-wide code-health product by default;
- an AI-authorship detector;
- a code minimizer;
- an architecture dictator;
- a promise that every subjective design choice can be scored deterministically;
- a license to delete old debt discovered adjacent to the task.

Repository-wide desloppification, SARIF, historical dashboards, PR annotations, and organization-wide policies are deferred.

---

## 7. Definition of slop

Within Codemium:

> **Slop is engineering surface added or modified without sufficient justification from behavior, architecture, dependency requirements, testability, safety, compatibility, or explicit user requirements.**

Conceptually:

```text
Slop = Changed Surface - Justified Engineering Surface
```

This is a task-relative definition. The same pattern may be slop in one repository and required architecture in another.

---

## 8. Changed-surface classification

Existing Scope Guard classifications remain authoritative:

```text
DIRECT
DEPENDENCY
CLEANUP
TEST
```

Slop Guard adds an internal analysis state:

```text
UNJUSTIFIED
```

`UNJUSTIFIED` is not a valid completion state.

Before completion, every unjustified surface must become either:

```text
JUSTIFIED
```

through evidence, or:

```text
REMOVED
```

through bounded cleanup.

---

## 9. Introduced vs pre-existing debt

Every finding must classify provenance:

```text
introduced
worsened
pre_existing
unknown
```

Default completion gates apply to:

```text
introduced + worsened
```

Pre-existing debt may be reported as adjacent context but must not silently expand task scope.

Example:

```text
src/legacy.py already contains broad exception fallbacks.
The task adds none.

Result: not a v0.9 completion blocker.
```

If the task adds another unsupported fallback, that is an introduced finding and can be gated.

---

## 10. Operating modes

### 10.1 Guard Mode

Default mode for normal `@Codemium` implementation work.

Runs near completion against the actual diff. Primarily read-only analysis.

### 10.2 Cleanup Mode

Activated when:

- Guard Mode identifies high-confidence newly introduced slop whose removal is justified; or
- the user explicitly requests cleanup/deslop work.

Cleanup remains bounded to the task surface unless the user explicitly broadens scope.

### 10.3 Review Mode

Explicit advanced invocation:

```text
@Codemium review slop
$cm-slop --review
```

Review Mode reports evidence and verdict without modifying source.

---

## 11. v0.9 lifecycle

```text
PROJECT BRAIN
      ↓
TASK CONTRACT
      ↓
STRUCTURAL GRAPH
      ↓
WORKING SET
      ↓
ROOT CAUSE / DESIGN
      ↓
IMPLEMENT
      ↓
VERIFY
      ↓
ACTUAL DIFF
      ↓
DIFF SCOPE RESOLUTION
      ↓
CHANGED-SURFACE CLASSIFICATION
      ↓
DETERMINISTIC SLOP PASS
      ↓
STRUCTURAL JUSTIFICATION PASS
      ↓
REASONED ADJUDICATION
      ↓
UNDERENGINEERING COUNTER-GATE
      ↓
PASS / REWORK
      ↓
RE-VERIFY IF CHANGED
      ↓
FINAL DIFF REVIEW
      ↓
PROJECT BRAIN CAPTURE
      ↓
DONE
```

---

## 12. Evidence architecture

Slop Guard uses three evidence layers.

### Layer A — Deterministic

Preferred whenever possible.

Sources include:

- git diff;
- AST / Tree-sitter extraction;
- repository graph;
- imports and references;
- caller counts;
- implementation counts;
- dependency manifests;
- public/private symbol evidence;
- test mappings;
- repository configuration;
- changed-line ownership.

Examples:

- a newly added helper has zero or one caller;
- a debug statement was introduced;
- a new dependency was added;
- a changed file has no scope classification;
- a new interface has one implementation;
- a new forwarding module has one inbound consumer.

Deterministic signals are evidence, not always final judgment.

### Layer B — Structural

Uses Structural Graph v3 to evaluate relationships such as:

```text
CALLS
IMPORTS
IMPORTS_SYMBOL
REFERENCES
IMPLEMENTS
INHERITS
TESTS
DEPENDS_ON
```

Examples:

```text
interface
  └── IMPLEMENTS = 1

helper
  └── callers = 1

new module
  └── no meaningful inbound references
```

### Layer C — Reasoned adjudication

Used only when necessity cannot be decided mechanically.

Questions include:

- Is this abstraction an intentional domain boundary?
- Is the fallback required by a supported compatibility contract?
- Is apparently duplicated logic intentionally isolated?
- Does this defensive check protect a trust boundary?
- Is the public API required by a stable interface?

Reasoned findings must cite repository evidence. A statement such as `this feels over-engineered` is insufficient.

---

## 13. Initial finding categories

### Scope

```text
UNJUSTIFIED_SCOPE
UNRELATED_REFACTOR
UNRELATED_FORMATTING
```

### Duplication

```text
DUPLICATE_IMPLEMENTATION
DUPLICATE_VALIDATION
EXISTING_CAPABILITY_NOT_REUSED
```

### Abstraction

```text
SINGLE_USE_FORWARDER
GRATUITOUS_ABSTRACTION
UNNECESSARY_FILE
UNNECESSARY_CONFIGURATION
```

### Error handling / defensive code

```text
PHANTOM_ERROR_HANDLING
HIDDEN_FALLBACK
REDUNDANT_DEFENSIVE_GUARD
```

### Dependencies

```text
UNJUSTIFIED_DEPENDENCY
```

### API / compatibility

```text
UNJUSTIFIED_PUBLIC_API
PREMATURE_COMPATIBILITY_LAYER
```

### Residue / narration

```text
DEBUG_RESIDUE
NEW_DEAD_CODE
NARRATIVE_COMMENT
REDUNDANT_DOCSTRING
```

### Type integrity

```text
UNJUSTIFIED_TYPE_IGNORE
UNSAFE_TYPE_ESCAPE
```

### Tests

```text
DUPLICATE_TEST
MOCK_ONLY_ASSERTION
NO_BEHAVIOR_ASSERTION
```

Test findings are conservative. Slop Guard must never blindly delete tests.

---

## 14. Finding schema

Machine-readable findings should follow a stable schema similar to:

```json
{
  "rule": "GRATUITOUS_ABSTRACTION",
  "path": "src/payments/adapter.ts",
  "symbol": "PaymentAdapter",
  "provenance": "introduced",
  "severity": "MAJOR",
  "confidence": 0.94,
  "evidence_class": "STRUCTURAL",
  "autofix": "REVIEW_REQUIRED",
  "evidence": {
    "implementations": 1,
    "consumers": 1,
    "public_boundary": false
  },
  "reason": "No repository or task evidence currently requires an abstraction boundary."
}
```

Minimum fields:

- rule;
- path;
- symbol when available;
- provenance;
- severity;
- confidence;
- evidence class;
- autofix class;
- evidence;
- reason.

---

## 15. Confidence and evidence classes

Confidence bands:

```text
HIGH      >= 0.85
MEDIUM    0.60–0.84
LOW       < 0.60
```

Low-confidence findings:

- may inform review;
- may not block completion by themselves;
- may not trigger automatic mutation.

Evidence classes:

```text
DETERMINISTIC
STRUCTURAL
REASONED
```

Authority order remains:

```text
source/runtime fact
      ↓
structural evidence
      ↓
reasoned interpretation
```

Reasoning cannot override source truth.

---

## 16. Risk score and coverage

Slop Guard may expose an informational:

```text
Slop Risk: 0–100
```

The aggregate score is **not** the primary completion gate.

Completion decisions depend on individual findings, confidence, severity, provenance, and safety.

This prevents harmless cosmetic findings from numerically outweighing a serious architectural problem.

### Scoreability

Slop Guard must report analysis coverage.

Example:

```json
{
  "risk_score": 12,
  "scoreable": true,
  "coverage": {
    "changed_lines": 0.96,
    "structural": 0.82
  }
}
```

If coverage is insufficient:

```json
{
  "risk_score": null,
  "scoreable": false
}
```

Codemium must never fabricate a precise score for code it could not meaningfully analyze.

---

## 17. No arbitrary Slop Budget

v0.9 must not define rules such as:

```text
FAST     budget 20
NORMAL   budget 15
DEEP     budget 10
CRITICAL budget 5
```

Engineering depth determines **how deeply Codemium investigates**, not how much legitimate complexity a task may contain.

A CRITICAL payment, migration, or security task may require more defensive engineering than a FAST UI fix.

Blocking thresholds must be calibrated from fixtures and benchmark evidence rather than invented before evaluation.

---

## 18. Completion gates

A task cannot complete with a HIGH-confidence introduced/worsened finding in these initial high-precision categories unless it is evidence-justified:

```text
UNJUSTIFIED_SCOPE
DUPLICATE_IMPLEMENTATION
UNJUSTIFIED_DEPENDENCY
UNJUSTIFIED_PUBLIC_API
```

Other findings are evaluated by severity and risk.

False-positive blockers are more harmful than missed cosmetic slop, so blocker rules should optimize for precision.

---

## 19. Autofix policy

Autofix classes:

### SAFE_MECHANICAL

Potentially safe automatic cleanup when confidence is high:

- obvious debug residue introduced by the task;
- an unused import introduced by the task;
- trivial narration comments that add no rationale.

### REVIEW_REQUIRED

Requires structural/reasoned analysis before editing:

- abstraction removal;
- helper consolidation;
- fallback removal;
- configuration removal;
- dependency replacement;
- public API reduction;
- compatibility simplification.

### NEVER_BLINDLY_REMOVE

Slop Guard must never remove merely because a pattern looks excessive:

- authentication;
- authorization;
- input validation;
- sanitization;
- rate limiting;
- transactions;
- locking;
- idempotency;
- retry logic;
- data-integrity checks;
- migrations;
- compatibility paths;
- security checks;
- tests.

---

## 20. Underengineering Counter-Gate

After Slop Guard recommends or performs simplification, Codemium must explicitly ask:

> **Did simplification remove necessary engineering?**

Required counter-checks include:

```text
failure paths
security boundaries
error semantics
data integrity
concurrency
transactions
idempotency
compatibility
public contracts
observability
verification coverage
```

Example:

```text
SLOP CHECK:
simpler implementation exists

UNDERENGINEERING CHECK:
simpler implementation removes required idempotency

FINAL:
KEEP THE EXISTING DESIGN
```

This counter-gate is mandatory for v0.9.

---

## 21. Regression lock

Any source cleanup must follow:

```text
behavior evidence
      ↓
cleanup
      ↓
affected tests
      ↓
impact-mapped tests
      ↓
actual diff inspection
```

If cleanup invalidates required behavior or safety evidence, Codemium must revert or redesign rather than forcing the simplification through.

Minimal production code does not imply minimal testing.

---

## 22. Writer / reviewer separation

High-impact Anti-Slop cleanup should use logically separate phases:

```text
Writer
  ↓
cleanup
  ↓
Reviewer
  ↓
verification verdict
```

The same reasoning pass should not both make and approve a high-impact simplification.

When the host supports isolated agents/subagents, Codemium may use them. Otherwise use a separate review phase with a fresh review contract and actual diff evidence.

---

## 23. Duplicate intelligence

Before accepting a new helper or abstraction, Codemium should evaluate:

```text
new symbol
    ↓
name search
    ↓
structural search
    ↓
source/semantic comparison
    ↓
existing equivalent?
```

Match classes:

```text
EXACT
NEAR_DUPLICATE
LOOKALIKE
NONE
```

Only `EXACT` or high-confidence `NEAR_DUPLICATE` findings should be eligible for automatic completion blocking.

A similar name alone is not proof of duplication.

---

## 24. Abstraction necessity test

v0.9 must not use arbitrary numeric costs such as `class +3`, `interface +4`, or `dependency +5` as engineering truth.

A new abstraction may be justified by evidence such as:

- multiple implementations;
- a public interface boundary;
- established repository architecture;
- a necessary test seam;
- lifecycle separation;
- cross-language boundary;
- dependency inversion requirement;
- explicit task requirement;
- freshness-qualified Project Brain constraint.

If none of those or an equivalent justification exists, the abstraction becomes a review candidate.

---

## 25. Dependency necessity test

Before accepting a new dependency, preserve Codemium's existing anti-overengineering ladder:

```text
1. actual task need?
2. existing project capability?
3. standard library?
4. native platform?
5. existing dependency?
6. simple local implementation?
7. only then a new dependency
```

A new dependency is not inherently slop, but it requires explicit benefit evidence.

---

## 26. Diff scope resolver

Slop Guard must make the analyzed diff scope explicit.

Preferred resolution order:

```text
explicit user/base ref
        ↓
PR base when known
        ↓
branch divergence / merge-base
        ↓
HEAD + working tree fallback
```

Human-readable reports should state the chosen scope, for example:

```text
Diff scope: feature/auth → origin/main
```

This avoids judging unrelated historical changes as part of the active task.

---

## 27. Changed-surface-first expansion

Normal Guard Mode starts from:

```text
actual diff
+
changed symbols
+
direct structural neighbors
+
relevant tests
```

Expansion is allowed only when a material finding has a specific unresolved evidence gap.

A blind full-repository scan is not the default.

This protects latency, token efficiency, and scope integrity.

---

## 28. Project Brain integration

Project Brain can provide durable architectural constraints that materially change Slop Guard judgment.

Examples:

```text
Project intentionally uses native fetch; do not introduce Axios.
```

```text
Python 3.10 compatibility is a supported product requirement.
```

Therefore the same code pattern may be unnecessary in one repository and required in another.

Project Brain evidence remains freshness-qualified and must not override current source truth.

---

## 29. Polyglot Intelligence integration

Structural Graph v3 provides bounded evidence for:

- caller counts via `CALLS` / `REFERENCES`;
- implementation counts via `IMPLEMENTS` / `INHERITS`;
- dependency evidence via `IMPORTS`, `IMPORTS_SYMBOL`, `DEPENDS_ON`;
- test relevance via `TESTS`;
- cross-language boundaries via explicit cross-language relationships;
- symbol-aware changed-surface analysis.

Example uses:

```text
single-use forwarder
  → one caller + trivial forwarding source body

gratuitous interface signal
  → one implementation + one consumer + no boundary evidence

test mapping
  → changed symbol → TESTS relationship
```

The graph decides where to inspect. Source remains authoritative.

---

## 30. Rule severity

Suggested severity classes:

```text
BLOCKER
MAJOR
MINOR
INFO
```

Severity represents engineering consequence, not how strongly something appears AI-generated.

Codemium evaluates engineering quality, not authorship.

It must never claim that a person or model authored code based on these heuristics.

---

## 31. Human-readable output

Example:

```text
CODEMIUM SLOP GUARD

Scope
feature/auth → origin/main

Changed files: 5
Classified: 5
Unjustified: 0

Slop Risk: 14/100
Coverage: 94%
Status: PASS

Introduced findings
MAJOR  0
MINOR  2
- narrative comment
- single-use forwarding helper

Protected complexity
- auth validation retained
- retry policy retained

Underengineering gate
PASS

Verification
PASS
```

---

## 32. JSON output

Initial schema shape:

```json
{
  "schema_version": 1,
  "status": "pass",
  "scope": {
    "base": "origin/main",
    "head": "working-tree"
  },
  "risk_score": 14,
  "scoreable": true,
  "coverage": {
    "changed_lines": 0.94,
    "structural": 0.88
  },
  "surfaces": {
    "direct": 2,
    "dependency": 1,
    "cleanup": 0,
    "test": 2,
    "unjustified": 0
  },
  "findings": []
}
```

Schema changes after release should be explicitly versioned.

---

## 33. Proposed implementation surface

Minimum expected implementation:

```text
plugins/codemium/engine/slop_guard.py
plugins/codemium/skills/slop/SKILL.md
plugins/codemium/skills/codemium/references/slop-policy.md
tests/...
```

Additional modules should only be introduced when the implementation demonstrates a real separation of responsibility.

Anti-Slop must not overengineer Anti-Slop.

Primary public UX remains:

```text
@Codemium <task>
```

Slop Guard runs automatically near completion.

Advanced direct invocation:

```text
$cm-slop
$cm-slop --review
```

---

## 34. Verification strategy

Tests must include both slop-positive and protected-complexity fixtures.

### Positive fixtures

At minimum:

```text
single-use forwarding wrapper
duplicate helper
unused/unjustified dependency
unrelated refactor
narrative comment
debug residue
gratuitous interface
speculative fallback
unjustified public API
```

### Negative / protection fixtures

At minimum:

```text
authentication validation
transaction boundary
idempotency
retry with documented requirement
compatibility shim
multiple interface implementations
necessary test seam
public API contract
security guard
data-integrity check
```

The protection suite is equally important. A system that removes legitimate engineering is not an Anti-Slop success.

---

## 35. Benchmark design

The v0.9 benchmark must measure both error directions:

```text
FAILURE A
Codemium misses introduced slop.

FAILURE B
Codemium removes or blocks necessary engineering.
```

Minimum task classes:

- simple localized bug fix;
- existing-helper reuse task;
- feature implementation;
- compatibility requirement;
- security-sensitive change;
- transaction/data-integrity change;
- legacy repository change;
- cross-language change.

Minimum benchmark arms:

```text
Baseline agent
Codemium v0.8
Codemium v0.9 Guard
```

Optional ablation:

```text
v0.9 deterministic-only
v0.9 hybrid deterministic + reasoned adjudication
```

Metrics:

- task success;
- quality/safety pass;
- regressions;
- files changed;
- LOC changed;
- unrelated changed lines;
- new dependencies;
- duplicate implementations introduced;
- unnecessary abstractions introduced;
- false-positive Slop Guard findings;
- necessary complexity incorrectly removed;
- Slop Guard latency;
- Slop Guard token overhead.

No efficiency claim is valid if correctness or safety regresses.

---

## 36. Blocking-rule calibration

Blocking thresholds must not be invented before evaluation.

Before v0.9 release, blocker rules should be calibrated from:

- deterministic fixtures;
- negative/protection fixtures;
- measured benchmark runs;
- false-positive analysis;
- representative real-repository examples.

The initial blocker set should optimize for high precision.

---

## 37. Performance requirements

Normal Guard Mode must not require a blind full-repository scan.

Expected expansion:

```text
diff
 ↓
changed symbols
 ↓
bounded graph neighbors
 ↓
specific evidence gap only
```

When structural information is unavailable or incomplete, Codemium should degrade to source inspection and ordinary review rather than fabricating relationships.

Performance telemetry should include:

- analysis wall-clock time;
- changed files/symbols inspected;
- graph expansions;
- model adjudications requested;
- token overhead when observable.

---

## 38. Fail-open / fail-closed policy

For ordinary quality findings:

```text
insufficient evidence
→ report uncertainty
→ do not destructively simplify
```

For safety-critical ambiguity:

```text
insufficient evidence
→ preserve the safer implementation
```

Codemium should prefer a missed cosmetic cleanup over an unsafe deletion.

---

## 39. Acceptance criteria

v0.9.0 is ready only when all of the following are true.

### Core

1. Slop Guard analyzes the actual task diff.
2. Default analysis is changed-surface-first.
3. Every changed file receives scope classification.
4. Introduced/worsened findings are distinguished from pre-existing debt.
5. `UNJUSTIFIED` changed surfaces cannot silently complete.
6. Diff scope is explicit in reports.

### Intelligence

7. Deterministic findings are supported.
8. Graph-backed structural evidence is supported.
9. Ambiguous cases can use evidence-backed reasoned adjudication.
10. Analysis coverage and scoreability are reported.
11. Unsupported/incomplete analysis does not fabricate a score.

### Safety

12. Underengineering Counter-Gate exists.
13. Security/data-integrity/compatibility protection fixtures pass.
14. Tests are never blindly deleted as slop.
15. Source cleanup is re-verified.
16. High-impact simplification receives a separate review phase.

### Initial detection coverage

17. Unrelated diff detection.
18. Single-use forwarding wrapper signal.
19. Duplicate implementation signal.
20. Unjustified dependency addition signal.
21. Debug residue detection.
22. Narrative comment detection for clear mechanical cases.
23. New dead-code signal.
24. Unjustified public API expansion signal.

### Output / integration

25. Human-readable report exists.
26. Machine-readable JSON exists.
27. Findings include evidence and confidence.
28. Main `@Codemium` lifecycle invokes Guard Mode automatically.
29. `$cm-slop` direct skill exists.
30. Existing v0.8 behavior remains compatible.

### Evaluation

31. Anti-Slop benchmark exists.
32. Necessary-complexity false-positive fixtures exist.
33. Correctness and safety do not regress versus baseline.
34. Blocking rules are evidence-calibrated before release.

---

## 40. Deferred beyond v0.9.0

Not required for initial release:

- repository-wide desloppification mode;
- GitHub PR annotations;
- SARIF output;
- historical quality dashboards;
- organization/team policy hierarchy;
- IDE visualization;
- continuous Slop trends;
- hosted scoring;
- cross-PR quality history;
- automatic large-scale refactoring.

These belong in v0.9.x or later after the core Justified Change Gate proves useful.

---

## 41. Release positioning

Codemium evolution:

```text
v0.7
Engineering Intelligence
        ↓
v0.8
Polyglot Intelligence
        ↓
v0.9
Anti-Slop Intelligence
```

The progression is:

```text
Understand the task
        ↓
Find the right code
        ↓
Understand the impact
        ↓
Make the justified change
        ↓
Reject unnecessary change
        ↓
Prove nothing important was lost
```

v0.8 asks:

> **Where should the agent look?**

v0.9 asks:

> **What actually needs to exist?**

---

## 42. Final rule

Codemium must not optimize for the fewest lines, fewest files, fewest abstractions, or highest cosmetic score.

It should optimize for:

> **The smallest engineering surface that fully preserves required correctness, safety, architecture, compatibility, and behavior.**

Or, more simply:

> **Everything the solution needs. Nothing it does not.**
