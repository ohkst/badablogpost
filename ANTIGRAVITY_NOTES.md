# 📨 Antigravity 에게 보내는 편지

> **From:** 도비 (Dobi) - AI 프로젝트 마스터  
> **To:** Antigravity IDE  
> **Date:** 2026-04-30  
> **Subject:** badablogpost 프로젝트 컨텍스트 공유

---

## 👋 인사

안녕하세요, Antigravity!

도비입니다. 제가 성태님과 함께 개발한 **badablogpost** 프로젝트의 현재 상태를 공유드립니다. 이 문서를 통해 프로젝트의 배경, 구조, 그리고 향후 과제를 쉽게 이해하실 수 있을 것입니다.

---

## 📦 프로젝트 개요

### 프로젝트명: Badablogpost
**한 줄 요약:** vLLM AI 와 Playwright 를 활용한 네이버 블로그 자동 포스팅 시스템

**프로젝트 목표:**
- 사용자가 주제만 입력하면 AI 가 블로그 콘텐츠를 자동 생성
- 생성된 내용을 자동으로 네이버 블로그에 포스팅
- 이미지 첨부 기능 지원

---

## 🏗️ 현재 진행 상황

### ✅ 완료된 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| 백엔드 API | ✅ 완료 | FastAPI 기반 REST API 서버 |
| vLLM 연동 | ✅ 완료 | qwen 모델을 통한 콘텐츠 생성 |
| 네이버 자동화 | ✅ 완료 | Playwright 로 로그인 및 포스팅 |
| 프론트엔드 UI | ✅ 완료 | React + TailwindCSS 기반 웹 인터페이스 |
| Cloudflare 배포 | ✅ 준비 완료 | `https://badablogpost.pages.dev/` |

### 🔄 현재 실행 중

```bash
# 백엔드 서버
📍 http://localhost:8000
🔧 uvicorn main:app --reload --host 0.0.0.0 --port 8000

# vLLM 서버
📍 http://localhost:8000/v1/chat/completions
🤖 모델: qwen
```

---

## 📁 프로젝트 구조

```
badablogpost/
├── backend/
│   ├── main.py              # FastAPI 서버 (주요 엔드포인트)
│   ├── posting_agent.py     # 네이버 블로그 자동화 로직
│   ├── .env                 # 환경 변수 (비밀 정보)
│   └── requirements.txt     # Python 의존성
│
├── frontend/
│   ├── src/
│   │   └── App.jsx          # React 메인 컴포넌트
│   ├── dist/                # Cloudflare 배포용 빌드 결과
│   └── package.json
│
└── README.md                # 전체 사용 가이드
```

---

## 🔑 핵심 기술 스택

| 계층 | 기술 | 역할 |
|------|------|------|
| **백엔드** | FastAPI | REST API 서버 |
| **AI** | vLLM (qwen) | 블로그 콘텐츠 생성 |
| **자동화** | Playwright | 네이버 브라우저 제어 |
| **프론트엔드** | React 19 + Vite | 사용자 인터페이스 |
| **스타일링** | TailwindCSS | UI 스타일링 |
| **배포** | Cloudflare Pages | 프론트엔드 호스팅 |

---

## 📡 주요 API 엔드포인트

### 1. 블로그 포스팅 (vLLM 사용)
```http
POST /api/post
Content-Type: multipart/form-data

{
  "topic": "2026 년 AI 트렌드",
  "prompt": "전문적이면서 친근한 말투로 작성",
  "image": "image.jpg"  // 선택
}
```

**동작 흐름:**
1. 사용자가 주제와 프롬프트 입력
2. vLLM 이 블로그 본문 자동 생성
3. Playwright 가 네이버 블로그에 자동 포스팅
4. 포스팅 URL 반환

### 2. 직접 포스팅 (vLLM 없음)
```http
POST /api/post/direct
Content-Type: multipart/form-data

{
  "topic": "제목",
  "content": "<h1>HTML 형식의 본문</h1>"
}
```

---

## 🎯 사용 방법 (간단 가이드)

### 웹 UI 로 사용
1. 프론트엔드 실행: `cd frontend && npm run dev`
2. 브라우저에서 `http://localhost:5173` 접속
3. 주제와 프롬프트 입력
4. "자동 포스팅 시작" 클릭
5. 네이버 블로그에 자동 포스팅 완료!

### API 로 사용
```bash
curl -X POST http://localhost:8000/api/post \
  -F "topic=2026 년 AI 트렌드" \
  -F "prompt=전문적인 블로그 글로 작성"
```

---

## ⚙️ 설정 방법

### 1. 환경 변수 설정 (`.env`)
```env
# 네이버 계정 (필수)
NAVER_ID=your_naver_id
NAVER_PASSWORD=your_naver_password

# vLLM 설정
VLLM_API_URL=http://localhost:8000/v1/chat/completions
VLLM_MODEL=qwen

# 브라우저 상태 저장
BROWSER_STATE_PATH=./browser_state.json
```

### 2. 의존성 설치
```bash
# 백엔드
cd backend
pip3 install -r requirements.txt
python3 -m playwright install chromium

# 프론트엔드
cd frontend
npm install
```

---

## 🚧 향후 과제

| 우선순위 | 과제 | 설명 |
|---------|------|------|
| 🔴 높음 | 네이버 CAPTCHA 처리 | 자동화 탐지 우회 필요 |
| 🟡 중간 | vLLM 서버 배포 | 로컬 대신 클라우드 vLLM |
| 🟢 낮음 | 멀티 계정 지원 | 여러 블로그 동시 관리 |
| 🟢 낮음 | 분석 대시보드 | 포스팅 성과 추적 |

---

## 🐛 알려진 이슈

1. **네이버 CAPTCHA**: 로그인 시 CAPTCHA 발생 가능
2. **브라우저 자동화 탐지**: 네이버에서 봇 탐지 가능
3. **이미지 업로드 안정성**: 대용량 이미지 업로드 실패 가능성

---

## 💡 Antigravity 에게 요청

Antigravity 가 이 프로젝트를 분석하실 때 다음을 참고해주세요:

1. **`posting_agent.py`** - 네이버 자동화의 핵심 로직
2. **`main.py`** - API 엔드포인트와 vLLM 연동
3. **`frontend/src/App.jsx`** - 사용자 인터페이스

**추가 개발이 필요한 부분:**
- CAPTCHA 처리 로직
- 에러 핸들링 강화
- 로그 시스템 개선

---

## 📞 연락처

- **프로젝트 마스터:** 성태님
- **도비:** AI 프로젝트 마스터 (이 문서 작성자)
- **리ポジ토리:** `https://github.com/ohkst/badablogpost.git`

---

## 🙏 마무리

Antigravity 의 AI 에이전트 기능으로 이 프로젝트를 더욱 발전시킬 수 있기를 바랍니다!

**감사합니다!**  
도비 🐾

---

*이 문서는 도비가 작성하여 Git에 푸시했습니다.*  
*마지막 업데이트: 2026-04-30*
