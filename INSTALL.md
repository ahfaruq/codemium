# Installing Codemium

Codemium uses one shared engineering core with host-native installation surfaces. The portable internal skill identifier is `cm`; the public invocation follows the host's native plugin or skill UX.

## Prerequisites

- Git for repository/extension installation where the host requires it.
- Python 3.11+ for Codemium's deterministic engine, doctor, verification, and portable Cursor/OpenCode installer. The Agent Skill doctrine can still operate through normal host tools when a helper is unavailable, but the full deterministic optimization layer requires Python.
- The target coding-agent host installed and authenticated according to that host's own setup.

## OpenAI Codex — Stable

Install Codemium from GitHub:

```sh
codex plugin marketplace add ahfaruq/codemium --ref main
codex plugin add codemium@codemium
```

Start a fresh Codex task/session after installation if the runtime has cached its plugin or skill inventory.

### Primary use

Mention the installed plugin naturally:

```text
@Codemium review this repository before making any changes
@Codemium fix the profile save bug
@Codemium deeply investigate why the websocket disconnects intermittently
@Codemium safely change this authentication flow and verify the impact
```

Codemium automatically classifies the task and selects the smallest safe engineering depth. Users do not need to learn internal skill names or specify `normal`.

### Advanced direct skill invocation

Codex also supports direct Agent Skill invocation when you explicitly want the internal `cm` skill:

```text
$cm <task>
$cm fast <task>
$cm deep <task>
$cm critical <task>
```

Focused direct skills remain available for advanced use: `$cm-fix`, `$cm-test`, `$cm-review`, `$cm-audit`, `$cm-health`, `$cm-init`.

The public Codemium plugin UX is `@Codemium`; `$cm` is the direct skill/compatibility path.

Upgrade the marketplace/plugin using the Codex plugin commands available in your installed Codex release, then start a fresh session if plugin/skill inventory is stale.

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

## Initialize project intelligence

Normal Codemium use may initialize `.codemium/` when durable state is useful. Manual deterministic initialization:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/test_map.py build --root .
```

Portable Cursor/OpenCode installs include copies of these engine helpers inside the installed `cm` skill directory.

Project Brain deliberately keeps transient repository maps, runtime state, the active task contract, and completed task snapshots out of Git by default while leaving durable sanitized architecture/decision knowledge available to the project.

## Safety note

Codemium never treats a user-requested lower depth as permission to weaken security, migration, payment, production-data, destructive-operation, or other critical verification requirements. Safety can escalate FAST/NORMAL to DEEP/CRITICAL.
