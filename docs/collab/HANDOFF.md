# 任务交接协议

实时任务保存在私人 Google Drive 的 `AI_PIC 协作｜任务交接`。本文件只保存公开协议和模板。

## 状态机

`DRAFT → PROPOSED → APPROVED → IN_PROGRESS → VERIFIED → CLOSED`

状态含义：

- `DRAFT`：尚未形成完整任务。
- `PROPOSED`：ChatGPT 或 Codex 已提出，等待用户确认。
- `APPROVED`：用户已确认，可以实施。
- `IN_PROGRESS`：Codex 正在实施。
- `VERIFIED`：实施端已提供验证证据。
- `CLOSED`：ChatGPT 或用户完成最终评审。

## 必填字段

```text
handoff_id: PIC-HANDOFF-NNN
status:
source:
target:
base_commit:
request:
evidence:
allowed_scope:
forbidden_scope:
acceptance:
verification:
completion_commit:
```

## 冲突规则

1. `base_commit` 与 GitHub 当前目标分支不一致时，不得静默继续。
2. 同一任务只能有一个实施端。
3. ChatGPT 建议默认是 `PROPOSED`，不得自动提升为 `APPROVED`。
4. 任务范围涉及 `INTERNAL` 或 `SENSITIVE` 内容时，不得把原文复制到公开 GitHub。
5. 完成状态必须由读回结果、测试输出或可核验 commit 支持。

## 自动路由规则

1. 自动协调器只路由最新、完整、未处理的来源消息；历史对话初始化时只登记游标，不批量重放。
2. 优先复用与主题匹配的现有 Codex 对话；无法可靠匹配时发送到项目协调入口。
3. 目标对话正在执行冲突任务时不得重复派发，应记录等待状态并在下一轮检查。
4. `APPROVED` 任务可在核对 `base_commit` 后自动进入 `IN_PROGRESS`；`PROPOSED` 任务只同步和评估。
5. Codex 写回 `VERIFIED` 证据后，协调器将摘要送回对应 ChatGPT 对话；ChatGPT 读回事实源后才能关闭任务。
