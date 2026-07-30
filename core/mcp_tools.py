from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.design_spec import DesignSpec
from core.mmi_model import estimate_mmi_length
from core.spec_parser import parse_design_request


TOOL_DEFINITIONS = [
    {
        "name": "validate_design_spec",
        "description": "Validate a V3.3 PIC DesignSpec or deterministic text request.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "design_spec": {"type": "object"},
                "request_text": {"type": "string"},
            },
        },
    },
    {
        "name": "estimate_mmi_geometry",
        "description": "Estimate the initial MMI self-imaging length.",
        "inputSchema": {
            "type": "object",
            "required": ["design_spec"],
            "properties": {"design_spec": {"type": "object"}},
        },
    },
    {
        "name": "inspect_latest_run",
        "description": "Inspect structured status for the latest local run.",
        "inputSchema": {
            "type": "object",
            "properties": {"output_dir": {"type": "string", "default": "outputs"}},
        },
    },
]


def _structured_result(payload: dict[str, Any], *, is_error: bool = False) -> dict:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False),
            }
        ],
        "structuredContent": payload,
        "isError": is_error,
    }


def validate_design_spec_tool(arguments: dict[str, Any]) -> dict:
    request_text = arguments.get("request_text")
    raw_spec = arguments.get("design_spec")
    if request_text is not None:
        result = parse_design_request(str(request_text))
        payload = result.model_dump(mode="json")
        return _structured_result(payload, is_error=result.status.value == "invalid")
    if raw_spec is None:
        return _structured_result(
            {
                "status": "invalid",
                "errors": ["Provide design_spec or request_text."],
            },
            is_error=True,
        )
    try:
        design_spec = DesignSpec.model_validate(raw_spec)
    except Exception as error:
        return _structured_result(
            {"status": "invalid", "errors": [str(error)]},
            is_error=True,
        )
    return _structured_result(
        {
            "status": design_spec.request_status.value,
            "is_valid": design_spec.request_status.value == "ready",
            "clarification_questions": design_spec.clarification_questions,
            "design_spec": design_spec.model_dump(mode="json"),
        }
    )


def estimate_mmi_geometry_tool(arguments: dict[str, Any]) -> dict:
    try:
        design_spec = DesignSpec.model_validate(arguments["design_spec"])
        legacy = design_spec.to_legacy_dict()
        length_um = estimate_mmi_length(
            wavelength_um=legacy["wavelength_um"],
            neff=legacy["neff"],
            mmi_width_um=legacy["mmi_width_um"],
        )
    except Exception as error:
        return _structured_result(
            {"status": "invalid", "errors": [str(error)]},
            is_error=True,
        )
    return _structured_result(
        {
            "status": "success",
            "mmi_width_um": legacy["mmi_width_um"],
            "estimated_length_um": float(length_um),
            "model": "V3.2 simplified self-imaging estimate",
            "boundary": "Not a full-vector electromagnetic result.",
        }
    )


def inspect_latest_run_tool(arguments: dict[str, Any]) -> dict:
    output_dir = Path(arguments.get("output_dir", "outputs"))
    if not output_dir.exists():
        return _structured_result(
            {"status": "not_found", "message": f"{output_dir} does not exist."}
        )
    run_dirs = sorted(
        (
            item
            for item in output_dir.iterdir()
            if item.is_dir() and item.name.startswith("run_")
        ),
        key=lambda item: item.name,
        reverse=True,
    )
    if not run_dirs:
        return _structured_result(
            {"status": "not_found", "message": "No run_* directory found."}
        )
    latest = run_dirs[0]
    status_path = latest / "status.json"
    manifest_path = latest / "run_manifest.json"
    payload: dict[str, Any] = {
        "status": "found",
        "run_directory": str(latest),
        "has_status": status_path.exists(),
        "has_manifest": manifest_path.exists(),
    }
    if status_path.exists():
        try:
            payload["latest_status"] = json.loads(
                status_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as error:
            payload["status_read_error"] = str(error)
    return _structured_result(payload)


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict:
    tools = {
        "validate_design_spec": validate_design_spec_tool,
        "estimate_mmi_geometry": estimate_mmi_geometry_tool,
        "inspect_latest_run": inspect_latest_run_tool,
    }
    handler = tools.get(name)
    if handler is None:
        return _structured_result(
            {"status": "invalid", "errors": [f"Unknown tool: {name}"]},
            is_error=True,
        )
    try:
        return handler(arguments or {})
    except Exception as error:
        return _structured_result(
            {"status": "failed", "errors": [f"{type(error).__name__}: {error}"]},
            is_error=True,
        )
