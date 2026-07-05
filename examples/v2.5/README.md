# V2.5 代表性结果

此目录用于保存 AI_PIC_Demo V2.5 的代表性结果。V2.5 是二维标量有限差分模式求解增强版，典型展示内容包括：

- `index_profile.png`：SOI 波导折射率截面
- `mode_profile.png`：二维标量模式场
- `neff_vs_width.png`：有效折射率随波导宽度变化
- `length_sweep.png`：最优宽度下的 MMI 长度扫描
- `width_length_heatmap.png`：MMI 宽度—长度二维优化热力图
- `wavelength_sweep.png`：输出功率随波长变化
- `wavelength_imbalance.png`：分光不均衡随波长变化
- `layout_preview.png`：版图预览图
- `mmi1x2_demo.gds`：GDS 版图文件
- `report.md`：中文设计报告

请从已验证的 `outputs/run_*` 中人工挑选少量结果，不要复制完整运行历史、缓存、密钥或大型 ZIP。

> 模型说明：V2.5 使用二维标量有限差分模式求解；MMI 响应仍采用轻量 surrogate model。当前版本不是严格的全矢量 FDE，也不是 FEM、EME 或 FDTD 电磁求解器。
