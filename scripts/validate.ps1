[CmdletBinding()]
param(
    [switch]$SkipIntegration,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repositoryRoot "backend"
$frontendRoot = Join-Path $repositoryRoot "frontend"
$backendVenvPython = Join-Path $backendRoot ".venv\Scripts\python.exe"
$pythonCommand = if (Test-Path -LiteralPath $backendVenvPython) {
    $backendVenvPython
} else {
    "python"
}
$npmExecutable = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npmExecutable) {
    $npmCommand = $npmExecutable.Source
} else {
    $codexNpm = Get-ChildItem `
        -Path "$env:LOCALAPPDATA\OpenAI\Codex\runtimes\cua_node" `
        -Filter npm.cmd `
        -Recurse `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    $npmCommand = if ($codexNpm) { $codexNpm } else { "npm.cmd" }
}
$npmDirectory = Split-Path -Parent $npmCommand
if ($npmDirectory -and (Test-Path -LiteralPath $npmDirectory)) {
    $env:Path = "$npmDirectory;$env:Path"
}
$testDatabaseName = "biztracker_test"
$databasePort = if ($env:BIZTRACKER_DB_PORT) {
    $env:BIZTRACKER_DB_PORT
} else {
    "5432"
}
$testDatabaseUrl = (
    "postgresql+psycopg://biztracker:biztracker_dev@localhost:" +
    "$databasePort/$testDatabaseName"
)

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)]
        [scriptblock]$Command,
        [Parameter(Mandatory)]
        [string]$FailureMessage
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

Push-Location $repositoryRoot
try {
    if (-not $SkipIntegration) {
        Invoke-CheckedCommand {
            docker compose up -d db
        } "A helyi PostgreSQL kontener nem indult el."

        $healthStatus = ""
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            $healthStatus = docker inspect --format "{{.State.Health.Status}}" biztracker-postgres
            if ($LASTEXITCODE -eq 0 -and $healthStatus -eq "healthy") {
                break
            }
            Start-Sleep -Seconds 1
        }
        if ($healthStatus -ne "healthy") {
            throw "A helyi PostgreSQL kontener nem valt healthy allapotuva."
        }
    }

    Push-Location $backendRoot
    try {
        $env:WEATHER_AUTOMATION_ENABLED = "false"
        $env:PYTHONDONTWRITEBYTECODE = "1"
        New-Item -ItemType Directory -Force -Path ".test-tmp" | Out-Null

        Invoke-CheckedCommand {
            & $pythonCommand -m pytest tests/unit -q -p no:cacheprovider `
                --basetemp .test-tmp/unit
        } "A backend unit tesztek hibaval alltak le."

        if (-not $SkipIntegration) {
            Pop-Location
            try {
                Invoke-CheckedCommand {
                    docker compose exec -T db dropdb `
                        --username biztracker `
                        --if-exists `
                        --force `
                        $testDatabaseName
                } "A dedikalt tesztadatbazis torlese sikertelen."
                Invoke-CheckedCommand {
                    docker compose exec -T db createdb `
                        --username biztracker `
                        $testDatabaseName
                } "A dedikalt tesztadatbazis letrehozasa sikertelen."
            }
            finally {
                Push-Location $backendRoot
            }

            $previousDatabaseUrl = $env:DATABASE_URL
            try {
                $env:DATABASE_URL = $testDatabaseUrl
                Invoke-CheckedCommand {
                    & $pythonCommand -m alembic upgrade head
                } "A tesztadatbazis migracioja sikertelen."
                Invoke-CheckedCommand {
                    & $pythonCommand -m scripts.bootstrap_reference_data
                } "A tesztadatbazis referenciaadatainak letrehozasa sikertelen."
                Invoke-CheckedCommand {
                    & $pythonCommand -m pytest tests/integration -q -p no:cacheprovider `
                        --basetemp .test-tmp/integration
                } "A backend integration tesztek hibaval alltak le."
            }
            finally {
                if ($null -eq $previousDatabaseUrl) {
                    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
                } else {
                    $env:DATABASE_URL = $previousDatabaseUrl
                }
            }
        }
    }
    finally {
        Pop-Location
    }

    if (-not $SkipFrontend) {
        Push-Location $frontendRoot
        try {
            Invoke-CheckedCommand {
                & $npmCommand run build:check
            } "A frontend build ellenorzese hibaval allt le."
        }
        finally {
            Pop-Location
        }
    }

    Write-Host "BizTracker validation completed successfully." -ForegroundColor Green
}
finally {
    Pop-Location
}
