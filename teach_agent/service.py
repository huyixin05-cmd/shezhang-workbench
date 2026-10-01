import asyncio
import json
from pathlib import Path
from uuid import uuid4
from pydantic import ValidationError
from .store import Store
from .model import Model, Plan
from .materials import Materials
from .artifacts import assemble_page, add_notices, notices
from .checking import check_page
from .prompts import PLAN_SYSTEM, BUILD_SYSTEM, REVIEW_SYSTEM


class Service:
    def __init__(self, settings, model=None, checker=None):
        self.settings = settings
        self.store = Store(settings.root)
        self.materials = Materials()
        self.model = model or Model(settings)
        self.checker = checker or check_page
        self.tasks = {}
        self.lock = asyncio.Lock()

    def require_model(self):
        if isinstance(self.model, Model) and not self.settings.public()['configured']:
            raise ValueError('请先在设置中配置模型，然后开始生成')

    def submit(self, pid, kind, inputs):
        job = self.store.new_job(pid, kind, inputs)
        self.tasks[job['id']] = asyncio.create_task(self.run(job))
        return job

    async def close(self):
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)

    def cancel(self, ident):
        j = self.store.job(ident)
        if j['status'] not in ('queued','running'):
            return j
        task = self.tasks.get(ident)
        if task:
            task.cancel()
        return self.store.update_job(ident, status='cancelled', stage='已取消')

    async def run(self, job):
        ident = job['id']
        try:
            async with self.lock:
                if self.store.job(ident)['status'] == 'cancelled':
                    return
                self.store.update_job(ident,status='running',stage='整理教学方案' if job['kind']=='plan' else '制作中')
                if job['kind'] == 'plan':
                    await self.plan(job)
                    result = {}
                else:
                    version = await self.build(job)
                    result = {'version_id':version['id']}
                self.store.update_job(ident,status='completed',stage='方案待确认' if job['kind']=='plan' else '制作完成',**result)
        except asyncio.CancelledError:
            self.store.update_job(ident,status='cancelled',stage='已取消；已有作品不受影响')
        except Exception as error:
            if isinstance(error, ValidationError):
                message = '模型方案结构不完整，请重新生成或修改方案'
            elif isinstance(error, ValueError):
                message = str(error)[:1000]
            else:
                message = f'制作失败（{type(error).__name__}），已有版本已保留，请检查配置后重试'
            key = self.settings.read().get('api_key')
            if key:
                message = message.replace(key,'[已隐藏]')
            self.store.update_job(ident,status='failed',stage='需要处理',error=message)

    async def plan(self, job):
        p = self.store.project(job['project_id'])
        raw = await self.model.json([
            {'role':'system','content':PLAN_SYSTEM},
            {'role':'user','content':json.dumps(dict(request=p['request'],kind=p['kind'],previous_plan=p['plan'],
                changes=job['input'].get('request'),catalog=self.materials.catalog()),ensure_ascii=False)}])
        plan = Plan.model_validate(raw).model_dump()
        if p['kind'] != 'auto' and plan['kind'] != p['kind']:
            raise ValueError('模型未遵循所选成品类型，请重新生成方案')
        self.materials.descriptions(plan['components'])
        self.store.save_plan(p['id'],plan,job['input']['revision'])

    def version_folder(self, version):
        # Directory names are server-created UUIDs, never a model path.
        folder = (self.settings.root / 'artifacts' / version['folder']).resolve()
        folder.relative_to((self.settings.root / 'artifacts').resolve())
        return folder

    async def build(self, job):
        plan = job['input']['plan']
        folder_id = uuid4().hex
        folder = self.settings.root / 'artifacts' / folder_id
        folder.mkdir(parents=True)
        (folder/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'THIRD_PARTY_NOTICES.txt').write_text(notices(),encoding='utf-8')
        if plan['kind'] == 'animation':
            from .animation import render_animation
            self.store.update_job(job['id'],stage='渲染教学动画')
            report = await render_animation(plan,folder,self.settings.read().get('manim_python',''))
            source = {'animation':plan['animation']}
        else:
            self.store.update_job(job['id'],stage='制作互动演示')
            previous = None
            if job['input'].get('version_id'):
                previous_v = self.store.version(job['input']['version_id'])
                previous = json.loads((self.version_folder(previous_v)/'source.json').read_text(encoding='utf-8'))
            messages = [{'role':'system','content':BUILD_SYSTEM}, {'role':'user','content':json.dumps(
                dict(plan=plan,components=self.materials.descriptions(plan['components']),previous=previous,
                     change=job['input'].get('request')),ensure_ascii=False)}]
            report = None
            for attempt in range(3):
                source = await self.model.json(messages)
                (folder/'source.json').write_text(json.dumps(source,ensure_ascii=False),encoding='utf-8')
                try:
                    raw_html = source.get('html')
                    if not isinstance(raw_html,str) or len(raw_html)>1_500_000:
                        raise ValueError('模型未生成完整课件')
                    # Validate model-authored resources before adding trusted vendored code.
                    assemble_page(raw_html)
                    expanded = self.materials.expand(raw_html,plan['components'])
                    page = add_notices(assemble_page(expanded))
                    (folder/'index.html').write_text(page,encoding='utf-8')
                    self.store.update_job(job['id'],stage='检查交互与离线资源')
                    report = await asyncio.wait_for(self.checker(folder/'index.html',source.get('checks')),timeout=90)
                    self.store.update_job(job['id'],stage='复核教学内容')
                    review = await self.model.json([{'role':'system','content':REVIEW_SYSTEM},
                        {'role':'user','content':json.dumps(dict(plan=plan,html=raw_html),ensure_ascii=False)}])
                    if review.get('passed') is not True or review.get('issues') != []:
                        report['errors'].append('教学复核：'+str(review.get('issues','复核结果无效'))[:1200])
                    report['model_review'] = review
                    report['passed'] = report.get('passed') is True and not report['errors']
                except ValueError as error:
                    report = dict(passed=False,errors=[str(error)],browser_checked=False)
                (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                if report['passed']:
                    break
                if attempt < 2:
                    self.store.update_job(job['id'],stage=f'修复检查问题（{attempt+1}/2）')
                    messages += [{'role':'assistant','content':json.dumps(source,ensure_ascii=False)},
                                 {'role':'user','content':'修复以下问题，返回完整 JSON：'+json.dumps(report['errors'],ensure_ascii=False)}]
            if not report or not report['passed']:
                self.store.update_job(job['id'],draft_folder=folder_id)
                raise ValueError('两轮修复后仍未通过检查，草稿保留：'+'；'.join(report['errors'])[:600])
        (folder/'source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        return self.store.save_version(job['project_id'],dict(title=plan['title'],kind=plan['kind'],folder=folder_id,
            plan=plan,report=report,base_version=job['input'].get('version_id'),plan_revision=job['input'].get('revision')))
