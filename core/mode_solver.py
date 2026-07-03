import json
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np


def estimate_effective_index(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
) -> float:
    """快速 neff 近似函数，保留给波长扫描和旧接口使用。"""
    width_factor = 1.0 - np.exp(-waveguide_width_um / 0.45)
    height_factor = 1.0 - np.exp(-waveguide_height_um / 0.18)
    wavelength_factor = 1.55 / wavelength_um

    confinement = 0.72 * width_factor * height_factor
    confinement = np.clip(confinement, 0.0, 0.95)

    neff = cladding_index + confinement * (core_index - cladding_index)
    neff = neff * (0.98 + 0.02 * wavelength_factor)
    return float(neff)


def _build_index_grid(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    grid_size_x: int = 96,
    grid_size_y: int = 72,
) -> Dict[str, Any]:
    """构建简化矩形 SOI 波导二维截面折射率网格。"""
    x_span_um = max(4.0, waveguide_width_um * 6.0)
    y_span_um = max(3.0, waveguide_height_um * 10.0)

    x = np.linspace(-x_span_um / 2, x_span_um / 2, grid_size_x)
    y = np.linspace(-y_span_um / 2, y_span_um / 2, grid_size_y)
    x_grid, y_grid = np.meshgrid(x, y)

    index_profile = np.full_like(x_grid, cladding_index, dtype=float)
    core_mask = (
        (np.abs(x_grid) <= waveguide_width_um / 2)
        & (np.abs(y_grid) <= waveguide_height_um / 2)
    )
    index_profile[core_mask] = core_index

    return {
        "x": x,
        "y": y,
        "X": x_grid,
        "Y": y_grid,
        "index_profile": index_profile,
        "core_mask": core_mask,
        "x_span_um": x_span_um,
        "y_span_um": y_span_um,
    }


def generate_index_profile(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    output_dir: str | Path,
    grid_size: int = 240,
) -> dict:
    """生成 SOI 波导折射率截面图 index_profile.png。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    grid = _build_index_grid(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_width_um=waveguide_width_um,
        waveguide_height_um=waveguide_height_um,
        grid_size_x=grid_size,
        grid_size_y=grid_size,
    )
    x = grid["x"]
    y = grid["y"]

    index_profile_path = output_dir / "index_profile.png"
    plt.figure(figsize=(6, 4.8))
    plt.imshow(
        grid["index_profile"],
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
        "x_span_um": float(grid["x_span_um"]),
        "y_span_um": float(grid["y_span_um"]),
    }


def solve_scalar_fd_mode(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
    grid_size_x: int = 96,
    grid_size_y: int = 72,
) -> Dict[str, Any]:
    """求解二维标量 Helmholtz 有限差分本征值问题。"""
    try:
        from scipy.sparse import diags, eye, kron
        from scipy.sparse.linalg import eigsh
    except ImportError as exc:
        raise ImportError(
            "V2.5 finite-difference mode solver requires scipy. "
            "Please run: pip install scipy"
        ) from exc

    grid = _build_index_grid(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_width_um=waveguide_width_um,
        waveguide_height_um=waveguide_height_um,
        grid_size_x=grid_size_x,
        grid_size_y=grid_size_y,
    )
    x = grid["x"]
    y = grid["y"]
    index_profile = grid["index_profile"]
    core_mask = grid["core_mask"]

    dx = float(x[1] - x[0])
    dy = float(y[1] - y[0])
    nx = len(x)
    ny = len(y)

    tx = diags(
        [
            np.ones(nx - 1) / dx**2,
            -2.0 * np.ones(nx) / dx**2,
            np.ones(nx - 1) / dx**2,
        ],
        offsets=[-1, 0, 1],
        format="csr",
    )
    ty = diags(
        [
            np.ones(ny - 1) / dy**2,
            -2.0 * np.ones(ny) / dy**2,
            np.ones(ny - 1) / dy**2,
        ],
        offsets=[-1, 0, 1],
        format="csr",
    )
    laplacian = kron(eye(ny, format="csr"), tx) + kron(
        ty,
        eye(nx, format="csr"),
    )

    k0 = 2.0 * np.pi / wavelength_um
    potential = diags(
        (k0 * index_profile.reshape(-1)) ** 2,
        offsets=0,
        format="csr",
    )
    operator = laplacian + potential

    eigenvalues, eigenvectors = eigsh(
        operator,
        k=1,
        which="LA",
        tol=1e-8,
        maxiter=2000,
    )
    beta_sq = float(eigenvalues[0])
    if beta_sq <= 0:
        raise ValueError(
            f"Invalid beta^2 from scalar FD solver: {beta_sq}. "
            "Please check grid size and waveguide parameters."
        )

    beta = float(np.sqrt(beta_sq))
    neff = float(beta / k0)
    field = np.real(eigenvectors[:, 0]).reshape(ny, nx)
    max_abs_field = np.max(np.abs(field))
    if max_abs_field > 0:
        field = field / max_abs_field

    intensity = field**2
    if np.max(intensity) > 0:
        intensity = intensity / np.max(intensity)

    confinement_factor = float(np.sum(intensity[core_mask]) / np.sum(intensity))
    mode_area_um2 = float(
        (np.sum(intensity) ** 2)
        / np.sum(intensity**2)
        * dx
        * dy
    )

    return {
        "x": x,
        "y": y,
        "index_profile": index_profile,
        "field": field,
        "intensity": intensity,
        "neff": neff,
        "beta": beta,
        "beta_sq": beta_sq,
        "confinement_factor": confinement_factor,
        "mode_area_um2": mode_area_um2,
        "dx_um": dx,
        "dy_um": dy,
        "grid_size_x": nx,
        "grid_size_y": ny,
        "x_span_um": float(grid["x_span_um"]),
        "y_span_um": float(grid["y_span_um"]),
    }


def generate_mode_profile(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
    output_dir: str | Path,
    grid_size_x: int = 96,
    grid_size_y: int = 72,
) -> dict:
    """生成 V2.5 有限差分标量模式结果和 mode_profile.png。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    solver_result = solve_scalar_fd_mode(
        core_index=core_index,
        cladding_index=cladding_index,
        waveguide_width_um=waveguide_width_um,
        waveguide_height_um=waveguide_height_um,
        wavelength_um=wavelength_um,
        grid_size_x=grid_size_x,
        grid_size_y=grid_size_y,
    )
    x = solver_result["x"]
    y = solver_result["y"]

    mode_profile_path = output_dir / "mode_profile.png"
    plt.figure(figsize=(6, 4.8))
    plt.imshow(
        solver_result["intensity"],
        extent=[x.min(), x.max(), y.min(), y.max()],
        origin="lower",
        aspect="auto",
    )
    plt.colorbar(label="Normalized intensity")
    plt.xlabel("x / μm")
    plt.ylabel("y / μm")
    plt.title("V2.5 Scalar FD Mode Profile")

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
        "mode_solver_type": "finite_difference_scalar_mode_solver_v2_5",
        "core_index": float(core_index),
        "cladding_index": float(cladding_index),
        "waveguide_width_um": float(waveguide_width_um),
        "waveguide_height_um": float(waveguide_height_um),
        "wavelength_um": float(wavelength_um),
        "estimated_neff": float(solver_result["neff"]),
        "beta": float(solver_result["beta"]),
        "beta_sq": float(solver_result["beta_sq"]),
        "confinement_factor": float(solver_result["confinement_factor"]),
        "mode_area_um2": float(solver_result["mode_area_um2"]),
        "grid_size_x": int(solver_result["grid_size_x"]),
        "grid_size_y": int(solver_result["grid_size_y"]),
        "dx_um": float(solver_result["dx_um"]),
        "dy_um": float(solver_result["dy_um"]),
        "x_span_um": float(solver_result["x_span_um"]),
        "y_span_um": float(solver_result["y_span_um"]),
        "mode_profile_path": str(mode_profile_path),
        "solver_note": (
            "Scalar finite-difference Helmholtz eigenmode solver. "
            "This is not a full-vectorial FDE/FEM solver."
        ),
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
    grid_size_x: int = 80,
    grid_size_y: int = 60,
) -> dict:
    """使用标量有限差分求解器扫描 neff 随波导宽度的变化。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    widths = np.linspace(width_min_um, width_max_um, num_points)
    neff_values = []
    failed_widths = []

    for width in widths:
        try:
            solver_result = solve_scalar_fd_mode(
                core_index=core_index,
                cladding_index=cladding_index,
                waveguide_width_um=float(width),
                waveguide_height_um=waveguide_height_um,
                wavelength_um=wavelength_um,
                grid_size_x=grid_size_x,
                grid_size_y=grid_size_y,
            )
            neff_values.append(float(solver_result["neff"]))
        except Exception:
            failed_widths.append(float(width))
            fallback_neff = estimate_effective_index(
                core_index=core_index,
                cladding_index=cladding_index,
                waveguide_width_um=float(width),
                waveguide_height_um=waveguide_height_um,
                wavelength_um=wavelength_um,
            )
            neff_values.append(float(fallback_neff))

    neff_vs_width_path = output_dir / "neff_vs_width.png"
    plt.figure(figsize=(6, 4))
    plt.plot(widths, neff_values, marker="o", markersize=3)
    plt.xlabel("Waveguide width / μm")
    plt.ylabel("Estimated neff")
    plt.title("V2.5 Scalar FD neff vs Waveguide Width")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(neff_vs_width_path, dpi=200)
    plt.close()

    return {
        "sweep_solver_type": "finite_difference_scalar_mode_solver_v2_5",
        "width_min_um": float(width_min_um),
        "width_max_um": float(width_max_um),
        "num_points": int(num_points),
        "waveguide_height_um": float(waveguide_height_um),
        "wavelength_um": float(wavelength_um),
        "widths_um": [float(value) for value in widths],
        "neff_values": [float(value) for value in neff_values],
        "failed_widths_um": failed_widths,
        "grid_size_x": int(grid_size_x),
        "grid_size_y": int(grid_size_y),
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
    num_width_points: int = 21,
) -> dict:
    """运行 V2.5 有限差分模式分析并保持既有结果接口。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    num_width_points = min(int(num_width_points), 25)

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
        grid_size_x=96,
        grid_size_y=72,
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
        grid_size_x=80,
        grid_size_y=60,
    )

    mode_result = {
        "mode_solver_version": "V2.5",
        "mode_solver_type": "finite_difference_scalar_mode_solver_v2_5",
        "index_profile_result": index_profile_result,
        "mode_profile_result": mode_profile_result,
        "neff_sweep_result": neff_sweep_result,
        "neff_used_for_mmi": float(mode_profile_result["estimated_neff"]),
        "note": (
            "V2.5 uses a scalar finite-difference Helmholtz eigenmode solver "
            "to estimate the fundamental mode and neff. It is more physical "
            "than the previous Gaussian-like approximation, but is not a "
            "full-vectorial FDE/FEM/EME solver."
        ),
    }

    mode_result_path = output_dir / "mode_result.json"
    with open(mode_result_path, "w", encoding="utf-8") as file:
        json.dump(mode_result, file, ensure_ascii=False, indent=2)

    mode_result["mode_result_path"] = str(mode_result_path)
    return mode_result
