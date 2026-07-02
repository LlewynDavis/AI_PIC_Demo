from pathlib import Path

import streamlit as st

from core.spec_parser import save_design_spec, parse_design_text
from core.optimizer import optimize_length
from core.report_generator import generate_report
from core.package_generator import create_result_package
from layout.gds_generator import generate_gds, generate_layout_preview


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


st.set_page_config(
    page_title="AI 光子芯片设计平台 Demo V1",
    layout="wide",
)


st.title("AI 光子芯片设计平台 Demo V1")
st.subheader("1×2 MMI 光功率分束器自动设计示例")

st.markdown(
    """
本版本为 **V1 物理建模增强版**，在原 V0 自动化流程基础上增加了：

**SOI 材料参数库 → 简化有效折射率估算 → MMI 宽度-长度二维联合扫描 → 二维优化热力图 → GDS 版图生成 → 中文报告输出**

当前版本仍然使用轻量级替代模型，不是真实 FDTD/FEM/EME 电磁仿真。
后续可以将 `core/mode_solver.py` 和 `core/mmi_model.py` 替换为真实电磁场求解模块。
"""
)


with st.sidebar:
    st.header("自然语言需求输入")

    user_text = st.text_area(
        "请输入设计需求",
        value="请帮我设计一个 1550 nm、SOI 平台、50:50 分光的 1×2 MMI 分束器。",
        height=120,
    )

    if st.button("解析需求"):
        parsed_spec = parse_design_text(user_text)

        st.session_state["parsed_spec"] = parsed_spec

        st.session_state["wavelength_um"] = parsed_spec["wavelength_um"]
        st.session_state["neff"] = parsed_spec["neff"]
        st.session_state["use_estimated_neff"] = parsed_spec["use_estimated_neff"]
        st.session_state["waveguide_width_um"] = parsed_spec["waveguide_width_um"]
        st.session_state["waveguide_height_um"] = parsed_spec["waveguide_height_um"]
        st.session_state["mmi_width_um"] = parsed_spec["mmi_width_um"]
        st.session_state["length_min_um"] = parsed_spec["length_scan_range_um"][0]
        st.session_state["length_max_um"] = parsed_spec["length_scan_range_um"][1]
        st.session_state["num_scan_points"] = parsed_spec["num_scan_points"]
        st.session_state["width_min_um"] = parsed_spec["mmi_width_scan_range_um"][0]
        st.session_state["width_max_um"] = parsed_spec["mmi_width_scan_range_um"][1]
        st.session_state["num_width_scan_points"] = parsed_spec["num_width_scan_points"]

        st.success("需求解析完成，参数已填入下方输入框。")

    if "parsed_spec" in st.session_state:
        st.markdown("#### 解析后的结构化参数")
        st.json(st.session_state["parsed_spec"])

    st.divider()

    st.header("物理平台参数")

    platform = st.selectbox(
        "光子平台",
        options=["SOI"],
        index=0,
    )

    use_estimated_neff = st.checkbox(
        "使用系统估算 neff",
        value=st.session_state.get("use_estimated_neff", True),
    )

    wavelength_um = st.number_input(
        "工作波长 wavelength / μm",
        min_value=1.0,
        max_value=2.0,
        value=st.session_state.get("wavelength_um", 1.55),
        step=0.01,
    )

    neff = st.number_input(
        "手动 neff",
        min_value=1.0,
        max_value=4.0,
        value=st.session_state.get("neff", 2.8),
        step=0.1,
        disabled=use_estimated_neff,
    )

    waveguide_width_um = st.number_input(
        "输入/输出波导宽度 / μm",
        min_value=0.2,
        max_value=2.0,
        value=st.session_state.get("waveguide_width_um", 0.5),
        step=0.05,
    )

    waveguide_height_um = st.number_input(
        "波导高度 / μm",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.get("waveguide_height_um", 0.22),
        step=0.01,
    )

    st.divider()

    st.header("MMI 初始参数")

    mmi_width_um = st.number_input(
        "名义 MMI 区域宽度 / μm",
        min_value=1.0,
        max_value=10.0,
        value=st.session_state.get("mmi_width_um", 2.5),
        step=0.1,
    )

    st.divider()

    st.header("二维扫描范围设置")

    length_min_um = st.number_input(
        "最小扫描长度 / μm",
        min_value=1.0,
        max_value=100.0,
        value=st.session_state.get("length_min_um", 3.0),
        step=0.5,
    )

    length_max_um = st.number_input(
        "最大扫描长度 / μm",
        min_value=1.0,
        max_value=100.0,
        value=st.session_state.get("length_max_um", 20.0),
        step=0.5,
    )

    num_scan_points = st.number_input(
        "长度扫描点数",
        min_value=20,
        max_value=1000,
        value=st.session_state.get("num_scan_points", 200),
        step=10,
    )

    width_min_um = st.number_input(
        "最小扫描宽度 / μm",
        min_value=1.0,
        max_value=10.0,
        value=st.session_state.get("width_min_um", 1.5),
        step=0.1,
    )

    width_max_um = st.number_input(
        "最大扫描宽度 / μm",
        min_value=1.0,
        max_value=10.0,
        value=st.session_state.get("width_max_um", 4.0),
        step=0.1,
    )

    num_width_scan_points = st.number_input(
        "宽度扫描点数",
        min_value=20,
        max_value=300,
        value=st.session_state.get("num_width_scan_points", 80),
        step=10,
    )

    run_button = st.button("运行 V1 设计", type="primary")


if run_button:
    if length_max_um <= length_min_um:
        st.error("最大扫描长度必须大于最小扫描长度。")
    elif width_max_um <= width_min_um:
        st.error("最大扫描宽度必须大于最小扫描宽度。")
    else:
        spec = {
            "component": "1x2_mmi_splitter",
            "platform": platform,
            "wavelength_um": wavelength_um,
            "use_estimated_neff": use_estimated_neff,
            "neff": neff,
            "waveguide_width_um": waveguide_width_um,
            "waveguide_height_um": waveguide_height_um,
            "mmi_width_um": mmi_width_um,
            "target_split_ratio": [0.5, 0.5],
            "length_scan_range_um": [length_min_um, length_max_um],
            "num_scan_points": int(num_scan_points),
            "mmi_width_scan_range_um": [width_min_um, width_max_um],
            "num_width_scan_points": int(num_width_scan_points),
        }

        with st.spinner("正在运行 V1 物理建模增强版设计流程..."):
            save_design_spec(spec=spec, output_dir=OUTPUT_DIR)

            result = optimize_length(spec=spec, output_dir=OUTPUT_DIR)

            gds_path = generate_gds(
                spec=spec,
                result=result,
                output_dir=OUTPUT_DIR,
            )

            layout_preview_path = generate_layout_preview(
                spec=spec,
                result=result,
                output_dir=OUTPUT_DIR,
            )

            report_path = generate_report(
                spec=spec,
                result=result,
                gds_path=gds_path,
                output_dir=OUTPUT_DIR,
            )

            package_path = create_result_package(output_dir=OUTPUT_DIR)

        st.success("V1 设计流程运行完成！")

        st.subheader("结构化设计参数")
        st.json(spec)

        st.subheader("物理建模结果")

        col_phy1, col_phy2, col_phy3 = st.columns(3)

        with col_phy1:
            st.metric(
                label="系统估算 neff",
                value=f"{result['estimated_neff']:.4f}",
            )

        with col_phy2:
            st.metric(
                label="实际使用 neff",
                value=f"{result['neff_used']:.4f}",
            )

        with col_phy3:
            st.metric(
                label="初始 MMI 长度",
                value=f"{result['initial_length_um']:.3f} μm",
            )

        st.divider()

        st.subheader("二维优化结果")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="最佳 MMI 宽度",
                value=f"{result['best_width_um']:.3f} μm",
            )

        with col2:
            st.metric(
                label="最佳 MMI 长度",
                value=f"{result['best_length_um']:.3f} μm",
            )

        with col3:
            st.metric(
                label="最优评分",
                value=f"{result['best_score']:.6f}",
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric(
                label="Output port 1",
                value=f"{result['p_out1']:.4f}",
            )

        with col5:
            st.metric(
                label="Output port 2",
                value=f"{result['p_out2']:.4f}",
            )

        with col6:
            st.metric(
                label="分光不均衡",
                value=f"{result['imbalance_db']:.3f} dB",
            )

        st.metric(
            label="插入损耗",
            value=f"{result['insertion_loss_db']:.3f} dB",
        )

        st.divider()

        st.subheader("MMI 长度扫描结果")

        plot_path = OUTPUT_DIR / "length_sweep.png"
        if plot_path.exists():
            st.image(
                str(plot_path),
                caption="在最优 MMI 宽度下的长度扫描结果",
                use_container_width=True,
            )
        else:
            st.warning("未找到 length_sweep.png。")

        st.divider()

        st.subheader("MMI 宽度-长度二维优化热力图")

        heatmap_path = OUTPUT_DIR / "width_length_heatmap.png"
        if heatmap_path.exists():
            st.image(
                str(heatmap_path),
                caption="MMI Width-Length Optimization Heatmap",
                use_container_width=True,
            )
        else:
            st.warning("未找到 width_length_heatmap.png。")

        st.divider()

        st.subheader("1×2 MMI 版图预览")

        preview_path = OUTPUT_DIR / "layout_preview.png"
        if preview_path.exists():
            st.image(
                str(preview_path),
                caption="Simplified Layout Preview",
                use_container_width=True,
            )
        else:
            st.warning("未找到 layout_preview.png。")

        st.divider()

        st.subheader("生成文件")

        st.write(f"设计参数文件：`{OUTPUT_DIR / 'design_spec.json'}`")
        st.write(f"物理参数文件：`{OUTPUT_DIR / 'physical_params.json'}`")
        st.write(f"优化结果文件：`{OUTPUT_DIR / 'optimization_result.json'}`")
        st.write(f"长度扫描图：`{OUTPUT_DIR / 'length_sweep.png'}`")
        st.write(f"二维优化热力图：`{OUTPUT_DIR / 'width_length_heatmap.png'}`")
        st.write(f"版图预览图：`{layout_preview_path}`")
        st.write(f"GDS 版图文件：`{gds_path}`")
        st.write(f"设计报告文件：`{report_path}`")

        col7, col8, col9 = st.columns(3)

        with col7:
            if report_path.exists():
                st.download_button(
                    label="下载设计报告 report.md",
                    data=report_path.read_text(encoding="utf-8"),
                    file_name="report.md",
                    mime="text/markdown",
                )

        with col8:
            if gds_path.exists():
                st.download_button(
                    label="下载 GDS 版图文件",
                    data=gds_path.read_bytes(),
                    file_name="mmi1x2_demo.gds",
                    mime="application/octet-stream",
                )

        with col9:
            if package_path.exists():
                st.download_button(
                    label="下载完整结果包 zip",
                    data=package_path.read_bytes(),
                    file_name="ai_pic_demo_results.zip",
                    mime="application/zip",
                )

else:
    st.info("请在左侧设置设计参数，然后点击“运行 V1 设计”。")


st.divider()

st.markdown(
    """
### 当前 V1 demo 的定位

当前版本重点展示的是 **物理建模链路增强**，而不是完整真实电磁仿真。

相比 V0，V1 已经完成：

1. 加入 SOI 材料参数库；
2. 根据材料参数和波导尺寸估算有效折射率 neff；
3. 将优化从一维 MMI 长度扫描扩展为 MMI 宽度-长度二维联合扫描；
4. 生成二维优化热力图；
5. 使用最优宽度和长度生成 GDS 版图；
6. 输出中文报告和完整结果包。

后续可以继续升级为：

- 接入真实 Mode Solver；
- 接入 Meep、Tidy3D、FEMWELL、COMSOL 或 Lumerical；
- 提取真实 S 参数；
- 加入 PDK 设计规则和 DRC 检查；
- 扩展 ring resonator、directional coupler、grating coupler 等器件。
"""
)