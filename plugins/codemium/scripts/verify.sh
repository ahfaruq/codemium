#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
[ "$VERSION" = "0.9.0" ] || { echo "FAIL: expected Codemium 0.9.0, got $VERSION" >&2; exit 1; }

printf '%s\n' '== Codemium v0.9.0 full validation =='

find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/hooks" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" "$ROOT/scripts" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'

python "$ROOT/scripts/verify_core.py"
python "$ROOT/scripts/verify_polyglot.py"
python "$ROOT/scripts/verify_codex_plugin.py"
python "$ROOT/scripts/doctor.py" --repo "$ROOT" >/dev/null
python "$ROOT/benchmarks/calibrate_v09_blocking.py" >/dev/null
printf '%s\n' 'PASS: core + Polyglot + Codex lifecycle + Anti-Slop calibration + doctor'

python "$ROOT/plugins/codemium/tests/test_fixture.py"
printf '%s\n' 'PASS: host-agnostic compatibility fixture'

python - "$ROOT" <<'PYEOF'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); version=(root/'VERSION').read_text().strip()
assert version=='0.9.0'
for path in ['plugins/codemium/.codex-plugin/plugin.json','.claude-plugin/plugin.json','gemini-extension.json']:
    data=json.loads((root/path).read_text()); assert data['version']==version,(path,data.get('version'))
market=json.loads((root/'.claude-plugin/marketplace.json').read_text()); entry=next(p for p in market['plugins'] if p['name']=='codemium'); assert entry['version']==version
readme=(root/'README.md').read_text()
for phrase in ['Anti-Slop Intelligence','Slop Guard','Justified Change Gate','Underengineering Counter-Gate','finding provenance','Polyglot Intelligence','v0.9.0']:
    assert phrase in readme, phrase
prd=(root/'PRD-v0.9.md').read_text()
for phrase in ['Anti-Slop Intelligence','Justified Change Gate','minimum justified engineering surface','Underengineering Counter-Gate']:
    assert phrase in prd, phrase
policy=(root/'plugins/codemium/skills/codemium/references/slop-policy.md').read_text()
for phrase in ['introduced','worsened','pre_existing','unknown','Evidence-backed adjudication','CLEANUP']:
    assert phrase in policy, phrase
notes=(root/'RELEASE_NOTES-v0.9.0.md').read_text()
for phrase in ['Codemium v0.9.0','Anti-Slop Intelligence','Slop Guard','Underengineering Counter-Gate']:
    assert phrase in notes, phrase
changelog=(root/'CHANGELOG.md').read_text(); assert '## 0.9.0 — Anti-Slop Intelligence' in changelog
print('PASS: v0.9 metadata and documentation contracts')
PYEOF

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" >/dev/null
test -f "$TMPDIR/.cursor/skills/cm/engine/parsers.py"
test -f "$TMPDIR/.cursor/skills/cm/engine/slop_guard.py"
test -f "$TMPDIR/.cursor/skills/cm/references/slop-policy.md"
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" --uninstall >/dev/null
test ! -e "$TMPDIR/.cursor/skills/cm"
python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" >/dev/null
test -f "$TMPDIR/.opencode/skills/cm/engine/parsers.py"
test -f "$TMPDIR/.opencode/skills/cm/engine/slop_guard.py"
python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" --uninstall >/dev/null
test ! -e "$TMPDIR/.opencode/skills/cm"
printf '%s\n' 'PASS: Cursor/OpenCode portable installer lifecycle + Slop Guard payload'

python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --svg "$TMPDIR/demo.svg" --markdown "$TMPDIR/demo.md" >/dev/null
grep -q 'SYNTHETIC / DEMO DATA' "$TMPDIR/demo.svg"
if python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --publish --svg "$TMPDIR/publish.svg" --markdown "$TMPDIR/publish.md" >/dev/null 2>&1; then
  echo 'FAIL: synthetic benchmark passed publication gate' >&2
  exit 1
fi
printf '%s\n' 'PASS: benchmark publication gate'
printf '%s\n' 'ALL CHECKS PASSED'
