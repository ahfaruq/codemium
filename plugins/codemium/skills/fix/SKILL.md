---
name: fix
description: "Codemium bug-fix mode: reproduce/trace root cause, choose smallest shared fix, add adequate regression coverage, preserve scope."
---

# Codemium Fix

Priorities: reproduce or establish evidence → trace execution/call path → root cause → smallest shared correct fix → regression tests → impact/scope verification.

Do not patch symptoms when a shared root cause is evidenced. Do not refactor adjacent code unless directly required. Search known bugs and project patterns before inventing a new mechanism. Testing depth follows the behavior and risk, not the size of the patch.
