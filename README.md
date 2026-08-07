# Codemium

**Persistent coding intelligence for Codex.**

Codemium is a Codex-first plugin for long-running software projects. Its goal is not the fewest lines of code or the shortest prompt. Its goal is the **smallest justified engineering change** while preserving project understanding, correctness, testing depth, architecture, scope discipline, and token efficiency.

> **Positioning:** the senior engineer who already knows your codebase.

## Why Codemium

Coding agents often pay repeatedly for the same understanding: rereading unchanged files, rediscovering architecture, repeating searches/tests, carrying stale conversation history, creating abstractions that the project already solved, or touching nearby code outside the task.

Codemium turns a repository into a persistent engineering memory:

- **Project Brain** — durable decisions, constraints, interfaces, patterns, and known bugs.
- **Repository Intelligence** — lightweight file/symbol/import/test graph built deterministically.
- **Task Compiler** — converts requests into scoped BUILD/FIX/TEST/REFACTOR/REVIEW/MIGRATION/SECURITY contracts.
- **Working Set Engine** — ranks only the files and project knowledge relevant to the current task.
- **Scope Guard** — detects files changed outside the task's allowed surface.
- **Impact Engine** — estimates callers, related tests, interfaces, and blast radius.
- **Test Intelligence** — maps changed source to likely tests; testing depth follows risk, not code minimalism.
- **Read/Search Cache** — reuses deterministic work when repository state has not changed.
- **Stop Engine doctrine** — stop once the requested behavior is proven and material uncertainty is resolved.
- **Model capability abstraction** — no permanent dependency on a specific GPT generation.

## Install

```sh
codex plugin marketplace add admahmad/codemium --ref main
codex plugin add codemium@codemium
```

Start a fresh Codex task after installation.

Use the primary skill:

```text
Use $codemium:codemium for this coding task.
```

Or a focused skill:

```text
$codemium:init
$codemium:fix
$codemium:test
$codemium:review
$codemium:audit
$codemium:health
```

## Initialize a project

From the target repository root:

```sh
python <plugin-dir>/engine/project_brain.py init --root .
python <plugin-dir>/engine/repo_graph.py build --root .
python <plugin-dir>/engine/test_map.py build --root .
```

This creates `.codemium/`. Runtime/generated data is ignored by default; durable project knowledge can be reviewed and committed if the team wants it shared.

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

## Example workflow

```sh
# 1. Compile a user request into a task contract
python <plugin-dir>/engine/task_compiler.py \
  --root . \
  --request "Customer receives two emails after one order completes"

# 2. Build/update repository intelligence
python <plugin-dir>/engine/repo_graph.py build --root .

# 3. Generate a bounded working set
python <plugin-dir>/engine/working_set.py \
  --root . \
  --query "duplicate order email notification" \
  --top 12

# 4. After edits, inspect blast radius
python <plugin-dir>/engine/impact.py --root . --git-diff

# 5. Check for scope pollution
python <plugin-dir>/engine/scope_guard.py --root .

# 6. Project health / deterministic telemetry
python <plugin-dir>/engine/health.py --root .
python <plugin-dir>/engine/telemetry.py --root .
```

## Engineering doctrine

Codemium uses this solution ladder **after** the problem is understood:

1. Is the requested behavior actually required?
2. Does the codebase already solve it?
3. Does the standard library solve it?
4. Does the native platform/framework solve it?
5. Does an existing dependency solve it?
6. Can a local simple implementation solve it?
7. Only then add a new abstraction or dependency.

The center of gravity is **minimum justified engineering**, not minimum LOC. A 25-line correct change is better than a 5-line fragile change.

## Testing is not minimized

Production-code minimalism must never be used as a reason to under-test. Codemium selects verification by blast radius and risk:

- V0 — reasoning-only for genuinely trivial/non-behavioral changes
- V1 — syntax/lint/type checks
- V2 — targeted tests
- V3 — subsystem/integration tests
- V4 — full build/test boundary
- V5 — runtime/E2E/environment verification

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

`v0.1.0` is an MVP focused on persistent project intelligence, bounded task context, task-aware engineering policy, scope control, impact/test mapping, deterministic reuse, and evidence-backed stopping.

## License

MIT
