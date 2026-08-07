# Changelog

All notable Codemium changes are recorded here.

## 0.6.0 — Multi-host architecture

- Reframed Codemium as persistent coding intelligence for AI coding agents rather than a Codex-only product.
- Standardized the native Codex invocation on `$cm` and `$cm-*` focused skills.
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
