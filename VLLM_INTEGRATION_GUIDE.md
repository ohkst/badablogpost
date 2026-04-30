# 오픈클로(Openclaw) 통합 및 연동 가이드

이 문서는 본 프로젝트(`naverblog`)의 코드를 분석하고 연동 작업을 수행할 **오픈클로(Openclaw) AI 에이전트 및 모델**을 위한 시스템 공유 가이드라인입니다. 오픈클로는 본 시스템의 핵심 엔진으로서 블로그 본문을 창작하고 데이터를 파싱하는 역할을 담당합니다.

## 1. 프로젝트 개요 (Project Overview)
본 프로젝트는 **네이버 블로그 자동 포스팅 시스템**입니다. 
- **프론트엔드 (Cloudflare Pages 배포 예정)**: 관리자가 포스팅 주제, 프롬프트, 이미지를 업로드하는 UI입니다. (`frontend/` 디렉토리)
- **백엔드 (vLLM 구동 서버와 동일한 환경 배포 권장)**: 프론트엔드의 요청을 받아 **vLLM API를 호출해 본문을 생성**하고, Playwright를 이용해 네이버 블로그에 포스팅을 자동화합니다. (`backend/` 디렉토리)

## 2. 오픈클로(Openclaw)의 역할 및 목표 (Your Goal)
현재 `backend/main.py` 파일의 37번 라인 부근에는 오픈클로(vLLM 기반) API를 호출하여 블로그 본문을 생성하는 로직이 임시(Mock)로 작성되어 있습니다. 오픈클로는 이 저장소를 읽고 다음을 수행해야 합니다.

**[수행해야 할 작업]**
1. **vLLM API 호출 연동**: `backend/main.py` 내부의 텍스트 생성 로직을 실제 구동 중인 vLLM 서버 API (예: OpenAI 호환 API인 `http://localhost:8000/v1/completions` 등)를 호출하도록 변경해야 합니다.
2. **프롬프트 튜닝 로직 추가**: 사용자가 프론트엔드에서 입력한 `topic`(주제)과 `prompt`(세부 지시사항)를 조합하여, 네이버 블로그 포맷(HTML 기반 혹은 Markdown 형식 등)에 최적화된 결과물을 내놓을 수 있도록 프롬프트 파싱 및 전처리 로직을 오픈클로가 이해하고 작성해야 합니다.
3. **결과물 반환**: 오픈클로가 생성한 텍스트 결과물(HTML 구조화된 문자열 권장)을 Playwright 에이전트(`posting_agent.py`)로 넘겨주어 정상적으로 네이버 에디터에 삽입될 수 있도록 흐름을 완성하세요.

## 3. 핵심 파일 위치 (Key Files to Modify)
- **`backend/main.py`**
  - 파일 상단에 `VLLM_ENDPOINT` 변수가 `.env` 파일로부터 로드되도록 구성되어 있습니다.
  - `@app.post("/api/post")` 엔드포인트 내의 `generated_text = ...` 부분을 `VLLM_ENDPOINT`를 활용한 비동기 통신 로직(예: `aiohttp` 또는 `requests` 활용)으로 교체하세요.
  - **주의**: API 키나 엔드포인트 URL은 절대 하드코딩하지 말고 `VLLM_ENDPOINT` 변수를 사용하세요.
- **`backend/posting_agent.py`**
  - 생성된 본문이 네이버 SmartEditor ONE의 DOM 구조에 올바르게 삽입될 수 있도록, vLLM이 반환하는 포맷과 네이버 에디터의 `type` 방식이 호환되는지 확인하고 필요시 파싱 로직을 추가하세요.

## 4. 백엔드 실행 환경 (Environment)
- Python 3.10+
- FastAPI, Uvicorn, Playwright
- 로컬 테스트 실행 시: `cd backend && uvicorn main:app --reload`

## 5. 추가 참고 사항
- 네이버 봇 탐지 우회를 위해 `posting_agent.py`는 `headless=False` 상태로 개발 및 디버깅하는 것을 권장하며, 로컬 브라우저의 쿠키(세션 상태)를 불러와 네이버 로그인을 패스하도록 구성되어야 합니다.
- **보안 설정**: vLLM 서버의 URL 등 민감한 정보는 `backend/.env.example`을 복사하여 `backend/.env`를 만든 후 그 안에 기입하세요. `.env` 파일은 깃허브에 노출되지 않도록 `.gitignore`에 등록되어 있습니다.
