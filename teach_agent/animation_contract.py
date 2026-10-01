from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True,min_length=1,max_length=800)]


class Shot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: Text
    visual: Text
    motion: Text
    explanation: Text
    seconds: float = Field(ge=2,le=60,allow_inf_nan=False)


class AnimationBrief(BaseModel):
    model_config = ConfigDict(extra='forbid')
    workflow: Literal['sol'] = 'sol'
    duration_seconds: float = Field(ge=4,le=300,allow_inf_nan=False)
    aspect_ratio: Literal['16:9','9:16'] = '16:9'
    shots: list[Shot] = Field(min_length=2,max_length=8)

    @model_validator(mode='after')
    def duration_matches(self):
        if abs(sum(shot.seconds for shot in self.shots)-self.duration_seconds)>1:
            raise ValueError('分镜时长合计应与总时长一致')
        return self


def validate_animation(value, *, allow_legacy=True):
    if isinstance(value,dict) and value.get('workflow')=='sol':
        return AnimationBrief.model_validate(value).model_dump()
    if allow_legacy and isinstance(value,dict) and value.get('template')=='force_composition':
        from .animation import validate_params
        return validate_params(value)
    raise ValueError('动画方案需要完整分镜，请重新生成方案')
