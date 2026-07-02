def estimate_effective_index(
    core_index: float,
    cladding_index: float,
    waveguide_width_um: float,
    waveguide_height_um: float,
    wavelength_um: float,
):
    """
    简化有效折射率估算模块。

    注意：
    这不是严格的 FDE/FEM 模式求解器。
    它只是 V1 demo 中用于体现“材料参数和波导尺寸影响 neff”的近似模型。

    后续可以将该函数替换为真实模式求解器，
    例如 FEMWELL、MPB、Lumerical MODE 或 COMSOL Mode Analysis。
    """
    width_factor = waveguide_width_um / (
        waveguide_width_um + 0.25 * wavelength_um
    )

    height_factor = waveguide_height_um / (
        waveguide_height_um + 0.08 * wavelength_um
    )

    confinement_factor = 0.35 + 0.55 * (
        0.6 * width_factor + 0.4 * height_factor
    )

    confinement_factor = max(0.05, min(confinement_factor, 0.95))

    neff = cladding_index + (core_index - cladding_index) * confinement_factor

    return neff