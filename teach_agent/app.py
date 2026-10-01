import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
from typing import Literal
from uuid import uuid4
from starlette.background import BackgroundTask
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .config import Settings
from .service import Service
from .model import Plan
from .artifacts import bundle, CSP


class NewProject(BaseModel):
    request: str = Field(min_length=1,max_length=6000)
    kind: Literal['auto','interactive','animation'] = 'auto'


class Confirmation(BaseModel):
    revision: int = Field(ge=0)


class EditPlan(BaseModel):
    revision: int = Field(ge=1)
    plan: Plan


class Rethink(BaseModel):
    revision: int = Field(ge=0)
    request: str = Field(min_length=1,max_length=6000)


class Revision(BaseModel):
    version_id: str
    request: str = Field(min_length=1,max_length=4000)


def create_app(root, model=None, checker=None):
    settings = Settings(root)
    service = Service(settings,model,checker)
    file_access = {}

    @asynccontextmanager
    async def lifespan(app):
        from .instance import instance_lock
        with instance_lock(settings.root):
            service.store.recover()
            if getattr(app.state,'server_url',None):
                (settings.root/'server.json').write_text(json.dumps({'url':app.state.server_url}),encoding='utf-8')
            try:
                yield
            finally:
                await service.close()

    app = FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    app.state.settings = settings
    app.state.service = service
    static = Path(__file__).parent / 'static'
    static.mkdir(exist_ok=True)

    @app.middleware('http')
    async def guard(request: Request, call_next):
        host = request.headers.get('host','')
        try:
            hostname = urlsplit('http://'+host).hostname
        except ValueError:
            hostname = None
        if hostname not in ('127.0.0.1','localhost','::1'):
            return JSONResponse({'detail':'仅允许本机访问'},status_code=403)
        origin = request.headers.get('origin')
        if origin is not None and origin != 'http://'+host and not request.url.path.startswith('/files/'):
            return JSONResponse({'detail':'不允许跨站访问'},status_code=403)
        if request.url.path.startswith('/api/'):
            actual = request.headers.get('authorization','')
            if not secrets.compare_digest(actual,'Bearer '+settings.token):
                return JSONResponse({'detail':'请从启动器打开工作台，或输入本机访问码'},status_code=401)
            length = request.headers.get('content-length','0')
            video_upload = request.url.path=='/api/import-video' or request.url.path.endswith('/video')
            if not length.isdigit() or int(length)>(200_000_000 if video_upload else 4_000_000):
                return JSONResponse({'detail':'请求内容过大'},status_code=413)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        if not request.url.path.endswith('/download'):
            response.headers['X-Frame-Options'] = 'DENY'
        return response

    @app.exception_handler(ValueError)
    async def bad_value(request,error):
        return JSONResponse({'detail':str(error)[:1000]},status_code=400)

    @app.exception_handler(KeyError)
    async def missing(request,error):
        return JSONResponse({'detail':'记录不存在'},status_code=404)

    @app.get('/')
    def home():
        return FileResponse(static/'index.html',headers={'Content-Security-Policy':
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; img-src 'self' data:; frame-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'"})

    app.mount('/static',StaticFiles(directory=static),name='static')

    @app.get('/api/status')
    def status():
        return dict(version='0.1.0',model=settings.public(),components=len(service.materials.items),
                    animation_templates=['force_composition'],standalone_export=True)

    @app.get('/api/settings')
    def get_settings():
        return settings.public()

    @app.put('/api/settings')
    async def put_settings(request: Request):
        data=await request.json()
        if not isinstance(data,dict):
            raise ValueError('设置必须为对象')
        return settings.save(data)

    @app.get('/api/projects')
    def projects():
        return service.store.projects()

    @app.post('/api/projects')
    async def new_project_async(body: NewProject):
        service.require_model()
        if not body.request.strip():
            raise ValueError('请先描述教学需求')
        p=service.store.create_project(body.request,body.kind)
        j=service.submit(p['id'],'plan',{'revision':0})
        return dict(project=p,job=j)

    @app.get('/api/projects/{pid}')
    def project(pid: str):
        return dict(project=service.store.project(pid),jobs=service.store.jobs(pid),versions=service.store.versions(pid))

    @app.post('/api/projects/{pid}/plan')
    def edit_plan(pid: str, body: EditPlan):
        plan=body.plan.model_dump()
        service.materials.descriptions(plan['components'])
        try:
            return service.store.save_plan(pid,plan,body.revision)
        except ValueError as error:
            raise HTTPException(409,str(error)) from error

    @app.post('/api/projects/{pid}/rethink')
    async def rethink(pid: str, body: Rethink):
        service.require_model()
        if service.store.project(pid)['plan_revision'] != body.revision:
            raise HTTPException(409,'方案已更新，请刷新')
        return service.submit(pid,'plan',body.model_dump())

    @app.post('/api/projects/{pid}/confirm')
    async def confirm(pid: str, body: Confirmation):
        p=service.store.project(pid)
        if p['plan'] and p['plan']['kind']=='interactive':
            service.require_model()
        if p['plan'] and p['plan']['kind']=='animation' and not p['plan'].get('animation'):
            raise ValueError('这个动画主题尚无可执行模板，请修改方案或选择互动演示')
        try:
            service.store.confirm(pid,body.revision)
            return service.submit(pid,'build',{'revision':body.revision})
        except ValueError as error:
            raise HTTPException(409,str(error)) from error

    @app.post('/api/projects/{pid}/revise')
    async def revise(pid: str, body: Revision):
        service.require_model()
        v=service.store.version(body.version_id)
        if v['project_id'] != pid:
            raise HTTPException(404,'版本不属于当前作品')
        if v['kind']!='interactive':
            raise ValueError('请从原互动版本继续修改后重新加入视频；动画可调整方案参数重新制作')
        p=service.store.project(pid)
        if p['confirmed_revision'] != p['plan_revision'] or p['plan'] != v['plan']:
            raise HTTPException(409,'方案已变更，请先确认当前方案重新制作')
        return service.submit(pid,'revision',dict(body.model_dump(),plan=v['plan'],revision=p['plan_revision']))

    @app.get('/api/jobs/{ident}')
    def job(ident: str):
        return service.store.job(ident)

    @app.post('/api/jobs/{ident}/cancel')
    async def cancel(ident: str):
        return service.cancel(ident)

    @app.get('/api/versions/{ident}/html')
    def version_html(ident: str):
        v=service.store.version(ident)
        return HTMLResponse((service.version_folder(v)/'index.html').read_text(encoding='utf-8'),headers={'Content-Security-Policy':CSP})

    @app.get('/api/versions/{ident}/download')
    def download(ident: str, format: Literal['html','video','zip','project']='html'):
        v=service.store.version(ident)
        folder=service.version_folder(v)
        if format=='html':
            if v['kind']!='interactive':
                raise ValueError('含视频作品请下载视频或完整离线包')
            return FileResponse(folder/'index.html',filename='lesson.html',media_type='text/html')
        if format=='video':
            path=folder/'assets/clip.mp4'
            if not path.is_file():
                raise ValueError('该作品没有视频')
            return FileResponse(path,filename='lesson.mp4',media_type='video/mp4')
        output=folder/(uuid4().hex+'.zip')
        bundle(folder,output,editable=format=='project')
        return FileResponse(output,filename='project.zip' if format=='project' else 'lesson.zip',media_type='application/zip',
                            background=BackgroundTask(output.unlink,missing_ok=True))

    @app.get('/api/versions/{ident}/access')
    def access(ident: str):
        service.store.version(ident)
        return create_access(ident)

    def create_access(ident):
        now=time.monotonic()
        for key,entry in list(file_access.items()):
            if entry[1]<now:
                file_access.pop(key,None)
        capability=secrets.token_urlsafe(32)
        file_access[capability]=(ident,now+3600)
        return {'url':'/files/'+capability,'expires_in':3600}

    @app.get('/files/{capability}')
    def scoped_file(capability: str, format: Literal['html','video','zip','project']='html'):
        entry=file_access.get(capability)
        if entry is None or entry[1]<time.monotonic():
            raise HTTPException(404,'下载链接已过期，请重新打开作品')
        if entry[0]=='builtin-force':
            response=HTMLResponse(example().body,headers={'Content-Disposition':'attachment; filename="force-example.html"'})
        else:
            response=download(entry[0],format)
        response.headers['Content-Security-Policy']=CSP
        response.headers['Access-Control-Allow-Origin']='*'
        return response

    @app.post('/api/import-video')
    async def import_existing(request: Request, title: str='已有教学动画'):
        from .importing import import_video
        return await import_video(service,request,title)

    @app.post('/api/versions/{ident}/video')
    async def attach_video(ident: str, request: Request):
        from .importing import import_video
        base=service.store.version(ident)
        return await import_video(service,request,base['title'],base)

    @app.get('/api/materials')
    def materials():
        return service.materials.catalog()

    @app.get('/api/examples/force')
    def example():
        from .artifacts import assemble_page,add_notices
        source=(static/'example.html').read_text(encoding='utf-8')
        page=service.materials.expand(source,['phy.apparatus.spring-scale.interactive'])
        return HTMLResponse(add_notices(assemble_page(page)))

    @app.get('/api/examples/force/access')
    def example_access():
        return create_access('builtin-force')

    return app
