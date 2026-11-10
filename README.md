# CodeMentor Pro

**FastAPI + Streamlit 기반 AI 코드 분석 및 개발자 지원 플랫폼**

**서비스:** https://codementor.hongtfolio.kr  
**GitHub:** https://github.com/skyn456-fumika/CodeMentor-Pro

CodeMentor Pro는 Python 소스 코드를 정적 분석하고, 생성형 AI를 활용해 코드 리뷰와 개선 방향을 제안하는 웹 애플리케이션입니다.

단순한 AI API 호출을 넘어 인증, 데이터 저장, 비즈니스 로직 분리, 트랜잭션 관리 및 자동화 테스트를 포함한 Python 백엔드 프로젝트입니다.

## 주요 기능

### 코드 분석 및 AI 리뷰
- Ruff를 이용한 Python 코드 정적 분석
- Gemini API 기반 코드 리뷰 및 개선 사항 제안
- 분석 결과 및 이전 분석 기록 조회
- 사용자별 분석 통계 제공

### AI 채팅
- Gemini 기반 코드 관련 질의응답
- 채팅 세션 생성 및 대화 이력 저장
- 이전 대화 내용을 활용한 문맥 기반 응답

### 사용자 인증
- 이메일·비밀번호 기반 회원가입 및 로그인
- JWT Access Token 인증
- Refresh Token Rotation 및 서버 측 토큰 폐기
- HttpOnly 쿠키를 이용한 로그인 상태 복원
- 브라우저 새로고침 후 로그인 유지
- Origin 및 CSRF 토큰 검증

## 기술 스택

| 구분 | 기술 |
|---|---|
| Backend | Python 3.11, FastAPI |
| Frontend | Streamlit |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy |
| Migration | Alembic |
| AI | Google Gemini API |
| Static Analysis | Ruff |
| Authentication | JWT, Refresh Token, HttpOnly Cookie |
| Testing | pytest, FastAPI TestClient |
| DevOps / Deployment | Docker Compose, Nginx, Apache, AWS EC2, Let’s Encrypt |
| Operations | PostgreSQL pg_dump/pg_restore, cron, AWS S3, IAM Role |
| Development | Docker, Git, GitHub |

## 시스템 구조

운영 환경에서는 Apache가 공개 HTTPS 연결을 종료하고, EC2의 localhost에만 바인딩된 Docker Nginx가 요청 경로를 분기합니다. Streamlit은 Docker 내부 네트워크로 FastAPI를 호출합니다.

```text
Browser (HTTPS)
    |
    v
Apache :443  -- Let's Encrypt TLS, HTTP -> HTTPS
    |
    v
127.0.0.1:18080 (Docker Nginx)
    |                   |
    | /                 | /api/, /health
    v                   v
Streamlit :8501      FastAPI :8000
    |                   |-- Authentication / JWT / CSRF
    +-- Internal API --> |-- Code Analysis ---- Ruff
                        |-- AI Review / Chat - Gemini API
                        |
                  Service / Repository
                        |
                  PostgreSQL 17
                  (Docker volume)

PostgreSQL -- pg_dump (daily) --> EC2 local backup
                                       |
                                       +--> Private S3 bucket
```

- 공개 도메인: `https://codementor.hongtfolio.kr`
- Nginx의 호스트 포트는 `127.0.0.1:18080`으로 제한해 외부 직접 접근을 차단합니다.
- 운영 환경에서는 Swagger / ReDoc / OpenAPI 경로를 Nginx에서 차단합니다.
- PostgreSQL은 외부 포트로 공개하지 않고 Docker 네트워크와 영속 볼륨을 사용합니다.

## 백엔드 설계 특징

### 계층별 책임 분리
API, Service, Repository 계층을 분리하여 HTTP 요청 처리, 비즈니스 로직, 데이터 접근 책임을 구분했습니다.

### 인증 및 토큰 관리
Access Token과 Refresh Token을 분리하고, Refresh Token의 해시를 데이터베이스에 저장하여 관리합니다.

토큰 갱신 시 기존 Refresh Token을 폐기하고 새로운 토큰을 발급하는 Rotation 방식을 구현했습니다.

### 데이터베이스 및 트랜잭션
SQLAlchemy를 사용해 데이터베이스에 접근하며, PostgreSQL과 Alembic을 이용해 영속 데이터 및 스키마 변경을 관리합니다.

### 예외 처리 및 테스트
API 오류 응답과 서비스 예외를 구분하고, pytest를 통해 인증, 코드 분석, AI 채팅, 데이터 접근 등의 기능을 검증합니다.

## 테스트

2026-11-10 로컬 검증 기준 **pytest 159개 통과**, Ruff 검사 통과입니다. 실제 Gemini 호출 대신 Mock을 사용하는 테스트와 API/인증 통합 테스트를 포함하며, 503 재시도 설정 검증도 추가했습니다.

```powershell
python -m pytest backend/tests frontend/tests -q
python -m ruff check backend frontend alembic
```

> 자동화 테스트 통과와 별도로, 운영 EC2에서 HTTPS 접속, 로그인·로그아웃, 세션 복원 및 Gemini AI 리뷰 호출을 점검했습니다.

## CI/CD 자동화

GitHub Actions를 이용해 코드 변경 시 정적 검사와 자동화 테스트를 수행합니다.

- **실행 조건:** `main` 브랜치 Push 및 Pull Request
- **정적 검사:** Ruff (Backend, Frontend, Alembic)
- **테스트 환경:** Python 3.11, PostgreSQL 17
- **데이터베이스:** Alembic 마이그레이션 자동 적용
- **자동 테스트:** pytest (로컬 기준 총 159개 검증; CI 실행별 결과는 GitHub Actions에서 확인)

CI는 로컬 개발 데이터베이스와 분리된 PostgreSQL 테스트 환경에서 실행되며, 테스트 결과를 GitHub Actions에서 확인할 수 있습니다.

[![CodeMentor Pro CI](https://github.com/skyn456-fumika/CodeMentor-Pro/actions/workflows/ci.yml/badge.svg)](https://github.com/skyn456-fumika/CodeMentor-Pro/actions/workflows/ci.yml)

## 개발 환경

- Python 3.11
- PostgreSQL 17
- Docker
- Windows 11 / PowerShell

## 설치 및 실행

### 1. 프로젝트 다운로드

```powershell
git clone https://github.com/skyn456-fumika/CodeMentor-Pro.git
cd CodeMentor-Pro
```

### 2. Python 가상환경 생성

Python 3.11을 기준으로 가상환경을 생성합니다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 의존성 설치

```powershell
python -m pip install -r requirements.txt
```

### 4. 환경변수 설정

`.env.example`을 복사하여 `.env`를 생성합니다.

```powershell
Copy-Item .env.example .env
```

이후 PostgreSQL 연결 정보, Gemini API 키, JWT 비밀키 등을 실제 개발 환경에 맞게 설정합니다.

`.env`에는 민감정보가 포함되므로 Git에 커밋하지 않습니다.

### 5. PostgreSQL 준비

PostgreSQL 17 서버를 실행하고 개발용 `codementor` 데이터베이스와 테스트용 `codementor_test` 데이터베이스를 준비합니다.

데이터베이스 연결 정보는 `.env`의 `DATABASE_URL`, `TEST_DATABASE_URL`을 사용합니다.

### 6. Alembic 마이그레이션

개발 DB:

```powershell
python -m alembic upgrade head
```

테스트 DB:

```powershell
# TEST_DATABASE_URL을 PowerShell 환경변수에 설정한 뒤
.\scripts\migrate_test.ps1
```

테스트 DB 스크립트는 실행 중 `DATABASE_URL`을 테스트 DB 주소로 변경하고, 작업 후 이전 환경변수 값을 복원합니다.

**환경변수 로딩 방식**

FastAPI와 Alembic은 `python-dotenv`를 이용해 프로젝트의 `.env` 파일에서 설정값을 읽습니다.

개발 DB 마이그레이션은 `.env`의 `DATABASE_URL`을 사용합니다.

테스트 DB 마이그레이션 스크립트는 PowerShell 프로세스의 `TEST_DATABASE_URL`을 사용하므로, 실행 전에 해당 환경변수를 별도로 설정해야 합니다.

스크립트는 작업 도중 `DATABASE_URL`을 테스트 DB 주소로 변경하고, 종료 시 이전 값으로 복원합니다.

**주의:** 개발 DB와 테스트 DB의 연결 주소를 반드시 구분해야 합니다.

### 7. FastAPI 실행

첫 번째 터미널에서:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API 문서: http://localhost:8000/docs

### 8. Streamlit 실행

두 번째 터미널에서:

```powershell
python -m streamlit run frontend/app.py
```

웹 애플리케이션: http://localhost:8501

### 9. 테스트 및 정적 검사

```powershell
python -m pytest backend/tests -q
python -m pytest frontend/tests -q
python -m ruff check backend
python -m ruff check frontend
```

로컬 검증 기준 전체 **159개 테스트가 통과**했습니다.

### 주의 사항

현재 실행 방법은 Windows 11 및 PowerShell 개발 환경을 기준으로 작성되었습니다. 브라우저 인증 쿠키는 로컬 개발 시 `localhost`를 사용하며, 실제 배포 시에는 HTTPS 및 운영 환경에 맞는 보안 설정이 필요합니다.

## Docker Compose 실행

CodeMentor-Pro는 Docker Compose를 이용해 PostgreSQL, FastAPI, Streamlit을 함께 실행할 수 있습니다.

### 1. 환경변수 준비

프로젝트 루트에서 `.env.example`을 복사해 `.env` 파일을 생성합니다.

```powershell
Copy-Item .env.example .env
```

`.env`에 PostgreSQL 비밀번호, Gemini API 키, JWT 비밀키 등 필요한 환경변수를 설정합니다.

Docker Compose용 `POSTGRES_PASSWORD`도 지정해야 합니다.

```dotenv
POSTGRES_PASSWORD=YOUR_LOCAL_DATABASE_PASSWORD
```

실제 비밀번호와 API 키가 포함된 `.env` 파일은 Git에 커밋하지 않습니다.

### 2. 컨테이너 실행

```powershell
docker compose up -d --build
```

Compose는 다음 세 서비스를 실행합니다.

- `db`: PostgreSQL 17
- `backend`: FastAPI 및 Alembic 마이그레이션
- `frontend`: Streamlit 웹 애플리케이션

PostgreSQL 데이터는 Docker 볼륨에 보관됩니다.

### 3. 서비스 접속

| 서비스 | URL |
|---|---|
| Streamlit | http://localhost:8501 |
| FastAPI Swagger | http://localhost:8000/docs |

### 4. 상태 및 로그 확인

```powershell
docker compose ps
docker compose logs --tail 50 backend
docker compose logs --tail 50 frontend
```

### 5. 컨테이너 종료

```powershell
docker compose down
```

위 명령은 컨테이너와 Compose 네트워크를 종료 및 제거하며, PostgreSQL 데이터 볼륨은 유지합니다.

**주의:** `docker compose down -v`는 Compose 데이터 볼륨도 삭제하므로 데이터 초기화가 필요한 경우에만 사용해야 합니다.

### Docker 네트워크 구성

Docker 컨테이너 사이의 내부 통신에는 서비스 이름을 사용합니다.

- Streamlit → FastAPI: `http://backend:8000`
- FastAPI → PostgreSQL: `db:5432`

브라우저에서 접근하는 주소는 `localhost`를 사용합니다.

위 `compose.yml` 절은 **로컬 개발 환경**을 설명합니다. 운영 EC2 배포는 별도의 `deploy/compose.ec2.yaml`을 사용합니다.


## AWS EC2 운영 배포

CodeMentor-Pro는 AWS EC2 Ubuntu 서버에서 Docker Compose로 실행됩니다. 기존에 운영 중인 Apache가 80/443 포트를 사용하므로 Docker Nginx는 `127.0.0.1:18080`에만 연결하고 Apache가 공개 요청을 전달합니다.

### 운영 환경변수

`deploy/production.env.example`을 참고하여 EC2에서 `deploy/.env.production`을 별도로 준비합니다. 실제 `.env.production`과 개인키·인증서 파일은 Git에 커밋하지 않습니다.

필수 설정 예시(값은 예시이며 실제 비밀키를 넣지 않음):

```dotenv
PUBLIC_URL=https://codementor.hongtfolio.kr
POSTGRES_PASSWORD=REPLACE_WITH_STRONG_DATABASE_PASSWORD
JWT_SECRET_KEY=REPLACE_WITH_STRONG_RANDOM_SECRET
GEMINI_API_KEY=REPLACE_WITH_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash
```

`deploy/compose.ec2.yaml`은 `GEMINI_MODEL`을 백엔드 컨테이너에 전달합니다. 운영에서 확인한 모델은 `gemini-3.5-flash`입니다. 사용 가능한 모델과 API 처리량은 시점·계정에 따라 달라질 수 있습니다.

### 배포 및 상태 확인

다음 명령은 EC2의 프로젝트 루트에서 실행합니다.

```bash
docker compose -p codementor-pro-ec2 \
  --env-file deploy/.env.production \
  -f deploy/compose.ec2.yaml config --quiet

docker compose -p codementor-pro-ec2 \
  --env-file deploy/.env.production \
  -f deploy/compose.ec2.yaml up -d --build

docker compose -p codementor-pro-ec2 \
  --env-file deploy/.env.production \
  -f deploy/compose.ec2.yaml ps

curl -i https://codementor.hongtfolio.kr/health
```

- 서비스: `db`, `backend`, `frontend`, `nginx`
- 백엔드 시작 시 `alembic upgrade head`로 스키마를 갱신합니다.
- 각 서비스의 재시작 정책은 `unless-stopped`입니다.
- 운영 변경 시 DB 볼륨 보존에 주의합니다. **`docker compose down -v`를 운영 서버에서 실행하지 마세요.**
- 도메인 및 TLS 인증서는 EC2의 Apache / Certbot에서 관리합니다. Docker 내부에 별도 TLS 인증서를 설치하지 않습니다.

### HTTPS 및 인증서 갱신

- 도메인: `codementor.hongtfolio.kr`
- TLS: Let's Encrypt + Apache
- HTTP 요청은 HTTPS로 리다이렉트하되 `/.well-known/acme-challenge/` 검증 경로는 유지합니다.
- `certbot.timer`가 활성화되어 있고 `certbot renew --dry-run --cert-name codementor.hongtfolio.kr` 검증을 통과했습니다.
- `/etc/letsencrypt/renewal-hooks/deploy/reload-apache.sh`에서 인증서 갱신 후 Apache를 재로드하도록 설정했습니다.

### PostgreSQL 백업과 복원

- **로컬 백업:** 매일 03:00 KST(EC2 UTC 기준 전날 18:00)에 사용자 crontab으로 실행
- **실행 스크립트:** `/home/ubuntu/scripts/codementor-backup.sh`
- **로컬 경로:** `/home/ubuntu/backups/codementor/`
- **백업 형식:** `pg_dump -Fc`, `pg_restore --list`로 파일 구조 검증
- **외부 백업:** EC2 IAM 역할을 사용하여 비공개 S3 버킷의 `codementor/` 접두사로 업로드
- **업로드 검사:** 로컬 파일과 S3 객체의 바이트 크기 비교
- **보관 기간:** 로컬 약 7일, S3 Lifecycle 30일
- **복원 검증:** 별도 임시 PostgreSQL 17 컨테이너로 복원하여 테이블 6개 확인. 운영 DB는 변경하지 않음

백업 파일에는 사용자 및 인증 관련 정보가 포함될 수 있으므로 파일 권한을 `600`으로 관리하고, 버킷은 퍼블릭 액세스를 차단합니다. IAM 역할에는 백업 경로에 필요한 최소 권한만 부여합니다.

백업 작업은 수동 실행·S3 업로드까지 검증했습니다. **예약된 Cron 작업의 실제 첫 자동 실행 결과는 `backup.log`에서 추가 확인이 필요합니다.** 파일 크기 검사는 복구 가능성을 보장하지 않으므로 추후 정기적인 복원 테스트를 수행해야 합니다.

```bash
# 백업 로그 확인
tail -n 30 /home/ubuntu/backups/codementor/backup.log

# 백업 파일 확인
ls -lh /home/ubuntu/backups/codementor/*.dump
```

## 문제 해결 사례

### Gemini AI 리뷰 API 503 / 504

운영 환경에서 `gemini-3.8-flash` 호출 시 `503 UNAVAILABLE`(일시적 과부하), `504 DEADLINE_EXCEEDED`(처리 시간 초과)가 발생했습니다. 503에 대한 제한적 재시도 설정을 추가하고 모델별 호출을 테스트하여, 실제 정상 응답이 확인된 `gemini-3.5-flash`를 운영 모델로 사용했습니다. 외부 AI 모델의 가용성은 변동될 수 있습니다.

### 기존 서비스와 포트 충돌 방지

EC2에서는 기존 Apache가 80/443 포트를 사용하고 있어 Docker Nginx를 루프백 `18080`에 연결했습니다. Apache가 공개 HTTPS를 처리하고 Docker Nginx가 `/api/`와 Streamlit 요청을 분기하도록 구성했습니다.

### 운영 중인 서버의 패키지 설치 문제

AWS CLI 설치 과정에서 Ubuntu의 APT 의존성 충돌을 확인했습니다. 기존 서비스를 보호하기 위해 커널 패키지 복구 작업을 보류하고, 공식 AWS CLI 설치 패키지를 별도로 설치했습니다. 서버 패키지 의존성 정리는 향후 유지보수 작업으로 남겨 두었습니다.

## 향후 개선 사항

- S3 백업의 정기적인 별도 복원 검증 및 알림 체계 마련
- AWS IAM, Secret 관리, API 사용량 및 비용 모니터링 강화
- Gemini 503/504 대응을 위한 시간 초과 정책과 대체 모델 전략 고도화
- EC2 운영 서버의 APT 의존성 문제를 계획된 유지보수 시간에 정리
- 배포 변경의 자동화 및 운영 지표·로그 모니터링 확대

## 프로젝트 목적

AI를 활용한 개발자 지원 기능을 구현하면서 Python 백엔드 개발에 필요한 API 설계, 인증, 데이터베이스 트랜잭션, 외부 서비스 연동, 자동화 테스트 경험을 통합하는 것을 목표로 했습니다.
