import json
import traceback
from pathlib import Path

import streamlit as st

from core.material_database import get_platform_materials
from core.mode_solver import run_mode_solver_analysis
from core.optimizer import optimize_length
from core.package_generator import create_result_package
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
from core.v2_report_appendix import insert_v2_mode_section
from core.v2_web_utils import display_v2_result_panel, find_latest_run_dir
from core.validation import validate_design_spec, validation_result_to_text
from layout.gds_generator import generate_gds, generate_layout_preview


DEMO_VERSION = "V2.1"
DEMO_DESCRIPTION = (
    "网页展示增强版：展示模式场、neff 宽度扫描、MMI 优化、GDS 与完整结果包"
)


def save_json(data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


st.set_page_config(
    page_title="AI 光子芯片设计平台 Demo V2.1",
    layout="wide",
)

st.title("AI 光子芯片设计平台 Demo")
st.caption(f"{DEMO_VERSION} | {DEMO_DESCRIPTION}")
st.subheader("1×2 MMI 光功率分束器自动设计示例")
st.markdown(
    """
V2.1 在 V2 模式求解主流程基础上，完整展示近似 TE0 模式场、neff 宽度扫描、
MMI 二维优化、版图与工程交付文件。当前仍为轻量近似模型，不是真实 FDE/FEM/EME 电磁仿真。
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
    run_button = st.button("运行 V2.1 设计", type="primary")


if run_button:
    st.session_state.pop("last_run_dir", None)
    run_dir = create_run_directory("outputs")
    init_run_log(run_dir, DEMO_VERSION, DEMO_DESCRIPTION)
    write_run_log(run_dir, "Streamlit V2.1 design run started.")

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

        with st.spinner("正在运行 V2.1 模式分析与 MMI 优化流程..."):
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
                num_width_points=40,
            )
            estimated_neff = mode_result["neff_used_for_mmi"]
            spec["neff"] = estimated_neff
            original_use_estimated_neff = spec["use_estimated_neff"]
            spec["use_estimated_neff"] = False
            write_run_log(run_dir, "V2.1 mode solver finished.")
            write_run_log(
                run_dir,
                f"V2.1 neff used for MMI: {estimated_neff:.4f}",
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
            write_run_log(run_dir, "V2.1 mode solver report section inserted.")

            zip_path = create_result_package(output_dir=run_dir)
            append_v15_report_appendix(
                report_path=report_path,
                run_dir=run_dir,
                validation_text=validation_text,
                version=DEMO_VERSION,
                description=DEMO_DESCRIPTION,
            )
            write_run_log(run_dir, "V2.1 engineering appendix added.")
            write_success_log(run_dir)
            zip_path = create_result_package(output_dir=run_dir)
            write_run_log(run_dir, f"Final result package generated: {zip_path}")

        st.success("V2.1 设计流程运行完成。")
        st.session_state["last_run_dir"] = str(run_dir)

    except Exception as error:
        st.error("运行失败，请查看错误信息。")
        st.exception(error)
        write_error_log(run_dir, error)
        write_run_log(run_dir, "Traceback:")
        write_run_log(run_dir, traceback.format_exc())


st.divider()
st.subheader("查看最近一次 V2.1 运行结果")
if st.button("加载最近一次运行结果"):
    latest_run_dir = find_latest_run_dir("outputs")
    if latest_run_dir is None:
        st.warning("未找到 outputs/run_时间戳 目录，请先运行一次设计。")
    else:
        st.session_state["last_run_dir"] = str(latest_run_dir)

if "last_run_dir" in st.session_state:
    display_v2_result_panel(st.session_state["last_run_dir"])
else:
    st.info("请运行一次 V2.1 设计，或加载最近一次运行结果。")

st.divider()
st.markdown(
    """
### 当前 V2.1 demo 的定位

V2.1 将 V2 模式求解主流程完整同步到网页端，可展示模式场、neff 扫描、MMI 优化、
版图、结构化 JSON 与全部交付文件。当前模式模块仍是近似模型，后续可替换为严格 FDE/FEM 求解器。
"""
)
