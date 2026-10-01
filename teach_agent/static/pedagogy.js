'use strict';
const designLabels = {
  request_analysis:'这次要解决的教学问题', student_problem:'这个知识点哪里难理解',
  difficulty_reason:'为什么这里容易卡住', design_response:'用什么讲解或互动解决',
  success_evidence:'学生最后应能解释或解决什么'
};
const stepLabels = {title:'这一步的名称',question:'要解决的小问题',explanation:'讲解什么',
  action:'学生做什么 · 或观察什么镜头',observation:'应看到什么证据',takeaway:'应理解什么',check:'怎样检查理解 · 判断依据'};
function teachingField(key,label,value,step=false){
  const wrapper=document.createElement('label');wrapper.textContent=label;
  const input=document.createElement(key==='title'?'input':'textarea');input.dataset.teachingField=key;
  input.value=value||'';input.required=true;input.maxLength=key==='title'?120:1200;
  if(step)input.dataset.stepField=key;
  wrapper.append(input);return wrapper;
}
function teachingSelect(key,label,options,value){
  const wrapper=document.createElement('label');wrapper.textContent=label;
  const input=document.createElement('select');input.dataset.teachingField=key;
  for(const [val,text] of options){const option=document.createElement('option');option.value=val;option.textContent=text;input.append(option);}
  input.value=value;wrapper.append(input);return wrapper;
}
function readTeachingSequence(){return [...document.querySelectorAll('#teaching-sequence .teaching-step')].map(card=>
  Object.fromEntries([...card.querySelectorAll('[data-teaching-field]')].map(el=>[el.dataset.teachingField,el.value.trim()])));}
function renderTeachingSequence(sequence){
  const root=document.getElementById('teaching-sequence');root.replaceChildren();
  sequence.forEach((step,index)=>{
    const card=document.createElement('section');card.className='teaching-step';
    const heading=document.createElement('div');heading.className='panel-heading';
    const title=document.createElement('h3');title.textContent='第 '+(index+1)+' 步';heading.append(title);
    const actions=document.createElement('div');actions.className='step-actions';
    for(const [label,delta] of [['上移',-1],['下移',1],['删除',0]]){
      const button=document.createElement('button');button.type='button';button.textContent=label;
      button.setAttribute('aria-label',label+'第'+(index+1)+'步');
      button.disabled=delta===0?sequence.length<=2:index+delta<0||index+delta>=sequence.length;
      button.onclick=()=>{const next=readTeachingSequence();if(delta===0)next.splice(index,1);
        else [next[index],next[index+delta]]=[next[index+delta],next[index]];renderTeachingSequence(next);};
      actions.append(button);
    }
    heading.append(actions);card.append(heading);
    card.append(teachingSelect('flow','讲解与操作的先后',[
      ['act_then_explain','先预测 / 操作观察 → 再解释'],['explain_then_act','先给必要讲解 → 再尝试验证']],step.flow||'act_then_explain'));
    const fields=document.createElement('div');fields.className='form-grid';
    for(const [key,label] of Object.entries(stepLabels))fields.append(teachingField(key,label,step[key],true));
    card.append(fields);root.append(card);
  });
  document.getElementById('add-teaching-step').disabled=sequence.length>=8;
}
function showTeachingDesign(design){
  const root=document.getElementById('learning-design');root.hidden=!design;
  document.getElementById('legacy-design-note').hidden=Boolean(design);
  const oldSteps=document.querySelector('[name="steps"]');oldSteps.closest('label').hidden=Boolean(design);oldSteps.disabled=Boolean(design);
  document.getElementById('design-fields').replaceChildren();document.getElementById('teaching-sequence').replaceChildren();
  if(!design)return;
  const fields=document.getElementById('design-fields');
  for(const [key,label] of Object.entries(designLabels))fields.append(teachingField(key,label,design[key]));
  renderTeachingSequence(design.sequence);
}
function readTeachingDesign(){
  const root=document.getElementById('learning-design');if(root.hidden)return null;
  const result=Object.fromEntries([...document.querySelectorAll('#design-fields [data-teaching-field]')].map(el=>[el.dataset.teachingField,el.value.trim()]));
  result.sequence=readTeachingSequence();return result;
}
document.getElementById('add-teaching-step').onclick=()=>{
  const sequence=readTeachingSequence();if(sequence.length<8){sequence.push({flow:'act_then_explain'});renderTeachingSequence(sequence);}
};
