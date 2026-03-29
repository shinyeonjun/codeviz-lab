param(
    [string]$ProjectName = "codeviz",
    [int]$PostgresHostPort = 55433
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonSandboxImage = "codeviz-python-sandbox:latest"
$cSandboxImage = "codeviz-c-sandbox:latest"
$composeFile = Join-Path $projectRoot "docker-compose.yml"

Write-Host "[1/4] Docker 상태 확인 중..."
docker version | Out-Null
docker compose version | Out-Null

Write-Host "[2/5] Python sandbox 이미지 빌드 중..."
docker build -t $pythonSandboxImage -f "$projectRoot\docker\python-runner\Dockerfile" $projectRoot

Write-Host "[3/5] C sandbox 이미지 빌드 중..."
docker build -t $cSandboxImage -f "$projectRoot\docker\c-runner\Dockerfile" $projectRoot

Write-Host "[4/5] PostgreSQL 컨테이너 시작 중..."
$env:POSTGRES_HOST_PORT = $PostgresHostPort.ToString()
docker compose -p $ProjectName -f $composeFile up -d db

$containerId = docker compose -p $ProjectName -f $composeFile ps -q db
if (-not $containerId) {
    throw "PostgreSQL 컨테이너 ID를 찾지 못했습니다."
}

Write-Host "[5/5] PostgreSQL health check 대기 중..."
for ($index = 0; $index -lt 30; $index++) {
    $status = docker inspect --format "{{.State.Health.Status}}" $containerId 2>$null
    if ($status -eq "healthy") {
        Write-Host "Docker 개발 환경 준비 완료 (PostgreSQL host port: $PostgresHostPort)"
        exit 0
    }
    Start-Sleep -Seconds 2
}

throw "PostgreSQL 컨테이너가 healthy 상태가 되지 않았습니다."
