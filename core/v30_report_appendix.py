import json
from pathlib import Path
from typing import Any


def _format_metric(data: dict[str, Any], key: str, digits: int = 4) -> str:
    value = data.get(key)
    if value is None:
        return "N/A"
    return f"{float(value):.{digits}f}"


def append_v30_propagation_section(
    report_path: Path,
    propagation_result_path: Path,
) -> Path:
    """在已有中文报告末尾追加 V3.0 标量 BPM 传播仿真章节。"""
    report_path = Path(report_path)
    propagation_result_path = Path(propagation_result_path)

    if not report_path.exists():
        raise FileNotFoundError(f"报告文件不存在：{report_path}")
    if not propagation_result_path.exists():
        raise FileNotFoundError(
            f"传播仿真结果不存在：{propagation_result_path}"
        )

    result = json.loads(propagation_result_path.read_text(encoding="utf-8"))
    section = f"""

---

## V3.0 MMI 光场传播仿真分析

### 一、分析目的

V3.0 在现有 MMI surrogate 优化流程之后增加传播仿真验证层，使用优化得到的 MMI 宽度和长度观察器件内部光场演化趋势，并通过输出端口窗口积分估算两个输出端口的归一化功率。

### 二、传播模型与参数

本次传播分析采用 **二维 x-z 标量 BPM 近似**。输入端使用功率归一化 Gaussian 光场，传播过程采用 split-step Fourier 方法，并在横向网格边缘使用平滑吸收窗。

| 参数 | 数值 |
|---|---:|
| 求解器类型 | `{result.get("propagation_solver_type", "unknown")}` |
| 工作波长 | {_format_metric(result, "wavelength_um")} μm |
| MMI 宽度 | {_format_metric(result, "mmi_width_um")} μm |
| MMI 长度 | {_format_metric(result, "mmi_length_um")} μm |
| 参考有效折射率 | {_format_metric(result, "reference_neff")} |
| 传播网格 | {int(result.get("nx", 0))} × {int(result.get("nz", 0))} |
| 横向步长 dx | {_format_metric(result, "dx_um", 5)} μm |
| 传播步长 dz | {_format_metric(result, "dz_um", 5)} μm |

### 三、输出端口功率估算

| 指标 | 数值 |
|---|---:|
| Output port 1 | {_format_metric(result, "p_out1")} |
| Output port 2 | {_format_metric(result, "p_out2")} |
| 总收集功率 | {_format_metric(result, "total_collected_power")} |
| 分光不均衡 | {_format_metric(result, "imbalance_db")} dB |
| 端口窗口插入损耗 | {_format_metric(result, "insertion_loss_db")} dB |

上述功率按输入总功率归一化，数值来自最终传播位置上的简单端口窗口积分，与 surrogate 优化器给出的目标函数结果属于不同层级的工程近似指标。

### 四、传播图与输出端强度分布

![V3.0 MMI 光场传播图](field_propagation.png)

![V3.0 输出端横向强度分布](field_output_profile.png)

### 五、模型边界

1. 当前方法是二维标量 BPM 近似，不是严格全矢量电磁仿真；
2. 当前结果不是全矢量 FDTD、FEM 或 EME 仿真结果；
3. 输出功率由简化端口窗口积分估算；
4. MMI 横向等效折射率、边界和端口模式仍较简化；
5. 后续可升级为更严格的 EME、FDTD、FEM，或接入 Lumerical、COMSOL 等外部工具。
"""

    with report_path.open("a", encoding="utf-8") as report_file:
        report_file.write(section)
    return report_path
