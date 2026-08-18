# Assumed Numbers

> **SYNTHETIC / ASSUMPTION MODEL — NOT MEASURED PRODUCT PERFORMANCE.**
>
> These values are scenario assumptions for communicating the intended efficiency profile of Codemium v0.7.0. They were not produced by live agent/API runs and must not be cited as measured benchmark evidence.

![Synthetic Codemium competitive benchmark chart](demo-numbers.svg)

## Scenario summary

The assumption model uses the repository's existing four-arm synthetic dataset (`example-runs-v2.json`) and keeps the same quality/safety floor for every arm.

| vs baseline | LOC | tokens | cost | time | quality | safety |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| caveman | -18% | +5% | +4% | +2% | 100% | 100% |
| ponytail | -38% | -19% | -18% | -21% | 100% | 100% |
| **codemium** | **-45%** | **-31%** | **-29%** | **-28%** | **100%** | **100%** |

## Interpretation

Under this synthetic scenario, Codemium is expected to reduce repeated repository discovery and unrelated implementation surface by reusing freshness-qualified Project Brain knowledge, selecting bounded structural Working Sets, and using impact/test intelligence before broad exploration.

The model therefore assumes the strongest relative improvement in LOC changed and context/token consumption, with smaller but related reductions in cost and wall-clock time.

These percentages are **targets/illustrations, not observations**. Real results may be better or worse.

## Why this page exists

Codemium can show a concrete expected performance profile before a paid benchmark campaign is run, while preserving a strict distinction between:

- **assumed/synthetic numbers** — this page;
- **measured numbers** — reserved for `NUMBERS.md` after a dataset passes `render_numbers.py --publish`.

## Source dataset

The scenario is generated from:

```text
benchmarks/example-runs-v2.json
benchmarks/demo-numbers.svg
```

The source dataset remains `meta.kind = synthetic`. Do not change it to `measured` unless the values are replaced by real host telemetry and the full publication gate passes.
