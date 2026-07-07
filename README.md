# AI_PIC_Demo

## 一、项目简介

AI_PIC_Demo 是一个基于 AI 思路的光子芯片自动化设计平台 Demo。项目当前以 SOI 平台 1×2 MMI 光功率分束器为示例，展示从自然语言需求输入、结构化参数解析、模式求解和 MMI 优化，到二维标量 BPM 传播验证、GDS 生成、Streamlit 网页展示、中文报告及结果打包的自动化流程。

本项目面向教学、原型验证和工程流程展示。计算结果可用于方案预研，但不能直接作为流片签核依据。

## 二、当前版本

当前 `dev` 分支开发版本：

```text
V3.2_port_mode_overlap
```

V3.2 在 V3.1 传播仿真校准基础上新增简化 Gaussian 输出端口模式，并将二维标量 BPM 最终复数场投影到端口模式上，以获得比简单窗口积分更具模式意识的输出功率估算。V3.0/V3.1 功能与输出继续保留。

## 三、当前版本主要功能

- 自然语言设计需求输入
- 结构化参数解析
- 参数合法性检查
- SOI 材料参数调用
- SOI 波导折射率截面生成
- 二维标量有限差分模式求解
- `neff_vs_width` 波导宽度扫描
- MMI 宽度—长度二维优化
- 波长扫描与带宽趋势分析
- MMI 区域二维标量 BPM 光场传播仿真
- `field_propagation.png` MMI 光场传播图
- `field_output_profile.png` 输出端横向强度分布
- `propagation_result.json` 传播仿真结构化结果
- 基于端口窗口积分估算 `p_out1`、`p_out2`、分光不均衡和插入损耗
- V3.1 输出窗口宽度敏感性分析
- V3.1 enhanced propagation plot
- Surrogate model 与 BPM model 对比
- Window-based insertion loss 解释与模型可信度校准
- 端口 Gaussian 模式构建与归一化
- BPM 输出复数场与端口模式重叠积分
- Overlap-based 输出端口功率、分光不均衡和等效插损估算
- Window integration 与 mode overlap integration 对比
- `mode_overlap_result.json` 模式重叠结构化结果
- `mode_overlap_comparison.png` 三类功率估算对比
- `field_output_profile_with_modes.png` 输出场与端口模式图
- GDS 版图及版图预览生成
- Streamlit 网页展示
- 中文设计报告生成
- 完整结果打包
- 本地输出目录安全清理
- GitHub 分支、tag、Release 和版本文档管理规范

## 四、项目结构

```text
AI_PIC_Demo/
├── README.md
├── CHANGELOG.md
├── VERSION
├── requirements.txt
├── .gitignore
├── app.py
├── run_demo.py
├── core/                 # 参数、模式、优化、扫描、报告与打包
├── layout/               # PDK、GDS 与版图预览
├── tools/                # 输出检查与清理工具
├── config/               # 非敏感配置说明或模板
├── docs/
│   └── versions/         # 历史版本说明，不复制历史源码
├── examples/
│   └── v2.5/             # 少量代表性展示结果说明
└── outputs/
    └── README.md          # 本地 run_* 结果不提交 GitHub
```

## 五、环境依赖

建议环境：

- Windows 10/11
- Python 3.11
- VS Code
- 项目内 `.venv` 虚拟环境

主要第三方依赖：

- `numpy`
- `scipy`
- `matplotlib`
- `pandas`
- `streamlit`
- `gdsfactory`
- `pydantic`

`pathlib`、`zipfile`、`json`、`shutil` 和 `argparse` 属于 Python 标准库，不需要写入 `requirements.txt`。

创建环境并安装依赖：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

在传统命令提示符中可使用：

```bat
.venv\Scripts\activate
```

## 六、命令行运行

```powershell
python run_demo.py
```

每次运行会创建独立结果目录：

```text
outputs/run_时间戳/
```

## 七、网页运行

```powershell
streamlit run app.py
```

如果当前终端找不到 `streamlit` 命令，也可以使用 `python -m streamlit run app.py`。启动成功后，在浏览器中打开终端显示的本地 Streamlit 地址，默认通常为 <http://localhost:8501>。Windows 用户也可使用 `start_demo.bat`。

## 八、主要输出文件

单次运行目录主要包含：

- `design_spec.json`
- `physical_params.json`
- `mode_result.json`
- `index_profile.png`
- `mode_profile.png`
- `neff_vs_width.png`
- `optimization_result.json`
- `wavelength_sweep_result.json`
- `wavelength_sweep.png`
- `wavelength_imbalance.png`
- `propagation_result.json`
- `field_propagation.png`
- `field_output_profile.png`
- `field_propagation_enhanced.png`
- `output_window_sensitivity.png`
- `output_window_sensitivity_result.json`
- `model_comparison.png`
- `model_comparison_result.json`
- `bpm_final_field_data.npz`
- `mode_overlap_result.json`
- `mode_overlap_comparison.png`
- `field_output_profile_with_modes.png`
- `length_sweep.png`
- `width_length_heatmap.png`
- `layout_preview.png`
- `mmi1x2_demo.gds`
- `report.md`
- `run_log.txt`
- `ai_pic_demo_results.zip`

## 九、输出清理

`outputs/run_*` 是本地运行结果，不建议提交到 GitHub。清理旧输出前可先查看 dry-run 计划：

```powershell
python tools/clean_outputs.py
python tools/clean_outputs.py --keep 3
```

确认计划后才执行实际删除：

```powershell
python tools/clean_outputs.py --keep 3 --apply
```

清理脚本不会删除 `outputs/` 目录本身或 `outputs/README.md`。

## 十、版本管理策略

- `main`：当前最新稳定版本
- `dev`：下一版本日常开发分支
- Git tag：保存重要历史版本节点
- GitHub Release：保存稳定版本发布说明和代表性附件
- `CHANGELOG.md`：记录完整版本变化
- `docs/versions/`：保存历史版本说明
- `examples/`：保存少量、清晰的代表性展示结果

`main` 中不创建 `V1/`、`V2/`、`V2.1/`、`V2.5/` 等完整历史源码副本。历史代码通过 Git tag 和 GitHub Release 查看。

## 十一、模型边界与局限性

- 当前模式求解是二维标量有限差分近似。
- V3.0 的 MMI 传播仿真是二维标量 BPM 近似。
- 当前版本不是严格的全矢量 FDE、FEM、EME 或 FDTD 仿真。
- MMI 响应模型仍是轻量 surrogate model。
- BPM 输出功率由简化端口窗口积分估算，不等同于严格端口模式重叠或 S 参数。
- V3.1 的 output power 仍是窗口积分估计。
- `window_based_insertion_loss_db` 不是严格器件插入损耗。
- Surrogate 与 BPM 的比较用于趋势分析，不是严格同一物理量的数值对比。
- V3.2 的输出端口模式是简化 Gaussian 近似。
- Overlap-based power 比窗口积分更接近端口模式功率提取，但仍不是严格全矢量本征模式 S 参数。
- 后续可将 Gaussian 模式替换为真实波导本征模式，或接入外部高保真仿真器结果。
- 所有优化和带宽趋势结果均应通过更高保真仿真或实验进一步验证。

## 十二、后续开发计划

- V3.5：宽带 S 参数趋势分析
- V4.0：PDK/DRC 工艺规则检查
- V5.0：AI Workflow / Agent 化设计流程

历史版本请查看 [CHANGELOG.md](CHANGELOG.md)、[docs/versions/](docs/versions/) 和仓库 Git tag。
