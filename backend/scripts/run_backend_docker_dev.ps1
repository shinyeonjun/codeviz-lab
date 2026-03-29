param(
    [string]$ProjectName = "codeviz",
    [int]$PostgresHostPort = 55433
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$setupScript = Join-Path $PSScriptRoot "setup_docker.ps1"
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "backend\\venv 가 없습니다. 먼저 Python 가상환경과 의존성을 설치해주세요."
}

& $setupScript -ProjectName $ProjectName -PostgresHostPort $PostgresHostPort

$env:DATABASE_URL = "postgresql+psycopg://codeviz:codeviz@127.0.0.1:$PostgresHostPort/codeviz"
$env:RUNNER_BACKEND = "docker"
$env:RUNNER_DOCKER_IMAGE = "codeviz-python-sandbox:latest"
$env:RUNNER_DOCKER_C_IMAGE = "codeviz-c-sandbox:latest"
$env:RUNNER_TIMEOUT_SECONDS = "3"
$env:RUNNER_DOCKER_MEMORY_LIMIT = "256m"
$env:RUNNER_DOCKER_CPUS = "0.5"
$env:RUNNER_DOCKER_PIDS_LIMIT = "64"
$env:RUNNER_DOCKER_TMPFS_SIZE = "64m"
$env:RUNNER_MAX_TRACE_STEPS = "0"
$env:RUNNER_MAX_STDOUT_CHARS = "10000"
$env:RUNNER_MAX_SOURCE_CODE_CHARS = "20000"
$env:RUNNER_MAX_STDIN_CHARS = "4000"

Write-Host "Docker sandbox + PostgreSQL 설정으로 백엔드를 실행합니다."
& $venvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
