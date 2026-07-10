from pathlib import Path


REQUIRED_FILES = [
    "design_spec.json",
    "physical_params.json",
    "mode_result.json",
    "index_profile.png",
    "mode_profile.png",
    "neff_vs_width.png",
    "optimization_result.json",
    "wavelength_sweep_result.json",
    "wavelength_sweep.png",
    "wavelength_imbalance.png",
    "propagation_result.json",
    "field_propagation.png",
    "field_output_profile.png",
    "field_propagation_enhanced.png",
    "output_window_sensitivity.png",
    "output_window_sensitivity_result.json",
    "model_comparison.png",
    "model_comparison_result.json",
    "bpm_final_field_data.npz",
    "mode_overlap_result.json",
    "mode_overlap_comparison.png",
    "field_output_profile_with_modes.png",
    "length_sweep.png",
    "width_length_heatmap.png",
    "layout_preview.png",
    "mmi1x2_demo.gds",
    "report.md",
    "run_log.txt",
    "ai_pic_demo_results.zip",
]


def find_latest_run_dir(outputs_dir: Path) -> Path | None:
    """查找 outputs 目录下最新的 run_时间戳文件夹。"""
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


def check_run_dir(run_dir: Path) -> bool:
    """检查指定运行目录中是否包含 V3.2 所需关键输出文件。"""
    print("=" * 70)
    print("AI PIC Demo V3.2 输出完整性检查")
    print("=" * 70)
    print(f"检查目录：{run_dir}")
    print()

    all_ok = True

    for filename in REQUIRED_FILES:
        file_path = run_dir / filename

        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"[OK]      {filename:<30} {size_kb:>10.2f} KB")
        else:
            print(f"[MISSING] {filename}")
            all_ok = False

    print()
    print("=" * 70)

    if all_ok:
        print("检查结果：通过。最新运行结果文件完整。")
    else:
        print("检查结果：未通过。存在缺失文件，请查看 run_log.txt 或终端报错。")

    print("=" * 70)
    return all_ok


def main() -> None:
    outputs_dir = Path("outputs")
    latest_run_dir = find_latest_run_dir(outputs_dir)

    if latest_run_dir is None:
        print("未找到 outputs/run_时间戳 目录。")
        print("请先运行：python run_demo.py")
        return

    check_run_dir(latest_run_dir)


if __name__ == "__main__":
    main()
