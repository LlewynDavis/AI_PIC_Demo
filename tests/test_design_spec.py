from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from core.design_spec import (
    DesignSpec,
    ParameterSource,
    RequestStatus,
    legacy_defaults,
    validate_design_spec_payload,
)
from core.spec_parser import parse_design_request, parse_design_text, save_design_spec


class DesignSpecTests(unittest.TestCase):
    def test_standard_request_is_ready(self) -> None:
        result = parse_design_request(
            "请设计 SOI 平台、1550 nm、TE、50:50 的 1x2 MMI 分束器"
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, RequestStatus.READY)
        self.assertAlmostEqual(result.design_spec.wavelength.value, 1.55)

    def test_mixed_units_are_normalized(self) -> None:
        result = parse_design_request(
            "SOI MMI 1550 nm 50:50，波导宽度 500 nm，MMI width 2.5 um"
        )
        legacy = result.design_spec.to_legacy_dict()
        self.assertAlmostEqual(legacy["waveguide_width_um"], 0.5)
        self.assertAlmostEqual(legacy["mmi_width_um"], 2.5)

    def test_missing_wavelength_needs_clarification(self) -> None:
        result = parse_design_request("SOI MMI 50:50")
        self.assertEqual(result.status, RequestStatus.NEEDS_CLARIFICATION)
        self.assertTrue(result.clarification_questions)

    def test_conflicting_wavelength_needs_clarification(self) -> None:
        result = parse_design_request(
            "SOI MMI 波长 1310 nm 和波长 1550 nm，50:50"
        )
        self.assertEqual(result.status, RequestStatus.NEEDS_CLARIFICATION)

    def test_negative_wavelength_is_invalid(self) -> None:
        result = parse_design_request("SOI MMI 波长 -1550 nm 50:50")
        self.assertEqual(result.status, RequestStatus.INVALID)

    def test_invalid_split_ratio_is_rejected(self) -> None:
        payload = legacy_defaults()
        payload["target_split_ratio"] = [0.0, 1.0]
        result = validate_design_spec_payload(payload)
        self.assertFalse(result.is_valid)

    def test_non_positive_geometry_is_rejected(self) -> None:
        payload = legacy_defaults()
        payload["mmi_width_um"] = 0
        result = validate_design_spec_payload(payload)
        self.assertFalse(result.is_valid)

    def test_unknown_solver_is_rejected(self) -> None:
        payload = legacy_defaults()
        payload["mode_solver"] = "unknown_solver"
        result = validate_design_spec_payload(payload)
        self.assertFalse(result.is_valid)

    def test_structured_schema_rejects_missing_required_sections(self) -> None:
        result = validate_design_spec_payload({"schema_version": "1.0"})
        self.assertFalse(result.is_valid)

    def test_legacy_entry_remains_compatible(self) -> None:
        parsed = parse_design_text("SOI MMI 1550 nm 50:50")
        self.assertEqual(parsed["component"], "1x2_mmi_splitter")
        self.assertAlmostEqual(parsed["wavelength_um"], 1.55)

    def test_json_and_yaml_examples_validate(self) -> None:
        root = Path(__file__).resolve().parents[1]
        json_payload = json.loads(
            (root / "config" / "v3.3_design_spec.example.json").read_text(
                encoding="utf-8"
            )
        )
        yaml_payload = yaml.safe_load(
            (root / "config" / "v3.3_design_spec.example.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIsInstance(DesignSpec.model_validate(json_payload), DesignSpec)
        self.assertIsInstance(DesignSpec.model_validate(yaml_payload), DesignSpec)

    def test_saved_spec_is_structured(self) -> None:
        spec = DesignSpec.from_legacy(
            legacy_defaults(),
            source=ParameterSource.DEFAULT,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = save_design_spec(spec, Path(temp_dir))
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertIn("geometry", payload)


if __name__ == "__main__":
    unittest.main()
