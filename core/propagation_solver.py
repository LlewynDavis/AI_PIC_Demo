import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def build_mmi_propagation_grid(
    wavelength_um: float,
    mmi_width_um: float,
    mmi_length_um: float,
    x_span_um: float,
    nx: int,
    nz: int,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """构建 MMI 区域的 x-z 标量传播网格。"""
    if wavelength_um <= 0 or mmi_width_um <= 0 or mmi_length_um <= 0:
        raise ValueError("波长、MMI 宽度和 MMI 长度必须为正数。")
    if x_span_um <= mmi_width_um:
        raise ValueError("x_span_um 必须大于 MMI 宽度。")
    if nx < 32 or nz < 2:
        raise ValueError("传播网格至少需要 nx >= 32 且 nz >= 2。")

    x_um = np.linspace(-x_span_um / 2, x_span_um / 2, int(nx))
    z_um = np.linspace(0.0, mmi_length_um, int(nz))
    dx_um = float(x_um[1] - x_um[0])
    dz_um = float(z_um[1] - z_um[0])
    return x_um, z_um, dx_um, dz_um


def build_lateral_index_profile(
    x_um: np.ndarray,
    mmi_width_um: float,
    core_neff: float,
    cladding_neff: float,
) -> np.ndarray:
    """构建 MMI 宽度方向的等效折射率分布。"""
    if core_neff <= cladding_neff:
        raise ValueError("core_neff 必须大于 cladding_neff。")
    if mmi_width_um <= 0:
        raise ValueError("MMI 宽度必须为正数。")

    n_x = np.full_like(x_um, float(cladding_neff), dtype=float)
    n_x[np.abs(x_um) <= mmi_width_um / 2] = float(core_neff)
    return n_x


def build_input_field(
    x_um: np.ndarray,
    input_width_um: float,
    center_um: float = 0.0,
) -> np.ndarray:
    """构建并按总功率归一化 Gaussian 输入场。"""
    if input_width_um <= 0:
        raise ValueError("输入场宽度必须为正数。")

    field_x = np.exp(-((x_um - center_um) / input_width_um) ** 2).astype(
        complex
    )
    power = float(np.trapezoid(np.abs(field_x) ** 2, x_um))
    if power <= 0:
        raise ValueError("输入场归一化失败。")
    return field_x / np.sqrt(power)


def _build_absorbing_window(x_um: np.ndarray) -> np.ndarray:
    """在横向网格外缘构建平滑吸收窗，减少 FFT 周期边界反射。"""
    half_span = float(np.max(np.abs(x_um)))
    absorption_start = 0.82 * half_span
    normalized_edge = np.clip(
        (np.abs(x_um) - absorption_start) / (half_span - absorption_start),
        0.0,
        1.0,
    )
    return np.exp(-0.08 * normalized_edge**2)


def propagate_scalar_bpm(
    wavelength_um: float,
    x_um: np.ndarray,
    z_um: np.ndarray,
    n_x: np.ndarray,
    input_field: np.ndarray,
    reference_neff: float,
) -> tuple[np.ndarray, np.ndarray]:
    """使用 split-step Fourier 方法执行二维 x-z 标量 BPM 传播。"""
    if wavelength_um <= 0 or reference_neff <= 0:
        raise ValueError("波长和参考有效折射率必须为正数。")
    if x_um.ndim != 1 or z_um.ndim != 1:
        raise ValueError("x_um 和 z_um 必须是一维数组。")
    if n_x.shape != x_um.shape or input_field.shape != x_um.shape:
        raise ValueError("折射率、输入场与横向网格的形状必须一致。")
    if z_um.size < 2:
        raise ValueError("z 方向至少需要两个网格点。")

    dx_um = float(x_um[1] - x_um[0])
    dz_um = float(z_um[1] - z_um[0])
    k0 = 2 * np.pi / wavelength_um
    kx = 2 * np.pi * np.fft.fftfreq(x_um.size, d=dx_um)

    diffraction_operator = np.exp(
        -1j * (kx**2) * dz_um / (2 * k0 * reference_neff)
    )
    index_phase_half_step = np.exp(
        1j
        * k0
        * (n_x**2 - reference_neff**2)
        * dz_um
        / (4 * reference_neff)
    )
    absorbing_window = _build_absorbing_window(x_um)

    field_map_complex = np.empty(
        (z_um.size, x_um.size),
        dtype=np.complex128,
    )
    field = np.asarray(input_field, dtype=np.complex128).copy()
    field_map_complex[0] = field

    for z_index in range(1, z_um.size):
        field *= index_phase_half_step
        field = np.fft.ifft(np.fft.fft(field) * diffraction_operator)
        field *= index_phase_half_step
        field *= absorbing_window
        field_map_complex[z_index] = field

    intensity_map = np.abs(field_map_complex) ** 2
    return field_map_complex, intensity_map


def estimate_output_powers(
    x_um: np.ndarray,
    output_field: np.ndarray,
    output_separation_um: float,
    output_window_um: float,
    eps: float = 1e-12,
) -> dict[str, float]:
    """通过两个输出端口窗口的强度积分估算归一化功率。"""
    if output_separation_um <= 0 or output_window_um <= 0:
        raise ValueError("输出端口间距和积分窗口必须为正数。")

    intensity = np.abs(output_field) ** 2
    output1_center_um = -output_separation_um / 2
    output2_center_um = output_separation_um / 2
    half_window = output_window_um / 2

    mask1 = np.abs(x_um - output1_center_um) <= half_window
    mask2 = np.abs(x_um - output2_center_um) <= half_window
    if np.count_nonzero(mask1) < 2 or np.count_nonzero(mask2) < 2:
        raise ValueError("输出端口积分窗口内的横向网格点不足。")

    p_out1 = float(np.trapezoid(intensity[mask1], x_um[mask1]))
    p_out2 = float(np.trapezoid(intensity[mask2], x_um[mask2]))
    total_collected_power = p_out1 + p_out2
    imbalance_db = float(
        10 * np.log10(max(p_out1, eps) / max(p_out2, eps))
    )
    insertion_loss_db = float(-10 * np.log10(max(total_collected_power, eps)))

    return {
        "output1_center_um": output1_center_um,
        "output2_center_um": output2_center_um,
        "p_out1": p_out1,
        "p_out2": p_out2,
        "total_collected_power": total_collected_power,
        "imbalance_db": imbalance_db,
        "insertion_loss_db": insertion_loss_db,
    }


def save_field_propagation_plot(
    x_um: np.ndarray,
    z_um: np.ndarray,
    intensity_map: np.ndarray,
    output_path: Path,
) -> Path:
    """保存 MMI 区域二维光场传播强度图。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(9, 4.8))
    image = axis.imshow(
        intensity_map.T,
        extent=[z_um[0], z_um[-1], x_um[0], x_um[-1]],
        origin="lower",
        aspect="auto",
        cmap="inferno",
        interpolation="nearest",
    )
    axis.set_title("V3.0 Scalar BPM Field Propagation")
    axis.set_xlabel("Propagation direction z (um)")
    axis.set_ylabel("Lateral direction x (um)")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Intensity |E|²")
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def save_field_output_profile_plot(
    x_um: np.ndarray,
    output_field: np.ndarray,
    output1_center_um: float,
    output2_center_um: float,
    output_window_um: float,
    output_path: Path,
) -> Path:
    """保存最终传播位置的横向归一化强度分布图。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    intensity = np.abs(output_field) ** 2
    normalized_intensity = intensity / max(float(np.max(intensity)), 1e-12)
    half_window = output_window_um / 2

    figure, axis = plt.subplots(figsize=(8.5, 4.5))
    axis.plot(x_um, normalized_intensity, color="navy", linewidth=1.8)
    axis.axvspan(
        output1_center_um - half_window,
        output1_center_um + half_window,
        color="tab:blue",
        alpha=0.18,
        label="Output 1 integration window",
    )
    axis.axvspan(
        output2_center_um - half_window,
        output2_center_um + half_window,
        color="tab:orange",
        alpha=0.18,
        label="Output 2 integration window",
    )
    axis.axvline(output1_center_um, color="tab:blue", linestyle="--")
    axis.axvline(output2_center_um, color="tab:orange", linestyle="--")
    axis.set_title("V3.0 BPM Output Intensity Profile")
    axis.set_xlabel("Lateral direction x (um)")
    axis.set_ylabel("Normalized intensity")
    axis.set_ylim(bottom=0)
    axis.grid(alpha=0.25)
    axis.legend(loc="upper right")
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def save_output_window_sensitivity_plot(
    window_results: list[dict[str, float]],
    output_path: Path,
) -> Path:
    """保存输出端口积分窗口宽度敏感性曲线。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    window_widths = [item["output_window_um"] for item in window_results]
    p_out1_values = [item["p_out1"] for item in window_results]
    p_out2_values = [item["p_out2"] for item in window_results]
    total_values = [item["total_collected_power"] for item in window_results]

    figure, axis = plt.subplots(figsize=(8.2, 4.8))
    axis.plot(
        window_widths,
        total_values,
        marker="o",
        linewidth=2.0,
        color="black",
        label="Total collected power",
    )
    axis.plot(
        window_widths,
        p_out1_values,
        marker="s",
        linewidth=1.5,
        color="tab:blue",
        label="Output 1",
    )
    axis.plot(
        window_widths,
        p_out2_values,
        marker="^",
        linewidth=1.5,
        color="tab:orange",
        label="Output 2",
    )
    axis.set_title("V3.1 Output Window Sensitivity")
    axis.set_xlabel("Output window width (um)")
    axis.set_ylabel("Collected power")
    axis.set_ylim(bottom=0)
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def run_output_window_sensitivity_analysis(
    wavelength_um: float,
    mmi_width_um: float,
    mmi_length_um: float,
    x_um: np.ndarray,
    output_field: np.ndarray,
    output_separation_um: float,
    default_output_window_um: float,
    output_dir: Path,
    window_widths_um: tuple[float, ...] = (0.25, 0.35, 0.45, 0.55, 0.70),
) -> dict[str, Any]:
    """分析输出端口窗口宽度对窗口积分功率的影响。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    max_window_um = 0.8 * output_separation_um
    candidate_windows = [
        min(float(window), max_window_um)
        for window in (*window_widths_um, default_output_window_um)
        if float(window) > 0
    ]
    valid_windows = sorted(
        {
            round(window, 8)
            for window in candidate_windows
            if window > 0 and window <= max_window_um + 1e-12
        }
    )
    if not valid_windows:
        raise ValueError("没有可用的输出窗口宽度。")

    window_results: list[dict[str, float]] = []
    for output_window_um in valid_windows:
        power_result = estimate_output_powers(
            x_um=x_um,
            output_field=output_field,
            output_separation_um=output_separation_um,
            output_window_um=output_window_um,
        )
        window_results.append(
            {
                "output_window_um": output_window_um,
                "p_out1": power_result["p_out1"],
                "p_out2": power_result["p_out2"],
                "total_collected_power": power_result[
                    "total_collected_power"
                ],
                "imbalance_db": power_result["imbalance_db"],
                "window_based_insertion_loss_db": power_result[
                    "insertion_loss_db"
                ],
            }
        )

    result: dict[str, Any] = {
        "analysis_type": "output_window_sensitivity",
        "version": "V3.1_propagation_calibration",
        "wavelength_um": wavelength_um,
        "mmi_width_um": mmi_width_um,
        "mmi_length_um": mmi_length_um,
        "output_separation_um": output_separation_um,
        "output1_center_um": -output_separation_um / 2,
        "output2_center_um": output_separation_um / 2,
        "default_output_window_um": default_output_window_um,
        "maximum_nonoverlap_window_um": max_window_um,
        "window_results": window_results,
        "interpretation": (
            "The collected power depends on the selected output integration "
            "window. This is a window-based estimation, not a strict "
            "mode-overlap S-parameter extraction."
        ),
        "limitations": [
            "The output power is estimated by simple spatial window integration.",
            "The result is sensitive to output_window_um.",
            "This is not equivalent to a full-vector mode-overlap calculation.",
        ],
    }

    result_path = output_dir / "output_window_sensitivity_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    plot_path = save_output_window_sensitivity_plot(
        window_results=window_results,
        output_path=output_dir / "output_window_sensitivity.png",
    )
    result.update(
        {
            "output_window_sensitivity_result_path": str(result_path),
            "output_window_sensitivity_plot_path": str(plot_path),
        }
    )
    return result


def save_field_propagation_enhanced_plot(
    x_um: np.ndarray,
    z_um: np.ndarray,
    intensity_map: np.ndarray,
    mmi_width_um: float,
    output1_center_um: float,
    output2_center_um: float,
    output_path: Path,
) -> Path:
    """保存带动态范围裁剪和结构标记的增强传播图。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_intensity = intensity_map / max(
        float(np.max(intensity_map)),
        1e-12,
    )
    intensity_db = 10 * np.log10(np.maximum(normalized_intensity, 1e-6))
    intensity_db = np.clip(intensity_db, -35.0, 0.0)

    figure, axis = plt.subplots(figsize=(9.2, 4.8))
    image = axis.imshow(
        intensity_db.T,
        extent=[z_um[0], z_um[-1], x_um[0], x_um[-1]],
        origin="lower",
        aspect="auto",
        cmap="viridis",
        vmin=-35.0,
        vmax=0.0,
        interpolation="nearest",
    )
    axis.axhline(
        mmi_width_um / 2,
        color="white",
        linewidth=1.0,
        linestyle="--",
        alpha=0.85,
        label="MMI boundaries",
    )
    axis.axhline(
        -mmi_width_um / 2,
        color="white",
        linewidth=1.0,
        linestyle="--",
        alpha=0.85,
    )
    axis.axvline(
        z_um[-1],
        color="red",
        linewidth=1.2,
        linestyle=":",
        label="MMI output plane",
    )
    axis.scatter(
        [z_um[-1], z_um[-1]],
        [output1_center_um, output2_center_um],
        color="red",
        marker="x",
        s=45,
        label="Output centers",
        zorder=5,
    )
    axis.set_title("V3.1 Enhanced Scalar BPM Field Propagation")
    axis.set_xlabel("Propagation direction z (um)")
    axis.set_ylabel("Lateral direction x (um)")
    axis.legend(loc="upper right")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Normalized intensity (dB)")
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _extract_mode_neff(mode_result: dict[str, Any]) -> float:
    """兼容 V2.5 模式结果结构并提取传播参考 neff。"""
    candidates = [
        mode_result.get("neff_used_for_mmi"),
        mode_result.get("mode_profile_result", {}).get("estimated_neff"),
        mode_result.get("estimated_neff"),
    ]
    for value in candidates:
        if value is not None and float(value) > 0:
            return float(value)
    raise ValueError("mode_result 中未找到有效 neff。")


def run_propagation_analysis(
    design_spec: dict[str, Any],
    optimization_result: dict[str, Any],
    mode_result: dict[str, Any],
    output_dir: Path,
    nx: int = 512,
    nz: int = 321,
) -> dict[str, Any]:
    """运行 V3.0 MMI 区域二维标量 BPM 传播分析。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wavelength_um = float(design_spec["wavelength_um"])
    mmi_width_um = float(
        optimization_result.get(
            "best_mmi_width_um",
            optimization_result["best_width_um"],
        )
    )
    mmi_length_um = float(
        optimization_result.get(
            "best_mmi_length_um",
            optimization_result["best_length_um"],
        )
    )
    reference_neff = _extract_mode_neff(mode_result)
    core_neff = reference_neff
    cladding_neff = float(
        mode_result.get("index_profile_result", {}).get("cladding_index", 1.44)
    )
    if cladding_neff >= core_neff:
        cladding_neff = max(1.0, core_neff - 0.1)

    output_separation_um = float(
        optimization_result.get(
            "output_separation_um",
            design_spec.get("output_separation_um", mmi_width_um / 2),
        )
    )
    output_window_um = float(max(0.35, mmi_width_um * 0.12))
    x_span_um = float(
        max(
            6.0,
            mmi_width_um * 2.4,
            output_separation_um + 4 * output_window_um,
        )
    )

    x_um, z_um, dx_um, dz_um = build_mmi_propagation_grid(
        wavelength_um=wavelength_um,
        mmi_width_um=mmi_width_um,
        mmi_length_um=mmi_length_um,
        x_span_um=x_span_um,
        nx=nx,
        nz=nz,
    )
    n_x = build_lateral_index_profile(
        x_um=x_um,
        mmi_width_um=mmi_width_um,
        core_neff=core_neff,
        cladding_neff=cladding_neff,
    )
    input_field = build_input_field(
        x_um=x_um,
        input_width_um=float(design_spec.get("waveguide_width_um", 0.5)),
    )
    field_map_complex, intensity_map = propagate_scalar_bpm(
        wavelength_um=wavelength_um,
        x_um=x_um,
        z_um=z_um,
        n_x=n_x,
        input_field=input_field,
        reference_neff=reference_neff,
    )
    power_result = estimate_output_powers(
        x_um=x_um,
        output_field=field_map_complex[-1],
        output_separation_um=output_separation_um,
        output_window_um=output_window_um,
    )

    propagation_plot_path = save_field_propagation_plot(
        x_um=x_um,
        z_um=z_um,
        intensity_map=intensity_map,
        output_path=output_dir / "field_propagation.png",
    )
    output_profile_plot_path = save_field_output_profile_plot(
        x_um=x_um,
        output_field=field_map_complex[-1],
        output1_center_um=power_result["output1_center_um"],
        output2_center_um=power_result["output2_center_um"],
        output_window_um=output_window_um,
        output_path=output_dir / "field_output_profile.png",
    )
    enhanced_propagation_plot_path = save_field_propagation_enhanced_plot(
        x_um=x_um,
        z_um=z_um,
        intensity_map=intensity_map,
        mmi_width_um=mmi_width_um,
        output1_center_um=power_result["output1_center_um"],
        output2_center_um=power_result["output2_center_um"],
        output_path=output_dir / "field_propagation_enhanced.png",
    )
    sensitivity_result = run_output_window_sensitivity_analysis(
        wavelength_um=wavelength_um,
        mmi_width_um=mmi_width_um,
        mmi_length_um=mmi_length_um,
        x_um=x_um,
        output_field=field_map_complex[-1],
        output_separation_um=output_separation_um,
        default_output_window_um=output_window_um,
        output_dir=output_dir,
    )

    propagation_result: dict[str, Any] = {
        "propagation_solver_type": "scalar_bpm_v3_0",
        "model_level": "2D scalar BPM approximation",
        "wavelength_um": wavelength_um,
        "mmi_width_um": mmi_width_um,
        "mmi_length_um": mmi_length_um,
        "x_span_um": x_span_um,
        "nx": int(nx),
        "nz": int(nz),
        "dx_um": dx_um,
        "dz_um": dz_um,
        "reference_neff": reference_neff,
        "core_neff": core_neff,
        "cladding_neff": cladding_neff,
        "output_separation_um": output_separation_um,
        "output_window_um": output_window_um,
        "output1_center_um": power_result["output1_center_um"],
        "output2_center_um": power_result["output2_center_um"],
        "p_out1": power_result["p_out1"],
        "p_out2": power_result["p_out2"],
        "total_collected_power": power_result["total_collected_power"],
        "imbalance_db": power_result["imbalance_db"],
        "insertion_loss_db": power_result["insertion_loss_db"],
        "window_based_insertion_loss_db": power_result[
            "insertion_loss_db"
        ],
        "field_propagation_png": propagation_plot_path.name,
        "field_output_profile_png": output_profile_plot_path.name,
        "field_propagation_enhanced_png": (
            enhanced_propagation_plot_path.name
        ),
        "output_window_sensitivity_result_json": (
            "output_window_sensitivity_result.json"
        ),
        "output_window_sensitivity_png": "output_window_sensitivity.png",
        "interpretation": (
            "insertion_loss_db is retained for compatibility. V3.1 recommends "
            "window_based_insertion_loss_db because the value is derived from "
            "simple output-window integration rather than strict device loss."
        ),
        "limitations": [
            "This is a 2D scalar BPM approximation.",
            "This is not a full-vector FDTD/FEM/EME simulation.",
            "The output power estimation is based on simple port-window integration.",
            "window_based_insertion_loss_db is not a strict device insertion loss.",
        ],
    }
    propagation_result_path = output_dir / "propagation_result.json"
    propagation_result_path.write_text(
        json.dumps(propagation_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    propagation_result.update(
        {
            "propagation_result_path": str(propagation_result_path),
            "field_propagation_path": str(propagation_plot_path),
            "field_output_profile_path": str(output_profile_plot_path),
            "field_propagation_enhanced_path": str(
                enhanced_propagation_plot_path
            ),
            "output_window_sensitivity_result_path": sensitivity_result[
                "output_window_sensitivity_result_path"
            ],
            "output_window_sensitivity_plot_path": sensitivity_result[
                "output_window_sensitivity_plot_path"
            ],
        }
    )
    return propagation_result
