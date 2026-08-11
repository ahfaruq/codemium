# Codemium v0.7 Product Requirements Document

## Structural Intelligence & Evidence Bridge

**Status:** Proposed implementation target  
**Target release:** v0.7.0  
**Baseline:** Codemium v0.6.x  
**Theme:** Upgrade repository inventory into evidence-backed structural engineering intelligence without turning Codemium into a generic knowledge-graph product.

---

## 1. Executive summary

Codemium v0.7 upgrades Repository Intelligence from a lightweight file/symbol/import inventory into an **evidence-backed structural intelligence layer**.

The purpose is not to copy Graphify or make Codemium a graph visualization, GraphRAG, or generic repository search product. The purpose is to strengthen Codemium's existing thesis:

> **The senior engineer who already knows your codebase.**

v0.7 gives Codemium deterministic structural knowledge that directly improves:

- Project Brain evidence and freshness;
- Working Set precision;
- Change Impact and blast-radius analysis;
- Test Intelligence;
- Scope Guard explanations;
- risk-aware verification;
- delta-first repository understanding.

The repository remains the source of truth. The Structural Graph is a regenerable derived artifact. Project Brain remains the durable engineering-memory layer.

```text
                        CODEMIUM
                           │
             ┌─────────────┴─────────────┐
             │                           │
      Structural Intelligence      Project Brain
       derived from source        learned engineering truth
             │                           │
             └──────── Evidence Bridge ──┘
                           │
                           ▼
                     Working Set
                           │
                           ▼
                    Change Impact
                           │
                           ▼
                     Verification
                           │
                           ▼
                    Coding Agent
```

---

## 2. Relationship to the main PRD

This document is the normative v0.7 extension to `PRD.md`.

All existing Codemium product invariants remain in force unless this document explicitly extends them. In particular:

1. safety and data integrity remain the highest quality priority;
2. Project Brain remains durable, concise, source-backed engineering knowledge rather than conversation memory;
3. `@Codemium` remains the primary Codex UX;
4. host adapters remain host-native while sharing one engineering contract;
5. context stays bounded and evidence-triggered;
6. Codemium optimizes minimum justified engineering, not minimum LOC;
7. source code and runtime/test evidence remain authoritative over derived indexes.

---

## 3. Problem

Codemium v0.6 already contains Repository Intelligence, Working Set generation, impact analysis, test mapping, deterministic caching, and Project Brain. However, the repository model is intentionally lightweight.

The current class of repository map can identify files, symbols, imports, and test-like files, but it cannot reliably model enough structural relationships to answer questions such as:

```text
A calls B.
B implements C.
D references A.
Test X directly exercises B.
Changing B reaches E through C.
Project Brain fact P was established from symbol A.
Symbol A changed after P was captured.
```

That produces downstream limitations.

### 3.1 Working Set precision

Candidate files can be selected because names or symbols match the task wording instead of because the files participate in the affected behavior.

### 3.2 Impact precision

Indirect callers, public interfaces, workers, events, and transitive dependencies can be missed when impact analysis depends primarily on filename/import heuristics.

### 3.3 Test selection

Source-to-test mapping can over-rely on naming and directory conventions instead of direct structural evidence.

### 3.4 Project Brain freshness

An ACTIVE Project Brain entry can remain reusable even after the source evidence that established it has changed.

### 3.5 Repeated discovery

Agents may still need broad search and file reading to discover relationships a deterministic structural index could already provide.

---

## 4. North-star outcome

For repeated work on an evolving repository:

```text
Structural understanding       ↑↑↑
Working Set precision           ↑↑
Impact visibility               ↑↑
Project Brain trustworthiness   ↑↑
Relevant test discovery         ↑↑

Repeated repository searching   ↓↓
Broad file reading              ↓↓
Stale knowledge reuse           ↓↓↓
False confidence                ↓↓↓

Correctness                     >= baseline
Safety                          >= baseline
Verification adequacy           >= baseline
Scope integrity                 >= baseline
```

Efficiency gains do not count if correctness, safety, architecture consistency, or verification quality decreases.

---

## 5. Dual Intelligence Model

Codemium v0.7 formalizes two different kinds of project intelligence.

### 5.1 Structural Intelligence

Mechanically derived from the repository.

Examples:

- files and modules;
- symbols;
- imports and dependencies;
- calls and references;
- inheritance and implementation relationships;
- source-to-test relationships;
- public interface relationships;
- changed/deleted source identity.

Properties:

- deterministic wherever practical;
- local by default;
- regenerable;
- source-backed;
- freshness-aware;
- relatively cheap;
- not durable interpretation.

Structural state lives under:

```text
.codemium/repository/
```

### 5.2 Engineering Intelligence

Learned through engineering work and stored in Project Brain.

Examples:

- decisions;
- constraints;
- architecture boundaries;
- interface behavior;
- established patterns;
- root causes;
- known bugs;
- material engineering risks.

Examples of facts that belong in Project Brain, not the Structural Graph:

```text
The mobile client requires a five-second token-rotation grace period.

The queue consumer is intentionally single-threaded because ordering is contractual.

The logout regression occurs when two refresh requests race.

Do not remove compatibility behavior until API v2 is retired.
```

### 5.3 Evidence Bridge

Project Brain entries may reference Structural Graph entities and source fingerprints.

The bridge must let Codemium answer:

```text
What source established this fact?
Does that source still exist?
Has the supporting implementation changed?
Is this knowledge still safe to reuse?
```

The bridge connects structural truth to learned engineering truth without collapsing them into one store.

---

## 6. Repository Structural Graph v2

`repository/graph.json` becomes a relational repository model rather than only a file inventory.

### 6.1 Minimum node types

```text
FILE
MODULE
SYMBOL
TEST
```

Supported symbol subtypes should include where parser capability permits:

```text
FUNCTION
METHOD
CLASS
INTERFACE
TYPE
ENUM
CONSTANT
TABLE
ROUTE
```

Additional node types may be introduced only when they have deterministic semantics and a concrete Codemium consumer.

### 6.2 Minimum relationship vocabulary

```text
DEFINES
IMPORTS
CALLS
REFERENCES
INHERITS
IMPLEMENTS
TESTS
CONTAINS
DEPENDS_ON
```

Relationship labels are governed schema values, not arbitrary free-form LLM prose.

### 6.3 Stable identity

Node identity must not depend solely on line numbers.

Preferred symbol identity:

```text
repository-relative path
+
qualified symbol name
+
symbol kind
```

Line ranges, source hashes, and parser metadata are evidence attributes rather than primary identity.

### 6.4 Relationship provenance

Every edge must expose how Codemium knows it exists.

Required provenance classes:

```text
DIRECT
RESOLVED
HEURISTIC
```

**DIRECT** — observed directly by a deterministic parser.

**RESOLVED** — derived deterministically from imports, symbol tables, or reference resolution.

**HEURISTIC** — likely relationship inferred through deterministic naming/project conventions.

HEURISTIC relationships must never silently receive the same trust as DIRECT relationships.

No LLM-generated structural edge is required for v0.7.

---

## 7. Parser capability model

Codemium must not imply equal analysis depth for every language.

Each parsed file must expose parser identity and capabilities.

Example:

```json
{
  "path": "src/auth/service.ts",
  "parser": "tree-sitter-typescript",
  "capabilities": [
    "symbols",
    "imports",
    "calls",
    "references"
  ]
}
```

Fallback example:

```json
{
  "path": "legacy/example.xyz",
  "parser": "fallback-regex",
  "capabilities": [
    "symbols",
    "imports"
  ]
}
```

Consumers must distinguish full structural evidence from partial parser coverage.

### 7.1 Distribution constraint

Structural Intelligence must not introduce a mandatory manual installation ceremony for normal Codemium use.

Implementation may use Tree-sitter, language-native parsers, bundled deterministic parsers, or safe fallback scanning.

If enhanced parsing is unavailable, Codemium must degrade honestly rather than claim relationships it cannot prove.

---

## 8. Incremental structural updates

Structural graph maintenance must become delta-first.

Maintain a manifest containing at least:

```text
path
content hash
parser identity
parser version
graph schema version
```

On refresh, classify files as:

```text
UNCHANGED
NEW
MODIFIED
DELETED
```

Only NEW and MODIFIED files should require structural re-extraction when parser/schema validity remains unchanged.

### 8.1 Modified files

For a modified source file:

1. invalidate entities and edges owned by the previous file state;
2. parse the new state;
3. rebuild affected relationships;
4. resolve cross-file relationships affected by the delta;
5. preserve unrelated graph state.

### 8.2 Deleted files

For a deleted file:

1. remove owned nodes;
2. remove invalid edges;
3. remove invalid source-to-test mappings;
4. mark Project Brain evidence pointing to removed source as requiring revalidation.

### 8.3 Atomicity

The manifest and graph must only replace the previous usable state after successful processing.

A failed refresh must not corrupt the last valid structural graph.

---

## 9. Structural query engine

Add an internal graph query surface.

Minimum operations:

```text
find-symbol
neighbors
callers
callees
dependents
dependencies
tests-for
path
impact
```

Conceptual examples:

```text
Who calls refreshToken?
What tests exercise AuthService?
What depends on SessionRepository?
What structural path connects CheckoutController to PaymentGateway?
```

These are engine capabilities first. They do not replace `@Codemium` as the primary product UX.

A diagnostic CLI may expose them for development, fixtures, and troubleshooting.

---

## 10. Working Set Engine v2

Working Set selection becomes **graph-assisted**, not graph-exclusive.

Preferred retrieval order:

```text
1. Active Task Contract
2. Relevant Project Brain knowledge
3. Task seed symbols/files
4. Structural neighbors
5. Relevant interfaces/dependencies
6. Relevant tests
7. Exact source regions
8. Additional graph expansion only when uncertainty remains
```

Task terms remain useful for seed discovery. After seeds are identified, relationship traversal becomes a primary relevance signal.

Example:

```text
Task:
Fix refresh-token race condition

Seed:
refreshToken

Graph expansion:
refreshToken
→ SessionService
→ TokenRepository
→ AuthController
→ refresh-token tests

Project Brain:
known auth constraint
known mobile compatibility decision
known previous refresh bug
```

The resulting Working Set should be smaller and more behaviorally relevant than broad repository search.

---

## 11. Context budgeting

Graph traversal must remain bounded.

Default traversal guidance:

```text
FAST       depth 0-1
NORMAL     depth 1
DEEP       depth 1-2
CRITICAL   risk-driven, normally <= 2
```

Depth is not the only limit.

Working Set construction should also enforce:

- maximum files;
- maximum graph nodes;
- maximum Project Brain entries;
- relevance threshold;
- relationship priority;
- source-region budget where practical.

Graph expansion beyond the normal budget requires a named unresolved question or risk.

---

## 12. Source remains authoritative

Structural Intelligence is a navigation and reasoning aid.

It is not a replacement for reading relevant source.

For a code change:

```text
Graph says where to inspect.
Source says what is actually true.
Tests/runtime evidence say whether the result works.
```

Codemium must not block all raw source reads merely to force graph usage.

It should instead avoid unnecessary raw reads when the graph already resolves navigation or dependency questions.

---

## 13. Project Brain evidence model

New Project Brain captures should support structured evidence.

Example:

```json
{
  "kind": "constraint",
  "text": "Token rotation requires a five-second grace period.",
  "evidence": [
    {
      "path": "src/auth/token_service.ts",
      "symbol": "TokenService.rotate",
      "graph_node_id": "symbol:src/auth/token_service.ts#TokenService.rotate",
      "content_hash": "...",
      "line_start": 84,
      "line_end": 116
    }
  ]
}
```

Existing legacy `source` values remain readable for backwards compatibility.

New entries should prefer structured evidence when available.

Evidence must not contain secrets or raw sensitive runtime payloads.

---

## 14. Project Brain freshness

Durable knowledge must not be treated as permanently trustworthy merely because its registry status is ACTIVE.

Introduce freshness states:

```text
FRESH
NEEDS_REVALIDATION
SUPERSEDED
UNKNOWN
```

### FRESH

Supporting source identity remains valid.

### NEEDS_REVALIDATION

One or more supporting source fingerprints or structural entities changed.

The knowledge may still be correct but must not be blindly trusted for a material decision.

### SUPERSEDED

A later verified Project Brain entry explicitly replaces it.

### UNKNOWN

Legacy entry or insufficient evidence prevents deterministic freshness evaluation.

Changing source must not automatically delete Project Brain history.

It invalidates confidence, not history.

---

## 15. Knowledge revalidation

When relevant Project Brain knowledge is `NEEDS_REVALIDATION`:

1. include it as historical context;
2. identify changed supporting evidence;
3. inspect the smallest necessary source region;
4. determine whether the fact remains valid;
5. refresh evidence if still valid;
6. supersede or amend it if materially changed.

The intended doctrine is:

> **Remember aggressively, trust conditionally.**

---

## 16. Change Impact Engine v2

Impact analysis moves from primarily filename/import heuristics to provenance-aware graph traversal.

Given changed files or symbols, classify impact as:

```text
DIRECT
TRANSITIVE
INTERFACE
TEST
```

Example:

```text
Changed:
TokenRepository.rotate()

Direct:
AuthService.refresh()

Transitive:
AuthController.refreshEndpoint()

Interface:
RefreshToken API behavior

Tests:
auth-refresh.integration.test.ts
mobile-token-compat.test.ts
```

Impact output must expose the evidence path that caused a dependent to be selected.

---

## 17. Blast radius

Blast radius must not be based primarily on changed-file count or high-risk keywords.

Signals should include:

- number of direct dependents;
- transitive dependency reach;
- public interface involvement;
- authentication/authorization or other trust-boundary involvement;
- database/schema involvement;
- worker/event/queue involvement;
- Project Brain constraints;
- relevant known bugs;
- test coverage and test relationships.

Blast radius remains an explainable risk classification, not fake numerical certainty.

Graph-derived risk may escalate the minimum safe task depth. It must never lower an already justified safety floor.

---

## 18. Test Intelligence v2

Source-to-test relationships should increasingly come from structural evidence.

Priority order:

```text
1. direct imports/references
2. observed symbol relationships
3. project test configuration
4. naming/location conventions
5. fallback heuristic
```

Every mapping should expose provenance.

Example:

```json
{
  "source": "src/auth/token_service.ts",
  "test": "tests/auth/token_service.test.ts",
  "confidence": "DIRECT"
}
```

Existing heuristic mapping remains available as fallback.

---

## 19. Scope Guard integration

Structural Intelligence may strengthen Scope Guard explanations.

For each changed file, Codemium should preferably be able to attribute the change to:

```text
DIRECT
DEPENDENCY
TEST
CLEANUP
```

with a structural or task reason.

Example:

```text
src/auth/controller.ts
DIRECT — requested behavior

src/auth/token_service.ts
DEPENDENCY — AuthController.refresh calls TokenService.rotate

tests/auth/refresh.test.ts
TEST — structurally related verification
```

Structural distance alone never authorizes opportunistic cleanup.

---

## 20. Task-depth integration

Structural evidence may raise the minimum safe engineering depth.

Examples:

```text
Task appears local,
but affected path crosses authorization boundary
→ CRITICAL floor may apply.

Task changes one helper,
but helper has many callers across multiple subsystems
→ DEEP may apply.
```

Graph signals may escalate safety. They must never weaken it.

---

## 21. Health and doctor diagnostics

Codemium health diagnostics must report Structural Intelligence status.

Minimum diagnostics:

```text
graph schema version
graph freshness
file coverage
language coverage
parser capability
DIRECT / RESOLVED / HEURISTIC edge counts
unresolved imports/references
Project Brain entries needing revalidation
```

Doctor must not report structural intelligence as healthy when the graph is stale, corrupted, or materially degraded without stating the limitation.

---

## 22. Failure and degradation policy

Structural Intelligence is an enhancement layer, not a single point of failure.

If the graph is missing, corrupt, stale beyond safe use, or unable to parse a language, Codemium must:

1. report degraded capability;
2. fall back to existing repository discovery;
3. preserve correctness and safety;
4. never fabricate structural relationships;
5. continue normal engineering work when safely possible.

---

## 23. Storage policy

Maintain conceptual separation:

```text
.codemium/
├── PROJECT.md
├── architecture/
├── registry/             durable Project Brain
│
├── repository/           derived structural state
│   ├── graph.json
│   ├── manifest.json
│   └── tests.json
│
├── tasks/
└── runtime/
```

`repository/` remains regenerable state.

It must not become the canonical durable knowledge store.

Project Brain remains the portable engineering memory.

---

## 24. Backwards compatibility

v0.7 must preserve existing v0.6 Project Brain data.

Legacy entries using `source` remain readable.

New readers support both:

```text
source
evidence[]
```

Because repository structural data is derived, graph schema v1 does not require a complex durable migration.

When incompatible:

```text
discard derived graph
rebuild graph v2
```

Never rewrite durable Project Brain merely to migrate a regenerable graph.

---

## 25. Performance requirements

Repository structural operations remain local and deterministic by default.

Requirements:

- no LLM call is required to build the Structural Graph;
- unchanged files are not unnecessarily reparsed;
- after initialization, refresh cost should roughly follow changed repository surface rather than total repository size;
- graph queries must be bounded;
- task startup must not introduce uncontrolled full-repository work;
- failed refreshes preserve the previous valid graph;
- derived artifacts remain inspectable and reproducible.

Exact performance claims require benchmark evidence.

---

## 26. Benchmark requirements

v0.7 must add controlled fixtures and benchmark scenarios.

### 26.1 Repeated task discovery

Compare with and without Structural Intelligence:

```text
files inspected
search operations
context bytes or equivalent context footprint
relevant file recall
task correctness
```

### 26.2 Working Set precision

Known relevant files and tests should appear within the bounded Working Set without unnecessary repository expansion.

### 26.3 Impact recall

Fixtures with known dependency chains must produce expected direct and transitive impact.

### 26.4 Freshness

Changing supporting source must move relevant Project Brain knowledge to `NEEDS_REVALIDATION`.

### 26.5 Incremental rebuild

A second graph build without source changes should perform zero unnecessary source parsing.

### 26.6 Degraded mode

Removing enhanced parser capability must preserve safe fallback behavior.

No public efficiency percentage should be published until real agent runs satisfy Codemium's existing benchmark publication policy.

---

## 27. Functional requirements

Existing FR-001 through FR-019 from `PRD.md` remain applicable.

Add:

- **FR-020** — build an evidence-backed relational repository graph.
- **FR-021** — expose parser capability and relationship provenance.
- **FR-022** — update Structural Intelligence incrementally from content identity.
- **FR-023** — prune or replace invalid structural entities when source changes or is deleted.
- **FR-024** — query callers, dependencies, paths, tests, and related structural entities.
- **FR-025** — use structural relationships to improve bounded Working Set selection.
- **FR-026** — use structural relationships for Change Impact analysis.
- **FR-027** — derive test relationships from structural evidence where possible.
- **FR-028** — allow Project Brain entries to reference structured source evidence.
- **FR-029** — detect when evidence supporting reusable knowledge has changed.
- **FR-030** — require revalidation before stale durable knowledge is trusted for material decisions.
- **FR-031** — preserve source code as authority over derived graph state.
- **FR-032** — degrade safely when enhanced structural analysis is unavailable.
- **FR-033** — surface Structural Intelligence coverage and freshness through health/doctor diagnostics.
- **FR-034** — keep Structural Intelligence local, deterministic, and LLM-free by default.
- **FR-035** — maintain backwards compatibility with v0.6 Project Brain entries.

---

## 28. Explicit non-goals for v0.7

v0.7 will not become a general-purpose knowledge-graph product.

Do not implement as part of this release unless required by a later approved PRD revision:

- graph visualization product/UI;
- PDF knowledge graph;
- image/video/audio ingestion;
- vector database or embeddings infrastructure;
- LLM-generated structural relationships;
- fuzzy semantic symbol deduplication;
- generic GraphRAG product;
- shared hosted graph server;
- multi-repository enterprise graph;
- replacing Project Brain with the Structural Graph;
- blocking all direct source inspection;
- automatic architecture rewriting;
- autonomous unrelated cleanup.

These exclusions are intentional product-boundary decisions, not missing acceptance criteria.

---

## 29. Future candidates — v0.8+

After v0.7 Structural Intelligence is proven, evaluate separately:

### Architectural communities

Detect naturally connected subsystems and important hubs for large repositories.

### Deterministic file/module synopsis

Provide bounded local summaries that help agents decide whether a source read is necessary.

### PR impact intelligence

Show which structural regions, interfaces, tests, and Project Brain constraints a pull request touches.

### Cross-PR conflict intelligence

Detect independent PRs affecting the same structural subsystem or interface boundary.

### Architecture drift

Compare observed repository structure against Project Brain architecture boundaries.

### Team-shared derived intelligence

Optionally share structural artifacts once reproducibility, schema compatibility, and merge behavior are proven.

None of these candidates may block v0.7.

---

## 30. Implementation phases

### Phase 1 — Structural Foundation

Deliver:

- graph schema v2;
- stable node IDs;
- relationship provenance;
- parser capability model;
- incremental manifest;
- atomic refresh;
- changed/deleted-file invalidation.

Gate:

Repository graph fixtures pass deterministically and fallback parsing remains safe.

### Phase 2 — Query and Working Set

Deliver:

- graph query primitives;
- seed resolution;
- bounded traversal;
- Working Set v2;
- fallback behavior.

Gate:

Known task fixtures retrieve expected files without uncontrolled context expansion.

### Phase 3 — Impact and Test Intelligence

Deliver:

- reverse dependency traversal;
- provenance-aware graph impact;
- improved test mapping;
- verification recommendations.

Gate:

Known dependency fixtures produce correct affected surfaces and relevant tests.

### Phase 4 — Evidence Bridge

Deliver:

- structured Project Brain evidence;
- evidence fingerprints;
- freshness states;
- revalidation workflow;
- legacy compatibility.

Gate:

Source changes deterministically invalidate confidence in relevant reusable knowledge without deleting history.

### Phase 5 — Integration and Release Hardening

Deliver:

- Scope Guard integration;
- depth-escalation signals;
- doctor/health coverage;
- cross-host packaging validation;
- degraded mode tests;
- benchmark fixtures;
- documentation alignment.

Gate:

All supported hosts preserve existing Codemium UX and safety invariants.

---

## 31. Release acceptance criteria

Codemium v0.7 is complete only when all of the following are true:

1. `repository/graph.json` models real repository relationships rather than only file inventory.
2. Every graph relationship exposes provenance.
3. Parser coverage and capability are reported honestly.
4. Unchanged files are not unnecessarily reprocessed.
5. Deleted or modified source cannot leave silently valid obsolete graph entities.
6. Working Set generation demonstrably consumes graph relationships.
7. Change Impact can traverse reverse dependencies.
8. Test selection uses structural evidence before heuristic naming when evidence exists.
9. New Project Brain entries can carry structured source evidence.
10. Changed evidence causes relevant Project Brain knowledge to require revalidation.
11. Historical Project Brain knowledge is preserved rather than silently deleted.
12. Source remains the final authority for engineering decisions.
13. Graph failures degrade to existing Codemium discovery instead of blocking safe work.
14. No LLM is required to construct the Structural Graph.
15. Normal users do not need a new initialization ceremony.
16. `@Codemium` remains the primary Codex UX.
17. Claude Code, Gemini CLI, Cursor, and OpenCode preserve shared engineering semantics.
18. Doctor reports parser coverage, graph freshness, and stale knowledge correctly.
19. CI includes deterministic structural, incremental, impact, freshness, compatibility, and fallback fixtures.
20. README, PRD, INSTALL, HOSTS, and CHANGELOG must be aligned before v0.7 is declared released.
21. Public performance claims remain evidence-gated.

---

## 32. Implementation discipline for Codex

When implementing this PRD, Codex must:

1. inspect the existing engine before designing replacements;
2. preserve existing behavior unless the PRD requires a change;
3. extend the canonical engine rather than creating a parallel architecture;
4. prefer deterministic local analysis over model calls;
5. reuse current `.codemium/` storage semantics where compatible;
6. keep derived repository state separate from durable Project Brain state;
7. make schema changes explicit and versioned;
8. preserve safe fallback behavior;
9. add tests before claiming a phase complete;
10. update docs only when implementation behavior is actually true;
11. avoid Graphify-specific product features that are explicit v0.7 non-goals;
12. keep changes phase-scoped and stop when the current phase gates are proven.

Codex should treat this PRD as requirements, not as permission to rewrite the repository wholesale.

---

## 33. Strategic outcome

Before v0.7:

```text
Codemium remembers what the agent learned.
```

After v0.7:

```text
Codemium understands enough repository structure
to know where knowledge belongs,
what a change can affect,
what should be loaded,
what should be tested,
and when old knowledge can no longer be trusted.
```

The intended long-term moat is the combination of:

```text
Structural Intelligence
        +
Persistent Engineering Memory
        +
Evidence Freshness
        +
Bounded Context
        +
Impact Intelligence
        +
Scope Discipline
        +
Risk-Aware Verification
```

That combination, rather than a generic knowledge graph, remains the defining Codemium architecture.
