import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


def _result_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    """兼容不同版本中可能存在的嵌套优化结果结构。"""
    candidates = [result]
    for key in ("best_result", "result"):
        nested = result.get(key)
        if isinstance(nested, dict):
            candidates.append(nested)
    return candidates


def _read_float(
    result: dict[str, Any],
    keys: tuple[str, ...],
    default: float | None = None,
) -> float:
    for candidate in _result_candidates(result):
        for key in keys:
            value = candidate.get(key)
            if value is not None:
                return float(value)
    if default is not None:
        return float(default)
    raise KeyError(f"未找到兼容字段：{', '.join(keys)}")


def save_model_comparison_plot(
    comparison_result: dict[str, Any],
    output_path: Path,
) -> Path:
    """保存 surrogate 与 BPM 输出功率对比柱状图。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    labels = ["Output 1", "Output 2", "Total power"]
    surrogate = comparison_result["surrogate_model"]
    bpm = comparison_result["bpm_model"]
    surrogate_values = [
        surrogate["p_out1"],
        surrogate["p_out2"],
        surrogate["total_power"],
    ]
    bpm_values = [
        bpm["p_out1"],
        bpm["p_out2"],
        bpm["total_collected_power"],
    ]

    positions = list(range(len(labels)))
    bar_width = 0.36
    figure, axis = plt.subplots(figsize=(8.2, 4.8))
    axis.bar(
        [position - bar_width / 2 for position in positions],
        surrogate_values,
        width=bar_width,
        color="tab:blue",
        label="Surrogate model",
    )
    axis.bar(
        [position + bar_width / 2 for position in positions],
        bpm_values,
        width=bar_width,
        color="tab:orange",
        label="Scalar BPM window integration",
    )
    axis.set_title("V3.1 Surrogate vs BPM Model Comparison")
    axis.set_xlabel("Power metric")
    axis.set_ylabel("Normalized power")
    axis.set_xticks(positions, labels)
    axis.set_ylim(bottom=0)
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return output_path


def run_model_comparison_analysis(
    optimization_result: dict[str, Any],
    propagation_result: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """比较 surrogate 优化结果与 BPM 窗口积分结果。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    surrogate_p_out1 = _read_float(
        optimization_result,
        ("p_out1", "output_port_1"),
    )
    surrogate_p_out2 = _read_float(
        optimization_result,
        ("p_out2", "output_port_2"),
    )
    surrogate_total = surrogate_p_out1 + surrogate_p_out2
    surrogate_imbalance = _read_float(
        optimization_result,
        ("imbalance_db",),
        default=10
        * math.log10(
            max(surrogate_p_out1, 1e-12)
            / max(surrogate_p_out2, 1e-12)
        ),
    )
    surrogate_insertion_loss = _read_float(
        optimization_result,
        ("insertion_loss_db",),
        default=-10 * math.log10(max(surrogate_total, 1e-12)),
    )

    bpm_p_out1 = _read_float(propagation_result, ("p_out1",))
    bpm_p_out2 = _read_float(propagation_result, ("p_out2",))
    bpm_total = _read_float(
        propagation_result,
        ("total_collected_power",),
        default=bpm_p_out1 + bpm_p_out2,
    )
    bpm_imbalance = _read_float(
        propagation_result,
        ("imbalance_db",),
        default=10
        * math.log10(max(bpm_p_out1, 1e-12) / max(bpm_p_out2, 1e-12)),
    )
    bpm_window_loss = _read_float(
        propagation_result,
        ("window_based_insertion_loss_db", "insertion_loss_db"),
        default=-10 * math.log10(max(bpm_total, 1e-12)),
    )

    result: dict[str, Any] = {
        "analysis_type": "surrogate_vs_bpm_comparison",
        "version": "V3.1_propagation_calibration",
        "surrogate_model": {
            "source": "core/mmi_model.py",
            "p_out1": surrogate_p_out1,
            "p_out2": surrogate_p_out2,
            "total_power": surrogate_total,
            "imbalance_db": surrogate_imbalance,
            "insertion_loss_db": surrogate_insertion_loss,
        },
        "bpm_model": {
            "source": "core/propagation_solver.py",
            "p_out1": bpm_p_out1,
            "p_out2": bpm_p_out2,
            "total_collected_power": bpm_total,
            "imbalance_db": bpm_imbalance,
            "window_based_insertion_loss_db": bpm_window_loss,
        },
        "difference": {
            "delta_p_out1": bpm_p_out1 - surrogate_p_out1,
            "delta_p_out2": bpm_p_out2 - surrogate_p_out2,
            "delta_total_power": bpm_total - surrogate_total,
            "delta_imbalance_db": bpm_imbalance - surrogate_imbalance,
            "delta_insertion_loss_db": (
                bpm_window_loss - surrogate_insertion_loss
            ),
        },
        "interpretation": (
            "The surrogate model is used for fast parameter optimization, "
            "while the BPM model provides a propagation-based field "
            "visualization and window-based output power estimation."
        ),
        "limitations": [
            "The two models do not represent the exact same physical quantity.",
            "The BPM output powers are based on spatial window integration.",
            "The comparison is intended for trend validation rather than strict numerical agreement.",
        ],
    }

    result_path = output_dir / "model_comparison_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    plot_path = save_model_comparison_plot(
        comparison_result=result,
        output_path=output_dir / "model_comparison.png",
    )
    result.update(
        {
            "model_comparison_result_path": str(result_path),
            "model_comparison_plot_path": str(plot_path),
        }
    )
    return result
