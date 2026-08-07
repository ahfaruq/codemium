$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object {
  Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null
}
$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks") -Recurse -Filter *.py
foreach ($f in $py) { python -m py_compile $f.FullName }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
Write-Host "ALL CHECKS PASSED"
