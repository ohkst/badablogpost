# 오픈클로(Openclaw) 통합 및 연동 가이드

이 문서는 본 프로젝트(`naverblog`)의 코드를 분석하고 연동 작업을 수행할 **오픈클로(Openclaw) AI 에이전트 및 모델**을 위한 시스템 공유 가이드라인입니다. 오픈클로는 본 시스템의 핵심 엔진으로서 블로그 본문을 창작하고 데이터를 파싱하는 역할을 담당합니다.

## 1. 프로젝트 개요 (Project Overview)
본 프로젝트는 **네이버 블로그 자동 포스팅 시스템**입니다. 
- **프론트엔드 (Cloudflare Pages 배포 예정)**: 관리자가 포스팅 주제, 프롬프트, 이미지를 업로드하는 UI입니다. (`frontend/` 디렉토리)
- **백엔드 (vLLM 구동 서버와 동일한 환경 배포 권장)**: 프론트엔드의 요청을 받아 **vLLM API를 호출해 본문을 생성**하고, Playwright를 이용해 네이버 블로그에 포스팅을 자동화합니다. (`backend/` 디렉토리)

## 2. 오픈클로(Openclaw)의 역할 및 목표 (Your Goal)
현재 `backend/main.py` 파일의 37번 라인 부근에는 오픈클로(vLLM 기반) API를 호출하여 블로그 본문을 생성하는 로직이 임시(Mock)로 작성되어 있습니다. 오픈클로는 이 저장소를 읽고 다음을 수행해야 합니다.

**[오픈클로를 위한 상세 작업 지시서 - 시행착오 방지 가이드]**

오픈클로님, 현재 1단계(vLLM API 연동)와 2단계(자동 로그인 쿠키 동기화)는 완벽하게 끝났습니다. 이제 당신이 집중해야 할 마지막 핵심 임무는 **`backend/posting_agent.py` 파일을 완성하여 네이버 블로그에 실제로 글을 작성하고 발행(Publish)하는 것**입니다. 네이버 블로그(SmartEditor ONE) 구조는 복잡하므로 아래의 순서와 힌트를 정확히 따라주세요.

**1. 프롬프트 및 파싱 최적화 (`backend/main.py`)**
- `main.py`의 `call_vllm_api` 함수 내 시스템 프롬프트를 다듬어주세요.
- **중요**: 네이버 에디터는 복잡한 HTML보다는 기본 텍스트와 `<p>`, `<h1>`, `<h2>` 정도만 잘 인식합니다. 마크다운(`**`, `#` 등)을 쓰지 말고, 평문이나 아주 단순한 HTML 구조만 출력하도록 프롬프트를 튜닝하세요.

**2. Playwright 자동화 로직 완성 (`backend/posting_agent.py` 수정)**
이 파일은 현재 쿠키를 불러와 브라우저를 띄우는 것까지만 작성되어 있습니다. 다음 단계를 코드로 정확하게 구현하세요:

*   **단계 A: 글쓰기 페이지 진입**
    *   `await page.goto("https://blog.naver.com/{사용자아이디}?Redirect=Write")` 로 바로 이동하세요. (사용자 아이디는 파라미터로 받거나 하드코딩 후 안내)
    *   또는 메인 화면에서 '글쓰기' 버튼을 클릭하게 하세요. 네이버 에디터는 로딩이 매우 느리므로 `await page.wait_for_load_state('networkidle')`를 충분히 주세요.

*   **단계 B: iframe(mainFrame) 제어 (가장 중요!)**
    *   네이버 블로그 에디터는 `mainFrame` 이라는 이름의 `iframe` 안에 들어있습니다. `page` 객체에 바로 `click`을 하면 절대 안 됩니다!
    *   반드시 `frame = page.frame(name="mainFrame")`을 잡고, 이 `frame` 객체를 통해 셀렉터를 제어해야 합니다.

*   **단계 C: 제목 입력**
    *   제목 셀렉터는 보통 `textarea.se-ff-nanumgothic.se-fs32` 또는 `[placeholder="제목"]` 입니다.
    *   `await frame.fill('textarea.se-ff-nanumgothic', topic)` 처럼 입력하세요.

*   **단계 D: 본문 입력 (클립보드 방식 추천)**
    *   본문은 `contenteditable` 속성을 가진 `.se-component-content` 내부에 있습니다.
    *   단순히 `fill`이나 `type`을 쓰면 한글이 씹히거나 HTML이 텍스트 그대로 들어가는 에러가 무조건 발생합니다.
    *   **해결책**: `await frame.click('.se-component-content')` 로 포커스를 맞춘 뒤, 브라우저 콘솔에서 `document.execCommand('insertHTML', false, content)`를 실행하도록 `await frame.evaluate(f"document.execCommand('insertHTML', false, `{content}`)")` 를 사용하는 방식이 가장 확실합니다. 백틱(```) 이스케이프에 주의하세요.

*   **단계 E: 발행 버튼 클릭**
    *   에디터 우측 상단의 '발행' 버튼을 클릭: `await frame.click('.btn_publish')` 또는 `.btn_submit`
    *   클릭 후 카테고리나 태그를 묻는 팝업이 뜰 수 있습니다. 팝업 내의 최종 '발행' 버튼을 한 번 더 클릭해야 할 수 있으니 DOM 구조를 확인하는 딜레이(`await page.wait_for_timeout(2000)`)를 적절히 넣으세요.

*   **단계 F: 봇 탐지 우회 유지**
    *   브라우저 띄울 때 `args=['--disable-blink-features=AutomationControlled']` 는 이미 적용되어 있습니다. 입력 중간중간에 `random` 모듈을 이용해 `await page.wait_for_timeout(랜덤시간)` 을 넣어 사람처럼 보이게 하세요.

## 4. 백엔드 실행 환경 (Environment)
- Python 3.10+
- FastAPI, Uvicorn, Playwright
- 로컬 테스트 실행 시: `cd backend && uvicorn main:app --reload`

## 5. 추가 참고 사항
- 네이버 봇 탐지 우회를 위해 `posting_agent.py`는 `headless=False` 상태로 개발 및 디버깅하는 것을 권장하며, 로컬 브라우저의 쿠키(세션 상태)를 불러와 네이버 로그인을 패스하도록 구성되어야 합니다.
- **보안 설정**: vLLM 서버의 URL 등 민감한 정보는 `backend/.env.example`을 복사하여 `backend/.env`를 만든 후 그 안에 기입하세요. `.env` 파일은 깃허브에 노출되지 않도록 `.gitignore`에 등록되어 있습니다.
