import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from core.material_database import get_platform_materials, save_physical_params
from core.mode_solver import estimate_effective_index
from core.mmi_model import estimate_mmi_length, toy_mmi_response


def prepare_physical_params(spec, output_dir: Path):
    """
    根据平台和波导参数准备物理参数。

    V1 中新增：
    1. 读取 SOI 材料参数；
    2. 根据波导宽度、高度和工作波长估算 neff；
    3. 保存 physical_params.json。
    """
    material_params = get_platform_materials(spec["platform"])

    estimated_neff = estimate_effective_index(
        core_index=material_params["core_index"],
        cladding_index=material_params["cladding_index"],
        waveguide_width_um=spec["waveguide_width_um"],
        waveguide_height_um=spec["waveguide_height_um"],
        wavelength_um=spec["wavelength_um"],
    )

    if spec.get("use_estimated_neff", True):
        neff_used = estimated_neff
    else:
        neff_used = spec["neff"]

    spec["neff"] = float(neff_used)

    physical_params = {
        "platform": material_params["platform"],
        "core_material": material_params["core_material"],
        "cladding_material": material_params["cladding_material"],
        "core_index": material_params["core_index"],
        "cladding_index": material_params["cladding_index"],
        "waveguide_width_um": spec["waveguide_width_um"],
        "waveguide_height_um": spec["waveguide_height_um"],
        "wavelength_um": spec["wavelength_um"],
        "estimated_neff": float(estimated_neff),
        "neff_used": float(neff_used),
        "use_estimated_neff": spec.get("use_estimated_neff", True),
        "note": "当前 neff 来自 V1 简化估算模型，不是真实 FDE/FEM 模式求解结果。",
    }

    save_physical_params(physical_params=physical_params, output_dir=output_dir)

    return physical_params


def optimize_length(spec, output_dir: Path):
    """
    V1 优化主函数。

    为了兼容原来的 run_demo.py 和 app.py，函数名仍保留 optimize_length。
    但实际已经从“一维长度扫描”升级为“MMI 宽度-长度二维联合扫描”。
    """
    physical_params = prepare_physical_params(spec=spec, output_dir=output_dir)

    wavelength_um = spec["wavelength_um"]
    neff = spec["neff"]
    nominal_mmi_width_um = spec["mmi_width_um"]

    length_min_um, length_max_um = spec["length_scan_range_um"]
    num_length_points = spec["num_scan_points"]

    width_min_um, width_max_um = spec["mmi_width_scan_range_um"]
    num_width_points = spec["num_width_scan_points"]

    lengths_um = np.linspace(length_min_um, length_max_um, num_length_points)
    widths_um = np.linspace(width_min_um, width_max_um, num_width_points)

    width_grid, length_grid = np.meshgrid(widths_um, lengths_um, indexing="ij")

    ideal_length_grid = estimate_mmi_length(
        wavelength_um=wavelength_um,
        neff=neff,
        mmi_width_um=width_grid,
    )

    p_out1, p_out2, insertion_loss_db, imbalance_db, base_score = toy_mmi_response(
        lengths_um=length_grid,
        ideal_length_um=ideal_length_grid,
    )

    width_penalty = (
        0.03 * np.abs(width_grid - nominal_mmi_width_um) / nominal_mmi_width_um
    )

    score = base_score + width_penalty

    best_flat_index = int(np.argmin(score))
    best_width_index, best_length_index = np.unravel_index(
        best_flat_index,
        score.shape,
    )

    best_width_um = float(widths_um[best_width_index])
    best_length_um = float(lengths_um[best_length_index])

    initial_length_um = estimate_mmi_length(
        wavelength_um=wavelength_um,
        neff=neff,
        mmi_width_um=nominal_mmi_width_um,
    )

    result = {
        "version": "V1_physical_model_enhanced",
        "initial_length_um": float(initial_length_um),
        "best_width_um": best_width_um,
        "best_length_um": best_length_um,
        "p_out1": float(p_out1[best_width_index, best_length_index]),
        "p_out2": float(p_out2[best_width_index, best_length_index]),
        "insertion_loss_db": float(
            insertion_loss_db[best_width_index, best_length_index]
        ),
        "imbalance_db": float(imbalance_db[best_width_index, best_length_index]),
        "best_score": float(score[best_width_index, best_length_index]),
        "estimated_neff": float(physical_params["estimated_neff"]),
        "neff_used": float(physical_params["neff_used"]),
    }

    result_path = output_dir / "optimization_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    plot_length_sweep_at_best_width(
        lengths_um=lengths_um,
        best_width_um=best_width_um,
        wavelength_um=wavelength_um,
        neff=neff,
        output_dir=output_dir,
        best_length_um=best_length_um,
    )

    plot_width_length_heatmap(
        widths_um=widths_um,
        lengths_um=lengths_um,
        score=score,
        best_width_um=best_width_um,
        best_length_um=best_length_um,
        output_dir=output_dir,
    )

    return result


def plot_length_sweep_at_best_width(
    lengths_um,
    best_width_um,
    wavelength_um,
    neff,
    output_dir: Path,
    best_length_um,
):
    """
    在最优 MMI 宽度下，绘制长度扫描结果图。
    """
    ideal_length_um = estimate_mmi_length(
        wavelength_um=wavelength_um,
        neff=neff,
        mmi_width_um=best_width_um,
    )

    p_out1, p_out2, _, _, _ = toy_mmi_response(
        lengths_um=lengths_um,
        ideal_length_um=ideal_length_um,
    )

    plt.figure(figsize=(8, 5))
    plt.plot(lengths_um, p_out1, label="Output port 1")
    plt.plot(lengths_um, p_out2, label="Output port 2")
    plt.axvline(best_length_um, linestyle="--", label="Best length")

    plt.xlabel("MMI length (um)")
    plt.ylabel("Normalized output power")
    plt.title(f"1x2 MMI Length Sweep at Width = {best_width_um:.3f} um")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plot_path = output_dir / "length_sweep.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()

    return plot_path


def plot_width_length_heatmap(
    widths_um,
    lengths_um,
    score,
    best_width_um,
    best_length_um,
    output_dir: Path,
):
    """
    绘制 MMI 宽度-长度二维扫描热力图。

    横轴为 MMI 长度，纵轴为 MMI 宽度，颜色表示目标函数评分。
    评分越低，代表越接近当前优化目标。
    """
    plt.figure(figsize=(8, 5))

    extent = [
        lengths_um.min(),
        lengths_um.max(),
        widths_um.min(),
        widths_um.max(),
    ]

    plt.imshow(
        score,
        origin="lower",
        aspect="auto",
        extent=extent,
    )

    plt.colorbar(label="Optimization score")
    plt.scatter(
        best_length_um,
        best_width_um,
        marker="x",
        s=80,
        label="Best point",
    )

    plt.xlabel("MMI length (um)")
    plt.ylabel("MMI width (um)")
    plt.title("2D Width-Length Optimization Heatmap")
    plt.legend()
    plt.tight_layout()

    heatmap_path = output_dir / "width_length_heatmap.png"
    plt.savefig(heatmap_path, dpi=300)
    plt.close()

    return heatmap_path