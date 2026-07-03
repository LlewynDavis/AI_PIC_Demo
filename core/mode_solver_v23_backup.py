import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def estimate_effective_index(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
) -> float:
    """V1/V1.5 兼容函数：简化有效折射率估算。"""
    width_factor = 1.0 - np.exp(-waveguide_width_um / 0.45)
    height_factor = 1.0 - np.exp(-waveguide_height_um / 0.18)
    wavelength_factor = 1.55 / wavelength_um

    confinement = 0.72 * width_factor * height_factor
    confinement = np.clip(confinement, 0.0, 0.95)

    neff = cladding_index + confinement * (core_index - cladding_index)
    neff = neff * (0.98 + 0.02 * wavelength_factor)

    return float(neff)


def generate_index_profile(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    output_dir: str | Path,
    grid_size: int = 240,
) -> dict:
    """生成 SOI 波导截面的折射率分布图及相关参数。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    x_span_um = max(4.0, waveguide_width_um * 5.0)
    y_span_um = max(3.0, waveguide_height_um * 8.0)

    x = np.linspace(-x_span_um / 2, x_span_um / 2, grid_size)
    y = np.linspace(-y_span_um / 2, y_span_um / 2, grid_size)
    x_grid, y_grid = np.meshgrid(x, y)

    index_profile = np.full_like(x_grid, cladding_index, dtype=float)
    core_mask = (
        (np.abs(x_grid) <= waveguide_width_um / 2)
        & (np.abs(y_grid) <= waveguide_height_um / 2)
    )
    index_profile[core_mask] = core_index

    index_profile_path = output_dir / "index_profile.png"

    plt.figure(figsize=(6, 4.8))
    plt.imshow(
        index_profile,
        extent=[x.min(), x.max(), y.min(), y.max()],
        origin="lower",
        aspect="auto",
    )
    plt.colorbar(label="Refractive index")
    plt.xlabel("x / μm")
    plt.ylabel("y / μm")
    plt.title("SOI Waveguide Index Profile")

    rect_x = [
        -waveguide_width_um / 2,
        waveguide_width_um / 2,
        waveguide_width_um / 2,
        -waveguide_width_um / 2,
        -waveguide_width_um / 2,
    ]
    rect_y = [
        -waveguide_height_um / 2,
        -waveguide_height_um / 2,
        waveguide_height_um / 2,
        waveguide_height_um / 2,
        -waveguide_height_um / 2,
    ]
    plt.plot(rect_x, rect_y, linewidth=1.5)

    plt.tight_layout()
    plt.savefig(index_profile_path, dpi=200)
    plt.close()

    return {
        "index_profile_path": str(index_profile_path),
        "core_index": float(core_index),
        "cladding_index": float(cladding_index),
        "waveguide_width_um": float(waveguide_width_um),
        "waveguide_height_um": float(waveguide_height_um),
        "x_span_um": float(x_span_um),
        "y_span_um": float(y_span_um),
    }


def generate_mode_profile(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
    output_dir: str | Path,
    grid_size: int = 240,
) -> dict:
    """生成教学和 demo 用的近似 TE0 模式场分布。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    neff = estimate_effective_index(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_width_um=waveguide_width_um,
        waveguide_height_um=waveguide_height_um,
        wavelength_um=wavelength_um,
    )

    x_span_um = max(4.0, waveguide_width_um * 5.0)
    y_span_um = max(3.0, waveguide_height_um * 8.0)

    x = np.linspace(-x_span_um / 2, x_span_um / 2, grid_size)
    y = np.linspace(-y_span_um / 2, y_span_um / 2, grid_size)
    x_grid, y_grid = np.meshgrid(x, y)

    sigma_x = max(waveguide_width_um / 2.2, 0.18)
    sigma_y = max(waveguide_height_um / 1.6, 0.10)

    field = np.exp(
        -(
            x_grid**2 / (2 * sigma_x**2)
            + y_grid**2 / (2 * sigma_y**2)
        )
    )
    intensity = field**2
    intensity = intensity / np.max(intensity)

    core_mask = (
        (np.abs(x_grid) <= waveguide_width_um / 2)
        & (np.abs(y_grid) <= waveguide_height_um / 2)
    )

    confinement_factor = float(np.sum(intensity[core_mask]) / np.sum(intensity))
    mode_area_um2 = float(
        (np.sum(intensity) ** 2)
        / np.sum(intensity**2)
        * (x[1] - x[0])
        * (y[1] - y[0])
    )

    mode_profile_path = output_dir / "mode_profile.png"

    plt.figure(figsize=(6, 4.8))
    plt.imshow(
        intensity,
        extent=[x.min(), x.max(), y.min(), y.max()],
        origin="lower",
        aspect="auto",
    )
    plt.colorbar(label="Normalized intensity")
    plt.xlabel("x / μm")
    plt.ylabel("y / μm")
    plt.title("Approximate TE0 Mode Profile")

    rect_x = [
        -waveguide_width_um / 2,
        waveguide_width_um / 2,
        waveguide_width_um / 2,
        -waveguide_width_um / 2,
        -waveguide_width_um / 2,
    ]
    rect_y = [
        -waveguide_height_um / 2,
        -waveguide_height_um / 2,
        waveguide_height_um / 2,
        waveguide_height_um / 2,
        -waveguide_height_um / 2,
    ]
    plt.plot(rect_x, rect_y, linewidth=1.5)

    plt.tight_layout()
    plt.savefig(mode_profile_path, dpi=200)
    plt.close()

    return {
        "mode_solver_type": "approximate_te0_mode_solver_v2",
        "core_index": core_index,
        "cladding_index": cladding_index,
        "waveguide_width_um": waveguide_width_um,
        "waveguide_height_um": waveguide_height_um,
        "wavelength_um": wavelength_um,
        "estimated_neff": neff,
        "confinement_factor": confinement_factor,
        "mode_area_um2": mode_area_um2,
        "mode_profile_path": str(mode_profile_path),
    }


def sweep_neff_vs_width(
    core_index: float,
    cladding_index: float,
    waveguide_height_um: float,
    wavelength_um: float,
    width_min_um: float,
    width_max_um: float,
    num_points: int,
    output_dir: str | Path,
) -> dict:
    """扫描不同波导宽度下的有效折射率变化。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    widths = np.linspace(width_min_um, width_max_um, num_points)
    neff_values = [
        estimate_effective_index(
            core_index=core_index,
            cladding_index=cladding_index,
            waveguide_width_um=float(width),
            waveguide_height_um=waveguide_height_um,
            wavelength_um=wavelength_um,
        )
        for width in widths
    ]

    neff_vs_width_path = output_dir / "neff_vs_width.png"

    plt.figure(figsize=(6, 4))
    plt.plot(widths, neff_values, marker="o", markersize=3)
    plt.xlabel("Waveguide width / μm")
    plt.ylabel("Estimated neff")
    plt.title("Estimated neff vs Waveguide Width")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(neff_vs_width_path, dpi=200)
    plt.close()

    return {
        "width_min_um": float(width_min_um),
        "width_max_um": float(width_max_um),
        "num_points": int(num_points),
        "waveguide_height_um": float(waveguide_height_um),
        "wavelength_um": float(wavelength_um),
        "widths_um": [float(value) for value in widths],
        "neff_values": [float(value) for value in neff_values],
        "neff_vs_width_path": str(neff_vs_width_path),
    }


def run_mode_solver_analysis(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
    output_dir: str | Path,
    width_min_um: float = 0.3,
    width_max_um: float = 0.8,
    num_width_points: int = 40,
) -> dict:
    """运行 V2 近似模式分析并生成图像与 JSON 结果。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_profile_result = generate_index_profile(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_width_um=waveguide_width_um,
        waveguide_height_um=waveguide_height_um,
        output_dir=output_dir,
    )

    mode_profile_result = generate_mode_profile(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_width_um=waveguide_width_um,
        waveguide_height_um=waveguide_height_um,
        wavelength_um=wavelength_um,
        output_dir=output_dir,
    )

    neff_sweep_result = sweep_neff_vs_width(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_height_um=waveguide_height_um,
        wavelength_um=wavelength_um,
        width_min_um=width_min_um,
        width_max_um=width_max_um,
        num_points=num_width_points,
        output_dir=output_dir,
    )

    mode_result = {
        "index_profile_result": index_profile_result,
        "mode_profile_result": mode_profile_result,
        "neff_sweep_result": neff_sweep_result,
        "neff_used_for_mmi": mode_profile_result["estimated_neff"],
        "note": (
            "This is an approximate V2.2 mode solver module for demo purpose. "
            "It includes index profile visualization, approximate TE0 mode "
            "profile, and neff width sweep. It is not a rigorous FDE/FEM "
            "eigenmode solver."
        ),
    }

    mode_result_path = output_dir / "mode_result.json"
    with open(mode_result_path, "w", encoding="utf-8") as file:
        json.dump(mode_result, file, ensure_ascii=False, indent=2)

    mode_result["mode_result_path"] = str(mode_result_path)
    return mode_result
