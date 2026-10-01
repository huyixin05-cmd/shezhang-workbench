"""Render arbitrary validated scenes with the existing Manim Python; extract evidence with PyAV."""
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import av
from .animation import inspect_video
from .process_tree import ProcessTree


def inspect_source(source):
    try: tree=ast.parse(source)
    except SyntaxError as error: raise ValueError('场景 Python 语法错误：'+str(error)) from error
    allowed={'manim','math','numpy','random','video_guard'}
    blocked={'open','eval','exec','compile','__import__','getattr','setattr','delattr','globals','locals','vars','input',
             'os','sys','subprocess','socket','ctypes','ctypeslib','builtins','load','save','savez','savez_compressed',
             'fromfile','tofile','dump','dumps','loadtxt','savetxt','genfromtxt','memmap','write','read','unlink','remove',
             'config','tempconfig','load_library','CDLL','PyDLL','WinDLL','windll','system','popen'}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            if any(a.name not in allowed for a in node.names):raise ValueError('场景包含不允许的模块')
        if isinstance(node,ast.ImportFrom):
            if node.level or node.module not in allowed or any(a.name in blocked or a.name.startswith('__') for a in node.names):
                raise ValueError('场景包含不允许的模块或成员')
        if isinstance(node,ast.Name) and (node.id in blocked or node.id.startswith('__')):
            raise ValueError('场景包含不允许的系统名称或渲染设置')
        if isinstance(node,ast.Attribute) and (node.attr.startswith('__') or node.attr in blocked):
            raise ValueError('场景包含不允许的系统或文件操作')
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in blocked:
            raise ValueError('场景包含不允许的动态调用')
    return tree


def extract_frames(video, folder, count=6, shots=None):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    metadata=inspect_video(video);duration=metadata['duration'];frames=[];records=[]
    # Reopen per seek: decoder buffers cannot contaminate the next checkpoint.
    times=[duration*(.08+.86*i/(count-1)) for i in range(count)]
    if shots:
        times=[];start=0;total=sum(s['seconds'] for s in shots)
        for shot in shots:
            times.extend((start+shot['seconds']*fraction)*duration/total for fraction in (.25,.75))
            start+=shot['seconds']
    for i,timestamp in enumerate(times):
        with av.open(str(video)) as container:
            stream=container.streams.video[0]
            container.seek(int(timestamp/stream.time_base),stream=stream)
            chosen=None
            for frame in container.decode(stream):
                chosen=frame
                if frame.time is not None and frame.time>=timestamp:break
            if chosen is None:raise ValueError('无法读取动画检查帧')
            small=chosen.reformat(width=64,height=36,format='gray')
            plane=small.planes[0];raw=bytes(plane)
            gray=b''.join(raw[row*plane.line_size:row*plane.line_size+64] for row in range(36))
            if max(gray)-min(gray)<8:raise ValueError(f'第 {timestamp:.1f} 秒画面为空白')
            frame=chosen.reformat(format='rgb24')
            codec=av.CodecContext.create('png','w');codec.width=frame.width;codec.height=frame.height;codec.pix_fmt='rgb24'
            path=folder/f'frame_{i+1:02d}.png'
            packets=codec.encode(frame)+codec.encode(None)
            path.write_bytes(b''.join(bytes(packet) for packet in packets))
            frames.append(path);records.append(dict(file=path.name,seconds=round(timestamp,3)))
    (folder/'timestamps.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    return frames


def render_scene(work, python, scene_name, quality, brief, attempt):
    work=Path(work).resolve()
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',scene_name):raise ValueError('动画场景名称无效')
    source=(work/'sol_scene.py').read_text(encoding='utf-8');inspect_source(source)
    vertical=brief['aspect_ratio']=='9:16'
    resolution=('480,854' if vertical else '854,480') if quality=='l' else ('720,1280' if vertical else '1280,720')
    name=f'{"preview" if quality=="l" else "final"}-{attempt}'
    output=work/name;output.mkdir(exist_ok=False)
    env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY','TOKEN','SECRET','PASSWORD'))}
    env.pop('PYTHONPATH',None);env['PYTHONUTF8']='1'
    config_file=output/'render.cfg'
    config_file.write_text('[CLI]\nframe_width = '+('4.5' if vertical else '14.2222222222')+'\nframe_height = 8\n',encoding='utf-8')
    command=[python,'-m','manim','-q'+quality,'-r',resolution,'--disable_caching','--progress_bar','none',
             '--config_file',str(config_file),'--media_dir',str(output),'sol_scene.py',scene_name]
    with ProcessTree(command,cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace') as process:
        stdout,stderr=process.communicate(timeout=600)
        returncode=process.returncode
    log=stdout+'\n'+stderr
    (output/'render.log').write_text(log,encoding='utf-8')
    if returncode:raise ValueError('Manim 渲染错误：'+log[-4500:])
    if re.search(r'\[layout\].*WARN',log):raise ValueError('画面布局检查发现越界或文字重叠：'+log[-3000:])
    candidates=[p for p in output.rglob('*.mp4') if 'partial_movie_files' not in p.parts]
    if len(candidates)!=1:raise ValueError('渲染未产生唯一新成片')
    video=candidates[0];metadata=inspect_video(video)
    if video.is_symlink() or not video.resolve().is_relative_to(output):raise ValueError('视频路径越出渲染目录')
    if abs(metadata['duration']-brief['duration_seconds'])>max(2,brief['duration_seconds']*.2):
        raise ValueError(f"实际时长 {metadata['duration']} 秒与分镜目标 {brief['duration_seconds']} 秒差异过大")
    ratio=9/16 if vertical else 16/9
    if abs(metadata['width']/metadata['height']-ratio)>.03:raise ValueError('动画画幅与已确认方案不符')
    frames=extract_frames(video,work/'review_frames'/name,shots=brief['shots'])
    return video,frames,metadata
