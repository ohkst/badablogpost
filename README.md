# Badablogpost - 네이버 블로그 자동 포스팅 시스템

vLLM AI 와 Playwright 를 활용한 네이버 블로그 자동 포스팅 시스템입니다.

## 🚀 기능

- **AI 자동 콘텐츠 생성**: vLLM (qwen 모델) 을 활용한 블로그 본문 자동 생성
- **자동 포스팅**: Playwright 를 사용한 네이버 블로그 자동화
- **이미지 첨부**: 포스팅 시 이미지 업로드 지원
- **웹 UI**: React + Vite 기반의 직관적인 인터페이스
- **Cloudflare 배포**: 프론트엔드는 Cloudflare Pages 에서 호스팅

## 📁 프로젝트 구조

```
badablogpost/
├── backend/
│   ├── main.py              # FastAPI 서버 (API 엔드포인트)
│   ├── posting_agent.py     # 네이버 블로그 자동화 (Playwright)
│   ├── .env                 # 환경 변수 설정
│   └── requirements.txt     # Python 의존성
├── frontend/
│   ├── src/
│   │   └── App.jsx          # React UI
│   ├── dist/                # 빌드 결과물 (Cloudflare 배포용)
│   └── package.json
└── README.md
```

## 🛠️ 설치 및 실행

### 1. 환경 설정

```bash
# backend/.env 파일 편집
cd backend
cp .env.example .env  # 없으면 직접 생성

# 환경 변수 편집
nano .env
```

**.env 파일 설정:**
```env
# 네이버 블로그 계정
NAVER_ID=your_naver_id
NAVER_PASSWORD=your_naver_password

# vLLM 설정
VLLM_API_URL=http://localhost:8000/v1/chat/completions
VLLM_MODEL=qwen

# 브라우저 상태 저장 경로
BROWSER_STATE_PATH=./browser_state.json
```

### 2. 백엔드 서버 실행

```bash
cd backend

# 의존성 설치
pip3 install -r requirements.txt

# Playwright 브라우저 설치
python3 -m playwright install chromium

# 서버 실행
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 프론트엔드 실행 (개발 모드)

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4. 프론트엔드 빌드 (Cloudflare 배포용)

```bash
cd frontend
npm run build

# dist/ 폴더를 Cloudflare Pages 에 배포
```

## 📡 API 엔드포인트

### 헬스 체크
```bash
GET /api/health
```

### 블로그 포스팅 (vLLM 사용)
```bash
POST /api/post
Content-Type: multipart/form-data

- topic: 포스팅 주제
- prompt: vLLM 프롬프트
- image: 첨부 이미지 (선택)
```

### 블로그 포스팅 (직접 내용)
```bash
POST /api/post/direct
Content-Type: multipart/form-data

- topic: 포스팅 제목
- content: 블로그 본문 내용 (HTML)
```

### 설정 확인
```bash
GET /api/config
```

## 🎯 사용 방법

### 웹 UI 사용

1. 프론트엔드 서버 실행 후 브라우저에서 접속
2. **주제** 입력 (예: "2026 년 인공지능 트렌드")
3. **프롬프트** 입력 (예: "전문적이고 친근한 말투로 작성해줘")
4. **이미지** 첨부 (선택)
5. **"자동 포스팅 시작"** 버튼 클릭
6. 네이버 블로그에 자동으로 포스팅 완료!

### API 직접 사용

```bash
curl -X POST http://localhost:8000/api/post \
  -F "topic=2026 년 AI 트렌드" \
  -F "prompt=전문적이면서도 친근한 블로거 말투로 작성해줘. 서론, 본론, 결론 구조로" \
  -F "image=@/path/to/image.jpg"
```

## 🔧 기술 스택

### 백엔드
- **FastAPI** - Python 웹 프레임워크
- **Playwright** - 브라우저 자동화
- **httpx** - 비동기 HTTP 클라이언트
- **uvicorn** - ASGI 서버

### 프론트엔드
- **React 19** - UI 라이브러리
- **Vite** - 빌드 도구
- **TailwindCSS** - 스타일링
- **Axios** - HTTP 클라이언트
- **Lucide React** - 아이콘

### AI
- **vLLM** - 로컬 LLM 서버
- **qwen 모델** - 콘텐츠 생성

## ⚠️ 주의사항

1. **네이버 계정 정보**: `.env` 파일에 네이버 ID 와 비밀번호를 안전하게 보관하세요
2. **브라우저 자동화 탐지**: 네이버에서 브라우저 자동화를 탐지할 수 있습니다. 필요시 CAPTCHA 처리 로직 추가 필요
3. **vLLM 서버**: vLLM 서버가 실행 중이어야 AI 콘텐츠 생성이 가능합니다
4. **이미지 크기**: 업로드 이미지는 10MB 이하 권장

## 📝 개발 로그

- **2026-04-30**: 초기 프로젝트 생성
- **2026-04-30**: vLLM 연동 완료
- **2026-04-30**: 네이버 블로그 자동화 완성
- **2026-04-30**: Cloudflare Pages 배포 준비 완료

## 🤝 기여

기여를 환영합니다! Issue 나 Pull Request 를 생성해주세요.

## 📄 라이선스

MIT License
