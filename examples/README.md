# examples

此目录用于保存关键版本的代表性展示结果。

这里不保存所有运行结果，只保存适合汇报、展示、对比和复现的少量结果。普通的 `outputs/run_*` 运行目录不应直接复制进来。

V2.5 的典型结果可以放在 `examples/v2.5/`，例如：

- `report.md`
- `mode_profile.png`
- `index_profile.png`
- `neff_vs_width.png`
- `wavelength_sweep.png`
- `wavelength_imbalance.png`
- `width_length_heatmap.png`
- `layout_preview.png`

V3.0 的典型传播仿真结果可以放在 `examples/v3.0/`。该目录应只保存少量传播结果、图像和报告说明。

V3.1 的窗口敏感性和模型对比结果可以放在 `examples/v3.1/`，同样只保留适合汇报与复现的代表性文件。

V3.2 的端口模式重叠积分结果可以放在 `examples/v3.2/`，只保存少量模式重叠图、结构化结果和报告。

历史完整代码不放在 `examples/`，应通过 Git tag 或 GitHub Release 查看。

示例文件应尽量小而清晰。请勿堆积大量 ZIP、临时文件、敏感配置或缓存。
