# Agent 图书编写

本仓库保存《AI 代码评审与多 Agent 协同》第 9 章的书稿、案例资产和可复现实验工程。

## 内容结构

- `第9章 AI 代码评审与多 Agent 协同.md`：原始章节稿。
- `第9章完善与案例落地方案.md`：章节重构与案例实施方案。
- `wallet-review-lab/`：可安装、可测试、可回放的实验工程。
- `wallet-review-lab/docs/chapter-09/`：第 9 章按概述、9.1～9.10 和项目案例拆分后的文档目录。
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
