# Agent 图书编写

本仓库保存《AI 代码评审与多 Agent 协同》第 9 章的书稿、订单案例工程、评审流程和可复现实验证据。

## 当前书稿版本

根据作者 2026-11-05 的指示，**以 IMA 笔记本“Agent图书写作”为来源基准，并按订单迁移规划更新正文**。阅读 [当前书稿目录](wallet-review-lab/docs/ima-sources/2026-11-05/README.md)：导语与 9.1～9.12 已改为优惠叠加、快照退款和 ORD 案例主线；9.6/9.7 合并的工业对照继续保留。原始 IMA 富文本作为来源记录保留。

每篇同时保存可阅读的 Markdown、与正文同步的富文本 JSON，以及供追溯的原始富文本。9.6、9.7 的原始富文本文件内合并保存主稿和补充材料的来源内容。表格、代码和格式属性随正文保留；笔记 ID、来源修改时间和编辑记录见 `manifest.json`。

章节清单、补充对照的合并位置及 9.1.6 已落实的修订，见 [当前书稿来源与修订关系](docs/manuscript-source.md)。

实施依据为 [电商订单工程与章节迁移规划](docs/order-case-migration-plan.md)，实际完成情况和剩余门槛见 [迁移状态与验证](docs/migration-status.md)。Java 订单基线、12 个案例及录制评审接入已完成；真实模型重复实验与出版审校仍单独验收。

再次从 IMA 取稿时使用新的日期目录，避免覆盖已经编辑的正文：

```bash
node scripts/export_ima_notes.mjs YYYY-MM-DD Asia/Shanghai --latest
```

## 内容结构

- [最新书稿](wallet-review-lab/docs/ima-sources/2026-11-05/README.md)：章首导语、十二节正文及配套材料。
- [订单案例迁移规划](docs/order-case-migration-plan.md)：Java 工程与章节调整的实施顺序、证据要求和验收标准。
- [书稿来源与修订记录](docs/manuscript-source.md)：格式、合并状态与来源追溯。
- [订单工程](order-review-lab/README.md)：Java/Spring Boot/MyBatis/MySQL 业务与真实集成测试。
- [订单案例与证据](order-review-lab/book-assets/README.md)：12 个独立变更、失败日志、修复与录制评审。
- [共享评审与历史钱包](wallet-review-lab/README.md)：Python 评审流程及钱包兼容实验。
- [工程记录](wallet-review-lab/docs/README.md)：架构决策、实施日志、图片与实验报告。

2026-11-05 已移除 63 个旧稿、重复归档、过时规划和旧稿拆分脚本。清理前版本为 Git 提交 `a705616`；历史内容通过 Git 查看，当前目录只提供新版书稿入口。最新书稿的富文本与原始来源文件继续保留，用于格式编辑和追溯。

## 快速开始

```bash
cd order-review-lab
./mvnw -B -ntp clean verify
python3 scripts/check_coverage.py
cd ../wallet-review-lab
uv sync --extra dev --locked
uv run pytest
uv run ruff check .
uv run mypy app review_system evaluation
uv run python -m evaluation.projects ../order-review-lab/evaluation/cases.yaml
```

订单案例按 `case/order/ORD-*` 与 `fix/order/ORD-*` 分支保存，`order-baseline-v1` / `order-stacking-v1` 指向正确基线。推荐按案例目录中的脚本在独立 worktree 重放；钱包 `case/pr-*` 分支保留历史含义。

## 覆盖边界

订单工程覆盖三类券叠加、门槛、互斥、整分分摊、快照、部分退款、拆单、授权、幂等和 MySQL 并发约束。其他业务服务以固定适配器提供；身份头与支付状态均为教学实现。录制评审只验证流程，不代表真实模型能力；worktree 也不构成恶意代码安全沙箱。

## 安全与复现

项目不连接真实资金。`.env`、虚拟环境、缓存和本地凭证不提交；实时模型适配器只从进程环境读取密钥。教学漏洞只存在于案例分支和补丁中，不应部署到公网。
