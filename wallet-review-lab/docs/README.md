# 项目记录索引

本目录保存 Wallet Review Lab 的实施过程、里程碑状态和架构决策。实验原始材料仍保存在 `book-assets/`，实验报告保存在 `evaluation/reports/`。

## 过程记录

- [execution-plan.md](execution-plan.md)：仓库内可版本化的执行基线与追踪矩阵。
- [implementation-log.md](implementation-log.md)：按时间记录实施、验证、失败及修正。
- [milestone-status.md](milestone-status.md)：当前完成度、阻塞项和下一步。

## 架构决策

- [ADR-001-wallet-transfer-case.md](decision-records/ADR-001-wallet-transfer-case.md)：选择钱包转账作为贯穿案例。
- [ADR-002-evidence-first-review.md](decision-records/ADR-002-evidence-first-review.md)：采用证据优先的评审与仲裁机制。
- [ADR-003-model-strategy.md](decision-records/ADR-003-model-strategy.md)：模型数量、角色复用和评测策略。

## 记录规则

- Git 提交记录“代码和文档发生了什么变化”。
- 实施日志记录“为什么执行、结果如何、失败后怎样处理”。
- ADR 记录“为什么选择当前方案，以及接受了什么代价”。
- 实验报告记录“在明确版本和条件下测到了什么”。
- 录制输出不得写成实时模型结果；厂商数据不得写成本项目实测数据。
