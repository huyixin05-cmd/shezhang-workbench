# 实验源码收录与使用

已核对原清单的 32 个具体仓库：27 个独立原始源码快照、5 个仅参考链接。快照总计 103,728,880 字节，6,508 个原始文件；这不是实验数量，也不表示这些实验已构建或接入。

## 怎么用

- 网页：设置 → 实验源码与参考。安装目录中也可以直接打开 `teach_agent/experiment_library/index.html`。
- WorkBuddy：说“找一下光学实验的源码”，通过 `list_experiment_resources` 查找；说“把 Ray Optics 源码导出来”，通过 `export_experiment_source` 保存到本地 exports。导出包附有来源与补充许可。
- 原始档案不会执行、不会自动进入课件。Java/GWT、Qt、PhET 共享库等按各自 README 准备，不随舍长工作台自动安装。
- 用户下载本项目能拿到快照和原许可。复用或另行分发时按每个上游许可处理，不能把独立 GPL/AGPL 项目统一改成 MIT。

## 已接入制作的能力

网页和 WorkBuddy 的互动制作都读取同一份 interaction-guide.md：抓取偏移、近距离吸附、指针捕获、触控/键盘替代、变量/读数同步、固定仿真步长、暂停恢复和完整复位。生成器可插入 TEACH_INTERACTION 标记获得内联辅助代码，离线 HTML 无需额外 JS 文件。检查报告记录规则和辅助脚本的哈希。

器材仍使用已有 Open Lab Components，参考实验的操作行为，不拼接各项目视觉风格。内置力与加速度示例已合并每帧更新，复位清除待更新和已揭晓答案，装饰过渡遵循减少动态效果设置。

## 逐项记录

| 项目 | 状态 / 根目录许可 | 运行要求或限制 |
| --- | --- | --- |
| [OpenLabs](https://github.com/hackeryard/openlabs) | 仅参考 / NOASSERTION | 专有许可明确不授予复制、修改或分发权；仅保留链接。 |
| [LearnChemE 模拟合集](https://github.com/LearnChemE/LearnChemE.github.io) | 仅参考 / 未确认 | 未找到整个仓库的统一开源授权；逐项授权待核实。 |
| [Virtual Lab 理化实验](https://github.com/bhoomika-254/virtual-lab) | 仅参考 / 未确认 | 未找到明确再分发许可；仅保留链接。 |
| [Concord 科学模型框架](https://github.com/concord-consortium/lab) | 源码已收录 / MIT | 按原始 README 安装构建工具；此处保存完整源码快照，未逐项构建验收。 |
| [myPhysicsLab 力学实验库](https://github.com/myphysicslab/myphysicslab) | 源码已收录 / Apache-2.0 | 按原始 README 安装构建工具；此处保存完整源码快照，未逐项构建验收。 |
| [RippleGL 波纹水槽](https://github.com/pfalstad/ripplegl) | 源码已收录 / GPL-2.0-or-later | Java/GWT 源码，需编译成网页；未在本项目构建。 |
| [酸碱溶液](https://github.com/phetsims/acid-base-solutions) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [比尔定律](https://github.com/phetsims/beers-law-lab) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [光的折射](https://github.com/phetsims/bending-light) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [搭建分子](https://github.com/phetsims/build-a-molecule) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [浮力](https://github.com/phetsims/buoyancy) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [直流电路](https://github.com/phetsims/circuit-construction-kit-dc) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [碰撞实验](https://github.com/phetsims/collision-lab) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [溶液浓度](https://github.com/phetsims/concentration) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [气体性质](https://github.com/phetsims/gas-properties) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [砝码与弹簧](https://github.com/phetsims/masses-and-springs) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [分子形状](https://github.com/phetsims/molecule-shapes) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [pH 标度](https://github.com/phetsims/ph-scale) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [反应物与剩余物](https://github.com/phetsims/reactants-products-and-leftovers) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [物态变化](https://github.com/phetsims/states-of-matter) | 源码已收录 / GPL-3.0 | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [波的干涉](https://github.com/phetsims/wave-interference) | 源码已收录 / MIT | 独立实验源码；需按 README 获取 PhET 共享库与 Node 构建环境，不能仅双击源码 HTML。 |
| [VirtualChemLab 化学实验室](https://github.com/qilaidev/virtual-chem-lab) | 源码已收录 / MIT | Python + PySide6/Qt6 桌面程序，按上游 README 安装；不是网页组件。 |
| [Ray Optics 光学搭建](https://github.com/ricktu288/ray-optics) | 源码已收录 / Apache-2.0 | 按原始 README 安装构建工具；此处保存完整源码快照，未逐项构建验收。 |
| [CircuitJS 电路搭建](https://github.com/sharpie7/circuitjs1) | 源码已收录 / GPL-2.0 | Java/GWT 源码，需编译成网页；未在本项目构建。 |
| [Energy2D 热学（Java）](https://github.com/stepheneb/energy2d) | 源码已收录 / LGPL-3.0 | Java 源码；需 Java/上游构建工具，不是浏览器运行版。 |
| [Virtua Chem Sim（Unity）](https://github.com/sufyanaslam44/Virtua-Chem-Sim) | 仅参考 / 未确认 | 未找到明确再分发许可；仅保留链接。 |
| [复摆实验](https://github.com/virtual-labs/exp-compound-pendulum-iitk) | 源码已收录 / AGPL-3.0 | 按实验源码的 HTML 和资源结构运行，第三方依赖与教学内容许可需分别核对。 |
| [铜的电化学当量](https://github.com/virtual-labs/exp-electrochemical-equivalent-of-copper-iitk) | 源码已收录 / AGPL-3.0 | 按实验源码的 HTML 和资源结构运行，第三方依赖与教学内容许可需分别核对。 |
| [牛顿环](https://github.com/virtual-labs/exp-newtons-ring-experiment-iitk) | 源码已收录 / AGPL-3.0 | 按实验源码的 HTML 和资源结构运行，第三方依赖与教学内容许可需分别核对。 |
| [串联 LCR 电路](https://github.com/virtual-labs/exp-series-lcr-circuit-iitk) | 源码已收录 / AGPL-3.0 | 按实验源码的 HTML 和资源结构运行，第三方依赖与教学内容许可需分别核对。 |
| [单缝衍射](https://github.com/virtual-labs/exp-single-slit-diffraction-iitk) | 源码已收录 / AGPL-3.0 | 按实验源码的 HTML 和资源结构运行，第三方依赖与教学内容许可需分别核对。 |
| [Virtual Chemistry Lab DEI](https://github.com/virtual-labs/virtual-chemistry-lab-dei) | 仅参考 / NOASSERTION | 软件 AGPL-3.0、教学内容 CC BY-NC-SA 4.0，旧实验内容与代码未逐项拆分核对；本次不整包收录。 |

完整固定提交、原始 ZIP 哈希和许可文件清单见 `teach_agent/experiment_library/catalog.json`。GPL 等上游文件保持原字节；ZIP 自带嵌套许可证。Virtual Labs 的五个档案另外标明教学内容 CC BY-NC-SA 4.0 政策；VirtualChemLab 的商业激活文档随原档案保留，不承诺桌面版本开箱即用。

## 验证范围

已检查源码快照哈希、导出许可、工具发现与导出、两个入口共同使用的生成规则，以及独立浏览器文件中的缩放 SVG 拖动/吸附/越界/取消/键盘操作和更新调度。未逐一构建第三方实验，未验证所有设备的帧率，未用真实模型评估新规则的教学效果。
