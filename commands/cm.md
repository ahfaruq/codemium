---
name: cm
description: Run Codemium on a coding task with optional fast, deep, or critical engineering depth.
argument-hint: "[fast|deep|critical] <coding task>"
---

Use the `cm` Codemium skill for the following request:

$ARGUMENTS

Interpret a leading `fast`, `deep`, or `critical` as the requested engineering-depth override. Otherwise use automatic depth. Apply the safety floor, shared `.codemium/` Project Brain, bounded working set, smallest justified change, risk-aware verification, scope guard, deterministic reuse, and explicit stop condition.

When deterministic helpers would reduce repeated model work, this Claude Code plugin is installed from the repository root, so the canonical engine is available at `${CLAUDE_PLUGIN_ROOT}/plugins/codemium/engine/`. Do not run helpers mechanically for trivial tasks.
