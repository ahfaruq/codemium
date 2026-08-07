# Testing Policy

Choose verification from behavior surface and blast radius, not production diff size.

- V0: reasoning-only for truly non-behavioral/trivial changes.
- V1: syntax, formatting gate, lint, type checks.
- V2: targeted unit/component tests.
- V3: affected subsystem/integration tests.
- V4: full build/test/release boundary.
- V5: runtime/E2E/browser/environment verification.

Escalate for shared core code, auth/security, concurrency, payments, migrations, public interfaces, infrastructure, destructive behavior, or material uncertainty.

Test mapping is a candidate generator, not proof of completeness. The model must still reason about missing edge/failure cases. Cache a passing check only for the exact relevant source/dependency state it proves.
