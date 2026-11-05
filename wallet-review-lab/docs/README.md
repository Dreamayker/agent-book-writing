# 项目记录索引

本目录保存 Wallet Review Lab 的实施过程、里程碑状态和架构决策。实验原始材料仍保存在 `book-assets/`，实验报告保存在 `evaluation/reports/`。

## 当前书稿来源

作者于 2026-11-05 指定 IMA 笔记本“Agent图书写作”为最新版本。阅读 [最新书稿目录](ima-sources/2026-11-05/README.md)。9.6、9.7 的补充对照已并入对应主章节，独立补充文件已删除；十二节正文及导语已去除 AI 回复和创作过程说明，Markdown 与富文本正文同步保留格式。下列合并稿和拆分稿为此前仓库版本；后续以最新目录中的正文为基准。

## 过程记录

- [电商订单工程与章节迁移规划](../../docs/order-case-migration-plan.md)：依据最新案例说明制定的工程及第 9 章调整方案；当前为规划，尚未实施迁移。
- [IMA 2026-10-20 文章归档](ima-sources/2026-10-20/README.md)：当天新建的 20 篇写作材料，保存 Markdown 和原始富文本 JSON。
- [chapter-09/README.md](chapter-09/README.md)：第 9 章按概述、9.1～9.10 和独立项目案例拆分后的阅读入口。
- [chapter-09-rewrite-draft.md](chapter-09-rewrite-draft.md)：第 9 章合并稿与拆分稿内容来源。
- [execution-plan.md](execution-plan.md)：仓库内可版本化的执行基线与追踪矩阵。
- [implementation-log.md](implementation-log.md)：按时间记录实施、验证、失败及修正。
- [milestone-status.md](milestone-status.md)：当前完成度、阻塞项和下一步。

## 架构决策

- [ADR-001-wallet-transfer-case.md](decision-records/ADR-001-wallet-transfer-case.md)：选择钱包转账作为贯穿案例。
- [ADR-002-evidence-first-review.md](decision-records/ADR-002-evidence-first-review.md)：采用证据优先的评审与仲裁机制。
- [ADR-003-model-strategy.md](decision-records/ADR-003-model-strategy.md)：模型数量、角色复用和评测策略。
- [ADR-004-order-case-migration.md](decision-records/ADR-004-order-case-migration.md)：提议新增 Java 订单案例工程，复用评审能力，分阶段迁移新版书稿。

## 记录规则

- Git 提交记录“代码和文档发生了什么变化”。
- 实施日志记录“为什么执行、结果如何、失败后怎样处理”。
- ADR 记录“为什么选择当前方案，以及接受了什么代价”。
- 实验报告记录“在明确版本和条件下测到了什么”。
- 录制输出不得写成实时模型结果；厂商数据不得写成本项目实测数据。
