#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/opt/codeviz-lab"
COMPOSE_FILE="deploy/docker-compose.prod.yml"

cd "$PROJECT_ROOT"

if [[ ! -f "deploy/.env.production" ]]; then
  echo "deploy/.env.production 파일이 없습니다."
  exit 1
fi

docker build -t codeviz-python-sandbox:latest -f backend/docker/python-runner/Dockerfile backend
docker build -t codeviz-c-sandbox:latest -f backend/docker/c-runner/Dockerfile backend
docker compose --env-file deploy/.env.production -f "$COMPOSE_FILE" up -d --build
docker image prune -f
