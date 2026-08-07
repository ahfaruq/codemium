# Model Capability Layer

Codemium policy is capability-based and host-agnostic. It is not permanently tied to GPT, Claude, Gemini, Cursor, OpenCode, or a named model generation.

Typical role contracts:

- primary: frontier reasoning, strong coding, reliable tool use;
- reviewer: frontier reasoning, risk detection, fresh-context capability;
- bounded worker: strong coding/instruction following where delegation creates net value.

## Portable reasoning classes

Codemium core uses `economy`, `balanced`, `strong`, and `frontier` as vendor-neutral reasoning classes. Host adapters may map those classes to native knobs only when the mapping is verified.

## Current Codex capability registry

The Codex adapter currently knows selected GPT effort labels so it can avoid recommending an unavailable level:

- GPT-5.6 / Sol / Terra / Luna: `none`, `low`, `medium`, `high`, `xhigh`, `max`.
- GPT-5.3-Codex and GPT-5.2-Codex: `low`, `medium`, `high`, `xhigh`.

These are Codex adapter details, not Codemium core semantics.

## Other hosts

Claude Code, Gemini CLI, Cursor, and OpenCode adapters intentionally leave vendor model/thinking effort host-owned unless the current host documents a safe per-task control and the runtime can confirm the effective setting.

Do not invent equivalences such as `Claude X = high`, `Gemini Y = xhigh`, or a Cursor/OpenCode model name = a Codemium reasoning class. Engineering depth remains portable even when host compute controls are unavailable.

## Promotion policy

Do not automatically promote a new model because it is newer. Benchmark representative project tasks, preserve the quality floor first, then compare correctness, real tokens/cost/latency, tool reliability, and regression behavior.

Likewise, do not promote a host adapter from beta to stable merely because its manifest or skill loads. Stable means the full Codemium contract—durable state, bounded context, scoped engineering, verification, update/uninstall behavior, and stop behavior—has been exercised on representative real projects in that host.

Never claim a model configuration was benchmarked or a host reasoning setting changed without evidence from the benchmark/runtime.
