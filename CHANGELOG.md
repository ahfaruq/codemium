# Changelog

All notable Codemium changes are recorded here.

## 0.7.0 — Structural Intelligence & Evidence Bridge

- Upgraded Repository Intelligence from a lightweight file/symbol/import inventory to **Structural Graph v2** with FILE/TEST, MODULE, and SYMBOL entities plus `DEFINES`, `CONTAINS`, `IMPORTS`, `CALLS`, `REFERENCES`, `INHERITS`, `IMPLEMENTS`, `TESTS`, and aggregate `DEPENDS_ON` relationships.
- Added explicit relationship provenance: **DIRECT**, **RESOLVED**, and **HEURISTIC**, so fallback or resolved relationships are never silently presented as direct source facts.
- Added deterministic Python AST extraction using the standard library and an honest `fallback-regex` parser for supported languages where deeper structural parsing is unavailable; parser capability/coverage is exposed in graph health.
- Added content-hash manifest state and delta-first graph refresh. Unchanged files reuse prior extraction, changed files are reparsed, deleted source is pruned, and the manifest is written only after graph construction succeeds.
- Added `graph_query.py` with bounded symbol discovery, neighbors, callers/callees, dependencies/dependents, tests, paths, and impact traversal.
- Upgraded the Working Set Engine to combine lexical task seeds with bounded structural traversal and to persist evidence explaining why each file entered the task working set.
- Upgraded Change Impact to structural reverse-dependency traversal with explicit evidence paths, transitive distance, related tests, and risk signals rather than relying primarily on import-name heuristics.
- Upgraded Test Intelligence to prefer structural `TESTS` evidence and retain deterministic naming/import heuristics only as a fallback with `HEURISTIC` provenance.
- Added structured Project Brain evidence with source paths, symbols/node IDs when available, content hashes, and source locations while retaining compatibility with legacy `source` fields.
- Added Project Brain freshness states: **FRESH**, **NEEDS_REVALIDATION**, **SUPERSEDED**, and **UNKNOWN**, plus a deterministic `revalidate` workflow. Source changes invalidate trust rather than deleting durable history.
- Added structural-risk depth escalation, structural Scope Guard explanations, and health/doctor reporting for graph schema/freshness, parser coverage, provenance counts, unresolved relationships, and Project Brain freshness.
- Updated Codex and portable Agent Skill contracts so agents use structural intelligence for navigation/impact while keeping source code authoritative and tests/runtime evidence responsible for behavioral proof.
- Added host-agnostic v0.7 fixtures covering AST/fallback parsing, incremental no-op rebuilds, changed/deleted source invalidation, graph queries, graph-assisted Working Sets, impact/test mapping, Project Brain freshness/revalidation, health degradation, and backwards-compatible Project Brain persistence.
- Kept v0.7 deliberately focused: no graph visualization product, GraphRAG/vector database, embeddings infrastructure, media ingestion, LLM-generated structural edges, fuzzy semantic symbol deduplication, or hosted/shared graph service.

## 0.6.6 — Cross-worktree memory consolidation

- Extended canonical Project Brain migration from only the current linked worktree to **all live Git worktrees** sharing the repository's common Git directory.
- Fixes the real Codex Desktop sequence where an older task stored v0.6.4 memory in worktree A but a later task starts in a fresh worktree B: worktree B now discovers and consolidates durable memory from worktree A into the Local canonical `.codemium/`.
- Added durable-source stamps in `.codemium/runtime/project-location.json` so unchanged legacy worktree brains are not re-imported on every turn; changed legacy registries are merged again through normal Project Brain deduplication.
- When the canonical Project Brain is new, stable project metadata is taken from the freshest legacy brain while active durable registry entries from every discovered worktree are merged into the canonical registry.
- Expanded the Git worktree integration fixture to use separate legacy-task and current-task worktrees, proving that memory can be recovered across different Desktop tasks rather than only from the current worktree.
- Kept `plugins/codemium/hooks/hooks.json` unchanged, so existing Codex hook trust remains valid.

## 0.6.5 — Canonical Project Brain root

- Anchored Codex Project Brain state to one canonical project root derived from Git's shared common directory, so Local checkout tasks and linked/Codex-managed worktrees reuse the same `.codemium/` instead of creating isolated memories per worktree.
- Added canonical project-location metadata under `.codemium/runtime/project-location.json`, recording the canonical root, runtime cwd, runtime git root, git common directory, linked-worktree status, and observed runtime roots.
- Added automatic migration for legacy v0.6.4 Project Brain state found inside a linked worktree: a new canonical brain copies durable registry/project metadata, while an existing canonical brain merges active durable entries through normal deduplication.
- Routed normal persistence gates, Stop handling, and lightweight memory retrieval through the same canonical-root resolver.
- Added project-location information to persistence-gate and memory-mode diagnostics so live Desktop behavior can be verified without guessing where state was written.
- Added an integration fixture that creates a real Git linked worktree, seeds legacy memory there, verifies migration into the Local checkout, and confirms Local/worktree tasks reuse the same durable brain.
- Kept `plugins/codemium/hooks/hooks.json` unchanged from 0.6.3/0.6.4, so existing Codex hook trust remains valid after this update.

## 0.6.4 — Lightweight Project Brain memory mode

- Reworked Project Brain-only follow-up questions into an explicit `CODEMIUM MEMORY RETRIEVAL MODE` that overrides the normal engineering lifecycle for that turn.
- Added stronger no-work instructions for memory-only turns: no task/depth classification, planning, git inspection, repository search, source reads, working-set/repository-state creation, tests, source verification, or normal completion workflow.
- Reduced the retrieval payload to a bounded six-entry snapshot and instructs Codex to use minimum reasoning and answer concisely unless more detail is requested.
- Removed the fast path's unnecessary `git rev-parse` repository-root lookup; Project Brain is resolved by walking parent directories for `.codemium/` instead.
- Avoids spawning the Project Brain init helper on retrieval-only turns when `.codemium/` already exists.
- Added deterministic timing diagnostics for root resolution, state init, registry read, ranking, context construction, gate write, and approximate host turn time to `Stop` under the transient persistence-gate record.
- Added test coverage for lightweight-mode override semantics, timing diagnostics, no repository/task-state creation, relevant-entry filtering, and normal engineering fallback.
- Kept `plugins/codemium/hooks/hooks.json` unchanged from 0.6.3 so existing Codex hook trust remains valid after this update.

## 0.6.3 — Project Brain retrieval fast path

- Added a Codex `UserPromptSubmit` dispatcher that recognizes explicit Project Brain-only retrieval requests before normal engineering orchestration begins.
- Injects a bounded set of relevant active Project Brain entries directly into the turn, using lightweight lexical ranking plus a small bilingual synonym bridge for common engineering terms.
- Pre-satisfies the persistence gate as `reused` (or `none` when no stored knowledge exists), so retrieval-only turns do not enter the Stop/finalizer continuation cycle.
- Explicitly tells Codex not to run task compilation, repository mapping, working-set discovery, git inspection, repository search, or source-file reads for Project Brain-only queries unless the user asks to refresh/verify stored knowledge.
- Preserves the existing deterministic persistence gate unchanged for normal investigation, implementation, review, and other repository-bound Codemium work.
- Added a dedicated fast-path fixture proving stored knowledge is reused without repository graph/task-state creation and that Stop exits immediately.
- Routed both Codex lifecycle hooks through the new dispatcher while retaining the existing manual finalizer compatibility path.

## 0.6.2 — Deterministic Codex persistence gate

- Replaced prompt-only Project Brain completion enforcement in the OpenAI Codex adapter with bundled lifecycle hooks.
- Added a `UserPromptSubmit` hook that initializes/reuses Project Brain and creates a per-turn persistence gate for Codemium-invoked repository work when workspace-state writes are allowed.
- Added a `Stop` hook that continues a turn while its persistence gate is still pending, requiring durable knowledge to be captured/reused or explicitly classified as none before normal completion.
- Added source-backed capture validation, duplicate reuse through the existing Project Brain engine, and a bounded retry guard that fails visibly rather than looping forever.
- Preserved read-only source-code workflows while respecting explicit prohibitions on all file/workspace changes.
- Added protection against creating a second persistence gate when a `Stop` continuation is submitted as another `UserPromptSubmit` event.
- Added a dedicated Codex lifecycle fixture and CI verifier that exercise actual hook behavior instead of merely asserting persistence wording exists in prompts/skills.
- Documented Codex hook trust: plugin command hooks are skipped until the user reviews and trusts the current hook definition with `/hooks`.

## 0.6.1 — Automatic Project Brain persistence

- Made `@Codemium` the primary OpenAI Codex plugin invocation for the public user experience.
- Kept `$cm` and focused `$cm-*` skills as advanced/direct Agent Skill compatibility paths.
- Updated the Codex plugin manifest, installation guide, host contract, PRD, doctor, and cross-host verifiers to distinguish plugin-level invocation from internal skill invocation.
- Made Project Brain initialization automatic for normal repository-bound Codemium tasks when workspace-state writes are allowed; users no longer need a separate `$cm-init` step before ordinary use.
- Added deterministic batched Project Brain capture with duplicate reuse for durable decisions, constraints, interfaces, patterns, and known bugs/risks.
- Added a completion persistence gate so source-backed durable findings from reviews/investigations are captured, reused, explicitly classified as none, or skipped only when the user forbids workspace-state writes.
- Clarified that “do not modify code” still permits `.codemium/` bookkeeping while an explicit prohibition on all file/workspace changes is respected.
- Added core regression coverage for automatic initialization, durable capture, and duplicate avoidance.

## 0.6.0 — Multi-host architecture

- Reframed Codemium as persistent coding intelligence for AI coding agents rather than a Codex-only product.
- Added the Codex plugin and `cm` Agent Skill with automatic task/depth selection and focused direct skills.
- Added a repository-root Claude Code plugin with `/codemium:cm` and on-demand `cm` Agent Skill support.
- Added a native Gemini CLI extension with `/cm`, lean `GEMINI.md` bootstrap context, and on-demand `cm` Agent Skill support.
- Added safe portable Agent Skill installation for Cursor and OpenCode, including the canonical deterministic engine and references.
- Added `scripts/doctor.py` for cross-host structural validation and host-binary discovery.
- Added generic reasoning classes (`economy`, `balanced`, `strong`, `frontier`) so Codemium core does not depend on vendor reasoning labels.
- Added Cursor and OpenCode to portable task/reasoning profiles.
- Consolidated Claude/Gemini/Cursor/OpenCode onto one root `skills/cm/SKILL.md` source of truth.
- Added safe transient-state migration so `.codemium/tasks/active.json`, repository maps, runtime data, and completed task snapshots stay out of Git by default.
- Split verification into three evidence layers: fast host-agnostic Core CI on every push/PR, full cross-host Linux/Windows validation only on manual/release runs, and a separate AI competitive benchmark for quality/performance claims.
- Added `scripts/verify_core.py` as the health-badge check and retained the full Linux/macOS + Windows verifier for release validation.
- Added `HOSTS.md` and `INSTALL.md`.
- Kept the public Numbers dashboard hidden until measured competitive benchmark data is available.

## 0.5.0 — Host abstraction

- Introduced the host-adapter architecture and portable `.codemium/` project state.
- Added initial Claude Code and Gemini CLI adapters.
- Separated portable reasoning depth from Codex-specific effort labels.

## 0.4.0 — Benchmark evidence infrastructure

- Added benchmark summarization/rendering and synthetic-vs-measured publication gating.
- Competitive benchmark infrastructure remains retained but hidden from the public README until real measured results are ready.

## 0.3.0 — Reasoning profiles

- Added depth-aware reasoning preferences and host-effort alignment without silently changing global model configuration.

## 0.2.0 — Short invocation and adaptive depth

- Added the short `cm` skill identity and FAST/NORMAL/DEEP/CRITICAL engineering depth model.

## 0.1.0 — Initial Project Brain MVP

- Added Project Brain, repository intelligence, task compilation, bounded working sets, scope guard, impact/test mapping, deterministic reuse, and stop conditions.
