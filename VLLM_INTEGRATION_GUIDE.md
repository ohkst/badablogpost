# vLLM Agent Integration Guide

이 문서는 본 프로젝트(`naverblog`)를 분석하고 연동 작업을 수행할 **vLLM 에이전트(혹은 AI 시스템)**를 위한 공유 가이드라인입니다.

## 1. 프로젝트 개요 (Project Overview)
본 프로젝트는 **네이버 블로그 자동 포스팅 시스템**입니다. 
- **프론트엔드 (Cloudflare Pages 배포 예정)**: 관리자가 포스팅 주제, 프롬프트, 이미지를 업로드하는 UI입니다. (`frontend/` 디렉토리)
- **백엔드 (vLLM 구동 서버와 동일한 환경 배포 권장)**: 프론트엔드의 요청을 받아 **vLLM API를 호출해 본문을 생성**하고, Playwright를 이용해 네이버 블로그에 포스팅을 자동화합니다. (`backend/` 디렉토리)

## 2. vLLM 에이전트의 역할 및 목표 (Your Goal)
현재 `backend/main.py` 파일의 37번 라인 부근에는 vLLM API를 호출하여 블로그 본문을 생성하는 로직이 임시(Mock)로 작성되어 있습니다.

**[수행해야 할 작업]**
1. **vLLM API 호출 연동**: `backend/main.py` 내부의 텍스트 생성 로직을 실제 구동 중인 vLLM 서버 API (예: OpenAI 호환 API인 `http://localhost:8000/v1/completions` 등)를 호출하도록 변경해야 합니다.
2. **프롬프트 튜닝 로직 추가**: 사용자가 프론트엔드에서 입력한 `topic`(주제)과 `prompt`(세부 지시사항)를 조합하여, 네이버 블로그 포맷(HTML 기반 혹은 Markdown 형식 등)에 최적화된 결과물을 내놓을 수 있도록 프롬프트 파싱 및 전처리 로직을 추가해야 합니다.
3. **결과물 반환**: vLLM이 생성한 텍스트 결과물(HTML 구조화된 문자열 권장)을 Playwright 에이전트(`posting_agent.py`)로 넘겨주어 정상적으로 네이버 에디터에 삽입될 수 있도록 흐름을 완성해야 합니다.

## 3. 핵심 파일 위치 (Key Files to Modify)
- **`backend/main.py`**
  - `@app.post("/api/post")` 엔드포인트 내의 `generated_text = ...` 부분을 vLLM API 비동기 통신 로직(예: `aiohttp` 또는 `requests` 활용)으로 교체하세요.
- **`backend/posting_agent.py`**
  - 생성된 본문이 네이버 SmartEditor ONE의 DOM 구조에 올바르게 삽입될 수 있도록, vLLM이 반환하는 포맷과 네이버 에디터의 `type` 방식이 호환되는지 확인하고 필요시 파싱 로직을 추가하세요.

## 4. 백엔드 실행 환경 (Environment)
- Python 3.10+
- FastAPI, Uvicorn, Playwright
- 로컬 테스트 실행 시: `cd backend && uvicorn main:app --reload`

## 5. 추가 참고 사항
- 네이버 봇 탐지 우회를 위해 `posting_agent.py`는 `headless=False` 상태로 개발 및 디버깅하는 것을 권장하며, 로컬 브라우저의 쿠키(세션 상태)를 불러와 네이버 로그인을 패스하도록 구성되어야 합니다.
- vLLM 서버가 별도의 포트(예: 8080)나 도메인에서 돌고 있다면 `main.py`에 환경변수(`.env`)를 통해 해당 URL을 주입하도록 구성하세요.
