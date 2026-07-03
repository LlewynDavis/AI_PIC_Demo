from pathlib import Path
from typing import Any, Dict


def _fmt(value, digits=4):
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def insert_v23_wavelength_section(
    report_path: Path,
    wavelength_sweep_result: Dict[str, Any],
) -> None:
    """在报告末尾的工程运行说明之前插入 V2.5 波长扫描章节。"""
    report_path = Path(report_path)
    if not report_path.exists():
        raise FileNotFoundError(f"未找到报告文件：{report_path}")

    section_lines = [
        "",
        "---",
        "",
        "## V2.5 波长扫描与带宽趋势分析",
        "",
        "### 1. 分析目的",
        "",
        "V2.5 在有限差分模式求解与波导截面展示基础上，进一步增加模型一致的波长扫描分析。",
        "该功能用于观察当前最优 MMI 结构在不同工作波长下的输出功率、插入损耗和分光不均衡变化趋势。",
        "",
        "各波长 neff 来自 V2.5 标量有限差分求解器；MMI 响应仍为轻量替代模型，不是真实宽带 FDTD/FEM/EME 仿真结果。",
        "",
        "### 2. 扫描设置",
        "",
        "| 参数 | 数值 |",
        "|---|---:|",
        (
            "| 波长扫描范围 | "
            f"{_fmt(wavelength_sweep_result.get('wavelength_min_um'))}–"
            f"{_fmt(wavelength_sweep_result.get('wavelength_max_um'))} μm |"
        ),
        f"| 扫描点数 | {wavelength_sweep_result.get('num_points')} |",
        (
            "| 固定 MMI 宽度 | "
            f"{_fmt(wavelength_sweep_result.get('best_width_um'))} μm |"
        ),
        (
            "| 固定 MMI 长度 | "
            f"{_fmt(wavelength_sweep_result.get('best_length_um'))} μm |"
        ),
        "",
        "### 3. 输出功率随波长变化",
        "",
        "下图展示了两个输出端口归一化功率随波长变化的趋势。",
        "",
        "![波长扫描输出功率](wavelength_sweep.png)",
        "",
        "### 4. 分光不均衡随波长变化",
        "",
        "下图展示了分光不均衡随波长变化的趋势。",
        "",
        "![波长扫描分光不均衡](wavelength_imbalance.png)",
        "",
        "### 5. 关键结果",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        (
            "| 中心波长 | "
            f"{_fmt(wavelength_sweep_result.get('center_wavelength_um'))} μm |"
        ),
        (
            "| 中心波长 Output port 1 | "
            f"{_fmt(wavelength_sweep_result.get('center_output_port_1'))} |"
        ),
        (
            "| 中心波长 Output port 2 | "
            f"{_fmt(wavelength_sweep_result.get('center_output_port_2'))} |"
        ),
        (
            "| 扫描范围最大绝对不均衡 | "
            f"{_fmt(wavelength_sweep_result.get('max_abs_imbalance_db'))} dB |"
        ),
        (
            "| 扫描范围平均绝对不均衡 | "
            f"{_fmt(wavelength_sweep_result.get('mean_abs_imbalance_db'))} dB |"
        ),
        (
            "| 扫描范围最大插入损耗 | "
            f"{_fmt(wavelength_sweep_result.get('max_insertion_loss_db'))} dB |"
        ),
        "",
        "### 6. 工程意义",
        "",
        "V2.5 使平台从单一中心波长设计，扩展到模型一致的初步宽带性能趋势分析。",
        "后续若接入真实电磁仿真器，该模块可以进一步升级为真实宽带 S 参数扫描和带宽评估。",
        "",
    ]

    section_text = "\n".join(section_lines)
    original_text = report_path.read_text(encoding="utf-8")

    engineering_markers = [
        "\n## V2.5 工程运行补充说明",
        "\n## V2.3 工程运行补充说明",
        "\n## V2 工程运行补充说明",
    ]
    for marker in engineering_markers:
        if marker in original_text:
            original_text = original_text.replace(marker, section_text + marker, 1)
            break
    else:
        original_text += section_text

    report_path.write_text(original_text, encoding="utf-8")
