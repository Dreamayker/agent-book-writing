# Wallet Review Lab

《AI 代码评审与多 Agent 协同》第 9 章共享 Python 评审流程与历史钱包实验工程。当前主线业务在 [Java 订单工程](../order-review-lab/README.md)，最新正文见 [书稿目录](docs/ima-sources/2026-11-05/README.md)，实施结果见 [迁移状态](../docs/migration-status.md)。

项目实施过程、实验记录和架构决策见 [`docs/`](docs/README.md)。

这个项目不是支付系统，也不连接真实资金。它用一个最小化的钱包转账服务演示 AI 代码评审中的正确性、安全、并发、幂等与提示注入问题。

## 核心不变量

1. 金额守恒：一次成功转账前后的总余额相同。
2. 余额非负：任何钱包都不能因转账变成负数。
3. 幂等：同一用户使用同一幂等键重试，只产生一次转账。
4. 授权：用户只能从自己拥有的钱包发起转账。

## 快速开始

```bash
uv sync --extra dev --locked
uv run pytest
uv run ruff check .
uv run mypy app review_system evaluation
```

回放 PR-04 的三种评审模式：

```bash
make replay-pr04
```

回放当前订单案例：

```bash
uv run python -m evaluation.projects ../order-review-lab/evaluation/cases.yaml
```

录制 Agent 输出只用于离线、确定性地复现编排和仲裁流程，不冒充实时模型判断。

## 实时模型模式

`ResponsesReviewAgent` 支持 OpenAI Responses API，并以 JSON Schema 约束 Finding 输出。配置方式见 `.env.example`；真实密钥只通过进程环境注入，不写入仓库。实现依据为[官方 Structured Outputs 文档](https://developers.openai.com/api/docs/guides/structured-outputs)。

真实模型实验需要显式配置模型、兼容端点和预算，目前尚未产生本项目双模型重复评测数据。离线录制回放的指标只验证评测流程，不代表模型 Precision 或 Recall。

启动演示 API：

```bash
uv run uvicorn app.api:app --reload
```

请求使用教学用身份头 `X-User-Id`，不能用于生产环境。

## 目录

- `app/`：正确的基线实现。
- `tests/`：领域不变量、授权、幂等和并发测试。
- `book-assets/`：各教学 PR 的需求、缺陷标准答案与讲解素材。
- `policies/`：风险路由和评审门禁规则。
- `review_system/`：已有的 Agent 适配、风险路由、Finding 校验、去重与规则仲裁。

## 教学分支

四个 P0 缺陷保存在 `case/pr-*` 分支，`main` 始终保留正确基线。具体分支、预期失败和人工裁决见 `book-assets/README.md`。

## 安全声明

所有账户和金额均为虚构测试数据。案例中的漏洞实现只以补丁或测试夹具形式保存，不应部署到公网。
