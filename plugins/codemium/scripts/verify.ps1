$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if ($Version -ne "0.6.0") { throw "Expected Codemium 0.6.0" }

# Codex
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object { Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null }
$Codex = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Codex.name -ne "codemium" -or $Codex.version -ne $Version) { throw "Codex adapter version mismatch" }
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
foreach ($Phrase in @("name: cm","# Codemium — `$cm","`$cm fast","preferred ``low``","preferred ``xhigh``","smallest **justified** change","Minimal production code **does not imply minimal tests**")) {
  if ($MainSkill -notmatch [regex]::Escape($Phrase)) { throw "Codex skill missing $Phrase" }
}
if ($MainSkill -match "# Codemium — @cm") { throw "Stale @cm Codex invocation" }
foreach ($Spec in @(
  @{Path="fix"; Heading="# `$cm-fix"}, @{Path="test"; Heading="# `$cm-test"},
  @{Path="review"; Heading="# `$cm-review"}, @{Path="audit"; Heading="# `$cm-audit"},
  @{Path="health"; Heading="# `$cm-health"}, @{Path="init"; Heading="# `$cm-init"}
)) {
  $Text = Get-Content (Join-Path $Root ("plugins\codemium\skills\" + $Spec.Path + "\SKILL.md")) -Raw
  if ($Text -notmatch [regex]::Escape($Spec.Heading)) { throw "Focused Codex skill mismatch: $($Spec.Path)" }
}

# Shared Agent Skill for Claude/Gemini/Cursor/OpenCode.
$Shared = Get-Content (Join-Path $Root "skills\cm\SKILL.md") -Raw
foreach ($Phrase in @("name: cm","portable Agent Skill",'opencode/slash: "true"',"Vendor model/thinking controls remain host-owned")) {
  if ($Shared -notmatch [regex]::Escape($Phrase)) { throw "Shared cm skill missing $Phrase" }
}

# Claude Code repository-root plugin.
$ClaudeMarket = Get-Content (Join-Path $Root ".claude-plugin\marketplace.json") -Raw | ConvertFrom-Json
$ClaudePlugin = Get-Content (Join-Path $Root ".claude-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($ClaudeMarket.name -ne "codemium" -or $ClaudeMarket.version -ne $Version -or $ClaudePlugin.version -ne $Version) { throw "Claude version mismatch" }
$ClaudeEntry = @($ClaudeMarket.plugins | Where-Object { $_.name -eq "codemium" })
if ($ClaudeEntry.Count -ne 1 -or $ClaudeEntry[0].source -ne "./" -or $ClaudeEntry[0].version -ne $Version) { throw "Claude marketplace source/version mismatch" }
$ClaudeCommand = Get-Content (Join-Path $Root "commands\cm.md") -Raw
if ($ClaudeCommand -notmatch '\$ARGUMENTS' -or $ClaudeCommand -notmatch '\$\{CLAUDE_PLUGIN_ROOT\}/plugins/codemium/engine/') { throw "Claude command contract missing" }
if (Test-Path (Join-Path $Root "adapters\claude-code\.claude-plugin\plugin.json")) { throw "Duplicated old Claude adapter still exists" }

# Gemini CLI.
$Gemini = Get-Content (Join-Path $Root "gemini-extension.json") -Raw | ConvertFrom-Json
if ($Gemini.name -ne "codemium" -or $Gemini.version -ne $Version -or $Gemini.contextFileName -ne "GEMINI.md") { throw "Gemini adapter mismatch" }
$GeminiContext = Get-Content (Join-Path $Root "GEMINI.md") -Raw
$GeminiCommand = Get-Content (Join-Path $Root "commands\cm.toml") -Raw
if ($GeminiContext -notmatch "host-agnostic coding-intelligence layer" -or $GeminiCommand -notmatch '\{\{args\}\}') { throw "Gemini context/command contract missing" }

# Docs and portable installer.
foreach ($Path in @("scripts\install_host.py","scripts\doctor.py","INSTALL.md","HOSTS.md","PRD.md")) {
  if (-not (Test-Path (Join-Path $Root $Path))) { throw "Missing $Path" }
}
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
foreach ($Phrase in @("Persistent coding intelligence for AI coding agents","OpenAI Codex | **Stable**","Claude Code | **Beta**","Gemini CLI | **Beta**","Cursor | **Beta**","OpenCode | **Beta**","INSTALL.md","HOSTS.md")) {
  if ($Readme -notmatch [regex]::Escape($Phrase)) { throw "README missing $Phrase" }
}
if ($Readme -match "Codex-first plugin" -or $Readme -match "## Numbers" -or $Readme -match "benchmarks/demo-numbers.svg" -or $Readme -match "Ponytail-style") { throw "Public positioning regression" }

# Python syntax + doctor + fixture.
$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks"),(Join-Path $Root "scripts") -Recurse -Filter *.py
foreach ($f in $py) { python -m py_compile $f.FullName }
python (Join-Path $Root "scripts\doctor.py") --repo $Root | Out-Null
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")

# Portable installer lifecycle + hidden benchmark gate.
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("codemium-" + [System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir | Out-Null
  if (-not (Test-Path (Join-Path $TempDir ".cursor\skills\cm\engine\project_brain.py"))) { throw "Cursor portable install failed" }
  $CursorSkill = Get-Content (Join-Path $TempDir ".cursor\skills\cm\SKILL.md") -Raw
  if ($CursorSkill -notmatch "portable Agent Skill") { throw "Cursor skill source drift" }
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir --uninstall | Out-Null
  if (Test-Path (Join-Path $TempDir ".cursor\skills\cm")) { throw "Cursor portable uninstall failed" }

  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir | Out-Null
  $OpenCodeSkill = Get-Content (Join-Path $TempDir ".opencode\skills\cm\SKILL.md") -Raw
  if ($OpenCodeSkill -notmatch 'opencode/slash: "true"') { throw "OpenCode portable install failed" }
  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir --uninstall | Out-Null
  if (Test-Path (Join-Path $TempDir ".opencode\skills\cm")) { throw "OpenCode portable uninstall failed" }

  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --svg (Join-Path $TempDir "demo.svg") --markdown (Join-Path $TempDir "demo.md") | Out-Null
  if ((Get-Content (Join-Path $TempDir "demo.svg") -Raw) -notmatch "SYNTHETIC / DEMO DATA") { throw "Synthetic watermark missing" }
  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --publish --svg (Join-Path $TempDir "publish.svg") --markdown (Join-Path $TempDir "publish.md") *> $null
  if ($LASTEXITCODE -eq 0) { throw "Synthetic benchmark passed publication gate" }
} finally {
  Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "ALL CHECKS PASSED"
