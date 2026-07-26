# 协作决策

## DEC-001：协作架构

- status：`APPROVED`
- decision：GitHub 为工程事实源；Google Drive 为实时协作与交接层；ChatGPT 为研究和评审端；Codex 为实施和验证端；Obsidian 为本地完整知识库，仅选择性发布。

## DEC-002：GitHub 写入责任

- status：`APPROVED`
- decision：Codex 是 GitHub 工程文件的主要写入端。ChatGPT 不通过 GitHub 应用直接推送代码，而是通过 Drive 提交研究结论、评审意见和结构化交接。

## DEC-003：信息分级

- status：`APPROVED`
- decision：
  - `PUBLIC` 可进入公开 GitHub。
  - `INTERNAL` 仅限 Drive 与本地。
  - `DRAFT` 未确认不得进入正式文档。
  - `SENSITIVE` 不得由自动流程复制。

## DEC-004：知识库发布

- status：`APPROVED`
- decision：不自动取消 `Obsidian Notes/` 的 Git 忽略规则。只有用户明确指定的内容可以整理为公开工程知识。

## DEC-005：冲突处理

- status：`APPROVED`
- decision：所有涉及代码的交接必须携带 `base_commit`。Codex 发现当前 commit 不一致时停止写入并报告漂移；Drive 更新使用最新文档修订并在写后读回。
