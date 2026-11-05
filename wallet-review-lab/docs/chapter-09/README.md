# 第 9 章拆分稿

> 版本说明（2026-11-05）：作者已指定 [IMA 最新书稿](../ima-sources/2026-11-05/README.md) 为当前版本，采用 9.1～9.12 结构并包含补充对照。本目录是此前仓库稿的拆分结果，以下生成规则仅适用于该历史版本。

本目录按出版子章节拆分。`00-overview.md` 是章节概述，`01`～`10` 分别对应 9.1～9.10，`11-project-cases.md` 是独立的项目案例子章节。

合并稿 `../chapter-09-rewrite-draft.md` 保留为内容来源。合并稿变化后，在仓库根目录运行 `ruby scripts/split_chapter09.rb` 重新生成本目录，避免两套稿件漂移。

## 阅读顺序

- [章节概述](00-overview.md)
- [9.1 AI 适合评审什么，不适合评审什么](01-capability-boundaries.md)
- [9.2 评审 Agent 的四类任务](02-review-task-types.md)
- [9.3 多 Agent 协同评审](03-multi-agent-collaboration.md)
- [9.4 测试、评审、安全 Agent 的协同](04-tool-agent-evidence-chain.md)
- [9.5 投票制、仲裁制和人工裁决](05-arbitration-human-decision.md)
- [9.6 PR 摘要、影响分析和风险标注](06-summary-impact-risk.md)
- [9.7 误报率和漏报率](07-false-positive-false-negative.md)
- [9.8 多 Agent 成本边界](08-cost-boundaries.md)
- [9.9 Token 成本与触发策略](09-routing-trigger-strategy.md)
- [9.10 如何评测代码评审 Agent](10-evaluation-and-rollout.md)
- [9.11 项目案例：Wallet Review Lab](11-project-cases.md)

## 编辑规则

- 内容修改优先落到合并稿，再运行拆分脚本。
- 不在拆分稿中单独维护重复内容。
- 项目案例的需求、Oracle、证据和补丁仍以 `../../book-assets/` 为准。
- 录制回放不得写成真实模型能力；未完成的真实模型实验继续明确标注。
