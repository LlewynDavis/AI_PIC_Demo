from datetime import datetime
from pathlib import Path
from typing import Optional


def create_run_directory(base_output_dir: str = "outputs") -> Path:
    """
    创建带时间戳的运行结果目录。

    示例：
    outputs/run_20260702_143025

    这样可以避免每次运行覆盖旧结果，也方便后续对比不同参数下的设计结果。
    """

    base_dir = Path(base_output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_{timestamp}"

    counter = 1
    while run_dir.exists():
        run_dir = base_dir / f"run_{timestamp}_{counter}"
        counter += 1

    run_dir.mkdir(parents=True, exist_ok=True)

    return run_dir


def write_run_log(
    run_dir: Path,
    message: str,
    mode: str = "a",
) -> None:
    """
    向 run_log.txt 写入日志信息。
    """

    log_path = run_dir / "run_log.txt"
    time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, mode, encoding="utf-8") as f:
        f.write(f"[{time_text}] {message}\n")


def init_run_log(
    run_dir: Path,
    version: str = "V1.5",
    description: Optional[str] = None,
) -> None:
    """
    初始化运行日志。
    """

    lines = []
    lines.append("=" * 60)
    lines.append(f"AI PIC Design Platform Demo {version} Run Log")
    lines.append("=" * 60)

    if description:
        lines.append(description)

    lines.append(f"Run directory: {run_dir}")
    lines.append("")

    log_path = run_dir / "run_log.txt"

    with open(log_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def write_success_log(run_dir: Path) -> None:
    """
    记录运行成功状态。
    """

    write_run_log(run_dir, "Status: SUCCESS")


def write_error_log(run_dir: Path, error: Exception) -> None:
    """
    记录运行失败状态和错误信息。
    """

    write_run_log(run_dir, "Status: FAILED")
    write_run_log(run_dir, f"Error type: {type(error).__name__}")
    write_run_log(run_dir, f"Error message: {str(error)}")


def get_output_path(run_dir: Path, filename: str) -> Path:
    """
    统一生成输出文件路径。

    示例：
    get_output_path(run_dir, "report.md")
    """

    return run_dir / filename