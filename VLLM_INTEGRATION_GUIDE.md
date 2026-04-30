# 오픈클로(Openclaw) 통합 및 연동 가이드

이 문서는 본 프로젝트(`naverblog`)의 코드를 분석하고 연동 작업을 수행할 **오픈클로(Openclaw) AI 에이전트 및 모델**을 위한 시스템 공유 가이드라인입니다. 오픈클로는 본 시스템의 핵심 엔진으로서 블로그 본문을 창작하고 데이터를 파싱하는 역할을 담당합니다.

## 1. 프로젝트 개요 (Project Overview)
본 프로젝트는 **네이버 블로그 자동 포스팅 시스템**입니다. 
- **프론트엔드 (Cloudflare Pages 배포 예정)**: 관리자가 포스팅 주제, 프롬프트, 이미지를 업로드하는 UI입니다. (`frontend/` 디렉토리)
- **백엔드 (vLLM 구동 서버와 동일한 환경 배포 권장)**: 프론트엔드의 요청을 받아 **vLLM API를 호출해 본문을 생성**하고, Playwright를 이용해 네이버 블로그에 포스팅을 자동화합니다. (`backend/` 디렉토리)

## 2. 오픈클로(Openclaw)의 역할 및 목표 (Your Goal)
현재 `backend/main.py` 파일의 37번 라인 부근에는 오픈클로(vLLM 기반) API를 호출하여 블로그 본문을 생성하는 로직이 임시(Mock)로 작성되어 있습니다. 오픈클로는 이 저장소를 읽고 다음을 수행해야 합니다.

**[수행해야 할 작업 및 현재 진행 상태]**
1. **[완료] vLLM API 호출 연동**: `backend/main.py` 내부에 `requests`를 사용한 vLLM API (OpenAI 호환 Chat Completions API) 연동 및 에러 핸들링 코드가 추가되었습니다.
2. **[진행 대기] 프롬프트 및 파싱 고도화**: 사용자의 주제와 프롬프트를 바탕으로 네이버 블로그 에디터(SmartEditor ONE)에 완벽하게 호환되는 HTML 요소들로 결과물이 출력되도록 시스템 프롬프트를 최적화해야 합니다.
3. **[진행 대기 - 핵심] Playwright 자동화 로직 완성**: `backend/posting_agent.py` 파일은 현재 뼈대(Mockup)만 존재합니다. 오픈클로는 이 파일을 수정하여 다음을 구현해야 합니다:
   - 네이버 로그인 쿠키(NID_AUT, NID_SES)를 활용한 실제 로그인 세션 유지
   - 네이버 블로그 글쓰기 페이지 진입 및 SmartEditor ONE DOM 셀렉터를 통한 실제 텍스트/이미지 삽입
   - 네이버 봇 탐지 우회 로직 고도화 및 최종 발행(Publish) 버튼 클릭 로직 완성

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
