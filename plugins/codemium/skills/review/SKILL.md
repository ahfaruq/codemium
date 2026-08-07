---
name: cm-review
description: "Short Codemium review skill: actual-diff review across correctness, scope, architecture, security, testing, compatibility, and complexity with adaptive depth."
---

# $cm-review

Pin task type to REVIEW. Accept `fast`, `deep`, or `critical` as optional depth requests; otherwise infer depth from diff risk and blast radius.

Review the actual diff. Activate only relevant lanes: correctness, scope integrity, architecture/interfaces, security, tests, performance, dependencies, compatibility, complexity. A smaller diff is not automatically better. Flag unrelated changed lines and under-testing as first-class defects. Escalate depth for security/trust-boundary, migration, payment, production-data, infrastructure, or breaking-interface changes.
