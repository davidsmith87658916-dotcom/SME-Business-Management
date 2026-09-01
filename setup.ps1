param(
    [switch]$RunMigrations
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendRoot = Join-Path $projectRoot "backend"
$venvRoot = Join-Path $backendRoot "venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $backendRoot)) {
    throw "Backend directory was not found: $backendRoot"
}

if (Test-Path -LiteralPath $venvPython) {
    try {
        $venvVersion = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($LASTEXITCODE -ne 0 -or $venvVersion -ne "3.12") {
            throw "invalid environment"
        }
    }
    catch {
        throw "The existing backend\venv is broken or is not Python 3.12. Rename it as a backup, then run this script again."
    }
}
else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python 3.12 is required. Install it, then run this script again."
    }

    $pythonVersion = & $pythonCommand.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($pythonVersion -ne "3.12") {
        throw "Python 3.12 is required; found Python $pythonVersion."
    }
    & $pythonCommand.Source -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the Python virtual environment."
    }
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $backendRoot "requirements.txt")

if ($RunMigrations) {
    Push-Location $backendRoot
    try {
        & $venvPython -m alembic upgrade head
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "Database migrations were not run. Back up the database, then rerun with -RunMigrations."
}

Write-Host "Setup completed successfully."
Write-Host "Run: $venvPython -m uvicorn app.main:app --reload --app-dir $backendRoot"
