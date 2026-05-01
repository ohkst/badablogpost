from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
import shutil
import uuid
import httpx
import requests
from dotenv import load_dotenv

# API Key 인증
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="Server API_KEY is not configured.")
    if api_key == expected_api_key:
        return api_key
    raise HTTPException(status_code=401, detail="Invalid or missing API Key.")

# .env 파일 로드
load_dotenv()

# vLLM 설정
VLLM_ENDPOINT = os.getenv("VLLM_ENDPOINT", "http://127.0.0.1:8080/v1/chat/completions")
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
VLLM_MODEL = os.getenv("VLLM_MODEL", "qwen")

# 브라우저 제어용 함수 (playwright)
from posting_agent import post_to_naver_blog

app = FastAPI(title="Naver Blog Auto Posting API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://badablogpost.pages.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class ExternalPostRequest(BaseModel):
    topic: str
    prompt: str
    image_url: Optional[str] = None


@app.get("/", response_model=HealthResponse)
async def root():
    """서버 상태 확인"""
    vllm_connected = True
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
    # 네이버 블로그 스마트 에디터 최적화 시스템 프롬프트
    system_prompt = """당신은 네이버 블로그 전문 블로거입니다. 다음 규칙을 엄격히 준수하세요:

1. **HTML 형식**: 네이버 스마트 에디터 ONE 에서 바로 사용할 수 있는 HTML 로 작성
   - 사용 가능 태그: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <br>
   - 금지 태그: <script>, <iframe>, <style>, <div> (네이버 에디터에서 동작하지 않음)

2. **구조**:
   - 서론: 주제 소개 및 독자의 관심을 끄는 오프닝
   - 본론: 핵심 내용을 2-3 개의 소제목 (<h2>) 으로 나누어 상세 설명
   - 결론: 요약 및 마무리 멘트

3. **스타일**:
   - 친근하고 전문적인 블로거 말투 (~해요, ~랍니다)
   - 이모지 적절히 사용 (📌, 💡, ✅, 🔥 등)
   - 가독성을 위한 불릿 포인트 활용
   - 핵심 내용은 **강조** 처리

4. **길이**: 800-1500 자 내외로 작성

5. **주의사항**:
   - HTML 이스케이프 처리 필요 (<, >, & 등을 &lt;, &gt;, &amp;로 변환)
   - 네이버 에디터에서 바로 렌더링 가능하도록 순수 HTML 만 작성"""
    
    user_message = f"""주제: {topic}

요청: {prompt}

위 주제로 네이버 블로그 포스팅을 작성해주세요. HTML 태그를 사용하여 가독성을 높이세요."""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                VLLM_ENDPOINT,
                json={
                    "model": VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", error_detail)
                except:
                    pass
                raise Exception(f"vLLM API error ({response.status_code}): {error_detail}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # HTML 이스케이프 처리 (vLLM 이 마크다운로 출력한 경우 대비)
            content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # 하지만 실제 HTML 태그는 복원
            content = content.replace("&lt;h1&gt;", "<h1>").replace("&lt;/h1&gt;", "</h1>")
            content = content.replace("&lt;h2&gt;", "<h2>").replace("&lt;/h2&gt;", "</h2>")
            content = content.replace("&lt;p&gt;", "<p>").replace("&lt;/p&gt;", "</p>")
            content = content.replace("&lt;ul&gt;", "<ul>").replace("&lt;/ul&gt;", "</ul>")
            content = content.replace("&lt;li&gt;", "<li>").replace("&lt;/li&gt;", "</li>")
            content = content.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
            content = content.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
            content = content.replace("&lt;br&gt;", "<br>")
            
            return content
            
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


@app.post("/api/external/post")
async def create_external_post(
    request: ExternalPostRequest,
    api_key: str = Depends(get_api_key)
):
    """외부 API 를 통한 포스팅 (API Key 인증 필요)"""
    image_path = None
    if request.image_url:
        os.makedirs("uploads", exist_ok=True)
        try:
            async with httpx.AsyncClient() as client:
                img_response = await client.get(request.image_url, timeout=30.0)
                img_response.raise_for_status()
                filename = request.image_url.split("/")[-1].split("?")[0]
                if not filename or "." not in filename:
                    filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
                image_path = f"uploads/{filename}"
                with open(image_path, "wb") as f:
                    f.write(img_response.content)
        except Exception as e:
            return {"status": "error", "message": f"이미지 다운로드 실패: {str(e)}"}

    # 1. vLLM 연동을 통한 본문 생성
    try:
        generated_text = await asyncio.to_thread(call_vllm_api, request.topic, request.prompt)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    # 2. Playwright 를 통한 네이버 블로그 포스팅
    try:
        result = await post_to_naver_blog(request.topic, generated_text, image_path)
        return {"status": "success", "message": "외부 포스팅 완료", "url": result.get("url")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/upload_state")
async def upload_state(file: UploadFile = File(...)):
    """
    로컬에서 추출한 naver_state.json 파일을 백엔드 서버로 업로드받아 저장합니다.
    """
    try:
        state_path = os.path.join(os.path.dirname(__file__), "naver_state.json")
        with open(state_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "message": "인증 세션 (naver_state.json) 이 성공적으로 업로드되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
