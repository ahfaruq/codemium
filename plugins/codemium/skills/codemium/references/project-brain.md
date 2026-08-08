# Project Brain

Store durable engineering knowledge, not a transcript.

Project Brain is a default Codemium capability. For normal repository-bound work, initialize `.codemium/` automatically when it is missing and state writes are allowed. Users should not need a separate init command before ordinary `@Codemium` use.

Useful durable categories:

- decisions — settled choices and rationale;
- constraints — active boundaries future work must preserve;
- interfaces — API/schema/event/public contracts and important cross-component flows;
- patterns — established repository conventions with real examples;
- bugs — important historical symptoms, root causes, risks, and fixes.

## Capture gate

Before a task completes, inspect the source-backed facts learned during the task and decide which are likely to matter to a future engineering task. Persist those facts when state writes are allowed, even if the current task was a read-only investigation and no source code changed.

A durable fact should generally be:

- supported by repository/runtime evidence rather than speculation;
- stable enough to remain useful after the current conversation ends;
- relevant to future implementation, debugging, review, migration, or testing;
- concise enough to retrieve without replaying the investigation.

Do not persist:

- secrets, credentials, tokens, personal data, or sensitive raw payloads;
- raw logs or temporary production snapshots;
- unverified hypotheses or brainstorming;
- tool commands, search history, or conversation transcripts;
- generic facts that can be rediscovered trivially and do not affect future engineering decisions.

If an equivalent ACTIVE entry already exists, reuse it instead of creating a duplicate. If the new evidence supersedes an older decision, preserve history and mark/supersede deliberately rather than silently deleting it.

## Read-only semantics

“Do not modify code” means source/product code stays untouched; it does not by itself disable `.codemium/` bookkeeping. If the user explicitly prohibits all file/workspace/state changes, do not initialize or capture Project Brain and report that persistence was skipped. An explicit request to initialize or retain project intelligence overrides a simultaneous source-code-only freeze.

## Deterministic capture

When the helper is available, batch new facts with:

```sh
python engine/project_brain.py --root . capture --entries '[{"kind":"bug","text":"...","source":"path:line"}]'
```

or the equivalent canonical plugin-engine path. Normal Project Brain helper operations auto-initialize state silently when needed.

At completion, report persistence honestly as one of: **captured**, **reused**, **none**, or **skipped by user constraint**.
