# Codemium

**Persistent coding intelligence for AI coding agents.**

Codemium is a host-agnostic engineering layer for long-running software projects. It aims for the **smallest justified engineering change** while preserving project understanding, correctness, testing depth, architecture, scope discipline, and context efficiency.

> **Positioning:** the senior engineer who already knows your codebase.

Codemium keeps durable project intelligence in `.codemium/`, then exposes the same engineering doctrine through native adapters for each coding-agent host.

## Supported hosts

| Host | Status | Native integration | Explicit invocation |
| --- | --- | --- | --- |
| OpenAI Codex | **Stable** | Codex plugin + Agent Skills | `$cm` |
| Claude Code | **Beta** | Claude plugin + Agent Skill + command | `/codemium:cm` |
| Gemini CLI | **Beta** | Gemini extension + context + command | `/cm` |
| Cursor | **Beta** | Portable Agent Skill | `/cm` / skill picker |
| OpenCode | **Beta** | Portable Agent Skill | `/cm` when slash exposure is supported, otherwise skill tool/auto-selection |

See [`HOSTS.md`](HOSTS.md) for the adapter contract and [`INSTALL.md`](INSTALL.md) for installation details.

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
        ┌───────────┬───────┼────────┬────────────┐
        │           │       │        │            │
      Codex       Claude  Gemini   Cursor      OpenCode
        │           │       │        │            │
       $cm    /codemium:cm  /cm      /cm        cm skill
```

Invocation syntax, extension format, model controls, and tool surfaces are host-specific. The engineering invariants are not.

## Core behavior

Codemium classifies work as BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, or SECURITY and then chooses the smallest safe engineering depth:

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
- **Stop Engine** — stop once the requested result is sufficiently proven;
- **Model Capability Layer** — engineering depth is portable while vendor reasoning knobs remain host-owned.

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

Codex's native explicit Agent Skill syntax is `$<skill-name>`:

```text
$cm fix the profile save bug
$cm fast adjust the card spacing
$cm deep investigate why the websocket disconnects intermittently
$cm critical change the authentication flow
```

Focused skills:

```text
$cm-fix
$cm-test
$cm-review
$cm-audit
$cm-health
$cm-init
```

> **v0.6 migration note:** earlier Codemium drafts documented `@cm`. Current Codex uses `$cm` for explicit skill invocation, so v0.6 standardizes on the native marker.

### Codex reasoning mapping

Codemium's portable reasoning classes map to current Codex effort preferences when supported:

| Depth | Portable class | Codex preference |
| --- | --- | --- |
| FAST | economy | `low` |
| NORMAL | balanced | `medium` |
| DEEP | strong | `high` |
| CRITICAL | frontier | `xhigh` |

Codemium never silently rewrites the global Codex model/reasoning selector. A host-effort change is only reported when the runtime confirms it.

---

# Claude Code

Claude Code uses the repository itself as the plugin root so the Claude adapter has access to the shared deterministic engine.

## Install

Inside Claude Code:

```text
/plugin marketplace add admahmad/codemium
/plugin install codemium@codemium
```

Start a new Claude Code session after installation if the host has not refreshed plugin discovery yet.

## Use

Claude may auto-select the `cm` Agent Skill when relevant, or invoke explicitly:

```text
/codemium:cm fix the profile save bug
/codemium:cm fast adjust the card spacing
/codemium:cm deep investigate a race condition
/codemium:cm critical change authorization behavior
```

Claude model/thinking controls remain Claude-owned unless the host documents and confirms a per-task control.

---

# Gemini CLI

Codemium is packaged as a native Gemini CLI extension with `gemini-extension.json`, `GEMINI.md`, and `/cm`.

## Install

From a terminal:

```sh
gemini extensions install https://github.com/admahmad/codemium --ref main
```

Restart Gemini CLI after installation or update so extension commands/context refresh.

## Use

```text
/cm fix the profile save bug
/cm fast adjust the card spacing
/cm deep investigate a race condition
/cm critical change authentication behavior
```

---

# Cursor

Cursor supports Agent Skills. Codemium installs the portable `cm` bundle together with its deterministic engine and references.

## User-wide install

```sh
python scripts/install_host.py --host cursor
```

## Project-local install

```sh
python scripts/install_host.py --host cursor --scope project --project /path/to/project
```

Then use the `cm` Agent Skill when Cursor discovers it; current Cursor releases expose skills in the slash menu, so `/cm` is the intended short invocation where available.

---

# OpenCode

OpenCode natively discovers Agent Skills. Codemium installs into OpenCode's documented skill directories and sets `opencode/slash: "true"` metadata.

## User-wide install

```sh
python scripts/install_host.py --host opencode
```

## Project-local install

```sh
python scripts/install_host.py --host opencode --scope project --project /path/to/project
```

OpenCode can auto-select/load `cm` via its skill tool. On versions exposing skill slash invocation, use `/cm`.

---

# Shared Project Brain

All adapters use the same project state:

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

A project initialized under one host can be understood by another host because durable state is vendor-neutral.

## Deterministic core helpers

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/test_map.py build --root .
python plugins/codemium/engine/working_set.py --root . --query "auth refresh" --top 8
```

They are optional accelerators, not mandatory ceremony. Use them when they reduce repeated model work.

## Host installer safety

`scripts/install_host.py` manages only its Codemium-owned skill directory. It refuses to overwrite or remove a non-Codemium directory unless `--force` is explicitly supplied.

Dry-run example:

```sh
python scripts/install_host.py --host cursor --dry-run
```

Uninstall:

```sh
python scripts/install_host.py --host cursor --uninstall
python scripts/install_host.py --host opencode --uninstall
```

## Doctor

Validate the repository and see which host binaries are available locally:

```sh
python scripts/doctor.py
```

Require one host binary when testing an adapter locally:

```sh
python scripts/doctor.py --require-host codex
python scripts/doctor.py --require-host claude-code
python scripts/doctor.py --require-host gemini-cli
python scripts/doctor.py --require-host cursor
python scripts/doctor.py --require-host opencode
```

## Repository verification

Linux/macOS:

```sh
sh plugins/codemium/scripts/verify.sh
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File plugins/codemium/scripts/verify.ps1
```

## Status

`v0.6.0` makes the host boundary explicit: Codex uses native `$cm`; Claude Code uses a repository-root plugin with the shared engine; Gemini CLI uses a native extension; Cursor and OpenCode use a portable Agent Skill installer; and all adapters share the same `.codemium/` project intelligence.

## License

MIT
