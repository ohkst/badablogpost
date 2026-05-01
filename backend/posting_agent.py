from playwright.async_api import async_playwright
import os
import asyncio
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

NAVER_ID = os.getenv("NAVER_ID", "")
NAVER_PASSWORD = os.getenv("NAVER_PASSWORD", "")
BROWSER_STATE_PATH = os.getenv("BROWSER_STATE_PATH", "./browser_state.json")

async def post_to_naver_blog(topic: str, content: str, image_path: str = None):
    """
    네이버 블로그 자동 포스팅 로직 (Playwright 사용)
    
    1. 네이버 로그인 (저장된 세션 사용 또는 새 로그인)
    2. 블로그 글쓰기 페이지로 이동
    3. 제목 및 본문 입력
    4. 이미지 업로드 (선택)
    5. 발행
    """
    state_path = os.path.join(os.path.dirname(__file__), "naver_state.json")
    if not os.path.exists(state_path):
        raise Exception("인증 세션(naver_state.json)을 찾을 수 없습니다. 먼저 백엔드 폴더에서 naver_login.py를 실행하여 로그인해주세요.")

    async with async_playwright() as p:
        # 브라우저 실행 (headless=False 로 시각적 확인 가능)
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # 브라우저 상태 로드 (로그인 유지)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        # 저장된 세션 상태 로드 (있는 경우)
        if os.path.exists(BROWSER_STATE_PATH):
            await context.storage_state(path=BROWSER_STATE_PATH)
        
        page = await context.new_page()
        
        try:
            # 1. 네이버 로그인 체크
            print("1. 네이버 로그인 확인 중...")
            await check_and_login_naver(page)
            
            # 2. 블로그 글쓰기 페이지로 이동
            print("2. 블로그 글쓰기 페이지로 이동 중...")
            # 사용자의 네이버 블로그 ID 필요 - 환경 변수에서 읽거나 입력받기
            naver_id = NAVER_ID or "your_naver_id"  # 실제 ID 로 변경 필요
            await page.goto(f"https://blog.naver.com/{naver_id}/postwrite")
            await page.wait_for_timeout(2000)
            
            # 3. 제목 입력
            print("3. 제목 입력 중...")
            await fill_title(page, topic)
            await page.wait_for_timeout(1000)
            
            # 4. 본문 입력
            print("4. 본문 입력 중...")
            await fill_content(page, content)
            await page.wait_for_timeout(1000)
            
            # 5. 이미지 업로드 (있는 경우)
            if image_path and os.path.exists(image_path):
                print("5. 이미지 업로드 중...")
                await upload_image(page, image_path)
                await page.wait_for_timeout(2000)
            
            # 6. 발행 버튼 클릭
            print("6. 발행 중...")
            await publish_post(page)
            
            # 성공 URL 확인
            current_url = page.url
            print(f"포스팅 완료! URL: {current_url}")
            
            return {
                "status": "success",
                "url": current_url,
                "message": "네이버 블로그에 성공적으로 포스팅되었습니다."
            }
            
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "url": None
            }
        finally:
            # 브라우저 상태 저장 (로그인 정보 유지)
            try:
                await context.storage_state(path=BROWSER_STATE_PATH)
            except:
                pass
            await browser.close()


async def check_and_login_naver(page):
    """네이버 로그인 확인 및 로그인"""
    # 네이버 로그인 페이지로 이동
    await page.goto("https://nid.naver.com/nidlogin.login")
    await page.wait_for_timeout(2000)
    
    # 로그인 폼 확인
    if await page.is_visible("#id"):
        print("로그인 필요 - 로그인 진행 중...")
        
        # 아이디 입력
        await page.fill("#id", NAVER_ID)
        await page.wait_for_timeout(500)
        
        # 비밀번호 입력
        await page.fill("#pw", NAVER_PASSWORD)
        await page.wait_for_timeout(500)
        
        # 로그인 버튼 클릭
        await page.click("#loginButton")
        await page.wait_for_timeout(3000)
    else:
        print("이미 로그인 상태입니다.")


async def fill_title(page, topic: str):
    """블로그 제목 입력"""
    # 네이버 블로그 에디터 제목 필드
    # 최신 네이버 블로그는 contenteditable div 사용
    title_selectors = [
        'input[placeholder="제목입력"]',
        'input[name="subject"]',
        '.se-input-control',
        '[contenteditable="true"]'
    ]
    
    for selector in title_selectors:
        try:
            if await page.is_visible(selector, timeout=2000):
                await page.fill(selector, topic)
                print(f"제목 입력 완료: {selector}")
                return
        except:
            continue
    
    # 기본 fallback: 첫 번째 contenteditable 찾기
    try:
        title_element = page.locator('[contenteditable="true"]').first
        if await title_element.count() > 0:
            await title_element.fill(topic)
            print("제목 입력 완료 (fallback)")
    except Exception as e:
        print(f"제목 입력 실패: {e}")


async def fill_content(page, content: str):
    """블로그 본문 입력 - 네이버 스마트 에디터"""
    # 네이버 스마트 에디터는 iframe 내부에 있을 수 있음
    try:
        # 에디터 iframe 찾기
        editor_frame = page.frame_locator("iframe.se_iframe")
        
        # 에디터 콘텐츠 영역 찾기
        content_selectors = [
            '.se-editarea',
            '[data-testid="editor"]',
            '.se-component.se-editarea',
            '[contenteditable="true"]'
        ]
        
        for selector in content_selectors:
            try:
                if await editor_frame.locator(selector).count() > 0:
                    await editor_frame.locator(selector).first.fill(content)
                    print("본문 입력 완료 (iframe)")
                    return
            except:
                continue
    except:
        pass
    
    # iframe 없이 직접 찾기
    try:
        content_selectors = [
            '.se-editarea',
            '[data-testid="editor"]',
            '.se-component.se-editarea',
            '[contenteditable="true"]'
        ]
        
        for selector in content_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    element = page.locator(selector)
                    if await element.count() > 0:
                        await element.first.fill(content)
                        print(f"본문 입력 완료: {selector}")
                        return
            except:
                continue
    except Exception as e:
        print(f"본문 입력 실패: {e}")


async def upload_image(page, image_path: str):
    """블로그에 이미지 업로드"""
    try:
        # 이미지 업로드 버튼 찾기
        upload_button_selectors = [
            'button[title="사진추가"]',
            '.se-button-icon',
            '[data-component-type="image"]',
            'button:has-text("사진")'
        ]
        
        for selector in upload_button_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    await page.click(selector)
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue
        
        # 파일 업로드 다이얼로그 처리
        # Playwright 는 파일 선택 다이얼로그를 직접 처리할 수 있음
        file_input = page.locator('input[type="file"]')
        if await file_input.count() > 0:
            await file_input.first.set_input_files(image_path)
            print(f"이미지 업로드 완료: {image_path}")
            await page.wait_for_timeout(3000)  # 업로드 완료 대기
            
    except Exception as e:
        print(f"이미지 업로드 실패: {e}")


async def publish_post(page):
    """블로그 게시글 발행"""
    try:
        # 발행 버튼 찾기
        publish_button_selectors = [
            'button.btn_publish',
            'button:has-text("발행")',
            'button:has-text("등록")',
            '.se-button-primary'
        ]
        
        for selector in publish_button_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    await page.click(selector)
                    print("발행 버튼 클릭 완료")
                    await page.wait_for_timeout(3000)  # 발행 완료 대기
                    return
            except:
                continue
        
        print("발행 버튼을 찾을 수 없습니다.")
        
    except Exception as e:
        print(f"발행 실패: {e}")
