# CodeMentor Pro

**FastAPI + Streamlit 기반 AI 코드 분석 및 개발자 지원 플랫폼**

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
| Development | Docker, Git, GitHub |

## 시스템 구조

```text
Browser
   |
   v
Streamlit Frontend
   |
   | HTTP API
   v
FastAPI Backend
   |
   +-- Authentication / JWT
   |
   +-- Code Analysis ---- Ruff
   |
   +-- AI Review -------- Gemini API
   |
   +-- AI Chat ---------- Gemini API
   |
   +-- Service Layer
          |
          v
     Repository Layer
          |
          v
      PostgreSQL
```

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

현재 로컬 개발 환경 검증 기준:

- Backend: **127 tests passed**
- Frontend: **5 tests passed**
- Total: **132 tests passed**
- Ruff: 백엔드 전체 검사 통과

```powershell
python -m pytest backend/tests -q
python -m pytest frontend/tests -q
python -m ruff check backend
python -m ruff check frontend
```

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

로컬 검증 기준 백엔드 127개, 프론트엔드 5개 테스트가 통과했습니다.

### 주의 사항

현재 실행 방법은 Windows 11 및 PowerShell 개발 환경을 기준으로 작성되었습니다. 브라우저 인증 쿠키는 로컬 개발 시 `localhost`를 사용하며, 실제 배포 시에는 HTTPS 및 운영 환경에 맞는 보안 설정이 필요합니다.


## 향후 개선 사항

- Docker 기반 실행 환경 정리
- GitHub Actions CI 구성
- 인증 및 CSRF 보안 추가 강화
- 배포 환경 구성 및 운영 검증

## 프로젝트 목적

AI를 활용한 개발자 지원 기능을 구현하면서 Python 백엔드 개발에 필요한 API 설계, 인증, 데이터베이스 트랜잭션, 외부 서비스 연동, 자동화 테스트 경험을 통합하는 것을 목표로 했습니다.
