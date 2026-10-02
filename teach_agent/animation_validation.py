"""Reuse the pinned AST/LaTeX checks without importing an agent or CLI runtime."""
import importlib.util
import json
from pathlib import Path
import sys

path=Path(__file__).parent/'vendor/math_to_manim/sol/scene_checks.py'
spec=importlib.util.spec_from_file_location('teach_agent._scene_checks',path)
checks=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=checks
spec.loader.exec_module(checks)

ARTIFACT_NAMES=('01_intent.json','02_knowledge_map.json','03_curriculum.json','04_math_dossier.json',
    '05_shot_list.json','06_scene_spec.json','sol_scene.py','validation.json','review.json')


def validate_run(work,*,require_video=False):
    from .animation_workflow import owned_file
    from .animation_rendering import inspect_source
    from .animation_pipeline import write_json
    work=Path(work);source=owned_file(work,'sol_scene.py').read_text(encoding='utf-8')
    tree=inspect_source(source);report=checks.validate_manim_code_report(source)
    write_json(work/'validation.json',checks.validation_from_scene(source))
    failures=list(report.errors);names=checks.discover_scene_classes(tree)
    if len(names)!=1:failures.append('场景必须包含一个可渲染的 Scene 类')
    for name in ARTIFACT_NAMES:
        path=owned_file(work,name)
        if name.endswith('.json'):
            try: value=json.loads(path.read_text(encoding='utf-8'))
            except ValueError:failures.append(name+' 格式错误');continue
            if not isinstance(value,dict) or not value:failures.append(name+' 不能为空')
    return failures,names[0] if len(names)==1 else None,None
