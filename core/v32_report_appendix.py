import json
from pathlib import Path
from typing import Any


def _format_value(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def append_v32_mode_overlap_section(
    report_path: Path,
    output_dir: Path,
) -> None:
    """向中文报告追加 V3.2 端口模式重叠积分章节。"""
    report_path = Path(report_path)
    output_dir = Path(output_dir)
    result_path = output_dir / "mode_overlap_result.json"
    if not report_path.exists():
        raise FileNotFoundError(f"未找到报告文件：{report_path}")
    if not result_path.exists():
        raise FileNotFoundError(f"未找到模式重叠结果：{result_path}")

    result = json.loads(result_path.read_text(encoding="utf-8"))
    reference = result.get("window_based_reference", {})
    section = f"""

---

## V3.2 端口模式重叠积分分析

### 一、分析目的

V3.2 在 V3.1 输出窗口敏感性分析的基础上，引入简化 Gaussian 输出端口模式，并将二维标量 BPM 的最终复数场投影到两个端口模式上。该方法使功率估算具备模式选择性，比单纯对空间窗口内强度积分更接近端口模式功率提取。

### 二、从窗口积分升级到模式重叠

窗口积分会收集指定横向范围内的全部场强，其结果随 `output_window_um` 明显变化。模式重叠积分则计算 BPM 输出复数场与目标端口模式之间的复振幅投影，只统计与所选 Gaussian 模式匹配的场分量。

当前端口模式采用中心位于两个输出端口、宽度为 `{_format_value(result.get('port_mode_width_um'), 3)} μm` 的归一化 Gaussian 场，并满足 `∫|φ(x)|²dx = 1`。

### 三、重叠积分结果

| 指标 | 数值 |
|---|---:|
| overlap_p_out1 | {_format_value(result.get('overlap_p_out1'))} |
| overlap_p_out2 | {_format_value(result.get('overlap_p_out2'))} |
| total_overlap_power | {_format_value(result.get('total_overlap_power'))} |
| overlap_imbalance_db | {_format_value(result.get('overlap_imbalance_db'))} dB |
| overlap_based_insertion_loss_db | {_format_value(result.get('overlap_based_insertion_loss_db'))} dB |

### 四、Window-based 与 overlap-based 的区别

默认窗口积分收集功率为 `{_format_value(reference.get('total_collected_power'))}`，对应 window-based insertion loss 为 `{_format_value(reference.get('window_based_insertion_loss_db'))} dB`；模式重叠总功率为 `{_format_value(result.get('total_overlap_power'))}`，对应 overlap-based insertion loss 为 `{_format_value(result.get('overlap_based_insertion_loss_db'))} dB`。

两者计算对象不同：窗口积分衡量空间区域内的总强度，模式重叠衡量输出场与指定端口模式的匹配分量。因此 overlap-based power 更具模式意识，但不能据此宣称获得了严格器件 S 参数。

![V3.2 输出场与 Gaussian 端口模式](field_output_profile_with_modes.png)

![V3.2 三类功率估算对比](mode_overlap_comparison.png)

### 五、生成文件

- `bpm_final_field_data.npz`
- `mode_overlap_result.json`
- `mode_overlap_comparison.png`
- `field_output_profile_with_modes.png`

### 六、模型边界

- 输出端口模式是简化 Gaussian 近似，不是真实波导全矢量本征模式；
- 传播场仍来自二维标量 BPM 近似；
- 当前计算不是严格全矢量 eigenmode expansion；
- 当前结果不是严格 S 参数提取，也不能替代 FDTD、FEM 或 EME 仿真。
"""
    with report_path.open("a", encoding="utf-8") as file:
        file.write(section)
