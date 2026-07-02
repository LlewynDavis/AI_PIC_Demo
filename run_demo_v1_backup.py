from pathlib import Path
import json
import traceback

from core.spec_parser import parse_design_request
from core.material_database import get_material_database
from core.mode_solver import estimate_effective_index
from core.optimizer import run_width_length_optimization
from core.report_generator import generate_report
from core.package_generator import package_results

from core.validation import validate_design_spec, validation_result_to_text
from core.run_manager import (
    create_run_directory,
    init_run_log,
    write_run_log,
    write_success_log,
    write_error_log,
    get_output_path,
)

from layout.gds_generator import generate_mmi_gds


DEMO_VERSION = "V1.5"
DEMO_DESCRIPTION = "工程稳定版：参数校验、异常处理、时间戳输出目录、运行日志"


def save_json(data, path: Path):
    """
    保存 JSON 文件。
    """

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def spec_to_dict(spec):
    """
    兼容 pydantic 对象、dataclass 对象和普通 dict。
    """

    if isinstance(spec, dict):
        return spec

    if hasattr(spec, "model_dump"):
        return spec.model_dump()

    if hasattr(spec, "dict"):
        return spec.dict()

    return spec.__dict__


def main():
    run_dir = create_run_directory("outputs")

    init_run_log(
        run_dir=run_dir,
        version=DEMO_VERSION,
        description=DEMO_DESCRIPTION,
    )

    write_run_log(run_dir, "Demo started.")
    write_run_log(run_dir, f"Run directory created: {run_dir}")

    try:
        user_requirement = "请帮我设计一个 1550 nm、SOI 平台、50:50 分光的 1×2 MMI 分束器。"

        write_run_log(run_dir, "Natural language requirement received.")
        write_run_log(run_dir, user_requirement)

        # 1. 自然语言解析
        design_spec = parse_design_request(user_requirement)
        design_spec_dict = spec_to_dict(design_spec)

        design_spec_path = get_output_path(run_dir, "design_spec.json")
        save_json(design_spec_dict, design_spec_path)

        write_run_log(run_dir, "Design specification parsed.")
        write_run_log(run_dir, f"Saved design_spec.json: {design_spec_path}")

        # 2. 参数合法性检查
        validation_result = validate_design_spec(design_spec)
        validation_text = validation_result_to_text(validation_result)

        write_run_log(run_dir, "Validation result:")
        write_run_log(run_dir, validation_text)

        if not validation_result.is_valid:
            print("\n参数校验未通过，程序已停止。")
            print(validation_text)
            write_run_log(run_dir, "Demo stopped because validation failed.")
            return

        print("\n参数校验通过。")
        if validation_result.warnings:
            print("\n参数警告：")
            for item in validation_result.warnings:
                print(f"- {item}")

        # 3. 读取材料参数
        material_db = get_material_database()
        platform = design_spec_dict.get("platform", "SOI")
        material_params = material_db.get(platform, material_db.get("SOI"))

        write_run_log(run_dir, f"Material platform selected: {platform}")

        # 4. 有效折射率估算
        waveguide_width_um = design_spec_dict.get("waveguide_width_um", 0.5)
        waveguide_height_um = design_spec_dict.get("waveguide_height_um", 0.22)
        wavelength_um = design_spec_dict.get("wavelength_um", 1.55)

        estimated_neff = estimate_effective_index(
            core_index=material_params["core_index"],
            cladding_index=material_params["cladding_index"],
            waveguide_width_um=waveguide_width_um,
            waveguide_height_um=waveguide_height_um,
            wavelength_um=wavelength_um,
        )

        design_spec_dict["neff"] = estimated_neff

        physical_params = {
            "platform": platform,
            "core_material": material_params.get("core_material", "Si"),
            "cladding_material": material_params.get("cladding_material", "SiO2"),
            "core_index": material_params["core_index"],
            "cladding_index": material_params["cladding_index"],
            "waveguide_width_um": waveguide_width_um,
            "waveguide_height_um": waveguide_height_um,
            "wavelength_um": wavelength_um,
            "estimated_neff": estimated_neff,
            "neff_used": estimated_neff,
            "mode_solver_type": "simplified_effective_index_estimator",
        }

        physical_params_path = get_output_path(run_dir, "physical_params.json")
        save_json(physical_params, physical_params_path)

        write_run_log(run_dir, f"Estimated neff: {estimated_neff:.4f}")
        write_run_log(run_dir, f"Saved physical_params.json: {physical_params_path}")

        # 5. 二维宽度-长度联合优化
        optimization_result = run_width_length_optimization(
            design_spec=design_spec_dict,
            output_dir=run_dir,
        )

        optimization_result_path = get_output_path(run_dir, "optimization_result.json")
        save_json(optimization_result, optimization_result_path)

        write_run_log(run_dir, "Width-length optimization finished.")
        write_run_log(run_dir, f"Saved optimization_result.json: {optimization_result_path}")

        best_width_um = optimization_result["best_width_um"]
        best_length_um = optimization_result["best_length_um"]

        # 6. 生成 GDS 和版图预览图
        gds_path = get_output_path(run_dir, "mmi1x2_demo.gds")
        layout_preview_path = get_output_path(run_dir, "layout_preview.png")

        generate_mmi_gds(
            width_um=best_width_um,
            length_um=best_length_um,
            waveguide_width_um=waveguide_width_um,
            gds_path=gds_path,
            preview_path=layout_preview_path,
        )

        write_run_log(run_dir, f"GDS generated: {gds_path}")
        write_run_log(run_dir, f"Layout preview generated: {layout_preview_path}")

        # 7. 生成中文报告
        report_path = get_output_path(run_dir, "report.md")

        generate_report(
            design_spec=design_spec_dict,
            physical_params=physical_params,
            optimization_result=optimization_result,
            output_path=report_path,
            version=DEMO_VERSION,
        )

        write_run_log(run_dir, f"Report generated: {report_path}")

        # 8. 打包本次运行结果
        zip_path = get_output_path(run_dir, "ai_pic_demo_results.zip")

        package_results(
            output_dir=run_dir,
            zip_path=zip_path,
        )

        write_run_log(run_dir, f"Result package generated: {zip_path}")

        # 9. 终端输出结果
        print("\nAI PIC Design Platform Demo V1.5 finished successfully.")
        print("=" * 60)
        print(f"Run directory:       {run_dir}")
        print(f"Estimated neff:      {estimated_neff:.4f}")
        print(f"Best MMI width:      {best_width_um:.3f} μm")
        print(f"Best MMI length:     {best_length_um:.3f} μm")
        print(f"Output port 1:       {optimization_result['output_port_1']:.4f}")
        print(f"Output port 2:       {optimization_result['output_port_2']:.4f}")
        print(f"Insertion loss:      {optimization_result['insertion_loss_db']:.3f} dB")
        print(f"Imbalance:           {optimization_result['imbalance_db']:.3f} dB")
        print(f"Best score:          {optimization_result['best_score']:.6f}")
        print("=" * 60)
        print(f"Report:              {report_path}")
        print(f"GDS:                 {gds_path}")
        print(f"ZIP:                 {zip_path}")

        write_success_log(run_dir)

    except Exception as e:
        print("\n程序运行失败，错误信息如下：")
        print(type(e).__name__)
        print(str(e))

        error_text = traceback.format_exc()
        print("\n完整错误追踪：")
        print(error_text)

        write_error_log(run_dir, e)
        write_run_log(run_dir, "Traceback:")
        write_run_log(run_dir, error_text)


if __name__ == "__main__":
    main()