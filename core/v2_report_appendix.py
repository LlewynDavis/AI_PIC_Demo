from pathlib import Path
from typing import Any, Dict


def _fmt(value, digits=4):
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def insert_v2_mode_section(
    report_path: Path,
    mode_result: Dict[str, Any],
) -> None:
    """在报告的工程运行补充说明之前插入 V2 模式求解分析。"""
    report_path = Path(report_path)

    if not report_path.exists():
        raise FileNotFoundError(f"未找到报告文件：{report_path}")

    mode_profile_result = mode_result.get("mode_profile_result", {})
    neff_sweep_result = mode_result.get("neff_sweep_result", {})

    mode_solver_type = mode_profile_result.get(
        "mode_solver_type",
        "finite_difference_scalar_mode_solver_v2_5",
    )
    waveguide_width_um = mode_profile_result.get("waveguide_width_um", "")
    waveguide_height_um = mode_profile_result.get("waveguide_height_um", "")
    wavelength_um = mode_profile_result.get("wavelength_um", "")
    estimated_neff = mode_profile_result.get("estimated_neff", "")
    confinement_factor = mode_profile_result.get("confinement_factor", "")
    mode_area_um2 = mode_profile_result.get("mode_area_um2", "")
    beta = mode_profile_result.get("beta", "")
    grid_size_x = mode_profile_result.get("grid_size_x", "")
    grid_size_y = mode_profile_result.get("grid_size_y", "")
    dx_um = mode_profile_result.get("dx_um", "")
    dy_um = mode_profile_result.get("dy_um", "")

    width_min_um = neff_sweep_result.get("width_min_um", "")
    width_max_um = neff_sweep_result.get("width_max_um", "")
    num_points = neff_sweep_result.get("num_points", "")

    section_lines = [
        "",
        "---",
        "",
        "## V2.5 有限差分模式求解模块分析",
        "",
        "### 1. 模块定位",
        "",
        "V2.5 版本在原有近似模式分析基础上，进一步引入二维标量有限差分模式求解。",
        "系统首先根据 SOI 材料参数和波导几何生成折射率截面 n(x,y)，随后离散标量 Helmholtz 方程并求解本征值问题，从而得到传播常数 β 和有效折射率 neff。",
        "该 neff 会被接入 MMI 宽度—长度二维优化流程，用于更新 MMI 初始长度和最终优化结果。",
        "",
        "需要说明的是，当前 V2.5 模式求解仍是标量有限差分近似，不是严格全矢量 FDE/FEM/EME 求解器。",
        "",
        "### 2. 模式求解输入参数",
        "",
        "| 参数 | 数值 |",
        "|---|---:|",
        f"| 模式求解类型 | {mode_solver_type} |",
        f"| 波导宽度 | {_fmt(waveguide_width_um, 4)} μm |",
        f"| 波导高度 | {_fmt(waveguide_height_um, 4)} μm |",
        f"| 工作波长 | {_fmt(wavelength_um, 4)} μm |",
        "",
        "### 3. SOI 波导折射率截面",
        "",
        "下图展示了当前 SOI 波导截面的折射率分布。高折射率区域对应 Si 波导核心，低折射率区域对应 SiO2 包层。",
        "",
        "![SOI 波导折射率截面](index_profile.png)",
        "",
        "该图用于说明模式求解模块的物理输入结构，即系统并非只处理抽象 neff 参数，而是进一步将材料参数和波导几何转换为截面折射率分布。",
        "",
        "### 4. 有限差分标量模式场分布",
        "",
        "下图为标量 Helmholtz 有限差分本征值问题求得的基模场强分布。颜色表示归一化光强，矩形框表示波导核心区域。",
        "",
        "![有限差分标量模式场分布](mode_profile.png)",
        "",
        "从图中可以看出，当前数值模式主要集中在波导核心附近，并向包层区域逐渐衰减。",
        "这符合 SOI 条形波导中基模场分布的基本物理直觉。",
        "",
        "### 5. neff 随波导宽度变化",
        "",
        "下图展示了在固定波导高度和工作波长条件下，有效折射率 neff 随波导宽度变化的趋势。",
        "",
        "![neff 随波导宽度变化曲线](neff_vs_width.png)",
        "",
        "| 参数 | 数值 |",
        "|---|---:|",
        f"| 宽度扫描下限 | {_fmt(width_min_um, 4)} μm |",
        f"| 宽度扫描上限 | {_fmt(width_max_um, 4)} μm |",
        f"| 扫描点数 | {num_points} |",
        f"| 当前设计使用 neff | {_fmt(estimated_neff, 4)} |",
        "",
        "曲线显示，随着波导宽度增大，模式约束增强，有效折射率整体上升。",
        "这说明 V2 模块已经能够体现波导横向尺寸变化对 neff 的影响。",
        "",
        "### 6. 模式分析结果",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 估算有效折射率 neff | {_fmt(estimated_neff, 4)} |",
        f"| 传播常数 β | {_fmt(beta, 4)} μm⁻¹ |",
        f"| 模式约束因子 | {_fmt(confinement_factor, 4)} |",
        f"| 模式面积 | {_fmt(mode_area_um2, 4)} μm² |",
        f"| 有限差分网格 | {grid_size_x} × {grid_size_y} |",
        f"| 网格步长 dx | {_fmt(dx_um, 4)} μm |",
        f"| 网格步长 dy | {_fmt(dy_um, 4)} μm |",
        "",
        "其中，模式约束因子用于近似表示光场能量集中在波导核心区域的比例；",
        "模式面积用于近似反映模式横向分布范围。",
        "",
        "### 7. 与 MMI 优化流程的连接",
        "",
        "V2.5 中，MMI 优化流程不再直接使用固定经验 neff，而是读取有限差分模式求解模块输出的 neff。",
        "该 neff 会影响 MMI 初始长度估算，并进一步影响宽度—长度二维扫描中的最优结构位置。",
        "",
        "因此，V2.5 已经形成如下自动化链路：",
        "",
        "```text",
        "SOI 材料参数",
        "→ 波导截面参数",
        "→ 标量 Helmholtz 有限差分本征模求解",
        "→ neff 提取",
        "→ MMI 宽度—长度二维优化",
        "→ GDS 版图生成",
        "→ 报告和结果包输出",
        "```",
        "",
        "后续若接入 FEMWELL、MPB、Lumerical MODE 或 COMSOL Mode Analysis，只需要替换当前模式求解模块的内部实现，主设计流程仍可保持不变。",
        "",
    ]

    section_text = "\n".join(section_lines)
    original_text = report_path.read_text(encoding="utf-8")

    marker = "\n## V2 工程运行补充说明"
    if marker in original_text:
        original_text = original_text.replace(marker, section_text + marker, 1)
    else:
        original_text += section_text

    original_text = original_text.replace(
        "AI 光子芯片设计平台 Demo V2：工程稳定版",
        "AI 光子芯片设计平台 Demo V2：模式求解版",
    )
    original_text = original_text.replace(
        "当前 V2 版本在验证“物理参数—器件建模—参数优化—版图生成”自动化链路的基础上，进一步增强了运行稳定性、结果追踪和工程交付能力。",
        "当前 V2 版本在验证“物理参数—器件建模—参数优化—版图生成”自动化链路的基础上，进一步加入近似 TE0 模式场分析、neff 宽度扫描和模式结果接入 MMI 优化流程。",
    )

    report_path.write_text(original_text, encoding="utf-8")
