# Codemium Hosts

Codemium is **host-agnostic at the product/core level**. Each coding agent gets a thin native adapter that translates Codemium's task/depth/project-intelligence contract into that host's extension model.

## Support matrix

| Host | Status | Native surface | Primary invocation |
| --- | --- | --- | --- |
| OpenAI Codex | Stable | Codex plugin + Agent Skills | `@cm` |
| Claude Code | Beta | Claude plugin + Agent Skill + slash command | auto skill or `/codemium:cm` |
| Gemini CLI | Beta | Gemini extension + context file + custom command | `/cm` |
| Cursor | Planned | Adapter TBD against current official extension surface | TBD |
| OpenCode | Planned | Adapter TBD against current official extension surface | TBD |

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

## Host-specific reasoning

Codemium depth is portable; vendor reasoning knobs are not.

- Codex currently maps depth to a preferred GPT reasoning profile when the model/runtime supports those labels.
- Claude Code adapter currently treats depth as engineering/context rigor and does not claim to change Claude thinking configuration.
- Gemini CLI adapter currently treats depth as engineering/context rigor and does not claim to change Gemini thinking configuration.

This separation prevents Codemium from binding its core architecture to one vendor's model controls.

## Shared state

All adapters use the same project-state namespace:

```text
.codemium/
```

A project initialized under one supported host should remain understandable to another adapter. Host-specific transient state must not pollute durable project decisions, constraints, interfaces, patterns, or bug history.
