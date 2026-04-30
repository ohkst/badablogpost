from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import shutil
from dotenv import load_dotenv
import requests

# .env 파일 로드
load_dotenv()

VLLM_ENDPOINT = os.getenv("VLLM_ENDPOINT", "http://127.0.0.1:8080/v1/chat/completions")

def call_vllm_api(topic: str, prompt: str) -> str:
    system_prompt = (
        "당신은 전문적인 네이버 블로그 포스팅 작가입니다. "
        "주어진 주제와 세부 지시사항을 바탕으로 완성도 높은 블로그 본문을 HTML 형식(<h1>, <h2>, <p> 등 사용)으로 작성해주세요. "
        "응답은 반드시 HTML 코드만 출력해야 하며, 마크다운 코드블록(```html)은 제외하고 순수 HTML만 반환하세요."
    )
    user_prompt = f"주제: {topic}\n세부 지시사항: {prompt}"

    # Chat Completions 형식
    payload = {
        "model": os.getenv("VLLM_MODEL", "openclo"), # 필요시 모델명 변경
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.7
    }

    try:
        response = requests.post(VLLM_ENDPOINT, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
                
        return f"<p>vLLM API 호출 성공했으나 결과를 파싱할 수 없습니다. 응답: {data}</p>"
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise Exception(f"vLLM API 호출 실패: 404 Not Found. VLLM_ENDPOINT 주소가 올바른지 확인하세요 (현재: {VLLM_ENDPOINT}). 보통 '/v1/chat/completions' 로 끝나야 합니다. 상세오류: {response.text}")
        raise Exception(f"vLLM API 오류: HTTP {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"vLLM API 호출 중 오류 발생: {str(e)}")

# 브라우저 제어용 함수 (playwright)
from posting_agent import post_to_naver_blog

app = FastAPI(title="Naver Blog Auto Posting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 보안을 위해 향후 프론트엔드 도메인으로 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostRequest(BaseModel):
    topic: str
    prompt: str

@app.post("/api/post")
async def create_post(
    topic: str = Form(...),
    prompt: str = Form(...),
    image: UploadFile = File(None)
):
    image_path = None
    if image:
        os.makedirs("uploads", exist_ok=True)
        image_path = f"uploads/{image.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    # 1. vLLM 연동을 통한 본문 생성
    try:
        # requests.post는 동기 함수이므로 event loop 블로킹 방지를 위해 to_thread 사용
        generated_text = await asyncio.to_thread(call_vllm_api, topic, prompt)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    # 2. Playwright를 통한 네이버 블로그 포스팅
    try:
        # 비동기 환경에서 Playwright 실행 
        # (실제 환경에서는 동시성 이슈 관리를 위해 큐 기반 워커나 태스크 큐 권장)
        result = await post_to_naver_blog(topic, generated_text, image_path)
        return {"status": "success", "message": "포스팅 완료", "url": result.get("url")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
