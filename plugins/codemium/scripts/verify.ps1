$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object {
  Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null
}
$Plugin = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Plugin.version -ne "0.2.0") { throw "Expected Codemium 0.2.0" }
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
if ($MainSkill -notmatch "name: cm" -or $MainSkill -notmatch "@cm fast" -or $MainSkill -notmatch "depth-policy") { throw "Short-tag/depth contract missing" }
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
if ($Readme -notmatch "@cm" -or $Readme -match '\$codemium:') { throw "README invocation UX is stale" }
$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks") -Recurse -Filter *.py
foreach ($f in $py) { python -m py_compile $f.FullName }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
Write-Host "ALL CHECKS PASSED"
