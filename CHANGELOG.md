# Changelog

All notable Codemium changes are recorded here.

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
