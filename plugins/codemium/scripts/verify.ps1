$ErrorActionPreference = "Stop"
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if ($Version -ne "0.7.0") { throw "Expected Codemium 0.7.0" }

function Assert-Contains([string]$Text, [string]$Needle, [string]$Message) {
  if (-not $Text.Contains($Needle)) { throw $Message }
}

# Codex adapter and lifecycle.
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object {
  Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null
}
$Codex = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Codex.name -ne "codemium" -or $Codex.version -ne $Version) { throw "Codex adapter version mismatch" }
if ($Codex.interface.displayName -ne "Codemium") { throw "Codex displayName mismatch" }
if ($Codex.hooks -ne './hooks/hooks.json') { throw "Codex manifest missing lifecycle hooks" }
$DefaultPrompt = ($Codex.interface.defaultPrompt -join ' ')
foreach ($Phrase in @(
  '@Codemium', 'automatically initialize or reuse .codemium Project Brain',
  'canonical project root shared across the Local checkout and linked worktrees',
  'Consolidate durable legacy Project Brain knowledge discovered in any linked worktree',
  'bundled UserPromptSubmit and Stop lifecycle hooks', 'CODEMIUM MEMORY RETRIEVAL MODE',
  'freshness-qualified', 'derived/regenerable structural index', 'DIRECT, RESOLVED, and HEURISTIC provenance'
)) {
  Assert-Contains ($Codex.interface.longDescription + ' ' + $DefaultPrompt) $Phrase "Codex manifest missing $Phrase"
}
$Hooks = Get-Content (Join-Path $Root "plugins\codemium\hooks\hooks.json") -Raw | ConvertFrom-Json
foreach ($Event in @('UserPromptSubmit','Stop')) {
  $Groups = @($Hooks.hooks.$Event)
  if ($Groups.Count -lt 1) { throw "Missing Codex hook event: $Event" }
  $Handlers = @($Groups[0].hooks)
  if ($Handlers.Count -lt 1 -or $Handlers[0].type -ne 'command') { throw "Invalid Codex hook handler: $Event" }
  if (-not $Handlers[0].commandWindows) { throw "Missing commandWindows for Codex hook: $Event" }
  Assert-Contains ($Handlers[0].command + $Handlers[0].commandWindows) 'project_brain_dispatch.py' "Codex hook must route through dispatcher: $Event"
}
$Gate = Get-Content (Join-Path $Root "plugins\codemium\hooks\project_brain_gate.py") -Raw
foreach ($Phrase in @('canonical_project_root','git-common-dir','migrate_legacy_project_brain','migrate_legacy_project_brains','worktree list','migrated_source_stamps','project-location.json')) {
  Assert-Contains $Gate $Phrase "Canonical Project Brain root missing $Phrase"
}
$Dispatch = Get-Content (Join-Path $Root "plugins\codemium\hooks\project_brain_dispatch.py") -Raw
foreach ($Phrase in @('CODEMIUM MEMORY RETRIEVAL MODE','rank_entries','Use minimum reasoning','host_turn_to_stop_ms','memory_mode','prepare_project_root')) {
  Assert-Contains $Dispatch $Phrase "Project Brain memory mode missing $Phrase"
}
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
foreach ($Phrase in @(
  'name: cm','# Codemium','@Codemium','$cm fast','preferred `low`','preferred `xhigh`',
  'Lightweight Project Brain memory mode','Project Brain persistence contract','Persistence gate',
  'Evidence freshness','Structural Intelligence contract','NEEDS_REVALIDATION','DIRECT','RESOLVED','HEURISTIC',
  'smallest **justified** change','Minimal production code **does not imply minimal tests**'
)) {
  Assert-Contains $MainSkill $Phrase "Codex skill missing $Phrase"
}
foreach ($Spec in @(
  @{Path="fix"; Heading='# $cm-fix'}, @{Path="test"; Heading='# $cm-test'},
  @{Path="review"; Heading='# $cm-review'}, @{Path="audit"; Heading='# $cm-audit'},
  @{Path="health"; Heading='# $cm-health'}, @{Path="init"; Heading='# $cm-init'}
)) {
  $Text = Get-Content (Join-Path $Root ("plugins\codemium\skills\" + $Spec.Path + "\SKILL.md")) -Raw
  Assert-Contains $Text $Spec.Heading "Focused Codex skill mismatch: $($Spec.Path)"
}

# Shared portable skill.
$Shared = Get-Content (Join-Path $Root "skills\cm\SKILL.md") -Raw
foreach ($Phrase in @('name: cm','portable Agent Skill','opencode/slash: "true"','Vendor model/thinking controls remain host-owned','Project Brain persistence is automatic','Evidence freshness','Structural Intelligence','NEEDS_REVALIDATION')) {
  Assert-Contains $Shared $Phrase "Shared cm skill missing $Phrase"
}

# Claude/Gemini manifests.
$ClaudeMarket = Get-Content (Join-Path $Root ".claude-plugin\marketplace.json") -Raw | ConvertFrom-Json
$ClaudePlugin = Get-Content (Join-Path $Root ".claude-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($ClaudeMarket.name -ne "codemium" -or $ClaudePlugin.version -ne $Version) { throw "Claude version mismatch" }
$ClaudeEntry = @($ClaudeMarket.plugins | Where-Object { $_.name -eq "codemium" })
if ($ClaudeEntry.Count -ne 1 -or $ClaudeEntry[0].source -ne "./" -or $ClaudeEntry[0].version -ne $Version) { throw "Claude marketplace source/version mismatch" }
$ClaudeCommand = Get-Content (Join-Path $Root "commands\cm.md") -Raw
Assert-Contains $ClaudeCommand '$ARGUMENTS' 'Claude command does not forward $ARGUMENTS'
Assert-Contains $ClaudeCommand '${CLAUDE_PLUGIN_ROOT}/plugins/codemium/engine/' 'Claude command does not reference the canonical engine'
if (Test-Path (Join-Path $Root "adapters\claude-code\.claude-plugin\plugin.json")) { throw "Duplicated old Claude adapter still exists" }

$Gemini = Get-Content (Join-Path $Root "gemini-extension.json") -Raw | ConvertFrom-Json
if ($Gemini.name -ne "codemium" -or $Gemini.version -ne $Version -or $Gemini.contextFileName -ne "GEMINI.md") { throw "Gemini adapter mismatch" }
$GeminiContext = Get-Content (Join-Path $Root "GEMINI.md") -Raw
$GeminiCommand = Get-Content (Join-Path $Root "commands\cm.toml") -Raw
Assert-Contains $GeminiContext 'host-agnostic coding-intelligence layer' 'Gemini context contract missing'
Assert-Contains $GeminiCommand '{{args}}' 'Gemini /cm must forward {{args}}'

# Shared v0.7 core contracts.
$Engine = Join-Path $Root "plugins\codemium\engine"
foreach ($Name in @('project_brain.py','repo_graph.py','graph_query.py','working_set.py','impact.py','scope_guard.py','test_map.py','health.py','task_compiler.py')) {
  if (-not (Test-Path (Join-Path $Engine $Name))) { throw "Missing engine/$Name" }
}
$RepoGraph = Get-Content (Join-Path $Engine "repo_graph.py") -Raw
foreach ($Phrase in @('GRAPH_SCHEMA_VERSION = 2','python-ast','fallback-regex','DIRECT','RESOLVED','HEURISTIC','manifest.json','DEPENDS_ON','TESTS')) {
  Assert-Contains $RepoGraph $Phrase "Structural Graph contract missing $Phrase"
}
$Brain = Get-Content (Join-Path $Engine "project_brain.py") -Raw
foreach ($Phrase in @('FRESH','NEEDS_REVALIDATION','SUPERSEDED','UNKNOWN','def entry_freshness(','def revalidate(','evidence')) {
  Assert-Contains $Brain $Phrase "Evidence freshness contract missing $Phrase"
}
$GraphQuery = Get-Content (Join-Path $Engine "graph_query.py") -Raw
foreach ($Phrase in @('find-symbol','callers','callees','dependents','dependencies','tests-for','def shortest_path(','def bounded_expand(')) {
  Assert-Contains $GraphQuery $Phrase "Graph query contract missing $Phrase"
}
Assert-Contains (Get-Content (Join-Path $Engine "working_set.py") -Raw) 'graph_assisted' 'Working Set v2 contract missing'
Assert-Contains (Get-Content (Join-Path $Engine "impact.py") -Raw) 'impact_mode' 'Impact v2 contract missing'
Assert-Contains (Get-Content (Join-Path $Engine "test_map.py") -Raw) 'provenance_counts' 'Test Intelligence v2 contract missing'
Assert-Contains (Get-Content (Join-Path $Engine "health.py") -Raw) 'fresh_to_worktree' 'Health freshness contract missing'
Assert-Contains (Get-Content (Join-Path $Engine "task_compiler.py") -Raw) 'apply_structural_escalation' 'Structural depth escalation missing'

# Docs.
foreach ($Path in @("scripts\install_host.py","scripts\doctor.py","scripts\verify_codex_plugin.py","INSTALL.md","HOSTS.md","PRD.md","PRD-v0.7.md","CHANGELOG.md")) {
  if (-not (Test-Path (Join-Path $Root $Path))) { throw "Missing $Path" }
}
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
foreach ($Phrase in @(
  'Persistent coding intelligence for AI coding agents','OpenAI Codex | **Stable**','Claude Code | **Beta**',
  'Gemini CLI | **Beta**','Cursor | **Beta**','OpenCode | **Beta**','@Codemium',
  'Project Brain is zero-setup for normal use','Structural Intelligence — v0.7','Evidence Bridge',
  'NEEDS_REVALIDATION','Source remains authoritative','INSTALL.md','HOSTS.md'
)) {
  Assert-Contains $Readme $Phrase "README missing $Phrase"
}
foreach ($Forbidden in @('Codex-first plugin','## Numbers','benchmarks/demo-numbers.svg','Ponytail-style')) {
  if ($Readme.Contains($Forbidden)) { throw "Public positioning regression: $Forbidden" }
}
$Hosts = Get-Content (Join-Path $Root "HOSTS.md") -Raw
foreach ($Phrase in @('host-agnostic at the product/core level','OpenCode | Beta','@Codemium','Structural Intelligence contract','Project Brain evidence/freshness contract')) {
  Assert-Contains $Hosts $Phrase "HOSTS.md missing $Phrase"
}
$Prd = Get-Content (Join-Path $Root "PRD.md") -Raw
Assert-Contains $Prd '@Codemium' 'PRD.md missing @Codemium invocation'
Assert-Contains $Prd 'Automatic lifecycle' 'PRD.md missing Project Brain automatic lifecycle'
Assert-Contains $Prd 'Durable capture policy' 'PRD.md missing durable capture policy'
Assert-Contains $Prd 'PRD-v0.7.md' 'PRD.md missing v0.7 extension'
$Prd07 = Get-Content (Join-Path $Root "PRD-v0.7.md") -Raw
foreach ($Phrase in @('Structural Intelligence & Evidence Bridge','Repository Structural Graph v2','Project Brain Freshness','FR-035')) {
  Assert-Contains $Prd07 $Phrase "PRD-v0.7 missing $Phrase"
}
$Install = Get-Content (Join-Path $Root "INSTALL.md") -Raw
foreach ($Phrase in @('/hooks','Structural Intelligence lifecycle','Evidence freshness lifecycle','0.7')) {
  Assert-Contains $Install $Phrase "INSTALL.md missing $Phrase"
}
$ChangeLog = Get-Content (Join-Path $Root "CHANGELOG.md") -Raw
Assert-Contains $ChangeLog '## 0.7.0 — Structural Intelligence & Evidence Bridge' 'CHANGELOG missing v0.7.0'

# Python syntax + core/Codex verifier + doctor + fixture.
$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\hooks"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks"),(Join-Path $Root "scripts") -Recurse -Filter *.py
foreach ($f in $py) {
  python -m py_compile $f.FullName
  if ($LASTEXITCODE -ne 0) { throw "Python syntax check failed: $($f.FullName)" }
}
python (Join-Path $Root "scripts\verify_core.py")
if ($LASTEXITCODE -ne 0) { throw "Core verification failed" }
python (Join-Path $Root "scripts\verify_codex_plugin.py")
if ($LASTEXITCODE -ne 0) { throw "Codex lifecycle verification failed" }
python (Join-Path $Root "scripts\doctor.py") --repo $Root | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Cross-host doctor failed" }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
if ($LASTEXITCODE -ne 0) { throw "Codemium fixture failed" }

# Portable installer lifecycle + hidden benchmark gate.
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("codemium-" + [System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Cursor install command failed" }
  foreach ($Path in @('.cursor\skills\cm\engine\project_brain.py','.cursor\skills\cm\engine\graph_query.py','.cursor\skills\cm\.codemium-installed.json')) {
    if (-not (Test-Path (Join-Path $TempDir $Path))) { throw "Cursor portable install missing $Path" }
  }
  $CursorSkill = Get-Content (Join-Path $TempDir ".cursor\skills\cm\SKILL.md") -Raw
  Assert-Contains $CursorSkill 'portable Agent Skill' 'Cursor skill source drift'
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir --uninstall | Out-Null
  if ($LASTEXITCODE -ne 0 -or (Test-Path (Join-Path $TempDir ".cursor\skills\cm"))) { throw "Cursor portable uninstall failed" }

  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "OpenCode install command failed" }
  if (-not (Test-Path (Join-Path $TempDir ".opencode\skills\cm\engine\graph_query.py"))) { throw "OpenCode graph_query install failed" }
  $OpenCodeSkill = Get-Content (Join-Path $TempDir ".opencode\skills\cm\SKILL.md") -Raw
  Assert-Contains $OpenCodeSkill 'opencode/slash: "true"' 'OpenCode portable install failed'
  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir --uninstall | Out-Null
  if ($LASTEXITCODE -ne 0 -or (Test-Path (Join-Path $TempDir ".opencode\skills\cm"))) { throw "OpenCode portable uninstall failed" }

  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --svg (Join-Path $TempDir "demo.svg") --markdown (Join-Path $TempDir "demo.md") | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Synthetic benchmark render failed" }
  Assert-Contains (Get-Content (Join-Path $TempDir "demo.svg") -Raw) 'SYNTHETIC / DEMO DATA' 'Synthetic watermark missing'
  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --publish --svg (Join-Path $TempDir "publish.svg") --markdown (Join-Path $TempDir "publish.md") *> $null
  if ($LASTEXITCODE -eq 0) { throw "Synthetic benchmark passed publication gate" }
} finally {
  Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "ALL CHECKS PASSED"
