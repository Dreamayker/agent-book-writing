# Wallet Review Lab

《AI 代码评审与多 Agent 协同》第 9 章配套实验仓库。

项目实施过程、里程碑和架构决策见 [`docs/`](docs/README.md)。

## API response wording

The transfer response now documents that `transfer_id` is safe to use for client-side tracing.

这个项目不是支付系统，也不连接真实资金。它用一个最小化的钱包转账服务演示 AI 代码评审中的正确性、安全、并发、幂等与提示注入问题。

## 核心不变量

1. 金额守恒：一次成功转账前后的总余额相同。
2. 余额非负：任何钱包都不能因转账变成负数。
3. 幂等：同一用户使用同一幂等键重试，只产生一次转账。
4. 授权：用户只能从自己拥有的钱包发起转账。

## 快速开始

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy app
```

回放 PR-04 的三种评审模式：

```bash
make replay-pr04
```

录制 Agent 输出只用于离线、确定性地复现编排和仲裁流程，不冒充实时模型判断。

## 实时模型模式

`ResponsesReviewAgent` 支持 OpenAI Responses API，并以 JSON Schema 约束 Finding 输出。配置方式见 `.env.example`；真实密钥只通过进程环境注入，不写入仓库。实现依据为[官方 Structured Outputs 文档](https://developers.openai.com/api/docs/guides/structured-outputs)。

当前环境没有配置 API Key，因此尚未产生实时模型评测数据。离线录制回放的指标只验证评测控制面，不代表模型 Precision 或 Recall。

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
- `review_system/`：后续多 Agent 评审实现。

## 教学分支

四个 P0 缺陷保存在 `case/pr-*` 分支，`main` 始终保留正确基线。具体分支、预期失败和人工裁决见 `book-assets/README.md`。

## 安全声明

所有账户和金额均为虚构测试数据。案例中的漏洞实现只以补丁或测试夹具形式保存，不应部署到公网。
