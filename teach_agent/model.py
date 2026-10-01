import asyncio
import json
import re
import httpx
from pydantic import BaseModel, Field, ConfigDict, StringConstraints, model_validator
from typing import Annotated, Literal
from .animation_contract import AnimationBrief, validate_animation


TeachingText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)]


class TeachingStep(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    question: TeachingText
    flow: Literal['act_then_explain', 'explain_then_act']
    explanation: TeachingText
    action: TeachingText
    observation: TeachingText
    takeaway: TeachingText
    check: TeachingText


class LearningDesign(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_analysis: TeachingText
    student_problem: TeachingText
    difficulty_reason: TeachingText
    design_response: TeachingText
    success_evidence: TeachingText
    sequence: list[TeachingStep] = Field(min_length=2, max_length=8)


class Plan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=120)
    kind: Literal['interactive', 'animation']
    grade: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=1000)
    misconception: str = Field(max_length=1000)
    interaction: str = Field(min_length=1, max_length=2000)
    steps: list[str] = Field(min_length=2, max_length=8)
    observation: str = Field(min_length=1, max_length=1000)
    check_question: str = Field(min_length=1, max_length=1000)
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    components: list[str] = Field(default_factory=list, max_length=8)
    animation: AnimationBrief | dict | None = None
    # Older saved projects remain readable; new model proposals must supply this.
    learning_design: LearningDesign | None = None

    @model_validator(mode='after')
    def align_steps(self):
        if self.kind == 'animation' and self.animation is not None:
            value = self.animation.model_dump() if isinstance(self.animation, AnimationBrief) else self.animation
            self.animation = validate_animation(value)
        if self.learning_design:
            self.steps = [step.title for step in self.learning_design.sequence]
        return self


class ModelOutputError(ValueError):
    """A model response can be corrected, unlike transport/configuration errors."""


def parse_json(text):
    if not isinstance(text, str) or len(text) > 2_000_000:
        raise ModelOutputError('模型返回为空或过大')
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ModelOutputError('模型未返回完整有效的 JSON，请重试') from error
    if not isinstance(value, dict):
        raise ModelOutputError('模型必须返回 JSON 对象')
    return value


class Model:
    def __init__(self, settings):
        self.settings = settings

    async def json(self, messages):
        config = self.settings.read()
        if not config.get('base_url') or not config.get('model'):
            raise ValueError('请先在设置中填写模型地址和模型名')
        headers = {'Content-Type': 'application/json'}
        if config.get('api_key'):
            headers['Authorization'] = 'Bearer ' + config['api_key']
        payload = dict(model=config['model'], messages=messages, temperature=0.3,
                       max_tokens=config.get('max_tokens', 12000))
        async with httpx.AsyncClient(timeout=httpx.Timeout(180, connect=15),
                                    follow_redirects=False, trust_env=False) as client:
            for attempt in range(2):
                try:
                    async with client.stream('POST', config['base_url'].rstrip('/') + '/chat/completions',
                                             headers=headers, json=payload) as response:
                        if response.status_code in (429, 502, 503, 504) and attempt == 0:
                            await asyncio.sleep(1)
                            continue
                        if response.status_code != 200:
                            raise ValueError(f'模型服务返回 HTTP {response.status_code}，请检查配置或额度')
                        raw = bytearray()
                        async for chunk in response.aiter_bytes():
                            raw.extend(chunk)
                            if len(raw) > 3_000_000:
                                raise ValueError('模型响应超过大小限制')
                    data = json.loads(raw)
                    choice = data['choices'][0]
                    if choice.get('finish_reason') == 'length':
                        raise ValueError('模型输出被截断，请提高输出上限或缩小内容范围')
                    return parse_json(choice['message']['content'])
                except httpx.TimeoutException as error:
                    raise ValueError('模型响应超时，请稍后重试') from error
                except httpx.HTTPError as error:
                    raise ValueError('无法连接模型服务，请检查地址和网络') from error
                except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
                    raise ValueError('模型响应格式不兼容 Chat Completions') from error
