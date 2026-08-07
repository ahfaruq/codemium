# Scope Policy

Every changed surface must map to one category:

- DIRECT — implements requested behavior.
- DEPENDENCY — required because a direct change cannot work safely without it.
- CLEANUP — only code made obsolete by this exact change.
- TEST — evidence for the changed behavior.

Disallowed by default: unrelated formatting, modernization, naming changes, comment rewriting, adjacent refactors, pre-existing dead-code removal, dependency upgrades, broad style cleanup.

If adjacent problems are discovered, report them separately. A short diff is not scoped merely because it is short.
