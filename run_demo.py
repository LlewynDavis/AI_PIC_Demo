from pathlib import Path
import json
import traceback

from core.material_database import get_platform_materials
from core.mode_solver import run_mode_solver_analysis
from core.optimizer import optimize_length
from core.package_generator import create_result_package
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
from core.spec_parser import parse_design_text
from core.validation import validate_design_spec, validation_result_to_text
from core.v2_report_appendix import insert_v2_mode_section
from layout.gds_generator import generate_gds, generate_layout_preview


DEMO_VERSION = "V2"
DEMO_DESCRIPTION = (
    "模式求解版：近似 TE0 模式场、neff 宽度扫描、模式结果接入 MMI 优化流程"
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
    run_dir = create_run_directory("outputs")
    init_run_log(
        run_dir=run_dir,
        version=DEMO_VERSION,
        description=DEMO_DESCRIPTION,
    )

    write_run_log(run_dir, "Demo started.")
    write_run_log(run_dir, f"Run directory created: {run_dir}")

    try:
        user_requirement = (
            "请帮我设计一个 1550 nm、SOI 平台、50:50 分光的 1×2 MMI 分束器。"
        )
        write_run_log(run_dir, "Natural language requirement received.")
        write_run_log(run_dir, user_requirement)

        # 1. 解析自然语言需求并保存结构化参数
        design_spec = parse_design_text(user_requirement)
        design_spec_dict = spec_to_dict(design_spec)
        design_spec_path = get_output_path(run_dir, "design_spec.json")
        save_json(design_spec_dict, design_spec_path)
        write_run_log(run_dir, "Design specification parsed.")
        write_run_log(run_dir, f"Saved design_spec.json: {design_spec_path}")

        # 2. 在进入物理建模和优化前完成参数校验
        validation_result = validate_design_spec(design_spec_dict)
        validation_text = validation_result_to_text(validation_result)
        write_run_log(run_dir, "Validation result:")
        write_run_log(run_dir, validation_text)

        if not validation_result.is_valid:
            print("\n参数校验未通过，程序已停止。")
            print(validation_text)
            write_run_log(run_dir, "Demo stopped because validation failed.")
            write_run_log(run_dir, "Status: FAILED")
            return

        print("\n参数校验通过。")
        if validation_result.warnings:
            print("\n参数警告：")
            for warning in validation_result.warnings:
                print(f"- {warning}")

        # 3. 运行 V2 模式分析，并将模式求解 neff 接入 MMI 优化
        material_params = get_platform_materials(design_spec_dict["platform"])
        waveguide_width_um = design_spec_dict["waveguide_width_um"]
        waveguide_height_um = design_spec_dict["waveguide_height_um"]
        wavelength_um = design_spec_dict["wavelength_um"]

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
            "Mode profile path: "
            f"{mode_result['mode_profile_result']['mode_profile_path']}",
        )
        write_run_log(
            run_dir,
            "neff vs width path: "
            f"{mode_result['neff_sweep_result']['neff_vs_width_path']}",
        )
        write_run_log(run_dir, f"V2 neff used for MMI: {estimated_neff:.4f}")

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
        save_json(design_spec_dict, design_spec_path)

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

        # 4. 生成 GDS 和版图预览图
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

        # 5. 生成报告并打包本次运行结果
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

        # 刷新结果包，确保 ZIP 中包含追加工程说明后的最终报告。
        zip_path = create_result_package(output_dir=run_dir)
        write_run_log(run_dir, "Result package refreshed with final report.")

        print(f"\nAI PIC Design Platform Demo {DEMO_VERSION} finished successfully.")
        print("=" * 60)
        print(f"Run directory:       {run_dir}")
        print(f"Estimated neff:      {estimated_neff:.4f}")
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


if __name__ == "__main__":
    main()
