from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "tools" / "pic_mcp_server.py"


class LocalMcpClient:
    def __init__(self) -> None:
        self.process = subprocess.Popen(
            [sys.executable, str(SERVER_PATH)],
            cwd=PROJECT_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        self._request_id = 0
        self.request(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "ai-pic-demo-client", "version": "3.3.0"},
            },
        )
        self.notify("notifications/initialized")

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict:
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }
        self._send(payload)
        assert self.process.stdout is not None
        line = self.process.stdout.readline()
        if not line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read()
            raise RuntimeError(f"MCP server stopped without a response: {stderr}")
        response = json.loads(line)
        if "error" in response:
            raise RuntimeError(response["error"])
        return response["result"]

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _send(self, payload: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise RuntimeError("MCP server stdin is unavailable.")
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def list_tools(self) -> list[dict[str, Any]]:
        return self.request("tools/list")["tools"]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        return self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.poll() is None:
            self.process.terminate()
        self.process.wait(timeout=5)
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()

    def __enter__(self) -> "LocalMcpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI_PIC_Demo local MCP client")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="List and call all three local tools.",
    )
    args = parser.parse_args()

    with LocalMcpClient() as client:
        tools = client.list_tools()
        print(json.dumps({"tools": [item["name"] for item in tools]}, indent=2))
        if not args.smoke_test:
            return

        validate_result = client.call_tool(
            "validate_design_spec",
            {
                "request_text": (
                    "设计一个 SOI 平台、1550 nm、TE、50:50 的 1x2 MMI 分束器"
                )
            },
        )
        structured_spec = validate_result["structuredContent"]["design_spec"]
        estimate_result = client.call_tool(
            "estimate_mmi_geometry",
            {"design_spec": structured_spec},
        )
        inspect_result = client.call_tool("inspect_latest_run", {})
        print(
            json.dumps(
                {
                    "validate_design_spec": validate_result,
                    "estimate_mmi_geometry": estimate_result,
                    "inspect_latest_run": inspect_result,
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
