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
            label=Text(value,font=font,font_size=size,color=color)
            if label.width>12.5:
                label.scale_to_fit_width(12.5)
            return label
        title=text(p['title'],34).to_edge(UP,buff=.4)
        a=p['force1']; b=p['force2']; angle=math.radians(p['angle'])
        scale=min(4.3/(a+b),2.5/max(abs(b*math.sin(angle)),.001))
        u=np.array([a*scale,0,0.]); v=np.array([b*math.cos(angle)*scale,b*math.sin(angle)*scale,0.])
        points=np.array([np.zeros(3),u,v,u+v])
        origin=-(points.min(axis=0)+points.max(axis=0))/2+np.array([0.,.25,0.])
        def arrow(start,end,color):
            return Arrow(start,end,buff=0,color=color,stroke_width=7,max_tip_length_to_length_ratio=.15)
        f1=arrow(origin,origin+u,teal); f2=arrow(origin,origin+v,amber)
        label1=text(f'F₁ = {a:g} N',25,teal).next_to(f1,DOWN,buff=.2)
        label2=text(f'F₂ = {b:g} N',25,amber).next_to(f2,LEFT,buff=.2)
        note=text('同一物体、同一时刻的两个力，从同一个作用点画起。',24).to_edge(DOWN,buff=.5)
        angle_label=text(f'θ = {p["angle"]:g}°',24).to_corner(UP+RIGHT,buff=.6).shift(DOWN*.6)
        self.add(title,angle_label)
        self.play(GrowArrow(f1),FadeIn(label1),run_time=1)
        self.play(GrowArrow(f2),FadeIn(label2),FadeIn(note),run_time=1)
        self.wait(p['hold'])
        lines=VGroup(DashedLine(origin+u,origin+u+v,color=amber),DashedLine(origin+v,origin+u+v,color=teal))
        direction_note='同向共线的两个力，大小直接相加。' if p['angle']==0 else '反向共线的两个力，大小取差，方向看较大的力。' if p['angle']==180 else '分别作平行线，构成平行四边形。'
        next_note=text(direction_note,24).to_edge(DOWN,buff=.5)
        self.play(FadeOut(note),FadeIn(next_note),Create(lines),run_time=1.5)
        self.wait(p['hold'])
        magnitude=math.sqrt(max(0,a*a+b*b+2*a*b*math.cos(angle)))
        equation=text(f'F = √(F₁² + F₂² + 2F₁F₂ cos θ) = {magnitude:.2f} N',24).to_edge(DOWN,buff=1.1)
        final_text='红色箭头表示合力：同向相加，反向相减。' if p['angle'] in (0,180) else '从共同起点指向对角顶点的箭头表示合力。'
        final=text(final_text,24).to_edge(DOWN,buff=.5)
        if magnitude>1e-6:
            resultant=arrow(origin,origin+u+v,result_color)
            self.play(GrowArrow(resultant),FadeOut(next_note),FadeIn(final),FadeIn(equation),run_time=1.5)
        else:
            final=text('两个力等大反向，合力为零。',24).to_edge(DOWN,buff=.5)
            self.play(FadeOut(next_note),FadeIn(final),FadeIn(equation),run_time=1.5)
        self.wait(p['hold']+1)
