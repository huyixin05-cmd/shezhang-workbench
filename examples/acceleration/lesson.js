document.addEventListener('DOMContentLoaded', () => {
  'use strict';
  const $ = id => document.getElementById(id);
  const modes = {
    force:{values:[2,2,4,2,0],enabled:['fb'],question:'质量相同，合力更大，速度变化会更快吗？',method:'保持两车质量均为 2 kg，只改变 B 车所受合力。',controlled:'控制变量：质量'},
    mass:{values:[4,1,4,2,0],enabled:['mb'],question:'合力相同，质量更大，速度变化会怎样？',method:'保持两车合力均为 4 N，只改变 B 车的总质量。',controlled:'控制变量：合力'},
    free:{values:[2,2,4,2,0],enabled:['fa','ma','fb','mb','v0'],question:'自己设定条件，验证你的想法。',method:'试试合力和质量一起翻倍，或让合力为零的小车带着初速度出发。',controlled:'自由控制 · 注意公平比较'}
  };
  const controls=['fa','ma','fb','mb','v0'];
  let mode='force', t=0, running=false, observed=false, prediction=null, revealed=false;
  let params, aA, aB, maxDistance, maxVelocity, animation;
  const number = value => Number(value).toFixed(2);
  const node = (tag,attributes,text) => {
    const el=document.createElementNS('http://www.w3.org/2000/svg',tag);
    Object.entries(attributes).forEach(([key,value])=>el.setAttribute(key,value));
    if(text!==undefined) el.textContent=text;
    return el;
  };
  function winner() { return Math.abs(aA-aB)<1e-9?'same':aA>aB?'a':'b'; }
  function setRunning(value) {
    running=value;
    $('play').textContent=value?'Ⅱ 暂停观察':t>=2?'↻ 再看一次':t>0?'▶ 继续实验':'▶ 同时出发';
    if(value) animation.start(); else animation.pause();
  }
  function axes() {
    const ticks=$('ticks');ticks.replaceChildren();
    for(let i=0;i<=4;i++) {
      const x=104+i*550/4;
      [94,211].forEach(y=>{
        ticks.append(node('line',{x1:x,x2:x,y1:y,y2:y+7,stroke:'#9eaea4'}));
        ticks.append(node('text',{x,y:y+25,'text-anchor':'middle',class:'tick-label'},(maxDistance*i/4).toFixed(1)));
      });
    }
    [119,236].forEach(y=>ticks.append(node('text',{x:798,y,class:'tick-label'},'m')));
    const grid=$('graph-grid');grid.replaceChildren();
    for(let i=0;i<=4;i++) {
      const x=60+i*710/4,y=193-i*155/4;
      grid.append(node('line',{x1:60,x2:770,y1:y,y2:y,stroke:'#e7ece4'}));
      grid.append(node('text',{x:48,y:y+5,'text-anchor':'end',fill:'#718079','font-size':13},(maxVelocity*i/4).toFixed(1)));
      grid.append(node('line',{x1:x,x2:x,y1:38,y2:193,stroke:'#edf0ea'}));
      grid.append(node('text',{x,y:215,'text-anchor':'middle',fill:'#718079','font-size':13},(i*.5).toFixed(1)));
    }
    grid.append(node('path',{d:'M60 28V193H782',stroke:'#8c9e91',fill:'none'}));
    grid.append(node('text',{x:10,y:18,fill:'#63786b','font-size':14},'速度 v / (m/s)'));
    grid.append(node('text',{x:774,y:232,'text-anchor':'end',fill:'#63786b','font-size':13},'时间 t / s'));
  }
  function cartAppearance(which,force,mass) {
    $('spec-'+which).textContent=`${force} N · ${mass} kg`;
    const cart=$('cart-'+which);
    for(let i=1;i<=3;i++) cart.querySelector('.dc__mass-'+i).style.display=i<mass?'':'none';
    const arrow=$('force-arrow-'+which);
    arrow.setAttribute('x2',String(105+force*18));
    arrow.style.display=force===0?'none':'';
    $('force-label-'+which).textContent=force===0?'合力 0 N':`${force} N`;
  }
  function readConditions() {
    params=Object.fromEntries(controls.map(id=>[id,Number($(id).value)]));
    aA=params.fa/params.ma;aB=params.fb/params.mb;
    maxDistance=Math.max(2,Math.ceil((params.v0*2+2*Math.max(aA,aB))/2)*2);
    maxVelocity=Math.max(2,Math.ceil((params.v0+2*Math.max(aA,aB))/2)*2);
    controls.forEach(id=>$(id+'-value').textContent=params[id]+(id==='v0'?' m/s':id[0]==='f'?' N':' kg'));
    cartAppearance('a',params.fa,params.ma);cartAppearance('b',params.fb,params.mb);
    axes();
  }
  function render() {
    $('clock').textContent=number(t);$('timeline').value=t;
    for(const [which,a,y] of [['a',aA,43],['b',aB,160]]) {
      const s=params.v0*t+.5*a*t*t,v=params.v0+a*t;
      $('cart-'+which).setAttribute('transform',`translate(${80+s/maxDistance*550} ${y})`);
      $('velocity-'+which).innerHTML=`${number(v)} <small>m/s</small>`;
      $('distance-'+which).textContent=`位移 ${number(s)} m`;
      const trace=$('trace-'+which);trace.replaceChildren();
      for(let tm=0;tm<=t+1e-8;tm+=.5) {
        const x=104+(params.v0*tm+.5*a*tm*tm)/maxDistance*550;
        trace.append(node('circle',{cx:x,cy:y+57,r:3.5,opacity:.55}));
      }
      const x=60+t/2*710, yy=193-v/maxVelocity*155, initialY=193-params.v0/maxVelocity*155;
      $('line-'+which).setAttribute('d',`M60 ${initialY}L${x} ${yy}`);
      $('point-'+which).setAttribute('cx',x);$('point-'+which).setAttribute('cy',yy);
    }
    const x=60+t/2*710;$('time-cursor').setAttribute('x1',x);$('time-cursor').setAttribute('x2',x);
    $('delta').textContent=t<.001?'等待出发':`A +${number(aA*t)} · B +${number(aB*t)} m/s`;
    if(t>=.5) observed=true;
    $('explain').disabled=!observed;
  }
  function clearFinding() {
    prediction=null;revealed=false;$('finding').hidden=true;$('explain').hidden=false;
    document.querySelectorAll('[data-prediction]').forEach(b=>{b.classList.remove('selected');b.setAttribute('aria-pressed','false');});
    $('prediction-note').textContent='选一个猜想，再用实验检验。';
    $('graph-note').textContent='横轴是时间，纵轴是速度。观察同一段时间内，两条线各升高了多少。';
  }
  function rewind(clear=false) {
    t=0;setRunning(false);
    if(clear) {observed=false;clearFinding();}
    render();$('run-status').textContent='两车已回到起点。条件相同，随时可以再做一次。';
  }
  const conditionsChanged=TeachInteraction.frame(()=>{readConditions();rewind(true);});
  controls.forEach(id=>$(id).addEventListener('input',()=>{setRunning(false);conditionsChanged();}));
  animation=TeachInteraction.simulation({dt:1/120,maxSteps:12,update:dt=>{
    if(!running) return;
    t=Math.min(2,t+dt*Number($('playback-speed').value));
    if(t>=2-1e-8) {t=2;setRunning(false);$('run-status').textContent='2 秒观察结束。拖动时间条回看，或点击“归纳规律”。';}
  },render});
  function chooseMode(nextMode) {
    conditionsChanged.cancel();setRunning(false);mode=nextMode;
    document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);b.setAttribute('aria-pressed',String(b.dataset.mode===mode));});
    $('experiment').hidden=mode==='quiz';$('quiz').hidden=mode!=='quiz';
    if(mode==='quiz') return;
    const config=modes[mode];
    controls.forEach((id,i)=>{$(id).value=config.values[i];$(id).disabled=!config.enabled.includes(id);});
    $('question').textContent=config.question;$('method').textContent=config.method;$('controlled').textContent=config.controlled;
    $('initial-control').hidden=mode!=='free';
    $('next').textContent=mode==='force'?'继续探究质量 →':mode==='mass'?'自由验证想法 →':'检验我的理解 →';
    readConditions();rewind(true);
  }
  document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>chooseMode(b.dataset.mode));
  $('play').onclick=()=>{conditionsChanged.flush();if(running) {setRunning(false);$('run-status').textContent='已暂停。观察读数，或拖动时间条回看。';return;}
    if(t>=2) rewind();setRunning(true);$('run-status').textContent='两车同时运动中。注意比较同一段时间内的速度增加量。';};
  $('restart').onclick=()=>{conditionsChanged.flush();rewind();};
  $('defaults').onclick=()=>chooseMode(mode);
  $('timeline').oninput=()=>{conditionsChanged.flush();setRunning(false);t=Number($('timeline').value);render();$('play').textContent=t>=2?'↻ 再看一次':t>0?'▶ 继续实验':'▶ 同时出发';$('run-status').textContent=`回看 ${number(t)} s：两车使用同一时刻比较。`;};
  document.querySelectorAll('[data-prediction]').forEach(b=>b.onclick=()=>{
    prediction=b.dataset.prediction;
    document.querySelectorAll('[data-prediction]').forEach(item=>{item.classList.toggle('selected',item===b);item.setAttribute('aria-pressed',String(item===b));});
    $('prediction-note').textContent='已记录你的猜想。看速度的变化，再判断。';
    if(revealed) showFinding();
  });
  function showFinding() {
    if(!observed) return;
    revealed=true;$('finding').hidden=false;$('explain').hidden=true;
    const match=winner(),who=match==='same'?'两车的速度变化一样快':`${match.toUpperCase()} 车的速度变化更快`;
    let explanation='';
    if(mode==='force') explanation=`质量相同，${who}。增大合力，会增大每秒的速度变化量。`;
    else if(mode==='mass') explanation=`合力相同，${who}。质量越大，每秒的速度变化量越小。`;
    else if(params.fa===0&&params.fb===0) explanation=params.v0>0?'两车都在运动，但速度不变，所以加速度都为零。':'两车合力为零，初速度也为零，因此保持静止，加速度为零。';
    else explanation=`${who}。比较的关键是合力与总质量的比值 F/m。`;
    $('finding-text').textContent=explanation;
    renderFormula($('equation'),'a=\\frac{\\Delta v}{\\Delta t}=\\frac{F_{\\text{合}}}{m}',true);
    $('acceleration-values').textContent=`A：${number(aA)} m/s²　B：${number(aB)} m/s²`;
    $('finding-caveat').textContent=mode==='free'&&params.fa!==params.fb&&params.ma!==params.mb?'本轮同时改变了合力和质量，不能用它单独判断其中一个因素的影响。':'加速度比较的是速度变化的快慢，不是某一时刻谁的速度更大。';
    $('graph-note').textContent=match==='same'?'两条速度线重合：同样的时间内，速度增加相同，加速度相同。':'速度—时间图中，线越陡，同样时间内速度增加越多，加速度越大。';
    $('prediction-note').textContent=prediction?(prediction===match?'你的预测与本轮结果一致。':'本轮结果与预测不同。用速度增加量解释原因。'):'现在回看：比较同样时间里的速度增加量。';
  }
  $('explain').onclick=showFinding;
  const showLessonTop=()=>document.querySelector('.steps').scrollIntoView({block:'start',behavior:'instant'});
  $('next').onclick=()=>{chooseMode(mode==='force'?'mass':mode==='mass'?'free':'quiz');showLessonTop();};
  $('back-lab').onclick=()=>{chooseMode('free');showLessonTop();};
  const correct=[0,1,2],feedback=[
    '总质量不变，合力变为 2 倍，F/m 也变为 2 倍，所以加速度变为原来的 2 倍。',
    '新的比值是 2F/(2m)=F/m，所以加速度不变。合力更大时，还要看质量是否也改变了。',
    '“匀速”意味着速度没有变化，所以加速度为零。速度大，不能说明速度变化得快。'
  ];
  $('check-quiz').onclick=()=>{
    let score=0,answered=0;
    correct.forEach((answer,i)=>{
      const selected=document.querySelector(`input[name="q${i}"]:checked`),out=$('feedback-'+i);
      out.hidden=false;
      if(!selected){out.textContent='先选一个答案，再检查这个问题。';out.classList.add('wrong');return;}
      answered++;const ok=Number(selected.value)===answer;score+=Number(ok);
      out.classList.toggle('wrong',!ok);out.textContent=(ok?'判断正确。':'再想一想。')+feedback[i];
    });
    $('quiz-score').textContent=answered<3?`已回答 ${answered}/3 题，还有问题没有选择。`:`答对 ${score}/3 题`;
    $('takeaway').hidden=answered<3;
    if(answered===3) renderFormula($('final-equation'),'a=\\frac{F_{\\text{合}}}{m}',true);
  };
  document.querySelectorAll('#quiz input').forEach(input=>input.onchange=()=>{
    const i=input.name.slice(1);$('feedback-'+i).hidden=true;$('quiz-score').textContent='';$('takeaway').hidden=true;
  });
  $('reset-all').onclick=()=>{
    document.querySelectorAll('#quiz input').forEach(input=>input.checked=false);
    document.querySelectorAll('.feedback').forEach(el=>el.hidden=true);
    $('takeaway').hidden=true;$('quiz-score').textContent='';$('playback-speed').value='1';chooseMode('force');
    window.scrollTo({top:0,behavior:'instant'});
  };
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&running){setRunning(false);$('run-status').textContent='离开页面时已暂停，回来后可继续。';}});
  const videoData='{{VIDEO_DATA}}';
  if(videoData) {
    $('watch-video').hidden=false;
    let movieURL=null;
    $('watch-video').onclick=()=>{
      setRunning(false);
      if(!movieURL) {
        const binary=atob(videoData),bytes=new Uint8Array(binary.length);
        for(let i=0;i<binary.length;i++) bytes[i]=binary.charCodeAt(i);
        movieURL=URL.createObjectURL(new Blob([bytes],{type:'video/mp4'}));
        $('lesson-video').src=movieURL;
      }
      $('video-dialog').showModal();
      $('lesson-video').play().catch(()=>{});
    };
    $('close-video').onclick=()=>$('video-dialog').close();
    $('video-dialog').addEventListener('close',()=>$('lesson-video').pause());
    window.addEventListener('beforeunload',()=>{if(movieURL)URL.revokeObjectURL(movieURL);},{once:true});
  }
  chooseMode('force');
});
