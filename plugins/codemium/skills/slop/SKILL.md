---
name: cm-slop
description: "Codemium v0.9 Anti-Slop review: inspect the actual task diff for unjustified engineering, preserve necessary complexity, and re-verify any cleanup."
---

# $cm-slop

Review the actual diff using Codemium's **Justified Change Gate**. The target is the **minimum justified engineering surface**, not minimum LOC.

## Default behavior

Use review/Guard Mode first. When `engine/slop_guard.py` is available, run it against the repository root and inspect its evidence:

```sh
python engine/slop_guard.py --root . --json --write-state
```

Repository-root plugin installs may instead expose the helper under `plugins/codemium/engine/slop_guard.py`.

Resolve findings with this authority order:

```text
deterministic diff/source evidence
→ Structural Graph v3 evidence
→ evidence-backed reasoning
```

Do not accept or remove code merely because the aggregate risk score is high or low. The score is informational and may be unavailable when coverage is insufficient.

## Changed-surface discipline

Classify every changed surface as `DIRECT`, `DEPENDENCY`, `CLEANUP`, or `TEST`. `UNJUSTIFIED` is temporary: either establish concrete task/architecture/safety evidence for it or remove it.

Focus on engineering introduced or worsened by the current task. Do not turn a bounded task into a repository-wide cleanup campaign because unrelated historical slop exists nearby.

## Cleanup

Only perform cleanup when the user requested cleanup or when a normal Codemium implementation task has a high-confidence introduced finding whose removal is low-risk and clearly preserves requested behavior.

Safe mechanical cleanup can include obvious debugger residue or redundant narration. Do not blindly remove abstractions, fallbacks, dependencies, compatibility code, public APIs, tests, validation, authentication/authorization, transactions, locking, idempotency, retry behavior, or data-integrity checks.

After any cleanup, re-run the relevant verification and inspect the actual diff again. High-impact simplification requires a logically separate review pass.

## Underengineering counter-gate

Before approving simplification, explicitly check whether it removed necessary failure handling, security boundaries, data integrity, concurrency controls, compatibility, public contracts, observability, or test confidence. When evidence is insufficient, preserve the safer implementation.

Read `references/slop-policy.md` when a Slop Guard decision is ambiguous or materially affects implementation.

## Completion

Report:

- diff scope used;
- pass/review/fail result;
- introduced/worsened findings that matter;
- any protected complexity intentionally retained;
- cleanup performed, if any;
- verification repeated after cleanup;
- residual uncertainty.
