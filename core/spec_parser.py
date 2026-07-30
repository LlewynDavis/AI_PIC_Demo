import re
from pathlib import Path

from pydantic import ValidationError

from core.design_spec import (
    DesignSpec,
    DesignSpecValidation,
    ParameterSource,
    RequestStatus,
    legacy_defaults,
)


def save_design_spec(spec: dict | DesignSpec, output_dir: Path) -> Path:
    """
    保存 V3.3 统一设计规格到 design_spec.json。

    继续接受 V3.2 的扁平字典，避免破坏旧入口。
    """
    spec_path = output_dir / "design_spec.json"
    design_spec = spec if isinstance(spec, DesignSpec) else DesignSpec.from_legacy(spec)
    return design_spec.save_json(spec_path)


def create_design_spec(output_dir: Path):
    """
    创建 V1 demo 的默认设计参数。

    V1 相比 V0 增加：
    1. 波导高度参数；
    2. 是否使用估算 neff；
    3. MMI 宽度扫描范围；
    4. MMI 宽度扫描点数。
    """
    spec = legacy_defaults()

    save_design_spec(spec=spec, output_dir=output_dir)

    return spec


def _to_um(value: float, unit: str) -> float:
    return value / 1000.0 if unit.lower() == "nm" else value


def _extract_context_length(text: str, labels: tuple[str, ...]) -> float | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?:{label_pattern})\s*(?:=|:|为|是)?\s*(-?\d+(?:\.\d+)?)\s*(nm|um|μm)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return _to_um(float(match.group(1)), match.group(2))


def _extract_wavelengths(text: str) -> list[float]:
    explicit = re.findall(
        r"(?:wavelength|波长)\s*(?:=|:|为|是)?\s*(-?\d+(?:\.\d+)?)\s*(nm|um|μm)",
        text,
        flags=re.IGNORECASE,
    )
    if explicit:
        return [_to_um(float(value), unit) for value, unit in explicit]

    dimension_pattern = (
        r"(?:waveguide\s+(?:width|height)|mmi\s+width|"
        r"波导\s*(?:宽度|高度)|mmi\s*宽度)"
        r"\s*(?:=|:|为|是)?\s*-?\d+(?:\.\d+)?\s*(?:nm|um|μm)"
    )
    scrubbed = re.sub(dimension_pattern, "", text, flags=re.IGNORECASE)
    matches = re.findall(
        r"(-?\d+(?:\.\d+)?)\s*(nm|um|μm)",
        scrubbed,
        flags=re.IGNORECASE,
    )
    return [_to_um(float(value), unit) for value, unit in matches]


def _extract_split_ratio(text: str) -> list[float] | None:
    if any(token in text for token in ("等分", "均分", "equal split")):
        return [0.5, 0.5]
    match = re.search(
        r"(-?\d+(?:\.\d+)?)\s*[:/]\s*(-?\d+(?:\.\d+)?)",
        text,
    )
    if not match:
        return None
    first = float(match.group(1))
    second = float(match.group(2))
    total = first + second
    if total == 0:
        return [first, second]
    return [first / total, second / total]


def parse_design_request(user_text: str) -> DesignSpecValidation:
    """
    将自然语言需求解析为 V3.3 DesignSpec。

    解析器保持确定性、无外部 API 密钥。缺少器件、平台、波长或目标时，
    返回 needs_clarification，而不是静默编造关键需求。
    """
    text = user_text.strip().lower()
    if not text:
        return DesignSpecValidation(
            is_valid=False,
            status=RequestStatus.NEEDS_CLARIFICATION,
            clarification_questions=["请描述器件类型、平台、工作波长和目标分光比。"],
        )

    parsed: dict = {}
    questions: list[str] = []

    if "mmi" in text or "分束器" in text or "splitter" in text:
        parsed["component"] = "1x2_mmi_splitter"
    else:
        questions.append("请确认器件类型；当前版本支持 1×2 MMI 分束器。")

    if "soi" in text:
        parsed["platform"] = "SOI"
    elif any(token in text for token in ("sin", "linbo3", "lno", "inp")):
        return DesignSpecValidation(
            is_valid=False,
            status=RequestStatus.INVALID,
            errors=["当前公开材料库仅支持 SOI 平台。"],
        )
    else:
        questions.append("请确认光子平台；当前版本支持 SOI。")

    wavelengths = _extract_wavelengths(text)
    unique_wavelengths = sorted({round(value, 9) for value in wavelengths})
    if len(unique_wavelengths) == 1:
        parsed["wavelength_um"] = unique_wavelengths[0]
    elif len(unique_wavelengths) > 1:
        questions.append(
            "检测到多个不同工作波长，请明确本次设计采用哪个中心波长。"
        )
    else:
        questions.append("请提供工作波长，并注明 nm 或 μm。")

    ratio = _extract_split_ratio(text)
    if ratio is None:
        questions.append("请提供目标分光比，例如 50:50。")
    else:
        parsed["target_split_ratio"] = ratio

    if re.search(r"\btm\b", text):
        parsed["polarization"] = "TM"
    elif re.search(r"\bte\b", text):
        parsed["polarization"] = "TE"

    neff_match = re.search(r"neff\s*=?\s*(-?\d+(?:\.\d+)?)", text)
    if neff_match:
        parsed["neff"] = float(neff_match.group(1))
        parsed["use_estimated_neff"] = False

    contextual_fields = {
        "waveguide_width_um": ("waveguide width", "波导宽度"),
        "waveguide_height_um": ("waveguide height", "波导高度"),
        "mmi_width_um": ("mmi width", "mmi宽度", "mmi 宽度"),
    }
    for key, labels in contextual_fields.items():
        extracted = _extract_context_length(text, labels)
        if extracted is not None:
            parsed[key] = extracted

    request_status = (
        RequestStatus.NEEDS_CLARIFICATION if questions else RequestStatus.READY
    )
    try:
        design_spec = DesignSpec.from_legacy(
            parsed,
            source=ParameterSource.USER,
            request_status=request_status,
            clarification_questions=questions,
        )
    except (ValidationError, ValueError, TypeError) as error:
        return DesignSpecValidation(
            is_valid=False,
            status=RequestStatus.INVALID,
            errors=[str(error)],
            clarification_questions=questions,
        )

    return DesignSpecValidation(
        is_valid=request_status == RequestStatus.READY,
        status=request_status,
        clarification_questions=questions,
        design_spec=design_spec,
    )


def parse_design_text(user_text: str) -> dict:
    """V3.2 兼容入口；成功时继续返回旧版扁平字典。"""
    result = parse_design_request(user_text)
    if result.design_spec is None:
        fallback = legacy_defaults()
        fallback["_request_status"] = result.status.value
        fallback["_clarification_questions"] = result.clarification_questions
        fallback["_validation_errors"] = result.errors
        return fallback
    legacy = result.design_spec.to_legacy_dict()
    legacy["_request_status"] = result.status.value
    legacy["_clarification_questions"] = result.clarification_questions
    return legacy
