"""Isolated browser checks for generated pages; never attaches to a user's browser."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def check_page(path, steps):
    if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
        return dict(passed=False, errors=['必须提供 1–8 个可执行交互检查'], browser_checked=False)
    errors = []
    async with async_playwright() as pw:
        executable = None
        for candidate in ('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                          'C:/Program Files/Google/Chrome/Application/chrome.exe'):
            if Path(candidate).is_file():
                executable = candidate
                break
        browser = await pw.chromium.launch(headless=True, executable_path=executable)
        try:
            context = await browser.new_context(viewport={'width':1280,'height':800}, service_workers='block',
                                                accept_downloads=False)
            uri = path.resolve().as_uri()
            video_path=path.parent/'assets/clip.mp4'
            video_uri=video_path.resolve().as_uri() if video_path.is_file() else None
            async def guard(route):
                if (route.request.url == uri and route.request.is_navigation_request()) or (route.request.url==video_uri and route.request.resource_type=='media'):
                    await route.continue_()
                else:
                    await route.abort()
            await context.route('**/*', guard)
            page = await context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)[:500]))
            page.on('console', lambda msg: errors.append(msg.text[:500]) if msg.type == 'error' else None)
            page.set_default_timeout(4000)
            await page.goto(uri, wait_until='load', timeout=20000)
            await page.evaluate('document.fonts.ready')
            if await page.locator('video').count():
                await page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>v.readyState>=2 && Number.isFinite(v.duration) && v.duration>0)",timeout=15000)
            for step in steps:
                if step.get('action') not in ('click','fill','check','select'):
                    raise ValueError('不支持的交互检查动作')
                selector = step.get('selector','')
                if not selector or len(selector) > 250:
                    raise ValueError('无效的交互检查选择器')
                element = page.locator(selector)
                action = step['action']
                if action == 'click':
                    await element.click()
                elif action == 'fill':
                    await element.fill(str(step.get('value','')))
                elif action == 'select':
                    await element.select_option(str(step.get('value','')))
                else:
                    await element.check()
                from playwright.async_api import expect
                if not step.get('expect_selector') or not str(step.get('expect_text','')).strip():
                    raise ValueError('检查必须包含结果元素和期望文字')
                await expect(page.locator(step['expect_selector'])).to_contain_text(str(step['expect_text']))
            for width in (1280,390):
                await page.set_viewport_size({'width':width,'height':800})
                overflow = await page.evaluate('document.documentElement.scrollWidth > innerWidth + 4')
                if overflow:
                    errors.append(f'{width}px 视口出现整页横向溢出')
            await page.set_viewport_size({'width':1280,'height':800})
            await page.screenshot(path=str(path.parent / 'preview.png'))
        except asyncio.CancelledError:
            raise
        except Exception as error:
            errors.append(str(error)[:600])
        finally:
            await browser.close()
    return dict(passed=not errors, errors=errors[:12], steps=len(steps), browser_checked=True,
                scientific_correctness='自动检查不能替代学科审核', cross_computer_tested=False)
