<p align="center">
  <img src="assets/codemium-logo.svg" alt="Codemium logo" width="160" />
</p>

<h1 align="center">Codemium</h1>

<p align="center"><strong>Persistent coding intelligence for AI coding agents.</strong></p>

<p align="center">
  The engineering layer that helps coding agents work like a senior engineer who already knows your codebase.
</p>

<p align="center">
  <a href="https://github.com/ahfaruq/codemium/actions/workflows/verify.yml"><img src="https://github.com/ahfaruq/codemium/actions/workflows/verify.yml/badge.svg" alt="Codemium Core" /></a>
  <img src="https://img.shields.io/badge/version-v0.9.0-2F81F7" alt="Version v0.9.0" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT License" /></a>
  <a href="https://github.com/sponsors/ahfaruq"><img src="https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-EA4AAA?logo=githubsponsors&logoColor=white" alt="Sponsor Codemium" /></a>
</p>

<p align="center"><sub>Host-agnostic &nbsp;•&nbsp; Project-aware &nbsp;•&nbsp; Evidence-backed &nbsp;•&nbsp; Scope-disciplined &nbsp;•&nbsp; Verification-driven</sub></p>

---

Codemium is a host-agnostic engineering layer for long-running software projects. It helps coding agents preserve project understanding, inspect the right code, make the **minimum justified engineering change**, verify the real impact, and avoid adding engineering surface that the task never required.

> **Positioning:** the senior engineer who already knows your codebase.
>
> **Investigate once. Preserve what matters. Reuse it safely.**

Codemium does not replace Codex, Claude Code, Gemini CLI, Cursor, or OpenCode. It gives those agents a shared engineering layer built from three complementary forms of intelligence:

- **Project Brain** — durable engineering knowledge learned through verified work over time;
- **Polyglot Intelligence** — deterministic structural understanding across supported repository languages;
- **Anti-Slop Intelligence** — task-aware proof that changed engineering surface is justified.

The repository remains the source of truth. Tests/runtime evidence remain the proof of behavior. Project Brain is freshness-qualified memory. The structural graph is a derived navigation/impact index. Slop Guard is a changed-surface quality gate, not a replacement for source review.

# Anti-Slop Intelligence — v0.9

v0.9 adds the **Justified Change Gate**, exposed publicly as **Slop Guard**.

The question is not:

> How few lines can the agent write?

It is:

> **Does every changed engineering surface actually need to exist?**

Codemium optimizes for the **minimum justified engineering surface**.

```text
TASK CONTRACT
      │
      ▼
PROJECT BRAIN + GRAPH
      │
      ▼
BOUNDED WORKING SET
      │
      ▼
IMPLEMENT + VERIFY
      │
      ▼
ACTUAL DIFF
      │
      ▼
SLOP GUARD
      │
      ├── Scope justification
      ├── Deterministic findings
      ├── Graph v3 evidence
      ├── Finding provenance
      ├── Evidence-backed adjudication
      └── Underengineering Counter-Gate
      │
      ▼
RE-VERIFY IF CLEANED
      │
      ▼
DONE
```

## Changed-surface classification

Every changed surface should be attributable to:

| Class | Meaning |
| --- | --- |
| `DIRECT` | implements requested behavior |
| `DEPENDENCY` | required for a direct change to work safely |
| `CLEANUP` | made obsolete by this exact task change |
| `TEST` | verifies changed behavior |
| `UNJUSTIFIED` | internal unresolved state; not valid at completion |

Slop Guard analyzes the actual task diff and also includes safe/readable untracked files. `.codemium/` runtime/project state is excluded from source-slop analysis.

`CLEANUP` is intentionally explicit. Codemium does not label unrelated historical debt as cleanup merely to make a diff look clean.

## Finding provenance

A finding records whether the suspicious property was:

```text
introduced
worsened
pre_existing
unknown
```

High-confidence completion blockers focus on **introduced** and **worsened** engineering. Pre-existing debt does not become part of the task simply because the current change touched the same file. Unknown major findings require review rather than fabricated certainty.

## What Slop Guard can detect

The initial v0.9 engine covers signals including:

- unrelated changed surfaces / scope creep;
- duplicate top-level implementation signals;
- unnecessary new dependencies;
- single-use forwarding helpers;
- small unnecessary-file signals;
- gratuitous abstraction signals;
- debug residue;
- obvious narrative comments;
- new dead-code signals;
- speculative fallback patterns;
- unjustified public API expansion signals;
- type-system escape hatches.

These are evidence signals, not blanket style rules. A class, helper, fallback, dependency, or public API is not automatically slop simply because it exists.

## Evidence-backed justification

Ambiguous engineering may be legitimate. Instead of weakening a rule globally, Codemium supports narrow `JUSTIFIED` adjudication backed by concrete evidence.

Default transient decision file:

```text
.codemium/runtime/slop-adjudications.json
```

Example:

```json
{
  "schema_version": 1,
  "decisions": [
    {
      "rule": "UNJUSTIFIED_PUBLIC_API",
      "path": "src/api.ts",
      "symbol": "createSession",
      "decision": "JUSTIFIED",
      "reason": "The repository-owned public adapter requires this export.",
      "evidence": [
        {"kind": "source", "path": "src/adapters/public.ts"},
        {"kind": "task", "detail": "acceptance requires the public adapter surface"}
      ]
    }
  ]
}
```

An accepted decision must match the finding and contain a substantive reason plus valid evidence. It remains visible in the report, but is removed from blocker/risk calculation.

## Underengineering Counter-Gate

Anti-Slop must reject both over-engineering and unsafe under-engineering.

Slop Guard does **not** blindly reward removal of:

- authentication / authorization;
- validation / sanitization;
- rate limiting;
- transactions / rollback;
- locking / idempotency;
- retry behavior;
- data-integrity checks;
- migrations / compatibility paths;
- security controls;
- tests.

If a simplification removes protected-complexity signals, the gate requires review. Evidence-backed adjudication does not bypass this safety check.

## Coverage honesty

Slop Risk is informational, not implementation truth. Codemium reports changed-line and structural coverage and returns no aggregate score when coverage is insufficient rather than manufacturing precision.

## Direct Anti-Slop review

Normal `@Codemium` source-changing work runs Slop Guard near completion. Advanced users can invoke the focused skill directly:

```text
$cm-slop
```

Or run the deterministic engine:

```sh
python plugins/codemium/engine/slop_guard.py --root . --json --write-state
```

# Polyglot Intelligence — v0.8 foundation

v0.9 retains Structural Graph v3 from v0.8: a parser-abstracted cross-language repository index with deep JavaScript/JSX, TypeScript, and TSX support through Tree-sitter while preserving Python AST extraction and deterministic fallback behavior.

## Graph entities and relationships

Minimum graph entities:

```text
FILE / TEST
MODULE
SYMBOL
```

Relationships can include:

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

Relationship provenance is explicit:

- **DIRECT** — observed directly by deterministic parsing;
- **RESOLVED** — deterministically resolved from source structure/names;
- **HEURISTIC** — fallback evidence that must not be presented as direct truth.

Python uses standard-library AST extraction. JavaScript/JSX, TypeScript, and TSX can use Tree-sitter deep parsing when the optional Polyglot runtime is installed. Unsupported or unavailable deep parsers degrade to deterministic fallback rather than making the repository unusable.

Install the optional runtime:

```sh
python -m pip install -r requirements-polyglot.txt
```

The graph guides where to inspect. Source remains authoritative:

```text
Structural graph → navigation and impact hypotheses
Source code       → implementation truth
Tests/runtime     → behavioral proof
Project Brain     → durable engineering knowledge, freshness-qualified
Slop Guard        → changed-surface justification gate
```

## Symbol-aware impact and tests

Git diff line ranges can map to changed symbols before bounded reverse traversal. Callers, imports, imported symbols, references, inheritance, dependencies, tests, and cross-language edges contribute impact evidence.

Test Intelligence v3 uses structural `TESTS` relationships and fallback evidence to produce prioritized P0/P1/P2 verification candidates. Actual test/runtime evidence determines sufficiency.

# Project Brain

Project Brain preserves durable, source-backed project knowledge between tasks and hosts.

Useful durable entries include:

- decisions;
- constraints;
- interfaces;
- architecture patterns;
- known bugs/risks.

It does not store secrets, raw logs, tool transcripts, personal data, speculative hypotheses, or full conversation history.

## Freshness states

- **FRESH** — supporting evidence still matches source;
- **NEEDS_REVALIDATION** — supporting source changed or disappeared;
- **SUPERSEDED** — retained history replaced by later verified knowledge;
- **UNKNOWN** — legacy or insufficient evidence; verify before material reliance.

> **Remember aggressively, trust conditionally.**

For Codex, Project Brain is anchored to one canonical project root and lifecycle hooks enforce the persistence gate for normal Codemium work.

# Core behavior

Codemium classifies work as BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY and selects the smallest safe engineering depth:

| Depth | Meaning |
| --- | --- |
| FAST | obvious, localized, low-risk work |
| NORMAL | ordinary project-aware engineering |
| DEEP | complex, cross-boundary, intermittent, concurrency/performance work |
| CRITICAL | auth/security, payments, migrations, production data, destructive or breaking changes |

The normal engineering loop applies:

- **Project Brain** — reuse durable knowledge when still fresh;
- **Polyglot Intelligence** — use Graph v3 to narrow navigation and impact;
- **Working Set Engine** — bound repository context around task evidence;
- **Scope Guard** — keep every changed surface attributable to the task;
- **Impact & Test Intelligence** — inspect likely dependents and prioritize verification;
- **Slop Guard** — reject unresolved unjustified engineering before completion;
- **Underengineering Counter-Gate** — preserve necessary complexity;
- **Read/Search Reuse** — avoid repeated deterministic work when validity is provable;
- **Stop Engine** — stop once behavior, verification, scope, Anti-Slop, freshness, and persistence gates are satisfied.

# Quick start

## OpenAI Codex

```sh
codex plugin marketplace add ahfaruq/codemium --ref main
codex plugin add codemium@codemium
```

After installing/updating, review lifecycle hook trust with `/hooks` when required, then start a fresh session if plugin inventory is cached.

Use Codemium naturally:

```text
@Codemium fix the profile save bug
@Codemium deeply investigate why this websocket disconnects intermittently
@Codemium safely change this authentication flow and verify the impact
@Codemium review this change for unnecessary engineering
```

Direct Agent Skill invocation remains available:

```text
$cm <task>
$cm fast <task>
$cm deep <task>
$cm critical <task>
$cm-slop
```

## Supported hosts

| Host | Status | Native integration | Primary invocation |
| --- | --- | --- | --- |
| OpenAI Codex | **Stable** | Codex plugin + lifecycle hooks + Agent Skills | `@Codemium` |
| Claude Code | **Beta** | Claude plugin + Agent Skill + command | `/codemium:cm` |
| Gemini CLI | **Beta** | Gemini extension + context + command | `/cm` |
| Cursor | **Beta** | Portable Agent Skill | `/cm` / skill picker |
| OpenCode | **Beta** | Portable Agent Skill | `/cm` when exposed, otherwise skill tool/auto-selection |

See [`INSTALL.md`](INSTALL.md) for installation and hook trust, [`HOSTS.md`](HOSTS.md) for the adapter contract, [`PRD-v0.9.md`](PRD-v0.9.md) for Anti-Slop requirements, [`PRD-v0.8.md`](PRD-v0.8.md) for Polyglot Intelligence, [`CHANGELOG.md`](CHANGELOG.md), and [`RELEASE_NOTES-v0.9.0.md`](RELEASE_NOTES-v0.9.0.md).

# Benchmark suite

Codemium keeps competitive performance claims separate from deterministic implementation/quality gates.

## v0.8 competitive efficiency

The existing v0.8 benchmark dashboard remains as historical benchmark evidence:

<p align="center">
  <img src="assets/benchmark-v08-competitive.svg" alt="Codemium v0.8 competitive efficiency benchmark" width="100%" />
</p>

| vs baseline | LOC | tokens | cost | time | quality | safety |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Caveman | -18% | +5% | +4% | +2% | 100% | 100% |
| Ponytail | -38% | -19% | -18% | -21% | 100% | 100% |
| **Codemium v0.8** | **-45%** | **-31%** | **-29%** | **-28%** | **100%** | **100%** |

## v0.8 polyglot structural coverage

<p align="center">
  <img src="assets/benchmark-v08-polyglot.svg" alt="Codemium v0.8 polyglot structural coverage benchmark" width="100%" />
</p>

| Capability | v0.7 | v0.8+ |
| --- | --- | --- |
| Deep-parsed core extensions (`.py/.js/.jsx/.ts/.tsx`) | **1 / 5** | **5 / 5** |
| Structural Graph | v2 | **v3** |
| JavaScript / TypeScript / TSX | fallback | **Tree-sitter** |
| Imported-symbol edges | — | **`IMPORTS_SYMBOL`** |
| Cross-language edge evidence | limited | **explicit** |

## v0.8 impact & test intelligence

<p align="center">
  <img src="assets/benchmark-v08-impact-test.svg" alt="Codemium v0.8 impact and test intelligence benchmark" width="100%" />
</p>

The deterministic mixed-language fixture verifies JavaScript → TypeScript imported-symbol/call resolution, changed-line → changed-symbol impact seeding, cross-language dependent discovery, related-test confidence, and prioritized test plans.

See [`benchmarks/V08_BENCHMARK_SUITE.md`](benchmarks/V08_BENCHMARK_SUITE.md).

## v0.9 Anti-Slop release calibration

v0.9 adds a labeled blocker-semantics corpus and deterministic calibration runner:

```sh
python benchmarks/calibrate_v09_blocking.py
```

It protects the intended behavior for introduced/worsened blockers, pre-existing debt, evidence-backed justification, ambiguous findings, protected-complexity removal, and clean diffs.

**This calibration is a release quality gate, not a competitive performance benchmark.** No numeric v0.9 Anti-Slop efficiency/quality improvement claim is published until representative multi-arm coding-agent runs are measured and retained as evidence.

See [`benchmarks/V09_ANTISLOP_BENCHMARK.md`](benchmarks/V09_ANTISLOP_BENCHMARK.md).

# Shared `.codemium/` state

```text
.codemium/
├── PROJECT.md
├── architecture/
├── registry/
│   ├── decisions.jsonl
│   ├── constraints.jsonl
│   ├── interfaces.jsonl
│   ├── patterns.jsonl
│   └── bugs.jsonl
├── repository/
│   ├── graph.json
│   ├── manifest.json
│   └── tests.json
├── tasks/
│   └── active.json
└── runtime/
    ├── cache.jsonl
    ├── operations.jsonl
    ├── slop-report.json
    ├── slop-adjudications.json
    ├── persistence-gates/
    └── snapshots/
```

Durable sanitized Project Brain knowledge is vendor-neutral. Repository graph/test maps, active task state, cache, Slop reports/adjudications, and persistence gates are transient/regenerable state and are ignored by Git by default.

# Deterministic helpers

Normal users do not need to run these manually. They are useful for diagnostics, testing, and host adapters:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/project_brain.py --root . freshness
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/graph_query.py --root . callers "refresh_session"
python plugins/codemium/engine/working_set.py --root . --query "auth refresh" --top 8
python plugins/codemium/engine/impact.py --root . --git-diff
python plugins/codemium/engine/slop_guard.py --root . --json --write-state
python plugins/codemium/engine/health.py --root .
```

# Host usage

## Claude Code

```text
/plugin marketplace add ahfaruq/codemium
/plugin install codemium@codemium
```

Use `/codemium:cm ...` or let Claude auto-select the shared `cm` Agent Skill.

## Gemini CLI

```sh
gemini extensions install https://github.com/ahfaruq/codemium --ref main
```

Use `/cm ...` after restarting Gemini CLI if extension inventory was cached.

## Cursor

```sh
python scripts/install_host.py --host cursor
# or project-local
python scripts/install_host.py --host cursor --scope project --project /path/to/project
```

## OpenCode

```sh
python scripts/install_host.py --host opencode
# or project-local
python scripts/install_host.py --host opencode --scope project --project /path/to/project
```

Portable installs copy the shared Agent Skill, Anti-Slop policy, and canonical deterministic engine.

# Verification model

## 1. Core CI — every push / pull request

```sh
python scripts/verify_core.py
```

Core CI validates engine syntax, Project Brain invariants, Structural Intelligence contracts, task/depth behavior, Slop Guard mechanics, finding provenance, evidence-backed adjudication, CLEANUP classification, the Underengineering Counter-Gate, and v0.9 blocker calibration.

It does not claim competitive AI quality or full host compatibility.

## 2. Polyglot Intelligence CI

```sh
python -m pip install -r requirements-polyglot.txt
python scripts/verify_polyglot.py
```

This verifies the real JS/TS/TSX Tree-sitter and cross-language fixture.

## 3. Codex lifecycle CI

```sh
python scripts/verify_codex_plugin.py
```

This exercises bundled persistence-hook mechanics.

## 4. Full host validation

Linux/macOS:

```sh
sh plugins/codemium/scripts/verify.sh
```

Windows:

```powershell
./plugins/codemium/scripts/verify.ps1
```

## 5. Competitive AI benchmark

AI quality/performance claims remain evidence-gated and require representative measured agent runs. Deterministic CI/calibration results are not converted into performance claims.

# v0.9 scope boundaries

Codemium v0.9 is not:

- a generic linter replacement;
- a code minimizer or code-golf tool;
- a repository-wide desloppification pass on every task;
- a generic graph visualization product or language server;
- GraphRAG/vector-database infrastructure;
- an AI-authorship detector;
- permission to remove defensive/security/compatibility/test complexity without behavioral evidence;
- evidence for a numeric v0.9 competitive Anti-Slop improvement claim by itself.

The product rule remains:

> **Everything the solution needs. Nothing it does not.**

# Status

`v0.9.0` introduces **Anti-Slop Intelligence** while preserving the v0.8 Polyglot Intelligence and Project Brain foundations. Slop Guard is task-aware, changed-surface-first, evidence-backed, provenance-aware, coverage-honest, and paired with an Underengineering Counter-Gate. Codex remains the stable/reference adapter; Claude Code, Gemini CLI, Cursor, and OpenCode share the same vendor-neutral core through their adapters.

# Support Codemium

Codemium is open source. If it helps your workflow or team, consider supporting continued compatibility testing, documentation, benchmarks, host integrations, and maintenance through GitHub Sponsors.

❤️ [Sponsor Codemium](https://github.com/sponsors/ahfaruq)

# License

MIT
