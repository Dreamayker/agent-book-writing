# Review Harness

本目录保存与业务工程分离的 Python 评审控制面：Finding Schema、证据校验、风险路由、角色编排、去重、规则仲裁和录制回放。

它不包含钱包业务，也不连接真实资金。当前案例清单位于 [`order-review-lab/evaluation/cases.yaml`](../order-review-lab/evaluation/cases.yaml)，订单业务源码和案例证据由 `order-review-lab` 管理。

## 运行

```bash
cd review-harness
uv sync --extra dev --locked
uv run pytest
uv run ruff check .
uv run mypy review_system evaluation
uv run python -m evaluation.projects ../order-review-lab/evaluation/cases.yaml --mode multi_arbitrated
```

录制输出只验证控制器的加载、路由、证据门禁、去重和仲裁，不代表实时模型能力。实时模型适配器需要明确的模型、端点和预算；没有这些配置时使用录制适配器。

## 目录

- `review_system/`：评审上下文、Finding、证据、角色适配器、流水线和仲裁。
- `evaluation/projects.py`：读取订单案例清单并回放录制评审。
- `policies/`：控制面风险和输入策略。
- `tests/`：控制面和订单案例回放测试。

订单业务、案例补丁、原始日志和 MySQL 测试见 [`order-review-lab`](../order-review-lab/README.md)。
