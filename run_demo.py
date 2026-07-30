from pathlib import Path
import json
import traceback

from core.design_spec import DESIGN_SPEC_VERSION, ParameterSource
from core.material_database import get_platform_materials
from core.mode_solver import run_mode_solver_analysis
from core.model_comparison import run_model_comparison_analysis
from core.mode_overlap import run_mode_overlap_analysis
from core.optimizer import optimize_length
from core.package_generator import create_result_package
from core.propagation_solver import run_propagation_analysis
from core.report_appendix import append_v15_report_appendix
from core.report_generator import generate_report
from core.run_manager import (
    create_run_directory,
    get_output_path,
    init_run_log,
    write_error_log,
    write_run_log,
    write_success_log,
)
from core.run_status import RunStatusTracker, StageCode
from core.spec_parser import parse_design_request, save_design_spec
from core.v23_report_appendix import insert_v23_wavelength_section
from core.v30_report_appendix import append_v30_propagation_section
from core.v31_report_appendix import append_v31_calibration_section
from core.v32_report_appendix import append_v32_mode_overlap_section
from core.v33_report_appendix import append_v33_engineering_section
from core.validation import validate_design_spec, validation_result_to_text
from core.v2_report_appendix import insert_v2_mode_section
from core.wavelength_sweep import run_wavelength_sweep
from layout.gds_generator import generate_gds, generate_layout_preview


DEMO_VERSION = "V3.3"
DEMO_DESCRIPTION = (
    "DesignSpec 与本地 MCP 基础版：保留 V3.2 物理流程并增加结构化工程接口"
)


def save_json(data: dict, path: Path) -> None:
    """将字典保存为 UTF-8 JSON 文件。"""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def spec_to_dict(spec) -> dict:
    """兼容普通字典、Pydantic 对象和 dataclass 对象。"""
    if isinstance(spec, dict):
        return spec
    if hasattr(spec, "model_dump"):
        return spec.model_dump()
    if hasattr(spec, "dict"):
        return spec.dict()
    return vars(spec)


def main() -> None:
    run_dir = create_run_directory(Path("outputs"))
    init_run_log(
        run_dir=run_dir,
        version=DEMO_VERSION,
        description=DEMO_DESCRIPTION,
    )

    write_run_log(run_dir, "Demo started.")
    write_run_log(run_dir, f"Run directory created: {run_dir}")
    status_tracker = RunStatusTracker(
        run_dir,
        demo_version=DEMO_VERSION,
        design_spec_schema_version=DESIGN_SPEC_VERSION,
    )
    active_code = StageCode.INPUT_EXTRACTION
    active_stage = "input_extraction"

    try:
        user_requirement = (
            "请帮我设计一个 1550 nm、SOI 平台、50:50 分光的 1×2 MMI 分束器。"
        )
        write_run_log(run_dir, "Natural language requirement received.")
        write_run_log(run_dir, user_requirement)

        # 1. 解析自然语言需求并保存结构化参数
        parse_result = parse_design_request(user_requirement)
        if not parse_result.is_valid or parse_result.design_spec is None:
            status_tracker.record(
                StageCode.INPUT_EXTRACTION,
                stage="input_extraction",
                state="failed",
                message="; ".join(
                    parse_result.errors or parse_result.clarification_questions
                ),
                recoverable=True,
                suggested_action="补充澄清问题后重新运行。",
            )
            print("\n需求需要澄清，程序已停止。")
            for question in parse_result.clarification_questions:
                print(f"- {question}")
            return
        unified_design_spec = parse_result.design_spec
        design_spec_dict = unified_design_spec.to_legacy_dict()
        design_spec_path = save_design_spec(unified_design_spec, run_dir)
        status_tracker.record(
            StageCode.INPUT_EXTRACTION,
            stage="input_extraction",
            state="success",
            message="Natural-language request parsed into DesignSpec 1.0.",
            recoverable=False,
            suggested_action="Continue with schema validation.",
        )
        write_run_log(run_dir, "Design specification parsed.")
        write_run_log(run_dir, f"Saved design_spec.json: {design_spec_path}")

        # 2. 在进入物理建模和优化前完成参数校验
        active_code = StageCode.SCHEMA_VALIDATION
        active_stage = "schema_validation"
        validation_result = validate_design_spec(design_spec_dict)
        validation_text = validation_result_to_text(validation_result)
        write_run_log(run_dir, "Validation result:")
        write_run_log(run_dir, validation_text)

        if not validation_result.is_valid:
            status_tracker.record(
                StageCode.SCHEMA_VALIDATION,
                stage="schema_validation",
                state="failed",
                message="; ".join(validation_result.errors),
                recoverable=True,
                suggested_action="修正 DesignSpec 中的物理范围或流程依赖。",
            )
            print("\n参数校验未通过，程序已停止。")
            print(validation_text)
            write_run_log(run_dir, "Demo stopped because validation failed.")
            write_run_log(run_dir, "Status: FAILED")
            return

        status_tracker.record(
            StageCode.SCHEMA_VALIDATION,
            stage="schema_validation",
            state="success",
            message="DesignSpec schema and legacy physical validation passed.",
            recoverable=False,
            suggested_action="Continue with physical parameter preparation.",
        )
        print("\n参数校验通过。")
        if validation_result.warnings:
            print("\n参数警告：")
            for warning in validation_result.warnings:
                print(f"- {warning}")

        # 3. 运行 V2 模式分析，并将模式求解 neff 接入 MMI 优化
        active_code = StageCode.PHYSICAL_PARAMETERS
        active_stage = "physical_parameters"
        material_params = get_platform_materials(design_spec_dict["platform"])
        waveguide_width_um = design_spec_dict["waveguide_width_um"]
        waveguide_height_um = design_spec_dict["waveguide_height_um"]
        wavelength_um = design_spec_dict["wavelength_um"]
        status_tracker.record(
            StageCode.PHYSICAL_PARAMETERS,
            stage="physical_parameters",
            state="success",
            message="SOI material and geometry parameters prepared.",
            recoverable=False,
            suggested_action="Run the existing scalar finite-difference mode solver.",
        )

        active_code = StageCode.MODE_SOLVER
        active_stage = "mode_solver"
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
        design_spec_dict["neff"] = estimated_neff
        use_estimated_neff = design_spec_dict.get("use_estimated_neff", True)
        design_spec_dict["use_estimated_neff"] = False

        write_run_log(run_dir, "V2 mode solver finished.")
        write_run_log(
            run_dir,
            f"Mode result path: {mode_result['mode_result_path']}",
        )
        write_run_log(
            run_dir,
            "Index profile path: "
            f"{mode_result['index_profile_result']['index_profile_path']}",
        )
        write_run_log(
            run_dir,
            "Mode profile path: "
            f"{mode_result['mode_profile_result']['mode_profile_path']}",
        )
        write_run_log(
            run_dir,
            "neff vs width path: "
            f"{mode_result['neff_sweep_result']['neff_vs_width_path']}",
        )
        write_run_log(run_dir, f"V2 neff used for MMI: {estimated_neff:.4f}")
        status_tracker.record(
            StageCode.MODE_SOLVER,
            stage="mode_solver",
            state="success",
            message="Existing V3.2 scalar finite-difference mode stage completed.",
            recoverable=False,
            suggested_action="Continue with the existing MMI optimization.",
        )

        active_code = StageCode.OPTIMIZATION
        active_stage = "optimization"
        optimization_result = optimize_length(
            spec=design_spec_dict,
            output_dir=run_dir,
        )
        optimization_result_path = get_output_path(
            run_dir, "optimization_result.json"
        )
        physical_params_path = get_output_path(run_dir, "physical_params.json")

        # 优化器保持 V1.5 兼容接口；运行后恢复用户语义并补充 V2 模式字段。
        design_spec_dict["use_estimated_neff"] = use_estimated_neff
        unified_design_spec.simulation.neff.value = float(estimated_neff)
        unified_design_spec.simulation.neff.source = ParameterSource.FORMULA
        unified_design_spec.save_json(design_spec_path)

        physical_params = json.loads(
            physical_params_path.read_text(encoding="utf-8")
        )
        physical_params.update(
            {
                "estimated_neff": estimated_neff,
                "neff_used": estimated_neff,
                "use_estimated_neff": use_estimated_neff,
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
                "note": (
                    "V2 neff comes from the approximate TE0 mode solver. "
                    "It is not a rigorous FDE/FEM eigenmode result."
                ),
            }
        )
        save_json(physical_params, physical_params_path)

        optimization_result["estimated_neff"] = estimated_neff
        optimization_result["neff_used"] = estimated_neff
        save_json(optimization_result, optimization_result_path)

        write_run_log(run_dir, "Width-length optimization finished.")
        write_run_log(
            run_dir,
            f"Saved physical_params.json: {physical_params_path}",
        )
        write_run_log(
            run_dir,
            f"Saved optimization_result.json: {optimization_result_path}",
        )

        best_width_um = optimization_result["best_width_um"]
        best_length_um = optimization_result["best_length_um"]

        wavelength_sweep_result = run_wavelength_sweep(
            design_spec=design_spec_dict,
            material_params=material_params,
            best_width_um=best_width_um,
            best_length_um=best_length_um,
            output_dir=run_dir,
            wavelength_min_um=1.50,
            wavelength_max_um=1.60,
            num_points=21,
        )
        write_run_log(run_dir, "V2.5 FD-neff wavelength sweep finished.")
        write_run_log(
            run_dir,
            "Wavelength sweep result path: "
            f"{wavelength_sweep_result['wavelength_sweep_result_path']}",
        )
        write_run_log(
            run_dir,
            "Max abs imbalance in wavelength sweep: "
            f"{wavelength_sweep_result['max_abs_imbalance_db']:.4f} dB",
        )
        status_tracker.record(
            StageCode.OPTIMIZATION,
            stage="optimization",
            state="success",
            message="Existing width-length optimization and wavelength sweep completed.",
            recoverable=False,
            suggested_action="Continue with scalar BPM propagation validation.",
        )

        # 4. 在 surrogate 优化之后增加 V3.0 标量 BPM 传播验证。
        active_code = StageCode.PROPAGATION
        active_stage = "propagation"
        propagation_result = None
        try:
            propagation_result = run_propagation_analysis(
                design_spec=design_spec_dict,
                optimization_result=optimization_result,
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
            status_tracker.record(
                StageCode.PROPAGATION,
                stage="propagation",
                state="success",
                message="Existing V3.2 scalar BPM stage completed.",
                recoverable=False,
                suggested_action="Continue with overlap analysis.",
            )
        except Exception as propagation_error:
            write_run_log(
                run_dir,
                "V3.0 propagation analysis failed; continuing V2.6 workflow: "
                f"{type(propagation_error).__name__}: {propagation_error}",
            )
            write_run_log(run_dir, traceback.format_exc())
            status_tracker.record(
                StageCode.PROPAGATION,
                stage="propagation",
                state="failed",
                message=f"{type(propagation_error).__name__}: {propagation_error}",
                recoverable=True,
                suggested_action="Inspect run_log.txt; non-BPM outputs may still be used.",
            )

        model_comparison_result = None
        if propagation_result is not None:
            try:
                model_comparison_result = run_model_comparison_analysis(
                    optimization_result=optimization_result,
                    propagation_result=propagation_result,
                    output_dir=run_dir,
                )
                write_run_log(run_dir, "V3.1 model comparison finished.")
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
        else:
            write_run_log(
                run_dir,
                "V3.1 model comparison skipped because propagation failed.",
            )

        active_code = StageCode.MODE_OVERLAP
        active_stage = "mode_overlap"
        mode_overlap_result = None
        if propagation_result is not None:
            try:
                mode_overlap_result = run_mode_overlap_analysis(
                    design_spec=design_spec_dict,
                    optimization_result=optimization_result,
                    mode_result=mode_result,
                    propagation_result=propagation_result,
                    output_dir=run_dir,
                )
                write_run_log(run_dir, "V3.2 port mode overlap analysis finished.")
                write_run_log(
                    run_dir,
                    "mode_overlap_result.json generated: "
                    f"{mode_overlap_result['mode_overlap_result_path']}",
                )
                write_run_log(
                    run_dir,
                    "mode_overlap_comparison.png generated: "
                    f"{mode_overlap_result['mode_overlap_comparison_path']}",
                )
                write_run_log(
                    run_dir,
                    "field_output_profile_with_modes.png generated: "
                    f"{mode_overlap_result['field_output_profile_with_modes_path']}",
                )
                status_tracker.record(
                    StageCode.MODE_OVERLAP,
                    stage="mode_overlap",
                    state="success",
                    message="Existing V3.2 Gaussian overlap stage completed.",
                    recoverable=False,
                    suggested_action="Continue with layout generation.",
                )
            except Exception as overlap_error:
                write_run_log(
                    run_dir,
                    "V3.2 mode overlap failed; continuing V3.1 workflow: "
                    f"{type(overlap_error).__name__}: {overlap_error}",
                )
                write_run_log(run_dir, traceback.format_exc())
                status_tracker.record(
                    StageCode.MODE_OVERLAP,
                    stage="mode_overlap",
                    state="failed",
                    message=f"{type(overlap_error).__name__}: {overlap_error}",
                    recoverable=True,
                    suggested_action="Inspect overlap inputs; earlier stages remain available.",
                )
        else:
            write_run_log(
                run_dir,
                "V3.2 mode overlap skipped because propagation failed.",
            )
            status_tracker.record(
                StageCode.MODE_OVERLAP,
                stage="mode_overlap",
                state="failed",
                message="Skipped because scalar BPM propagation did not complete.",
                recoverable=True,
                suggested_action="Resolve the BPM stage before requesting overlap results.",
            )

        # 5. 生成 GDS 和版图预览图
        active_code = StageCode.LAYOUT
        active_stage = "layout"
        gds_path = generate_gds(
            spec=design_spec_dict,
            result=optimization_result,
            output_dir=run_dir,
        )
        layout_preview_path = generate_layout_preview(
            spec=design_spec_dict,
            result=optimization_result,
            output_dir=run_dir,
        )
        write_run_log(run_dir, f"GDS generated: {gds_path}")
        write_run_log(
            run_dir,
            f"Layout preview generated: {layout_preview_path}",
        )
        status_tracker.record(
            StageCode.LAYOUT,
            stage="layout",
            state="success",
            message="GDS and layout preview generated.",
            recoverable=False,
            suggested_action="Generate the report and package.",
        )

        # 6. 生成报告并打包本次运行结果
        active_code = StageCode.REPORT
        active_stage = "report"
        report_path = generate_report(
            spec=design_spec_dict,
            result=optimization_result,
            gds_path=gds_path,
            output_dir=run_dir,
            version=DEMO_VERSION,
        )
        write_run_log(run_dir, f"Report generated: {report_path}")

        insert_v2_mode_section(
            report_path=report_path,
            mode_result=mode_result,
        )
        write_run_log(run_dir, "V2 mode solver report section inserted.")

        insert_v23_wavelength_section(
            report_path=report_path,
            wavelength_sweep_result=wavelength_sweep_result,
        )
        write_run_log(run_dir, "V2.5 wavelength sweep report section inserted.")

        if propagation_result is not None:
            append_v30_propagation_section(
                report_path=report_path,
                propagation_result_path=Path(
                    propagation_result["propagation_result_path"]
                ),
            )
            write_run_log(run_dir, "V3.0 propagation report section appended.")

        if model_comparison_result is not None:
            try:
                append_v31_calibration_section(
                    report_path=report_path,
                    output_dir=run_dir,
                )
                write_run_log(
                    run_dir,
                    "V3.1 calibration report section appended.",
                )
            except Exception as calibration_report_error:
                write_run_log(
                    run_dir,
                    "V3.1 calibration report append failed; continuing: "
                    f"{type(calibration_report_error).__name__}: "
                    f"{calibration_report_error}",
                )
                write_run_log(run_dir, traceback.format_exc())

        if mode_overlap_result is not None:
            try:
                append_v32_mode_overlap_section(
                    report_path=report_path,
                    output_dir=run_dir,
                )
                write_run_log(
                    run_dir,
                    "V3.2 mode overlap report section appended.",
                )
            except Exception as overlap_report_error:
                write_run_log(
                    run_dir,
                    "V3.2 mode overlap report append failed; continuing: "
                    f"{type(overlap_report_error).__name__}: "
                    f"{overlap_report_error}",
                )
                write_run_log(run_dir, traceback.format_exc())

        append_v33_engineering_section(report_path)
        write_run_log(run_dir, "V3.3 DesignSpec/MCP report section appended.")

        zip_path = create_result_package(output_dir=run_dir)
        write_run_log(run_dir, f"Result package generated: {zip_path}")

        append_v15_report_appendix(
            report_path=report_path,
            run_dir=run_dir,
            validation_text=validation_text,
            version=DEMO_VERSION,
            description=DEMO_DESCRIPTION,
        )
        write_run_log(run_dir, f"{DEMO_VERSION} report appendix added.")
        status_tracker.record(
            StageCode.REPORT,
            stage="report",
            state="success",
            message="Report and engineering appendix generated.",
            recoverable=False,
            suggested_action="Finalize the run manifest and result package.",
        )

        # 刷新结果包，确保 ZIP 中包含追加工程说明后的最终报告。
        status_tracker.success(
            "V3.3 DesignSpec/MCP engineering flow completed without changing V3.2 physics."
        )
        zip_path = create_result_package(output_dir=run_dir)
        write_run_log(run_dir, "Result package refreshed with final report.")

        print(f"\nAI PIC Design Platform Demo {DEMO_VERSION} finished successfully.")
        print("=" * 60)
        print(f"Run directory:       {run_dir}")
        print(f"Estimated neff:      {estimated_neff:.4f}")
        print(
            "Index profile:       "
            f"{mode_result['index_profile_result']['index_profile_path']}"
        )
        print(
            "Mode profile:        "
            f"{mode_result['mode_profile_result']['mode_profile_path']}"
        )
        print(
            "neff vs width:       "
            f"{mode_result['neff_sweep_result']['neff_vs_width_path']}"
        )
        print(f"Best MMI width:      {best_width_um:.3f} μm")
        print(f"Best MMI length:     {best_length_um:.3f} μm")
        print(f"Output port 1:       {optimization_result['p_out1']:.4f}")
        print(f"Output port 2:       {optimization_result['p_out2']:.4f}")
        print(
            "Insertion loss:      "
            f"{optimization_result['insertion_loss_db']:.3f} dB"
        )
        print(f"Imbalance:           {optimization_result['imbalance_db']:.3f} dB")
        print(f"Best score:          {optimization_result['best_score']:.6f}")
        if propagation_result is not None:
            print(
                "BPM output powers:   "
                f"{propagation_result['p_out1']:.4f} / "
                f"{propagation_result['p_out2']:.4f}"
            )
            print(
                "BPM collected power: "
                f"{propagation_result['total_collected_power']:.4f}"
            )
        if model_comparison_result is not None:
            print(
                "BPM-surrogate ΔP:    "
                f"{model_comparison_result['difference']['delta_total_power']:.4f}"
            )
        if mode_overlap_result is not None:
            print(
                "BPM overlap powers:  "
                f"{mode_overlap_result['overlap_p_out1']:.4f} / "
                f"{mode_overlap_result['overlap_p_out2']:.4f}"
            )
            print(
                "BPM overlap total:   "
                f"{mode_overlap_result['total_overlap_power']:.4f}"
            )
        print("=" * 60)
        print(f"Report:              {report_path}")
        print(f"GDS:                 {gds_path}")
        print(f"ZIP:                 {zip_path}")

        write_success_log(run_dir)

    except Exception as error:
        print("\n程序运行失败，错误信息如下：")
        print(type(error).__name__)
        print(str(error))

        error_text = traceback.format_exc()
        print("\n完整错误追踪：")
        print(error_text)

        write_error_log(run_dir, error)
        write_run_log(run_dir, "Traceback:")
        write_run_log(run_dir, error_text)
        status_tracker.record(
            active_code,
            stage=active_stage,
            state="failed",
            message=f"{type(error).__name__}: {error}",
            recoverable=False,
            suggested_action="Inspect run_log.txt and the latest traceback.",
        )


if __name__ == "__main__":
    main()
