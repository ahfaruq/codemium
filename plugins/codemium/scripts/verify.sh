#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
python - "$ROOT" <<'PYEOF'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])
for p in [root/'.agents/plugins/marketplace.json',root/'plugins/codemium/.codex-plugin/plugin.json']:
    json.loads(p.read_text())
plugin=json.loads((root/'plugins/codemium/.codex-plugin/plugin.json').read_text())
assert plugin['name']=='codemium' and plugin['version']=='0.4.0'
main=(root/'plugins/codemium/skills/codemium/SKILL.md').read_text()
for phrase in ['name: cm','@cm fast','preferred `low`','preferred `xhigh`','reasoning-policy.md','smallest **justified** change','Minimal production code **does not imply minimal tests**']:
    assert phrase in main, phrase
expected={'fix':'name: cm-fix','test':'name: cm-test','review':'name: cm-review','audit':'name: cm-audit','health':'name: cm-health','init':'name: cm-init'}
for folder,phrase in expected.items():
    assert phrase in (root/f'plugins/codemium/skills/{folder}/SKILL.md').read_text(), phrase
readme=(root/'README.md').read_text()
assert '@cm' in readme and '$codemium:' not in readme
assert 'FAST | `low`' in readme and 'CRITICAL | `xhigh`' in readme
assert '## Numbers' in readme
assert 'Ponytail-style' not in readme
for phrase in ['**baseline**','**caveman**','**ponytail**','**codemium**']:
    assert phrase in readme, phrase
demo=json.loads((root/'benchmarks/example-runs-v2.json').read_text())
systems={r['system'] for r in demo['runs']}
assert {'baseline','caveman','ponytail','codemium'} <= systems
svg=(root/'benchmarks/demo-numbers.svg').read_text()
for phrase in ['SYNTHETIC / DEMO DATA','caveman','ponytail','codemium']:
    assert phrase in svg, phrase
assert (root/'plugins/codemium/engine/reasoning_profile.py').exists()
assert (root/'plugins/codemium/skills/codemium/references/reasoning-policy.md').exists()
assert (root/'benchmarks/render_numbers.py').exists()
assert (root/'VERSION').read_text().strip()=='0.4.0'
print('PASS: manifests, @cm, competitive Numbers framing, and core doctrine')
PYEOF
find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'
python "$ROOT/plugins/codemium/tests/test_fixture.py"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --svg "$TMPDIR/demo.svg" --markdown "$TMPDIR/demo.md" >/dev/null
grep -q 'SYNTHETIC / DEMO DATA' "$TMPDIR/demo.svg"
grep -q 'caveman' "$TMPDIR/demo.svg"
grep -q 'ponytail' "$TMPDIR/demo.svg"
grep -q 'codemium' "$TMPDIR/demo.svg"
if python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --publish --svg "$TMPDIR/publish.svg" --markdown "$TMPDIR/publish.md" >/dev/null 2>&1; then
  echo 'FAIL: synthetic benchmark passed publication gate' >&2
  exit 1
fi
printf '%s\n' 'PASS: competitive renderer + synthetic publication gate'
printf '%s\n' 'ALL CHECKS PASSED'
