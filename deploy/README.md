# GCP 배포 가이드

소수 사용자용 운영 기준으로 `Compute Engine VM 1대 + Docker Compose` 구성을 사용합니다.

## 1. GCP 프로젝트

- 프로젝트 ID: `codeviz-491716`
- 권장 리전: 서울(`asia-northeast3`)

## 2. VM 권장 사양

- 머신 타입: `e2-small` 또는 `e2-medium`
- OS: `Ubuntu 24.04 LTS`
- 디스크: `30GB` 이상
- 방화벽: `80`, `443`, 필요하면 `22`

## 3. 서버 1회 초기 설정

서버 접속 후 아래 스크립트를 실행합니다.

```bash
chmod +x deploy/bootstrap-server.sh
./deploy/bootstrap-server.sh
```

## 4. 배포용 환경 파일 준비

서버에서 아래 파일을 직접 만듭니다.

```bash
cp deploy/.env.production.example deploy/.env.production
```

최소한 아래 값은 반드시 수정합니다.

- `APP_DOMAIN`
- `SITE_ADDRESS`
- `APP_ORIGIN`
- `CADDY_EMAIL`
- `POSTGRES_PASSWORD`
- `OPENAI_API_KEY` (AI selector 사용할 때)
- `VISUALIZATION_SELECTOR_BACKEND=openai` 또는 `manual`
- `AUTH_COOKIE_SECURE`

첫 배포를 IP 주소로 먼저 확인할 때는 아래처럼 두는 것을 권장합니다.

- `APP_DOMAIN=34.64.113.142`
- `SITE_ADDRESS=http://34.64.113.142`
- `APP_ORIGIN=http://34.64.113.142`
- `AUTH_COOKIE_SECURE=false`

도메인과 HTTPS를 붙인 뒤에는 아래처럼 바꿉니다.

- `APP_DOMAIN=codeviz.example.com`
- `SITE_ADDRESS=codeviz.example.com`
- `APP_ORIGIN=https://codeviz.example.com`
- `AUTH_COOKIE_SECURE=true`

## 5. GitHub Actions 시크릿

GitHub 저장소 Settings > Secrets and variables > Actions 에 아래를 등록합니다.

- `GCP_VM_HOST`
- `GCP_VM_USER`
- `GCP_VM_SSH_KEY`

## 6. 수동 첫 배포

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

이 스크립트는 아래를 수행합니다.

- Python sandbox 이미지 빌드
- 전체 서비스 `docker compose up -d --build`
- 불필요 이미지 정리

## 7. 자동 배포

`main` 브랜치에 push 하면 `.github/workflows/deploy-gcp.yml`이 실행됩니다.

## 8. 주의사항

- `deploy/.env.production`은 Git에 올리지 않습니다.
- 현재 구조는 백엔드 컨테이너가 Docker socket을 사용해 sandbox 컨테이너를 실행합니다.
- 공개 서비스로 열기 전에는 도메인/HTTPS/비밀번호/DB 백업 정책을 꼭 확인하세요.
