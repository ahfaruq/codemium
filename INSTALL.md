# Installing Codemium

Codemium uses one shared engineering core with host-native installation surfaces. The short identifier is `cm`; the invocation marker follows the host.

## OpenAI Codex — Stable

```sh
codex plugin marketplace add admahmad/codemium --ref main
codex plugin add codemium@codemium
```

Start a fresh task/session after installation if the current runtime has cached skill inventory.

Use:

```text
$cm <task>
$cm fast <task>
$cm deep <task>
$cm critical <task>
```

Focused skills: `$cm-fix`, `$cm-test`, `$cm-review`, `$cm-audit`, `$cm-health`, `$cm-init`.

Upgrade the marketplace/plugin using the Codex plugin commands available in your installed Codex release, then start a fresh session if skill inventory is stale.

## Claude Code — Beta

Inside Claude Code:

```text
/plugin marketplace add admahmad/codemium
/plugin install codemium@codemium
```

The repository root is the Claude plugin root. This is intentional: it gives Claude's skill access to the canonical Codemium engine under `plugins/codemium/engine/`.

Use:

```text
/codemium:cm <task>
/codemium:cm fast <task>
/codemium:cm deep <task>
/codemium:cm critical <task>
```

Claude may also auto-activate the `cm` Agent Skill when its description matches the task.

## Gemini CLI — Beta

From a terminal (extension management is not performed from Gemini CLI interactive mode):

```sh
gemini extensions install https://github.com/admahmad/codemium --ref main
```

Restart Gemini CLI after installing or updating the extension.

Use:

```text
/cm <task>
/cm fast <task>
/cm deep <task>
/cm critical <task>
```

To update later, use the `gemini extensions update` command supported by your installed Gemini CLI release.

## Cursor — Beta

Codemium uses Cursor's Agent Skills support.

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

Cursor can discover the `cm` skill automatically. Current Cursor releases expose Agent Skills in the slash menu; use `/cm` where that UI is available.

## OpenCode — Beta

Codemium uses OpenCode's Agent Skills support.

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

The skill includes `opencode/slash: "true"` metadata. OpenCode can always advertise/load the skill through its native skill tool when permissions allow it; `/cm` is used on releases that expose skill slash invocation.

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

## Verify installation source

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

## Initialize project intelligence

Normal Codemium use may initialize `.codemium/` when durable state is useful. Manual deterministic initialization:

```sh
python plugins/codemium/engine/project_brain.py --root . init
python plugins/codemium/engine/repo_graph.py build --root .
python plugins/codemium/engine/test_map.py build --root .
```

Portable Cursor/OpenCode installs include copies of these engine helpers inside the installed `cm` skill directory.

## Safety note

Codemium never treats a user-requested lower depth as permission to weaken security, migration, payment, production-data, destructive-operation, or other critical verification requirements. Safety can escalate FAST/NORMAL to DEEP/CRITICAL.
