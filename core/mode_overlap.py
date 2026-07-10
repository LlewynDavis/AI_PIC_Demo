import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def _integrate(values: np.ndarray, x_um: np.ndarray) -> complex:
    """兼容不同 NumPy 版本的一维数值积分。"""
    trapezoid = getattr(np, "trapezoid", None)
    if trapezoid is None:
        trapezoid = getattr(np, "trapz")
    return trapezoid(values, x_um)


def _result_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [result]
    for key in ("best_result", "result"):
        nested = result.get(key)
        if isinstance(nested, dict):
            candidates.append(nested)
    return candidates


def _read_float(
    result: dict[str, Any],
    keys: tuple[str, ...],
    default: float | None = None,
) -> float:
    for candidate in _result_candidates(result):
        for key in keys:
            value = candidate.get(key)
            if value is not None:
                return float(value)
    if default is not None:
        return float(default)
    raise KeyError(f"未找到兼容字段：{', '.join(keys)}")


def build_output_port_mode(
    x_um: np.ndarray,
    center_um: float,
    mode_width_um: float,
) -> np.ndarray:
    """构建并归一化简化 Gaussian 输出端口模式。"""
    x_um = np.asarray(x_um, dtype=float)
    if x_um.ndim != 1 or x_um.size < 2:
        raise ValueError("x_um 必须是至少包含两个点的一维数组。")
    if mode_width_um <= 0:
        raise ValueError("mode_width_um 必须为正数。")

    mode_field = np.exp(-((x_um - center_um) / mode_width_um) ** 2).astype(
        np.complex128
    )
    mode_power = float(np.real(_integrate(np.abs(mode_field) ** 2, x_um)))
    if not np.isfinite(mode_power) or mode_power <= 0:
        raise ValueError("输出端口模式归一化失败。")
    return mode_field / np.sqrt(mode_power)


def compute_mode_overlap_power(
    x_um: np.ndarray,
    output_field: np.ndarray,
    port_mode: np.ndarray,
    input_power: float = 1.0,
    eps: float = 1e-12,
) -> float:
    """计算复数输出场投影到归一化端口模式后的功率。"""
    x_um = np.asarray(x_um, dtype=float)
    output_field = np.asarray(output_field, dtype=np.complex128)
    port_mode = np.asarray(port_mode, dtype=np.complex128)
    if output_field.shape != x_um.shape or port_mode.shape != x_um.shape:
        raise ValueError("输出场、端口模式和横向网格的形状必须一致。")
    if input_power <= eps:
        raise ValueError("input_power 必须为正数。")

    mode_power = float(np.real(_integrate(np.abs(port_mode) ** 2, x_um)))
    if not np.isfinite(mode_power) or mode_power <= eps:
        raise ValueError("端口模式功率为零，无法计算重叠积分。")
    overlap = _integrate(output_field * np.conjugate(port_mode), x_um)
    power = float(np.abs(overlap) ** 2 / (input_power * mode_power))
    return max(power, 0.0)


def save_mode_overlap_comparison_plot(
    result: dict[str, Any],
    surrogate_result: dict[str, float],
    output_path: Path,
) -> Path:
    """比较 surrogate、窗口积分和模式重叠三类输出功率。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    reference = result["window_based_reference"]
    labels = ["Output 1", "Output 2", "Total power"]
    series = [
        (
            "Surrogate model",
            [
                surrogate_result["p_out1"],
                surrogate_result["p_out2"],
                surrogate_result["total_power"],
            ],
            "tab:blue",
        ),
        (
            "BPM window integration",
            [
                reference["p_out1"],
                reference["p_out2"],
                reference["total_collected_power"],
            ],
            "tab:orange",
        ),
        (
            "BPM mode overlap",
            [
                result["overlap_p_out1"],
                result["overlap_p_out2"],
                result["total_overlap_power"],
            ],
            "tab:green",
        ),
    ]
    positions = np.arange(len(labels), dtype=float)
    bar_width = 0.24
    figure, axis = plt.subplots(figsize=(8.6, 4.8))
    for index, (name, values, color) in enumerate(series):
        axis.bar(
            positions + (index - 1) * bar_width,
            values,
            width=bar_width,
            label=name,
            color=color,
        )
    axis.set_title("V3.2 Port Mode Overlap Power Comparison")
    axis.set_xlabel("Power metric")
    axis.set_ylabel("Normalized power")
    axis.set_xticks(positions, labels)
    axis.set_ylim(bottom=0)
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def save_field_output_profile_with_modes_plot(
    x_um: np.ndarray,
    output_field: np.ndarray,
    output1_mode: np.ndarray,
    output2_mode: np.ndarray,
    output1_center_um: float,
    output2_center_um: float,
    port_mode_width_um: float,
    output_path: Path,
) -> Path:
    """展示 BPM 输出强度和两个 Gaussian 端口模式。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    intensity = np.abs(output_field) ** 2
    normalized_intensity = intensity / max(float(np.max(intensity)), 1e-12)
    mode1_amplitude = np.abs(output1_mode)
    mode2_amplitude = np.abs(output2_mode)
    mode1_amplitude /= max(float(np.max(mode1_amplitude)), 1e-12)
    mode2_amplitude /= max(float(np.max(mode2_amplitude)), 1e-12)

    figure, axis = plt.subplots(figsize=(8.8, 4.8))
    axis.plot(
        x_um,
        normalized_intensity,
        color="black",
        linewidth=2.0,
        label="BPM output intensity",
    )
    axis.plot(
        x_um,
        mode1_amplitude,
        color="tab:blue",
        linestyle="--",
        label="Output 1 Gaussian mode",
    )
    axis.plot(
        x_um,
        mode2_amplitude,
        color="tab:orange",
        linestyle="--",
        label="Output 2 Gaussian mode",
    )
    axis.axvline(output1_center_um, color="tab:blue", alpha=0.6)
    axis.axvline(output2_center_um, color="tab:orange", alpha=0.6)
    axis.set_title(
        f"V3.2 BPM Output Field and Port Modes (width={port_mode_width_um:.3f} um)"
    )
    axis.set_xlabel("Lateral direction x (um)")
    axis.set_ylabel("Normalized intensity / mode amplitude")
    axis.set_ylim(bottom=0)
    axis.grid(alpha=0.25)
    axis.legend(loc="upper right")
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def run_mode_overlap_analysis(
    design_spec: dict[str, Any],
    optimization_result: dict[str, Any],
    mode_result: dict[str, Any],
    propagation_result: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """运行 V3.2 简化 Gaussian 输出端口模式重叠分析。"""
    del mode_result  # 保留接口，供后续替换为真实本征模式。
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data_name = str(
        propagation_result.get(
            "bpm_final_field_data_npz",
            "bpm_final_field_data.npz",
        )
    )
    data_path = Path(data_name)
    if not data_path.is_absolute():
        data_path = output_dir / data_path
    if not data_path.exists():
        raise FileNotFoundError(f"未找到 BPM 最终复数场数据：{data_path}")

    with np.load(data_path) as data:
        x_um = np.asarray(data["x_um"], dtype=float)
        output_field = np.asarray(data["final_field_real"], dtype=float) + 1j * np.asarray(
            data["final_field_imag"], dtype=float
        )

    mmi_width_um = float(propagation_result["mmi_width_um"])
    mmi_length_um = float(propagation_result["mmi_length_um"])
    output1_center_um = float(propagation_result["output1_center_um"])
    output2_center_um = float(propagation_result["output2_center_um"])
    port_mode_width_um = float(max(0.35, mmi_width_um * 0.12))
    output1_mode = build_output_port_mode(
        x_um=x_um,
        center_um=output1_center_um,
        mode_width_um=port_mode_width_um,
    )
    output2_mode = build_output_port_mode(
        x_um=x_um,
        center_um=output2_center_um,
        mode_width_um=port_mode_width_um,
    )
    overlap_p_out1 = compute_mode_overlap_power(
        x_um=x_um,
        output_field=output_field,
        port_mode=output1_mode,
    )
    overlap_p_out2 = compute_mode_overlap_power(
        x_um=x_um,
        output_field=output_field,
        port_mode=output2_mode,
    )
    total_overlap_power = overlap_p_out1 + overlap_p_out2
    eps = 1e-12
    overlap_imbalance_db = float(
        10 * np.log10(max(overlap_p_out1, eps) / max(overlap_p_out2, eps))
    )
    overlap_based_insertion_loss_db = float(
        -10 * np.log10(max(total_overlap_power, eps))
    )

    window_p_out1 = float(propagation_result["p_out1"])
    window_p_out2 = float(propagation_result["p_out2"])
    window_total = float(propagation_result["total_collected_power"])
    surrogate_p_out1 = _read_float(
        optimization_result,
        ("p_out1", "output_port_1"),
    )
    surrogate_p_out2 = _read_float(
        optimization_result,
        ("p_out2", "output_port_2"),
    )
    surrogate_result = {
        "p_out1": surrogate_p_out1,
        "p_out2": surrogate_p_out2,
        "total_power": surrogate_p_out1 + surrogate_p_out2,
    }

    result: dict[str, Any] = {
        "analysis_type": "port_mode_overlap",
        "version": "V3.2_port_mode_overlap",
        "model_level": (
            "2D scalar BPM field with simplified Gaussian port-mode overlap"
        ),
        "wavelength_um": float(design_spec["wavelength_um"]),
        "mmi_width_um": mmi_width_um,
        "mmi_length_um": mmi_length_um,
        "output1_center_um": output1_center_um,
        "output2_center_um": output2_center_um,
        "port_mode_width_um": port_mode_width_um,
        "overlap_p_out1": overlap_p_out1,
        "overlap_p_out2": overlap_p_out2,
        "total_overlap_power": total_overlap_power,
        "overlap_imbalance_db": overlap_imbalance_db,
        "overlap_based_insertion_loss_db": overlap_based_insertion_loss_db,
        "window_based_reference": {
            "output_window_um": float(propagation_result["output_window_um"]),
            "p_out1": window_p_out1,
            "p_out2": window_p_out2,
            "total_collected_power": window_total,
            "window_based_insertion_loss_db": float(
                propagation_result.get(
                    "window_based_insertion_loss_db",
                    -10 * math.log10(max(window_total, eps)),
                )
            ),
        },
        "interpretation": (
            "The overlap-based power is estimated by projecting the BPM output "
            "field onto simplified Gaussian port modes. It is more mode-aware "
            "than simple spatial window integration, but still not equivalent "
            "to full-vector eigenmode S-parameter extraction."
        ),
        "limitations": [
            "The port modes are simplified Gaussian approximations.",
            "The BPM field is a 2D scalar approximation.",
            (
                "This is not a full-vector eigenmode expansion or FDTD/FEM/EME "
                "S-parameter extraction."
            ),
        ],
    }

    result_path = output_dir / "mode_overlap_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    comparison_path = save_mode_overlap_comparison_plot(
        result=result,
        surrogate_result=surrogate_result,
        output_path=output_dir / "mode_overlap_comparison.png",
    )
    profile_path = save_field_output_profile_with_modes_plot(
        x_um=x_um,
        output_field=output_field,
        output1_mode=output1_mode,
        output2_mode=output2_mode,
        output1_center_um=output1_center_um,
        output2_center_um=output2_center_um,
        port_mode_width_um=port_mode_width_um,
        output_path=output_dir / "field_output_profile_with_modes.png",
    )
    result.update(
        {
            "mode_overlap_result_path": str(result_path),
            "mode_overlap_comparison_path": str(comparison_path),
            "field_output_profile_with_modes_path": str(profile_path),
            "bpm_final_field_data_path": str(data_path),
        }
    )
    return result
