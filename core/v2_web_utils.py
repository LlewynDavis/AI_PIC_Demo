import json
from pathlib import Path
from typing import Any, Dict, Optional


V2_OUTPUT_FILES = [
    ("design_spec.json", "结构化设计参数"),
    ("physical_params.json", "材料参数与模式求解摘要"),
    ("mode_result.json", "V2.5 有限差分模式分析结果"),
    ("index_profile.png", "SOI 波导折射率截面分布"),
    ("mode_profile.png", "有限差分标量模式场分布"),
    ("neff_vs_width.png", "neff 随波导宽度变化曲线"),
    ("optimization_result.json", "MMI 二维优化结果"),
    ("wavelength_sweep_result.json", "V2.5 有限差分 neff 波长扫描结果"),
    ("wavelength_sweep.png", "输出功率随波长变化图"),
    ("wavelength_imbalance.png", "分光不均衡随波长变化图"),
    ("propagation_result.json", "V3.0 标量 BPM 传播仿真结果"),
    ("field_propagation.png", "MMI 区域标量 BPM 光场传播图"),
    ("field_output_profile.png", "输出端横向强度分布"),
    ("field_propagation_enhanced.png", "V3.1 增强版标量 BPM 传播图"),
    ("output_window_sensitivity.png", "输出窗口宽度敏感性图"),
    (
        "output_window_sensitivity_result.json",
        "输出窗口宽度敏感性结果",
    ),
    ("model_comparison.png", "Surrogate 与 BPM 模型对比图"),
    ("model_comparison_result.json", "Surrogate 与 BPM 模型对比结果"),
    ("length_sweep.png", "MMI 长度扫描图"),
    ("width_length_heatmap.png", "MMI 宽度—长度二维优化热力图"),
    ("layout_preview.png", "版图预览图"),
    ("mmi1x2_demo.gds", "GDS 版图文件"),
    ("report.md", "中文设计报告"),
    ("run_log.txt", "运行日志"),
    ("ai_pic_demo_results.zip", "完整结果包"),
]


def find_latest_run_dir(outputs_dir: str | Path = "outputs") -> Optional[Path]:
    """查找 outputs 目录下最新的 run_时间戳文件夹。"""
    outputs_dir = Path(outputs_dir)
    if not outputs_dir.exists():
        return None

    run_dirs = [
        item
        for item in outputs_dir.iterdir()
        if item.is_dir() and item.name.startswith("run_")
    ]
    if not run_dirs:
        return None

    run_dirs.sort(key=lambda path: path.name, reverse=True)
    return run_dirs[0]


def load_json_file(path: str | Path) -> Dict[str, Any]:
    """读取 JSON 文件；文件不存在时返回空字典。"""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def format_file_size(path: str | Path) -> str:
    """格式化文件大小。"""
    path = Path(path)
    if not path.exists():
        return "缺失"

    size_bytes = path.stat().st_size
    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"
    return f"{size_kb / 1024:.2f} MB"


def _download_file(st, path: Path, label: str, file_name: str, mime: str) -> None:
    """渲染 Streamlit 下载按钮。"""
    if not path.exists():
        st.warning(f"未找到文件：{path}")
        return

    st.download_button(
        label=label,
        data=path.read_bytes(),
        file_name=file_name,
        mime=mime,
    )


def display_v2_result_panel(run_dir: str | Path) -> None:
    """在 Streamlit 页面中展示 V2.5 基线与 V3.0 传播结果。"""
    import streamlit as st

    run_dir = Path(run_dir)
    st.subheader("V3.1 运行结果总览")

    if not run_dir.exists():
        st.error(f"运行目录不存在：{run_dir}")
        return

    st.info(f"当前运行目录：`{run_dir}`")

    design_spec = load_json_file(run_dir / "design_spec.json")
    physical_params = load_json_file(run_dir / "physical_params.json")
    mode_result = load_json_file(run_dir / "mode_result.json")
    optimization_result = load_json_file(run_dir / "optimization_result.json")
    wavelength_sweep_result = load_json_file(
        run_dir / "wavelength_sweep_result.json"
    )
    propagation_result = load_json_file(run_dir / "propagation_result.json")
    sensitivity_result = load_json_file(
        run_dir / "output_window_sensitivity_result.json"
    )
    model_comparison_result = load_json_file(
        run_dir / "model_comparison_result.json"
    )

    mode_profile_result = mode_result.get("mode_profile_result", {})

    st.markdown("### 1. V2.5 有限差分模式求解结果")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        neff = mode_result.get(
            "neff_used_for_mmi",
            physical_params.get("neff_used", 0),
        )
        st.metric("neff", f"{float(neff):.4f}")
    with col2:
        confinement = mode_profile_result.get("confinement_factor", 0)
        st.metric("模式约束因子", f"{float(confinement):.4f}")
    with col3:
        mode_area = mode_profile_result.get("mode_area_um2", 0)
        st.metric("模式面积", f"{float(mode_area):.4f} μm²")
    with col4:
        waveguide_width = mode_profile_result.get(
            "waveguide_width_um",
            design_spec.get("waveguide_width_um", 0),
        )
        st.metric("波导宽度", f"{float(waveguide_width):.3f} μm")

    st.write(
        "模式求解类型：",
        f"`{mode_profile_result.get('mode_solver_type', 'unknown')}`",
    )

    solver_col1, solver_col2, solver_col3, solver_col4 = st.columns(4)
    with solver_col1:
        st.metric("传播常数 β", f"{float(mode_profile_result.get('beta', 0)):.4f} μm⁻¹")
    with solver_col2:
        grid_x = int(mode_profile_result.get("grid_size_x", 0))
        grid_y = int(mode_profile_result.get("grid_size_y", 0))
        st.metric("有限差分网格", f"{grid_x} × {grid_y}")
    with solver_col3:
        st.metric("网格步长 dx", f"{float(mode_profile_result.get('dx_um', 0)):.4f} μm")
    with solver_col4:
        st.metric("网格步长 dy", f"{float(mode_profile_result.get('dy_um', 0)):.4f} μm")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### SOI 波导折射率截面")
        index_profile_path = run_dir / "index_profile.png"
        if index_profile_path.exists():
            st.image(str(index_profile_path), width="stretch")
        else:
            st.warning("未找到 index_profile.png")
    with col_right:
        st.markdown("#### 有限差分标量模式场分布")
        mode_profile_path = run_dir / "mode_profile.png"
        if mode_profile_path.exists():
            st.image(str(mode_profile_path), width="stretch")
        else:
            st.warning("未找到 mode_profile.png")
    st.markdown("#### neff 随波导宽度变化")
    neff_vs_width_path = run_dir / "neff_vs_width.png"
    if neff_vs_width_path.exists():
        st.image(str(neff_vs_width_path), width="stretch")
    else:
        st.warning("未找到 neff_vs_width.png")

    st.markdown("### 2. MMI 二维优化结果")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        value = optimization_result.get("best_width_um", 0)
        st.metric("最佳 MMI 宽度", f"{float(value):.3f} μm")
    with col2:
        value = optimization_result.get("best_length_um", 0)
        st.metric("最佳 MMI 长度", f"{float(value):.3f} μm")
    with col3:
        value = optimization_result.get(
            "p_out1",
            optimization_result.get("output_port_1", 0),
        )
        st.metric("Output port 1", f"{float(value):.4f}")
    with col4:
        value = optimization_result.get(
            "p_out2",
            optimization_result.get("output_port_2", 0),
        )
        st.metric("Output port 2", f"{float(value):.4f}")

    col5, col6, col7 = st.columns(3)
    with col5:
        value = optimization_result.get("insertion_loss_db", 0)
        st.metric("插入损耗", f"{float(value):.3f} dB")
    with col6:
        value = optimization_result.get("imbalance_db", 0)
        st.metric("分光不均衡", f"{float(value):.3f} dB")
    with col7:
        value = optimization_result.get("best_score", 0)
        st.metric("最优评分", f"{float(value):.6f}")

    st.markdown("### 3. V2.5 波长扫描与带宽趋势")
    if wavelength_sweep_result:
        col1, col2, col3 = st.columns(3)
        with col1:
            value = wavelength_sweep_result.get("max_abs_imbalance_db", 0)
            st.metric("最大绝对不均衡", f"{float(value):.4f} dB")
        with col2:
            value = wavelength_sweep_result.get("mean_abs_imbalance_db", 0)
            st.metric("平均绝对不均衡", f"{float(value):.4f} dB")
        with col3:
            value = wavelength_sweep_result.get("max_insertion_loss_db", 0)
            st.metric("最大插入损耗", f"{float(value):.4f} dB")

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### 输出功率随波长变化")
            image_path = run_dir / "wavelength_sweep.png"
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.warning("未找到 wavelength_sweep.png")
        with col_right:
            st.markdown("#### 分光不均衡随波长变化")
            image_path = run_dir / "wavelength_imbalance.png"
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.warning("未找到 wavelength_imbalance.png")

        with st.expander("查看 wavelength_sweep_result.json"):
            st.json(wavelength_sweep_result)
    else:
        st.info("当前运行结果中暂未找到 wavelength_sweep_result.json。")

    st.markdown("### 4. V3.0 MMI 光场传播仿真")
    st.info(
        "V3.0 使用二维标量 BPM 近似方法对 MMI 区域进行光场传播仿真，"
        "用于观察器件内部光场演化趋势。该结果不是严格全矢量 "
        "FDTD/FEM/EME 仿真。"
    )
    if propagation_result:
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric(
                "BPM Output 1",
                f"{float(propagation_result.get('p_out1', 0)):.4f}",
            )
        with metric_col2:
            st.metric(
                "BPM Output 2",
                f"{float(propagation_result.get('p_out2', 0)):.4f}",
            )
        with metric_col3:
            st.metric(
                "总收集功率",
                f"{float(propagation_result.get('total_collected_power', 0)):.4f}",
            )
        with metric_col4:
            st.metric(
                "参考 neff",
                f"{float(propagation_result.get('reference_neff', 0)):.4f}",
            )

        metric_col5, metric_col6, metric_col7 = st.columns(3)
        with metric_col5:
            st.metric(
                "BPM 分光不均衡",
                f"{float(propagation_result.get('imbalance_db', 0)):.4f} dB",
            )
        with metric_col6:
            st.metric(
                "BPM 窗口插损",
                f"{float(propagation_result.get('insertion_loss_db', 0)):.4f} dB",
            )
        with metric_col7:
            st.metric(
                "传播求解器",
                str(propagation_result.get("propagation_solver_type", "unknown")),
            )

        propagation_left, propagation_right = st.columns(2)
        with propagation_left:
            st.markdown("#### MMI 内部光场传播")
            image_path = run_dir / "field_propagation.png"
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.warning("未找到 field_propagation.png")
        with propagation_right:
            st.markdown("#### 输出端横向强度分布")
            image_path = run_dir / "field_output_profile.png"
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.warning("未找到 field_output_profile.png")

        with st.expander("查看 propagation_result.json"):
            st.json(propagation_result)

        download_columns = st.columns(3)
        propagation_downloads = [
            (
                "propagation_result.json",
                "下载 propagation_result.json",
                "application/json",
            ),
            (
                "field_propagation.png",
                "下载 field_propagation.png",
                "image/png",
            ),
            (
                "field_output_profile.png",
                "下载 field_output_profile.png",
                "image/png",
            ),
        ]
        for column, (filename, label, mime) in zip(
            download_columns,
            propagation_downloads,
        ):
            with column:
                _download_file(st, run_dir / filename, label, filename, mime)
    else:
        st.warning(
            "当前运行结果缺少 V3.0 传播仿真文件；V2.5 基线结果仍可正常查看。"
        )

    st.markdown("### 5. V3.1 传播仿真校准与模型对比")
    st.info(
        "V3.1 用于校准 V3.0 的二维标量 BPM 传播结果。输出端口功率采用窗口积分估算，"
        "因此 window-based insertion loss 不能等同于严格器件插入损耗。"
        "surrogate model 与 BPM model 的对比主要用于趋势验证，而不是严格数值一致性验证。"
    )
    if sensitivity_result and model_comparison_result:
        window_results = sensitivity_result.get("window_results", [])
        minimum_window = window_results[0] if window_results else {}
        maximum_window = window_results[-1] if window_results else {}
        difference = model_comparison_result.get("difference", {})
        calibration_col1, calibration_col2, calibration_col3, calibration_col4 = (
            st.columns(4)
        )
        with calibration_col1:
            st.metric(
                "默认输出窗口",
                f"{float(sensitivity_result.get('default_output_window_um', 0)):.3f} μm",
            )
        with calibration_col2:
            st.metric("窗口扫描点数", str(len(window_results)))
        with calibration_col3:
            st.metric(
                "最小窗口收集功率",
                f"{float(minimum_window.get('total_collected_power', 0)):.4f}",
            )
        with calibration_col4:
            st.metric(
                "最大窗口收集功率",
                f"{float(maximum_window.get('total_collected_power', 0)):.4f}",
            )

        comparison_col1, comparison_col2, comparison_col3 = st.columns(3)
        with comparison_col1:
            st.metric(
                "BPM - surrogate ΔP1",
                f"{float(difference.get('delta_p_out1', 0)):.4f}",
            )
        with comparison_col2:
            st.metric(
                "BPM - surrogate ΔP2",
                f"{float(difference.get('delta_p_out2', 0)):.4f}",
            )
        with comparison_col3:
            st.metric(
                "BPM - surrogate ΔTotal",
                f"{float(difference.get('delta_total_power', 0)):.4f}",
            )

        st.markdown("#### Enhanced scalar BPM propagation")
        enhanced_path = run_dir / "field_propagation_enhanced.png"
        if enhanced_path.exists():
            st.image(str(enhanced_path), width="stretch")
        else:
            st.warning("未找到 field_propagation_enhanced.png")

        calibration_left, calibration_right = st.columns(2)
        with calibration_left:
            st.markdown("#### Output window sensitivity")
            image_path = run_dir / "output_window_sensitivity.png"
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.warning("未找到 output_window_sensitivity.png")
        with calibration_right:
            st.markdown("#### Surrogate vs BPM comparison")
            image_path = run_dir / "model_comparison.png"
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.warning("未找到 model_comparison.png")

        with st.expander("查看 output_window_sensitivity_result.json"):
            st.json(sensitivity_result)
        with st.expander("查看 model_comparison_result.json"):
            st.json(model_comparison_result)

        calibration_downloads = [
            (
                "field_propagation_enhanced.png",
                "下载增强传播图",
                "image/png",
            ),
            (
                "output_window_sensitivity.png",
                "下载窗口敏感性图",
                "image/png",
            ),
            (
                "output_window_sensitivity_result.json",
                "下载窗口敏感性 JSON",
                "application/json",
            ),
            ("model_comparison.png", "下载模型对比图", "image/png"),
            (
                "model_comparison_result.json",
                "下载模型对比 JSON",
                "application/json",
            ),
        ]
        for column, (filename, label, mime) in zip(
            st.columns(5),
            calibration_downloads,
        ):
            with column:
                _download_file(st, run_dir / filename, label, filename, mime)
    else:
        st.warning("当前运行结果中暂未找到完整的 V3.1 校准与模型对比文件。")

    st.markdown("### 6. MMI 优化与版图可视化")
    visualizations = [
        ("length_sweep.png", "MMI 长度扫描图"),
        ("width_length_heatmap.png", "MMI 宽度—长度二维优化热力图"),
        ("layout_preview.png", "1×2 MMI 版图预览"),
    ]
    for filename, heading in visualizations:
        st.markdown(f"#### {heading}")
        image_path = run_dir / filename
        if image_path.exists():
            st.image(str(image_path), width="stretch")
        else:
            st.warning(f"未找到 {filename}")

    st.markdown("### 7. 结构化结果数据")
    json_sections = [
        ("design_spec.json", design_spec),
        ("physical_params.json", physical_params),
        ("mode_result.json", mode_result),
        ("optimization_result.json", optimization_result),
    ]
    for filename, data in json_sections:
        with st.expander(f"查看 {filename}"):
            st.json(data)

    st.markdown("### 8. 输出文件清单")
    file_rows = []
    for filename, description in V2_OUTPUT_FILES:
        file_path = run_dir / filename
        file_rows.append(
            {
                "文件名": filename,
                "说明": description,
                "状态": "存在" if file_path.exists() else "缺失",
                "大小": format_file_size(file_path),
            }
        )
    st.table(file_rows)

    st.markdown("### 9. 下载结果文件")
    downloads = [
        ("report.md", "下载中文报告", "text/markdown"),
        ("mmi1x2_demo.gds", "下载 GDS 文件", "application/octet-stream"),
        ("ai_pic_demo_results.zip", "下载完整结果包", "application/zip"),
        ("mode_result.json", "下载 mode_result.json", "application/json"),
    ]
    columns = st.columns(4)
    for column, (filename, label, mime) in zip(columns, downloads):
        with column:
            _download_file(st, run_dir / filename, label, filename, mime)
