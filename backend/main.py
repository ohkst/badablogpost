from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import shutil
import httpx
from typing import Optional
from dotenv import load_dotenv

# 브라우저 제어용 함수 (playwright)
from posting_agent import post_to_naver_blog

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="Naver Blog Auto Posting API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 프론트엔드 도메인만 허용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# vLLM 설정
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
VLLM_MODEL = os.getenv("VLLM_MODEL", "qwen")

# 업로드 폴더 생성
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class PostResponse(BaseModel):
    status: str
    message: str
    url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    vllm_connected: bool = False
    naver_configured: bool = False


@app.get("/", response_model=HealthResponse)
async def root():
    """서버 상태 확인"""
    vllm_connected = os.path.exists("/tmp/vllm_health_check")  # 임시 체크
    naver_configured = bool(os.getenv("NAVER_ID") and os.getenv("NAVER_PASSWORD"))
    
    return HealthResponse(
        status="ok",
        vllm_connected=vllm_connected,
        naver_configured=naver_configured
    )


@app.get("/api/health")
async def health_check():
    """API 헬스 체크"""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/post", response_model=PostResponse)
async def create_post(
    topic: str = Form(...),
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """
    네이버 블로그 자동 포스팅
    
    Args:
        topic: 포스팅 주제
        prompt: vLLM 에 전달할 상세 프롬프트
        image: 첨부할 이미지 (선택)
    
    Returns:
        - status: success/error
        - message: 결과 메시지
        - url: 포스팅된 블로그 URL
    """
    image_path = None
    
    # 이미지 업로드 처리
    if image:
        try:
            image_path = f"{UPLOAD_FOLDER}/{image.filename}"
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            print(f"이미지 업로드 완료: {image_path}")
        except Exception as e:
            return PostResponse(
                status="error",
                message=f"이미지 업로드 실패: {str(e)}",
                url=None
            )
    
    # 1. vLLM 연동을 통한 본문 생성
    generated_text = None
    try:
        generated_text = await call_vllm_api(topic, prompt)
        print(f"vLLM 에서 본문 생성 완료 (길이: {len(generated_text)} 자)")
    except Exception as e:
        return PostResponse(
            status="error",
            message=f"vLLM API 오류: {str(e)}",
            url=None
        )
    
    # 2. Playwright 를 통한 네이버 블로그 포스팅
    try:
        result = await post_to_naver_blog(topic, generated_text, image_path)
        
        # 임시 파일 정리
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        
        return PostResponse(
            status=result.get("status", "success"),
            message=result.get("message", "포스팅 완료"),
            url=result.get("url")
        )
        
    except Exception as e:
        return PostResponse(
            status="error",
            message=f"포스팅 실패: {str(e)}",
            url=None
        )


@app.post("/api/post/direct")
async def create_post_direct(
    topic: str = Form(...),
    content: str = Form(...)
):
    """
    vLLM 없이 직접 내용을 네이버 블로그에 포스팅
    
    Args:
        topic: 포스팅 제목
        content: 블로그 본문 내용 (HTML 포함 가능)
    
    Returns:
        - status: success/error
        - message: 결과 메시지
        - url: 포스팅된 블로그 URL
    """
    try:
        result = await post_to_naver_blog(topic, content, None)
        return PostResponse(
            status=result.get("status", "success"),
            message=result.get("message", "포스팅 완료"),
            url=result.get("url")
        )
    except Exception as e:
        return PostResponse(
            status="error",
            message=f"포스팅 실패: {str(e)}",
            url=None
        )


async def call_vllm_api(topic: str, prompt: str) -> str:
    """
    vLLM API 를 호출하여 블로그 본문 생성
    
    Args:
        topic: 포스팅 주제
        prompt: 상세 프롬프트
    
    Returns:
        생성된 블로그 본문 (HTML 형식)
    """
    system_prompt = """당신은 전문 블로거입니다. 독자들이 이해하기 쉽고 친근한 말투로 작성하세요.
- 서론, 본론, 결론 구조로 작성
- HTML 태그 (<h1>, <h2>, <p>, <ul>, <li>, <strong> 등) 를 사용하여 가독성 높이기
- 이모지를 적절히 사용하여 친근감 주기
- 네이버 블로그 최적화 내용 작성"""
    
    user_message = f"""주제: {topic}

요청: {prompt}

위 주제로 네이버 블로그 포스팅을 작성해주세요. HTML 태그를 사용하여 가독성을 높이세요."""

    try:
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
            
    except httpx.RequestError as e:
        raise Exception(f"vLLM 서버 연결 실패: {str(e)}. vLLM 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        raise Exception(f"vLLM API 호출 실패: {str(e)}")


@app.get("/api/config")
async def get_config():
    """현재 설정 정보 반환 (보안을 위해 민감 정보 제외)"""
    return {
        "vllm_url": VLLM_API_URL,
        "vllm_model": VLLM_MODEL,
        "naver_configured": bool(os.getenv("NAVER_ID")),
        "upload_folder": UPLOAD_FOLDER
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
