# AI_PIC_Demo 版本变更记录

本文档按照时间倒序记录主要版本变化。历史代码通过 Git tag 和 GitHub Release 保存，主分支不维护完整源码副本。

## V3.3_designspec_mcp_foundation — DesignSpec 与本地 MCP 基础版

### 版本定位

在保持 V3.2 物理算法和基准结果不变的前提下，为自然语言需求、物理流程和外部工具调用建立统一、可验证、可追踪的结构化接口。

### 新增功能

- 新增版本化 PIC DesignSpec 1.0，覆盖器件、平台、波长、偏振、几何、目标、仿真和输出。
- 所有设计参数记录 `user/default/formula/optimizer/unverified` 来源。
- 新增 Pydantic 类型、单位、物理范围和求解器校验。
- 新增 `needs_clarification` 状态，含糊或冲突需求不再静默补齐关键参数。
- 新增 `run_manifest.json`、`status.json` 和 IE/SV/PH/MODE/OPT/BPM/OVL/LAY/REP/SUCCESS 阶段码。
- 新增最小本地 MCP Server/Client 与三个结构化工具。
- 新增 30 条自然语言需求 Benchmark、自动执行脚本和测试。
- 新增 JSON/YAML DesignSpec 示例、版本说明和公开路线文档。

### 局限性或备注

- V3.3 是工程接口升级，不是电磁求解精度升级。
- 没有接入外部密钥型 LLM、RAG、多 Agent 或付费仿真器。
- 二维标量 BPM、Gaussian 模式和 overlap-based power 仍不是严格全矢量 S 参数。

## V3.2_port_mode_overlap — 端口模式重叠积分版

### 版本定位

V3.2 在 V3.1 传播仿真校准基础上，增加简化 Gaussian 输出端口模式，并将二维标量 BPM 输出场投影到端口模式上，用于获得比窗口积分更合理、更具模式意识的端口功率估计。

### 新增功能

- 新增 `core/mode_overlap.py`。
- 新增 `bpm_final_field_data.npz`，保存最终输出端复数场和强度。
- 新增 `mode_overlap_result.json`。
- 新增 `mode_overlap_comparison.png`。
- 新增 `field_output_profile_with_modes.png`。
- 网页新增 V3.2 端口模式重叠展示与下载区。
- 报告新增 V3.2 端口模式重叠积分分析。
- 完整性检查和结果包加入 V3.2 输出。

### 局限性或备注

- 端口模式仍是 Gaussian 近似。
- BPM 场仍是二维标量近似。
- Overlap-based power 不是严格全矢量 eigenmode S 参数提取。
- 后续可接入真实波导本征模式或外部高保真仿真器。

## V3.1_propagation_calibration — 传播仿真校准与模型对比版

### 版本定位

V3.1 在 V3.0 二维标量 BPM 传播仿真基础上，增加输出窗口敏感性分析、增强传播图和 surrogate/BPM 模型对比，用于提高传播结果的可解释性和工程可信度。

### 新增功能

- 新增输出窗口宽度敏感性分析。
- 新增 `output_window_sensitivity_result.json`。
- 新增 `output_window_sensitivity.png`。
- 新增 `field_propagation_enhanced.png`。
- 新增 `core/model_comparison.py`。
- 新增 `model_comparison_result.json`。
- 新增 `model_comparison.png`。
- 新增 `core/v31_report_appendix.py`，在报告中追加校准分析。
- 网页新增 V3.1 展示与下载区。
- 完整性检查和结果包加入 V3.1 输出。

### 修复内容

- 为 V3.0 兼容字段 `insertion_loss_db` 增加语义更准确的 `window_based_insertion_loss_db`。
- 通过多窗口积分解释 V3.0 插损偏大的窗口依赖来源。
- 明确 surrogate 与 BPM 结果属于不同物理层级，避免将趋势对比解释为严格数值验证。

### 局限性或备注

- V3.1 不改变 V3.0 的 BPM 基本物理模型。
- 输出功率仍然是窗口积分估计，不是严格模式重叠积分。
- `window_based_insertion_loss_db` 不是严格器件插入损耗。
- 当前版本没有执行严格全矢量 S 参数提取。

## V3.0_scalar_bpm_propagation — MMI 二维标量光场传播仿真版

### 版本定位

V3.0 在 V2.6 工程稳定版本基础上，新增 MMI 内部光场传播可视化和输出端口功率估算，并保留原有 surrogate 优化模型作为前级设计流程。

### 新增功能

- 新增 `core/propagation_solver.py`。
- 新增二维标量 split-step Fourier BPM 传播仿真。
- 生成 `field_propagation.png`。
- 生成 `field_output_profile.png`。
- 生成 `propagation_result.json`。
- 网页端展示并下载 V3.0 传播仿真结果。
- 新增 `core/v30_report_appendix.py`，在报告中追加传播分析。
- 输出完整性检查和 ZIP 结果包加入 V3.0 文件。

### 修复内容

- 将 MMI 光场传播验证接入命令行和 Streamlit 完整流程。
- 为传播仿真增加独立异常隔离，BPM 失败时不阻断 V2.6 基线流程。
- 更新报告中的模式和传播模型边界说明。

### 局限性或备注

- 该传播仿真是二维标量 BPM 近似。
- 不是严格全矢量 FDTD/FEM/EME。
- 输出功率由简单端口窗口积分估算。
- 后续可升级为更严格的传播求解器或接入外部仿真工具。

## V2.6 — 工程清理与 GitHub 同步准备版

### 版本定位

在 V2.5 稳定算法基础上完成工程结构整理、文档封版、输出管理和 GitHub 版本管理规范化。

### 新增功能

- 新增 `VERSION`，统一版本标识为 `V2.6_engineering_cleanup`。
- 新增 `tools/clean_outputs.py`，支持 dry-run、保留数量设置和显式 `--apply`。
- 新增或完善 `outputs/README.md`、`examples/README.md` 和 `examples/v2.5/README.md`。
- 新增 `docs/versions/` 历史版本说明。
- 明确 `main` 为最新稳定版、`dev` 为下一版本开发分支。

### 修复内容

- 完善 `.gitignore`，排除虚拟环境、缓存、密钥、临时文件和本地运行结果。
- 清理历史源码副本、旧的已跟踪输出产物和分发 ZIP。
- 统一 README、CHANGELOG、版本说明和模型边界表述。
- 历史版本改用 Git tag、GitHub Release、CHANGELOG 和版本文档管理。

### 局限性或备注

本版本不修改核心物理算法。模式求解仍为二维标量有限差分近似，MMI 响应仍使用轻量 surrogate model。

## V2.5 — 二维标量有限差分模式求解版

### 版本定位

将波导模式分析升级为二维标量有限差分求解，并作为后续开发的稳定算法基线。

### 新增功能

- 实现 `solve_scalar_fd_mode()`。
- 根据 SOI 波导截面构建二维折射率分布 `n(x,y)`。
- 离散标量 Helmholtz 方程并求解本征值 `β²`。
- 提取 `neff = β / k0`，生成有限差分模式场和 `neff_vs_width`。
- 在 `mode_result.json` 中记录传播常数、网格和步长信息。
- 将有限差分 `neff` 接入 MMI 优化和波长扫描。

### 修复内容

- 修正波长扫描使用旧经验 `neff`、与模式求解结果不一致的问题。
- 统一命令行、网页、报告和结果包中的 V2.5 模式结果。

### 局限性或备注

当前仍是二维标量近似，不是严格全矢量 FDE/FEM/EME/FDTD；MMI 区域尚未进行真实传播仿真。

## V2.3 — 波长扫描与带宽趋势分析版

### 版本定位

在固定最优 MMI 参数下分析波长变化对输出功率和分光性能的影响。

### 新增功能

- 新增 `core/wavelength_sweep.py`。
- 扫描 1.50–1.60 μm 波长范围。
- 生成波长扫描、分光不均衡曲线及结构化结果。
- 在报告和网页中新增波长趋势展示。

### 修复内容

- 将带宽趋势分析纳入统一运行、报告和打包流程。

### 局限性或备注

初始版本使用旧 `neff` 经验公式，与后续有限差分结果存在不一致；该问题在 V2.5 中修正。

## V2.1 — Streamlit 网页展示增强版

### 版本定位

重点提升网页端结果展示、最新运行加载和文件下载能力。

### 新增功能

- 新增 `core/v2_web_utils.py`。
- 网页展示模式场、`neff_vs_width`、模式指标和 MMI 优化结果。
- 展示长度扫描、二维热力图和版图预览。
- 支持报告、GDS、ZIP 和模式结果下载。

### 修复内容

- 完善网页端最新运行结果加载和缺失文件提示。

### 局限性或备注

主要增强展示层，底层物理模型与 V2 基本一致，尚未加入波长扫描。

## V2 — 模式求解版

### 版本定位

开始将波导模式分析结果接入 MMI 优化流程。

### 新增功能

- 增强 `core/mode_solver.py`。
- 生成近似 TE0 模式场、`neff_vs_width` 和结构化模式结果。
- 将模式模块输出的 `neff` 接入 MMI 二维优化。
- 在报告中增加模式分析章节。

### 修复内容

- 统一模式输出文件和报告引用关系。

### 局限性或备注

模式场仍是近似模型，不是严格有限差分或全矢量模式求解；MMI 传播未真实仿真。

## V1.5 — 工程稳定版

### 版本定位

增强运行隔离、参数校验、日志记录和输出完整性检查。

### 新增功能

- 新增参数合法性检查。
- 新增时间戳运行目录管理和 `run_log.txt`。
- 新增 `tools/check_latest_run.py` 结果完整性检查。
- 完善报告附录和结果打包。

### 修复内容

- 降低多次运行相互覆盖结果的风险。
- 增强异常提示和结果追踪能力。

### 局限性或备注

物理模型仍以简化有效折射率估算为主，尚未真正求解波导模式。

## V1 — 物理建模增强版

### 版本定位

形成 SOI 平台 MMI 分束器的材料、优化、版图、网页和报告自动化流程。

### 新增功能

- 新增 SOI 材料参数库和简化 `neff` 估算。
- 新增 MMI 宽度—长度二维扫描和优化热力图。
- 根据最优参数生成 GDS 和版图预览。
- 支持 Streamlit 展示、中文报告和结果打包。

### 修复内容

- 将分散的参数、优化、版图和报告步骤串联为统一流程。

### 局限性或备注

`neff` 仍是简化估算，MMI 响应采用 surrogate model，尚未引入模式场求解。
