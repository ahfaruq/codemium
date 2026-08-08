#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)

python - "$ROOT" <<'PYEOF'
import json,sys,tomllib
from pathlib import Path
root=Path(sys.argv[1])
version=(root/'VERSION').read_text().strip()
assert version=='0.6.1', version

# Codex adapter
for p in [root/'.agents/plugins/marketplace.json',root/'plugins/codemium/.codex-plugin/plugin.json']:
    json.loads(p.read_text())
codex=json.loads((root/'plugins/codemium/.codex-plugin/plugin.json').read_text())
assert codex['name']=='codemium' and codex['version']==version
assert codex['interface']['displayName']=='Codemium'
assert '@Codemium' in codex['interface']['longDescription']
assert 'automatically initialize or reuse .codemium Project Brain' in ' '.join(codex['interface']['defaultPrompt'])
main=(root/'plugins/codemium/skills/codemium/SKILL.md').read_text()
for phrase in ['name: cm','# Codemium','@Codemium','$cm fast','preferred `low`','preferred `xhigh`','Project Brain persistence contract','Persistence gate','smallest **justified** change','Minimal production code **does not imply minimal tests**']:
    assert phrase in main, phrase
focused={
    'fix':'# $cm-fix','test':'# $cm-test','review':'# $cm-review',
    'audit':'# $cm-audit','health':'# $cm-health','init':'# $cm-init'
}
for folder,heading in focused.items():
    text=(root/f'plugins/codemium/skills/{folder}/SKILL.md').read_text()
    assert heading in text, (folder,heading)

# One shared Agent Skill for Claude/Gemini/Cursor/OpenCode.
shared=(root/'skills/cm/SKILL.md').read_text()
for phrase in ['name: cm','portable Agent Skill','opencode/slash: "true"','Vendor model/thinking controls remain host-owned','Project Brain persistence is automatic']:
    assert phrase in shared, phrase

# Claude Code adapter: repository root is plugin root.
claude_market=json.loads((root/'.claude-plugin/marketplace.json').read_text())
assert claude_market['name']=='codemium'
entry=next(p for p in claude_market['plugins'] if p['name']=='codemium')
assert entry['version']==version and entry['source']=='./'
claude_plugin=json.loads((root/'.claude-plugin/plugin.json').read_text())
assert claude_plugin['name']=='codemium' and claude_plugin['version']==version
claude_command=(root/'commands/cm.md').read_text()
assert '$ARGUMENTS' in claude_command and 'name: cm' in claude_command
assert '${CLAUDE_PLUGIN_ROOT}/plugins/codemium/engine/' in claude_command
assert not (root/'adapters/claude-code/.claude-plugin/plugin.json').exists()

# Gemini CLI adapter; root shared skill is also available to Gemini extension skill discovery.
gemini=json.loads((root/'gemini-extension.json').read_text())
assert gemini['name']=='codemium' and gemini['version']==version and gemini['contextFileName']=='GEMINI.md'
assert 'host-agnostic coding-intelligence layer' in (root/'GEMINI.md').read_text()
parsed_cm=tomllib.loads((root/'commands/cm.toml').read_text())
assert '{{args}}' in parsed_cm['prompt'] and 'Run Codemium' in parsed_cm['description']

# Portable host installer / doctor.
assert (root/'scripts/install_host.py').exists()
assert (root/'scripts/doctor.py').exists()

# Public positioning / docs.
readme=(root/'README.md').read_text()
for phrase in [
    'Persistent coding intelligence for AI coding agents',
    'OpenAI Codex | **Stable**', 'Claude Code | **Beta**', 'Gemini CLI | **Beta**',
    'Cursor | **Beta**', 'OpenCode | **Beta**', '@Codemium',
    'Project Brain is zero-setup for normal use', 'INSTALL.md', 'HOSTS.md'
]:
    assert phrase in readme, phrase
assert 'Codex-first plugin' not in readme
assert '## Numbers' not in readme and 'benchmarks/demo-numbers.svg' not in readme
assert 'Ponytail-style' not in readme
hosts=(root/'HOSTS.md').read_text()
assert 'host-agnostic at the product/core level' in hosts and 'OpenCode | Beta' in hosts and '@Codemium' in hosts
prd=(root/'PRD.md').read_text()
assert 'host-agnostic persistent coding-intelligence layer' in prd
assert 'v0.6 release definition' in prd
assert '@Codemium' in prd
assert 'Automatic lifecycle' in prd and 'Durable capture policy' in prd

# Hidden benchmark infrastructure remains retained and non-publishable when synthetic.
demo=json.loads((root/'benchmarks/example-runs-v2.json').read_text())
systems={r['system'] for r in demo['runs']}
assert {'baseline','caveman','ponytail','codemium'} <= systems
svg=(root/'benchmarks/demo-numbers.svg').read_text()
assert 'SYNTHETIC / DEMO DATA' in svg

print('PASS: v0.6.1 native host layouts, plugin mention UX, Project Brain persistence, docs, and invocation contracts')
PYEOF

find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" "$ROOT/scripts" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'

python "$ROOT/scripts/doctor.py" --repo "$ROOT" >/dev/null
printf '%s\n' 'PASS: cross-host doctor'

python "$ROOT/plugins/codemium/tests/test_fixture.py"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Portable installer: Cursor and OpenCode project-local install/update/uninstall.
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" >/dev/null
test -f "$TMPDIR/.cursor/skills/cm/SKILL.md"
test -f "$TMPDIR/.cursor/skills/cm/engine/project_brain.py"
test -f "$TMPDIR/.cursor/skills/cm/.codemium-installed.json"
grep -q 'portable Agent Skill' "$TMPDIR/.cursor/skills/cm/SKILL.md"
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" >/dev/null
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" --uninstall >/dev/null
test ! -e "$TMPDIR/.cursor/skills/cm"

python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" >/dev/null
test -f "$TMPDIR/.opencode/skills/cm/SKILL.md"
grep -q 'opencode/slash: "true"' "$TMPDIR/.opencode/skills/cm/SKILL.md"
python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" >/dev/null
python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" --uninstall >/dev/null
test ! -e "$TMPDIR/.opencode/skills/cm"
printf '%s\n' 'PASS: Cursor/OpenCode portable installer lifecycle'

# Synthetic benchmark remains hidden and cannot pass publication gate.
python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --svg "$TMPDIR/demo.svg" --markdown "$TMPDIR/demo.md" >/dev/null
grep -q 'SYNTHETIC / DEMO DATA' "$TMPDIR/demo.svg"
if python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --publish --svg "$TMPDIR/publish.svg" --markdown "$TMPDIR/publish.md" >/dev/null 2>&1; then
  echo 'FAIL: synthetic benchmark passed publication gate' >&2
  exit 1
fi
printf '%s\n' 'PASS: hidden benchmark publication gate'
printf '%s\n' 'ALL CHECKS PASSED'
