import json
from pathlib import Path
from typing import Any


def _format_value(value: Any, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.{digits}f}"


def append_v31_calibration_section(
    report_path: Path,
    output_dir: Path,
) -> Path:
    """向中文报告追加 V3.1 传播校准与模型对比章节。"""
    report_path = Path(report_path)
    output_dir = Path(output_dir)
    sensitivity_path = output_dir / "output_window_sensitivity_result.json"
    comparison_path = output_dir / "model_comparison_result.json"

    if not report_path.exists():
        raise FileNotFoundError(f"报告文件不存在：{report_path}")
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"窗口敏感性结果不存在：{sensitivity_path}")
    if not comparison_path.exists():
        raise FileNotFoundError(f"模型对比结果不存在：{comparison_path}")

    sensitivity = json.loads(sensitivity_path.read_text(encoding="utf-8"))
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    window_rows = "\n".join(
        "| {window:.3f} | {p1} | {p2} | {total} | {loss} |".format(
            window=float(item["output_window_um"]),
            p1=_format_value(item.get("p_out1")),
            p2=_format_value(item.get("p_out2")),
            total=_format_value(item.get("total_collected_power")),
            loss=_format_value(
                item.get("window_based_insertion_loss_db")
            ),
        )
        for item in sensitivity.get("window_results", [])
    )
    surrogate = comparison.get("surrogate_model", {})
    bpm = comparison.get("bpm_model", {})
    difference = comparison.get("difference", {})

    section = f"""

---

## V3.1 传播仿真校准与模型对比分析

### 一、校准目的

V3.1 不改变 V3.0 的二维标量 BPM 基本传播模型，而是通过输出窗口宽度敏感性和 surrogate/BPM 模型对比，提高传播结果的可解释性。重点是说明输出功率与窗口选择之间的关系，而不是追求两个模型的严格数值一致。

### 二、输出窗口宽度敏感性

| 输出窗口宽度 / μm | P1 | P2 | 总收集功率 | Window-based loss / dB |
|---:|---:|---:|---:|---:|
{window_rows}

随着 `output_window_um` 增大，端口窗口覆盖的空间范围增大，因此 `total_collected_power` 通常也会增大。该变化反映的是积分区域选择，而不是器件材料吸收或辐射损耗本身发生变化。

![V3.1 输出窗口宽度敏感性](output_window_sensitivity.png)

### 三、Window-based insertion loss 说明

`propagation_result.json` 保留 `insertion_loss_db` 作为 V3.0 兼容字段。V3.1 推荐使用 `window_based_insertion_loss_db`，明确它是根据两个输出窗口收集功率计算的等效损耗。

该指标不能等同于真实器件插入损耗，因为当前方法没有执行严格输出模式重叠、端口归一化或全矢量 S 参数提取。

### 四、Surrogate model 与 BPM model 对比

| 指标 | Surrogate model | BPM window integration |
|---|---:|---:|
| Output 1 | {_format_value(surrogate.get("p_out1"))} | {_format_value(bpm.get("p_out1"))} |
| Output 2 | {_format_value(surrogate.get("p_out2"))} | {_format_value(bpm.get("p_out2"))} |
| Total power | {_format_value(surrogate.get("total_power"))} | {_format_value(bpm.get("total_collected_power"))} |
| Imbalance / dB | {_format_value(surrogate.get("imbalance_db"))} | {_format_value(bpm.get("imbalance_db"))} |
| Insertion loss / dB | {_format_value(surrogate.get("insertion_loss_db"))} | {_format_value(bpm.get("window_based_insertion_loss_db"))} |

总功率差值（BPM - surrogate）为 `{_format_value(difference.get("delta_total_power"))}`。Surrogate model 用于快速参数优化；BPM model 用于传播趋势可视化和窗口积分功率估算。两者并不表示完全相同的物理量，因此该对比只用于趋势验证。

![V3.1 Surrogate 与 BPM 模型对比](model_comparison.png)

### 五、增强传播图

增强图使用归一化 dB 动态范围，并标记 MMI 横向边界、输出平面和端口中心，使分束趋势更易观察。

![V3.1 增强版 BPM 光场传播图](field_propagation_enhanced.png)

### 六、生成文件

- `field_propagation_enhanced.png`
- `output_window_sensitivity.png`
- `output_window_sensitivity_result.json`
- `model_comparison.png`
- `model_comparison_result.json`

### 七、模型边界

1. 当前传播方法仍是二维标量 BPM 近似；
2. 输出功率来自简单空间窗口积分；
3. `window_based_insertion_loss_db` 不是严格器件插入损耗；
4. Surrogate model 和 BPM model 不属于完全相同的物理层级；
5. 当前结果不是严格全矢量模式重叠或 S 参数提取。
"""

    with report_path.open("a", encoding="utf-8") as report_file:
        report_file.write(section)
    return report_path
