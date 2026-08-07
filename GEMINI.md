# Codemium bootstrap

Codemium is a **host-agnostic coding-intelligence layer**. Keep this always-loaded extension context intentionally small.

- Explicit user entry point: `/cm`.
- The extension also ships the `cm` Agent Skill under `skills/cm/SKILL.md`; use that skill when Codemium behavior is relevant instead of expanding this bootstrap into a large persistent prompt.
- Durable project intelligence lives in `.codemium/` and is portable across supported hosts.
- Prefer bounded working sets, relevant durable facts, and targeted evidence over broad repository rereads.
- Make the smallest **justified** change, never unrelated cleanup.
- Verification follows behavior, blast radius, and risk; minimal production code never means minimal tests.
- FAST/NORMAL/DEEP/CRITICAL are engineering-depth policies. Safety can escalate depth.
- Gemini model/thinking configuration remains host-owned unless Gemini CLI documents and confirms a per-task control.
- Stop when requested behavior is proven, verification is sufficient, scope is clean, and no material unexplained uncertainty remains.

Load detailed Codemium instructions from the `cm` Agent Skill only when needed.
