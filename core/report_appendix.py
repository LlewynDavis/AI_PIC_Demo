from datetime import datetime
from pathlib import Path
from typing import Optional


REQUIRED_OUTPUT_FILES = [
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
    "ai_pic_demo_results.zip",
]


def _format_file_size(file_path: Path) -> str:
    if not file_path.exists():
        return "缺失"

    size_bytes = file_path.stat().st_size

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"

    size_mb = size_kb / 1024
    return f"{size_mb:.2f} MB"


def append_v15_report_appendix(
    report_path: Path,
    run_dir: Path,
    validation_text: Optional[str] = None,
    version: str = "V1.5",
    description: str = "工程稳定版：参数校验、异常处理、时间戳输出目录、运行日志",
) -> None:
    """在已有 report.md 后追加当前版本的工程运行说明。"""
    report_path = Path(report_path)
    run_dir = Path(run_dir)

    if not report_path.exists():
        raise FileNotFoundError(f"未找到报告文件：{report_path}")

    now_text = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    lines = [
        "",
        "---",
        "",
        f"## {version} 工程运行补充说明",
        "",
        "### 1. 版本信息",
        "",
        f"- 当前版本：{version}",
        f"- 版本定位：{description}",
        f"- 报告补充时间：{now_text}",
        "",
        "本版本在 V1 物理建模增强版的基础上，重点补充了工程稳定性能力。",
        "主要包括参数合法性检查、异常处理、按时间戳保存结果、运行日志记录和结果完整性检查。",
        "",
        "### 2. 参数校验结果",
        "",
    ]

    if validation_text:
        lines.extend(["```text", validation_text, "```"])
    else:
        lines.append("本次运行未写入参数校验文本。")

    lines.extend(
        [
            "",
            "### 3. 本次运行目录",
            "",
            f"```text\n{run_dir}\n```",
            "",
            "该目录保存了本次设计运行的全部输入参数、物理建模结果、优化结果、图像、GDS 版图、报告、日志和压缩包。",
            "",
            "### 4. 输出文件清单",
            "",
            "| 文件名 | 状态 | 文件大小 |",
            "|---|---:|---:|",
        ]
    )

    for filename in REQUIRED_OUTPUT_FILES:
        file_path = run_dir / filename
        status = "存在" if file_path.exists() else "缺失"
        size_text = _format_file_size(file_path)
        lines.append(f"| {filename} | {status} | {size_text} |")

    lines.extend(
        [
            "",
            "### 5. 工程意义",
            "",
            f"{version} 在工程稳定性的基础上继续增强平台的物理建模能力和可展示性。",
            "通过独立运行目录和日志文件，后续可以追踪每一次设计输入、优化结果和异常信息；",
            "通过参数校验，可以避免明显不合理的结构参数进入后续优化和版图生成流程；",
            "通过输出完整性检查，可以快速确认一次设计运行是否生成了完整交付文件。",
            "",
            f"因此，{version} 可作为后续接入严格 FDE/FEM 模式求解器的基础版本。",
            "",
        ]
    )

    with open(report_path, "a", encoding="utf-8") as file:
        file.write("\n".join(lines))
