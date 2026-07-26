# AI_PIC 协作入口

本目录定义 `AI_PIC_Demo`、私人 ChatGPT 项目“光子芯片项目”和 Google Drive 协作层之间的工作协议。

## 事实源

| 内容 | 事实源 | 主要写入端 |
| --- | --- | --- |
| 代码、版本、正式技术文档 | GitHub `main` | Codex |
| 实时状态、任务交接、研究记录 | Google Drive `AI_PIC_Collaboration` | ChatGPT、Codex |
| 项目讨论和评审过程 | ChatGPT 私人项目“光子芯片项目” | 用户、ChatGPT |
| 完整个人学习知识库 | 本地 `Obsidian Notes/` | 用户、经授权的 Codex |

## 本目录文件

- `CURRENT_STATE.md`：公开、稳定的项目状态和能力边界。
- `DECISIONS.md`：已经确认并允许公开的协作决策。
- `HANDOFF.md`：任务状态机和交接格式；实时任务内容保存在私人 Drive。
- `CHATGPT_PROJECT_INSTRUCTIONS.md`：应配置到“光子芯片项目”的项目指令。

## Google Drive 协作层

私人 Drive 文件夹名称为 `AI_PIC_Collaboration`，包含：

- `AI_PIC 协作｜当前状态`
- `AI_PIC 协作｜决策记录`
- `AI_PIC 协作｜任务交接`
- `AI_PIC 协作｜研究资料索引`

Drive 链接和文件 ID 不写入公开仓库。ChatGPT 应通过已连接的 Google Drive 应用访问该文件夹。

## 同步协议

1. ChatGPT 先读取 Drive 的“当前状态”“决策记录”和“任务交接”。
2. 涉及代码时，再读取 GitHub `main` 的 `README.md`、`VERSION`、`AGENTS.md` 和本目录。
3. ChatGPT 将建议写为 `PROPOSED`；用户确认后改为 `APPROVED`。
4. Codex 核对 `base_commit` 后实施，并记录验证证据和完成 commit。
5. ChatGPT 重新读取 GitHub 与 Drive，评审通过后将任务置为 `CLOSED`。

Google Drive 是按需读取的协作层，不应假设聊天会自动获得最新内容。每次关键操作都必须重新读取目标文档。
