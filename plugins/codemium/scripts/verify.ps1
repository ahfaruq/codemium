$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
@(".agents\plugins\marketplace.json","plugins\codemium\.codex-plugin\plugin.json") | ForEach-Object { Get-Content (Join-Path $Root $_) -Raw | ConvertFrom-Json | Out-Null }
$Plugin = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw | ConvertFrom-Json
if ($Plugin.version -ne "0.4.0") { throw "Expected Codemium 0.4.0" }
$MainSkill = Get-Content (Join-Path $Root "plugins\codemium\skills\codemium\SKILL.md") -Raw
if ($MainSkill -notmatch "name: cm" -or $MainSkill -notmatch "@cm fast" -or $MainSkill -notmatch "reasoning-policy" -or $MainSkill -notmatch "preferred ``low``" -or $MainSkill -notmatch "preferred ``xhigh``") { throw "Short-tag/depth/reasoning contract missing" }
$Readme = Get-Content (Join-Path $Root "README.md") -Raw
if ($Readme -notmatch "@cm" -or $Readme -match '\$codemium:' -or $Readme -notmatch "FAST \| ``low``" -or $Readme -notmatch "CRITICAL \| ``xhigh``") { throw "README UX is stale" }
if ($Readme -match "## Numbers" -or $Readme -match "benchmarks/demo-numbers.svg") { throw "Numbers must remain hidden from the public README" }
if ($Readme -match "Ponytail-style") { throw "Codemium is incorrectly framed as Ponytail-style" }
$ManifestText = Get-Content (Join-Path $Root "plugins\codemium\.codex-plugin\plugin.json") -Raw
if ($ManifestText -match "benchmark dashboard") { throw "Benchmark dashboard must remain hidden from public plugin metadata" }
$Demo = Get-Content (Join-Path $Root "benchmarks\example-runs-v2.json") -Raw | ConvertFrom-Json
$Systems = @($Demo.runs | ForEach-Object { $_.system } | Select-Object -Unique)
foreach ($Arm in @("baseline","caveman","ponytail","codemium")) { if ($Systems -notcontains $Arm) { throw "Missing demo arm $Arm" } }
$DemoSvg = Get-Content (Join-Path $Root "benchmarks\demo-numbers.svg") -Raw
foreach ($Phrase in @("SYNTHETIC / DEMO DATA","caveman","ponytail","codemium")) { if ($DemoSvg -notmatch $Phrase) { throw "Demo SVG missing $Phrase" } }
if (-not (Test-Path (Join-Path $Root "plugins\codemium\engine\reasoning_profile.py"))) { throw "reasoning_profile.py missing" }
if (-not (Test-Path (Join-Path $Root "plugins\codemium\skills\codemium\references\reasoning-policy.md"))) { throw "reasoning-policy.md missing" }
if (-not (Test-Path (Join-Path $Root "benchmarks\render_numbers.py"))) { throw "render_numbers.py missing" }
if ((Get-Content (Join-Path $Root "VERSION") -Raw).Trim() -ne "0.4.0") { throw "VERSION mismatch" }
$py = Get-ChildItem (Join-Path $Root "plugins\codemium\engine"),(Join-Path $Root "plugins\codemium\tests"),(Join-Path $Root "benchmarks") -Recurse -Filter *.py
foreach ($f in $py) { python -m py_compile $f.FullName }
python (Join-Path $Root "plugins\codemium\tests\test_fixture.py")
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("codemium-" + [System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --svg (Join-Path $TempDir "demo.svg") --markdown (Join-Path $TempDir "demo.md") | Out-Null
  $Rendered = Get-Content (Join-Path $TempDir "demo.svg") -Raw
  foreach ($Phrase in @("SYNTHETIC / DEMO DATA","caveman","ponytail","codemium")) { if ($Rendered -notmatch $Phrase) { throw "Rendered benchmark missing $Phrase" } }
  python (Join-Path $Root "benchmarks\render_numbers.py") (Join-Path $Root "benchmarks\example-runs-v2.json") --publish --svg (Join-Path $TempDir "publish.svg") --markdown (Join-Path $TempDir "publish.md") *> $null
  if ($LASTEXITCODE -eq 0) { throw "Synthetic benchmark passed publication gate" }
} finally { Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "ALL CHECKS PASSED"
