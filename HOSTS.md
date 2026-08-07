# Codemium Hosts

Codemium is **host-agnostic at the product/core level**. Each coding agent gets a thin native adapter that translates Codemium's task/depth/project-intelligence contract into that host's extension or Agent Skill model.

## Support matrix

| Host | Status | Native surface | Explicit invocation |
| --- | --- | --- | --- |
| OpenAI Codex | Stable | Codex plugin + Agent Skills | `$cm` |
| Claude Code | Beta | repository-root Claude plugin + Agent Skill + slash command | `/codemium:cm` |
| Gemini CLI | Beta | Gemini extension + context file + custom command | `/cm` |
| Cursor | Beta | portable Agent Skill | `/cm` / skill picker |
| OpenCode | Beta | portable Agent Skill with slash metadata | `/cm` where exposed; otherwise skill tool/auto-selection |

**Stable** means the adapter is the reference implementation and repository contract is fully exercised by Codemium's fixture/verification suite. **Beta** means the packaging follows the host's documented extension/skill surface and is validated structurally in CI, but a release is not promoted to Stable until it is also exercised on the real host runtime.

## Adapter contract

A host adapter may change syntax and host-specific configuration, but it must preserve these Codemium invariants:

1. Task classification: BUILD, FIX, TEST, REFACTOR, REVIEW, MIGRATION, SECURITY.
2. Engineering depth: FAST, NORMAL, DEEP, CRITICAL with a safety floor.
3. Persistent `.codemium/` project knowledge where the host can access the workspace.
4. Bounded working sets and targeted context expansion.
5. Smallest justified engineering change; no unrelated cleanup.
6. Testing and verification based on behavior/risk, never LOC minimalism.
7. Reuse unchanged deterministic evidence when validity can be proven.
8. Explicit completion/stop conditions.
9. Host model/reasoning controls remain host-owned unless a safe per-task mechanism is documented and confirmed.
10. The adapter must not fork project memory into a vendor-specific durable state format.

## Invocation is host-native

Codemium intentionally does not fake one universal trigger when hosts expose different native mechanisms.

- **Codex:** explicit skills use `$<skill-name>`, therefore `$cm`.
- **Claude Code:** installed plugin commands are namespaced, therefore `/codemium:cm`; the `cm` skill may also auto-activate.
- **Gemini CLI:** extension command `commands/cm.toml` becomes `/cm`.
- **Cursor:** Agent Skills can be selected by the agent/skill UI and current releases expose skills in the slash menu; use `/cm` where available.
- **OpenCode:** Agent Skills are advertised to the agent and loaded through the native skill tool. Codemium sets `opencode/slash: "true"` for releases that expose slash invocation.

The short identifier is always **`cm`** even though the host marker differs.

## Shared state

All adapters use the same project-state namespace:

```text
.codemium/
```

A project initialized under one supported host should remain understandable to another adapter. Host-specific transient state must not pollute durable project decisions, constraints, interfaces, patterns, or bug history.

## Shared deterministic engine

The canonical engine lives at:

```text
plugins/codemium/engine/
```

Distribution strategy:

- Codex plugin: engine is inside the plugin root.
- Claude Code: repository root is the plugin root, so the same engine is available through `${CLAUDE_PLUGIN_ROOT}/plugins/codemium/engine/`.
- Gemini CLI: repository root is installed as the extension, so the core remains part of the extension bundle.
- Cursor/OpenCode: `scripts/install_host.py` copies the portable Agent Skill plus the canonical engine/references into the host's skill directory.

The engine is an optimization layer. An adapter must still preserve Codemium doctrine if a host cannot or should not execute a helper script for a specific task.

## Reasoning portability

Codemium core uses portable classes:

| Depth | Portable reasoning class |
| --- | --- |
| FAST | economy |
| NORMAL | balanced |
| DEEP | strong |
| CRITICAL | frontier |

Vendor-specific reasoning knobs are adapter mappings, not core semantics.

The Codex adapter currently maps these classes to `low`, `medium`, `high`, and `xhigh` when the active model supports them. Claude Code, Gemini CLI, Cursor, and OpenCode remain host-owned unless their runtime exposes a documented, safe, confirmable per-task control.

## Portable Agent Skill installation

Cursor user scope:

```sh
python scripts/install_host.py --host cursor
```

OpenCode user scope:

```sh
python scripts/install_host.py --host opencode
```

Project-local variants use `--scope project --project <path>`.

The installer refuses to overwrite/remove a directory it cannot identify as Codemium-owned unless `--force` is explicitly provided.

## Promotion policy

A Beta adapter is promoted to Stable only after all of the following are true:

- manifest/skill layout matches current host documentation;
- repository CI validates the adapter bundle;
- installation succeeds in the actual host;
- explicit invocation resolves to Codemium correctly;
- a fixture project demonstrates Project Brain reuse, bounded context behavior, scoped editing, and verification;
- update/uninstall behavior is documented and tested;
- no host-specific behavior silently weakens the Codemium safety floor.

Run `python scripts/doctor.py` for repository-level adapter validation and host-binary availability.
