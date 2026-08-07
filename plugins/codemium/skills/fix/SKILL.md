---
name: cm-fix
description: "Short Codemium bug-fix tag: root-cause-first fixing with bounded project context, sufficient regression evidence, scope control, and adaptive depth."
---

# @cm-fix

Pin task type to FIX. If the first modifier is `fast`, `deep`, or `critical`, treat it as the requested depth; otherwise auto-select depth using the same policy as `@cm`.

Priorities: reproduce or establish evidence → trace execution/call path → root cause → smallest shared correct fix → regression tests → impact/scope verification.

Do not patch symptoms when a shared root cause is evidenced. Do not refactor adjacent code unless directly required. Search known bugs and project patterns before inventing a new mechanism. Testing depth follows behavior/risk, not patch size. A requested lower depth cannot override a higher safety floor.
