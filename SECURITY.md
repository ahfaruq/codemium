# Security

Codemium project state can contain architecture and repository metadata. Do not store credentials, tokens, private keys, customer payloads, or unredacted production logs in `.codemium` registries.

Runtime repository maps, completed task snapshots, and the current `tasks/active.json` are transient local state and are ignored by the Project Brain `.gitignore` policy. Codemium initialization migrates these ignore rules without deleting existing user-owned `.codemium/.gitignore` entries.

Durable registry entries should contain sanitized engineering facts only. Project Brain is not a conversation transcript and must not be used as a secret store.

For security-sensitive coding work, token or context efficiency is subordinate to trust-boundary validation, authentication/authorization correctness, secret handling, data integrity, migration safety, and adequate verification.

Portable installers manage only directories marked as Codemium-owned. They refuse to overwrite or remove an unrecognized skill directory unless the user explicitly supplies `--force` after reviewing the target.

For host model/reasoning controls, Codemium must never silently weaken the host's security posture or claim a setting changed unless the host confirms the effective value.

Report security issues privately to the repository owner rather than opening a public issue containing exploit details or secrets.
