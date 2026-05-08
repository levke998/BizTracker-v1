<#
Installs or updates the BizTracker shared Szolnok weather forecast sync Windows task.

The task refreshes the forecast cache on a fixed interval. Forecast rows are not
historical facts: the same location/time/provider row is updated when the
provider changes the forecast, and dashboard read-models recalculate from the
latest cached forecast.
#>

param(
    [string]$TaskName = "BizTrackerWeatherForecastSync",
    [int]$EveryHours = 3,
    [int]$ForecastDays = 7,
    [string]$PythonCommand = "python",
    [datetime]$StartAt = (Get-Date).Date.AddHours((Get-Date).Hour + 1)
)

$ErrorActionPreference = "Stop"

$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDirectory = Split-Path -Parent $ScriptDirectory
$LogDirectory = Join-Path $BackendDirectory "logs"
$LogFile = Join-Path $LogDirectory "weather-forecast-sync.log"

if (!(Test-Path -LiteralPath $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory | Out-Null
}

$SyncCommand = @"
Set-Location -LiteralPath '$BackendDirectory'
if (!(Test-Path -LiteralPath '$LogDirectory')) { New-Item -ItemType Directory -Path '$LogDirectory' | Out-Null }
$PythonCommand -m scripts.sync_weather_forecast --forecast-days $ForecastDays --json *>> '$LogFile'
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
    -ExecutionTimeLimit (New-TimeSpan -Minutes 45)

Register-ScheduledTask `
    -TaskName $TaskName `
    -TaskPath "\BizTracker\" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "BizTracker shared Szolnok hourly weather forecast cache sync." `
    -Force | Out-Null

Write-Host "Installed scheduled task: \BizTracker\$TaskName"
Write-Host "Interval: every $EveryHours hour(s)"
Write-Host "Command: $PythonCommand -m scripts.sync_weather_forecast --forecast-days $ForecastDays --json"
Write-Host "Log file: $LogFile"
