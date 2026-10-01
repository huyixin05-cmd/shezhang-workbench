"""Import a chosen local video; never execute paths or code from the upload."""
import asyncio
import json
import re
import shutil
from uuid import uuid4
from .animation import inspect_video, video_page
from .artifacts import add_notices, assemble_page, notices


async def import_video(service, request, title, base=None):
    if not title.strip() or len(title)>120:
        raise ValueError('视频名称需为 1–120 字')
    if base and base['kind']!='interactive':
        raise ValueError('请在纯互动版本上加入动画；已有版本会保留')
    folder_id=uuid4().hex
    folder=service.settings.root/'artifacts'/folder_id
    (folder/'assets').mkdir(parents=True)
    path=folder/'assets/clip.mp4'
    try:
        size=0
        with path.open('wb') as stream:
            async for chunk in request.stream():
                size+=len(chunk)
                if size>200_000_000:
                    raise ValueError('首版支持导入 200 MB 以内的视频')
                stream.write(chunk)
        # MP4 container, not a renamed playlist or arbitrary FFmpeg input.
        with path.open('rb') as stream:
            if stream.read(12)[4:8]!=b'ftyp':
                raise ValueError('请选择 H.264 编码的 MP4 文件')
        metadata=await asyncio.wait_for(asyncio.to_thread(inspect_video,path),30)
        report=dict(passed=True,source='imported',video=metadata,browser_checked=False,
                    scientific_correctness='已导入的视频未做内容审核，请老师预览确认',cross_computer_tested=False)
        if base:
            previous=service.version_folder(base)
            for name in ('source.json','plan.json'):
                shutil.copyfile(previous/name,folder/name)
            page=(previous/'index.html').read_text(encoding='utf-8')
            section='<section style="max-width:1100px;margin:32px auto;padding:24px"><h2>配套教学动画</h2><video controls playsinline style="width:100%" src="assets/clip.mp4"></video></section>'
            page=re.sub(r'</body\s*>',lambda m:section+m.group(),page,count=1,flags=re.I)
            project=service.store.project(base['project_id'])
            info=dict(base,title=title,kind='combined',folder=folder_id,base_version=base['id'],
                      report=dict(base['report'],video=metadata,imported_video_review=report))
        else:
            page=add_notices(assemble_page(video_page(title)))
            project=None
            info=dict(title=title,kind='animation',folder=folder_id,plan=None,plan_revision=None,
                      base_version=None,report=report)
            (folder/'source.json').write_text(json.dumps({'imported_video':True}),encoding='utf-8')
        (folder/'index.html').write_text(page,encoding='utf-8')
        (folder/'report.json').write_text(json.dumps(info['report'],ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'THIRD_PARTY_NOTICES.txt').write_text(notices(),encoding='utf-8')
        if project is None:
            project=service.store.create_project(title,'animation')
        return dict(project=project,version=service.store.save_version(project['id'],info))
    except BaseException:
        # This UUID directory was created by this operation and contains no prior work.
        shutil.rmtree(folder)
        raise
