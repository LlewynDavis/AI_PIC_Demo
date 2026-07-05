import json
import traceback
from pathlib import Path

import streamlit as st

from core.material_database import get_platform_materials
from core.mode_solver import run_mode_solver_analysis
from core.model_comparison import run_model_comparison_analysis
from core.optimizer import optimize_length
from core.package_generator import create_result_package
from core.propagation_solver import run_propagation_analysis
from core.report_appendix import append_v15_report_appendix
from core.report_generator import generate_report
from core.run_manager import (
    create_run_directory,
    init_run_log,
    write_error_log,
    write_run_log,
    write_success_log,
)
from core.spec_parser import parse_design_text, save_design_spec
from core.v23_report_appendix import insert_v23_wavelength_section
from core.v2_report_appendix import insert_v2_mode_section
from core.v30_report_appendix import append_v30_propagation_section
from core.v31_report_appendix import append_v31_calibration_section
from core.v2_web_utils import display_v2_result_panel, find_latest_run_dir
from core.validation import validate_design_spec, validation_result_to_text
from core.wavelength_sweep import run_wavelength_sweep
from layout.gds_generator import generate_gds, generate_layout_preview


DEMO_VERSION = "V3.1"
DEMO_DESCRIPTION = (
    "传播仿真校准与模型对比版：展示窗口敏感性和 surrogate/BPM 趋势对比"
)


def save_json(data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


st.set_page_config(
    page_title="AI 光子芯片设计平台 Demo V3.1",
    layout="wide",
)

st.title("AI 光子芯片设计平台 Demo")
st.caption(f"{DEMO_VERSION} | {DEMO_DESCRIPTION}")
st.subheader("1×2 MMI 光功率分束器自动设计示例")
st.markdown(
    """
V3.1 在 V3.0 二维标量 BPM 传播基础上增加输出窗口敏感性和 surrogate/BPM 对比，
用于趋势校准和结果解释。Window-based insertion loss 不是严格器件插入损耗。
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
        st.session_state["use_estimated_neff"] = parsed_spec[
            "use_estimated_neff"
        ]
        st.session_state["waveguide_width_um"] = parsed_spec[
            "waveguide_width_um"
        ]
        st.session_state["waveguide_height_um"] = parsed_spec[
            "waveguide_height_um"
        ]
        st.session_state["mmi_width_um"] = parsed_spec["mmi_width_um"]
        st.session_state["length_min_um"] = parsed_spec[
            "length_scan_range_um"
        ][0]
        st.session_state["length_max_um"] = parsed_spec[
            "length_scan_range_um"
        ][1]
        st.session_state["num_scan_points"] = parsed_spec["num_scan_points"]
        st.session_state["width_min_um"] = parsed_spec[
            "mmi_width_scan_range_um"
        ][0]
        st.session_state["width_max_um"] = parsed_spec[
            "mmi_width_scan_range_um"
        ][1]
        st.session_state["num_width_scan_points"] = parsed_spec[
            "num_width_scan_points"
        ]
        st.success("需求解析完成，参数已填入下方输入框。")

    if "parsed_spec" in st.session_state:
        st.markdown("#### 解析后的结构化参数")
        st.json(st.session_state["parsed_spec"])

    st.divider()
    st.header("物理平台参数")
    platform = st.selectbox("光子平台", options=["SOI"], index=0)
    use_estimated_neff = st.checkbox(
        "使用 V2 模式求解 neff",
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
    run_button = st.button("运行 V3.1 设计", type="primary")


if run_button:
    st.session_state.pop("last_run_dir", None)
    run_dir = create_run_directory(Path("outputs"))
    init_run_log(run_dir, DEMO_VERSION, DEMO_DESCRIPTION)
    write_run_log(run_dir, "Streamlit V3.1 design run started.")

    try:
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
        design_spec_path = save_design_spec(spec=spec, output_dir=run_dir)
        write_run_log(run_dir, f"Saved design_spec.json: {design_spec_path}")

        validation_result = validate_design_spec(spec)
        validation_text = validation_result_to_text(validation_result)
        write_run_log(run_dir, "Validation result:")
        write_run_log(run_dir, validation_text)

        if not validation_result.is_valid:
            st.error("参数校验未通过，请修改输入参数后重新运行。")
            st.text(validation_text)
            write_run_log(run_dir, "Streamlit run stopped: validation failed.")
            write_run_log(run_dir, "Status: FAILED")
            st.stop()

        st.success("参数校验通过。")
        if validation_result.warnings:
            with st.expander("参数警告信息", expanded=True):
                for warning in validation_result.warnings:
                    st.warning(warning)

        with st.spinner("正在运行 V3.1 模式、优化、BPM 传播与校准分析..."):
            material_params = get_platform_materials(spec["platform"])
            mode_result = run_mode_solver_analysis(
                core_index=material_params["core_index"],
                cladding_index=material_params["cladding_index"],
                waveguide_width_um=waveguide_width_um,
                waveguide_height_um=waveguide_height_um,
                wavelength_um=wavelength_um,
                output_dir=run_dir,
                width_min_um=0.3,
                width_max_um=0.8,
                num_width_points=21,
            )
            estimated_neff = mode_result["neff_used_for_mmi"]
            spec["neff"] = estimated_neff
            original_use_estimated_neff = spec["use_estimated_neff"]
            spec["use_estimated_neff"] = False
            write_run_log(run_dir, "V2.5 finite-difference mode solver finished.")
            write_run_log(
                run_dir,
                f"V2.5 FD neff used for MMI: {estimated_neff:.4f}",
            )
            write_run_log(
                run_dir,
                f"Mode result path: {mode_result['mode_result_path']}",
            )

            result = optimize_length(spec=spec, output_dir=run_dir)
            spec["use_estimated_neff"] = original_use_estimated_neff
            save_design_spec(spec=spec, output_dir=run_dir)

            physical_params_path = run_dir / "physical_params.json"
            physical_params = json.loads(
                physical_params_path.read_text(encoding="utf-8")
            )
            physical_params.update(
                {
                    "estimated_neff": estimated_neff,
                    "neff_used": estimated_neff,
                    "use_estimated_neff": original_use_estimated_neff,
                    "mode_solver_type": mode_result["mode_profile_result"][
                        "mode_solver_type"
                    ],
                    "mode_solver_version": mode_result["mode_solver_version"],
                    "beta": mode_result["mode_profile_result"]["beta"],
                    "grid_size_x": mode_result["mode_profile_result"][
                        "grid_size_x"
                    ],
                    "grid_size_y": mode_result["mode_profile_result"][
                        "grid_size_y"
                    ],
                    "dx_um": mode_result["mode_profile_result"]["dx_um"],
                    "dy_um": mode_result["mode_profile_result"]["dy_um"],
                    "index_profile_path": mode_result["index_profile_result"][
                        "index_profile_path"
                    ],
                    "mode_profile_path": mode_result["mode_profile_result"][
                        "mode_profile_path"
                    ],
                    "neff_vs_width_path": mode_result["neff_sweep_result"][
                        "neff_vs_width_path"
                    ],
                    "mode_result_path": mode_result["mode_result_path"],
                    "confinement_factor": mode_result["mode_profile_result"][
                        "confinement_factor"
                    ],
                    "mode_area_um2": mode_result["mode_profile_result"][
                        "mode_area_um2"
                    ],
                }
            )
            save_json(physical_params, physical_params_path)

            result["estimated_neff"] = estimated_neff
            result["neff_used"] = estimated_neff
            save_json(result, run_dir / "optimization_result.json")
            write_run_log(run_dir, "Width-length optimization finished.")

            wavelength_sweep_result = run_wavelength_sweep(
                design_spec=spec,
                material_params=material_params,
                best_width_um=result["best_width_um"],
                best_length_um=result["best_length_um"],
                output_dir=run_dir,
                wavelength_min_um=1.50,
                wavelength_max_um=1.60,
                num_points=21,
            )
            write_run_log(
                run_dir,
                "V2.5 FD-neff wavelength sweep finished in Streamlit.",
            )

            propagation_result = None
            try:
                propagation_result = run_propagation_analysis(
                    design_spec=spec,
                    optimization_result=result,
                    mode_result=mode_result,
                    output_dir=run_dir,
                )
                write_run_log(run_dir, "V3.0 scalar BPM propagation finished.")
                write_run_log(
                    run_dir,
                    "propagation_result.json generated: "
                    f"{propagation_result['propagation_result_path']}",
                )
                write_run_log(
                    run_dir,
                    "field_propagation.png generated: "
                    f"{propagation_result['field_propagation_path']}",
                )
                write_run_log(
                    run_dir,
                    "field_output_profile.png generated: "
                    f"{propagation_result['field_output_profile_path']}",
                )
                write_run_log(
                    run_dir,
                    "field_propagation_enhanced.png generated: "
                    f"{propagation_result['field_propagation_enhanced_path']}",
                )
                write_run_log(
                    run_dir,
                    "output_window_sensitivity_result.json generated: "
                    f"{propagation_result['output_window_sensitivity_result_path']}",
                )
                write_run_log(
                    run_dir,
                    "output_window_sensitivity.png generated: "
                    f"{propagation_result['output_window_sensitivity_plot_path']}",
                )
            except Exception as propagation_error:
                write_run_log(
                    run_dir,
                    "V3.0 propagation analysis failed; continuing V2.6 workflow: "
                    f"{type(propagation_error).__name__}: {propagation_error}",
                )
                write_run_log(run_dir, traceback.format_exc())
                st.warning(
                    "V3.0 传播仿真未完成；V2.6 模式、优化、波长扫描和版图流程将继续。"
                )

            model_comparison_result = None
            if propagation_result is not None:
                try:
                    model_comparison_result = run_model_comparison_analysis(
                        optimization_result=result,
                        propagation_result=propagation_result,
                        output_dir=run_dir,
                    )
                    write_run_log(
                        run_dir,
                        "V3.1 surrogate/BPM model comparison finished.",
                    )
                    write_run_log(
                        run_dir,
                        "model_comparison_result.json generated: "
                        f"{model_comparison_result['model_comparison_result_path']}",
                    )
                    write_run_log(
                        run_dir,
                        "model_comparison.png generated: "
                        f"{model_comparison_result['model_comparison_plot_path']}",
                    )
                except Exception as comparison_error:
                    write_run_log(
                        run_dir,
                        "V3.1 model comparison failed; continuing V3.0 workflow: "
                        f"{type(comparison_error).__name__}: {comparison_error}",
                    )
                    write_run_log(run_dir, traceback.format_exc())
                    st.warning(
                        "V3.1 模型对比未完成；V3.0 传播和 V2.6 基线结果仍可继续生成。"
                    )

            gds_path = generate_gds(spec=spec, result=result, output_dir=run_dir)
            layout_preview_path = generate_layout_preview(
                spec=spec,
                result=result,
                output_dir=run_dir,
            )
            write_run_log(run_dir, f"GDS generated: {gds_path}")
            write_run_log(
                run_dir,
                f"Layout preview generated: {layout_preview_path}",
            )

            report_path = generate_report(
                spec=spec,
                result=result,
                gds_path=gds_path,
                output_dir=run_dir,
                version=DEMO_VERSION,
            )
            insert_v2_mode_section(report_path=report_path, mode_result=mode_result)
            write_run_log(run_dir, "V2.5 FD mode solver report section inserted.")

            insert_v23_wavelength_section(
                report_path=report_path,
                wavelength_sweep_result=wavelength_sweep_result,
            )
            write_run_log(
                run_dir,
                "V2.5 wavelength sweep report section inserted in Streamlit.",
            )

            if propagation_result is not None:
                append_v30_propagation_section(
                    report_path=report_path,
                    propagation_result_path=Path(
                        propagation_result["propagation_result_path"]
                    ),
                )
                write_run_log(
                    run_dir,
                    "V3.0 propagation report section appended in Streamlit.",
                )

            if model_comparison_result is not None:
                try:
                    append_v31_calibration_section(
                        report_path=report_path,
                        output_dir=run_dir,
                    )
                    write_run_log(
                        run_dir,
                        "V3.1 calibration report section appended in Streamlit.",
                    )
                except Exception as calibration_report_error:
                    write_run_log(
                        run_dir,
                        "V3.1 calibration report append failed; continuing: "
                        f"{type(calibration_report_error).__name__}: "
                        f"{calibration_report_error}",
                    )
                    write_run_log(run_dir, traceback.format_exc())

            zip_path = create_result_package(output_dir=run_dir)
            append_v15_report_appendix(
                report_path=report_path,
                run_dir=run_dir,
                validation_text=validation_text,
                version=DEMO_VERSION,
                description=DEMO_DESCRIPTION,
            )
            write_run_log(run_dir, "V3.1 engineering appendix added.")
            write_success_log(run_dir)
            zip_path = create_result_package(output_dir=run_dir)
            write_run_log(run_dir, f"Final result package generated: {zip_path}")

        st.success("V3.1 设计流程运行完成。")
        st.session_state["last_run_dir"] = str(run_dir)

    except Exception as error:
        st.error("运行失败，请查看错误信息。")
        st.exception(error)
        write_error_log(run_dir, error)
        write_run_log(run_dir, "Traceback:")
        write_run_log(run_dir, traceback.format_exc())


st.divider()
st.subheader("查看最近一次 V3.1 运行结果")
if st.button("加载最近一次运行结果"):
    latest_run_dir = find_latest_run_dir(Path("outputs"))
    if latest_run_dir is None:
        st.warning("未找到 outputs/run_时间戳 目录，请先运行一次设计。")
    else:
        st.session_state["last_run_dir"] = str(latest_run_dir)

if "last_run_dir" in st.session_state:
    display_v2_result_panel(st.session_state["last_run_dir"])
else:
    st.info("请运行一次 V3.1 设计，或加载最近一次运行结果。")

st.divider()
st.markdown(
    """
### 当前 V3.1 demo 的定位

V3.1 保留 V3.0 二维标量 BPM 传播，并新增窗口宽度敏感性、增强传播图和 surrogate/BPM 对比。
输出功率仍是窗口积分估计，window-based insertion loss 不是严格器件损耗，也不是全矢量 S 参数。
"""
)
