from pathlib import Path

import gdsfactory as gf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from layout.pdk_setup import activate_pdk


def _snap_port_width_to_grid(width_um: float) -> float:
    """Snap a port-bearing width to kfactory's required two-DBU grid."""
    if width_um <= 0:
        raise ValueError(f"Port width must be greater than 0 um, got {width_um}.")

    return gf.snap.snap_to_grid(width_um, grid_factor=2)


def generate_gds(spec, result, output_dir: Path):
    """
    使用 gdsfactory 生成 1x2 MMI 的 GDS 版图。

    V1 中优先使用二维扫描得到的 best_width_um 和 best_length_um。
    在调用 gdsfactory 参数化器件前，先激活 generic PDK，
    避免出现 No active PDK 报错。
    """
    activate_pdk()

    length_mmi = result["best_length_um"]
    # kfactory requires every port width to be an even number of DBUs.  The
    # optimizer uses linspace and can therefore return values such as 2.513 um
    # (2513 DBU), so align layout widths to the active PDK's two-DBU grid.
    width_mmi = _snap_port_width_to_grid(
        result.get("best_width_um", spec["mmi_width_um"])
    )
    waveguide_width = _snap_port_width_to_grid(spec["waveguide_width_um"])

    component = gf.components.mmi1x2(
        width=waveguide_width,
        width_mmi=width_mmi,
        length_mmi=length_mmi,
    )

    gds_path = output_dir / "mmi1x2_demo.gds"
    component.write_gds(gds_path)

    return gds_path


def generate_layout_preview(spec, result, output_dir: Path):
    """
    生成 1x2 MMI 的简化版图预览图。

    注意：
    这个图是结构示意预览图，不是 GDS 文件的精确截图。
    """
    length_mmi = result["best_length_um"]
    width_mmi = result.get("best_width_um", spec["mmi_width_um"])
    waveguide_width = spec["waveguide_width_um"]

    input_wg_length = 3.0
    output_wg_length = 4.0
    output_gap = width_mmi / 2

    fig, ax = plt.subplots(figsize=(9, 4))

    input_wg = Rectangle(
        (-input_wg_length, -waveguide_width / 2),
        input_wg_length,
        waveguide_width,
        fill=False,
        linewidth=2,
    )
    ax.add_patch(input_wg)

    mmi_region = Rectangle(
        (0, -width_mmi / 2),
        length_mmi,
        width_mmi,
        fill=False,
        linewidth=2,
    )
    ax.add_patch(mmi_region)

    upper_output = Rectangle(
        (length_mmi, output_gap / 2 - waveguide_width / 2),
        output_wg_length,
        waveguide_width,
        fill=False,
        linewidth=2,
    )
    ax.add_patch(upper_output)

    lower_output = Rectangle(
        (length_mmi, -output_gap / 2 - waveguide_width / 2),
        output_wg_length,
        waveguide_width,
        fill=False,
        linewidth=2,
    )
    ax.add_patch(lower_output)

    ax.text(length_mmi / 2, 0, "MMI region", ha="center", va="center", fontsize=11)
    ax.text(-input_wg_length / 2, waveguide_width, "Input", ha="center", fontsize=10)
    ax.text(
        length_mmi + output_wg_length / 2,
        output_gap / 2 + waveguide_width,
        "Output 1",
        ha="center",
        fontsize=10,
    )
    ax.text(
        length_mmi + output_wg_length / 2,
        -output_gap / 2 - waveguide_width * 2,
        "Output 2",
        ha="center",
        fontsize=10,
    )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x / μm")
    ax.set_ylabel("y / μm")
    ax.set_title("Simplified Layout Preview of 1x2 MMI Splitter")
    ax.grid(True)

    margin = 1.5
    ax.set_xlim(-input_wg_length - margin, length_mmi + output_wg_length + margin)
    ax.set_ylim(-width_mmi / 2 - margin, width_mmi / 2 + margin)

    plt.tight_layout()

    preview_path = output_dir / "layout_preview.png"
    plt.savefig(preview_path, dpi=300)
    plt.close()

    return preview_path
