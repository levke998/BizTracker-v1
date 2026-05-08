<#
Installs or updates the BizTracker shared Szolnok weather sync Windows task.

The task runs the idempotent sync command on a fixed interval. It does not
duplicate weather observations because the database has a unique
location/time/provider constraint and the Python command only fetches missing
hours.
#>

param(
    [string]$TaskName = "BizTrackerWeatherSync",
    [int]$EveryHours = 3,
    [int]$DaysBack = 2,
    [string]$PythonCommand = "python",
    [datetime]$StartAt = (Get-Date).Date.AddHours((Get-Date).Hour + 1)
)

$ErrorActionPreference = "Stop"

$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDirectory = Split-Path -Parent $ScriptDirectory
$LogDirectory = Join-Path $BackendDirectory "logs"
$LogFile = Join-Path $LogDirectory "weather-sync.log"

if (!(Test-Path -LiteralPath $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory | Out-Null
}

$SyncCommand = @"
Set-Location -LiteralPath '$BackendDirectory'
if (!(Test-Path -LiteralPath '$LogDirectory')) { New-Item -ItemType Directory -Path '$LogDirectory' | Out-Null }
$PythonCommand -m scripts.sync_weather --days-back $DaysBack --json *>> '$LogFile'
"@

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command $($SyncCommand | ConvertTo-Json -Compress)"

$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At $StartAt `
    -RepetitionInterval (New-TimeSpan -Hours $EveryHours) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -TaskPath "\BizTracker\" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "BizTracker shared Szolnok hourly weather cache sync." `
    -Force | Out-Null

Write-Host "Installed scheduled task: \BizTracker\$TaskName"
Write-Host "Interval: every $EveryHours hour(s)"
Write-Host "Command: $PythonCommand -m scripts.sync_weather --days-back $DaysBack --json"
Write-Host "Log file: $LogFile"
