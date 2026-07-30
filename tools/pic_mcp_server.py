from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.mcp_tools import TOOL_DEFINITIONS, call_tool


def response(request_id: Any, *, result: Any = None, error: Any = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    return payload


def handle_request(request: dict[str, Any]) -> dict | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        return response(
            request_id,
            result={
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "ai-pic-demo-local",
                    "version": "3.3.0",
                },
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return response(request_id, result={"tools": TOOL_DEFINITIONS})
    if method == "tools/call":
        params = request.get("params") or {}
        return response(
            request_id,
            result=call_tool(
                str(params.get("name", "")),
                params.get("arguments") or {},
            ),
        )
    return response(
        request_id,
        error={"code": -32601, "message": f"Method not found: {method}"},
    )


def main() -> None:
    for raw_line in sys.stdin:
        if not raw_line.strip():
            continue
        try:
            request = json.loads(raw_line)
            payload = handle_request(request)
        except Exception as error:
            payload = response(
                None,
                error={
                    "code": -32603,
                    "message": f"{type(error).__name__}: {error}",
                },
            )
        if payload is not None:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
