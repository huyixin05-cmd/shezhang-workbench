"""A controlled adaptation of the user's existing force-composition workflow.

Parameters are data only. The agent never executes model-authored Python here.
"""
import json
import math
import os
from pathlib import Path
from manim import Scene, Text, Arrow, DashedLine, VGroup, FadeIn, FadeOut, GrowArrow, Create, UP, DOWN, LEFT, RIGHT
import numpy as np


class ForceComposition(Scene):
    def construct(self):
        p=json.loads(Path(os.environ['TEACH_SCENE_PARAMS']).read_text(encoding='utf-8'))
        self.camera.background_color='#F4F8F6'
        ink='#173630'; teal='#168A80'; amber='#CB8615'; result_color='#C55051'
        font='Microsoft YaHei' if os.name=='nt' else 'sans-serif'
        def text(value,size=28,color=ink):
            return Text(value,font=font,font_size=size,color=color)
        title=text(p['title'],34).to_edge(UP,buff=.4)
        origin=np.array([-2.8,-.8,0.])
        a=p['force1']; b=p['force2']; angle=math.radians(p['angle'])
        scale=4.3/(a+b)
        u=np.array([a*scale,0,0.]); v=np.array([b*math.cos(angle)*scale,b*math.sin(angle)*scale,0.])
        def arrow(start,end,color):
            return Arrow(start,end,buff=0,color=color,stroke_width=7,max_tip_length_to_length_ratio=.15)
        f1=arrow(origin,origin+u,teal); f2=arrow(origin,origin+v,amber)
        label1=text(f'F₁ = {a:g} N',25,teal).next_to(f1,DOWN,buff=.2)
        label2=text(f'F₂ = {b:g} N',25,amber).next_to(f2,LEFT,buff=.2)
        note=text('同一物体、同一时刻的两个力，从同一个作用点画起。',24).to_edge(DOWN,buff=.5)
        self.add(title)
        self.play(GrowArrow(f1),FadeIn(label1),run_time=1)
        self.play(GrowArrow(f2),FadeIn(label2),FadeIn(note),run_time=1)
        self.wait(p['hold'])
        lines=VGroup(DashedLine(origin+u,origin+u+v,color=amber),DashedLine(origin+v,origin+u+v,color=teal))
        next_note=text('分别作平行线，构成平行四边形。',24).to_edge(DOWN,buff=.5)
        self.play(FadeOut(note),FadeIn(next_note),Create(lines),run_time=1.5)
        self.wait(p['hold'])
        magnitude=math.sqrt(max(0,a*a+b*b+2*a*b*math.cos(angle)))
        equation=text(f'F = √(F₁² + F₂² + 2F₁F₂ cos θ) = {magnitude:.2f} N',24).to_edge(DOWN,buff=1.1)
        final=text('从共同起点指向对角顶点的箭头表示合力。',24).to_edge(DOWN,buff=.5)
        if magnitude>1e-6:
            resultant=arrow(origin,origin+u+v,result_color)
            self.play(GrowArrow(resultant),FadeOut(next_note),FadeIn(final),FadeIn(equation),run_time=1.5)
        else:
            final=text('两个力等大反向，合力为零。',24).to_edge(DOWN,buff=.5)
            self.play(FadeOut(next_note),FadeIn(final),FadeIn(equation),run_time=1.5)
        self.wait(p['hold']+1)
