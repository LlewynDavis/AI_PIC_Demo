from pathlib import Path


def append_v33_engineering_section(report_path: Path) -> None:
    """在现有物理报告后追加 V3.3 结构化工程说明。"""
    section = """

## V3.3 DesignSpec 与本地 MCP 工程层

本次运行使用版本化 `PIC DesignSpec 1.0` 记录器件、平台、波长、偏振、
几何、设计目标、仿真设置和输出要求。每项设计参数同时记录
`user/default/formula/optimizer/unverified` 来源之一，避免把默认值误写为用户输入。

运行目录中的 `run_manifest.json` 与 `status.json` 记录输入解析、Schema 校验、
物理参数、模式求解、优化、BPM、overlap、版图、报告和完成状态。V3.3 还提供
本地无密钥 MCP Server/Client，用于校验 DesignSpec、估算初始 MMI 几何和检查
最近运行结果。

V3.3 只新增结构化工程接口，没有修改 V3.2 的模式求解、MMI 优化、二维标量
BPM、Gaussian 端口模式或 overlap 物理算法。当前结果仍不是严格全矢量
FDE/FDTD/FEM/EME 或完整 S 参数，也不属于流片签核级验证。
"""
    with Path(report_path).open("a", encoding="utf-8") as file:
        file.write(section)
