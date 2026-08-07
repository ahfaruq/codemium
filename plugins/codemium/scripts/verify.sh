#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
python - "$ROOT" <<'PYEOF'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])
version=(root/'VERSION').read_text().strip()
assert version=='0.5.0', version

# Codex adapter
for p in [root/'.agents/plugins/marketplace.json',root/'plugins/codemium/.codex-plugin/plugin.json']:
    json.loads(p.read_text())
codex=json.loads((root/'plugins/codemium/.codex-plugin/plugin.json').read_text())
assert codex['name']=='codemium' and codex['version']==version
main=(root/'plugins/codemium/skills/codemium/SKILL.md').read_text()
for phrase in ['name: cm','@cm fast','preferred `low`','preferred `xhigh`','smallest **justified** change','Minimal production code **does not imply minimal tests**']:
    assert phrase in main, phrase

# Claude Code adapter
claude_market=json.loads((root/'.claude-plugin/marketplace.json').read_text())
assert claude_market['name']=='codemium'
claude_plugin=json.loads((root/'adapters/claude-code/.claude-plugin/plugin.json').read_text())
assert claude_plugin['name']=='codemium' and claude_plugin['version']==version
claude_skill=(root/'adapters/claude-code/skills/cm/SKILL.md').read_text()
assert 'name: cm' in claude_skill and 'smallest justified engineering change' in claude_skill
claude_command=(root/'adapters/claude-code/commands/cm.md').read_text()
assert '$ARGUMENTS' in claude_command and 'name: cm' in claude_command

# Gemini CLI adapter
gemini=json.loads((root/'gemini-extension.json').read_text())
assert gemini['name']=='codemium' and gemini['version']==version and gemini['contextFileName']=='GEMINI.md'
assert 'host-agnostic coding-intelligence layer' in (root/'GEMINI.md').read_text()
cm_toml=(root/'commands/cm.toml').read_text()
assert '{{args}}' in cm_toml and 'Run Codemium' in cm_toml

# Public positioning
readme=(root/'README.md').read_text()
for phrase in ['Persistent coding intelligence for AI coding agents','OpenAI Codex | **Stable**','Claude Code | **Beta**','Gemini CLI | **Beta**','HOSTS.md']:
    assert phrase in readme, phrase
assert 'Codex-first plugin' not in readme
assert '## Numbers' not in readme and 'benchmarks/demo-numbers.svg' not in readme
assert 'Ponytail-style' not in readme
hosts=(root/'HOSTS.md').read_text()
assert 'host-agnostic at the product/core level' in hosts

# Hidden benchmark infrastructure remains retained and non-publishable when synthetic.
demo=json.loads((root/'benchmarks/example-runs-v2.json').read_text())
systems={r['system'] for r in demo['runs']}
assert {'baseline','caveman','ponytail','codemium'} <= systems
svg=(root/'benchmarks/demo-numbers.svg').read_text()
assert 'SYNTHETIC / DEMO DATA' in svg

assert (root/'plugins/codemium/engine/reasoning_profile.py').exists()
assert (root/'benchmarks/render_numbers.py').exists()
print('PASS: Codex stable + Claude/Gemini beta adapters + host-agnostic positioning')
PYEOF
find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'
python "$ROOT/plugins/codemium/tests/test_fixture.py"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --svg "$TMPDIR/demo.svg" --markdown "$TMPDIR/demo.md" >/dev/null
grep -q 'SYNTHETIC / DEMO DATA' "$TMPDIR/demo.svg"
if python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --publish --svg "$TMPDIR/publish.svg" --markdown "$TMPDIR/publish.md" >/dev/null 2>&1; then
  echo 'FAIL: synthetic benchmark passed publication gate' >&2
  exit 1
fi
printf '%s\n' 'PASS: hidden benchmark publication gate'
printf '%s\n' 'ALL CHECKS PASSED'
