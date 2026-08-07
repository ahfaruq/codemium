# Codemium

**Persistent coding intelligence for AI coding agents.**

Codemium is a host-agnostic engineering layer for long-running software projects. It aims for the **smallest justified engineering change** while preserving project understanding, correctness, testing depth, architecture, scope discipline, and context efficiency.

> **Positioning:** the senior engineer who already knows your codebase.

Codex is the first stable host. Claude Code and Gemini CLI now have native beta adapters built on the same Codemium doctrine and `.codemium/` project state.

## Supported hosts

| Host | Status | Native integration | Primary invocation |
| --- | --- | --- | --- |
| OpenAI Codex | **Stable** | Codex plugin + Agent Skills | `@cm` |
| Claude Code | **Beta** | Claude plugin + Agent Skill + command | auto skill or `/codemium:cm` |
| Gemini CLI | **Beta** | Gemini extension + context + command | `/cm` |
| Cursor | Planned | host adapter | TBD |
| OpenCode | Planned | host adapter | TBD |

See [`HOSTS.md`](HOSTS.md) for the adapter contract.

## One core, native adapters

```text
                         CODEMIUM
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
     Project Brain     Engineering Core   Shared State
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
               ┌────────────┼────────────┐
               │            │            │
             Codex      Claude Code   Gemini CLI
               │            │            │
             @cm      /codemium:cm      /cm
```

The host may change the invocation syntax, plugin format, model controls, and tool surface. It must not change Codemium's engineering invariants.

## Core behavior

Codemium classifies each task as BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY, then selects the smallest safe engineering depth:

| Depth | Meaning |
| --- | --- |
| FAST | obvious, localized, low-risk work |
| NORMAL | ordinary project-aware engineering |
| DEEP | complex, cross-boundary, intermittent, concurrency/performance work |
| CRITICAL | auth/security, payments, migrations, production data, destructive or breaking changes |

Safety may **escalate** depth but never downgrade below the safe minimum.

Codemium then applies:

- **Project Brain** — durable decisions, constraints, interfaces, patterns, and known bugs;
- **Repository Intelligence** — lightweight file/symbol/import/test discovery;
- **Working Set Engine** — only context relevant to the current task;
- **Scope Guard** — no unrelated edits or opportunistic cleanup;
- **Impact & Test Intelligence** — verification follows behavior and blast radius;
- **Read/Search Reuse** — unchanged deterministic work is not paid for twice;
- **Stop Engine** — stop once the requested result is sufficiently proven.

## Engineering doctrine

After the real requirement is understood:

1. Is the behavior actually required?
2. Does the project already solve it?
3. Does the standard library solve it?
4. Does the native framework/platform solve it?
5. Does an existing dependency solve it?
6. Can a local simple implementation solve it?
7. Only then add a new abstraction or dependency.

The goal is **minimum justified engineering**, not minimum LOC. Minimal production code never means minimal testing.

---

# OpenAI Codex

Codex is currently the stable/reference adapter.

## Install

```sh
codex plugin marketplace add admahmad/codemium --ref main
codex plugin add codemium@codemium
```

Start a fresh Codex task after installation.

## Use

```text
@cm fix the profile save bug
@cm fast adjust the card spacing
@cm deep investigate why the websocket disconnects intermittently
@cm critical change the authentication flow
```

Focused shortcuts remain available:

```text
@cm-fix
@cm-test
@cm-review
@cm-audit
@cm-health
@cm-init
```

### Codex reasoning profile

The Codex adapter currently derives a preferred GPT reasoning effort when the active model supports these labels:

| Codemium depth | Preferred Codex reasoning |
| --- | --- |
| FAST | `low` |
| NORMAL | `medium` |
| DEEP | `high` |
| CRITICAL | `xhigh` |

This is a **preference**, not proof that the host changed. Codemium never silently rewrites global Codex settings and never claims a reasoning change unless the runtime confirms it.

---

# Claude Code

Claude Code support is **beta** and uses its native plugin/Agent Skill model.

## Install

Inside Claude Code:

```text
/plugin marketplace add admahmad/codemium
/plugin install codemium@codemium
```

## Use

Claude can trigger the installed `cm` skill from the task naturally. For explicit invocation:

```text
/codemium:cm fix the profile save bug
/codemium:cm fast adjust card spacing
/codemium:cm deep investigate the intermittent queue race
/codemium:cm critical change authorization behavior
```

The Claude adapter preserves Codemium depth and engineering policy but does **not** claim to modify Claude's thinking/model settings.

---

# Gemini CLI

Gemini CLI support is **beta** and uses its native extension format.

## Install

```sh
gemini extensions install https://github.com/admahmad/codemium --ref main
```

Restart/reload the CLI as required by Gemini CLI after extension changes.

## Use

```text
/cm fix the profile save bug
/cm fast adjust card spacing
/cm deep investigate the intermittent queue race
/cm critical change authorization behavior
```

The command accepts the rest of the line as its task arguments. The Gemini adapter preserves Codemium depth and engineering policy but does **not** claim to modify Gemini thinking/model settings.

---

## Shared project state

All supported adapters use the same durable project namespace:

```text
.codemium/
├── PROJECT.md
├── architecture/
│   └── system.json
├── model-profile.json
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

A project initialized under one supported host should remain understandable to another adapter. Durable project knowledge belongs to the project, not to a model vendor.

## Deterministic engine

The current shared engine lives under `plugins/codemium/engine/` while the multi-host adapter layout stabilizes. It owns Project Brain, repository mapping, task compilation, impact analysis, scope checks, cache reuse, telemetry, and Codex reasoning-profile alignment.

Example:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/test_map.py build --root .
```

## Validate this repository

```sh
sh plugins/codemium/scripts/verify.sh
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File plugins/codemium/scripts/verify.ps1
```

## Status

`v0.5.0` introduces the host-adapter architecture: Codex stable, Claude Code beta, Gemini CLI beta, one shared Codemium engineering doctrine and project state.

## License

MIT
