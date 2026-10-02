from pathlib import Path
import hashlib
import json
import zipfile
import pytest


def test_resource_catalog_accounts_for_list_and_exports_original_source(tmp_path):
    from teach_agent.experiments import ExperimentLibrary
    library=ExperimentLibrary()
    items=library.search('')
    assert len(items)==32
    optics=next(item for item in library.search('光学') if item['id']=='ricktu288--ray-optics')
    assert optics['license']=='Apache-2.0' and optics['status']=='source_archive'
    exported=library.export(optics['id'],tmp_path)
    with zipfile.ZipFile(exported['path']) as archive:
        assert any(name.endswith('/src/core/Editor.js') for name in archive.namelist())
        assert any('LICENSE' in name for name in archive.namelist())
    with pytest.raises(ValueError):library.export('HackerYard--openlabs',tmp_path)
    with pytest.raises(ValueError):library.export('../../config',tmp_path)


def test_all_bundled_archives_match_their_recorded_sources():
    from teach_agent.experiments import ExperimentLibrary
    library=ExperimentLibrary()
    for item in library.entries:
        if item['status']!='source_archive':continue
        path=library.root/item['archive']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        assert len(item['commit'])==40
        assert item['license_files']
        assert all((library.root/p).is_file() for p in item['license_files'])


def test_interaction_rules_are_used_by_both_generation_and_review():
    from teach_agent.prompts import BUILD_SYSTEM, REVIEW_SYSTEM
    from teach_agent.materials import Materials
    assert 'TeachInteraction' in BUILD_SYSTEM
    assert '拖动' in REVIEW_SYSTEM and '复位' in REVIEW_SYSTEM
    page=Materials().expand('<html><head><!--TEACH_INTERACTION--></head><body></body></html>',[])
    assert '<!--TEACH_INTERACTION-->' not in page
    assert 'setPointerCapture' in page and 'requestAnimationFrame' in page


def test_export_carries_supplemental_gpl_notice(tmp_path):
    from teach_agent.experiments import ExperimentLibrary
    result=ExperimentLibrary().export('pfalstad--ripplegl',tmp_path)
    with zipfile.ZipFile(result['path']) as archive:
        assert b'GNU GENERAL PUBLIC LICENSE' in archive.read('TEACH_AGENT_RESOURCE_NOTICES/GPL-2.0.txt')
        assert b'GNU General Public License' in archive.read('TEACH_AGENT_RESOURCE_NOTICES/SOURCE-NOTICE.txt')


def test_web_downloads_include_all_supplemental_notices():
    from teach_agent.experiments import ExperimentLibrary
    library=ExperimentLibrary()
    page=(library.root/'index.html').read_text(encoding='utf-8')
    for item in library.entries:
        if item['status']=='reference_only':
            assert '保存完整源码快照' not in item['setup']
            continue
        if item['id']=='pfalstad--ripplegl' or item['id'].startswith('virtual-labs--'):
            path=library.root/item['download']
            assert f'href="{item["download"]}"' in page
            assert hashlib.sha256(path.read_bytes()).hexdigest()==item['download_sha256']
            with zipfile.ZipFile(path) as archive:
                for notice in item['license_files']:
                    assert archive.read('TEACH_AGENT_RESOURCE_NOTICES/'+Path(notice).name)==(library.root/notice).read_bytes()


@pytest.mark.asyncio
async def test_dragging_scaled_svg_snap_bounds_cancel_keyboard_and_frame(tmp_path):
    # An authored isolated file fixture; never visits the user's workbench/browser.
    from playwright.async_api import async_playwright
    from teach_agent.materials import Materials
    page_source='''<html><head><!--TEACH_INTERACTION--></head><body>
    <svg id="surface" width="600" height="400" viewBox="0 0 300 200"><rect id="object" width="20" height="20" fill="green"/></svg>
    <script>window.position={x:40,y:40};window.commits=0;
    const obj=document.querySelector('#object');
    window.write=p=>{position=p;obj.setAttribute('x',p.x);obj.setAttribute('y',p.y);};write(position);
    window.drag=TeachInteraction.drag(obj,{surface:document.querySelector('#surface'),read:()=>position,write,
      bounds:()=>({minX:0,minY:0,maxX:280,maxY:180}),snap:[{x:100,y:80}],radius:8,onCommit:()=>commits++});
    </script></body></html>'''
    path=tmp_path/'fixture.html'
    path.write_text(Materials().expand(page_source,[]),encoding='utf-8')
    executable=next((p for p in ('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
                                'C:/Program Files/Google/Chrome/Application/chrome.exe') if Path(p).is_file()),None)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,executable_path=executable)
        try:
            page=await browser.new_page()
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            await page.route('**/*',lambda route:route.continue_() if route.request.url==path.resolve().as_uri() else route.abort())
            await page.goto(path.resolve().as_uri())
            box=await page.locator('#surface').bounding_box()
            async def pointer(x,y):await page.mouse.move(box['x']+x*2,box['y']+y*2)
            await pointer(45,45);await page.mouse.down()
            assert await page.evaluate('position')=={'x':40,'y':40}  # no initial jump
            await pointer(101,82);await page.mouse.up()
            assert await page.evaluate('position')=={'x':100,'y':80}  # offset retained, snap near only
            await pointer(105,85);await page.mouse.down();await pointer(210,150);await page.keyboard.press('Escape');await page.mouse.up()
            assert await page.evaluate('position')=={'x':100,'y':80}
            await page.locator('#object').press('ArrowRight')
            assert await page.evaluate('position.x')==101
            await pointer(106,85);await page.mouse.down();await pointer(500,300);await page.mouse.up()
            assert await page.evaluate('position')=={'x':280,'y':180}
            assert await page.evaluate('commits')==3
            # Deterministic scheduler to verify coalescing, catch-up limit and reset.
            result=await page.evaluate('''() => {
              const savedRAF=window.requestAnimationFrame,savedCancel=window.cancelAnimationFrame;
              let tasks=new Map(),id=0;
              window.requestAnimationFrame=fn=>{tasks.set(++id,fn);return id;};
              window.cancelAnimationFrame=id=>tasks.delete(id);
              const advance=t=>{const pending=[...tasks.values()];tasks.clear();pending.forEach(fn=>fn(t));};
              try {
                let values=[];const draw=TeachInteraction.frame(v=>values.push(v));draw(1);draw(2);draw(3);advance(0);
                draw(4);draw.cancel();advance(1);
                let steps=0;const sim=TeachInteraction.simulation({update:()=>steps++,render:()=>{},dt:.01,maxSteps:4});
                sim.start();advance(0);advance(10000);const bounded=steps;sim.pause();advance(20000);
                const paused=steps;sim.reset(()=>steps=0);const reset=steps;sim.destroy();drag.destroy();
                return {values,bounded,paused,reset,remaining:tasks.size,tab:obj.getAttribute('tabindex')};
              } finally {window.requestAnimationFrame=savedRAF;window.cancelAnimationFrame=savedCancel;}
            }''')
            assert result=={'values':[3],'bounded':3,'paused':3,'reset':0,'remaining':0,'tab':None} or result=={'values':[3],'bounded':4,'paused':4,'reset':0,'remaining':0,'tab':None}
            assert not errors
        finally:
            await browser.close()
