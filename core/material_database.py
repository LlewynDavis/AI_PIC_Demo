import json
from pathlib import Path


def get_platform_materials(platform: str):
    """
    根据平台名称返回材料和基础波导参数。

    当前 V1 版本只内置 SOI 平台。
    这里的折射率用于 demo 近似计算，
    后续可以替换为更精确的材料色散模型或 PDK 数据。
    """
    platform = platform.upper()

    material_database = {
        "SOI": {
            "platform": "SOI",
            "core_material": "Si",
            "cladding_material": "SiO2",
            "core_index": 3.48,
            "cladding_index": 1.44,
            "default_waveguide_height_um": 0.22,
            "description": "Silicon-on-Insulator photonic platform",
        }
    }

    if platform not in material_database:
        raise ValueError(f"当前材料库暂不支持平台：{platform}")

    return material_database[platform]


def save_physical_params(physical_params: dict, output_dir: Path):
    """
    保存物理平台参数和有效折射率估算结果。
    """
    output_path = output_dir / "physical_params.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(physical_params, f, indent=4, ensure_ascii=False)

    return output_path