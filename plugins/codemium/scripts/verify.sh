#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)

python - "$ROOT" <<'PYEOF'
import json,sys,tomllib
from pathlib import Path
root=Path(sys.argv[1])
version=(root/'VERSION').read_text().strip()
assert version=='0.7.0', version

# Codex adapter
for p in [root/'.agents/plugins/marketplace.json',root/'plugins/codemium/.codex-plugin/plugin.json']:
    json.loads(p.read_text())
codex=json.loads((root/'plugins/codemium/.codex-plugin/plugin.json').read_text())
assert codex['name']=='codemium' and codex['version']==version
assert codex['interface']['displayName']=='Codemium'
assert '@Codemium' in codex['interface']['longDescription']
assert codex['hooks']=='./hooks/hooks.json'
default_prompt=' '.join(codex['interface']['defaultPrompt'])
for phrase in [
    'automatically initialize or reuse .codemium Project Brain',
    'canonical project root shared across the Local checkout and linked worktrees',
    'Consolidate durable legacy Project Brain knowledge discovered in any linked worktree',
    'bundled UserPromptSubmit and Stop lifecycle hooks',
    'CODEMIUM MEMORY RETRIEVAL MODE',
    'freshness-qualified',
    'derived/regenerable structural index',
    'DIRECT, RESOLVED, and HEURISTIC provenance',
]:
    assert phrase in default_prompt, phrase
hooks=json.loads((root/'plugins/codemium/hooks/hooks.json').read_text())
assert hooks['hooks']['UserPromptSubmit'] and hooks['hooks']['Stop']
for event in ['UserPromptSubmit','Stop']:
    handler=hooks['hooks'][event][0]['hooks'][0]
    assert handler['type']=='command'
    assert 'commandWindows' in handler
    assert 'project_brain_dispatch.py' in (handler['command'] + handler['commandWindows'])
gate=(root/'plugins/codemium/hooks/project_brain_gate.py').read_text()
for phrase in ['canonical_project_root','git-common-dir','migrate_legacy_project_brain','migrate_legacy_project_brains','worktree list','migrated_source_stamps','project-location.json']:
    assert phrase in gate, phrase
dispatch=(root/'plugins/codemium/hooks/project_brain_dispatch.py').read_text()
for phrase in ['CODEMIUM MEMORY RETRIEVAL MODE','rank_entries','Use minimum reasoning','host_turn_to_stop_ms','memory_mode','prepare_project_root']:
    assert phrase in dispatch, phrase
main=(root/'plugins/codemium/skills/codemium/SKILL.md').read_text()
for phrase in [
    'name: cm','# Codemium','@Codemium','$cm fast','preferred `low`','preferred `xhigh`',
    'Lightweight Project Brain memory mode','Project Brain persistence contract','Persistence gate',
    'Evidence freshness','Structural Intelligence contract','NEEDS_REVALIDATION','DIRECT','RESOLVED','HEURISTIC',
    'smallest **justified** change','Minimal production code **does not imply minimal tests**'
]:
    assert phrase in main, phrase
focused={'fix':'# $cm-fix','test':'# $cm-test','review':'# $cm-review','audit':'# $cm-audit','health':'# $cm-health','init':'# $cm-init'}
for folder,heading in focused.items():
    text=(root/f'plugins/codemium/skills/{folder}/SKILL.md').read_text()
    assert heading in text, (folder,heading)

# Shared Agent Skill for Claude/Gemini/Cursor/OpenCode.
shared=(root/'skills/cm/SKILL.md').read_text()
for phrase in ['name: cm','portable Agent Skill','opencode/slash: "true"','Vendor model/thinking controls remain host-owned','Project Brain persistence is automatic','Evidence freshness','Structural Intelligence','NEEDS_REVALIDATION']:
    assert phrase in shared, phrase

# Claude Code adapter.
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

# Gemini CLI adapter.
gemini=json.loads((root/'gemini-extension.json').read_text())
assert gemini['name']=='codemium' and gemini['version']==version and gemini['contextFileName']=='GEMINI.md'
assert 'host-agnostic coding-intelligence layer' in (root/'GEMINI.md').read_text()
parsed_cm=tomllib.loads((root/'commands/cm.toml').read_text())
assert '{{args}}' in parsed_cm['prompt'] and 'Run Codemium' in parsed_cm['description']

# Shared core v0.7.
engine=root/'plugins/codemium/engine'
for name in ['project_brain.py','repo_graph.py','graph_query.py','working_set.py','impact.py','scope_guard.py','test_map.py','health.py','task_compiler.py']:
    assert (engine/name).exists(), name
repo_graph=(engine/'repo_graph.py').read_text()
for phrase in ['GRAPH_SCHEMA_VERSION = 2','python-ast','fallback-regex','DIRECT','RESOLVED','HEURISTIC','manifest.json','DEPENDS_ON','TESTS']:
    assert phrase in repo_graph, phrase
project_brain=(engine/'project_brain.py').read_text()
for phrase in ['FRESH','NEEDS_REVALIDATION','SUPERSEDED','UNKNOWN','def entry_freshness(','def revalidate(','evidence']:
    assert phrase in project_brain, phrase
graph_query=(engine/'graph_query.py').read_text()
for phrase in ['find-symbol','callers','callees','dependents','dependencies','tests-for','def shortest_path(','def bounded_expand(']:
    assert phrase in graph_query, phrase
assert 'graph_assisted' in (engine/'working_set.py').read_text()
assert 'impact_mode' in (engine/'impact.py').read_text()
assert 'provenance_counts' in (engine/'test_map.py').read_text()
assert 'fresh_to_worktree' in (engine/'health.py').read_text()
assert 'apply_structural_escalation' in (engine/'task_compiler.py').read_text()

# Public positioning / docs.
readme=(root/'README.md').read_text()
for phrase in [
    'Persistent coding intelligence for AI coding agents',
    'OpenAI Codex | **Stable**', 'Claude Code | **Beta**', 'Gemini CLI | **Beta**',
    'Cursor | **Beta**', 'OpenCode | **Beta**', '@Codemium',
    'Project Brain is zero-setup for normal use', 'Structural Intelligence — v0.7',
    'Evidence Bridge', 'NEEDS_REVALIDATION', 'Source remains authoritative', 'INSTALL.md', 'HOSTS.md'
]:
    assert phrase in readme, phrase
for forbidden in ['Codex-first plugin','## Numbers','benchmarks/demo-numbers.svg','Ponytail-style']:
    assert forbidden not in readme, forbidden
hosts=(root/'HOSTS.md').read_text()
for phrase in ['host-agnostic at the product/core level','OpenCode | Beta','@Codemium','Structural Intelligence contract','Project Brain evidence/freshness contract']:
    assert phrase in hosts, phrase
prd=(root/'PRD.md').read_text()
assert 'host-agnostic persistent coding-intelligence layer' in prd
assert 'v0.6 release definition' in prd
assert '@Codemium' in prd
assert 'Automatic lifecycle' in prd and 'Durable capture policy' in prd
assert 'PRD-v0.7.md' in prd
prd07=(root/'PRD-v0.7.md').read_text()
for phrase in ['Structural Intelligence & Evidence Bridge','Repository Structural Graph v2','Project Brain Freshness','FR-035']:
    assert phrase in prd07, phrase
install=(root/'INSTALL.md').read_text()
for phrase in ['/hooks','Structural Intelligence lifecycle','Evidence freshness lifecycle','0.7']:
    assert phrase in install, phrase
changelog=(root/'CHANGELOG.md').read_text()
assert '## 0.7.0 — Structural Intelligence & Evidence Bridge' in changelog

# Hidden benchmark infrastructure remains retained and non-publishable when synthetic.
demo=json.loads((root/'benchmarks/example-runs-v2.json').read_text())
systems={r['system'] for r in demo['runs']}
assert {'baseline','caveman','ponytail','codemium'} <= systems
svg=(root/'benchmarks/demo-numbers.svg').read_text()
assert 'SYNTHETIC / DEMO DATA' in svg

print('PASS: v0.7.0 native host layouts, Structural Intelligence, Evidence Bridge, canonical Project Brain, Codex persistence, docs, and invocation contracts')
PYEOF

find "$ROOT/plugins/codemium/engine" "$ROOT/plugins/codemium/hooks" "$ROOT/plugins/codemium/tests" "$ROOT/benchmarks" "$ROOT/scripts" -name '*.py' -print0 | xargs -0 python -m py_compile
printf '%s\n' 'PASS: Python syntax'

python "$ROOT/scripts/verify_core.py"
python "$ROOT/scripts/verify_codex_plugin.py"
printf '%s\n' 'PASS: core + Codex lifecycle verification'

python "$ROOT/scripts/doctor.py" --repo "$ROOT" >/dev/null
printf '%s\n' 'PASS: cross-host doctor'

python "$ROOT/plugins/codemium/tests/test_fixture.py"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" >/dev/null
test -f "$TMPDIR/.cursor/skills/cm/SKILL.md"
test -f "$TMPDIR/.cursor/skills/cm/engine/project_brain.py"
test -f "$TMPDIR/.cursor/skills/cm/engine/graph_query.py"
test -f "$TMPDIR/.cursor/skills/cm/.codemium-installed.json"
grep -q 'portable Agent Skill' "$TMPDIR/.cursor/skills/cm/SKILL.md"
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" >/dev/null
python "$ROOT/scripts/install_host.py" --host cursor --scope project --project "$TMPDIR" --uninstall >/dev/null
test ! -e "$TMPDIR/.cursor/skills/cm"

python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" >/dev/null
test -f "$TMPDIR/.opencode/skills/cm/SKILL.md"
test -f "$TMPDIR/.opencode/skills/cm/engine/graph_query.py"
grep -q 'opencode/slash: "true"' "$TMPDIR/.opencode/skills/cm/SKILL.md"
python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" >/dev/null
python "$ROOT/scripts/install_host.py" --host opencode --scope project --project "$TMPDIR" --uninstall >/dev/null
test ! -e "$TMPDIR/.opencode/skills/cm"
printf '%s\n' 'PASS: Cursor/OpenCode portable installer lifecycle'

python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --svg "$TMPDIR/demo.svg" --markdown "$TMPDIR/demo.md" >/dev/null
grep -q 'SYNTHETIC / DEMO DATA' "$TMPDIR/demo.svg"
if python "$ROOT/benchmarks/render_numbers.py" "$ROOT/benchmarks/example-runs-v2.json" --publish --svg "$TMPDIR/publish.svg" --markdown "$TMPDIR/publish.md" >/dev/null 2>&1; then
  echo 'FAIL: synthetic benchmark passed publication gate' >&2
  exit 1
fi
printf '%s\n' 'PASS: hidden benchmark publication gate'
printf '%s\n' 'ALL CHECKS PASSED'
