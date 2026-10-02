# 互动实验实现规则

这是舍长工作台自写的规则与辅助代码接口，不复制第三方实验实现。源码档案独立提供；不要把 GPL/AGPL 实验拼进课件或把不明授权素材当成组件。已有器材仍用统一的 Open Lab Components。

## 操作与反馈

- 先明确学生要观察的关系。一个操作只改变预期的变量，画面、读数、单位、公式同步；实验中的简化假设须可见。
- 拖动必须保留抓取点偏移，不能按下后跳到鼠标中心。捕获指针，离开器材仍能继续；限制在实验区域内，取消操作恢复原位置。
- 只在接近有效位置时吸附，显示目标位置/连接状态；不要用吸附偷改自由实验的数值。触屏提供足够大的命中区域，键盘方向键可替代拖动。
- 连续输入合并到每帧一次。拖动整个器材时移动稳定外层的 transform，不反复重建器材内部节点；updateComponent 会重建，按需要限频或操作结束后更新。
- 仿真使用固定时间步长，显示用 requestAnimationFrame；暂停页签后不补算长时间积压。数值积分方法需符合模型，固定步长不等于科学准确。
- 暂停/继续保留当前状态，复位恢复所有控制变量、图形、测量值与轨迹。缩放窗口后重新计算边界，不让读数遮挡器材。装饰性过渡遵守 prefers-reduced-motion。
- 保持浅色青绿色工作台、统一器材和系统字体；反馈贴近操作对象。不要混入多个上游项目的皮肤，不用弹窗代替实时反馈。

## 内置辅助接口

在 head 中插入 `<!--TEACH_INTERACTION-->`，系统内联离线辅助代码。脚本在 DOM 就绪后调用：

`const draw = TeachInteraction.frame((value) => { /* 更新画面、读数 */ }); draw(value);`
只保留当前帧的最后一次调用；`draw.flush()` 立即完成，`draw.cancel()` 取消待更新。

`const handle = TeachInteraction.drag(element, {surface, read:()=>({x,y}), write:position=>{/* 同步模型和 transform */}, bounds:()=>({minX:0,minY:0,maxX:300,maxY:200}), snap:[{x:120,y:80}], radius:12, step:1, onCommit:position=>{/* 更新测量 */}});`
坐标为 surface 的局部坐标，SVG 支持 viewBox；CSS surface 应无旋转/倾斜变换。bounds 要扣除器材自身宽高。设置元素 aria-label 并展示键盘提示。`handle.cancel()` 取消当前拖动；复位时先取消再设置初始值；移除元素时 `handle.destroy()`。

`const sim = TeachInteraction.simulation({update:dt=>{/* 更新物理状态，dt单位秒 */}, render:alpha=>{/* 根据状态画图 */}, dt:1/120, maxSteps:12});`
显式调用 `sim.start()`；`sim.pause()` 暂停；`sim.reset(()=>{/* 重置完整模型 */})` 保持当前播放/暂停状态；`sim.destroy()` 释放监听器。显示时间从模型的 dt 累加，不从帧数估计。不需要连续仿真时不用这个循环。

## 参考依据

这些是行为层面的参考，具体快照提交与许可见相邻 catalog.json。

- myPhysicsLab：src/lab/app/SimController.ts 的抓取偏移与坐标转换，src/lab/app/SimRunner.ts 的仿真与绘制调度。
- Ray Optics：src/core/Editor.js 与对象混入逻辑中的命中、拖动、网格/方向约束。
- Concord Lab：atoms-interactions 的拖动状态与模型操作分离。
- VirtualChemLab：game_interaction、interaction_feedback 中的拖动光标与操作反馈。
- PhET Wave Interference：测量工具和实验画面的空间关系。这里只借鉴教学操作，不复用它的整套视觉皮肤。
