# 当前状态

## 项目

- repository：`LlewynDavis/AI_PIC_Demo`
- canonical branch：`main`
- stable version：`V3.2_port_mode_overlap`
- repository visibility：`PUBLIC`
- collaboration protocol revision：`2`

当前精确 commit 必须从 GitHub `main` 或本地 `git rev-parse HEAD` 实时读取，不在本文档中维护自引用 commit。

## 已实现能力

- 自然语言设计需求解析与参数合法性检查。
- SOI 材料参数、二维标量有限差分模式求解和 `neff_vs_width` 扫描。
- MMI 宽度—长度优化、波长扫描和带宽趋势分析。
- 二维标量 BPM 传播、输出窗口敏感性和模型对比。
- 简化 Gaussian 端口模式重叠积分。
- GDS 版图、Streamlit 界面、中文报告和结果打包。

## 模型边界

- 当前 BPM 是二维标量近似，不是严格全矢量 FDTD、FEM 或 EME。
- Gaussian 输出端口模式是简化模型，不是真实波导本征模。
- 当前 overlap 指标适合 Demo、趋势分析和流程验证。
- 当前结果不是完整 S 参数，也不代表流片签核结果。

## 协作状态

- GitHub 工程事实源：已存在。
- 仓库级 Codex 规则：已建立。
- Google Drive 实时协作层：已建立。
- ChatGPT Project 项目指令：以 `CHATGPT_PROJECT_INSTRUCTIONS.md` 为准。
- 项目级自动对齐协调器：已建立，覆盖版本、工程、研究、网页、教学与文档任务。
- Obsidian 同步策略：仅选择性发布，默认不进入 GitHub。

## 状态更新规则

公开稳定状态写入本文件；实时 `base_commit`、任务状态、研究过程和往返验证结果写入私人 Drive。
