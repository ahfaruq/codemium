# Codemium Competitive Benchmarks

Codemium treats performance claims as engineering evidence, not marketing copy.

The benchmark is explicitly competitive: **Codemium is compared against baseline, caveman, and Ponytail on the same work.** Ponytail is a comparison target, not a parent framework or positioning reference for Codemium.

> **Assumed benchmark:** [`ASSUMED_NUMBERS.md`](ASSUMED_NUMBERS.md) publishes the current synthetic scenario model. It is explicitly **not measured product performance**.
>
> **Measured benchmark program:** [`PUBLIC_BENCHMARK.md`](PUBLIC_BENCHMARK.md) defines the evidence gate for future real runs. Measured datasets belong in [`results/`](results/).

## Primary benchmark arms

A public competitive study must include:

- `baseline` — same coding agent, model, reasoning configuration, and environment with no optimization skill;
- `caveman` — terse-prose/minimal-control benchmark arm;
- `ponytail` — Ponytail on the identical task set and repository starts;
- `codemium` — Codemium `@cm` on those identical conditions.

Internal Codemium variants such as `codemium-fast`, `codemium-deep`, different reasoning efforts, or feature-disabled builds are **ablation studies**. They should not replace the four primary competitive arms.

## Fair-comparison protocol

For every arm:

1. use the same task/ticket text;
2. start from the same repository commit or clean fixture;
3. use the same coding agent host;
4. use the same base model and host reasoning configuration unless the study explicitly tests reasoning policy;
5. use the same tools, network permissions, environment, timeout, and dependency state;
6. isolate runs so one arm cannot inherit another arm's context;
7. score the final diff and observable behavior using the same evaluator;
8. record raw run data before aggregation;
9. use repeated runs (`n >= 4` recommended) because agentic results vary.

Where practical, quality/safety scoring should be blind to the arm identity.

## Publication rule

A public **measured Numbers** chart may be rendered only when:

- `meta.kind` is exactly `measured`;
- the `baseline`, `caveman`, `ponytail`, and `codemium` arms all exist;
- the four arms cover identical task IDs;
- quality and safety results are recorded for every competitive run;
- measured token values come from host telemetry;
- measured cost comes from billing/run telemetry rather than fabricated or stale pricing estimates.

Synthetic data may be published only when it remains visibly labeled as synthetic/assumed and is never represented as measured product performance.

## Core public metrics

Lower is better:

- LOC changed;
- total tokens = input + reasoning + output;
- measured cost;
- wall-clock time.

Higher is better:

- quality pass rate;
- safety pass rate.

Diagnostic metrics should also be retained:

- tool calls;
- unique files read;
- duplicate reads;
- unrelated changed lines;
- tests/checks executed;
- regression findings;
- context/cache reuse where measurable.

## Quality gate

Efficiency is not a win when correctness or safety falls.

A Codemium result should only be described as better when the quality floor is preserved:

```text
quality >= baseline/control quality
safety  >= baseline/control safety
regressions <= controls
```

Only after that should LOC, tokens, cost, and time be compared.

## Dataset format

```json
{
  "meta": {
    "kind": "measured",
    "study_type": "competitive",
    "title": "Codemium competitive agent benchmark",
    "repository": "owner/repo@commit",
    "agent": "Codex",
    "model": "same model + reasoning configuration",
    "runs_per_arm": 4,
    "required_arms": ["baseline", "caveman", "ponytail", "codemium"]
  },
  "runs": [
    {
      "task_id": "ticket-01",
      "system": "baseline",
      "quality_pass": true,
      "safety_pass": true,
      "input_tokens": 12345,
      "reasoning_tokens": 2345,
      "output_tokens": 678,
      "cost_usd": 0.0123,
      "loc_changed": 42,
      "seconds": 90
    }
  ]
}
```

Each `task_id` must appear in every primary arm for publication.

## Render

Synthetic/assumed scenario:

```sh
python benchmarks/render_numbers.py \
  benchmarks/example-runs-v2.json \
  --svg benchmarks/demo-numbers.svg \
  --markdown benchmarks/demo-NUMBERS.md
```

Publish measured competitive results:

```sh
python benchmarks/render_numbers.py \
  benchmarks/results/<study>.json \
  --publish \
  --svg benchmarks/numbers.svg \
  --markdown benchmarks/NUMBERS.md
```

The renderer is stdlib-only. System colors are intentionally stable in the primary chart:

- baseline — gray;
- caveman — orange;
- ponytail — green;
- codemium — purple.

## Current public status

As of 2026-08-18, the repository publishes an **explicitly synthetic assumption model** in [`ASSUMED_NUMBERS.md`](ASSUMED_NUMBERS.md): Codemium is modeled at approximately **-45% LOC, -31% tokens, -29% cost, and -28% time vs baseline**, with the same assumed quality/safety floor.

No complete measured Codemium-vs-baseline-vs-caveman-vs-Ponytail dataset is committed yet, so those percentages are **not measured product-performance claims**.
