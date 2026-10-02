# 理化互动实验源码资源清单

整理日期：2026 年 10 月 2 日。

本清单收集支持拖动、搭建、测量、调整参数或按步骤操作的物理与化学实验项目，包含整套实验库、单项实验及开发框架。所有地址来自本次检索到的项目仓库或官方页面。

核查范围：已查看仓库页面和项目介绍，未逐个安装、运行或验证科学模型。公开源码不一定等于采用开源许可证；许可未确认或采用专有许可的项目已单独列出。

## 1. 优先选择

| 你的需求 | 建议优先查看 | 理由 |
| --- | --- | --- |
| 大量带步骤、仪器和测量的实验 | Virtual Labs | 按实验拆分仓库，便于按课程筛选 |
| 初高中理化互动实验 | PhET | 覆盖力学、电学、光学、热学和基础化学 |
| 自由摆放光源、透镜、反射镜 | Ray Optics | 支持搭建和修改光学场景 |
| 自由接线、修改电路和观察波形 | CircuitJS | 提供浏览器电路编辑与仿真 |
| 单摆、弹簧、碰撞等力学实验 | myPhysicsLab | 一个代码库包含约 50 种模拟 |
| 化学实验步骤和桌面交互 | VirtualChemLab、Virtual Chemistry Lab DEI | 可进一步筛选实验流程和器材操作实现 |
| 热力学、流体、反应器等大学内容 | LearnChemE | 按化工课程组织交互模拟 |

以上顺序是根据本次需求作出的筛选建议，不代表已完成运行质量评测。

## 2. 整套实验库与项目

### 2.1 Virtual Labs

- 内容：大学理工科虚拟实验，包含实验说明、步骤、模拟和测量等资源；各实验实现方式不同。
- 源码总入口：[Virtual Labs GitHub](https://github.com/virtual-labs)
- 特点：本次查看时组织页面显示三千多个仓库，其中也有平台、模板和维护工具，不能全部视作独立实验。
- 许可：需要查看具体仓库，软件与教学内容可能分别采用不同许可。
- 适合：批量寻找有仪器、有实验流程的源码。

### 2.2 PhET

- 内容：力学、电学、光学、热学、原子分子、溶液等互动模拟。
- 源码总入口：[PhET GitHub](https://github.com/phetsims)
- 官方源码说明：[Source Code](https://phet.colorado.edu/en/about/source-code)
- 技术：HTML5、JavaScript／TypeScript。
- 特点：实验通常各有独立仓库，同时依赖一套共享库；仅下载单个实验文件夹通常不足以运行。
- 许可：多数实验专属仓库采用 GPL，具体以目标仓库 LICENSE 为准。
- 适合：基础理化教学、中文化和交互实验改造。

### 2.3 myPhysicsLab

- 内容：单摆、双摆、弹簧、碰撞、台球、牛顿摆、过山车等。
- 操作：拖动物体、修改重力等参数，观察运动及图表。
- 源码：[myphysicslab/myphysicslab](https://github.com/myphysicslab/myphysicslab)
- 在线体验：[myPhysicsLab](https://myphysicslab.com/)
- 规模：仓库说明约有 50 种模拟。
- 技术：TypeScript，构建后在浏览器运行。
- 许可：Apache-2.0。

### 2.4 Ray Optics

- 内容：二维几何光学，光源、反射镜、透镜及其他光学元件。
- 操作：摆放和拖动元件、调整参数、观察光路、保存场景。
- 源码：[ricktu288/ray-optics](https://github.com/ricktu288/ray-optics)
- 在线体验：[Ray Optics Simulation](https://phydemo.app/ray-optics/)
- 技术：JavaScript 网页应用。
- 许可：Apache-2.0。
- 适合：凸透镜成像、反射折射和自由搭建光学实验。

### 2.5 CircuitJS

- 内容：电路搭建与实时仿真。
- 操作：连接元件、修改参数、观察电流、电压和波形。
- 源码：[sharpie7/circuitjs1](https://github.com/sharpie7/circuitjs1)
- 在线体验：[Falstad Circuit Simulator](https://www.falstad.com/circuit/)
- 技术：Java／GWT，编译后在浏览器运行。
- 许可：仓库标注 GPL-2.0。
- 备注：修改源码的构建流程涉及 Java／GWT，需要按项目说明配置。

### 2.6 LearnChemE

- 内容：热力学、传热、流体、反应动力学、反应器、物料与能量衡算等。
- 操作：以调整参数、观察过程与图表为主，具体体验因模拟而异。
- 源码：[LearnChemE/LearnChemE.github.io](https://github.com/LearnChemE/LearnChemE.github.io)
- 在线目录：[LearnChemE Simulations](https://learncheme.com/simulations/)
- 适合：大学化工、物理化学及工程原理教学。
- 许可：本次未确认整个仓库统一的开源许可，复用前核对目标内容的授权。

### 2.7 Concord Lab Framework

- 内容：科学模型、可视化、图表和传感器相关能力。
- 源码：[concord-consortium/lab](https://github.com/concord-consortium/lab)
- 示例入口：[Lab Framework](https://lab-framework.concord.org/)
- 技术：HTML5／JavaScript。
- 许可：MIT。
- 定位：开发框架，可用于构建自己的互动实验；不应直接当作完整的器材操作实验室。

### 2.8 Energy2D

- 内容：热传导、对流、辐射等热学交互模拟。
- 源码：[stepheneb/energy2d](https://github.com/stepheneb/energy2d)
- 项目页面：[Energy2D](https://energy2d.concord.org/)
- 技术：所列仓库为 Java 版本。
- 许可：LGPL-3.0。
- 备注：此链接是一个分支仓库，运行与构建需查看仓库说明。

### 2.9 Falstad RippleGL

- 内容：浏览器波纹水槽，研究波传播、干涉、衍射等现象。
- 源码：[pfalstad/ripplegl](https://github.com/pfalstad/ripplegl)
- 在线体验：[Ripple Tank](https://www.falstad.com/ripple/)
- 技术：GWT／WebGL。
- 许可：本次未单独核验许可文件。
- 适合：波动实验和课堂演示。

## 3. PhET 物理实验源码

下表均为具体实验仓库。运行方式和依赖见各自 README，通常可以从 README 的 Try it 链接进入在线版本。

| 实验 | 交互内容 | 源码地址 |
| --- | --- | --- |
| 直流电路 | 拖动电池、灯泡、电阻，接线并测量 | [circuit-construction-kit-dc](https://github.com/phetsims/circuit-construction-kit-dc) |
| 浮力 | 改变物体和液体条件，观察沉浮 | [buoyancy](https://github.com/phetsims/buoyancy) |
| 砝码与弹簧 | 挂砝码、调整条件、观察伸长与振动 | [masses-and-springs](https://github.com/phetsims/masses-and-springs) |
| 碰撞实验 | 调整碰撞条件，观察运动和动量 | [collision-lab](https://github.com/phetsims/collision-lab) |
| 光的折射 | 改变入射光和介质条件 | [bending-light](https://github.com/phetsims/bending-light) |
| 波的干涉 | 改变波源和障碍条件，观察干涉图样 | [wave-interference](https://github.com/phetsims/wave-interference) |
| 气体性质 | 调整气体条件，观察温度、压强等变化 | [gas-properties](https://github.com/phetsims/gas-properties) |

## 4. PhET 化学与物态模拟源码

这些项目包括溶液实验和原子分子模型操作，并非每个都是烧杯、试管式实验。

| 实验或模型 | 交互内容 | 源码地址 |
| --- | --- | --- |
| 酸碱溶液 | 改变酸碱强度和浓度，观察 pH 与导电性 | [acid-base-solutions](https://github.com/phetsims/acid-base-solutions) |
| 溶液浓度 | 添加溶质、加水、蒸发，观察浓度和饱和 | [concentration](https://github.com/phetsims/concentration) |
| pH 标度 | 选择液体、稀释和测量 pH | [ph-scale](https://github.com/phetsims/ph-scale) |
| 比尔定律实验 | 改变溶液与光学条件，观察吸光度 | [beers-law-lab](https://github.com/phetsims/beers-law-lab) |
| 物态变化 | 改变温度等条件，观察粒子和物态 | [states-of-matter](https://github.com/phetsims/states-of-matter) |
| 分子形状 | 调整分子模型，观察空间结构 | [molecule-shapes](https://github.com/phetsims/molecule-shapes) |
| 反应物、生成物与剩余物 | 改变配比，理解限量反应物 | [reactants-products-and-leftovers](https://github.com/phetsims/reactants-products-and-leftovers) |
| 搭建分子 | 拖动原子，组合分子 | [build-a-molecule](https://github.com/phetsims/build-a-molecule) |

## 5. Virtual Labs 单项实验源码

| 实验 | 主要内容 | 源码地址 |
| --- | --- | --- |
| 牛顿环 | 用牛顿环实验测定钠光波长 | [exp-newtons-ring-experiment-iitk](https://github.com/virtual-labs/exp-newtons-ring-experiment-iitk) |
| 单缝衍射 | 用单缝衍射测定氦氖激光波长 | [exp-single-slit-diffraction-iitk](https://github.com/virtual-labs/exp-single-slit-diffraction-iitk) |
| 复摆 | 测定重力加速度 | [exp-compound-pendulum-iitk](https://github.com/virtual-labs/exp-compound-pendulum-iitk) |
| 铜的电化学当量 | 电化学当量测定 | [exp-electrochemical-equivalent-of-copper-iitk](https://github.com/virtual-labs/exp-electrochemical-equivalent-of-copper-iitk) |
| 串联 LCR 电路 | 研究串联电路的谐振条件 | [exp-series-lcr-circuit-iitk](https://github.com/virtual-labs/exp-series-lcr-circuit-iitk) |

更多实验继续从 [Virtual Labs 仓库总入口](https://github.com/virtual-labs) 按课程或实验英文名称查找。上述仓库已确认存在，具体操作完整性需要运行后检查。

## 6. 化学实验室项目

### 6.1 Virtual Chemistry Lab DEI

- 内容：Virtual Labs 的化学实验室源码项目。
- 源码：[virtual-labs/virtual-chemistry-lab-dei](https://github.com/virtual-labs/virtual-chemistry-lab-dei)
- 许可：仓库说明软件采用 AGPL-3.0，内容采用 CC BY-NC-SA 4.0。
- 备注：软件与教学内容的许可不同；具体实验的运行兼容性尚未测试。

### 6.2 VirtualChemLab

- 内容：游戏化桌面化学实验，包含模板、步骤引导、交互、曲线生成与学习记录等。
- 源码：[qilaidev/virtual-chem-lab](https://github.com/qilaidev/virtual-chem-lab)
- 技术：Python＋PySide6／Qt6。
- 许可：MIT。
- 适合：本地桌面化学教学和实验流程训练。
- 备注：属于本次发现的社区项目，功能描述来自 README，尚未实测。

### 6.3 Virtua Chem Sim

- 内容：酸碱滴定、石蕊试纸测试、三维交互，以及音频、文字和测验。
- 源码：[sufyanaslam44/Virtua-Chem-Sim](https://github.com/sufyanaslam44/Virtua-Chem-Sim)
- 技术：Unity。
- 状态：源码公开，本次未确认明确的开源许可。
- 适合：研究三维化学实验的场景和操作实现。

### 6.4 bhoomika-254/virtual-lab

- 内容：酸碱滴定、高锰酸钾滴定、单摆和弹簧振动。
- 源码：[bhoomika-254/virtual-lab](https://github.com/bhoomika-254/virtual-lab)
- 技术：React／Node.js 等。
- 状态：源码公开，本次未确认明确的开源许可。
- 备注：功能来自项目说明，尚未验证模拟精度和可运行性。

### 6.5 OpenLabs

- 内容：包括虚拟滴定，提供滴定管、旋塞滴液、锥形瓶、实时 pH 曲线和颜色观察记录。
- 源码：[HackerYard/openlabs](https://github.com/HackerYard/openlabs)
- 技术：Web 应用，仓库提供本地开发说明。
- 状态：**公开源码，但 README 明确标注专有许可，不归入可自由复用的开源项目。**
- 用途：可作为功能和交互设计调研对象，代码使用范围需查看其 LICENSE。

## 7. 获取源码与开始使用

1. 打开对应 GitHub 仓库，查看 README 中的运行说明。
2. 使用 Code → Download ZIP 下载源码，或通过 Git 克隆仓库。
3. 区分源码和发布版：源码通常需要安装依赖或编译，发布版才可能直接运行。
4. PhET 需要共享依赖；CircuitJS 和 RippleGL 涉及 GWT；Unity 和桌面 Python 项目也各有运行环境。
5. 若要改造并发布，先看目标仓库的 LICENSE；未写明许可的公开仓库，不应视为已授予自由复用权限。

建议先从一个具体实验验证运行效果，再扩展成实验合集。按本次需求，优先试跑一个 PhET 实验、一个 Virtual Labs 实验和一个化学实验室项目，便于比较操作体验及改造成本。
