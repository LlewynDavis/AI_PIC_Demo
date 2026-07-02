import json
import re
from pathlib import Path


def save_design_spec(spec: dict, output_dir: Path):
    """
    保存设计参数到 design_spec.json。
    """
    spec_path = output_dir / "design_spec.json"

    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=4, ensure_ascii=False)

    return spec_path


def create_design_spec(output_dir: Path):
    """
    创建 V1 demo 的默认设计参数。

    V1 相比 V0 增加：
    1. 波导高度参数；
    2. 是否使用估算 neff；
    3. MMI 宽度扫描范围；
    4. MMI 宽度扫描点数。
    """
    spec = {
        "component": "1x2_mmi_splitter",
        "platform": "SOI",
        "wavelength_um": 1.55,
        "use_estimated_neff": True,
        "neff": 2.8,
        "waveguide_width_um": 0.5,
        "waveguide_height_um": 0.22,
        "mmi_width_um": 2.5,
        "target_split_ratio": [0.5, 0.5],
        "length_scan_range_um": [3.0, 20.0],
        "num_scan_points": 200,
        "mmi_width_scan_range_um": [1.5, 4.0],
        "num_width_scan_points": 80,
    }

    save_design_spec(spec=spec, output_dir=output_dir)

    return spec


def parse_design_text(user_text: str):
    """
    规则版自然语言需求解析器。

    当前版本不是完整大模型 AI，
    而是用关键词和正则表达式提取设计参数。
    后续可以替换为大模型结构化输出。
    """
    text = user_text.lower()

    parsed = {
        "component": "1x2_mmi_splitter",
        "platform": "SOI",
        "wavelength_um": 1.55,
        "use_estimated_neff": True,
        "neff": 2.8,
        "waveguide_width_um": 0.5,
        "waveguide_height_um": 0.22,
        "mmi_width_um": 2.5,
        "target_split_ratio": [0.5, 0.5],
        "length_scan_range_um": [3.0, 20.0],
        "num_scan_points": 200,
        "mmi_width_scan_range_um": [1.5, 4.0],
        "num_width_scan_points": 80,
    }

    if "mmi" in text or "分束器" in text or "splitter" in text:
        parsed["component"] = "1x2_mmi_splitter"

    if "soi" in text:
        parsed["platform"] = "SOI"

    nm_match = re.search(r"(\d+\.?\d*)\s*nm", text)
    if nm_match:
        wavelength_nm = float(nm_match.group(1))
        parsed["wavelength_um"] = wavelength_nm / 1000

    um_match = re.search(r"(\d+\.?\d*)\s*(um|μm)", text)
    if um_match:
        parsed["wavelength_um"] = float(um_match.group(1))

    if "50:50" in text or "50/50" in text or "等分" in text or "均分" in text:
        parsed["target_split_ratio"] = [0.5, 0.5]

    neff_match = re.search(r"neff\s*=?\s*(\d+\.?\d*)", text)
    if neff_match:
        parsed["neff"] = float(neff_match.group(1))
        parsed["use_estimated_neff"] = False

    wg_match = re.search(r"waveguide\s*width\s*=?\s*(\d+\.?\d*)", text)
    if wg_match:
        parsed["waveguide_width_um"] = float(wg_match.group(1))

    mmi_width_match = re.search(r"mmi\s*width\s*=?\s*(\d+\.?\d*)", text)
    if mmi_width_match:
        parsed["mmi_width_um"] = float(mmi_width_match.group(1))

    return parsed