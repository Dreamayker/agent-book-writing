# Agent 图书编写

本仓库保存《AI 代码评审与多 Agent 协同》第 9 章的书稿、案例资产和可复现实验工程。

## 当前书稿版本

根据作者 2026-11-05 的指示，**以 IMA 笔记本“Agent图书写作”中的最新内容为书稿基准**。阅读 [最新书稿目录](wallet-review-lab/docs/ima-sources/2026-11-05/README.md)，包含章首导语、9.1～9.12 正文、结构方案、审校报告和全书案例说明。9.6 与 9.7 的补充对照已并入主章节，独立补充文件已删除；十二节正文和导语已清理 AI 回复及创作过程说明。

每篇同时保存可阅读的 Markdown、与正文同步的富文本 JSON，以及供追溯的原始富文本。9.6、9.7 的原始富文本文件内合并保存主稿和补充材料的来源内容。表格、代码和格式属性随正文保留；笔记 ID、来源修改时间和编辑记录见 `manifest.json`。

章节清单、补充对照的合并位置及 9.1.6 已落实的修订，见 [当前书稿来源与修订关系](docs/manuscript-source.md)。

依据最新全书案例说明制定的 [电商订单工程与章节迁移规划](docs/order-case-migration-plan.md)，列出了 Java 订单工程、现有评审能力复用、十二节书稿调整和分阶段验收方案。当前为规划草案，工程与正文尚未迁移。

再次从 IMA 取稿时使用新的日期目录，避免覆盖已经编辑的正文：

```bash
node scripts/export_ima_notes.mjs YYYY-MM-DD Asia/Shanghai --latest
```

## 内容结构

- [最新书稿](wallet-review-lab/docs/ima-sources/2026-11-05/README.md)：章首导语、十二节正文及配套材料。
- [订单案例迁移规划](docs/order-case-migration-plan.md)：Java 工程与章节调整的实施顺序、证据要求和验收标准。
- [书稿来源与修订记录](docs/manuscript-source.md)：格式、合并状态与来源追溯。
- [实验工程](wallet-review-lab/README.md)：当前可运行的钱包业务及 Python 评审流程，后续按规划迁移订单案例。
- [案例与证据](wallet-review-lab/book-assets/README.md)：需求、补丁、Oracle、工具输出及人工裁决。
- [工程记录](wallet-review-lab/docs/README.md)：架构决策、实施日志、图片与实验报告。

2026-11-05 已移除 63 个旧稿、重复归档、过时规划和旧稿拆分脚本。清理前版本为 Git 提交 `a705616`；历史内容通过 Git 查看，当前目录只提供新版书稿入口。最新书稿的富文本与原始来源文件继续保留，用于格式编辑和追溯。

## 快速开始

```bash
cd wallet-review-lab
uv sync --extra dev --locked
uv run pytest
uv run ruff check .
uv run mypy app review_system evaluation
make replay-pr04
```

案例按 `case/pr-*` 分支保存。切换到某个缺陷分支后，可以按 `wallet-review-lab/book-assets/README.md` 中的命令复现失败，再切回 `main` 验证正确基线。

## 覆盖边界

现有实验工程聚焦代码评审 Agent 的证据流水线，覆盖低风险变更、金额精度、对象授权、并发双花、幂等重试、依赖漏洞和提示注入。当前业务仍为 Python 内存钱包；Java 订单工程、章节迁移和真实模型重复评测尚未完成，交付门槛见 [迁移规划](docs/order-case-migration-plan.md)。

## 安全与复现

项目不连接真实资金。`.env`、虚拟环境、缓存和本地凭证不提交；实时模型适配器只从进程环境读取密钥。教学漏洞只存在于案例分支和补丁中，不应部署到公网。
