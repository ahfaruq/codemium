# Model Capability Layer

Codemium policy is capability-based, not permanently tied to a named GPT generation.

Typical contracts:

- primary: frontier reasoning, strong coding, reliable tool use;
- reviewer: frontier reasoning, risk detection, fresh-context capability;
- bounded worker: strong coding/instruction following where delegation creates net value.

Reasoning profiles are capabilities too. The engine currently knows the supported effort labels for selected model families so it can avoid recommending an unavailable level. Unknown/new models remain advisory until their capabilities are verified.

Current registry examples:

- GPT-5.6 / Sol / Terra / Luna: `none`, `low`, `medium`, `high`, `xhigh`, `max`.
- GPT-5.3-Codex and GPT-5.2-Codex: `low`, `medium`, `high`, `xhigh`.

Do not automatically promote a new model because it is newer. Benchmark representative project tasks, preserve the quality floor first, then compare real tokens/cost/latency/tool reliability. Test the same reasoning level and, where sensible, one level lower before assuming a newer model needs the same compute.

Never claim a model configuration was benchmarked or a host effort was changed without evidence from the benchmark/runtime.
