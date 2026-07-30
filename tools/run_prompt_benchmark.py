from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.design_spec import DesignSpec
from core.spec_parser import parse_design_request
from core.validation import validate_design_spec


DEFAULT_DATASET = PROJECT_ROOT / "benchmarks" / "v3.3" / "requirements.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "benchmarks" / "v3.3" / "benchmark_result.json"


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def values_match(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float):
        return abs(float(actual) - expected) <= 1e-9
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            values_match(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected)
        )
    return actual == expected


def run_benchmark(cases: list[dict[str, Any]]) -> dict[str, Any]:
    started = perf_counter()
    details: list[dict[str, Any]] = []
    failure_stages: Counter[str] = Counter()
    parse_passes = 0
    schema_passes = 0
    end_to_end_passes = 0

    for case in cases:
        case_started = perf_counter()
        result = parse_design_request(case["request"])
        actual_status = result.status.value
        if actual_status == "ready":
            failure_stage = "success"
        elif actual_status == "needs_clarification":
            failure_stage = "input_extraction"
        else:
            failure_stage = "schema_validation"
        failure_stages[failure_stage] += 1
        legacy = result.design_spec.to_legacy_dict() if result.design_spec else {}
        expected_values = case.get("expected", {})
        fields_match = all(
            key in legacy and values_match(legacy[key], expected)
            for key, expected in expected_values.items()
        )
        parse_ok = actual_status == case["expected_status"] and fields_match
        parse_passes += int(parse_ok)

        schema_ok = result.design_spec is None and actual_status in {
            "needs_clarification",
            "invalid",
        }
        end_to_end_ok = False
        if result.design_spec is not None:
            try:
                DesignSpec.model_validate(result.design_spec.model_dump(mode="json"))
                schema_ok = True
            except Exception:
                schema_ok = False
            if actual_status == "ready":
                end_to_end_ok = validate_design_spec(legacy).is_valid
        schema_passes += int(schema_ok)
        end_to_end_passes += int(end_to_end_ok)

        details.append(
            {
                "id": case["id"],
                "category": case["category"],
                "expected_status": case["expected_status"],
                "actual_status": actual_status,
                "parse_pass": parse_ok,
                "schema_pass": schema_ok,
                "end_to_end_pass": end_to_end_ok,
                "failure_stage": failure_stage,
                "elapsed_ms": round((perf_counter() - case_started) * 1000, 3),
            }
        )

    total = len(cases)
    ready_cases = sum(case["expected_status"] == "ready" for case in cases)
    return {
        "benchmark_version": "V3.3",
        "dataset_size": total,
        "parsing_accuracy": parse_passes / total if total else 0.0,
        "schema_pass_rate": schema_passes / total if total else 0.0,
        "end_to_end_success_rate": (
            end_to_end_passes / ready_cases if ready_cases else 0.0
        ),
        "failure_stage_distribution": dict(failure_stages),
        "total_runtime_ms": round((perf_counter() - started) * 1000, 3),
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the V3.3 prompt benchmark.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = run_benchmark(load_cases(args.dataset))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
