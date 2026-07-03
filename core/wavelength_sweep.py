import json
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np

from core.mmi_model import estimate_mmi_length, toy_mmi_response
from core.mode_solver import estimate_effective_index, solve_scalar_fd_mode


def run_wavelength_sweep(
    design_spec: Dict[str, Any],
    material_params: Dict[str, Any],
    best_width_um: float,
    best_length_um: float,
    output_dir: str | Path,
    wavelength_min_um: float = 1.50,
    wavelength_max_um: float = 1.60,
    num_points: int = 21,
) -> Dict[str, Any]:
    """使用 V2.5 有限差分 neff 扫描固定 MMI 结构的波长响应。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    waveguide_width_um = float(design_spec.get("waveguide_width_um", 0.5))
    waveguide_height_um = float(design_spec.get("waveguide_height_um", 0.22))
    core_index = float(material_params["core_index"])
    cladding_index = float(material_params["cladding_index"])

    wavelengths = np.linspace(wavelength_min_um, wavelength_max_um, num_points)
    neff_values = []
    output_port_1_values = []
    output_port_2_values = []
    insertion_loss_values = []
    imbalance_values = []
    score_values = []
    failed_wavelengths = []

    for wavelength_um in wavelengths:
        try:
            solver_result = solve_scalar_fd_mode(
                core_index=core_index,
                cladding_index=cladding_index,
                waveguide_width_um=waveguide_width_um,
                waveguide_height_um=waveguide_height_um,
                wavelength_um=float(wavelength_um),
                grid_size_x=96,
                grid_size_y=72,
            )
            neff = float(solver_result["neff"])
        except Exception:
            failed_wavelengths.append(float(wavelength_um))
            neff = estimate_effective_index(
                core_index=core_index,
                cladding_index=cladding_index,
                waveguide_width_um=waveguide_width_um,
                waveguide_height_um=waveguide_height_um,
                wavelength_um=float(wavelength_um),
            )
        ideal_length_um = estimate_mmi_length(
            wavelength_um=float(wavelength_um),
            neff=float(neff),
            mmi_width_um=float(best_width_um),
        )
        p_out1, p_out2, insertion_loss_db, imbalance_db, score = (
            toy_mmi_response(
                lengths_um=float(best_length_um),
                ideal_length_um=float(ideal_length_um),
            )
        )

        neff_values.append(float(neff))
        output_port_1_values.append(float(p_out1))
        output_port_2_values.append(float(p_out2))
        insertion_loss_values.append(float(insertion_loss_db))
        imbalance_values.append(float(imbalance_db))
        score_values.append(float(score))

    wavelength_sweep_path = output_dir / "wavelength_sweep.png"
    plt.figure(figsize=(7, 4.8))
    plt.plot(wavelengths, output_port_1_values, label="Output port 1")
    plt.plot(wavelengths, output_port_2_values, label="Output port 2")
    plt.axhline(0.5, linestyle="--", linewidth=1.0, label="Target 0.5")
    plt.xlabel("Wavelength / μm")
    plt.ylabel("Normalized power")
    plt.title("V2.5 FD Wavelength Sweep of 1×2 MMI Splitter")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(wavelength_sweep_path, dpi=200)
    plt.close()

    imbalance_plot_path = output_dir / "wavelength_imbalance.png"
    plt.figure(figsize=(7, 4.8))
    plt.plot(wavelengths, imbalance_values, marker="o", markersize=3)
    plt.axhline(0.0, linestyle="--", linewidth=1.0)
    plt.xlabel("Wavelength / μm")
    plt.ylabel("Imbalance / dB")
    plt.title("V2.5 FD Wavelength Dependence of Splitting Imbalance")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(imbalance_plot_path, dpi=200)
    plt.close()

    center_wavelength = float(design_spec.get("wavelength_um", 1.55))
    center_index = int(np.argmin(np.abs(wavelengths - center_wavelength)))

    result = {
        "analysis_type": "wavelength_sweep_v2_5",
        "sweep_version": "V2.5",
        "neff_solver_type": "finite_difference_scalar_mode_solver_v2_5",
        "fallback_used": bool(failed_wavelengths),
        "failed_wavelengths_um": failed_wavelengths,
        "grid_size_x": 96,
        "grid_size_y": 72,
        "wavelength_min_um": float(wavelength_min_um),
        "wavelength_max_um": float(wavelength_max_um),
        "num_points": int(num_points),
        "best_width_um": float(best_width_um),
        "best_length_um": float(best_length_um),
        "center_wavelength_um": float(wavelengths[center_index]),
        "center_output_port_1": float(output_port_1_values[center_index]),
        "center_output_port_2": float(output_port_2_values[center_index]),
        "max_abs_imbalance_db": float(np.max(np.abs(imbalance_values))),
        "mean_abs_imbalance_db": float(np.mean(np.abs(imbalance_values))),
        "max_insertion_loss_db": float(np.max(insertion_loss_values)),
        "wavelengths_um": [float(value) for value in wavelengths],
        "neff_values": [float(value) for value in neff_values],
        "output_port_1": output_port_1_values,
        "output_port_2": output_port_2_values,
        "insertion_loss_db": insertion_loss_values,
        "imbalance_db": imbalance_values,
        "score": score_values,
        "wavelength_sweep_path": str(wavelength_sweep_path),
        "wavelength_imbalance_path": str(imbalance_plot_path),
        "note": (
            "V2.5 wavelength-dependent neff values come from the scalar "
            "finite-difference Helmholtz solver. The MMI response remains a "
            "lightweight surrogate model for trend analysis, not final "
            "tape-out validation."
        ),
    }

    result_path = output_dir / "wavelength_sweep_result.json"
    with open(result_path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    result["wavelength_sweep_result_path"] = str(result_path)
    return result
