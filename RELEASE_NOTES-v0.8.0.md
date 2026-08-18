# Codemium v0.8.0 — Polyglot Intelligence

Codemium v0.8.0 extends the deterministic engineering layer from Python-deep Structural Intelligence into a polyglot repository graph.

## Highlights

- Parser abstraction with explicit capability/degradation reporting.
- Tree-sitter deep parsing for JavaScript/JSX, TypeScript, and TSX.
- Structural Graph v3 with `IMPORTS_SYMBOL` and explicit cross-language relationships.
- Relative repository imports can resolve across JS/TS/TSX source boundaries.
- Symbol-aware Git diff impact starts from changed symbols when source ranges are available.
- Weighted impact evidence exposes confidence, provenance, distance, and cross-language blast radius.
- Test Intelligence v3 classifies unit/integration/e2e tests and emits P0/P1/P2 priorities.
- Project Brain persistence, evidence freshness, source authority, Scope Guard, Working Sets, and deterministic fallback behavior are preserved.

## Optional Polyglot runtime

```sh
python -m pip install -r requirements-polyglot.txt
```

Without the optional runtime, Codemium remains functional and degrades JS/TS/TSX extraction to deterministic fallback parsing.

## Verification

The release gate tests both modes:

1. dependency-light core/fallback mode;
2. installed Tree-sitter JS/TS/TSX mode with cross-language fixtures.

See `PRD-v0.8.md` for the normative release requirements.
