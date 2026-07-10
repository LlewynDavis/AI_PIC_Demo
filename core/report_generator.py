import json
from pathlib import Path


def load_physical_params(output_dir: Path):
    """
    读取 physical_params.json。
    如果文件不存在，则返回空字典。
    """
    physical_params_path = output_dir / "physical_params.json"

    if physical_params_path.exists():
        with open(physical_params_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def generate_report(
    spec,
    result,
    gds_path,
    output_dir: Path,
    version: str = "V1",
):
    """
    自动生成中文 Markdown 格式设计报告。

    V1 报告重点说明：
    1. SOI 材料参数；
    2. 简化 neff 估算；
    3. MMI 宽度-长度二维联合扫描；
    4. 二维优化热力图；
    5. GDS 版图生成；
    6. 当前模型局限和后续升级方向。
    """
    physical_params = load_physical_params(output_dir)

    core_material = physical_params.get("core_material", "Si")
    cladding_material = physical_params.get("cladding_material", "SiO2")
    core_index = physical_params.get("core_index", "N/A")
    cladding_index = physical_params.get("cladding_index", "N/A")
    estimated_neff = result.get("estimated_neff", spec.get("neff", "N/A"))
    neff_used = result.get("neff_used", spec.get("neff", "N/A"))

    output_files = [
        ("design_spec.json", "保存结构化设计参数"),
        ("physical_params.json", "保存材料参数和 neff 估算结果"),
        ("mode_result.json", "保存 V2.5 有限差分模式分析结果"),
        ("index_profile.png", "SOI 波导折射率截面分布"),
        ("mode_profile.png", "有限差分标量模式场分布"),
        ("neff_vs_width.png", "neff 随波导宽度变化曲线"),
        ("optimization_result.json", "保存二维优化结果"),
        ("wavelength_sweep_result.json", "保存 V2.5 有限差分 neff 波长扫描结果"),
        ("wavelength_sweep.png", "输出功率随波长变化图"),
        ("wavelength_imbalance.png", "分光不均衡随波长变化图"),
        ("propagation_result.json", "保存 V3.0 标量 BPM 传播结果"),
        ("field_propagation.png", "MMI 区域标量 BPM 光场传播图"),
        ("field_output_profile.png", "输出端横向强度与端口积分窗口"),
        ("field_propagation_enhanced.png", "V3.1 增强版标量 BPM 传播图"),
        ("output_window_sensitivity.png", "输出窗口宽度敏感性图"),
        (
            "output_window_sensitivity_result.json",
            "输出窗口宽度敏感性结果",
        ),
        ("model_comparison.png", "Surrogate 与 BPM 模型对比图"),
        ("model_comparison_result.json", "Surrogate 与 BPM 模型对比结果"),
        ("bpm_final_field_data.npz", "BPM 输出端复数场压缩数据"),
        ("mode_overlap_result.json", "V3.2 端口模式重叠积分结果"),
        ("mode_overlap_comparison.png", "三类端口功率估算对比图"),
        ("field_output_profile_with_modes.png", "输出场与 Gaussian 端口模式"),
        ("length_sweep.png", "最优宽度下的 MMI 长度扫描图"),
        ("width_length_heatmap.png", "MMI 宽度—长度二维优化热力图"),
        ("layout_preview.png", "1×2 MMI 简化版图预览"),
        ("mmi1x2_demo.gds", "自动生成的 GDS 版图文件"),
        ("report.md", "自动生成的中文设计报告"),
        ("run_log.txt", "本次运行过程与状态日志"),
        ("ai_pic_demo_results.zip", "完整结果包"),
    ]
    output_file_rows = "\n".join(
        f"| `{output_dir / filename}` | {description} |"
        for filename, description in output_files
    )

    if version == "V3.2":
        version_positioning = "端口模式重叠积分版"
    elif version == "V3.1":
        version_positioning = "传播仿真校准与模型对比版"
    elif version.startswith("V3"):
        version_positioning = "二维标量 BPM 光场传播仿真版"
    elif version == "V2.5":
        version_positioning = "有限差分模式求解版"
    elif version == "V2.3":
        version_positioning = "波长扫描增强版"
    elif version.startswith("V2"):
        version_positioning = "模式求解版"
    else:
        version_positioning = "工程稳定版"

    report = f"""# 基于 AI 的 1×2 MMI 光功率分束器自动设计报告（{version}）

## 一、Demo 版本说明

本报告对应 **AI 光子芯片设计平台 Demo {version}：{version_positioning}**。

相比 V0 版本，{version} 不再只使用固定的有效折射率和一维长度扫描，而是在原有自动化流程基础上进一步加入了：

1. SOI 平台材料参数库；
2. 简化有效折射率 neff 估算模块；
3. MMI 宽度与长度二维联合扫描；
4. 二维优化热力图；
5. 基于最优宽度和长度的 GDS 版图生成；
6. 中文设计报告和完整结果包输出。

当前 {version} 版本在验证“物理参数—器件建模—参数优化—版图生成”自动化链路的基础上，进一步增强了运行稳定性、结果追踪和工程交付能力。

---

## 二、设计目标

本次 demo 以 **1×2 MMI 光功率分束器** 为示例器件，目标是在 SOI 光子平台上实现接近 50:50 的光功率分束。

具体目标如下：

| 项目 | 内容 |
|---|---|
| 器件类型 | {spec["component"]} |
| 光子平台 | {spec["platform"]} |
| 工作波长 | {spec["wavelength_um"]} μm |
| 目标分光比 | 50:50 |
| 优化目标 | 两个输出端口功率接近 0.5，同时降低插入损耗和分光不均衡 |

---

## 三、SOI 平台材料参数

{version} 版本包含基础材料参数库。当前使用的 SOI 平台参数如下：

| 参数 | 数值 |
|---|---:|
| 核心材料 | {core_material} |
| 包层材料 | {cladding_material} |
| 核心折射率 | {core_index} |
| 包层折射率 | {cladding_index} |
| 波导宽度 | {spec["waveguide_width_um"]} μm |
| 波导高度 | {spec["waveguide_height_um"]} μm |
| 工作波长 | {spec["wavelength_um"]} μm |

需要说明的是，当前折射率参数用于 demo 近似计算，后续可以替换为更精确的材料色散模型或具体 PDK 数据。

---

## 四、有效折射率估算

{version} 版本包含简化有效折射率估算模块。系统根据核心折射率、包层折射率、波导宽度、波导高度和工作波长估算有效折射率 neff。

本次计算结果如下：

| 指标 | 数值 |
|---|---:|
| 系统估算 neff | {float(estimated_neff):.4f} |
| 实际使用 neff | {float(neff_used):.4f} |
| 是否使用系统估算 neff | {spec.get("use_estimated_neff", True)} |

当前 neff 估算模块仍属于简化模型，不是真实 FDE、FEM 或 MODE Solver 结果。后续可将该模块替换为 FEMWELL、MPB、Lumerical MODE 或 COMSOL Mode Analysis 等真实模式求解器。

---

## 五、MMI 初始物理建模

MMI 分束器的基本原理是 **多模干涉自成像效应**。

当输入光进入较宽的 MMI 区域后，会激发多个横向模式。不同模式在传播过程中积累不同相位，并在特定传播长度处重新组合形成自成像，从而实现光功率分束。

当前 {version} 版本仍使用简化自成像模型估算 MMI 初始长度：

| 指标 | 数值 |
|---|---:|
| 名义 MMI 宽度 | {spec["mmi_width_um"]} μm |
| 初始估算 MMI 长度 | {result["initial_length_um"]:.3f} μm |

该初始长度只作为参数扫描参考，并不代表最终精确设计结果。

---

## 六、二维参数扫描与优化结果

{version} 将 V0 中的一维长度扫描升级为 **MMI 宽度—长度二维联合扫描**。

扫描设置如下：

| 参数 | 数值 |
|---|---:|
| MMI 长度扫描范围 | {spec["length_scan_range_um"][0]}–{spec["length_scan_range_um"][1]} μm |
| 长度扫描点数 | {spec["num_scan_points"]} |
| MMI 宽度扫描范围 | {spec["mmi_width_scan_range_um"][0]}–{spec["mmi_width_scan_range_um"][1]} μm |
| 宽度扫描点数 | {spec["num_width_scan_points"]} |

系统综合考虑输出功率误差、插入损耗、分光不均衡和宽度偏离惩罚，选择当前模型下的最优结构参数。

优化结果如下：

| 指标 | 结果 |
|---|---:|
| 最佳 MMI 宽度 | {result["best_width_um"]:.3f} μm |
| 最佳 MMI 长度 | {result["best_length_um"]:.3f} μm |
| Output port 1 归一化功率 | {result["p_out1"]:.4f} |
| Output port 2 归一化功率 | {result["p_out2"]:.4f} |
| 插入损耗 | {result["insertion_loss_db"]:.3f} dB |
| 分光不均衡 | {result["imbalance_db"]:.3f} dB |
| 最优评分 | {result["best_score"]:.6f} |

从当前结果看，两个输出端口功率接近 0.5，说明该设计在 {version} 简化模型下实现了接近 50:50 的分光效果。

---

## 七、MMI 长度扫描图

下图展示了在最优 MMI 宽度下，不同 MMI 长度对应的两个输出端口归一化功率变化。

![MMI 长度扫描结果](length_sweep.png)

---

## 八、MMI 宽度—长度二维优化热力图

下图展示了不同 MMI 宽度和长度组合下的优化评分分布。颜色表示目标函数评分，评分越低，代表越接近当前优化目标。

![MMI 宽度-长度二维优化热力图](width_length_heatmap.png)

该图用于直观展示系统如何在二维参数空间中寻找最优结构。

---

## 九、版图生成与版图预览

系统根据优化得到的最佳 MMI 宽度和最佳 MMI 长度，调用 gdsfactory 自动生成 1×2 MMI 分束器的 GDS 版图文件。

生成的 GDS 文件路径为：

`{gds_path}`

同时，系统生成了简化版图预览图：

![1×2 MMI 版图预览](layout_preview.png)

需要注意的是，版图预览图是根据参数绘制的结构示意图，不是 GDS 文件的精确截图；真正的版图文件为 `mmi1x2_demo.gds`。

---

## 十、自动生成文件

本次 {version} 设计流程自动生成以下文件：

| 文件 | 作用 |
|---|---|
{output_file_rows}

---

## 十一、当前 {version} demo 的局限性

当前版本虽然增强了物理参数链路，但仍属于轻量级 demo，主要局限如下：

1. **模式求解仍是标量近似模型**
   当前有效折射率来自二维标量有限差分模式求解，不是严格全矢量 FDE/FEM 结果。

2. **MMI 响应仍是替代模型**  
   输出功率、插入损耗和分光不均衡来自轻量级 surrogate model，并不代表真实器件性能。

3. **传播场仍是二维标量近似**
   V3.0 使用二维标量 BPM 展示 MMI 光场演化趋势，不是严格全矢量 FDTD/FEM/EME 仿真。

4. **传播损耗是窗口积分意义下的等效指标**
   V3.1 的 window-based insertion loss 随输出窗口宽度变化，不能等同于严格器件插入损耗或全矢量 S 参数。V3.2 的端口模式仍是 Gaussian 近似，overlap-based power 也不是严格全矢量本征模式 S 参数。

5. **未提取真实 S 参数**
   当前结果不能直接作为最终设计验证结果使用。

6. **尚未加入 DRC / LVS / 工艺规则检查**
   GDS 文件已经可以生成，但还没有进行完整的工艺规则验证。

---

## 十二、后续升级方向

后续可以从以下方向继续完善：

1. **接入真实 Mode Solver**  
   将 `core/mode_solver.py` 替换为 FEMWELL、MPB、Lumerical MODE 或 COMSOL Mode Analysis。

2. **接入真实电磁场求解器**  
   将 `core/mmi_model.py` 替换为 Meep、Tidy3D、FEMWELL、COMSOL 或 Ansys Lumerical 仿真结果。

3. **提取真实 S 参数**  
   计算 S11、S21、S31 等参数，用于评价插入损耗、反射和分光性能。

4. **加入 PDK 和 DRC 检查**  
   引入更真实的工艺层信息、最小线宽、最小间距和版图规则。

5. **扩展更多器件类型**  
   在 MMI 基础上继续加入 ring resonator、directional coupler、grating coupler、Y-branch 等器件。

6. **升级 AI 需求解析模块**  
   将当前规则版解析器替换为大模型结构化输出或 LangGraph workflow。

---

## 十三、阶段性结论

当前 {version} demo 已经在 V0 自动化闭环基础上进一步增强了物理建模链路和工程稳定性。

系统不再只依赖手动输入 neff，而是加入了 SOI 材料参数库和简化有效折射率估算模块；同时，优化过程也从单一 MMI 长度扫描扩展为 MMI 宽度和长度的二维联合扫描。

因此，{version} 版本已经更接近真实 PIC 设计流程中的“材料参数—物理建模—参数优化—版图生成”链路，可作为后续接入真实电磁场求解器和 AI 工作流的稳定基础框架。
"""

    report_path = output_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")

    return report_path
