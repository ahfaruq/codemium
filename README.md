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
  <img src="https://img.shields.io/badge/version-v0.10.0-2F81F7" alt="Version v0.10.0" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-3FB950" alt="MIT License" /></a>
  <a href="https://github.com/sponsors/ahfaruq"><img src="https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-EA4AAA?logo=githubsponsors&logoColor=white" alt="Sponsor Codemium" /></a>
</p>

<p align="center"><sub>Host-agnostic &nbsp;•&nbsp; Project-aware &nbsp;•&nbsp; Evidence-backed &nbsp;•&nbsp; Execution-disciplined &nbsp;•&nbsp; Scope-disciplined</sub></p>

---

Codemium is a host-agnostic engineering layer for long-running software projects. It helps coding agents preserve project understanding, inspect the right code, avoid wasteful investigation loops, make the **minimum justified engineering change**, verify the real impact, and stop once the task is proven.

> **Positioning:** the senior engineer who already knows your codebase.
>
> **Investigate once. Preserve what matters. Reuse it safely.**

Codemium does not replace Codex, Claude Code, Gemini CLI, Cursor, or OpenCode. It gives those agents a shared engineering layer built from four complementary forms of intelligence:

- **Project Brain** — durable engineering knowledge learned through verified work over time;
- **Polyglot Intelligence** — deterministic structural understanding across supported repository languages;
- **Anti-Slop Intelligence** — task-aware proof that changed engineering surface is justified;
- **Execution Intelligence** — task-aware proof that the next investigation action is worth doing.

The repository remains the source of truth. Tests/runtime evidence remain the proof of behavior. Project Brain is freshness-qualified memory. Structural Graph v3 is a derived navigation/impact index. Slop Guard is a changed-surface quality gate. Execution Guard is a transient investigation-control layer. None of them outrank source/runtime truth.

# Execution Intelligence — v0.10

v0.10 adds the **Evidence Delta Gate**, exposed through the deterministic **Execution Guard**.

The question is no longer only:

> Where should the agent look?

or:

> What actually needs to change?

v0.10 adds:

> **What should the agent do next, and will that action produce new evidence or the solution?**

The core law is:

> **Every action must buy information or produce the solution.**

Codemium now targets both:

```text
minimum justified investigation surface
+
minimum justified engineering surface
```

without arbitrary token, time, or action budgets.

## Execution lifecycle

```text
PROJECT BRAIN
      │
      ▼
TASK CONTRACT
      │
      ▼
STRUCTURAL GRAPH + WORKING SET
      │
      ▼
OBSERVE
      │
      ▼
HYPOTHESIS LEDGER
      │
      ▼
CONTRADICTION GATE
      │
      ▼
EVIDENCE DELTA GATE
      │
      ├── new evidence → continue
      ├── necessary mutation → mutate
      ├── required verification → verify
      └── no gain → STOP / reconsider assumptions
      │
      ▼
VERIFY
      │
      ▼
SLOP GUARD
      │
      ▼
UNDERENGINEERING COUNTER-GATE
      │
      ▼
DONE
```

## Contradiction Gate

Materially conflicting observations block mutation until the conflict is resolved or explicitly superseded by stronger evidence.

A representative UI failure:

```text
DOM says dropdown is open
        +
early screenshot says not visible
        ↓
CONTRADICTION
        ↓
DO NOT mutate z-index yet
        ↓
stabilize UI / inspect geometry / computed style / visibility
        ↓
resolve evidence first
```

This prevents an agent from converting observation timing problems into speculative source changes.

## UI stabilization

For UI/runtime investigations, a negative screenshot is not automatically authoritative.

When stronger state evidence says a transition has started, prefer:

```text
interaction
→ DOM/accessibility state
→ animation/render/network stabilization
→ computed style / geometry / visibility
→ screenshot
```

A screenshot captured before stabilization must not by itself justify a CSS/layout mutation.

## Hypothesis Ledger

Root-cause guesses become explicit execution state.

Example:

```text
H1: dropdown is behind an overlay
Expected evidence: computed stacking order places it below the overlay
Result: REJECTED
```

Once rejected, the same hypothesis cannot be retried against unchanged evidence unless material new information reopens it.

## Evidence Delta Gate

Repeat-sensitive actions are compared against relevant evidence and repository state.

If an equivalent action was already performed and nothing material changed, Codemium stops the repeat instead of allowing another no-gain loop.

This applies to work such as:

- repeated browser probes;
- repeated equivalent searches/reads;
- repeated hypothesis tests;
- repeated builds;
- repeated deployments;
- repeated verification that adds no required coverage or confidence.

There is intentionally no arbitrary action or token quota. Difficult engineering may require deep investigation. The stopping signal is **zero meaningful evidence delta**.

## Action outcomes

Execution Intelligence classifies task actions into:

```text
NEW_EVIDENCE
NECESSARY_MUTATION
REQUIRED_VERIFICATION
NO_GAIN
```

`NO_GAIN` becomes visible execution waste instead of silently consuming more model/tool usage.

Typical helper:

```sh
python plugins/codemium/engine/execution_guard.py --root . status
```

See [`PRD-v0.10.md`](PRD-v0.10.md) and [`plugins/codemium/skills/codemium/references/execution-policy.md`](plugins/codemium/skills/codemium/references/execution-policy.md).

# Anti-Slop Intelligence — v0.9 foundation

v0.9 introduced the **Justified Change Gate**, exposed publicly as **Slop Guard**.

The question is:

> **Does every changed engineering surface actually need to exist?**

Codemium optimizes for the **minimum justified engineering surface**, not minimum LOC.

Every changed surface should be attributable to:

| Class | Meaning |
| --- | --- |
| `DIRECT` | implements requested behavior |
| `DEPENDENCY` | required for a direct change to work safely |
| `CLEANUP` | made obsolete by this exact task change |
| `TEST` | verifies changed behavior |
| `UNJUSTIFIED` | internal unresolved state; not valid at completion |

Finding provenance is explicit:

```text
introduced
worsened
pre_existing
unknown
```

High-confidence completion blockers focus on **introduced** and **worsened** engineering. Pre-existing debt does not become task scope merely because the current change touched the same file.

Slop Guard covers signals including unjustified scope, duplicate implementations, unnecessary dependencies, single-use forwarding helpers, unnecessary abstractions/files, debug residue, narrative comments, dead-code signals, speculative fallbacks, public API expansion, and type-system escapes.

Ambiguous engineering may be marked `JUSTIFIED` only with concrete source/task evidence. The aggregate Slop Risk score remains informational and coverage-honest.

## Underengineering Counter-Gate

Anti-Slop must reject both over-engineering and unsafe under-engineering.

Codemium does **not** blindly reward removal of:

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

Typical helper:

```sh
python plugins/codemium/engine/slop_guard.py --root . --json --write-state
```

See [`PRD-v0.9.md`](PRD-v0.9.md) and [`plugins/codemium/skills/codemium/references/slop-policy.md`](plugins/codemium/skills/codemium/references/slop-policy.md).

# Polyglot Intelligence — v0.8 foundation

Structural Graph v3 is a parser-abstracted cross-language repository index with deep JavaScript/JSX, TypeScript, and TSX support through Tree-sitter while preserving Python AST extraction and deterministic fallback behavior.

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

Python uses standard-library AST extraction. JavaScript/JSX, TypeScript, and TSX can use Tree-sitter deep parsing when the optional runtime is installed.

```sh
python -m pip install -r requirements-polyglot.txt
```

The authority order remains:

```text
Structural graph → navigation and impact hypotheses
Source code       → implementation truth
Tests/runtime     → behavioral proof
Project Brain     → durable engineering knowledge, freshness-qualified
Execution Guard   → transient action/investigation gate
Slop Guard        → changed-surface justification gate
```

Git diff line ranges can map to changed symbols before bounded reverse traversal. Test Intelligence v3 uses structural `TESTS` relationships and fallback evidence to produce prioritized P0/P1/P2 verification candidates.

See [`PRD-v0.8.md`](PRD-v0.8.md).

# Project Brain

Project Brain preserves durable, source-backed project knowledge between tasks and hosts.

Useful durable entries include:

- decisions;
- constraints;
- interfaces;
- architecture patterns;
- known bugs/risks.

It does not store secrets, raw logs, tool transcripts, personal data, speculative hypotheses, transient Execution Guard observations, or full conversation history.

Freshness states:

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
- **Execution Guard** — require evidence-backed next actions and stop zero-delta loops;
- **Contradiction Gate** — resolve material observation conflicts before mutation;
- **Hypothesis Ledger** — prevent rejected guesses from silently cycling back;
- **Evidence Delta Gate** — block equivalent repeat work when evidence/repository state did not change;
- **Scope Guard** — keep every changed surface attributable to the task;
- **Impact & Test Intelligence** — inspect likely dependents and prioritize verification;
- **Slop Guard** — reject unresolved unjustified engineering before completion;
- **Underengineering Counter-Gate** — preserve necessary complexity;
- **Stop Engine** — stop once behavior, verification, execution, scope, Anti-Slop, freshness, and persistence gates are satisfied.

# Quick start

## OpenAI Codex

```sh
codex plugin marketplace add ahfaruq/codemium --ref main
codex plugin add codemium@codemium
```

After installing or refreshing the marketplace/plugin source, review lifecycle hook trust with `/hooks` when required, then start a fresh session if plugin inventory is cached.

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

See [`INSTALL.md`](INSTALL.md), [`HOSTS.md`](HOSTS.md), [`PRD-v0.10.md`](PRD-v0.10.md), [`CHANGELOG.md`](CHANGELOG.md), and [`RELEASE_NOTES-v0.10.0.md`](RELEASE_NOTES-v0.10.0.md).

# Benchmark suite

Codemium keeps competitive performance claims separate from deterministic implementation/quality gates.

## v0.8 competitive efficiency

The existing v0.8 dashboard remains historical benchmark evidence:

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

See [`benchmarks/V08_BENCHMARK_SUITE.md`](benchmarks/V08_BENCHMARK_SUITE.md).

## v0.9 Anti-Slop release calibration

v0.9 retains a labeled blocker-semantics corpus and deterministic calibration runner:

```sh
python benchmarks/calibrate_v09_blocking.py
```

This is a release-quality gate, not a competitive AI performance benchmark.

## v0.10 Execution Intelligence verification

The deterministic Execution Guard fixture protects contradiction handling, UI stabilization, rejected-hypothesis reuse, evidence-delta stopping, and repeated build/deploy/probe behavior.

No numeric v0.10 token/cost/time improvement claim is published from deterministic fixtures alone. Representative measured agent runs are required before publishing competitive efficiency claims.

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
    ├── execution/
    ├── slop-report.json
    ├── slop-adjudications.json
    ├── persistence-gates/
    └── snapshots/
```

Durable sanitized Project Brain knowledge is vendor-neutral. Repository graph/test maps, active task state, cache, Execution Guard ledgers, Slop reports/adjudications, and persistence gates are transient/regenerable state and are ignored by Git by default.

# Deterministic helpers

Normal users do not need to run these manually. They are useful for diagnostics, testing, and host adapters:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/project_brain.py --root . freshness
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/graph_query.py --root . callers "refresh_session"
python plugins/codemium/engine/working_set.py --root . --query "auth refresh" --top 8
python plugins/codemium/engine/impact.py --root . --git-diff
python plugins/codemium/engine/execution_guard.py --root . status
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

Portable installs copy the shared Agent Skill, Execution Intelligence policy, Anti-Slop policy, and canonical deterministic engine.

# Verification model

## 1. Core CI — every push / pull request

```sh
python scripts/verify_core.py
```

Core CI validates engine syntax, Project Brain invariants, Structural Intelligence contracts, task/depth behavior, Execution Guard mechanics, the Contradiction Gate, Evidence Delta Gate, Hypothesis Ledger, Slop Guard mechanics, finding provenance, evidence-backed adjudication, CLEANUP classification, the Underengineering Counter-Gate, and v0.9 blocker calibration.

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

# v0.10 scope boundaries

Codemium v0.10 is not:

- a token-budget enforcer;
- an arbitrary action-count limiter;
- permission to skip required verification merely because an action appears expensive;
- a generic linter replacement;
- a code minimizer or code-golf tool;
- a repository-wide desloppification pass on every task;
- a generic graph visualization product or language server;
- GraphRAG/vector-database infrastructure;
- an AI-authorship detector;
- permission to remove defensive/security/compatibility/test complexity without behavioral evidence;
- evidence for a numeric v0.10 competitive efficiency improvement claim by itself.

The two product rules now work together:

> **Every action must buy information or produce the solution.**
>
> **Everything the solution needs. Nothing it does not.**

# Status

`v0.10.0` introduces **Execution Intelligence** while preserving v0.9 Anti-Slop Intelligence, v0.8 Polyglot Intelligence, and Project Brain. Execution Guard is task-aware, contradiction-aware, evidence-delta-driven, and designed to stop repeated no-gain investigation before mutation/build/deployment loops waste model/tool usage. Slop Guard still reviews the final changed surface, and the Underengineering Counter-Gate still protects necessary complexity. Codex remains the stable/reference adapter; Claude Code, Gemini CLI, Cursor, and OpenCode share the same vendor-neutral core through their adapters.

# Support Codemium

Codemium is open source. If it helps your workflow or team, consider supporting continued compatibility testing, documentation, benchmarks, host integrations, and maintenance through GitHub Sponsors.

❤️ [Sponsor Codemium](https://github.com/sponsors/ahfaruq)

# License

MIT
