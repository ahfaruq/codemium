$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if ($Version -ne "0.5.0") { throw "Expected Codemium 0.5.0" }

# Codex
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object { Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null }
$Codex = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Codex.name -ne "codemium" -or $Codex.version -ne $Version) { throw "Codex adapter version mismatch" }
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
foreach ($Phrase in @("name: cm","@cm fast","preferred ``low``","preferred ``xhigh``","smallest **justified** change","Minimal production code **does not imply minimal tests**")) { if ($MainSkill -notmatch [regex]::Escape($Phrase)) { throw "Codex skill missing $Phrase" } }

# Claude Code
$ClaudeMarket = Get-Content (Join-Path $Root ".claude-plugin\marketplace.json") -Raw | ConvertFrom-Json
$ClaudePlugin = Get-Content (Join-Path $Root "adapters\claude-code\.claude-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($ClaudeMarket.name -ne "codemium" -or $ClaudePlugin.name -ne "codemium" -or $ClaudePlugin.version -ne $Version) { throw "Claude adapter mismatch" }
$ClaudeSkill = Get-Content (Join-Path $Root "adapters\claude-code\skills\cm\SKILL.md") -Raw
$ClaudeCommand = Get-Content (Join-Path $Root "adapters\claude-code\commands\cm.md") -Raw
if ($ClaudeSkill -notmatch "name: cm" -or $ClaudeSkill -notmatch "smallest justified engineering change" -or $ClaudeCommand -notmatch '\$ARGUMENTS') { throw "Claude skill/command contract missing" }

# Gemini CLI
$Gemini = Get-Content (Join-Path $Root "gemini-extension.json") -Raw | ConvertFrom-Json
if ($Gemini.name -ne "codemium" -or $Gemini.version -ne $Version -or $Gemini.contextFileName -ne "GEMINI.md") { throw "Gemini adapter mismatch" }
$GeminiContext = Get-Content (Join-Path $Root "GEMINI.md") -Raw
$GeminiCommand = Get-Content (Join-Path $Root "commands\cm.toml") -Raw
if ($GeminiContext -notmatch "host-agnostic coding-intelligence layer" -or $GeminiCommand -notmatch '\{\{args\}\}') { throw "Gemini context/command contract missing" }

# Public positioning
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
foreach ($Phrase in @("Persistent coding intelligence for AI coding agents","OpenAI Codex | **Stable**","Claude Code | **Beta**","Gemini CLI | **Beta**","HOSTS.md")) { if ($Readme -notmatch [regex]::Escape($Phrase)) { throw "README missing $Phrase" } }
if ($Readme -match "Codex-first plugin" -or $Readme -match "## Numbers" -or $Readme -match "benchmarks/demo-numbers.svg" -or $Readme -match "Ponytail-style") { throw "Public positioning regression" }
$Hosts = Get-Content (Join-Path $Root "HOSTS.md") -Raw
if ($Hosts -notmatch "host-agnostic at the product/core level") { throw "HOSTS contract missing" }

$Demo = Get-Content (Join-Path $Root "benchmarks\example-runs-v2.json") -Raw | ConvertFrom-Json
$Systems = @($Demo.runs | ForEach-Object { $_.system } | Select-Object -Unique)
foreach ($Arm in @("baseline","caveman","ponytail","codemium")) { if ($Systems -notcontains $Arm) { throw "Missing hidden benchmark arm $Arm" } }
if ((Get-Content (Join-Path $Root "benchmarks\demo-numbers.svg") -Raw) -notmatch "SYNTHETIC / DEMO DATA") { throw "Synthetic watermark missing" }

$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks") -Recurse -Filter *.py
foreach ($f in $py) { python -m py_compile $f.FullName }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
Write-Host "ALL CHECKS PASSED"
