$ErrorActionPreference = "Stop"
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
  # The benchmark publication-gate test intentionally executes one command
  # that must return non-zero. We inspect $LASTEXITCODE ourselves below.
  $PSNativeCommandUseErrorActionPreference = $false
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if ($Version -ne "0.6.5") { throw "Expected Codemium 0.6.5" }

function Assert-Contains([string]$Text, [string]$Needle, [string]$Message) {
  if (-not $Text.Contains($Needle)) { throw $Message }
}

# Codex
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object {
  Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null
}
$Codex = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Codex.name -ne "codemium" -or $Codex.version -ne $Version) { throw "Codex adapter version mismatch" }
if ($Codex.interface.displayName -ne "Codemium") { throw "Codex displayName mismatch" }
if ($Codex.hooks -ne './hooks/hooks.json') { throw "Codex manifest missing lifecycle hooks" }
$DefaultPrompt = ($Codex.interface.defaultPrompt -join ' ')
Assert-Contains $Codex.interface.longDescription '@Codemium' 'Codex manifest does not document @Codemium invocation'
Assert-Contains $DefaultPrompt 'automatically initialize or reuse .codemium Project Brain' 'Codex manifest missing automatic Project Brain persistence'
Assert-Contains $DefaultPrompt 'canonical project root shared across the Local checkout and linked worktrees' 'Codex manifest missing canonical Project Brain root'
Assert-Contains $DefaultPrompt 'bundled UserPromptSubmit and Stop lifecycle hooks' 'Codex manifest missing deterministic persistence gate'
Assert-Contains $DefaultPrompt 'CODEMIUM MEMORY RETRIEVAL MODE' 'Codex manifest missing lightweight memory-mode policy'
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
foreach ($Phrase in @('canonical_project_root','git-common-dir','migrate_legacy_project_brain','project-location.json')) {
  Assert-Contains $Gate $Phrase "Canonical Project Brain root missing $Phrase"
}
$Dispatch = Get-Content (Join-Path $Root "plugins\codemium\hooks\project_brain_dispatch.py") -Raw
foreach ($Phrase in @('CODEMIUM MEMORY RETRIEVAL MODE','rank_entries','Use minimum reasoning','host_turn_to_stop_ms','memory_mode','prepare_project_root')) {
  Assert-Contains $Dispatch $Phrase "Project Brain memory mode missing $Phrase"
}
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
foreach ($Phrase in @(
  'name: cm', '# Codemium', '@Codemium', '$cm fast', 'preferred `low`', 'preferred `xhigh`',
  'Lightweight Project Brain memory mode', 'Project Brain persistence contract', 'Persistence gate',
  'smallest **justified** change', 'Minimal production code **does not imply minimal tests**'
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

# Shared Agent Skill for Claude/Gemini/Cursor/OpenCode.
$Shared = Get-Content (Join-Path $Root "skills\cm\SKILL.md") -Raw
foreach ($Phrase in @('name: cm', 'portable Agent Skill', 'opencode/slash: "true"', 'Vendor model/thinking controls remain host-owned', 'Project Brain persistence is automatic')) {
  Assert-Contains $Shared $Phrase "Shared cm skill missing $Phrase"
}

# Claude Code repository-root plugin.
$ClaudeMarket = Get-Content (Join-Path $Root ".claude-plugin\marketplace.json") -Raw | ConvertFrom-Json
$ClaudePlugin = Get-Content (Join-Path $Root ".claude-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($ClaudeMarket.name -ne "codemium" -or $ClaudePlugin.version -ne $Version) { throw "Claude version mismatch" }
$ClaudeEntry = @($ClaudeMarket.plugins | Where-Object { $_.name -eq "codemium" })
if ($ClaudeEntry.Count -ne 1 -or $ClaudeEntry[0].source -ne "./" -or $ClaudeEntry[0].version -ne $Version) { throw "Claude marketplace source/version mismatch" }
$ClaudeCommand = Get-Content (Join-Path $Root "commands\cm.md") -Raw
Assert-Contains $ClaudeCommand '$ARGUMENTS' 'Claude command does not forward $ARGUMENTS'
Assert-Contains $ClaudeCommand '${CLAUDE_PLUGIN_ROOT}/plugins/codemium/engine/' 'Claude command does not reference the canonical engine'
if (Test-Path (Join-Path $Root "adapters\claude-code\.claude-plugin\plugin.json")) { throw "Duplicated old Claude adapter still exists" }

# Gemini CLI.
$Gemini = Get-Content (Join-Path $Root "gemini-extension.json") -Raw | ConvertFrom-Json
if ($Gemini.name -ne "codemium" -or $Gemini.version -ne $Version -or $Gemini.contextFileName -ne "GEMINI.md") { throw "Gemini adapter mismatch" }
$GeminiContext = Get-Content (Join-Path $Root "GEMINI.md") -Raw
$GeminiCommand = Get-Content (Join-Path $Root "commands\cm.toml") -Raw
Assert-Contains $GeminiContext 'host-agnostic coding-intelligence layer' 'Gemini context contract missing'
Assert-Contains $GeminiCommand '{{args}}' 'Gemini /cm must forward {{args}}'

# Docs and portable installer.
foreach ($Path in @("scripts\install_host.py","scripts\doctor.py","scripts\verify_codex_plugin.py","INSTALL.md","HOSTS.md","PRD.md","CHANGELOG.md")) {
  if (-not (Test-Path (Join-Path $Root $Path))) { throw "Missing $Path" }
}
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
foreach ($Phrase in @(
  'Persistent coding intelligence for AI coding agents', 'OpenAI Codex | **Stable**',
  'Claude Code | **Beta**', 'Gemini CLI | **Beta**', 'Cursor | **Beta**',
  'OpenCode | **Beta**', '@Codemium', 'Project Brain is zero-setup for normal use', 'INSTALL.md', 'HOSTS.md'
)) {
  Assert-Contains $Readme $Phrase "README missing $Phrase"
}
foreach ($Forbidden in @('Codex-first plugin', '## Numbers', 'benchmarks/demo-numbers.svg', 'Ponytail-style')) {
  if ($Readme.Contains($Forbidden)) { throw "Public positioning regression: $Forbidden" }
}

$Hosts = Get-Content (Join-Path $Root "HOSTS.md") -Raw
Assert-Contains $Hosts '@Codemium' 'HOSTS.md missing @Codemium invocation'
$Prd = Get-Content (Join-Path $Root "PRD.md") -Raw
Assert-Contains $Prd '@Codemium' 'PRD.md missing @Codemium invocation'
Assert-Contains $Prd 'Automatic lifecycle' 'PRD.md missing Project Brain automatic lifecycle'
Assert-Contains $Prd 'Durable capture policy' 'PRD.md missing durable capture policy'
$Install = Get-Content (Join-Path $Root "INSTALL.md") -Raw
Assert-Contains $Install '/hooks' 'INSTALL.md missing hook trust instructions'
Assert-Contains $Install 'Codemium `0.6.2` bundles `UserPromptSubmit` and `Stop` lifecycle hooks' 'INSTALL.md missing v0.6.2 lifecycle documentation'
$ChangeLog = Get-Content (Join-Path $Root "CHANGELOG.md") -Raw
Assert-Contains $ChangeLog '## 0.6.5 — Canonical Project Brain root' 'CHANGELOG missing v0.6.5'

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
  if (-not (Test-Path (Join-Path $TempDir ".cursor\skills\cm\engine\project_brain.py"))) { throw "Cursor portable install failed" }
  $CursorSkill = Get-Content (Join-Path $TempDir ".cursor\skills\cm\SKILL.md") -Raw
  Assert-Contains $CursorSkill 'portable Agent Skill' 'Cursor skill source drift'
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir --uninstall | Out-Null
  if ($LASTEXITCODE -ne 0 -or (Test-Path (Join-Path $TempDir ".cursor\skills\cm"))) { throw "Cursor portable uninstall failed" }

  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "OpenCode install command failed" }
  $OpenCodeSkill = Get-Content (Join-Path $TempDir ".opencode\skills\cm\SKILL.md") -Raw
  Assert-Contains $OpenCodeSkill 'opencode/slash: "true"' 'OpenCode portable install failed'
  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir --uninstall | Out-Null
  if ($LASTEXITCODE -ne 0 -or (Test-Path (Join-Path $TempDir ".opencode\skills\cm"))) { throw "OpenCode portable uninstall failed" }

  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --svg (Join-Path $TempDir "demo.svg") --markdown (Join-Path $TempDir "demo.md") | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Synthetic benchmark render failed" }
  $Rendered = Get-Content (Join-Path $TempDir "demo.svg") -Raw
  Assert-Contains $Rendered 'SYNTHETIC / DEMO DATA' 'Synthetic watermark missing'

  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --publish --svg (Join-Path $TempDir "publish.svg") --markdown (Join-Path $TempDir "publish.md") *> $null
  $PublishExit = $LASTEXITCODE
  if ($PublishExit -eq 0) { throw "Synthetic benchmark passed publication gate" }
} finally {
  Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "ALL CHECKS PASSED"
