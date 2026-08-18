# Codemium Public Competitive Benchmark

**Status:** Public measurement program launched — measured competitive results pending  
**Launch date:** 2026-08-18  
**Release under test:** Codemium v0.7.0

Codemium publishes performance claims only when they are backed by measured run evidence. This page is the canonical public entry point for the competitive benchmark program.

## What is being compared

Every publishable competitive study must run the same task set under four primary arms:

1. `baseline` — the same coding agent without an optimization skill;
2. `caveman` — terse/minimal-control comparison arm;
3. `ponytail` — Ponytail on the identical work;
4. `codemium` — Codemium on the identical work.

The same repository commit, task text, coding-agent host, model, reasoning configuration, tools, permissions, dependency state, timeout policy, and evaluator must be used across arms.

## What is measured

Primary efficiency metrics:

- input, reasoning, output, and total tokens from host telemetry;
- measured run cost from billing/run telemetry;
- wall-clock time;
- LOC changed.

Quality and safety gates:

- quality pass/fail;
- safety pass/fail;
- regressions;
- unrelated changed lines.

Diagnostic evidence should retain tool calls, unique files read, duplicate reads, tests/checks executed, and other host-observable context-efficiency signals when available.

## Publication gate

A result is publishable only when:

- `meta.kind` is `measured`;
- all required competitive arms are present;
- every arm covers identical task IDs;
- quality and safety are recorded for every competitive run;
- token counts come from host telemetry;
- cost comes from measured billing/run telemetry;
- the dataset passes `benchmarks/render_numbers.py --publish`.

Synthetic/demo datasets cannot be relabeled as measured product performance.

## Repetition and evaluation

Agentic runs vary. A competitive study should use at least four runs per arm per task when practical. Final behavior and diff quality should be evaluated with the same rubric for every arm; blind scoring is preferred where practical.

Efficiency only counts as a win after quality and safety floors are preserved:

```text
quality >= baseline/control quality
safety  >= baseline/control safety
regressions <= controls
```

## Results

Measured datasets belong in [`benchmarks/results/`](results/). Once a complete dataset passes the publication gate, generate the public dashboard with:

```sh
python benchmarks/render_numbers.py \
  benchmarks/results/<study>.json \
  --publish \
  --svg benchmarks/numbers.svg \
  --markdown benchmarks/NUMBERS.md
```

`benchmarks/NUMBERS.md` and `benchmarks/numbers.svg` are reserved for measured, publication-gated competitive results.

## Current evidence state

As of 2026-08-18, no complete measured Codemium-vs-baseline-vs-caveman-vs-Ponytail dataset is committed. Therefore this repository does **not** claim competitive token, cost, time, or LOC savings yet.

The existing `demo-NUMBERS.md`, `demo-numbers.svg`, and example datasets remain renderer demonstrations only and are explicitly synthetic.

This distinction is intentional: Codemium treats benchmark numbers as engineering evidence, not marketing copy.
