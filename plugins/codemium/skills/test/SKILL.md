---
name: cm-test
description: "Short Codemium testing skill: sufficient behavioral, edge-case, and failure-mode coverage with adaptive depth and no production-code minimalism applied to justified tests."
---

# $cm-test

Pin task type to TEST. Accept `fast`, `deep`, or `critical` as optional depth requests; otherwise auto-select depth from behavior and risk.

Tests are evidence, not code-volume waste. Identify behavioral surface, boundaries, likely regressions, failure modes, and risk. Reuse project test patterns/helpers, but add as many distinct cases as justified. Avoid duplicate cases that prove the same condition with no added confidence. A lower requested depth cannot bypass security, migration, payment, data-integrity, or other safety requirements.
