# AI_PIC_Demo

## Current Version: V3.3_designspec_mcp_foundation

AI_PIC_Demo 是一个基于 AI 思路的光子芯片自动化设计平台 Demo。项目以 SOI 平台 **1×2 MMI 光功率分束器**为例，展示从自然语言需求解析、参数建模、模式求解、MMI 优化、BPM 光场传播、端口模式重叠积分、GDS 版图生成、网页展示到报告输出的自动化流程。

当前 V3.3 在不改变 V3.2 物理算法和既有基准结果的前提下，引入版本化 PIC DesignSpec、Pydantic 校验、单位归一化、需求澄清状态、阶段错误码、Prompt Benchmark，以及无需外部 API 密钥的最小本地 MCP Server/Client。V3.2 的二维标量有限差分模式求解、MMI 优化、二维标量 BPM 和简化 Gaussian overlap 仍作为物理基线。

## 主要功能

- 自然语言设计需求输入与结构化参数解析
- PIC DesignSpec 1.0 与参数来源追踪
- `needs_clarification` 需求澄清状态
- 参数合法性检查
- SOI 材料参数库
- 二维标量有限差分模式求解
- `neff_vs_width` 扫描
- MMI 宽度—长度二维优化
- 波长扫描与带宽趋势分析
- 二维标量 BPM 光场传播仿真
- 输出窗口宽度敏感性分析
- surrogate model 与 BPM model 对比
- 简化 Gaussian 端口模式重叠积分
- GDS 版图生成
- Streamlit 科研仿真工作台
- 中文报告与结果打包
- `run_manifest.json` / `status.json` 阶段状态
- 本地 MCP 工具：DesignSpec 校验、MMI 初值估算、最近运行检查
- 30 条需求 Prompt Benchmark

## 主要输出文件

每次运行在 `outputs/run_时间戳/` 下生成独立结果目录，主要包括：

- `design_spec.json`、`run_manifest.json`、`status.json`
- `physical_params.json`、`mode_result.json`
- `index_profile.png`、`mode_profile.png`、`neff_vs_width.png`
- `optimization_result.json`
- `wavelength_sweep_result.json`、`wavelength_sweep.png`、`wavelength_imbalance.png`
- `propagation_result.json`、`field_propagation.png`、`field_output_profile.png`
- `field_propagation_enhanced.png`
- `output_window_sensitivity.png`、`output_window_sensitivity_result.json`
- `model_comparison.png`、`model_comparison_result.json`
- `bpm_final_field_data.npz`
- `mode_overlap_result.json`、`mode_overlap_comparison.png`
- `field_output_profile_with_modes.png`
- `layout_preview.png`、`mmi1x2_demo.gds`
- `report.md`、`ai_pic_demo_results.zip`

## 运行

推荐环境：Windows 10/11、Python 3.11、VS Code，以及项目内 `.venv` 虚拟环境。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python run_demo.py
streamlit run app.py
python tools/check_latest_run.py
python -m unittest discover -s tests -v
python tools/run_prompt_benchmark.py
python tools/pic_mcp_client.py --smoke-test
```

如果终端未识别 `streamlit`，可使用 `python -m streamlit run app.py`。网页默认地址通常为 <http://localhost:8501>。

## 模型边界

- V3.3 没有提高 V3.2 物理模型的电磁精度。
- 当前模式和传播计算仍然是二维标量近似。
- BPM 不是严格全矢量 FDTD、FEM 或 EME。
- Gaussian port mode 是简化端口模式。
- overlap-based power 比窗口积分更合理，但仍不是严格全矢量本征模式 S 参数。
- 当前结果适合 Demo、趋势分析和流程验证，不是流片签核级仿真结果。

## 版本管理与结果组织

- `main`：当前最新稳定版。
- `dev`：后续开发分支；当前暂停开发时与 `main` 保持一致。
- Git tag：保存重要历史版本节点。
- `docs/versions/`：保存版本说明。
- `examples/`：保存少量代表性结果。
- `outputs/`：保存本地运行输出；不提交大量 `run_*` 目录。

历史版本与变更请查看 [CHANGELOG.md](CHANGELOG.md)、[docs/versions/](docs/versions/) 和 Git tag。

## 建议学习重点

- MMI 自成像原理
- SOI 波导模式
- 有限差分模式求解
- BPM 光束传播法
- 端口模式重叠积分
- 插入损耗与分光不均衡
- GDS 版图与 PDK 基础

## ChatGPT 与 Codex 协作

本项目使用 GitHub 作为工程事实源，使用私人 Google Drive 作为实时协作与任务交接层。ChatGPT 负责研究和评审，Codex 负责实施和验证，Obsidian 知识库只做选择性发布。

项目级自动协调器负责发现双方新增或更新的对话、复用现有专用对话、同步完整上下文、核对 `base_commit`、路由已批准任务和回写验证证据。自动对齐不改变事实源，也不会把未批准建议直接当作工程任务执行。

协作规则、状态、决策、交接格式和 ChatGPT Project 指令见 [`docs/collab/`](docs/collab/README.md)。

## V3.3 工程资料

- DesignSpec JSON 示例：[`config/v3.3_design_spec.example.json`](config/v3.3_design_spec.example.json)
- DesignSpec YAML 示例：[`config/v3.3_design_spec.example.yaml`](config/v3.3_design_spec.example.yaml)
- V3.3 版本说明：[`docs/versions/v3.3.md`](docs/versions/v3.3.md)
- V3.3 验证记录：[`docs/verification/v3.3.md`](docs/verification/v3.3.md)
- 后续工程路线：[`docs/ROADMAP.md`](docs/ROADMAP.md)
- Benchmark 数据：[`benchmarks/v3.3/requirements.jsonl`](benchmarks/v3.3/requirements.jsonl)

V3.3 的结构化设计思想参考 Sharma 等人在 2025 年发表的 PhIDO 工作，但本项目只采用可公开复现的 Schema、工具边界和评测思路；没有实现论文中的完整 RAG、多 Agent 或高保真求解器体系。
