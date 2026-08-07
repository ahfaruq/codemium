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
assert plugin['name']=='codemium' and plugin['version']=='0.1.0'
skill=(root/'plugins/codemium/skills/codemium/SKILL.md').read_text()
for phrase in ['smallest **justified** change','Minimal production code **does not imply minimal tests**','Scope correction','Stop once']:
    assert phrase in skill, phrase
print('PASS: manifests and core doctrine')
PYEOF
find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'
python "$ROOT/plugins/codemium/tests/test_fixture.py"
printf '%s\n' 'ALL CHECKS PASSED'
