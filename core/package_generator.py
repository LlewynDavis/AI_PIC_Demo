from pathlib import Path
from zipfile import ZipFile


def create_result_package(output_dir: Path):
    """
    将本次 demo 生成的结果文件打包成 zip。

    便于汇报、备份或发送给老师。
    """
    package_path = output_dir / "ai_pic_demo_results.zip"

    files_to_package = [
        "design_spec.json",
        "physical_params.json",
        "mode_result.json",
        "mode_profile.png",
        "neff_vs_width.png",
        "optimization_result.json",
        "length_sweep.png",
        "width_length_heatmap.png",
        "layout_preview.png",
        "mmi1x2_demo.gds",
        "report.md",
        "run_log.txt",
    ]

    with ZipFile(package_path, "w") as zip_file:
        for file_name in files_to_package:
            file_path = output_dir / file_name
            if file_path.exists():
                zip_file.write(file_path, arcname=file_name)

    return package_path
