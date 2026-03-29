#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y ca-certificates curl git docker.io docker-compose-v2

sudo systemctl enable docker
sudo systemctl start docker

if ! groups "$USER" | grep -q docker; then
  sudo usermod -aG docker "$USER"
  echo "docker 그룹이 추가되었습니다. 한 번 로그아웃 후 다시 접속하세요."
fi

sudo mkdir -p /opt/codeviz-lab
sudo chown -R "$USER":"$USER" /opt/codeviz-lab

echo "기본 서버 준비가 끝났습니다."
