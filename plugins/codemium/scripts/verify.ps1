$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object {
  Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null
}
$Plugin = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Plugin.version -ne "0.3.0") { throw "Expected Codemium 0.3.0" }
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
if ($MainSkill -notmatch "name: cm" -or $MainSkill -notmatch "@cm fast" -or $MainSkill -notmatch "reasoning-policy" -or $MainSkill -notmatch "preferred ``low``" -or $MainSkill -notmatch "preferred ``xhigh``") { throw "Short-tag/depth/reasoning contract missing" }
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
if ($Readme -notmatch "@cm" -or $Readme -match '\$codemium:' -or $Readme -notmatch "FAST \| ``low``" -or $Readme -notmatch "CRITICAL \| ``xhigh``") { throw "README invocation/reasoning UX is stale" }
if (-not (Test-Path (Join-Path $Root "plugins\codemium\engine\reasoning_profile.py"))) { throw "reasoning_profile.py missing" }
if (-not (Test-Path (Join-Path $Root "plugins\codemium\skills\codemium\references\reasoning-policy.md"))) { throw "reasoning-policy.md missing" }
if ((Get-Content (Join-Path $Root "VERSION") -Raw).Trim() -ne "0.3.0") { throw "VERSION mismatch" }
$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks") -Recurse -Filter *.py
foreach ($f in $py) { python -m py_compile $f.FullName }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
Write-Host "ALL CHECKS PASSED"
