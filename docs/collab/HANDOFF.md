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
