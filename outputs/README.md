# outputs

此目录用于保存 AI_PIC_Demo 的本地运行结果，包括结构化参数、模式求解结果、优化图、GDS 版图、中文报告和打包文件。

每次运行会创建 `outputs/run_时间戳/` 目录。`run_*` 目录通常不提交到 GitHub。

如需保留重要展示结果，请人工筛选后复制到 `examples/` 对应的版本目录。

可在项目根目录预览或执行历史结果清理：

```powershell
python tools/clean_outputs.py
python tools/clean_outputs.py --keep 3
python tools/clean_outputs.py --keep 3 --apply
```

前两条命令只显示清理计划；只有传入 `--apply` 才会实际删除旧目录。脚本不会删除 `outputs/` 目录本身或本说明文件。
