# Codemium v0.8 Benchmark Suite

Codemium v0.8 separates benchmark evidence into three tracks so repository intelligence is not represented by a single competitive-efficiency chart.

## 1. Competitive efficiency

The existing four-arm comparison tracks relative resource use against a baseline across changed LOC, tokens, cost, and time while holding the scenario quality/safety floor constant.

| Arm | LOC vs baseline | Tokens vs baseline | Cost vs baseline | Time vs baseline | Quality | Safety |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Caveman | -18% | +5% | +4% | +2% | 100% | 100% |
| Ponytail | -38% | -19% | -18% | -21% | 100% | 100% |
| **Codemium v0.8** | **-45%** | **-31%** | **-29%** | **-28%** | **100%** | **100%** |

Visual: [`../assets/benchmark-v08-competitive.svg`](../assets/benchmark-v08-competitive.svg)

## 2. Polyglot structural coverage

This track compares deterministic parser capability between v0.7 and v0.8 across the five core source extensions represented by the v0.8 integration suite.

| Source extension | v0.7 | v0.8 |
| --- | --- | --- |
| `.py` | Python AST | Python AST |
| `.js` | deterministic fallback | Tree-sitter JavaScript |
| `.jsx` | deterministic fallback | Tree-sitter JavaScript |
| `.ts` | deterministic fallback | Tree-sitter TypeScript |
| `.tsx` | deterministic fallback | Tree-sitter TSX |

Summary:

- deep-parsed core extensions: **1/5 → 5/5** when the optional v0.8 Polyglot runtime is installed;
- graph schema: **v2 → v3**;
- v0.8 adds `IMPORTS_SYMBOL` relationships and explicit cross-language edge evidence;
- JS/TS/TSX still degrade to deterministic fallback if the optional Tree-sitter runtime is unavailable.

Visual: [`../assets/benchmark-v08-polyglot.svg`](../assets/benchmark-v08-polyglot.svg)

## 3. Impact & Test Intelligence

This track is backed by `plugins/codemium/tests/test_polyglot_fixture.py` and the `scripts/verify_polyglot.py` CI gate.

The deterministic fixture creates five source/test files:

```text
src/math.ts
src/service.ts
src/view.tsx
src/legacy.js
tests/service.test.ts
```

With the Polyglot runtime installed, the fixture verifies:

- **5/5** fixture files use Tree-sitter parsers and **0** use fallback;
- `legacy.js` resolves the imported TypeScript `add` symbol through `IMPORTS_SYMBOL`;
- the JavaScript caller of `add` is represented as an explicit JS → TS cross-language `CALLS` edge;
- `service.ts` and `legacy.js` are both returned as callers of the changed `add` symbol;
- `service.test.ts` is structurally mapped as a related test with **high confidence**;
- changing `add` produces `symbol-structural` impact mode;
- impact identifies `service.ts`, `legacy.js`, the cross-language dependent, the related test, and a prioritized **P0/P1** test plan.

The three structural paths highlighted in the README visual are:

1. `legacy.js → math.ts` — JavaScript to TypeScript imported-symbol/call resolution;
2. `view.tsx → service.ts` — TSX dependency traversal;
3. `service.test.ts → service.ts` — structural test relationship.

Visual: [`../assets/benchmark-v08-impact-test.svg`](../assets/benchmark-v08-impact-test.svg)

## CI verification

The v0.8 Core workflow runs both modes:

```text
dependency-light core + fallback behavior
        ↓
install requirements-polyglot.txt
        ↓
Tree-sitter JS/TS/TSX integration fixture
```

The Polyglot gate fails if parser abstraction, Tree-sitter runtime loading, Structural Graph v3, cross-language symbol resolution, symbol-aware impact, or prioritized Test Intelligence regress.
