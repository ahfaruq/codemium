# Codemium Benchmarks

Codemium treats performance claims as engineering evidence, not marketing copy.

## Publication rule

A public **Numbers** chart may be generated from any dataset, but `--publish` refuses the dataset unless:

- `meta.kind` is exactly `measured`;
- the baseline arm exists;
- the same benchmark task set is represented across compared arms;
- quality and safety results are recorded;
- token/cost values come from host or billing telemetry rather than estimates when presented as measured.

Synthetic data is allowed only for renderer/demo testing and must remain visibly labeled **SYNTHETIC / DEMO DATA — NOT CODEMIUM PRODUCT PERFORMANCE**.

## Recommended benchmark arms

For a first real study:

- `vanilla` — same Codex host/model/reasoning without Codemium;
- `codemium-auto` — `@cm` with automatic task/depth policy;
- optionally `ponytail` or another control, if installed and tested on the exact same task set.

Do not compare `@cm fast` and `@cm deep` across different task populations as if they were interchangeable systems. Depth-specific studies should use task sets where that depth is appropriate and clearly report the population.

## Core metrics

Lower is better:

- LOC changed;
- total tokens = input + reasoning + output;
- measured cost;
- wall-clock time.

Higher is better:

- quality pass rate;
- safety pass rate.

Also retain diagnostic metrics such as tool calls, unique files read, duplicate reads, unrelated changed lines, and verification results.

## Dataset format

```json
{
  "meta": {
    "kind": "measured",
    "title": "Codemium agent benchmark",
    "repository": "owner/repo@commit",
    "agent": "Codex",
    "model": "model + reasoning configuration",
    "runs_per_arm": 4
  },
  "runs": [
    {
      "task_id": "ticket-01",
      "system": "vanilla",
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

## Render

Demo:

```sh
python benchmarks/render_numbers.py \
  benchmarks/example-runs-v2.json \
  --svg benchmarks/demo-numbers.svg \
  --markdown benchmarks/demo-NUMBERS.md
```

Publish measured results:

```sh
python benchmarks/render_numbers.py \
  benchmarks/results/<study>.json \
  --publish \
  --svg benchmarks/numbers.svg \
  --markdown benchmarks/NUMBERS.md
```

The renderer is stdlib-only and produces a dark SVG dashboard plus a Markdown summary.

## Current public status

No real Codemium agent-performance dataset is committed yet. `demo-numbers.svg` is deliberately synthetic and exists only to show the dashboard format.
