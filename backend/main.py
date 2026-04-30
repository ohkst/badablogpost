from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import shutil

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

    # 1. vLLM 연동을 통한 본문 생성 (여기서는 Mockup 또는 향후 구현)
    # generated_text = call_vllm_api(topic, prompt)
    generated_text = f"<h1>{topic}</h1>\n<p>이 내용은 vLLM을 통해 자동 생성된 테스트용 본문입니다.</p>\n<p>프롬프트: {prompt}</p>"
    
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
