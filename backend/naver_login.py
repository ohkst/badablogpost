import asyncio
from playwright.async_api import async_playwright
import os

async def login_and_save_state():
    print("🚀 네이버 자동 로그인 스크립트를 시작합니다...")
    print("브라우저 창이 열리면 직접 로그인을 진행해주세요.")
    
    async with async_playwright() as p:
        # headless=False 로 설정하여 브라우저 창을 띄움
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.goto("https://nid.naver.com/nidlogin.login")
        
        print("⏳ 로그인 완료를 기다리는 중입니다...")
        print("직접 아이디와 비밀번호를 입력하고 로그인(필요 시 2단계 인증 포함)을 완료해주세요.")
        
        # 로그인 완료 후 쿠키에 NID_SES가 생길 때까지 주기적으로 체크
        try:
            while True:
                cookies = await context.cookies()
                has_nid_ses = any(c['name'] == 'NID_SES' for c in cookies)
                has_nid_aut = any(c['name'] == 'NID_AUT' for c in cookies)
                
                if has_nid_ses and has_nid_aut:
                    print("✅ 네이버 로그인이 감지되었습니다!")
                    break
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"오류 발생: {e}")
            
        # 로그인 직후 쿠키 세팅을 위해 잠시 대기
        await page.wait_for_timeout(2000)
        
        # 쿠키 및 로컬 스토리지 상태 저장
        state_path = os.path.join(os.path.dirname(__file__), "naver_state.json")
        await context.storage_state(path=state_path)
        
        print(f"🎉 인증 상태(쿠키)가 성공적으로 저장되었습니다: {state_path}")
        print("이제 백엔드가 이 파일을 읽어 자동으로 포스팅을 진행합니다.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_and_save_state())
