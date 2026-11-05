# Agent 图书编写

本仓库保存《AI 代码评审与多 Agent 协同》第 9 章的书稿、案例资产和可复现实验工程。

## 当前书稿版本

根据作者 2026-11-05 的指示，**以 IMA 笔记本“Agent图书写作”中的最新内容为书稿基准**。阅读 [最新书稿目录](wallet-review-lab/docs/ima-sources/2026-11-05/README.md)，包含章首导语、9.1～9.12 正文、结构方案、审校报告和全书案例说明。9.6 与 9.7 的补充对照已并入主章节，独立补充文件已删除；十二节正文和导语已清理 AI 回复及创作过程说明。

每篇同时保存可阅读的 Markdown、与正文同步的富文本 JSON，以及供追溯的原始富文本。9.6、9.7 的原始富文本文件内合并保存主稿和补充材料的来源内容。表格、代码和格式属性随正文保留；笔记 ID、来源修改时间和编辑记录见 `manifest.json`。

章节清单、补充对照的合并位置及 9.1.6 已落实的修订，见 [当前书稿来源与修订关系](docs/manuscript-source.md)。

`wallet-review-lab/docs/chapter-09-rewrite-draft.md` 与旧 `chapter-09/` 拆分稿是此前的仓库版本，尚未按 IMA 的 12 节结构整合。后续编辑和审校以最新书稿目录中的主章节为依据。再次从 IMA 取稿时使用新的日期目录，避免覆盖已经编辑的正文：

```bash
node scripts/export_ima_notes.mjs YYYY-MM-DD Asia/Shanghai --latest
```

## 内容结构

- `第9章 AI 代码评审与多 Agent 协同.md`：原始章节稿。
- `第9章完善与案例落地方案.md`：章节重构与案例实施方案。
- `wallet-review-lab/`：可安装、可测试、可回放的实验工程。
- `wallet-review-lab/docs/chapter-09/`：此前仓库稿按概述、9.1～9.10 和项目案例拆分后的历史文档目录。
- [IMA 今日文章归档](wallet-review-lab/docs/ima-sources/2026-10-20/README.md)：2026-10-20 新建的 20 篇写作材料，含 Markdown 和原始富文本 JSON。
- `docs/chapter-09-expansion-plan.md`：按分子章节拆解的扩写蓝图。
- `docs/project-readiness-audit.md`：项目覆盖范围、出版缺口和整改记录。

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

本项目聚焦代码评审 Agent 的证据流水线，覆盖低风险变更、金额精度、对象授权、并发双花、幂等重试、依赖漏洞和提示注入。它不等同于完整的软件安全或生产支付系统，也不覆盖所有数据库、网络、供应链和分布式系统场景。出版状态、真实模型实验和案例截图等未完成项见项目审查记录。

## 安全与复现

项目不连接真实资金。`.env`、虚拟环境、缓存和本地凭证不提交；实时模型适配器只从进程环境读取密钥。教学漏洞只存在于案例分支和补丁中，不应部署到公网。
