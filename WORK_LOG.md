# Bada Blog Post Project - 작업 기록 (Work Log)

이 문서는 프로젝트의 작업 내역, 구조 분석 및 향후 맥락(Context)을 유지하기 위해 기록되는 파일입니다. 오픈클로(OpenClo) 등 AI가 작업 맥락을 쉽게 이어갈 수 있도록 모든 주요 변경 사항과 진행 상황을 이곳에 남깁니다.

## 📌 프로젝트 개요
- **주요 기능**: vLLM과 Playwright를 활용한 네이버 블로그 자동 포스팅 시스템
- **백엔드**: FastAPI, Python (vLLM API 호출, Playwright 기반 블로그 자동화)
- **프론트엔드**: React(v19), Vite, TailwindCSS (사용자 입력 및 포스팅 요청 UI)

## 📅 작업 기록

### [2026-05-01] 프로젝트 초기 설정 및 분석 완료
- **내용**: 
  - GitHub 저장소(ohkst/badablogpost) 클론 완료.
  - 백엔드(`/backend`) 및 프론트엔드(`/frontend`) 코드 구조 파악 완료.
  - 향후 작업 시 한국어 피드백 제공 및 변경 사항을 `WORK_LOG.md`에 지속 기록하기로 합의.
  - 매 작업 완료 시 깃허브에 푸시(Push)하는 원칙 수립.
- **상태**: 초기화 완료

### [2026-05-01] 백엔드 터널 URL 연동
- **내용**:
  - 사용자로부터 전달받은 백엔드 터널 URL(`https://badablogpost.your-domain.com`)을 프론트엔드 환경 변수에 적용.
  - `frontend/.env.production` 파일 내 `VITE_API_BASE_URL` 수정.
  - `frontend/.env` 파일을 추가 생성하여 로컬 개발 환경에서도 해당 터널 URL을 바라보도록 설정.
- **상태**: 완료

### [2026-05-01] 파이썬 실행 환경 세팅 완료
- **내용**:
  - `backend` 폴더 내에 가상 환경(`venv`) 생성.
  - `requirements.txt`에 명시된 모든 패키지(FastAPI, vLLM 연동 모듈, Playwright 등) 설치 완료.
  - 네이버 블로그 포스팅 자동화를 위한 Playwright Chromium 브라우저 설치 완료.
- **상태**: 완료

### [2026-05-01] 네이버 로그인 스크립트 오류 핸들링 개선
- **내용**:
  - `naver_login.py` 실행 시 백엔드가 꺼져 있어서 발생하는 `JSONDecodeError` 문제 수정.
  - 백엔드 업로드가 실패하더라도, 같은 기기(맥미니)에서 실행 중이면 이미 로컬에 `naver_state.json`이 저장되므로 정상 작동한다는 안내 문구 추가.
- **상태**: 완료

### [2026-05-01] 외부 포스팅 전용 API 및 API Key 보안 추가
- **내용**:
  - `backend/main.py`에 `X-API-Key` 헤더를 검증하는 보안 로직 추가.
  - 외부 서비스(n8n, Zapier 등) 연동을 위해 JSON Payload를 허용하는 `/api/external/post` 엔드포인트 생성.
  - `image_url`을 전달받아 서버가 직접 이미지를 다운로드하고 Playwright로 전달하는 기능 구현.
  - `backend/.env.example`에 `API_KEY` 설정 가이드 추가.
- **상태**: 완료

### [2026-05-01] 프론트엔드 연동 CORS 오류 해결
- **내용**:
  - 프론트엔드(`https://badablogpost.pages.dev`)에서 백엔드로 요청 시 발생하던 CORS 오류 수정.
  - `FastAPI`의 `CORSMiddleware` 설정에서 `allow_credentials=True`와 `allow_origins=["*"]` 조합이 충돌하는 문제를 방지하기 위해 프론트엔드 도메인을 명시적으로 지정.
- **상태**: 완료
