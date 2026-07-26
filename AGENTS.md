# AI_PIC_Demo 协作规则

## 适用范围

本文件适用于整个 `AI_PIC_Demo` 仓库。若子目录中出现更具体的 `AGENTS.md`，以更靠近目标文件的规则为准。

## 协作边界

- GitHub 是代码、版本、正式技术文档和已确认工程结论的事实源。
- Google Drive 是实时协作、研究记录、决策草案和任务交接层。
- ChatGPT 私人项目“光子芯片项目”负责研究、需求澄清和评审。
- Codex 负责本地实施、验证、文档落盘和 GitHub 工程写入。
- `Obsidian Notes/` 是本地完整知识库，只能按用户明确指定的范围选择性发布。

## 开始任务前

1. 阅读 `README.md`、`VERSION` 和 `docs/collab/README.md`。
2. 涉及协作状态时，继续阅读 `docs/collab/CURRENT_STATE.md`、`docs/collab/DECISIONS.md` 和 `docs/collab/HANDOFF.md`。
3. 检查当前分支、`git status` 和 `git rev-parse HEAD`。
4. 对照任务中的 `base_commit`；不一致时先报告漂移，不得静默覆盖。
5. 仅实施状态为 `APPROVED` 的 Drive 交接任务，或用户在当前任务中直接授权的变更。

## 信息分级

- `PUBLIC`：允许进入公开 GitHub。
- `INTERNAL`：仅限 Google Drive 和本地环境。
- `DRAFT`：未经确认，不得写入正式工程结论。
- `SENSITIVE`：不得由自动流程复制、上传或提交。

不得提交密钥、令牌、账号信息、私有 PDK、代工厂保密规则、未公开实验数据或私人学习记录。不得自动取消 `Obsidian Notes/` 的 Git 忽略规则。

## 修改与验证

- 保持变更范围与已批准任务一致，不顺带修改无关代码。
- 代码、模型或仿真变更必须执行与风险相称的测试，并记录命令、结果和局限性。
- 纯协作文档变更至少执行 `git diff --check`，并检查引用路径存在。
- 不得把二维标量 BPM、Gaussian 端口模式或当前 overlap 结果表述为全矢量、S 参数或流片签核级结论。
- 未运行的仿真、未发布的平台配置、未完成的外部接入必须明确标为未验证。

## 交接与完成

- Drive 任务状态使用 `DRAFT → PROPOSED → APPROVED → IN_PROGRESS → VERIFIED → CLOSED`。
- 每个工程任务必须有唯一 `handoff_id`、`base_commit`、允许范围、禁止范围和验收标准。
- Codex 完成实施后，应记录验证证据和完成 commit。
- ChatGPT 评审时应重新读取 GitHub 当前分支和 Drive 当前状态，不依赖旧聊天记忆。
