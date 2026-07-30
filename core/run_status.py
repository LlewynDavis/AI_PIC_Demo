from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class StageCode(str, Enum):
    INPUT_EXTRACTION = "IE"
    SCHEMA_VALIDATION = "SV"
    PHYSICAL_PARAMETERS = "PH"
    MODE_SOLVER = "MODE"
    OPTIMIZATION = "OPT"
    PROPAGATION = "BPM"
    MODE_OVERLAP = "OVL"
    LAYOUT = "LAY"
    REPORT = "REP"
    SUCCESS = "SUCCESS"


class StageEvent(BaseModel):
    code: StageCode
    stage: str
    state: str
    message: str
    recoverable: bool
    suggested_action: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now().astimezone().isoformat(timespec="seconds")
    )


class RunManifest(BaseModel):
    manifest_version: str = "1.0"
    demo_version: str
    design_spec_schema_version: str
    run_directory: str
    state: str = "in_progress"
    current_stage: StageCode = StageCode.INPUT_EXTRACTION
    supported_codes: list[str] = Field(
        default_factory=lambda: [code.value for code in StageCode]
    )
    events: list[StageEvent] = Field(default_factory=list)


class RunStatusTracker:
    """将运行阶段写入结构化 run_manifest.json 和 status.json。"""

    def __init__(
        self,
        run_dir: Path,
        *,
        demo_version: str,
        design_spec_schema_version: str,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.manifest_path = self.run_dir / "run_manifest.json"
        self.status_path = self.run_dir / "status.json"
        self.manifest = RunManifest(
            demo_version=demo_version,
            design_spec_schema_version=design_spec_schema_version,
            run_directory=str(self.run_dir),
        )
        self.record(
            StageCode.INPUT_EXTRACTION,
            stage="input_extraction",
            state="started",
            message="Run initialized.",
            recoverable=True,
            suggested_action="Provide or parse a design request.",
        )

    def record(
        self,
        code: StageCode,
        *,
        stage: str,
        state: str,
        message: str,
        recoverable: bool,
        suggested_action: str,
    ) -> None:
        event = StageEvent(
            code=code,
            stage=stage,
            state=state,
            message=message,
            recoverable=recoverable,
            suggested_action=suggested_action,
        )
        self.manifest.current_stage = code
        self.manifest.events.append(event)
        if code == StageCode.SUCCESS and state == "success":
            self.manifest.state = "success"
        elif state == "failed" and not recoverable:
            self.manifest.state = "failed"
        self._write(event)

    def success(self, message: str = "Run completed successfully.") -> None:
        self.record(
            StageCode.SUCCESS,
            stage="complete",
            state="success",
            message=message,
            recoverable=False,
            suggested_action="Inspect the generated report and artifacts.",
        )

    def _write(self, latest_event: StageEvent) -> None:
        self.manifest_path.write_text(
            self.manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        self.status_path.write_text(
            json.dumps(
                {
                    "manifest_version": self.manifest.manifest_version,
                    "demo_version": self.manifest.demo_version,
                    "state": self.manifest.state,
                    "code": latest_event.code.value,
                    "stage": latest_event.stage,
                    "message": latest_event.message,
                    "recoverable": latest_event.recoverable,
                    "suggested_action": latest_event.suggested_action,
                    "timestamp": latest_event.timestamp,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
