from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import shutil
import httpx

# 브라우저 제어용 함수 (playwright)
from posting_agent import post_to_naver_blog

# vLLM 엔드포인트 설정 (현재 연결된 vLLM 서버)
VLLM_API_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "qwen"

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
        generated_text = await call_vllm_api(topic, prompt)
    except Exception as e:
        return {"status": "error", "message": f"vLLM API 오류: {str(e)}"}
    
    # 2. Playwright 를 통한 네이버 블로그 포스팅
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

async def call_vllm_api(topic: str, prompt: str) -> str:
    """
    vLLM API 를 호출하여 블로그 본문 생성
    현재 연결된 vLLM 서버 (qwen 모델) 사용
    """
    system_prompt = "당신은 전문 블로거입니다. 독자들이 이해하기 쉽고 친근한 말투로 작성하세요."
    user_message = f"주제: {topic}\n\n요청: {prompt}\n\n위 주제로 네이버 블로그 포스팅을 작성해주세요. 서론, 본론, 결론 구조로 작성하고, HTML 태그를 사용하여 가독성을 높이세요."
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            VLLM_API_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"vLLM API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
