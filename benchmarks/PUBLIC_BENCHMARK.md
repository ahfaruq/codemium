# Codemium Public Competitive Benchmark

**Status:** Synthetic assumption dashboard published — measured competitive results pending  
**Launch date:** 2026-08-18  
**Release under test:** Codemium v0.7.0

Codemium separates **assumed/synthetic benchmark scenarios** from **measured benchmark evidence**.

The current assumed dashboard is published in [`ASSUMED_NUMBERS.md`](ASSUMED_NUMBERS.md). It models the expected efficiency profile of Codemium using the repository's existing synthetic four-arm dataset and is explicitly **not measured product performance**.

Measured results remain subject to the evidence gate below.

## Current assumed scenario

Using `benchmarks/example-runs-v2.json`, the synthetic model currently shows:

| vs baseline | LOC | tokens | cost | time | quality | safety |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| caveman | -18% | +5% | +4% | +2% | 100% | 100% |
| ponytail | -38% | -19% | -18% | -21% | 100% | 100% |
| **codemium** | **-45%** | **-31%** | **-29%** | **-28%** | **100%** | **100%** |

These figures are assumptions/illustrations only. They are useful as targets and product-positioning scenarios, but they must not be cited as observed benchmark results.

## What is being compared

Every future publishable measured study must run the same task set under four primary arms:

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

## Publication gate for measured results

A result may be labeled **measured** only when:

- `meta.kind` is `measured`;
- all required competitive arms are present;
- every arm covers identical task IDs;
- quality and safety are recorded for every competitive run;
- token counts come from host telemetry;
- cost comes from measured billing/run telemetry;
- the dataset passes `benchmarks/render_numbers.py --publish`.

Synthetic/assumed datasets cannot be relabeled as measured product performance.

## Repetition and evaluation

Agentic runs vary. A measured competitive study should use at least four runs per arm per task when practical. Final behavior and diff quality should be evaluated with the same rubric for every arm; blind scoring is preferred where practical.

Efficiency only counts as a measured win after quality and safety floors are preserved:

```text
quality >= baseline/control quality
safety  >= baseline/control safety
regressions <= controls
```

## Results

Synthetic/assumed dashboard:

```text
benchmarks/ASSUMED_NUMBERS.md
benchmarks/demo-numbers.svg
benchmarks/example-runs-v2.json
```

Measured datasets belong in [`benchmarks/results/`](results/). Once a complete dataset passes the publication gate, generate the measured dashboard with:

```sh
python benchmarks/render_numbers.py \
  benchmarks/results/<study>.json \
  --publish \
  --svg benchmarks/numbers.svg \
  --markdown benchmarks/NUMBERS.md
```

`benchmarks/NUMBERS.md` and `benchmarks/numbers.svg` remain reserved for measured, publication-gated competitive results.

## Current evidence state

As of 2026-08-18, Codemium publishes a synthetic assumption model but no complete measured Codemium-vs-baseline-vs-caveman-vs-Ponytail dataset.

That distinction is intentional: assumptions can communicate the expected profile now, while measured claims remain evidence-gated.
