"""Controlled Manim rendering; video inspection adapted from the user's existing toolkit."""
import asyncio
import html
import json
import math
import os
import shutil
from pathlib import Path
import av


def validate_params(value):
    if not isinstance(value,dict) or value.get('template','force_composition') != 'force_composition':
        raise ValueError('当前仅支持两力合成受控动画模板')
    result={'template':'force_composition'}
    for key,default,low,high in [('force1',3,.1,10),('force2',4,.1,10),('angle',60,0,180),('hold',2,1,5)]:
        try:
            number=float(value.get(key,default))
        except (ValueError,TypeError) as error:
            raise ValueError('动画参数必须是数值') from error
        if not math.isfinite(number) or not low<=number<=high:
            raise ValueError(f'{key} 超出范围 {low}–{high}')
        result[key]=number
    return result


def inspect_video(path):
    try:
        with av.open(str(path)) as container:
            if not container.streams.video:
                raise ValueError('文件没有视频画面')
            stream=container.streams.video[0]
            frame=next(container.decode(stream),None)
            duration=(float(stream.duration*stream.time_base) if stream.duration is not None and stream.time_base
                      else (container.duration or 0)/av.time_base)
            if frame is None or duration<=0 or stream.codec_context.name!='h264':
                raise ValueError('需要可播放的 H.264 MP4 视频')
            return dict(duration=round(duration,3),width=stream.width,height=stream.height,
                        codec=stream.codec_context.name,pixel_format=frame.format.name)
    except av.FFmpegError as error:
        raise ValueError('无法解码这个视频') from error


def video_page(title):
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>教学动画</title><style>body{font-family:system-ui,sans-serif;background:#f3f6f5;color:#173630;margin:0;padding:4vw}main{max-width:1100px;margin:auto}video{width:100%;background:#101c22;border-radius:16px}p{line-height:1.7}h1{font-size:28px}</style></head><body><main><h1>'''+html.escape(title)+'''</h1><video controls playsinline preload="metadata" src="assets/clip.mp4"></video><p>可暂停、拖动进度或全屏播放。视频和本页均保存在本地。</p></main></body></html>'''


async def render_animation(plan,folder,python_path):
    params=validate_params(plan.get('animation'))
    executable=Path(python_path)
    if not python_path or not executable.is_file():
        raise ValueError('请在设置中选择已安装 Manim 的 Python；互动演示不需要此设置')
    params['title']=plan['title'][:38]
    parameters=folder/'animation-parameters.json'
    parameters.write_text(json.dumps(params,ensure_ascii=False),encoding='utf-8')
    template=Path(__file__).parent/'animation_templates/force_composition.py'
    env=os.environ.copy()
    # No model keys are passed to the rendering subprocess.
    for key in list(env):
        if any(word in key.upper() for word in ('API_KEY','TOKEN','SECRET','PASSWORD')):
            env.pop(key,None)
    env['TEACH_SCENE_PARAMS']=str(parameters.resolve())
    process=await asyncio.create_subprocess_exec(str(executable),'-m','manim','-qm','--disable_caching',
        '--media_dir',str((folder/'render').resolve()),'-o','clip',str(template.resolve()),'ForceComposition',
        cwd=str(folder.resolve()),env=env,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
    try:
        output,_=await asyncio.wait_for(process.communicate(),180)
    except (asyncio.CancelledError,TimeoutError):
        if process.returncode is None:
            process.kill()
            await process.wait()
        raise
    (folder/'render.log').write_bytes(output[-100000:])
    if process.returncode:
        raise ValueError('Manim 渲染失败，请检查环境；渲染日志已保存在本地作品目录')
    clips=list((folder/'render').rglob('clip.mp4'))
    if len(clips)!=1:
        raise ValueError('Manim 未生成预期视频')
    (folder/'assets').mkdir(exist_ok=True)
    destination=folder/'assets/clip.mp4'
    shutil.copyfile(clips[0],destination)
    metadata=await asyncio.to_thread(inspect_video,destination)
    (folder/'index.html').write_text(video_page(plan['title']),encoding='utf-8')
    return dict(passed=True,video=metadata,template='force_composition',parameters=params,
                browser_checked=False,scientific_correctness='受控两力合成模板；仍需老师预览确认',cross_computer_tested=False)
