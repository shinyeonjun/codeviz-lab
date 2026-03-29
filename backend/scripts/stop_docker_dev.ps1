param(
    [string]$ProjectName = "codeviz"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot "docker-compose.yml"

docker compose -p $ProjectName -f $composeFile down
