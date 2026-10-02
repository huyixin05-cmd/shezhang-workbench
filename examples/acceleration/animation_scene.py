"""Topic-specific Manim lesson, with local narration and original OLC cart geometry."""
from pathlib import Path
import re
import wave
from xml.etree import ElementTree as ET
from manim import *
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WORK=HERE/'render-local'
BG='#F5F6F0';INK='#203E35';MUTED='#63786B';GREEN='#126B59';AMBER='#AD642B';LINE='#CDD8CD'
FONT='Microsoft YaHei'
config.background_color=BG


def text(value,size=27,color=INK):
    return Text(value,font=FONT,font_size=size,color=color)


def fraction(top,bottom,size=58):
    numerator=text(top,size,GREEN).move_to([0,.42,0])
    denominator=text(bottom,size,GREEN).move_to([0,-.42,0])
    bar=Line(LEFT*max(numerator.width,denominator.width)*.65,RIGHT*max(numerator.width,denominator.width)*.65,color=GREEN,stroke_width=3)
    return VGroup(numerator,bar,denominator)


def cart_asset(color,mass):
    path=WORK/f'cart-{color[1:]}-{mass}.svg'
    source=(ROOT/'teach_agent/vendor/olc/components/physics/mechanics/phy.mechanics.cart.dynamics.html').read_text(encoding='utf-8')
    raw=re.search(r'<svg\b[^>]*>.*?</svg>',source,re.S).group(0)
    raw=raw.replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" ')
    for key,value in {'body':color,'stroke':'#263238','stroke-width':'1.5','wheel':'#37474f'}.items():
        raw=re.sub(r'var\(--cmp-'+re.escape(key)+r',[^)]+\)',value,raw)
    raw=raw.replace('calc(1.5*0.7)','1.05').replace('rgba(0,0,0,0.15)','#48675D').replace('rgba(0,0,0,0.08)','#526E65')
    tree=ET.fromstring(raw)
    for group in list(tree):
        match=re.search(r'dc__mass-(\d+)',group.attrib.get('class',''))
        if match:
            if int(match[1])>=mass:tree.remove(group)
            else:group.attrib.pop('style',None)
    ET.register_namespace('','http://www.w3.org/2000/svg')
    path.write_text(ET.tostring(tree,encoding='unicode'),encoding='utf-8')
    return path


class AccelerationLesson(Scene):
    def title(self,label,subtitle):
        heading=text(label,34).to_edge(UP,buff=.42).to_edge(LEFT,buff=.7)
        sub=text(subtitle,20,MUTED).next_to(heading,DOWN,buff=.16,aligned_edge=LEFT)
        brand=text('舍长工作台  /  物理实验室',14,MUTED).to_corner(DR,buff=.2)
        self.add(heading,sub,brand)

    def caption(self,line):
        if hasattr(self,'caption_group'):self.remove(self.caption_group)
        box=RoundedRectangle(width=12.7,height=.78,corner_radius=.12,stroke_width=0,fill_color='#E7EFE3',fill_opacity=1).move_to([0,-3.14,0])
        label=text(line,25).move_to(box)
        if label.width>11.8:label.scale_to_fit_width(11.8)
        self.caption_group=VGroup(box,label)
        self.add(self.caption_group)

    def audio(self,key):
        path=WORK/'audio'/f'{key}.wav'
        with wave.open(str(path)) as stream:duration=stream.getnframes()/stream.getframerate()
        self.add_sound(str(path))
        return duration

    def finish(self,duration,start):
        elapsed=self.time-start
        self.wait(max(.4,duration+.6-elapsed))
        self.play(FadeOut(Group(*self.mobjects)),run_time=.5)

    def construct(self):
        WORK.mkdir(exist_ok=True)
        self.intro()
        self.compare('force',2,2,2,4)
        self.compare('mass',1,2,4,4)
        self.uniform()
        self.ratio()

    def intro(self):
        start=self.time;duration=self.audio('intro')
        kicker=text('观察 · 比较 · 理解',20,MUTED).move_to([0,2,0])
        title=text('加速度，由什么决定？',49).move_to([0,.85,0])
        question=text('同样的时间，速度改变了多少？',30,GREEN).move_to([0,-.45,0])
        foot=text('理想模型：水平直线运动，忽略摩擦；F 表示水平合力。',20,MUTED).move_to([0,-2.05,0])
        self.play(FadeIn(kicker),FadeIn(title,shift=UP*.15),run_time=.7)
        self.play(FadeIn(question),FadeIn(foot),run_time=.8)
        self.finish(duration,start)

    def compare(self,mode,mA,mB,fA,fB):
        start=self.time;duration=self.audio(mode)
        aA=fA/mA;aB=fB/mB
        if mode=='force':
            heading='① 质量相同，改变合力';sub='只改变一个因素，才能判断它的影响。';conclusion='质量相同：合力变为 2 倍，加速度也变为 2 倍。'
        else:
            heading='② 合力相同，改变质量';sub='仍从静止出发，比较同样的 2 秒。';conclusion='合力相同：质量变为 2 倍，加速度变为原来的一半。'
        self.title(heading,sub)
        tracker=ValueTracker(0)
        axes=Axes(x_range=[0,2,.5],y_range=[0,max(aA,aB)*2,max(aA,aB)/2],x_length=4.55,y_length=3.3,
                  axis_config={'color':MUTED,'stroke_width':1.5,'include_tip':False,'include_ticks':False}).move_to([3.55,.1,0])
        self.add(axes)
        self.add(text('速度 v / (m/s)',19,MUTED).next_to(axes,UP,buff=.18),text('时间 t / s',17,MUTED).next_to(axes,DOWN,buff=.35).align_to(axes,RIGHT))
        for tm in [0,1,2]:self.add(text(str(tm),16,MUTED).next_to(axes.c2p(tm,0),DOWN,buff=.12))
        for v in [0,max(aA,aB),2*max(aA,aB)]:self.add(text(f'{v:g}',16,MUTED).next_to(axes.c2p(0,v),LEFT,buff=.15))
        time_number=DecimalNumber(0,mob_class=Text,num_decimal_places=2,font_size=26,color=INK).move_to([-.65,-2.12,0])
        self.add(text('共同时间',18,MUTED).next_to(time_number,LEFT,buff=.22),time_number,text('s',18,MUTED).next_to(time_number,RIGHT,buff=.1))
        time_number.add_updater(lambda d:d.set_value(tracker.get_value()))
        distance_scale=4.0/(2*max(aA,aB))
        for name,mass,force,acc,y,color in [('A',mA,fA,aA,1.3,GREEN),('B',mB,fB,aB,-.8,AMBER)]:
            line=Line([-6.25,y-.37,0],[.45,y-.37,0],stroke_color=LINE,stroke_width=3)
            car=SVGMobject(str(cart_asset(color,mass)),height=.67).move_to([-5.65,y,0])
            arrow=Arrow(car.get_right()+UP*.4,car.get_right()+UP*.4+RIGHT*force*.22,buff=0,color=color,stroke_width=4,max_tip_length_to_length_ratio=.2)
            moving=VGroup(car,arrow)
            baseline=moving.get_center().copy()
            moving.add_updater(lambda mob,baseline=baseline,acc=acc:mob.move_to(baseline+RIGHT*(.5*acc*tracker.get_value()**2*distance_scale)))
            label=text(f'{name} 车     F = {force} N     m = {mass} kg',21,color).move_to([-3.65,y+.65,0])
            vnum=DecimalNumber(0,mob_class=Text,num_decimal_places=2,font_size=25,color=color).move_to([-3.15,y-.9,0])
            vnum.add_updater(lambda d,acc=acc:d.set_value(acc*tracker.get_value()))
            self.add(line,moving,label,text('速度',18,MUTED).next_to(vnum,LEFT,buff=.18),vnum,text('m/s',18,MUTED).next_to(vnum,RIGHT,buff=.12))
            graph=always_redraw(lambda acc=acc,color=color:Line(axes.c2p(0,0),axes.c2p(max(.0001,tracker.get_value()),acc*max(.0001,tracker.get_value())),color=color,stroke_width=4))
            self.add(graph)
        self.caption('先观察：同样的时间里，哪辆车的速度增加得更多？')
        self.wait(min(5,duration*.3))
        self.play(tracker.animate.set_value(2),run_time=4,rate_func=linear)
        for obj in self.mobjects:obj.clear_updaters()
        self.caption(conclusion)
        values=text(f'aA = {aA:g} m/s²     aB = {aB:g} m/s²',24,GREEN).move_to([3.55,-2.42,0])
        self.play(FadeIn(values),run_time=.4)
        self.finish(duration,start)

    def uniform(self):
        start=self.time;duration=self.audio('zero')
        self.title('③ 速度大，不等于加速度大','合力为零，初速度不为零。')
        track=Line([-5.8,.5,0],[5.8,.5,0],color=LINE,stroke_width=4)
        car=SVGMobject(str(cart_asset(GREEN,1)),height=.95).move_to([-5.1,1,0])
        ticks=VGroup(*[Dot([-5.1+i*2.1,.4,0],color=GREEN,radius=.055) for i in range(5)])
        specs=text('F = 0 N       v = 3 m/s',32,GREEN).move_to([0,2.1,0])
        equal=text('每隔 1 秒，前进相同的距离',24,MUTED).move_to([0,-.2,0])
        self.add(track,specs,car,ticks,equal)
        self.caption('小车一直在前进，但速度没有变化。')
        self.wait(2)
        self.play(car.animate.shift(RIGHT*8.4),run_time=4,rate_func=linear)
        statement=text('Δv = 0     →     a = 0',40,GREEN).move_to([0,-1.55,0])
        self.play(FadeIn(statement),run_time=.5)
        self.caption('加速度看的是“速度的变化”，不是“速度的大小”。')
        self.finish(duration,start)

    def ratio(self):
        start=self.time;duration=self.audio('ratio')
        self.title('④ 两个因素一起改变呢？','用关系判断，再回到实验验证。')
        equation=VGroup(text('a =',64,GREEN),fraction('F','m',64)).arrange(RIGHT,buff=.25).move_to([-3.6,.9,0])
        self.add(equation,text('F：合力   m：总质量',23,MUTED).next_to(equation,DOWN,buff=.45))
        q=text('合力 ×2，质量也 ×2',32).move_to([2.8,1.5,0])
        self.play(FadeIn(q),run_time=.5)
        self.caption('先想一想：加速度会变大、变小，还是不变？')
        self.wait(max(2,duration*.48))
        answer=VGroup(fraction('2F','2m',48),text('=',48,GREEN),fraction('F','m',48)).arrange(RIGHT,buff=.25).move_to([2.8,.15,0])
        label=text('比值不变，加速度不变。',30,GREEN).move_to([2.8,-1.2,0])
        self.play(FadeIn(answer),FadeIn(label),run_time=.7)
        self.caption('质量不变看合力，合力不变看质量；一起变，就比较 F/m。')
        self.finish(duration,start)
