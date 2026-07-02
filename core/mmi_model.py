import numpy as np


def estimate_mmi_length(wavelength_um, neff, mmi_width_um):
    """
    使用简化自成像模型估算 MMI 初始长度。

    注意：
    这里仍然不是严格电磁仿真，
    只是用于给自动化设计流程提供初始物理估算。
    """
    l_pi = 4 * neff * mmi_width_um**2 / (3 * wavelength_um)
    l_mmi = 3 * l_pi / 8
    return l_mmi


def toy_mmi_response(lengths_um, ideal_length_um):
    """
    V1 demo 中使用的简化 MMI 响应模型。

    输入可以是一维数组，也可以是二维网格。
    用于模拟 MMI 长度偏离理想长度时，两个输出端口功率的变化趋势。
    """
    detuning = (lengths_um - ideal_length_um) / ideal_length_um

    efficiency = np.exp(-18 * detuning**2)
    imbalance = 0.18 * np.sin(2 * np.pi * detuning)

    p_out1 = 0.5 * efficiency * (1 + imbalance)
    p_out2 = 0.5 * efficiency * (1 - imbalance)

    total_power = np.maximum(p_out1 + p_out2, 1e-12)
    insertion_loss_db = -10 * np.log10(total_power)

    imbalance_db = 10 * np.log10(
        np.maximum(p_out1, 1e-12) / np.maximum(p_out2, 1e-12)
    )

    score = (
        abs(p_out1 - 0.5)
        + abs(p_out2 - 0.5)
        + 0.05 * insertion_loss_db
        + 0.05 * abs(imbalance_db)
    )

    return p_out1, p_out2, insertion_loss_db, imbalance_db, score