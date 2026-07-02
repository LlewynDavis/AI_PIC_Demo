# AI_PIC_Demo

AI_PIC_Demo 是一个基于 AI 思路的光子芯片自动化设计平台 Demo，当前版本为 **V2.1**。项目以 **1×2 MMI 光功率分束器**为示例器件，展示从自然语言需求到参数解析、物理近似建模、优化、GDS 版图、报告和结果打包的完整流程。

> 注意：本项目用于教学、原型验证与流程展示。当前计算结果不能直接作为流片依据。

## 当前能力

- 自然语言需求输入
- 结构化设计参数解析
- SOI 材料参数库
- 近似 TE0 模式求解
- neff 随波导宽度扫描
- MMI 宽度—长度二维优化
- GDS 版图生成
- Streamlit 网页展示
- 中文报告生成
- 结果打包输出

## 当前限制

- 当前模式求解仍是近似模型，不是真实 FDE、FEM 或 EME 求解器。
- MMI 响应模型仍是轻量 surrogate model（代理模型）。
- 后续可接入 FEMWELL、MPB、Lumerical MODE、COMSOL、Meep、Tidy3D 等工具，以获得更高保真的模式与电磁仿真能力。

## 运行方法

推荐环境：Windows 10/11、Python 3.11、PowerShell 或 VS Code。

### 1. 创建并激活虚拟环境

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. 运行命令行 Demo

```powershell
python run_demo.py
```

### 4. 运行 Streamlit 网页

```powershell
python -m streamlit run app.py
```

网页默认地址为 <http://localhost:8501>。Windows 用户也可以双击 `start_demo.bat` 启动。

运行结果保存在 `outputs/` 目录中。带时间戳的单次运行目录默认不会提交到 Git。

## 项目结构

```text
AI_PIC_Demo/
├── core/             # 参数解析、物理模型、模式求解、优化、报告与打包
├── layout/           # GDS 与版图预览生成
├── tools/            # 辅助检查工具
├── outputs/          # 运行结果与说明
├── app.py            # Streamlit 网页入口
├── run_demo.py       # 命令行入口
└── requirements.txt  # Python 依赖
```

## 版本记录

- **V0**：命令行最小闭环
- **V1**：物理建模增强版
- **V1.5**：工程稳定版
- **V2**：模式求解版
- **V2.1**：网页展示增强版

详细变更见 [CHANGELOG.md](CHANGELOG.md)。
