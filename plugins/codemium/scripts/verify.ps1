$ErrorActionPreference = "Stop"
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) { $PSNativeCommandUseErrorActionPreference = $false }
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if ($Version -ne "0.8.0") { throw "Expected Codemium 0.8.0, got $Version" }

Write-Host "== Codemium v0.8.0 full validation =="
$PyFiles = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\hooks"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks"),(Join-Path $Root "scripts") -Recurse -Filter *.py
foreach ($File in $PyFiles) {
  python -m py_compile $File.FullName
  if ($LASTEXITCODE -ne 0) { throw "Python syntax check failed: $($File.FullName)" }
}
Write-Host "PASS: Python syntax"

python (Join-Path $Root "scripts\verify_core.py")
if ($LASTEXITCODE -ne 0) { throw "Core verification failed" }
python (Join-Path $Root "scripts\verify_polyglot.py")
if ($LASTEXITCODE -ne 0) { throw "Polyglot verification failed" }
python (Join-Path $Root "scripts\verify_codex_plugin.py")
if ($LASTEXITCODE -ne 0) { throw "Codex lifecycle verification failed" }
python (Join-Path $Root "scripts\doctor.py") --repo $Root | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Cross-host doctor failed" }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
if ($LASTEXITCODE -ne 0) { throw "Compatibility fixture failed" }
Write-Host "PASS: core + Polyglot + Codex lifecycle + doctor + compatibility fixture"

$Codex = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
$Claude = Get-Content (Join-Path $Root ".claude-plugin\plugin.json") -Raw | ConvertFrom-Json
$ClaudeMarket = Get-Content (Join-Path $Root ".claude-plugin\marketplace.json") -Raw | ConvertFrom-Json
$Gemini = Get-Content (Join-Path $Root "gemini-extension.json") -Raw | ConvertFrom-Json
if ($Codex.version -ne $Version -or $Claude.version -ne $Version -or $Gemini.version -ne $Version) { throw "Host manifest version mismatch" }
$ClaudeEntry = @($ClaudeMarket.plugins | Where-Object { $_.name -eq "codemium" })
if ($ClaudeEntry.Count -ne 1 -or $ClaudeEntry[0].version -ne $Version) { throw "Claude marketplace version mismatch" }
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
foreach ($Phrase in @('Polyglot Intelligence','Tree-sitter','JavaScript','TypeScript','TSX','Cross-language','symbol-aware impact','test intelligence','v0.8.0')) {
  if (-not $Readme.Contains($Phrase)) { throw "README missing $Phrase" }
}
$Prd = Get-Content (Join-Path $Root "PRD-v0.8.md") -Raw
foreach ($Phrase in @('Polyglot Intelligence','Parser abstraction','Tree-sitter','Cross-language graph','Better impact intelligence','Better test intelligence')) {
  if (-not $Prd.Contains($Phrase)) { throw "PRD-v0.8 missing $Phrase" }
}
$Changelog = Get-Content (Join-Path $Root "CHANGELOG.md") -Raw
if (-not $Changelog.Contains('## 0.8.0 — Polyglot Intelligence')) { throw "CHANGELOG missing v0.8.0" }
Write-Host "PASS: v0.8 metadata and documentation contracts"

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("codemium-v08-" + [System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir | Out-Null
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $TempDir ".cursor\skills\cm\engine\parsers.py"))) { throw "Cursor portable install failed" }
  python (Join-Path $Root "scripts\install_host.py") --host cursor --scope project --project $TempDir --uninstall | Out-Null
  if ($LASTEXITCODE -ne 0 -or (Test-Path (Join-Path $TempDir ".cursor\skills\cm"))) { throw "Cursor portable uninstall failed" }

  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir | Out-Null
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $TempDir ".opencode\skills\cm\engine\parsers.py"))) { throw "OpenCode portable install failed" }
  python (Join-Path $Root "scripts\install_host.py") --host opencode --scope project --project $TempDir --uninstall | Out-Null
  if ($LASTEXITCODE -ne 0 -or (Test-Path (Join-Path $TempDir ".opencode\skills\cm"))) { throw "OpenCode portable uninstall failed" }

  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --svg (Join-Path $TempDir "demo.svg") --markdown (Join-Path $TempDir "demo.md") | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Synthetic benchmark render failed" }
  $DemoSvg = Get-Content (Join-Path $TempDir "demo.svg") -Raw
  if (-not $DemoSvg.Contains('SYNTHETIC / DEMO DATA')) { throw "Synthetic watermark missing" }
  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --publish --svg (Join-Path $TempDir "publish.svg") --markdown (Join-Path $TempDir "publish.md") 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { throw "Synthetic benchmark passed publication gate" }
} finally {
  Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}
Write-Host "PASS: portable installers + benchmark publication gate"
Write-Host "ALL CHECKS PASSED"
