# Codemium v0.8 — Polyglot Intelligence PRD

**Release:** v0.8.0  
**Theme:** Polyglot Intelligence  
**Status:** Release candidate implementation  
**Date:** 2026-08-18

## 1. Release thesis

Codemium v0.8 extends Structural Intelligence from a Python-deep / other-languages-fallback graph into a deterministic **polyglot engineering graph** that can understand JavaScript, TypeScript, and TSX deeply enough to improve repository navigation, dependency reasoning, blast-radius analysis, and test selection across language boundaries.

The core product rule does not change:

> Repository source is authoritative. The graph narrows where to inspect; it never replaces source or runtime evidence.

Polyglot Intelligence must remain useful when optional parser dependencies are absent. Deep parsing is an enhancement; safe deterministic degradation is a release requirement.

## 2. Scope

v0.8.0 delivers:

- Parser abstraction
- Tree-sitter runtime integration
- JavaScript / JSX deep parsing
- TypeScript deep parsing
- TSX deep parsing
- Cross-language graph relationships
- Better impact intelligence
- Better test intelligence

## 3. Parser abstraction

### 3.1 Contract

Repository extraction is selected through parser adapters rather than language-specific branching inside the graph builder.

Every parser adapter exposes:

- support detection by path/language;
- runtime availability;
- deterministic parse output;
- parser identity/version;
- capability reporting;
- metadata describing deep/degraded parsing.

Canonical parser order for v0.8:

```text
Python source
  -> PythonAstParser

.js / .jsx
  -> TreeSitterJSTSParser (JavaScript grammar)
  -> RegexFallbackParser when unavailable/failing

.ts
  -> TreeSitterJSTSParser (TypeScript grammar)
  -> RegexFallbackParser when unavailable/failing

.tsx
  -> TreeSitterJSTSParser (TSX grammar)
  -> RegexFallbackParser when unavailable/failing

Other supported source
  -> RegexFallbackParser
```

### 3.2 Safe degradation

Codemium core must still start and build a graph without Tree-sitter installed. Missing optional runtime packages, unsupported syntax, or parser failures must fall back to deterministic extraction rather than making the repository unusable.

Parser availability and coverage must be visible through graph coverage, health, and doctor diagnostics.

## 4. Tree-sitter runtime

The v0.8 deep parser runtime is declared separately in `requirements-polyglot.txt` so the host-agnostic core remains dependency-light.

Required packages for the v0.8 deep runtime:

```text
tree-sitter
tree-sitter-javascript
tree-sitter-typescript
```

The dedicated Polyglot CI path installs the pinned runtime and must execute the real JS/TS/TSX fixture.

## 5. JavaScript, TypeScript, and TSX extraction

The deep parser extracts deterministic facts including, where structurally available:

- functions and generator functions;
- arrow-function assignments;
- classes;
- class methods;
- TypeScript interfaces;
- TypeScript type aliases;
- TypeScript enums;
- imports;
- default imports;
- named imports;
- namespace imports;
- CommonJS `require(...)` bindings;
- exports/re-exports;
- calls and constructor calls;
- class inheritance/implementation evidence;
- source locations;
- parser dialect and parse-error metadata.

No LLM is used to generate these structural facts.

## 6. Cross-language graph

### 6.1 Structural Graph v3

v0.8 raises repository graph schema to **Structural Graph v3**.

Graph v3 retains the v0.7 relationships and adds imported-symbol evidence:

```text
DEFINES
CONTAINS
IMPORTS
IMPORTS_SYMBOL
CALLS
REFERENCES
INHERITS
IMPLEMENTS
TESTS
DEPENDS_ON
```

### 6.2 Cross-language resolution

Graph resolution must support repository-owned relative module paths across compatible source extensions. Examples:

```text
legacy.js -> ./math -> math.ts
view.tsx  -> ./service -> service.ts
service.test.ts -> ../src/service -> service.ts
```

Resolved import bindings should connect local aliases to source symbols where deterministic evidence exists.

Example:

```text
import { add } from './math'

module:src/legacy.js
  IMPORTS -> module:src/math.ts
  IMPORTS_SYMBOL -> symbol:src/math.ts#add:function

symbol:src/legacy.js#plusOne:function
  CALLS -> symbol:src/math.ts#add:function
```

Edges crossing source-language boundaries carry `cross_language = true`.

### 6.3 Provenance

Existing provenance semantics remain mandatory:

- `DIRECT` — directly observed in parsed source;
- `RESOLVED` — deterministically resolved through repository structure/bindings;
- `HEURISTIC` — deterministic fallback evidence, lower confidence.

Cross-language status does not weaken provenance requirements.

## 7. Better impact intelligence

v0.7 impact starts primarily from changed files. v0.8 must prefer the smallest structurally justified seed when a diff can be mapped to symbols.

### 7.1 Changed-line mapping

For Git diffs, Codemium reads zero-context hunk ranges and intersects those ranges with graph symbol locations.

```text
changed lines
  -> changed symbol(s), when known
  -> reverse structural traversal
  -> affected files/symbols
  -> prioritized tests
```

If no symbol can be identified, Codemium falls back to the changed file as the seed.

### 7.2 Weighted traversal

Impact evidence is weighted by:

- relationship type;
- provenance quality;
- traversal distance.

Affected rows expose:

- distance;
- score;
- confidence;
- relations;
- provenance;
- cross-language status;
- compact evidence path.

### 7.3 Cross-language risk

A materially affected surface across a language boundary contributes to blast-radius escalation. It must not automatically force maximum verification, but it is explicit risk evidence.

Impact output includes:

```text
impact_mode
seed_evidence
affected
likely_dependents
cross_language_dependents
related_tests
test_plan
blast_radius
risk_reasons
recommended_verification
```

## 8. Better test intelligence

Test Intelligence v3 prioritizes structural evidence before naming/import heuristics.

### 8.1 Evidence ranking

Highest confidence:

```text
DIRECT structural call/reference evidence
RESOLVED imported-symbol/module evidence
```

Fallback:

```text
HEURISTIC naming/import similarity
```

### 8.2 Test classification

Mapped tests are classified as:

- unit;
- integration;
- e2e.

Test relationships expose confidence and score. Impact output converts relevant tests into a prioritized plan:

- `P0` — strongest direct/resolved evidence on highly affected surface;
- `P1` — meaningful structural evidence;
- `P2` — weak/heuristic supporting evidence.

### 8.3 Cross-language tests

Tests can cover source written in another language/dialect when the import/call relationship resolves structurally. Example: JavaScript consumer or test evidence may map into TypeScript source.

## 9. Incremental behavior

Graph v3 preserves delta-first refresh:

```text
UNCHANGED -> reuse compatible extraction
NEW       -> parse
MODIFIED  -> invalidate/reparse changed source
DELETED   -> prune owned graph entities and relationships
```

Parser version, graph schema, content hash, parser identity, and capabilities participate in reuse validity.

Upgrading from Graph v2 to Graph v3 forces incompatible cached extraction to rebuild rather than silently reusing stale structural facts.

## 10. Health and diagnostics

`health.py` and `doctor.py` must report enough information to distinguish deep Polyglot Intelligence from degraded fallback mode, including:

- graph schema version;
- parser version;
- Tree-sitter runtime availability;
- deep languages;
- parser counts;
- language counts;
- capability coverage;
- cross-language edge count/relation counts;
- unresolved relationships;
- graph freshness.

## 11. Compatibility

v0.8 must preserve:

- Project Brain persistence/freshness behavior;
- canonical project-root handling;
- Codex persistence gate;
- FAST/NORMAL/DEEP/CRITICAL task depth contract;
- bounded Working Set behavior;
- Scope Guard;
- deterministic cache behavior;
- host-neutral core state;
- stable Codex adapter and Beta Claude/Gemini/Cursor/OpenCode adapters;
- safe behavior when optional Polyglot runtime is unavailable.

## 12. Verification strategy

### Core gate

Runs without installing optional Tree-sitter packages first. It proves:

- parser abstraction imports safely;
- Python AST behavior remains intact;
- non-deep languages can degrade to fallback;
- Graph v3 works;
- Project Brain regressions remain protected;
- symbol-aware impact works for Python;
- Test Intelligence v3 works.

### Polyglot gate

CI then installs `requirements-polyglot.txt` and runs `scripts/verify_polyglot.py`.

The fixture must include all of:

```text
math.ts
service.ts -> math.ts
view.tsx -> service.ts
legacy.js -> math.ts
tests/service.test.ts -> service.ts
```

It must prove:

- zero fallback parsing for those fixture JS/TS/TSX files;
- expected Tree-sitter parser identities;
- JS -> TS imported-symbol edge;
- JS -> TS resolved call edge;
- TSX -> TS dependency;
- mapped TS test evidence;
- cross-language edge accounting;
- symbol-aware impact after modifying a TypeScript function;
- JS and TS dependents are discovered;
- related test appears in the prioritized test plan.

## 13. Acceptance criteria

v0.8.0 is release-ready only when:

1. `VERSION` and all host manifests report `0.8.0`.
2. Graph schema is v3.
3. Parser abstraction is the canonical extraction entry point.
4. JavaScript, TypeScript, and TSX pass Tree-sitter integration tests.
5. Missing Tree-sitter dependencies degrade safely to deterministic fallback.
6. At least one JS -> TS cross-language `IMPORTS_SYMBOL` and resolved `CALLS` relationship is proven by fixture.
7. Symbol-aware diff impact is proven by fixture.
8. Cross-language dependents are surfaced explicitly.
9. Test Intelligence v3 emits confidence, score, classification, and priority.
10. Existing Project Brain/core regression fixture passes.
11. Codex lifecycle CI passes.
12. Linux and Windows full-validation scripts are v0.8-aware.
13. README, PRD, changelog, installation docs, and host metadata are consistent.
14. No graph inference is presented as stronger provenance than its evidence supports.

## 14. Non-goals for v0.8.0

Not required in this release:

- deep Go/Rust/Java parsing;
- semantic embeddings or vector search;
- GraphRAG;
- LLM-generated graph relations;
- graph visualization UI;
- hosted/shared graph server;
- package-manager dependency solving beyond deterministic source import resolution;
- type-checker replacement;
- full language-server replacement.

These can follow after the JS/TS/TSX architecture is proven stable.

## 15. Release definition

**v0.8.0 Polyglot Intelligence** is complete when Codemium can deeply parse JavaScript/TypeScript/TSX through Tree-sitter, build deterministic cross-language structural evidence, narrow diffs to changed symbols, traverse blast radius across language boundaries, and choose tests with stronger structural confidence—while preserving the dependency-light fallback and all existing durable Project Brain guarantees.
