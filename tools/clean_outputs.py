import argparse
import shutil
from pathlib import Path


def directory_size_bytes(path: Path) -> int:
    """计算目录内普通文件的总大小，忽略读取失败的条目。"""
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"
    return f"{size_kb / 1024:.2f} MB"


def find_run_dirs(outputs_dir: Path) -> list[Path]:
    if not outputs_dir.exists():
        return []
    return sorted(
        (
            item
            for item in outputs_dir.iterdir()
            if item.is_dir() and item.name.startswith("run_")
        ),
        key=lambda path: path.name,
        reverse=True,
    )


def build_cleanup_plan(
    outputs_dir: Path,
    keep_count: int,
) -> tuple[list[Path], list[Path]]:
    run_dirs = find_run_dirs(outputs_dir)
    keep_dirs = run_dirs[:keep_count]
    delete_dirs = run_dirs[keep_count:]
    return keep_dirs, delete_dirs


def safe_delete_run_dir(outputs_dir: Path, run_dir: Path) -> None:
    """只允许删除 outputs 的直接子目录且名称必须以 run_ 开头。"""
    outputs_resolved = outputs_dir.resolve()
    run_resolved = run_dir.resolve()

    if run_resolved.parent != outputs_resolved:
        raise ValueError(f"拒绝删除 outputs 之外的目录：{run_dir}")
    if not run_dir.name.startswith("run_"):
        raise ValueError(f"拒绝删除非 run_ 目录：{run_dir}")
    if run_dir.is_symlink():
        raise ValueError(f"拒绝递归删除符号链接：{run_dir}")

    shutil.rmtree(run_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="安全清理 outputs/run_*，默认仅 dry-run。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="输出目录，默认：outputs",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=3,
        help="保留最近的 run 数量，默认：3",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="执行已展示的删除计划",
    )
    args = parser.parse_args()
    if args.keep < 0:
        parser.error("--keep 不能小于 0")
    return args


def main() -> None:
    args = parse_args()
    outputs_dir = args.output_dir
    if not outputs_dir.exists():
        print(f"输出目录不存在：{outputs_dir}；无需清理。")
        return
    if not outputs_dir.is_dir():
        print(f"指定路径不是目录：{outputs_dir}；无需清理。")
        return

    keep_dirs, delete_dirs = build_cleanup_plan(
        outputs_dir=outputs_dir,
        keep_count=args.keep,
    )
    total_count = len(keep_dirs) + len(delete_dirs)
    mode_text = "APPLY" if args.apply else "DRY-RUN"

    print("=" * 72)
    print(f"outputs 运行目录清理计划 [{mode_text}]")
    print("=" * 72)
    print(f"outputs 目录：{outputs_dir}")
    print(f"run 目录总数：{total_count}")
    print(f"将保留：{len(keep_dirs)}")
    print(f"将删除：{len(delete_dirs)}")

    print("\n将保留：")
    if keep_dirs:
        for path in keep_dirs:
            print(f"  [KEEP]   {path}")
    else:
        print("  （无）")

    print("\n将删除：")
    if delete_dirs:
        for path in delete_dirs:
            print(f"  [DELETE] {path}  {format_size(directory_size_bytes(path))}")
    else:
        print("  （无）")

    if not args.apply:
        print("\n当前为 dry-run，未删除任何目录。")
        print("确认清单后，使用 --apply 执行删除。")
        return

    print("\n开始删除：")
    deleted = 0
    for path in delete_dirs:
        safe_delete_run_dir(outputs_dir, path)
        deleted += 1
        print(f"  [DELETED] {path}")

    print(f"\n删除完成：{deleted} 个目录；保留：{len(keep_dirs)} 个目录。")
    print("outputs 目录、README.md 和所有非 run_ 条目均未处理。")


if __name__ == "__main__":
    main()
