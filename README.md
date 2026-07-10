# AI_PIC_Demo

## Current Stable Version: V3.2_port_mode_overlap

AI_PIC_Demo 是一个基于 AI 思路的光子芯片自动化设计平台 Demo。项目以 SOI 平台 **1×2 MMI 光功率分束器**为例，展示从自然语言需求解析、参数建模、模式求解、MMI 优化、BPM 光场传播、端口模式重叠积分、GDS 版图生成、网页展示到报告输出的自动化流程。

当前 V3.2 在 V3.1 传播仿真校准的基础上，引入简化 Gaussian 输出端口模式，并将二维标量 BPM 的最终复数场投影到端口模式上。该版本的 overlap 总功率约为 0.843，overlap-based insertion loss 约为 0.74 dB；这些数值用于 Demo、趋势分析和流程验证，不代表流片签核结果。

## 主要功能

- 自然语言设计需求输入与结构化参数解析
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

## 主要输出文件

每次运行在 `outputs/run_时间戳/` 下生成独立结果目录，主要包括：

- `design_spec.json`、`physical_params.json`、`mode_result.json`
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
```

如果终端未识别 `streamlit`，可使用 `python -m streamlit run app.py`。网页默认地址通常为 <http://localhost:8501>。

## 模型边界

- V3.2 仍然是二维标量近似。
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
