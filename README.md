# Codemium

**Persistent coding intelligence for Codex.**

Codemium is a Codex-first plugin for long-running software projects. It aims for the **smallest justified engineering change** while preserving project understanding, correctness, testing depth, architecture, scope discipline, and token efficiency.

> **Positioning:** the senior engineer who already knows your codebase.

## The short UX

The primary tag is intentionally tiny:

```text
@cm
```

That is the normal/default experience. Codemium automatically detects both the coding task and the engineering depth.

Optional depth overrides:

```text
@cm fast
@cm deep
@cm critical
```

There is deliberately no need to type `normal`; plain `@cm` is auto mode and will usually resolve to NORMAL for ordinary work.

Examples:

```text
@cm fix the profile save bug
@cm fast adjust the card spacing
@cm deep investigate why the websocket disconnects intermittently
@cm critical change the authentication flow
```

Focused shortcuts are available when you want to pin the task type:

```text
@cm-fix
@cm-test
@cm-review
@cm-audit
@cm-health
@cm-init
```

Focused shortcuts can also receive a depth override when it makes sense:

```text
@cm-fix deep
@cm-test critical
@cm-review deep
```

## Depth model

Depth controls **engineering investigation and verification depth**, not a promise to switch the host model's reasoning setting.

- **FAST** — obvious, localized, low-risk work; narrow context and targeted verification.
- **NORMAL** — default project-aware engineering for ordinary tasks.
- **DEEP** — complex debugging, concurrency, distributed/cross-boundary behavior, performance, or material uncertainty.
- **CRITICAL** — authentication/authorization, payments, migrations, secrets, production data, destructive operations, infrastructure/deployment, or breaking public interfaces.

Explicit depth can increase rigor, but it cannot lower the safety floor. For example, `@cm fast` on an authentication change is automatically escalated to CRITICAL.

## Why Codemium

Coding agents often pay repeatedly for the same understanding: rereading unchanged files, rediscovering architecture, repeating searches/tests, carrying stale conversation history, creating abstractions that the project already solved, or touching nearby code outside the task.

Codemium turns a repository into persistent engineering memory:

- **Project Brain** — durable decisions, constraints, interfaces, patterns, and known bugs.
- **Repository Intelligence** — lightweight file/symbol/import/test graph built deterministically.
- **Task Compiler** — detects BUILD/FIX/TEST/REFACTOR/REVIEW/MIGRATION/SECURITY plus FAST/NORMAL/DEEP/CRITICAL depth.
- **Working Set Engine** — ranks only files and project knowledge relevant to the task.
- **Scope Guard** — detects files changed outside the allowed surface.
- **Impact Engine** — estimates affected code/tests and blast radius.
- **Test Intelligence** — testing follows behavior and risk, never production-code minimalism.
- **Read/Search Cache** — reuses deterministic work when repository state has not changed.
- **Stop Engine** — stops once requested behavior is proven and material uncertainty is resolved.
- **Model capability abstraction** — no permanent dependency on one GPT generation.

## Install

```sh
codex plugin marketplace add admahmad/codemium --ref main
codex plugin add codemium@codemium
```

Start a fresh Codex task after installation, then use `@cm`.

## Initialize a project

`@cm` may initialize project intelligence when `.codemium/` is missing and durable state creates value. Manual initialization is also available with `@cm-init` or the deterministic helpers:

```sh
python <plugin-dir>/engine/project_brain.py init --root .
python <plugin-dir>/engine/repo_graph.py build --root .
python <plugin-dir>/engine/test_map.py build --root .
```

Project state:

```text
.codemium/
├── PROJECT.md
├── architecture/
│   └── system.json
├── registry/
│   ├── decisions.jsonl
│   ├── constraints.jsonl
│   ├── interfaces.jsonl
│   ├── patterns.jsonl
│   └── bugs.jsonl
├── repository/
│   ├── graph.json
│   └── tests.json
├── tasks/
│   └── active.json
└── runtime/
    ├── cache.jsonl
    ├── operations.jsonl
    └── snapshots/
```

## Task compiler

The deterministic task compiler mirrors the tag behavior:

```sh
python <plugin-dir>/engine/task_compiler.py \
  --root . \
  --request "Investigate intermittent queue race bug"
```

Explicit override:

```sh
python <plugin-dir>/engine/task_compiler.py \
  --root . \
  --depth deep \
  --request "Investigate intermittent queue race bug"
```

Supported CLI overrides are `auto`, `fast`, `deep`, and `critical`. NORMAL is an internal auto-selected depth.

## Engineering doctrine

Codemium uses this solution ladder **after** the problem is understood:

1. Is the requested behavior actually required?
2. Does the codebase already solve it?
3. Does the standard library solve it?
4. Does the native platform/framework solve it?
5. Does an existing dependency solve it?
6. Can a local simple implementation solve it?
7. Only then add a new abstraction or dependency.

The center of gravity is **minimum justified engineering**, not minimum LOC.

## Testing is not minimized

Production-code minimalism must never be used as a reason to under-test. Verification depth follows blast radius and risk, from targeted local checks through subsystem/full/runtime verification where justified.

## Token claims

Codemium does **not** invent exact token savings. If the host exposes real token usage, benchmark it. Otherwise Codemium reports deterministic proxies such as working-set size, duplicate operations, repeated reads, test reuse, and persistent-state footprint.

## Validate this repository

```sh
sh plugins/codemium/scripts/verify.sh
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File plugins/codemium/scripts/verify.ps1
```

## Status

`v0.2.0` adds the short `@cm` UX and adaptive FAST/NORMAL/DEEP/CRITICAL engineering depth on top of the v0.1 project-intelligence MVP.

## License

MIT
