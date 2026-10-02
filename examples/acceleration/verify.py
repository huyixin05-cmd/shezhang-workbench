"""Exercise the authored offline lesson in an isolated browser, with network blocked."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright,expect
from build import build


async def main():
    path=build()
    executable=next((p for p in ('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                                'C:/Program Files/Google/Chrome/Application/chrome.exe') if Path(p).is_file()),None)
    errors=[];blocked=[]
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,executable_path=executable)
        try:
            page=await browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
            page.on('pageerror',lambda e:errors.append(str(e)))
            async def guard(route):
                if route.request.url==path.resolve().as_uri():await route.continue_()
                else:blocked.append(route.request.url);await route.abort()
            await page.route('**/*',guard)
            await page.goto(path.resolve().as_uri());await page.evaluate('document.fonts.ready')
            async def set_range(selector,value):
                await page.locator(selector).evaluate('(el,v)=>{el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}));}',str(value))
                await page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            await expect(page.locator('#fa')).to_be_disabled()
            await expect(page.locator('#mb')).to_be_disabled()
            await expect(page.locator('#finding')).to_be_hidden()
            await expect(page.locator('#explain')).to_be_disabled()
            await page.screenshot(path=str(path.parent/'初始界面.png'),full_page=True)
            await page.locator('[data-prediction="b"]').click()
            await page.locator('#play').click()
            await page.wait_for_function('() => Number(document.querySelector("#clock").textContent)>.2')
            await page.locator('#play').click()
            paused=await page.locator('#clock').inner_text()
            await page.wait_for_timeout(150)
            assert paused==await page.locator('#clock').inner_text()
            await set_range('#timeline',1)
            await expect(page.locator('#velocity-a')).to_contain_text('1.00')
            await expect(page.locator('#velocity-b')).to_contain_text('2.00')
            await expect(page.locator('#distance-a')).to_contain_text('0.50')
            await expect(page.locator('#distance-b')).to_contain_text('1.00')
            await page.locator('#explain').click()
            await expect(page.locator('#prediction-note')).to_contain_text('一致')
            await expect(page.locator('#equation .katex')).to_have_count(1)
            await set_range('#timeline',2)
            await page.screenshot(path=str(path.parent/'实验结果.png'),full_page=True)
            await page.locator('[data-mode="mass"]').click()
            await expect(page.locator('#finding')).to_be_hidden()
            await expect(page.locator('#fb')).to_be_disabled()
            await expect(page.locator('#mb')).to_be_enabled()
            await set_range('#timeline',1)
            await expect(page.locator('#velocity-a')).to_contain_text('4.00')
            await expect(page.locator('#velocity-b')).to_contain_text('2.00')
            await page.locator('#mb').press('End')
            await expect(page.locator('#clock')).to_have_text('0.00')
            await expect(page.locator('#mb-value')).to_have_text('4 kg')
            await set_range('#timeline',1)
            await expect(page.locator('#velocity-b')).to_contain_text('1.00')
            await page.locator('[data-mode="free"]').click()
            await set_range('#fa',0);await set_range('#fb',0);await set_range('#v0',3)
            await set_range('#timeline',2)
            await expect(page.locator('#velocity-a')).to_contain_text('3.00')
            await expect(page.locator('#distance-a')).to_contain_text('6.00')
            await page.locator('#explain').click()
            await expect(page.locator('#finding-text')).to_contain_text('加速度都为零')
            await page.locator('[data-mode="quiz"]').click()
            await page.locator('#check-quiz').click()
            await expect(page.locator('#quiz-score')).to_contain_text('还有问题没有选择')
            for i,value in enumerate([0,1,2]):await page.locator(f'input[name=q{i}][value="{value}"]').check()
            await page.locator('#check-quiz').click()
            await expect(page.locator('#quiz-score')).to_have_text('答对 3/3 题')
            await expect(page.locator('#final-equation .katex')).to_have_count(1)
            await page.locator('input[name=q2][value="0"]').check()
            await page.locator('#check-quiz').click()
            await expect(page.locator('#feedback-2')).to_contain_text('加速度为零')
            await page.locator('#reset-all').click()
            await expect(page.locator('#clock')).to_have_text('0.00')
            await expect(page.locator('#play')).to_have_text('▶ 同时出发')
            await expect(page.locator('#finding')).to_be_hidden()
            assert await page.locator('#quiz input:checked').count()==0
            if (path.parent/'加速度的影响因素-讲解.mp4').exists():
                await page.locator('#watch-video').click()
                await page.wait_for_function('() => {const v=document.querySelector("#lesson-video");return v.readyState>=2&&v.currentTime>.1;}',timeout=15000)
                media=await page.locator('#lesson-video').evaluate('(v)=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,src:v.currentSrc})')
                assert 90<media['duration']<100 and media['width']==1280 and media['height']==720,media
                assert media['src'].startswith('blob:'),media
                await page.screenshot(path=str(path.parent/'视频入口.png'),full_page=False)
                await page.locator('#close-video').click()
                assert await page.locator('#lesson-video').evaluate('(v)=>v.paused')
            for width in [1280,768,390]:
                await page.set_viewport_size({'width':width,'height':900})
                assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),width
            await page.screenshot(path=str(path.parent/'手机界面.png'),full_page=True)
            assert not errors,errors
            assert not blocked,blocked
            report={'passed':True,'checked':['离线无外部请求','实际播放与暂停','同质量改变合力','同合力改变质量','初速度非零且合力为零','时间回看','预测与解释','KaTeX公式','三题判分与解释','完整复位','1280/768/390宽度无横向溢出'],
                    'errors':errors,'external_requests':blocked,'note':'对当前手工制作成品的验证，不代表自动生成工作流或所有课题质量已验收。'}
            (path.parent/'检查报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(report,ensure_ascii=False))
        finally:await browser.close()


if __name__=='__main__':asyncio.run(main())
