# AI_PIC_Demo

AI_PIC_Demo 是一个面向教学、原型验证和工程流程展示的 SOI 光子芯片自动化设计 Demo。项目以 **1×2 MMI 光功率分束器**为示例，串联自然语言需求输入、结构化参数解析与校验、模式近似求解、参数扫描与优化、GDS 生成、网页展示、中文报告及结果打包。

当前稳定版本为 **V2.5**。V2.6 的工作范围是工程清理与 GitHub 同步准备，不改变 V2.5 已跑通的核心算法和使用方式。

> 本项目的计算结果适合教学与方案预研，不可直接作为流片签核依据。

## 主要能力

- 自然语言设计需求输入、结构化参数解析与参数校验
- SOI 波导折射率截面生成
- 二维标量有限差分模式求解、模式场图和有效折射率 `neff`
- `neff_vs_width` 波导宽度扫描
- MMI 宽度—长度二维优化及热力图
- 波长扫描、输出功率和分光不均衡曲线
- 1×2 MMI GDS 版图与预览图生成
- Streamlit 网页展示
- 中文设计报告与 ZIP 结果包

## 安装与运行

推荐使用 Windows 10/11、Python 3.11 和 PowerShell。

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

运行命令行 Demo：

```powershell
python run_demo.py
```

启动 Streamlit 网页：

```powershell
python -m streamlit run app.py
```

网页默认地址为 <http://localhost:8501>。Windows 用户也可双击 `start_demo.bat` 启动。

## 输出文件

每次命令行或网页运行会在 `outputs/run_时间戳/` 下生成一组结果，主要包括：

- `design_spec.json`：结构化设计参数
- `physical_params.json`：材料与物理参数
- `mode_result.json`：模式求解结果
- `index_profile.png`、`mode_profile.png`、`neff_vs_width.png`：折射率截面、模式场和宽度扫描
- `optimization_result.json`、`length_sweep.png`、`width_length_heatmap.png`：MMI 优化结果
- `wavelength_sweep_result.json`、`wavelength_sweep.png`、`wavelength_imbalance.png`：波长扫描结果
- `layout_preview.png`、`mmi1x2_demo.gds`：版图预览和 GDS 文件
- `report.md`、`run_log.txt`、`ai_pic_demo_results.zip`：中文报告、日志和结果包

`outputs/run_*` 和 `outputs/*.zip` 是本地生成物，默认不提交 Git。清理旧运行目录前可先预览计划：

```powershell
python tools/clean_outputs.py
```

## 模型局限

V2.5 使用的是**二维标量有限差分近似**，不是严格的全矢量 FDE，也不是 FEM、EME 或 FDTD 电磁求解器。当前 MMI 响应与优化流程同样包含简化模型，因此结果应通过更高保真工具及实验数据进一步验证。

## 项目结构

```text
AI_PIC_Demo/
├── core/              # 参数解析、求解、扫描、优化、报告与打包
├── layout/            # GDS 与版图预览生成
├── tools/             # 结果检查与清理工具
├── outputs/           # 本地运行结果（run_* 默认忽略）
├── examples/          # 人工挑选的关键版本展示结果
├── archive/           # 历史备份与临时测试脚本
├── app.py             # Streamlit 网页入口
├── run_demo.py        # 命令行入口
└── requirements.txt   # Python 依赖
```

详细版本变化见 [CHANGELOG.md](CHANGELOG.md)。
