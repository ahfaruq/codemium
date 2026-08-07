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
assert plugin['name']=='codemium' and plugin['version']=='0.2.0'
main=(root/'plugins/codemium/skills/codemium/SKILL.md').read_text()
for phrase in ['name: cm','@cm fast','smallest **justified** change','Minimal production code **does not imply minimal tests**','references/depth-policy.md']:
    assert phrase in main, phrase
expected={
    'fix':'name: cm-fix','test':'name: cm-test','review':'name: cm-review',
    'audit':'name: cm-audit','health':'name: cm-health','init':'name: cm-init'
}
for folder,phrase in expected.items():
    assert phrase in (root/f'plugins/codemium/skills/{folder}/SKILL.md').read_text(), phrase
readme=(root/'README.md').read_text()
assert '@cm' in readme and '$codemium:' not in readme
print('PASS: manifests, short tags, depth policy, and core doctrine')
PYEOF
find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'
python "$ROOT/plugins/codemium/tests/test_fixture.py"
printf '%s\n' 'ALL CHECKS PASSED'
