# Codemium Product Requirements Document

## Product definition

Codemium is a **host-agnostic persistent coding-intelligence layer** for AI coding agents. It makes an agent behave increasingly like an engineer who has worked on the same repository for months: durable project knowledge is reused when still valid, repository structure is mapped deterministically, only the relevant project slice is activated for each task, changes stay scoped, testing follows risk, and unchanged understanding is not repeatedly paid for.

Codemium is not a wrapper around one vendor, model family, or prompt syntax. OpenAI Codex is the reference adapter; Claude Code, Gemini CLI, Cursor, OpenCode, and future hosts consume the same engineering contract through host-native surfaces.

The normative v0.7 extension is [`PRD-v0.7.md`](PRD-v0.7.md).

## North-star outcome

As project complexity grows:

```text
Durable project knowledge        ↑↑↑
Structural project understanding ↑↑↑
Project understanding            ↑↑
Correctness                      >= baseline
Architecture consistency         >= baseline

Active task context              bounded
Repeated discovery               ↓↓↓
Stale knowledge reuse            ↓↓↓
Unrelated changes                → 0
Token/context waste              ↓↓↓
```

Resource efficiency only counts as a win after correctness, security, testing adequacy, architecture consistency, source authority, and scope integrity meet the quality floor.

## Positioning

> **The senior engineer who already knows your codebase.**

Codemium optimizes **minimum justified engineering**, not minimum LOC.

## Dual intelligence model

Codemium keeps two different kinds of project intelligence connected but intentionally separate:

```text
                         CODEMIUM CORE
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
   Structural Intelligence                 Project Brain
     derived/regenerable             durable engineering memory
            │                                   │
            └────────── Evidence Bridge ─────────┘
                              │
                              ▼
                         Working Set
                              │
                     Impact / Verification
```

**Structural Intelligence** describes what the repository currently contains: files, modules, symbols, calls, imports, references, inheritance, dependencies, and test relationships where deterministic parser capability permits.

**Project Brain** stores concise durable engineering knowledge: decisions, constraints, interfaces, patterns, known bugs/root causes, and material risks learned through verified engineering work.

The repository remains the source of implementation truth. Tests/runtime evidence remain the source of behavioral proof. The graph guides navigation and impact; Project Brain carries freshness-qualified durable knowledge.

## Host architecture

```text
                         CODEMIUM CORE
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
     Project Brain     Structural/Task Core   Shared Policy
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
        ┌───────────┬─────────┼─────────┬───────────┐
        │           │         │         │           │
      Codex       Claude    Gemini    Cursor     OpenCode
        │           │         │         │           │
  @Codemium  /codemium:cm    /cm       /cm      cm skill
```

A host adapter may change invocation syntax, plugin/extension layout, model controls, and tool plumbing. It must not fork Codemium's durable project-state semantics, structural provenance semantics, freshness semantics, or safety invariants.

## Supported-host policy

- **Stable**: host integration is the reference implementation and exercised by repository fixtures plus actual-host validation for the release line.
- **Beta**: packaging follows the host's documented native surface and repository CI validates the bundle, but actual-host runtime validation is still required before Stable promotion.
- **Planned**: no installable adapter should be advertised as working.

Current release target:

| Host | Status | Primary invocation |
| --- | --- | --- |
| OpenAI Codex | Stable | `@Codemium` |
| Claude Code | Beta | `/codemium:cm` or skill auto-selection |
| Gemini CLI | Beta | `/cm` |
| Cursor | Beta | `/cm` / Agent Skill UI |
| OpenCode | Beta | skill tool/auto-selection, `/cm` where exposed |

## User experience

Codemium should expose the most natural host-level identity available. On OpenAI Codex, the primary product UX is the installed plugin mention **`@Codemium`**. The portable internal Agent Skill identifier remains **`cm`** for direct skill invocation and non-plugin hosts.

Typical Codex usage should be natural language:

```text
@Codemium review this repository before making changes
@Codemium fix the profile save bug
@Codemium deeply investigate this intermittent queue failure
@Codemium safely change this authentication flow and verify the impact
```

Codemium automatically classifies the task and selects the smallest safe depth. Users should not need to learn internal task/depth syntax for ordinary use, initialize Project Brain manually, or manually build the repository graph before normal tasks. Structural risk may escalate but never lower the safety floor.

Advanced direct skill invocation remains available:

```text
$cm
$cm fast
$cm deep
$cm critical
```

Other hosts retain their native surfaces:

- Codex: `@Codemium ...` primary; `$cm ...` direct Agent Skill fallback.
- Claude Code: `/codemium:cm ...`.
- Gemini CLI: `/cm ...`.
- Cursor: `/cm` where the Agent Skill slash UI is available.
- OpenCode: native skill loading; slash exposure when supported.

## Task axis

Codemium classifies work as:

- BUILD
- FIX
- TEST
- REFACTOR
- REVIEW
- MIGRATION
- SECURITY

Task type changes engineering policy, not just wording.

## Depth axis

- **FAST** — narrow, obvious, localized, low-risk work.
- **NORMAL** — ordinary project-aware engineering.
- **DEEP** — complex, intermittent, concurrent, distributed, performance-sensitive, cross-boundary, broad-dependency, or materially uncertain work.
- **CRITICAL** — trust-boundary/security, authentication/authorization, payments, migrations, secrets, production data, destructive operations, deployment/infrastructure, or breaking public interfaces.

A user override may increase depth but cannot lower the minimum safe depth. Structural blast-radius evidence may raise the minimum safe depth.

## Portable reasoning classes

| Depth | Preferred class | Minimum class |
| --- | --- | --- |
| FAST | economy | economy |
| NORMAL | balanced | economy |
| DEEP | strong | balanced |
| CRITICAL | frontier | strong |

Host adapters may map these classes only when the host exposes documented, safe, confirmable controls. The Codex adapter currently maps economy/balanced/strong/frontier to `low`/`medium`/`high`/`xhigh` when supported. Other adapters must not invent equivalent vendor controls.

# Project Brain

Codemium durable state lives in:

```text
.codemium/
```

Durable Project Brain content may include:

- Project Charter;
- architecture boundaries;
- Decision Ledger;
- Constraint Registry;
- Interface Registry;
- Pattern Registry;
- Known Bug Registry.

Derived repository/test intelligence, active task contracts, and runtime/cache/gate state use the same namespace but remain transient/regenerable rather than durable engineering memory.

Project Brain is not a conversation transcript and must not store secrets.

## Automatic lifecycle

Project Brain is a default runtime capability, not an opt-in setup ceremony.

- On the first repository-bound Codemium task, initialize `.codemium/` automatically when it is missing and workspace-state writes are allowed.
- Do not require `$cm-init` before ordinary use.
- A source-code-only freeze such as “do not modify code” does not disable `.codemium/` bookkeeping. An explicit prohibition on **all** workspace/file/state changes must be respected.
- Read-only investigations and reviews may improve Project Brain while leaving source code untouched.
- At completion, source-backed facts that are durable enough to matter to future work must be captured or reused rather than left only in conversation context.

## Durable capture policy

Capture only concise, future-useful, evidence-backed:

- decisions;
- constraints;
- interfaces and important cross-component flows;
- established patterns;
- known bugs, root causes, and material risks.

Do not capture secrets, personal data, raw logs, temporary production snapshots, unverified hypotheses, tool/search history, or conversation transcripts. Equivalent ACTIVE entries should be reused rather than duplicated. If a task yields no durable fact, record none instead of inventing knowledge.

Before completion, persistence must be classified as one of: **captured**, **reused**, **none**, or **skipped by user constraint**.

## Evidence and freshness

New durable entries should prefer structured evidence when available:

```text
repository-relative path
symbol / graph node ID when available
content hash
source line range when available
```

Legacy `source` fields remain readable.

Freshness states:

- **FRESH** — supporting source identity remains valid;
- **NEEDS_REVALIDATION** — supporting source changed/disappeared; historical context only until verified;
- **SUPERSEDED** — later verified knowledge replaces the entry while history is retained;
- **UNKNOWN** — legacy/insufficient evidence; verify before material reliance.

Source change invalidates confidence, not history. Codemium must revalidate the smallest necessary evidence before relying materially on stale/unknown durable knowledge.

# Structural Intelligence

Repository Structural Intelligence is derived and regenerable under `.codemium/repository/`.

Structural Graph v2 models at least:

```text
FILE / TEST
MODULE
SYMBOL
```

with governed relationships:

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

Relationship provenance is mandatory:

- **DIRECT** — observed directly by a deterministic parser;
- **RESOLVED** — deterministically resolved from source structure/names;
- **HEURISTIC** — deterministic fallback evidence with lower trust.

Parser capability must be explicit. Python receives standard-library AST extraction in v0.7. Other supported languages may use deterministic fallback parsing and must not claim capabilities they do not provide.

No LLM is required to construct the Structural Graph.

## Incremental structural lifecycle

A manifest records source content identity, parser identity/version, and graph schema validity. Later builds classify files as unchanged/new/modified/deleted.

- unchanged files reuse prior extraction;
- new/modified files are parsed;
- deleted-source entities are pruned;
- previous valid graph state must not be silently corrupted by a failed refresh.

## Structural query surface

Internal/diagnostic operations include symbol discovery, neighbors, callers, callees, dependencies, dependents, test relationships, shortest paths, and impact traversal. These engine operations support `@Codemium`; they do not replace the public product UX.

## Source authority

Structural Intelligence is a navigation/reasoning aid, not implementation truth.

```text
Graph         → where to inspect and what may be affected
Source        → what implementation is actually true
Tests/runtime → whether behavior works
Project Brain → what verified engineering work learned, freshness-qualified
```

When structural state is unavailable or incomplete, Codemium degrades safely to normal repository tools and must never fabricate a relationship.

# Working Set Engine

Each task receives a bounded Working Set. Preferred retrieval order:

1. active task contract;
2. relevant freshness-qualified durable Project Brain facts;
3. task seed symbols/files;
4. bounded structural neighbors;
5. relevant interfaces/dependencies/tests;
6. exact candidate source regions;
7. deeper evidence only for a named unresolved question.

Context expansion is progressive and evidence-triggered. Graph depth/file/node budgets vary by engineering depth but remain bounded.

# Read-once / delta-first behavior

If an artifact's relevant state identity has not changed, reuse extracted understanding. When it changes, inspect the delta/changed symbols before rereading the whole artifact.

Equivalent deterministic reads, searches, graph extraction, and verification should be reused when validity is provable.

# Engineering doctrine

After understanding the actual requirement:

```text
need?
→ existing project solution?
→ standard library?
→ native framework/platform?
→ existing dependency?
→ local simple implementation?
→ new abstraction/dependency
```

A shorter diff is not automatically better. The winning change is the smallest change that is correct for the current architecture, interfaces, risk, and required testing.

# Scope Guard

Every changed hunk should be attributable to:

- DIRECT — requested behavior;
- DEPENDENCY — necessary supporting change;
- CLEANUP — code made obsolete specifically by this change;
- TEST — evidence for changed behavior.

Structural Working Set evidence may explain why a dependency/test file is in scope, but structural distance alone never authorizes unrelated work.

Default-disallowed opportunistic work includes unrelated formatting, adjacent refactoring, style modernization, unrelated renaming/comments, pre-existing dead-code deletion, and speculative architecture changes.

# Test Intelligence

Production-code minimalism never implies minimal tests.

Test selection prefers:

1. direct structural test/source relationships;
2. resolved symbol/source relationships;
3. project test configuration where available;
4. naming/location/import heuristics as an explicit HEURISTIC fallback.

Testing depth follows behavior surface, failure modes, boundaries, security/data risk, blast radius, historical regressions, and existing project patterns.

# Change Impact

Before completion, identify affected callers/dependents, interfaces, background workers/events, database/public surfaces, and relevant tests where practical.

v0.7 uses reverse structural dependency traversal where graph evidence exists, retains bounded transitive distance, and falls back honestly when structural state is unavailable. Blast radius informs verification depth; it is a risk classification, not fake mathematical certainty.

# Stop Engine

Stop when all required gates pass:

```text
objective satisfied
acceptance satisfied
verification sufficient
scope clean
architecture/security preserved
persistence obligation satisfied
freshness/revalidation obligation satisfied
material uncertainty resolved
required review complete
```

Additional inspection after these gates requires a named unresolved risk or persistence obligation that the next operation can reduce.

# Host adapter contract

Every supported adapter must preserve:

1. task classification;
2. safety-bounded depth;
3. shared `.codemium/` state;
4. automatic Project Brain initialization when state writes are allowed;
5. durable knowledge capture/reuse before completion;
6. evidence freshness before material knowledge reuse;
7. Structural Intelligence provenance/capability semantics when helpers are available;
8. source authority over derived graph state;
9. bounded graph-assisted context/working sets;
10. minimum justified engineering;
11. scope integrity;
12. risk-aware testing and structural impact where available;
13. deterministic reuse where valid;
14. explicit stop conditions;
15. honest host/model-control reporting;
16. safe degradation when structural helpers cannot run.

# Distribution architecture

### Codex

Codex plugin lives under `plugins/codemium/`, including the canonical deterministic engine and Agent Skills. The primary product invocation is `@Codemium`; direct `$cm` invocation remains available for advanced/compatibility use.

### Claude Code

The repository root is the Claude plugin root. `.claude-plugin/plugin.json`, `skills/cm/SKILL.md`, and `commands/cm.md` are auto-discovered. The same canonical engine remains available inside the installed plugin bundle.

### Gemini CLI

The repository root contains `gemini-extension.json`, `GEMINI.md`, and `commands/cm.toml`.

### Cursor / OpenCode

`scripts/install_host.py` copies the portable `SKILL.md`, canonical engine (including structural/evidence helpers), and references into the host's documented skill directory. It manages only Codemium-owned directories and refuses unrecognized overwrite/removal without explicit `--force`.

# Doctor / validation

`scripts/doctor.py` validates cross-host manifests, version synchronization, native invocation contracts, portable-skill packaging, and engine completeness. When `.codemium/` exists, health/doctor also reports graph schema/freshness, parser/capability coverage, relationship provenance, unresolved relationships, and Project Brain freshness.

Repository CI runs deterministic core and Codex lifecycle verification on pull requests/main. Full host validation remains manual/release-tag evidence.

# Functional requirements

Existing baseline requirements remain:

- FR-001 — initialize portable Project Brain automatically on first normal repository-bound task when state writes are allowed.
- FR-002 — build deterministic repository/test intelligence.
- FR-003 — compile task + safe depth contracts.
- FR-004 — generate bounded Working Sets.
- FR-005 — expand context only for material uncertainty.
- FR-006 — preserve/reuse unchanged understanding where identity is valid.
- FR-007 — enforce scoped diffs.
- FR-008 — map impact to sufficient verification.
- FR-009 — preserve architecture/constraint/interface knowledge.
- FR-010 — detect/avoid duplicate deterministic work.
- FR-011 — stop after sufficient proof.
- FR-012 — keep reasoning semantics model/vendor-independent.
- FR-013 — provide native Codex, Claude Code, Gemini CLI, Cursor, and OpenCode distribution surfaces.
- FR-014 — keep adapter versions synchronized with repository VERSION.
- FR-015 — provide safe install/uninstall for portable Agent Skill hosts.
- FR-016 — never claim host reasoning changes or token savings without evidence.
- FR-017 — expose `@Codemium` as the primary Codex plugin UX while preserving direct internal skill invocation.
- FR-018 — capture or reuse durable source-backed project knowledge before task completion when state writes are allowed.
- FR-019 — deduplicate equivalent ACTIVE Project Brain entries and never fabricate knowledge to satisfy persistence.

v0.7 requirements from [`PRD-v0.7.md`](PRD-v0.7.md):

- FR-020 — build an evidence-backed relational repository graph.
- FR-021 — expose parser capability and relationship provenance.
- FR-022 — update Structural Intelligence incrementally from content identity.
- FR-023 — prune invalid structural entities when source is changed or deleted.
- FR-024 — query callers, dependencies, paths, tests, and related structural entities.
- FR-025 — use structural relationships to improve bounded Working Set selection.
- FR-026 — use structural relationships for Change Impact analysis.
- FR-027 — derive test relationships from structural evidence where possible.
- FR-028 — allow Project Brain entries to reference structured source evidence.
- FR-029 — detect when evidence supporting reusable knowledge has changed.
- FR-030 — require revalidation before stale durable knowledge is trusted for material decisions.
- FR-031 — preserve source code as authority over derived graph state.
- FR-032 — degrade safely when enhanced structural analysis is unavailable.
- FR-033 — surface Structural Intelligence coverage and freshness through health/doctor diagnostics.
- FR-034 — keep Structural Intelligence local, deterministic, and LLM-free by default.
- FR-035 — maintain backwards compatibility with v0.6 Project Brain entries.

# Quality order

1. Safety and data integrity
2. Correctness
3. Architecture/interface consistency
4. Verification adequacy
5. Scope integrity
6. Context/token/latency efficiency
7. Code volume

Optimization that lowers a higher-ranked quality dimension is a failure.

# Benchmarking

The benchmark engine remains evidence-gated. Public efficiency claims require measured agent runs under controlled, comparable conditions and must not substitute synthetic/demo numbers for real performance.

Competitive/ablation data is not part of Codemium's public README until measured publication criteria are met.

# Non-goals

Codemium is not:

- a minimum-LOC contest;
- a license to under-test;
- a generic multi-agent bureaucracy;
- a replacement for CI;
- a promise that one model/reasoning level is best forever;
- a vendor-specific project-memory format;
- a reason to preload an entire repository;
- permission to edit unrelated code;
- a conversation-memory transcript disguised as project state;
- a generic graph visualization or GraphRAG product;
- a reason to add embeddings/vector infrastructure without evidence of need.

## v0.6 release definition

v0.6 established the multi-host foundation and deterministic Project Brain lifecycle:

- `@Codemium` as the primary installed Codex plugin invocation while retaining `$cm` as the direct skill path;
- automatic Project Brain initialization/capture when permitted;
- deterministic Codex persistence hooks and lightweight memory retrieval mode;
- canonical Project Brain state shared across Local and linked worktrees;
- Claude/Gemini/Cursor/OpenCode shared core packaging;
- vendor-neutral reasoning classes and evidence-gated benchmark policy.

## v0.7 release definition — Structural Intelligence & Evidence Bridge

v0.7 is complete when the implementation and verification satisfy [`PRD-v0.7.md`](PRD-v0.7.md), including:

- real relational Repository Structural Graph v2 instead of only file inventory;
- explicit relationship provenance and parser capability reporting;
- delta-first graph refresh with changed/deleted-source invalidation;
- bounded graph query primitives and graph-assisted Working Sets;
- structural reverse-dependency impact and provenance-aware test mapping;
- structured Project Brain evidence, freshness detection, and revalidation;
- source authority and safe degraded fallback behavior;
- structural signals integrated into task depth, Scope Guard, health, and doctor;
- backwards compatibility with v0.6 Project Brain data;
- synchronized `0.7.0` release metadata and documentation;
- deterministic core/Codex CI plus release-grade full verifier contracts;
- no graph visualization, GraphRAG, media ingestion, embeddings, hosted graph server, or other explicitly excluded v0.7 scope expansion.
