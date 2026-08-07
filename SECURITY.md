# Security

Codemium project state can contain architecture and repository metadata. Do not store credentials, tokens, private keys, customer payloads, or unredacted production logs in `.codemium` registries.

Runtime files are ignored by default. Durable registry entries should contain sanitized engineering facts only.

For security-sensitive coding work, token or context efficiency is subordinate to trust-boundary validation, authentication/authorization correctness, secret handling, data integrity, migration safety, and adequate verification.

Report security issues privately to the repository owner rather than opening a public issue containing exploit details or secrets.
