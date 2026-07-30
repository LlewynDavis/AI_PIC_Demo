from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.design_spec import DesignSpec, legacy_defaults
from core.mcp_tools import TOOL_DEFINITIONS, call_tool
from core.run_status import RunStatusTracker, StageCode
from tools.pic_mcp_client import LocalMcpClient


class RunStatusAndMcpTests(unittest.TestCase):
    def test_stage_codes_cover_required_pipeline(self) -> None:
        self.assertEqual(
            {item.value for item in StageCode},
            {"IE", "SV", "PH", "MODE", "OPT", "BPM", "OVL", "LAY", "REP", "SUCCESS"},
        )

    def test_run_tracker_writes_manifest_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            tracker = RunStatusTracker(
                run_dir,
                demo_version="V3.3",
                design_spec_schema_version="1.0",
            )
            tracker.success()
            manifest = json.loads(
                (run_dir / "run_manifest.json").read_text(encoding="utf-8")
            )
            status = json.loads(
                (run_dir / "status.json").read_text(encoding="utf-8")
            )
        self.assertEqual(manifest["state"], "success")
        self.assertEqual(status["code"], "SUCCESS")

    def test_mcp_tool_names_are_stable(self) -> None:
        self.assertEqual(
            {item["name"] for item in TOOL_DEFINITIONS},
            {
                "validate_design_spec",
                "estimate_mmi_geometry",
                "inspect_latest_run",
            },
        )

    def test_validate_tool_returns_structured_error(self) -> None:
        result = call_tool("validate_design_spec", {"design_spec": {}})
        self.assertTrue(result["isError"])
        self.assertEqual(result["structuredContent"]["status"], "invalid")

    def test_estimate_tool_uses_design_spec(self) -> None:
        design_spec = DesignSpec.from_legacy(legacy_defaults())
        result = call_tool(
            "estimate_mmi_geometry",
            {"design_spec": design_spec.model_dump(mode="json")},
        )
        self.assertFalse(result["isError"])
        self.assertGreater(
            result["structuredContent"]["estimated_length_um"],
            0,
        )

    def test_inspect_latest_run_without_outputs_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = call_tool(
                "inspect_latest_run",
                {"output_dir": str(Path(temp_dir) / "missing")},
            )
        self.assertFalse(result["isError"])
        self.assertEqual(result["structuredContent"]["status"], "not_found")

    def test_stdio_client_lists_and_calls_tools(self) -> None:
        with LocalMcpClient() as client:
            names = {item["name"] for item in client.list_tools()}
            result = client.call_tool(
                "validate_design_spec",
                {"request_text": "SOI MMI 1550 nm 50:50"},
            )
        self.assertIn("validate_design_spec", names)
        self.assertFalse(result["isError"])


if __name__ == "__main__":
    unittest.main()
