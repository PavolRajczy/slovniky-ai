# Runs all API scenario tests under tests-api
# Usage: .\run_api_tests.ps1

Write-Host "Running Semantic Modeling Assistant API tests..." -ForegroundColor Cyan

# Resolve Python executable
$pythonFromVenv = Join-Path -Path $PWD -ChildPath ".venv/Scripts/python.exe"
if (Test-Path $pythonFromVenv) {
    $py = $pythonFromVenv
} else {
    $py = "python"
}

# Prepare environment
$env:PYTHONPATH = Join-Path $PWD "src"
$env:ONTOLOGY_BASE_DIR = Join-Path $PWD "data_test/ontologies"
New-Item -ItemType Directory -Force -Path $env:ONTOLOGY_BASE_DIR | Out-Null

# Discover tests
$testDir = Join-Path $PWD "tests-api"
if (-not (Test-Path $testDir)) {
    Write-Host "tests-api folder not found at $testDir" -ForegroundColor Red
    exit 1
}

$tests = Get-ChildItem -Path $testDir -Filter "test_*.py" -File | Sort-Object Name
if ($tests.Count -eq 0) {
    Write-Host "No tests found in tests-api." -ForegroundColor Yellow
    exit 0
}

$failures = @()
foreach ($t in $tests) {
    Write-Host ("==> Running {0}" -f $t.Name) -ForegroundColor Green
    & $py $t.FullName
    if ($LASTEXITCODE -ne 0) {
        $failures += $t.Name
        Write-Host ("FAILED: {0}" -f $t.Name) -ForegroundColor Red
    } else {
        Write-Host ("PASSED: {0}" -f $t.Name) -ForegroundColor DarkGreen
    }
}

Write-Host "" 
Write-Host "API tests completed." -ForegroundColor Cyan
if ($failures.Count -gt 0) {
    Write-Host ("Failed tests ({0}):" -f $failures.Count) -ForegroundColor Red
    $failures | ForEach-Object { Write-Host (" - {0}" -f $_) -ForegroundColor Red }
    exit 1
} else {
    Write-Host "All tests passed." -ForegroundColor DarkGreen
    exit 0
}
