<p align="center">
  <img src="assets/codemium-logo.svg" alt="Codemium logo" width="160" />
</p>

<h1 align="center">Codemium</h1>

<p align="center"><strong>Persistent coding intelligence for AI coding agents.</strong></p>

<p align="center">
  The engineering layer that helps coding agents understand the project, avoid wasteful investigation, make justified changes, and stop when the task is proven.
</p>

<p align="center">
  <a href="https://github.com/ahfaruq/codemium/actions/workflows/verify.yml"><img src="https://github.com/ahfaruq/codemium/actions/workflows/verify.yml/badge.svg" alt="Codemium Core" /></a>
  <img src="https://img.shields.io/badge/version-v0.10.0-2F81F7" alt="Version v0.10.0" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT License" /></a>
</p>

---

## What Codemium does

Codemium is a host-agnostic engineering layer for long-running software projects.

It helps coding agents:

- reuse verified project knowledge instead of relearning the repository;
- narrow investigation to the right files, symbols, dependencies, and tests;
- avoid repeated probes, builds, deployments, and guesses that add no new evidence;
- make the minimum justified engineering change;
- verify the real impact before completion;
- preserve necessary complexity such as security, validation, transactions, retries, compatibility, and tests.

> **Positioning:** the senior engineer who already knows your codebase.
>
> **Core law:** Every action must buy information or produce the solution.

## Current release: v0.10.0 — Execution Intelligence

Codemium v0.10.0 focuses on controlling the engineering process itself, not only the final diff.

The normal loop is:

```text
TASK
  ↓
PROJECT BRAIN
  ↓
STRUCTURAL INTELLIGENCE
  ↓
OBSERVE
  ↓
HYPOTHESIS
  ↓
CONTRADICTION GATE
  ↓
EVIDENCE DELTA GATE
  ↓
CHANGE ONLY IF JUSTIFIED
  ↓
VERIFY
  ↓
SLOP GUARD
  ↓
DONE
```

### Execution Intelligence

Execution Intelligence prevents zero-information investigation loops.

Key behavior:

- **Contradiction Gate** — conflicting observations must be resolved before mutation.
- **Hypothesis Ledger** — rejected hypotheses cannot silently cycle back without new evidence.
- **Evidence Delta Gate** — equivalent probes, builds, deployments, or checks stop when the evidence and repository state have not materially changed.
- **UI stabilization** — an early negative screenshot does not override stronger DOM/runtime/accessibility evidence.
- **Action outcomes** — investigation actions are classified as `NEW_EVIDENCE`, `NECESSARY_MUTATION`, `REQUIRED_VERIFICATION`, or `NO_GAIN`.

Example:

```text
DOM says dropdown is open
+ screenshot taken too early says not visible
= contradiction

Do not change z-index yet.
Stabilize the UI, inspect runtime evidence, then decide.
```

The goal is the **minimum justified investigation surface**, without arbitrary token or action limits.

### Anti-Slop Intelligence

Codemium also protects the final engineering surface through **Anti-Slop Intelligence** and the **Justified Change Gate**, exposed as **Slop Guard**.

Every changed surface should be attributable to the task as:

- `DIRECT`
- `DEPENDENCY`
- `CLEANUP`
- `TEST`

Internal `UNJUSTIFIED` work must be explained or removed before completion.

Slop Guard also tracks **finding provenance** such as `introduced`, `worsened`, `pre_existing`, and `unknown`, so historical debt does not automatically become part of the current task.

The **Underengineering Counter-Gate** prevents “simplification” from removing necessary security, validation, transactions, locking, idempotency, retry behavior, compatibility, data-integrity checks, or tests.

### Polyglot Intelligence

**Polyglot Intelligence** provides deterministic repository understanding across supported languages.

Structural Graph v3 can map:

```text
DEFINES
IMPORTS
IMPORTS_SYMBOL
CALLS
REFERENCES
INHERITS
IMPLEMENTS
TESTS
DEPENDS_ON
```

Python uses standard-library AST extraction. JavaScript, JSX, TypeScript, and TSX can use Tree-sitter when the optional runtime is installed.

The graph guides navigation and impact analysis. Source code and runtime/test evidence remain authoritative.

### Project Brain

Project Brain preserves durable, source-backed project knowledge between tasks and hosts.

It stores useful engineering knowledge such as:

- decisions;
- constraints;
- interfaces;
- architecture patterns;
- known bugs and risks.

It does **not** store secrets, raw tool transcripts, temporary execution observations, speculative hypotheses, or full chat history.

Knowledge is freshness-qualified as `FRESH`, `NEEDS_REVALIDATION`, `SUPERSEDED`, or `UNKNOWN`.

## Quick start

### OpenAI Codex

```sh
codex plugin marketplace add ahfaruq/codemium --ref main
codex plugin add codemium@codemium
```

Then use Codemium naturally:

```text
@Codemium fix the profile save bug
@Codemium deeply investigate why this websocket disconnects intermittently
@Codemium review this change for unnecessary engineering
```

After upgrading the marketplace/plugin, start a fresh Codex session if plugin inventory is cached.

### Other supported hosts

| Host | Status | Primary invocation |
| --- | --- | --- |
| OpenAI Codex | Stable | `@Codemium` |
| Claude Code | Beta | `/codemium:cm` |
| Gemini CLI | Beta | `/cm` |
| Cursor | Beta | `/cm` / skill picker |
| OpenCode | Beta | `/cm` / skill tool |

See [`INSTALL.md`](INSTALL.md) and [`HOSTS.md`](HOSTS.md) for host-specific installation details.

## Deterministic helpers

Normal users do not need to run these manually, but they are useful for diagnostics and host integrations:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/working_set.py --root . --query "auth refresh" --top 8
python plugins/codemium/engine/impact.py --root . --git-diff
python plugins/codemium/engine/execution_guard.py --root . status
python plugins/codemium/engine/slop_guard.py --root . --json --write-state
python plugins/codemium/engine/health.py --root .
```

## Design principles

```text
Repository source → implementation truth
Runtime/tests      → behavioral proof
Structural graph   → navigation and impact evidence
Project Brain      → durable verified knowledge
Execution Guard    → investigation discipline
Slop Guard         → changed-surface discipline
```

Codemium optimizes for:

> **minimum justified investigation surface + minimum justified engineering surface**

not minimum LOC, minimum reasoning, or artificial token quotas.

## Verification and benchmarks

Codemium keeps deterministic release-quality checks separate from competitive AI performance claims.

Current validation covers engine syntax, Project Brain behavior, Structural Graph v3, Polyglot Intelligence, Execution Intelligence, Evidence Delta Gate, Contradiction Gate, Hypothesis Ledger, Slop Guard, finding provenance, and the Underengineering Counter-Gate.

No numeric v0.10 token/cost/time improvement claim is published from deterministic fixtures alone. Competitive performance claims require representative measured agent runs.

## Documentation

- [`PRD-v0.10.md`](PRD-v0.10.md) — current Execution Intelligence specification
- [`RELEASE_NOTES-v0.10.0.md`](RELEASE_NOTES-v0.10.0.md) — current release notes
- [`INSTALL.md`](INSTALL.md) — installation
- [`HOSTS.md`](HOSTS.md) — host integration contract
- [`CHANGELOG.md`](CHANGELOG.md) — complete release history
- [`benchmarks/`](benchmarks/) — benchmark and calibration material

Older implementation details are intentionally kept out of this README. Use the changelog and archived PRDs when historical version context is needed.

## Support

Codemium is open source. If it helps your workflow, you can support continued development through GitHub Sponsors.

❤️ [Sponsor Codemium](https://github.com/sponsors/ahfaruq)

## License

MIT
