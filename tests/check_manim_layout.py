"""Run explicitly with the configured Manim Python; does not render frames."""
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from manim import Scene, tempconfig

template=Path(__file__).resolve().parents[1]/'teach_agent/animation_templates/force_composition.py'
spec=importlib.util.spec_from_file_location('controlled_scene',template)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
original_text=module.Text
with tempfile.TemporaryDirectory() as temporary:
    for angle,a,b in [(180,.1,10),(0,10,.1),(90,10,10),(60,3,4)]:
        texts=[]
        def capture(*args,**kwargs):
            value=original_text(*args,**kwargs);texts.append(value);return value
        module.Text=capture
        path=Path(temporary)/'params.json'
        path.write_text(json.dumps(dict(title='两个力如何合成',force1=a,force2=b,angle=angle,hold=1)),encoding='utf-8')
        os.environ['TEACH_SCENE_PARAMS']=str(path)
        with tempconfig({'media_dir':temporary}):
            scene=module.ForceComposition()
            scene.play=lambda *args,**kwargs:None
            scene.wait=lambda *args,**kwargs:None
            scene.construct()
            if angle in (0,180):
                assert not any('对角顶点' in item.text for item in texts)
            for item in texts:
                assert item.get_left()[0]>=-6.95 and item.get_right()[0]<=6.95, (angle,a,b,item.text,item.get_left(),item.get_right())
print('4 animation layouts: all text remains inside the frame')
