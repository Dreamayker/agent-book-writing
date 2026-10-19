# PR-04 首轮离线回放报告

> 运行类型：录制输出回放，用于验证编排、去重和仲裁，不代表实时模型能力。  
> 基线提交：`714ea49`  
> 缺陷提交：`8c0db46`  
> 回放实现：`7a4f717`

## 结果

| 模式 | 运行角色 | 原始发现 | 根因是否检出 | 最终结论 |
|---|---|---:|---|---|
| 单 Agent | general-review | 1 | 否 | comment |
| 多 Agent | correctness、test、security、impact | 2 | 是，但重复 | request_changes |
| 多 Agent + 仲裁 | 同上并执行去重与策略仲裁 | 1 | 是，源码与测试证据已合并 | escalate |

## 观察

单通用 Agent 只指出固定休眠带来的延迟问题，没有识别“原子边界被移除”这一双花根因。专业正确性 Agent 定位到仓储锁被移除，测试 Agent 提供并发回归测试失败证据。两条发现使用同一 `finding_id` 和文件定位，经仲裁合并为一条 Finding。

由于变更同时命中敏感路径并带有 `money`、`database-transaction` 标签，风险路由器将其提升为高风险。即便 Finding 已有充分证据，最终结果仍为 `escalate`，必须由人类批准，符合评审政策。

## 复现

```bash
make replay-pr04
```

如果本地 `uv` 因网络受限尝试重建环境，可在依赖已经安装的情况下直接运行：

```bash
.venv/bin/python -m evaluation.replay_pr04 --mode single
.venv/bin/python -m evaluation.replay_pr04 --mode multi
.venv/bin/python -m evaluation.replay_pr04 --mode multi_arbitrated
```

## 下一轮评测要求

- 接入至少一个真实模型适配器后保存模型、提示词和采样参数。
- 每种模式重复运行 3～5 次。
- 补充 Token、首次反馈延迟、Precision、Recall 和重复率。
- 录制结果与实时模型结果分栏展示，禁止混合统计。
