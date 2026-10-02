"""Hand model work back to the MCP conversation, without a second inference API."""
import asyncio
import json
from uuid import uuid4
from .model import ModelServiceError


class HostBroker:
    def __init__(self,timeout=900):
        self.timeout=timeout
        self.requests={}

    async def ask(self,job_id,messages):
        if job_id in self.requests:
            raise ModelServiceError('当前任务已有一个等待处理的模型步骤')
        future=asyncio.get_running_loop().create_future()
        entry={'id':uuid4().hex,'job_id':job_id,'messages':messages,'future':future}
        self.requests[job_id]=entry
        try:
            return await asyncio.wait_for(future,timeout=self.timeout)
        except asyncio.TimeoutError as error:
            raise ModelServiceError('等待对话模型处理超时，请在 WorkBuddy 中重新提交任务；已有版本保留。') from error
        finally:
            if self.requests.get(job_id) is entry:
                del self.requests[job_id]

    def pending(self,job_id):
        entry=self.requests.get(job_id)
        if not entry or entry['future'].done():
            return None
        return {key:entry[key] for key in ('id','job_id','messages')}

    def submit(self,job_id,request_id,result,error=None):
        entry=self.requests.get(job_id)
        if not entry or entry['id']!=request_id or entry['future'].done():
            raise ValueError('模型步骤已失效或不属于该任务，请重新查看进度')
        if error:
            entry['future'].set_exception(ModelServiceError('对话模型无法完成此步骤：'+str(error)[:800]))
        else:
            if not isinstance(result,dict) or len(json.dumps(result,ensure_ascii=False))>2_000_000:
                raise ValueError('模型步骤需要有效 JSON 对象，且不能超过大小限制')
            entry['future'].set_result(result)
        return {'accepted':True}

    def cancel(self,job_id):
        entry=self.requests.get(job_id)
        if entry and not entry['future'].done():
            entry['future'].cancel()
