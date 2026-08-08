# Installing Codemium

Codemium uses one shared engineering core with host-native installation surfaces. The portable internal skill identifier is `cm`; the public invocation follows the host's native plugin or skill UX.

## Prerequisites

- Git for repository/extension installation where the host requires it.
- Python 3.11+ for Codemium's deterministic engine, doctor, verification, portable Cursor/OpenCode installer, and the Codex Project Brain lifecycle hook.
- The target coding-agent host installed and authenticated according to that host's own setup.

## OpenAI Codex — Stable

Install Codemium from GitHub:

```sh
codex plugin marketplace add ahfaruq/codemium --ref main
codex plugin add codemium@codemium
```

Start a fresh Codex task/session after installation if the runtime has cached its plugin or skill inventory.

### Trust the Project Brain lifecycle hooks

Codemium `0.6.2` bundles `UserPromptSubmit` and `Stop` lifecycle hooks. They are the deterministic enforcement layer that initializes Project Brain for a Codemium turn and prevents the turn from finishing while its Project Brain persistence gate is still pending.

Codex intentionally does **not** auto-trust plugin command hooks. After installing or updating Codemium, open:

```text
/hooks
```

Review the hooks coming from the Codemium plugin and trust the current definitions. Codex records trust against the exact hook definition, so a later Codemium release that changes a hook can require review again.

If the hooks are still untrusted or hooks are disabled in Codex, the plugin's skills/prompts may still load, but deterministic Project Brain completion enforcement will not run. In that state Codemium must not be treated as having guaranteed persistence.

### Primary use

Mention the installed plugin naturally:

```text
@Codemium review this repository before making any changes
@Codemium fix the profile save bug
@Codemium deeply investigate why the websocket disconnects intermittently
@Codemium safely change this authentication flow and verify the impact
```

Codemium automatically classifies the task and selects the smallest safe engineering depth. Users do not need to learn internal skill names, specify `normal`, or initialize Project Brain manually before ordinary use.

On a repository-bound Codemium task, the lifecycle hook initializes or reuses `.codemium/` when workspace-state writes are allowed and opens a per-turn persistence gate. Before the turn is allowed to finish, durable source-backed project knowledge must be captured/reused or the task must explicitly classify that it learned nothing durable. A read-only **source-code** request can still update `.codemium/`; an explicit prohibition on **all** file/workspace changes disables that bookkeeping for the task.

### Verify persistence after installation or update

Use a real repository and run an investigation that is likely to produce a durable fact:

```text
@Codemium investigate this authentication flow. Do not modify source code. Persist any durable source-backed findings to Project Brain.
```

Then start a fresh Codex session and ask:

```text
@Codemium based only on Project Brain, explain the known authentication behavior. Do not rescan unless stored knowledge is stale.
```

The second turn should be able to reuse the durable registry entry created by the first turn. Codemium does not retroactively convert earlier chat history into Project Brain entries.

### Advanced direct skill invocation

Codex also supports direct Agent Skill invocation when you explicitly want the internal `cm` skill:

```text
$cm <task>
$cm fast <task>
$cm deep <task>
$cm critical <task>
```

Focused direct skills remain available for advanced use: `$cm-fix`, `$cm-test`, `$cm-review`, `$cm-audit`, `$cm-health`. `$cm-init` remains a manual maintenance/diagnostic path but is not a prerequisite for normal `@Codemium` work.

The public Codemium plugin UX is `@Codemium`; `$cm` is the direct skill/compatibility path.

Upgrade the marketplace/plugin using the Codex plugin commands available in your installed Codex release, review any changed hook definitions with `/hooks`, then start a fresh session if plugin/skill inventory is stale.

## Claude Code — Beta

Inside Claude Code:

```text
/plugin marketplace add ahfaruq/codemium
/plugin install codemium@codemium
```

The repository root is the Claude plugin root. This is intentional: it gives Claude's command access to the canonical Codemium engine under `plugins/codemium/engine/`, while `skills/cm/SKILL.md` remains the shared Agent Skill source.

Use:

```text
/codemium:cm <task>
/codemium:cm fast <task>
/codemium:cm deep <task>
/codemium:cm critical <task>
```

Claude may also auto-activate the `cm` Agent Skill when its description matches the task.

Native schema validation from a checkout:

```sh
claude plugin validate . --strict
```

## Gemini CLI — Beta

From a terminal (extension management is not performed from Gemini CLI interactive mode):

```sh
gemini extensions install https://github.com/ahfaruq/codemium --ref main
```

Restart Gemini CLI after installing or updating the extension.

Use:

```text
/cm <task>
/cm fast <task>
/cm deep <task>
/cm critical <task>
```

Validate the extension from a checkout:

```sh
gemini extensions validate .
```

To update later:

```sh
gemini extensions update codemium
```

## Cursor — Beta

Codemium uses Cursor's Agent Skills support. Current Cursor releases use `agent` as the primary CLI entrypoint; `cursor-agent` remains a compatibility alias.

### User-wide

```sh
python scripts/install_host.py --host cursor
```

Target:

```text
~/.cursor/skills/cm/
```

### Project-local

```sh
python scripts/install_host.py --host cursor --scope project --project /path/to/project
```

Target:

```text
<project>/.cursor/skills/cm/
```

Cursor can discover the `cm` skill automatically and exposes skills through the slash-command UI on supported releases; use `/cm` there.

Basic host check:

```sh
agent --version
# or on older/compatibility installs
cursor-agent --version
```

## OpenCode — Beta

Codemium uses OpenCode's native Agent Skills support.

### User-wide

```sh
python scripts/install_host.py --host opencode
```

Target:

```text
~/.config/opencode/skills/cm/
```

### Project-local

```sh
python scripts/install_host.py --host opencode --scope project --project /path/to/project
```

Target:

```text
<project>/.opencode/skills/cm/
```

The shared skill includes `opencode/slash: "true"` metadata. OpenCode advertises permitted skills on demand and loads the body only when selected, avoiding always-on context injection. Use `/cm` on releases that expose the skill slash catalog; otherwise let the agent load `cm` through the native skill tool.

## Portable Agent Skills path

For another Agent Skills-compatible host or manual experimentation:

```sh
python scripts/install_host.py --host agents
```

This installs to:

```text
~/.agents/skills/cm/
```

This generic path is not a substitute for a host-native adapter when that host has stronger installation semantics.

## Dry run

```sh
python scripts/install_host.py --host cursor --dry-run
python scripts/install_host.py --host opencode --dry-run
```

## Uninstall portable skill adapters

```sh
python scripts/install_host.py --host cursor --uninstall
python scripts/install_host.py --host opencode --uninstall
```

Project-local uninstall:

```sh
python scripts/install_host.py --host cursor --scope project --project /path/to/project --uninstall
```

The installer removes only directories containing Codemium's ownership marker. It refuses to delete/overwrite an unrecognized directory unless `--force` is explicitly supplied.

## Verify repository and host availability

Run repository doctor:

```sh
python scripts/doctor.py
```

Require a host binary for local runtime testing:

```sh
python scripts/doctor.py --require-host codex
python scripts/doctor.py --require-host claude-code
python scripts/doctor.py --require-host gemini-cli
python scripts/doctor.py --require-host cursor
python scripts/doctor.py --require-host opencode
```

The doctor recognizes Cursor's modern `agent` entrypoint and the `cursor-agent` compatibility alias.

## Project intelligence lifecycle

Normal Codemium use initializes `.codemium/` automatically on the first repository-bound task when state writes are allowed. At completion Codemium captures only durable, source-backed decisions, constraints, interfaces, patterns, and known bugs/risks that are likely to matter later; equivalent active entries are reused rather than duplicated.

For the OpenAI Codex adapter, `0.6.2` adds a host lifecycle enforcement layer around that contract. Other host adapters continue to use their native skill/command behavior unless that host provides and Codemium implements an equivalent deterministic lifecycle surface.

Manual deterministic initialization/capture is available for diagnostics or host integration:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/project_brain.py --root . capture --entries '[{"kind":"bug","text":"Durable source-backed finding","source":"src/example.py:42"}]'
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/test_map.py build --root .
```

Portable Cursor/OpenCode installs include copies of these engine helpers inside the installed `cm` skill directory.

Project Brain deliberately keeps transient repository maps, runtime state, the active task contract, completed task snapshots, and Codex persistence-gate state out of Git by default while leaving durable sanitized architecture/decision knowledge available to the project. It never treats chat transcripts, secrets, speculative hypotheses, or temporary runtime observations as durable project knowledge.

## Safety note

Codemium never treats a user-requested lower depth as permission to weaken security, migration, payment, production-data, destructive-operation, or other critical verification requirements. Safety can escalate FAST/NORMAL to DEEP/CRITICAL.
