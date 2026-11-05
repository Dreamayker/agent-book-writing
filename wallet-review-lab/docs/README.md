# 项目记录索引

本目录保存最新书稿、架构决策、实施日志和图片。实验原始材料见 [案例目录](../book-assets/README.md)，实验报告见下方链接。

## 当前书稿来源

作者于 2026-11-05 指定 IMA 笔记本“Agent图书写作”为最新版本。阅读 [最新书稿目录](ima-sources/2026-11-05/README.md)。9.6、9.7 的补充对照已并入对应主章节，独立补充文件已删除；十二节正文及导语已去除 AI 回复和创作过程说明，Markdown 与富文本正文同步保留格式。来源与修订细节见 [版本说明](../../docs/manuscript-source.md)。

## 过程记录

- [电商订单工程与章节迁移规划](../../docs/order-case-migration-plan.md)：依据最新案例说明制定的工程及第 9 章调整方案；当前为规划，尚未实施迁移。
- [implementation-log.md](implementation-log.md)：历史实施、验证、失败及修正记录。
- [figures/README.md](figures/README.md)：现有钱包案例的图片源码及渲染方式。

旧合并稿、拆分稿、重复归档及过时规划已于 2026-11-05 清理；历史版本见 Git 提交 `a705616`。当前实施顺序与验收统一以订单案例迁移规划为准。

## 已有实验记录

- [PR-04 首次回放](../evaluation/reports/pr04-first-run.md)。
- [录制案例集首次评测](../evaluation/reports/recorded-suite-first-run.md)。
- [Semgrep 首次运行](../evaluation/reports/semgrep-first-run.md)。
- [历史事实核验](../references/README.md)：旧稿外部声明的处置记录。

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
