from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


DESIGN_SPEC_VERSION = "1.0"


class ParameterSource(str, Enum):
    USER = "user"
    DEFAULT = "default"
    FORMULA = "formula"
    OPTIMIZER = "optimizer"
    UNVERIFIED = "unverified"


class RequestStatus(str, Enum):
    READY = "ready"
    NEEDS_CLARIFICATION = "needs_clarification"
    INVALID = "invalid"


class SourcedFloat(BaseModel):
    value: float
    unit: str = ""
    source: ParameterSource


class SourcedInt(BaseModel):
    value: int
    unit: str = ""
    source: ParameterSource


class SourcedBool(BaseModel):
    value: bool
    source: ParameterSource


class SourcedText(BaseModel):
    value: str
    source: ParameterSource


class SourcedTextList(BaseModel):
    value: list[str]
    source: ParameterSource


class SourcedRange(BaseModel):
    minimum: float
    maximum: float
    unit: str
    source: ParameterSource

    @field_validator("minimum", "maximum")
    @classmethod
    def require_positive_bounds(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("range bounds must be greater than zero")
        return value

    def model_post_init(self, __context: Any) -> None:
        if self.maximum <= self.minimum:
            raise ValueError("range maximum must be greater than minimum")


class SplitRatio(BaseModel):
    values: tuple[float, float]
    source: ParameterSource

    @field_validator("values")
    @classmethod
    def validate_ratio(cls, values: tuple[float, float]) -> tuple[float, float]:
        if len(values) != 2 or any(value <= 0 for value in values):
            raise ValueError("split ratio must contain two positive values")
        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError("split ratio must sum to one")
        return values


class DeviceSpec(BaseModel):
    type: SourcedText
    input_ports: SourcedInt
    output_ports: SourcedInt


class PlatformSpec(BaseModel):
    name: SourcedText
    core_material: SourcedText
    cladding_material: SourcedText


class GeometrySpec(BaseModel):
    waveguide_width: SourcedFloat
    waveguide_height: SourcedFloat
    mmi_width: SourcedFloat
    length_scan: SourcedRange
    mmi_width_scan: SourcedRange

    @field_validator("waveguide_width", "waveguide_height", "mmi_width")
    @classmethod
    def require_positive_geometry(cls, item: SourcedFloat) -> SourcedFloat:
        if item.value <= 0:
            raise ValueError("geometry values must be greater than zero")
        return item

    @model_validator(mode="after")
    def validate_geometry_relationships(self) -> "GeometrySpec":
        if self.waveguide_width.value >= self.mmi_width.value:
            raise ValueError("waveguide width must be smaller than MMI width")
        return self


class TargetSpec(BaseModel):
    split_ratio: SplitRatio


class SimulationSpec(BaseModel):
    mode_solver: SourcedText
    propagation_solver: SourcedText
    use_estimated_neff: SourcedBool
    neff: SourcedFloat
    length_scan_points: SourcedInt
    width_scan_points: SourcedInt

    @field_validator("mode_solver")
    @classmethod
    def validate_mode_solver(cls, item: SourcedText) -> SourcedText:
        allowed = {"scalar_fd_2d", "manual_neff"}
        if item.value not in allowed:
            raise ValueError(f"unknown mode solver: {item.value}")
        return item

    @field_validator("propagation_solver")
    @classmethod
    def validate_propagation_solver(cls, item: SourcedText) -> SourcedText:
        allowed = {"scalar_bpm_2d", "disabled"}
        if item.value not in allowed:
            raise ValueError(f"unknown propagation solver: {item.value}")
        return item

    @field_validator("length_scan_points", "width_scan_points")
    @classmethod
    def validate_scan_points(cls, item: SourcedInt) -> SourcedInt:
        if item.value < 20:
            raise ValueError("scan points must be at least 20")
        return item

    @field_validator("neff")
    @classmethod
    def validate_neff(cls, item: SourcedFloat) -> SourcedFloat:
        if item.value <= 1.0:
            raise ValueError("neff must be greater than 1.0")
        return item


class OutputSpec(BaseModel):
    directory: SourcedText
    formats: SourcedTextList


class DesignSpec(BaseModel):
    """V3.3 统一 PIC 设计规格。

    该模型只组织参数、来源和流程约束，不替代任何物理求解器。
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = DESIGN_SPEC_VERSION
    request_status: RequestStatus = RequestStatus.READY
    clarification_questions: list[str] = Field(default_factory=list)
    device: DeviceSpec
    platform: PlatformSpec
    wavelength: SourcedFloat
    polarization: SourcedText
    geometry: GeometrySpec
    targets: TargetSpec
    simulation: SimulationSpec
    outputs: OutputSpec

    @field_validator("wavelength")
    @classmethod
    def validate_wavelength(cls, item: SourcedFloat) -> SourcedFloat:
        if item.value <= 0:
            raise ValueError("wavelength must be greater than zero")
        if item.unit != "um":
            raise ValueError("canonical wavelength unit must be um")
        return item

    @field_validator("polarization")
    @classmethod
    def validate_polarization(cls, item: SourcedText) -> SourcedText:
        if item.value not in {"TE", "TM"}:
            raise ValueError("polarization must be TE or TM")
        return item

    def to_legacy_dict(self) -> dict[str, Any]:
        """转换为 V3.2 物理流程使用的兼容字典。"""
        return {
            "component": self.device.type.value,
            "platform": self.platform.name.value,
            "wavelength_um": self.wavelength.value,
            "polarization": self.polarization.value,
            "use_estimated_neff": self.simulation.use_estimated_neff.value,
            "neff": self.simulation.neff.value,
            "waveguide_width_um": self.geometry.waveguide_width.value,
            "waveguide_height_um": self.geometry.waveguide_height.value,
            "mmi_width_um": self.geometry.mmi_width.value,
            "target_split_ratio": list(self.targets.split_ratio.values),
            "length_scan_range_um": [
                self.geometry.length_scan.minimum,
                self.geometry.length_scan.maximum,
            ],
            "num_scan_points": self.simulation.length_scan_points.value,
            "mmi_width_scan_range_um": [
                self.geometry.mmi_width_scan.minimum,
                self.geometry.mmi_width_scan.maximum,
            ],
            "num_width_scan_points": self.simulation.width_scan_points.value,
        }

    def save_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def save_yaml(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                self.model_dump(mode="json"),
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return path

    @classmethod
    def from_legacy(
        cls,
        legacy: dict[str, Any],
        *,
        source: ParameterSource = ParameterSource.USER,
        request_status: RequestStatus = RequestStatus.READY,
        clarification_questions: list[str] | None = None,
    ) -> "DesignSpec":
        defaults = legacy_defaults()

        def value(key: str) -> Any:
            return legacy.get(key, defaults[key])

        def field_source(key: str) -> ParameterSource:
            return source if key in legacy else ParameterSource.DEFAULT

        platform_name = str(value("platform")).upper()
        if platform_name != "SOI":
            raise ValueError(f"unsupported platform: {platform_name}")

        ratio_values = tuple(float(item) for item in value("target_split_ratio"))
        return cls(
            request_status=request_status,
            clarification_questions=clarification_questions or [],
            device=DeviceSpec(
                type=SourcedText(
                    value=str(value("component")),
                    source=field_source("component"),
                ),
                input_ports=SourcedInt(value=1, source=ParameterSource.FORMULA),
                output_ports=SourcedInt(value=2, source=ParameterSource.FORMULA),
            ),
            platform=PlatformSpec(
                name=SourcedText(
                    value=platform_name,
                    source=field_source("platform"),
                ),
                core_material=SourcedText(
                    value="Si",
                    source=ParameterSource.DEFAULT,
                ),
                cladding_material=SourcedText(
                    value="SiO2",
                    source=ParameterSource.DEFAULT,
                ),
            ),
            wavelength=SourcedFloat(
                value=float(value("wavelength_um")),
                unit="um",
                source=field_source("wavelength_um"),
            ),
            polarization=SourcedText(
                value=str(legacy.get("polarization", "TE")).upper(),
                source=field_source("polarization"),
            ),
            geometry=GeometrySpec(
                waveguide_width=SourcedFloat(
                    value=float(value("waveguide_width_um")),
                    unit="um",
                    source=field_source("waveguide_width_um"),
                ),
                waveguide_height=SourcedFloat(
                    value=float(value("waveguide_height_um")),
                    unit="um",
                    source=field_source("waveguide_height_um"),
                ),
                mmi_width=SourcedFloat(
                    value=float(value("mmi_width_um")),
                    unit="um",
                    source=field_source("mmi_width_um"),
                ),
                length_scan=SourcedRange(
                    minimum=float(value("length_scan_range_um")[0]),
                    maximum=float(value("length_scan_range_um")[1]),
                    unit="um",
                    source=field_source("length_scan_range_um"),
                ),
                mmi_width_scan=SourcedRange(
                    minimum=float(value("mmi_width_scan_range_um")[0]),
                    maximum=float(value("mmi_width_scan_range_um")[1]),
                    unit="um",
                    source=field_source("mmi_width_scan_range_um"),
                ),
            ),
            targets=TargetSpec(
                split_ratio=SplitRatio(
                    values=ratio_values,
                    source=field_source("target_split_ratio"),
                )
            ),
            simulation=SimulationSpec(
                mode_solver=SourcedText(
                    value=str(legacy.get("mode_solver", "scalar_fd_2d")),
                    source=field_source("mode_solver"),
                ),
                propagation_solver=SourcedText(
                    value=str(legacy.get("propagation_solver", "scalar_bpm_2d")),
                    source=field_source("propagation_solver"),
                ),
                use_estimated_neff=SourcedBool(
                    value=bool(value("use_estimated_neff")),
                    source=field_source("use_estimated_neff"),
                ),
                neff=SourcedFloat(
                    value=float(value("neff")),
                    source=field_source("neff"),
                ),
                length_scan_points=SourcedInt(
                    value=int(value("num_scan_points")),
                    source=field_source("num_scan_points"),
                ),
                width_scan_points=SourcedInt(
                    value=int(value("num_width_scan_points")),
                    source=field_source("num_width_scan_points"),
                ),
            ),
            outputs=OutputSpec(
                directory=SourcedText(
                    value=str(legacy.get("output_dir", "outputs")),
                    source=field_source("output_dir"),
                ),
                formats=SourcedTextList(
                    value=["json", "png", "gds", "md", "zip"],
                    source=ParameterSource.DEFAULT,
                ),
            ),
        )


class DesignSpecValidation(BaseModel):
    is_valid: bool
    status: RequestStatus
    errors: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    design_spec: DesignSpec | None = None


def legacy_defaults() -> dict[str, Any]:
    return {
        "component": "1x2_mmi_splitter",
        "platform": "SOI",
        "wavelength_um": 1.55,
        "polarization": "TE",
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


def validate_design_spec_payload(payload: dict[str, Any]) -> DesignSpecValidation:
    try:
        if "schema_version" in payload:
            design_spec = DesignSpec.model_validate(payload)
        else:
            design_spec = DesignSpec.from_legacy(payload)
    except (ValidationError, ValueError, TypeError) as error:
        return DesignSpecValidation(
            is_valid=False,
            status=RequestStatus.INVALID,
            errors=[str(error)],
        )

    questions = list(design_spec.clarification_questions)
    status = (
        RequestStatus.NEEDS_CLARIFICATION
        if questions
        else design_spec.request_status
    )
    return DesignSpecValidation(
        is_valid=status == RequestStatus.READY,
        status=status,
        clarification_questions=questions,
        design_spec=design_spec,
    )
