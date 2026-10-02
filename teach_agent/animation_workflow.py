"""Async boundary around the program-owned animation worker."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import sys
import time
import subprocess
from urllib.parse import urlsplit
from .process_tree import ProcessTree

from .animation_contract import validate_animation

ROOT = Path(__file__).parent


def owned_file(root, relative):
    root=Path(root).resolve();relative=Path(relative)
    if relative.is_absolute():
        raise ValueError('动画结果路径必须相对于作品目录')
    path=root/relative
    resolved=path.resolve()
    if not resolved.is_relative_to(root) or not path.is_file() or path.is_symlink():
        raise ValueError('动画结果文件不存在或越出作品目录')
    return resolved


def validate_visual_review(review, root, frames):
    if not isinstance(review,dict) or review.get('status')!='approved' or review.get('defects')!=[]:
        raise ValueError('画面检查未通过：'+str(review.get('defects','无有效复核结果') if isinstance(review,dict) else review)[:1200])
    evidence=review.get('evidence')
    if not isinstance(evidence,list) or not evidence or not isinstance(review.get('observations'),list) or not review['observations']:
        raise ValueError('画面检查缺少实际抽帧证据或观察记录')
    inspected={owned_file(root,path) for path in evidence if isinstance(path,str)}
    if not {Path(p).resolve() for p in frames}.issubset(inspected):
        raise ValueError('画面检查没有覆盖本次渲染的全部代表帧')
    return review


def workflow_configuration(config):
    python=Path(config.get('manim_python',''))
    if not config.get('manim_python') or not python.is_file():
        raise ValueError('请在设置中选择已有 Manim 环境的 Python')
    if not config.get('base_url') or not config.get('model'):
        raise ValueError('请先在设置中填写模型地址和模型名；动画使用同一模型，需要支持图片输入和代码生成')
    url=urlsplit(config['base_url'])
    if url.username or url.password or url.query or url.fragment or not url.hostname or (
        url.scheme!='https' and not (url.scheme=='http' and url.hostname in ('localhost','127.0.0.1','::1'))):
        raise ValueError('模型地址须为 HTTPS 或本机 HTTP，不能含账号或查询参数')
    result={key:config[key] for key in ('base_url','model','api_key','max_tokens') if key in config}
    result['manim_python']=str(python.resolve())
    if len(json.dumps(result).encode('utf-8'))>24000:raise ValueError('模型配置过长，请检查设置')
    return result


def clean_environment():
    env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY','TOKEN','SECRET','PASSWORD'))}
    env['PYTHONUTF8']='1'
    # Import the installed workbench, never a generated module from the render folder.
    env['PYTHONPATH']=str(ROOT.parent)
    return env


async def run_animation_workflow(plan, folder, config, progress, previous=None, changes=None):
    validate_animation(plan.get('animation'),allow_legacy=False)
    runtime=workflow_configuration(config)
    folder=Path(folder).resolve();work=folder/'animation';work.mkdir()
    (work/'approved_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    if previous:
        # Only copy approved scene/artifacts, never old videos or stage records that could pass as new output.
        for name in ['sol_scene.py','05_shot_list.json','06_scene_spec.json']:
            source=Path(previous)/'animation'/name
            if source.is_file() and not source.is_symlink():
                shutil.copyfile(source,work/('previous_'+name))
    request=dict(**runtime,changes=changes)
    payload=json.dumps(request,ensure_ascii=False).encode('utf-8')
    if len(payload)>32768:raise ValueError('动画请求过长，请缩短修改要求')
    log=work/'worker.log'
    with log.open('wb') as output:
        tree=ProcessTree([sys.executable,'-m','teach_agent.animation_worker',str(work)],
            cwd=str(ROOT.parent),env=clean_environment(),stdin=subprocess.PIPE,stdout=output,stderr=output)
        process=tree.process
        started=time.monotonic();last=None
        try:
            # Credentials travel only through a private pipe, never files/arguments/environment.
            process.stdin.write(payload);process.stdin.close()
            while process.poll() is None:
                if time.monotonic()-started>3600:raise ValueError('动画制作超时，已保留草稿和日志')
                status=work/'progress.json'
                if status.is_file():
                    try:
                        message=json.loads(status.read_text(encoding='utf-8')).get('stage')
                        if isinstance(message,str) and message!=last:
                            progress(message[:160]);last=message
                    except (ValueError,OSError):pass
                await asyncio.sleep(.3)
        finally:
            tree.close()
    result_path=work/'worker-result.json'
    result=json.loads(result_path.read_text(encoding='utf-8')) if result_path.is_file() else {}
    if process.returncode or result.get('passed') is not True:
        raise ValueError(result.get('error','动画工作流失败，已保留草稿和日志')[:1200])
    video=owned_file(work,result.get('video_path',''))
    frames=[owned_file(work,p) for p in result.get('frames',[])]
    if not frames:raise ValueError('动画缺少本次渲染的检查帧')
    validate_visual_review(result.get('visual_review'),work,frames)
    from .animation import inspect_video,video_page
    metadata=inspect_video(video)
    (folder/'assets').mkdir(exist_ok=True);shutil.copyfile(video,folder/'assets/clip.mp4')
    (folder/'index.html').write_text(video_page(plan['title']),encoding='utf-8')
    source=dict(animation=plan['animation'],scene=owned_file(work,'sol_scene.py').read_text(encoding='utf-8'))
    report=dict(result,video=metadata,workflow='manim',browser_checked=False,
                scientific_correctness='生成场景与抽帧经过模型复核；教学效果仍需老师预览')
    return source,report
