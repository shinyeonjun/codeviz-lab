# CodeViz Backend

코드 실행 과정 시각화 서비스용 FastAPI 백엔드입니다.

## 구조

이 백엔드는 기능 중심 모듈 구조를 따릅니다.

- `app/core`: 설정, DB 연결 같은 공통 인프라
- `app/common`: 공통 응답 형식
- `app/modules/auth`: 로그인/세션 인증
- `app/modules/health`: 상태 확인
- `app/modules/examples`: 학습 카탈로그 기반 예제 코드 조회
- `app/modules/learning`: 학습 카테고리/수업 카탈로그
- `app/modules/executions`: 코드 실행, trace 저장, WebSocket 스트림
- `app/modules/exams`: 카테고리 시험, 채점 결과 저장

`executions` 모듈은 다음 책임으로 나뉩니다.

- `router`: HTTP/WebSocket 진입점
- `service`: 유스케이스 조합
- `repository`: 영속성 처리
- `ports`: 추상 인터페이스
- `runners`: 실제 코드 실행기
- `models`: DB 모델
- `schemas`: 요청/응답 스키마

## 실행 방법

### 1. 가상환경 생성

```powershell
cd D:\hohyun\backend
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. 패키지 설치

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. PostgreSQL 실행

SQLite는 더 이상 지원하지 않습니다. 로컬 개발도 PostgreSQL 기준입니다.

```powershell
cd D:\hohyun\backend
.\scripts\setup_docker.ps1
```

### 4. 환경 변수 설정

```powershell
Copy-Item .env.example .env
```

### 5. 서버 실행

```powershell
uvicorn app.main:app --reload
```

서버가 뜨면 아래 주소를 사용할 수 있습니다.

- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/docs`

## 테스트

```powershell
pytest
```

## Alembic 마이그레이션

앞으로 스키마 변경은 Alembic 기준으로 관리합니다.

```powershell
cd D:\hohyun\backend
venv\Scripts\Activate.ps1
python .\scripts\bootstrap_alembic.py
```

이 스크립트는 두 경우를 자동으로 처리합니다.

- 기존 앱이 이미 만든 테이블이 있으면 `alembic stamp head`
- 새 DB면 `alembic upgrade head`

새 마이그레이션을 만들 때는 아래처럼 사용합니다.

```powershell
alembic revision -m "설명"
```

## Docker 개발 환경

여자친구 프로젝트처럼 바로 세팅해서 돌려야 하면 아래 스크립트를 쓰면 됩니다.

```powershell
cd D:\hohyun\backend
.\scripts\setup_docker.ps1
.\scripts\run_backend_docker_dev.ps1
```

다른 프로젝트 Docker가 이미 떠 있으면 포트를 바꿔서 실행하면 됩니다.

```powershell
.\scripts\run_backend_docker_dev.ps1 -ProjectName codeviz-gf -PostgresHostPort 55433
```

이 스크립트는 다음을 처리합니다.

- Python sandbox 이미지 빌드
- PostgreSQL + pgvector 컨테이너 실행
- Docker sandbox 제한값을 환경 변수로 주입

## 샌드박스 보호 장치

현재 Docker 실행기는 아래 제한을 기본값으로 둡니다.

- `--network none`
- `--read-only`
- `--cap-drop ALL`
- `--security-opt no-new-privileges`
- `--memory 256m`
- `--cpus 0.5`
- `--pids-limit 64`
- `--tmpfs /tmp`
- 실행 시간 제한
- trace 단계 수 제한
- stdout 길이 제한
- source code / stdin 길이 제한

## 현재 구현 범위

- Python 코드 실행
- 실행 결과 trace 생성
- 실행 결과 DB 저장
- 예제 코드 조회
- 실행 결과 WebSocket 스냅샷 스트림

## 이후 확장 포인트

- AI 설명 생성 모듈 추가
- 다중 언어 실행기 추가
- 실행 로그 보존 정책 추가
