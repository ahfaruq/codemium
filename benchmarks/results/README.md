# Measured Benchmark Results

This directory is reserved for raw, measured competitive benchmark datasets that are eligible for Codemium's public publication gate.

Do not commit synthetic/demo numbers here.

A publishable dataset must:

- set `meta.kind` to `measured`;
- use `meta.study_type` = `competitive`;
- include `baseline`, `caveman`, `ponytail`, and `codemium`;
- cover identical task IDs in every required arm;
- include `quality_pass` and `safety_pass` for every run;
- use host-observed token telemetry;
- use measured cost/billing telemetry;
- identify repository commit, agent, model/reasoning configuration, and runs per arm.

Before publishing:

```sh
python benchmarks/render_numbers.py \
  benchmarks/results/<study>.json \
  --publish \
  --svg benchmarks/numbers.svg \
  --markdown benchmarks/NUMBERS.md
```

If the command refuses publication, the dataset is not ready to support public performance claims.

See [`../PUBLIC_BENCHMARK.md`](../PUBLIC_BENCHMARK.md) for the public protocol and [`../README.md`](../README.md) for the complete benchmark rules.
