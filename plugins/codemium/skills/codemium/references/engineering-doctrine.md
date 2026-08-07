# Engineering Doctrine

Codemium optimizes **engineering surface**, not lines alone.

Before adding custom machinery, evaluate in order:

1. Is the behavior actually required by the current task?
2. Does the repository already implement the same pattern?
3. Does the language standard library solve it adequately?
4. Does the framework/platform expose a native capability?
5. Does an already-installed dependency cover it?
6. Can a narrow local implementation solve the current case cleanly?
7. Only then create a new abstraction or dependency.

An abstraction is justified by current complexity or multiple actual consumers, not hypothetical reuse. A dependency must pay for its permanent security, licensing, update, bundle/runtime, and operational surface.

Prefer a slightly longer obvious solution over a shorter solution that hides behavior, violates architecture, weakens safety, or creates future ambiguity.
