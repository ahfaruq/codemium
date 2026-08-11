# Codemium v0.7 Product Requirements Document

## Structural Intelligence & Evidence Bridge

**Status:** Implemented and CI-validated  
**Release:** v0.7.0  
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

Codemium v0.6 already contained Repository Intelligence, Working Set generation, impact analysis, test mapping, deterministic caching, and Project Brain. However, the repository model was intentionally lightweight.

A file/symbol/import inventory could not reliably model enough structure to answer questions such as:

```text
A calls B.
B implements C.
D references A.
Test X exercises A.
Changing B can affect E through C.
Project Brain fact P was learned from symbol A.
Symbol A changed after fact P was captured.
```

That limited Working Set precision, impact recall, test discovery, and the ability to know whether old durable knowledge was still safe to reuse.

---

## 4. v0.7 north-star outcome

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

Efficiency gains do not count if correctness, source authority, safety, or verification quality decreases.

---

## 5. Dual Intelligence Model

### 5.1 Structural Intelligence

Derived mechanically from the repository and stored under `.codemium/repository/`.

Characteristics:

- deterministic wherever practical;
- local and LLM-free by default;
- regenerable;
- source-backed;
- freshness-aware;
- cheaper than repeated broad source discovery.

### 5.2 Engineering Intelligence

Stored in Project Brain.

Characteristics:

- learned through engineering work;
- durable;
- concise;
- evidence-backed;
- reusable across tasks;
- may contain engineering facts that syntax alone cannot derive.

Examples include compatibility constraints, prior root causes, contractual interface behavior, deliberate architectural decisions, and material known risks.

### 5.3 Evidence Bridge

Project Brain entries may reference Structural Graph entities and source fingerprints so Codemium can answer:

```text
What source established this fact?
Does that source still exist?
Has the implementation changed?
Is this knowledge still safe to reuse?
```

---

## 6. Repository Structural Graph v2

`repository/graph.json` is a true relational repository model while retaining backwards-compatible file inventory data where useful.

### 6.1 Node types

Required graph node classes:

```text
FILE
TEST
MODULE
SYMBOL
```

Symbol subtype coverage depends on parser capability and may include functions, methods, classes, interfaces/types, enums, constants, tables, routes, or future deterministically supported entities.

### 6.2 Relationships

Governed relationship vocabulary:

```text
DEFINES
CONTAINS
IMPORTS
CALLS
REFERENCES
INHERITS
IMPLEMENTS
TESTS
DEPENDS_ON
```

### 6.3 Stable identity

Symbol identity must not depend solely on line number. v0.7 uses repository-relative path plus qualified symbol identity/kind so line movement does not automatically create unrelated entities.

### 6.4 Relationship provenance

Every relationship exposes how Codemium knows it:

- **DIRECT** — observed directly by deterministic parsing;
- **RESOLVED** — derived deterministically by symbol/import resolution;
- **HEURISTIC** — deterministic fallback evidence with lower trust.

HEURISTIC relationships must never be presented as DIRECT source evidence.

---

## 7. Parser capability model

Codemium must not pretend all languages receive identical structural coverage.

Each file records parser identity and capability coverage.

v0.7 ships:

- `python-ast` — Python standard-library AST extraction for symbols/imports/calls/references/inheritance;
- `fallback-regex` — deterministic partial coverage for supported languages when deeper parsing is unavailable.

The fallback is degraded capability, not fake parity.

No LLM or remote API is required to construct Structural Intelligence.

---

## 8. Incremental Structural Intelligence

Repository graph maintenance is delta-first.

`repository/manifest.json` records at least:

```text
path
content hash
parser identity
parser version
graph schema version
```

Files are classified as:

```text
UNCHANGED
NEW
MODIFIED
DELETED
```

Behavior:

- UNCHANGED files reuse prior deterministic extraction;
- NEW/MODIFIED files are parsed;
- entities/edges owned by deleted or prior modified source cannot remain silently valid;
- deleted-source entities are pruned;
- manifest state is written after a successful graph build so a failed refresh does not advertise invalid freshness.

---

## 9. Graph query engine

Codemium exposes bounded internal/diagnostic structural queries:

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

These operations strengthen the Codemium engine. They do not replace `@Codemium` as the product UX.

---

## 10. Working Set Engine v2

Working Sets are graph-assisted, not graph-exclusive.

Preferred retrieval order:

```text
1. Active Task Contract
2. Relevant freshness-qualified Project Brain knowledge
3. Task seed symbols/files
4. Structural neighbors
5. Relevant interfaces/dependencies
6. Relevant tests
7. Exact source regions
8. Additional evidence only for named uncertainty
```

Task terms remain useful for seed discovery. Once seeds exist, bounded structural traversal becomes a primary relevance signal.

Graph expansion remains bounded by task depth, maximum nodes/files, and relationship relevance. Structural distance alone never authorizes unrelated work.

---

## 11. Source remains authoritative

Structural Intelligence narrows navigation and impact hypotheses. It never replaces relevant source reads for material implementation claims or edits.

```text
Graph         → where to inspect / what may be affected
Source        → implementation truth
Tests/runtime → behavioral proof
Project Brain → durable engineering knowledge, freshness-qualified
```

If the graph is absent, stale, corrupt, or incomplete for a language, Codemium degrades to normal repository tools rather than fabricating structure.

---

## 12. Project Brain evidence model

New durable Project Brain entries can carry structured evidence:

```json
{
  "kind": "constraint",
  "text": "Token rotation requires a grace period.",
  "evidence": [
    {
      "path": "src/auth/token_service.py",
      "symbol": "TokenService.rotate",
      "graph_node_id": "symbol:src/auth/token_service.py#TokenService.rotate:method",
      "content_hash": "...",
      "line_start": 84,
      "line_end": 116
    }
  ]
}
```

Legacy `source` fields remain readable for v0.6 compatibility and may be normalized into structured evidence when a safe repository-relative file can be identified.

---

## 13. Project Brain Freshness

Durable knowledge is no longer treated as eternally valid simply because the registry entry remains ACTIVE.

Freshness states:

```text
FRESH
NEEDS_REVALIDATION
SUPERSEDED
UNKNOWN
```

- **FRESH** — supporting evidence still matches source identity.
- **NEEDS_REVALIDATION** — one or more supporting sources changed/disappeared. The entry remains historical context but must not be blindly trusted.
- **SUPERSEDED** — later verified knowledge replaces it while preserving history.
- **UNKNOWN** — legacy or insufficient evidence prevents deterministic freshness evaluation.

Source changes invalidate confidence, not history.

### Revalidation

For relevant `NEEDS_REVALIDATION` or `UNKNOWN` knowledge:

1. retain the historical entry;
2. inspect the smallest necessary supporting source;
3. determine whether the fact remains valid;
4. refresh evidence if valid;
5. supersede it if materially changed.

> **Remember aggressively, trust conditionally.**

---

## 14. Change Impact Engine v2

Impact analysis uses structural traversal before fallback heuristics.

Given changed files/symbols, Codemium identifies direct/transitive dependents, relationship evidence, distance, related tests, and risk signals.

Blast radius may consider:

- direct dependent count;
- transitive dependency depth;
- high-risk domains/trust boundaries;
- public/interface/database/background-worker surfaces where observable;
- Project Brain constraints/known risks;
- mapped tests.

Blast radius remains a risk classification, not fake mathematical certainty.

---

## 15. Test Intelligence v2

Test mapping preference:

```text
1. structural TESTS relationships
2. resolved source/symbol relationships
3. deterministic project conventions
4. naming/import fallback marked HEURISTIC
```

Every relationship must expose provenance rather than presenting fallback naming as direct test coverage.

---

## 16. Scope Guard and task depth integration

Structural Working Set evidence can explain why a changed file is DIRECT, DEPENDENCY, or TEST scope. It cannot justify opportunistic cleanup.

Structural risk can raise safe engineering depth, for example when a seemingly small task reaches an authentication/payment boundary or has broad dependency fan-in. Structural signals never lower an existing safety floor.

---

## 17. Health and doctor

Health/doctor diagnostics expose at least:

```text
graph schema version
graph freshness vs repository/worktree
file/parser coverage
parser capabilities
DIRECT / RESOLVED / HEURISTIC edge counts
unresolved relationships
incremental refresh summary
Project Brain freshness counts
```

Doctor must not claim Structural Intelligence is healthy when graph state is missing/degraded/stale.

---

## 18. Failure and degradation policy

Structural Intelligence is an enhancement layer, not a single point of failure.

If the graph is missing, corrupt, cannot parse a language deeply, or cannot be refreshed safely, Codemium must:

1. report degraded capability when diagnostics are requested;
2. fall back to existing repository discovery;
3. preserve correctness/source authority;
4. never fabricate a graph relationship.

---

## 19. Storage policy

```text
.codemium/
├── PROJECT.md
├── architecture/
├── registry/             durable Project Brain
├── repository/           derived structural state
│   ├── graph.json
│   ├── manifest.json
│   └── tests.json
├── tasks/                transient task state
└── runtime/              transient cache/gate/telemetry
```

`repository/` remains regenerable structural state. It is not the canonical durable knowledge store.

---

## 20. Backwards compatibility

v0.7 preserves v0.6 Project Brain data.

- legacy registry entries remain readable;
- legacy `source` metadata remains valid input;
- structured `evidence[]` is additive;
- incompatible graph schemas may be discarded/rebuilt because structural state is derived;
- durable Project Brain must never be destructively rewritten merely to migrate a regenerable graph.

---

## 21. Performance policy

Structural graph operations are local and deterministic by default.

- unchanged files should not be reparsed unnecessarily;
- no LLM call is required to build the structural graph;
- update cost should follow changed repository surface after initialization where practical;
- graph queries and Working Set expansion remain bounded;
- failed refresh must not silently advertise an invalid successful manifest.

Exact performance claims require benchmark evidence.

---

## 22. Benchmark requirements

v0.7 fixtures/benchmarks should measure or verify:

- repeated task discovery behavior;
- Working Set retrieval of known relevant source/tests;
- structural impact recall on known dependency chains;
- evidence freshness after supporting-source change;
- incremental no-op rebuild behavior;
- safe degraded fallback behavior.

No public efficiency percentage is publishable merely because synthetic fixtures pass. Codemium's existing evidence-gated benchmark policy remains authoritative.

---

## 23. Functional requirements

Existing FR-001 through FR-019 remain applicable.

- **FR-020** — build an evidence-backed relational repository graph.
- **FR-021** — expose parser capability and relationship provenance.
- **FR-022** — update Structural Intelligence incrementally from content identity.
- **FR-023** — prune invalid structural entities when source is changed or deleted.
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

## 24. Non-goals for v0.7

v0.7 is not a general-purpose knowledge graph platform.

Explicit non-goals:

- graph visualization product;
- PDF/image/video/audio knowledge-graph ingestion;
- vector database;
- embedding infrastructure;
- generic GraphRAG product;
- LLM-generated structural relationships;
- fuzzy semantic symbol deduplication;
- shared hosted graph server;
- replacing Project Brain with a graph;
- blocking all direct source inspection;
- autonomous unrelated cleanup.

---

## 25. Implementation mapping

v0.7 implementation extends the canonical core rather than creating a parallel subsystem.

Primary modules:

```text
plugins/codemium/engine/repo_graph.py
    Structural Graph v2, parser capability, provenance, manifest/incremental refresh

plugins/codemium/engine/graph_query.py
    bounded structural query and traversal primitives

plugins/codemium/engine/working_set.py
    graph-assisted bounded Working Sets

plugins/codemium/engine/impact.py
    structural reverse impact and verification recommendation

plugins/codemium/engine/test_map.py
    provenance-aware structural/fallback test mapping

plugins/codemium/engine/project_brain.py
    structured evidence, freshness, revalidation, v0.6 compatibility

plugins/codemium/engine/task_compiler.py
    structural-risk depth escalation

plugins/codemium/engine/scope_guard.py
    structural scope explanations

plugins/codemium/engine/health.py
scripts/doctor.py
    Structural Intelligence + Project Brain freshness diagnostics
```

Agent contracts under Codex and the shared portable `cm` skill explicitly preserve source authority and freshness-qualified memory reuse.

---

## 26. Verification implementation

v0.7 core fixtures exercise:

- Python AST extraction;
- deterministic fallback parser reporting;
- Structural Graph v2 nodes/edges/provenance;
- zero unnecessary parsing on an unchanged second build;
- modified-file incremental parsing;
- deleted-source pruning;
- callers/path/query primitives;
- graph-assisted Working Set selection;
- structural test mapping;
- reverse dependency impact;
- Project Brain structured capture/deduplication;
- source-change `NEEDS_REVALIDATION` behavior;
- deterministic revalidation back to `FRESH`;
- graph worktree freshness diagnostics;
- legacy automatic Project Brain initialization/capture behavior.

Repository PR CI validates the core fixture and Codex lifecycle contract independently. Full Linux/Windows host validation remains the release/manual verifier surface.

---

## 27. Release acceptance criteria

Codemium v0.7 is complete when:

1. `repository/graph.json` models real repository relationships rather than only file inventory.
2. Every graph relationship identifies its evidence/provenance class.
3. Parser capability is visible and partial coverage is not disguised as full coverage.
4. Unchanged files are not unnecessarily reprocessed.
5. Deleted or modified source cannot leave silently valid obsolete structural entities.
6. Working Set generation consumes graph relationships.
7. Change Impact can traverse reverse dependencies.
8. Test selection uses structural evidence before heuristic naming when available.
9. New Project Brain entries can carry structured source evidence.
10. Changed supporting evidence causes relevant Project Brain knowledge to require revalidation.
11. Historical Project Brain knowledge is preserved rather than silently deleted.
12. Revalidation can refresh a still-valid durable fact.
13. Source remains the final authority for engineering decisions.
14. Graph failures/partial coverage degrade to normal repository discovery instead of blocking safe work.
15. No LLM is required to construct Structural Intelligence.
16. Normal users do not need a new initialization ceremony.
17. `@Codemium` remains the primary Codex UX.
18. Claude Code, Gemini CLI, Cursor, and OpenCode preserve the same engineering semantics through the shared core/skill contract.
19. Doctor/health report structural coverage/freshness and stale Project Brain knowledge correctly.
20. CI includes deterministic structural, incremental, impact, freshness, compatibility, and fallback fixtures.
21. README, PRD, INSTALL, HOSTS, CHANGELOG, VERSION, and adapter manifests agree on v0.7 behavior/version.
22. Public performance claims remain evidence-gated.
23. Explicit v0.7 non-goals remain out of scope.

---

## 28. Implemented release state

v0.7.0 satisfies the architectural intent of this PRD through a local deterministic Structural Graph, graph-assisted task/impact/test intelligence, and a Project Brain Evidence Bridge.

The implementation deliberately chooses a pragmatic parser-capability floor for the first release: Python receives AST-backed structural extraction while other currently supported languages retain deterministic partial fallback coverage. The capability is surfaced honestly rather than hidden behind a universal-parser claim.

Repository CI validates the host-agnostic core and the Codex lifecycle contract. No benchmark or token-efficiency claim is implied by those CI results.

---

## 29. Strategic outcome

Before v0.7:

```text
Codemium remembers what the agent learned.
```

After v0.7:

```text
Codemium also understands enough repository structure
 to know where knowledge belongs,
 what a change can affect,
 what should be loaded,
 what should be tested,
 and when old knowledge can no longer be trusted.
```

The long-term moat is the combination of:

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

That combination remains the defining Codemium architecture.
