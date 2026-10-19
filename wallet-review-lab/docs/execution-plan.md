# 第9章配套工程执行方案

> 状态：执行中  
> 版本：V1.0  
> 建立日期：2026-08-16  
> 上位方案：`../../第9章完善与案例落地方案.md`

## 1. 目的

本文档是 `wallet-review-lab` 仓库内可版本化、可验收的执行基线。上位方案负责章节定位、案例论证和出版规划；本文档负责回答以下问题：

- 当前要交付什么。
- 每项任务对应哪些代码和文档。
- 使用什么测试或证据验收。
- 哪些结论已经验证，哪些仍等待真实模型实验。

任何新增案例、Agent、工具或评测指标，应先更新本文档或对应 ADR，再进入实现。

## 2. 交付范围

### 2.1 必须交付

1. 一个不连接真实资金的数字钱包转账服务。
2. 可验证的金额守恒、余额非负、幂等和授权不变量。
3. 至少四个高价值教学 PR：金额精度、对象越权、并发双花、提示注入。
4. 统一 Finding Schema、风险路由、证据校验、去重和仲裁。
5. 单 Agent、多 Agent、多 Agent＋仲裁三种运行模式。
6. 确定性工具证据、人工裁决和可回放实验。
7. 真实模型适配器，以及与录制输出严格分离的评测路径。
8. 能支撑图书正文的数据表、过程记录和事实核验材料。

### 2.2 不在当前范围

- 真实支付、银行或清算网络接入。
- 生产级身份、账务和合规系统。
- 自动把教学漏洞部署到公网。
- 由 AI 单独批准资金、授权或事务类高风险变更。
- 在没有真实运行数据时推断模型精度、成本或效率提升。

## 3. 实施原则

### 3.1 正确基线优先

先建立通过不变量测试的正确实现，再从基线产生缺陷分支。`main` 必须保持正确，教学漏洞只存在于 `case/pr-*` 分支和补丁中。

### 3.2 证据优先

阻断 Finding 必须包含精确位置及测试、静态分析、依赖扫描或策略证据。模型置信度不能替代证据。

### 3.3 风险驱动

低风险变更使用轻量路径；金额、授权、凭证和数据库事务类变更必须进入高风险路径并由人类终审。

### 3.4 录制与实时分离

Recorded Agent 用于验证控制面和出版复现；实时模型用于能力评测。两类输出、报告和统计禁止混用。

### 3.5 可回放与可追踪

每个案例至少包含需求、Oracle、错误补丁、工具证据、人工裁决和运行输出。每个里程碑必须对应 Git SHA 和实施日志。

## 4. 系统工作流

```text
PR / Patch
  → 识别变更路径与语义标签
  → 风险路由
  → 确定性工具
  → 专业 Agent 并行评审
  → Finding Schema 校验
  → 根因去重与证据合并
  → 策略仲裁
  → 自动评论 / 请求修改 / 人工升级
  → 保存运行记录并评分
```

## 5. 角色与权限

| 角色 | 职责 | 可修改代码 | 可批准高风险 PR |
|---|---|---:|---:|
| general-review | 低风险通用评审和摘要 | 否 | 否 |
| correctness | 逻辑、不变量、并发与事务 | 否 | 否 |
| test | 测试缺口与失败证据 | 否 | 否 |
| security | 授权、输入、凭证和依赖安全 | 否 | 否 |
| impact | 调用方、API 和依赖影响 | 否 | 否 |
| arbitrator | 去重、合并证据、应用策略 | 否 | 否 |
| human Tech Lead | 业务权衡和最终责任 | 是 | 是 |

## 6. 案例实施规范

每个案例目录遵循：

```text
book-assets/<case>/
├── requirement.md
├── oracle.yaml
├── 0001-*.patch
├── fixed.patch
├── tool-evidence/
│   ├── observed.yaml
│   └── raw/
├── runs/
│   ├── recorded-agents.json
│   └── live/                   # 有 API Key 后生成
└── human-verdict.yaml
```

### 6.1 P0 案例

| 案例 | 标准 Finding | 主要验证方法 | 当前状态 |
|---|---|---|---|
| PR-02 金额精度 | `MONEY-001` | Semgrep + 货币策略 | 已完成 |
| PR-03 对象越权 | `AUTHZ-001` | 授权回归测试 | 已完成 |
| PR-04 并发双花 | `CONCURRENCY-001` | 并发回归测试 | 已完成 |
| PR-08 提示注入 | `AGENTSEC-001` | 本地守卫 + Semgrep | 已完成 |

### 6.2 P1 案例

| 案例 | 教学目标 | 状态 |
|---|---|---|
| PR-01 文档或文案 | 低风险单 Agent 路由 | 已完成 |
| PR-05 幂等错误 | 重试、重复扣款和状态不变量 | 已完成 |
| PR-07 依赖升级 | OSV 证据和可利用性判断 | 已完成 |

## 7. 评测设计

### 7.1 运行模式

| 模式 | 目的 |
|---|---|
| deterministic-only | 测量规则、测试和扫描工具的能力边界 |
| single | 建立单通用 Agent 基线 |
| multi | 观察专业分工和重复报告 |
| multi_arbitrated | 观察去重、证据合并和人工升级 |

### 7.2 指标

- Finding 级：TP、FP、FN、Precision、Recall、重复率。
- PR 级：高风险检出率、错误阻断率、最终裁决。
- 效率级：首次反馈延迟、总耗时、输入与输出 Token。
- 经济级：单 PR 模型成本、缓存输入成本。
- 稳定性：相同配置重复运行的 Finding 和严重性波动。

### 7.3 模型实验

- 最小：一种模型复用全部角色。
- 推荐：模型 A 执行专业 Agent，模型 B 独立仲裁。
- 可选：第三种模型用于跨模型稳健性复验。
- 每种配置、每个案例运行 3～5 次。
- 必须保存模型标识、提示词版本、参数、Token、延迟和原始输出。

当前没有 API Key，实时模型实验状态为“等待凭据”，不影响控制面、案例和工具链实施。

## 8. 分阶段计划

### 阶段 A：正确基线与 P0 案例

状态：已完成主体。

验收：

- 正确基线通过四条不变量。
- 四个案例拥有真实 Git 分支和 `format-patch`。
- 错误实现能够被对应证据稳定识别。

修复分支、`fixed.patch` 和原始证据快照已经补齐。

### 阶段 B：多 Agent 控制面

状态：已完成。

验收：

- Finding Schema 拒绝无证据阻断结论。
- 风险路由可以强制人工审核。
- 重复 Finding 能合并来源和证据。
- 三种 Agent 模式可离线回放。

### 阶段 C：确定性工具与 CI

状态：进行中。

已完成：pytest、Hypothesis、Ruff、mypy、85% 覆盖率门槛、Semgrep 教学规则、OSV Scanner 工作流和策略门禁。

剩余：

- 在远程 GitHub 仓库首次运行并验证 OSV/Semgrep 工作流结果。

### 阶段 D：P1 案例与完整评测数据结构

状态：案例已完成，评测扩展等待实时模型实验。

案例任务已完成。剩余任务是补齐重复率、延迟、Token 和成本字段并用真实运行数据填充。

### 阶段 E：实时模型实验

状态：等待 API Key。

任务：执行模型矩阵，重复运行，保存原始输出并生成真实评测报告。

### 阶段 F：正文、引用和出版资产

状态：进行中。

已完成：建立并收口事实核验表；在 `docs/chapter-09-rewrite-draft.md` 按新的十节结构完成不依赖实时模型数据的技术初稿；完成实现一致性技术审校；生成图 9-1 和图 9-2 的 Mermaid、SVG 和 PNG 资产。

剩余：完成真实模型实验后填充实验表与实验图；进行最终出版编辑；补齐案例截图。

## 9. 追踪矩阵

| 方案项 | 实现 | 验证/证据 | 报告/记录 | Git |
|---|---|---|---|---|
| 正确转账基线 | `app/domain.py`、`repository.py`、`service.py` | `tests/test_transfer_invariants.py` | `implementation-log.md` | `714ea49` |
| P0 案例分支 | `case/pr-*`、`book-assets/pr-*` | 各案例 `observed.yaml`、`oracle.yaml` | `book-assets/README.md` | `308b7cf` + 案例 SHA |
| 提示注入边界 | `review_system/untrusted_input.py` | `test_repository_instruction_*`、Semgrep | `semgrep-first-run.md` | `308b7cf`、`79b63bd` |
| 风险路由 | `review_system/router.py` | `tests/test_review_contracts.py` | `ADR-002` | `308b7cf` |
| Finding Schema | `review_system/schemas.py` | 无证据阻断测试 | `ADR-002` | `308b7cf` |
| 去重与仲裁 | `review_system/adjudication.py` | 合并证据和人工升级测试 | `pr04-first-run.md` | `7a4f717` |
| 三种评审模式 | `review_system/pipeline.py` | `tests/test_review_pipeline.py` | `pr04-first-run.md` | `7a4f717` |
| 六缺陷案例评分 | `evaluation/suite.py`、`scoring.py` | `tests/test_evaluation_suite.py` | `recorded-suite-first-run.md` | `8d1f174`、`11b3868` |
| Semgrep 工具证据 | `semgrep.yml` | Semgrep 1.173.0 验证与扫描 | `semgrep-first-run.md` | `79b63bd` |
| 实时模型接口 | `responses_agent.py` | 注入式 HTTP 单元测试 | 实时报告待生成 | `79b63bd` |
| 实施审计 | `docs/` | Git diff 与链接检查 | `implementation-log.md` | `4a9700f` |
| API 层质量 | `app/api.py` | API 测试、API 覆盖率 100% | 实施日志 | `3a115ef` 前批次 |
| P1 案例 | `book-assets/pr-01-*`、`pr-05-*`、`pr-07-*` | Oracle、原始证据和人工裁决 | 实施日志 | `11b3868`、`3a115ef`、`bccdff6` |
| PR-05 幂等案例 | `case/pr-05-idempotency-retry`、`book-assets/pr-05-*` | 幂等回归测试 | 六缺陷回放报告 | `dec5045`、`ef46eb4` |
| PR-01 低风险案例 | `case/pr-01-documentation-only`、`book-assets/pr-01-*` | 低风险 approve 路径测试 | 实施日志 | `9dae8b4`、`e47f09d` |
| PR-07 依赖案例 | `case/pr-07-vulnerable-dependency`、`book-assets/pr-07-*` | OSV Query 与中风险路由测试 | 六缺陷回放报告 | `12860d9`、`a704d3d` |
| 事实核验 | `references/source-audit.csv` | 22 条声明均有保留、重写、删除或本地实验决策 | `references/README.md` | `323722c` + 本批次 |
| 真实模型评测 | 适配器已就绪 | 3～5 次重复实验 | 待生成 | 等待 Key |
| 章节重写 | `docs/chapter-09-rewrite-draft.md` | 旧章覆盖审校、干净环境复现 | `chapter-09-technical-review.md` | `ace377f`、`6d6cc9a`、`2227774` |

## 10. 变更与验收规则

### 10.1 方案变更

以下变化必须新增或更新 ADR：

- 更换贯穿案例或扩大业务边界。
- 改变高风险人工终审规则。
- 改变 Finding Schema 的阻断证据要求。
- 将系统绑定到单一模型或供应商。
- 将录制数据用于模型能力结论。

### 10.2 每批次完成条件

- 代码、测试、证据和文档同步更新。
- Ruff、严格 mypy 和 pytest 通过。
- 工具配置先验证再扫描。
- 实施日志追加结果和失败处理。
- 里程碑状态更新。
- Git 工作区干净并形成有意义的提交。

## 11. 下一批任务

在等待 API Key 期间按以下顺序执行：

1. 对正文初稿进行技术审校和出版编辑，确认后再覆盖上层原稿。
2. 继续核验论文、厂商和工具数据的一手来源。
3. 收到 API Key 后执行双模型家族重复实验并填充占位表。
4. 远程仓库建立后验证 GitHub Actions。
