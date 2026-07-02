from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


def _get_value(spec: Any, key: str, default=None):
    """
    兼容 dict 和 pydantic/dataclass 对象的取值方式。
    """
    if isinstance(spec, dict):
        return spec.get(key, default)
    return getattr(spec, key, default)


def _get_range(spec: Any, key: str, default: Tuple[float, float]):
    value = _get_value(spec, key, default)

    if value is None:
        return default

    if isinstance(value, (list, tuple)) and len(value) == 2:
        return float(value[0]), float(value[1])

    return default


def validate_design_spec(spec: Any) -> ValidationResult:
    """
    对设计输入参数进行合法性检查。

    当前 V1.5 主要用于防止以下问题：
    1. 输入参数不合理导致优化失败；
    2. GDS 生成时出现几何尺寸错误；
    3. Streamlit 网页因异常输入直接崩溃；
    4. 后续真实模式求解时参数越界。
    """

    errors: List[str] = []
    warnings: List[str] = []

    wavelength_um = float(_get_value(spec, "wavelength_um", 1.55))
    neff = float(_get_value(spec, "neff", 2.8))
    waveguide_width_um = float(_get_value(spec, "waveguide_width_um", 0.5))
    waveguide_height_um = float(_get_value(spec, "waveguide_height_um", 0.22))
    mmi_width_um = float(_get_value(spec, "mmi_width_um", 2.5))
    num_scan_points = int(_get_value(spec, "num_scan_points", 200))

    length_min, length_max = _get_range(
        spec,
        "length_scan_range_um",
        (3.0, 20.0),
    )

    width_min, width_max = _get_range(
        spec,
        "mmi_width_scan_range_um",
        (2.0, 4.0),
    )

    target_split_ratio = _get_value(spec, "target_split_ratio", [0.5, 0.5])

    # 基础数值检查
    if wavelength_um <= 0:
        errors.append("工作波长 wavelength_um 必须大于 0。")

    if neff <= 1.0:
        errors.append("有效折射率 neff 应大于 1.0。")

    if waveguide_width_um <= 0:
        errors.append("波导宽度 waveguide_width_um 必须大于 0。")

    if waveguide_height_um <= 0:
        errors.append("波导高度 waveguide_height_um 必须大于 0。")

    if mmi_width_um <= 0:
        errors.append("MMI 宽度 mmi_width_um 必须大于 0。")

    # 长度扫描范围检查
    if length_max <= length_min:
        errors.append("MMI 长度扫描范围错误：最大长度必须大于最小长度。")

    if length_min <= 0:
        errors.append("MMI 最小扫描长度必须大于 0。")

    # 宽度扫描范围检查
    if width_max <= width_min:
        errors.append("MMI 宽度扫描范围错误：最大宽度必须大于最小宽度。")

    if width_min <= 0:
        errors.append("MMI 最小扫描宽度必须大于 0。")

    # 结构尺寸合理性检查
    if waveguide_width_um >= mmi_width_um:
        errors.append("波导宽度不能大于或等于 MMI 宽度。")

    if waveguide_width_um >= width_min:
        warnings.append(
            "波导宽度接近或超过 MMI 宽度扫描下限，建议适当增大 MMI 宽度扫描范围。"
        )

    if mmi_width_um < 1.5:
        warnings.append("当前 MMI 宽度偏小，可能不适合作为典型 SOI 1×2 MMI 结构。")

    if waveguide_width_um < 0.3:
        warnings.append("当前波导宽度偏小，可能导致模式约束较弱。")

    if waveguide_width_um > 0.8:
        warnings.append("当前波导宽度偏大，可能不符合常见 220 nm SOI 单模波导设计。")

    # 扫描点数检查
    if num_scan_points < 20:
        errors.append("扫描点数 num_scan_points 过低，建议不小于 20。")

    if num_scan_points < 80:
        warnings.append("扫描点数偏少，优化结果可能不够平滑。")

    if num_scan_points > 1000:
        warnings.append("扫描点数较大，运行时间和图像生成时间可能增加。")

    # 分光比检查
    if not isinstance(target_split_ratio, (list, tuple)) or len(target_split_ratio) != 2:
        errors.append("目标分光比 target_split_ratio 应为长度为 2 的列表，例如 [0.5, 0.5]。")
    else:
        r1 = float(target_split_ratio[0])
        r2 = float(target_split_ratio[1])
        ratio_sum = r1 + r2

        if r1 <= 0 or r2 <= 0:
            errors.append("目标分光比中的两个数值都必须大于 0。")

        if abs(ratio_sum - 1.0) > 1e-6:
            warnings.append("目标分光比之和不等于 1，系统后续可考虑自动归一化处理。")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validation_result_to_text(result: ValidationResult) -> str:
    """
    将参数检查结果转换为可写入日志或报告的文本。
    """

    lines = []

    if result.is_valid:
        lines.append("参数合法性检查：通过。")
    else:
        lines.append("参数合法性检查：未通过。")

    if result.errors:
        lines.append("")
        lines.append("错误信息：")
        for item in result.errors:
            lines.append(f"- {item}")

    if result.warnings:
        lines.append("")
        lines.append("警告信息：")
        for item in result.warnings:
            lines.append(f"- {item}")

    return "\n".join(lines)
