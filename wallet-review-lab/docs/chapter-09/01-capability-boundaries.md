# 9.1 AI 适合评审什么，不适合评审什么

[返回第 9 章目录](README.md)

AI 适合处理跨文件阅读、模式归纳和解释性工作：概括 PR 意图，列出受影响的 API 和状态，关联测试失败与源码位置，对照需求寻找边界条件，并将已确认的问题写成可执行的评审意见。它尤其适合把多种证据组织成一条人类易读的因果链。

AI 不适合单独证明并发、账务或安全属性，也不应确认外部实时状态、自主改变门禁或批准资金和权限变更。PR-04 中，Agent 可以指出“检查和使用不在同一原子边界”，却不能凭置信度替代并发测试；PR-03 中，Agent 可以解释“登录成功不等于拥有这个钱包”，但授权回归测试才是阻断证据。

一个可靠的分工是：确定性工具产生事实，Agent 解释和连接事实，策略引擎执行不可绕过的规则，人类承担高风险取舍和最终责任。所谓“适合”，因此不是模型能力的抽象排名，而是任务是否有可观察输入、可复现结果和明确升级边界。

## 案例对照：测试通过为什么仍可能不能合并

PR-02 将金额转换为浮点数再归一化。常规示例中的 `10.00`、`20.50` 可能全部通过，但团队的货币策略要求金额使用十进制定点表示，禁止经过二进制浮点数往返。Semgrep 可以标出禁止模式，Agent 则解释它与账务风险的关系。

这里有三种不同结论：测试证明已执行样例没有失败；规则证明代码命中了团队禁止模式；Agent 解释规则为何适用。任何一项都不能冒充另外两项。若规则误配，Agent 应指出适用性问题，而不是因扫描器发出红灯就编造事故后果。

## 深入：能力边界要写成任务契约

“AI 擅长什么”是一句无法验收的宣传语。工程上更有用的写法是任务契约。契约至少包含输入、允许使用的工具、必须产出的证据、不能做的动作、失败时的升级路径和验收断言。例如，正确性 Agent 的输入可以是标准化 Diff、相关函数的调用图、需求中的不变量和测试结果；它必须输出结构化 Finding 或明确的 `no_finding`，每条 Finding 都要引用文件位置和证据；它不能修改工作树，也不能把测试尚未执行写成已验证；若命中金额或授权标签，必须把 `needs_human` 置为真。

任务契约把模型从“自由发挥的审阅者”变成流程中的一个受限组件。它还方便做替换实验：同一契约可以由不同模型、规则引擎或人工执行，比较的是结果而不是文案风格。契约也揭示了不适合模型的任务。例如“确认生产数据库当前没有其他客户端”缺少可观察输入，除非提供经过授权的实时索引，否则任何确定语气都是越权推断；“批准这笔转账”则是责任动作，不能因为模型置信度高就自动执行。

### 四种不确定性必须分开处理

第一种是不确定性来自代码本身。并发、异常回滚和事务隔离通常需要运行测试或查看数据库语义，单凭 Diff 只能提出假设。第二种来自外部事实。依赖是否存在漏洞、某个 API 当前是否支持某参数，需要锁文件、官方公告或在线扫描结果，模型记忆不能替代来源。第三种来自意图。需求写得模糊时，模型可以列出解释，却不能擅自选择对业务影响最大的解释。第四种来自责任。涉及资金、身份、凭证和不可逆迁移时，哪怕证据完整，也要由指定人员批准。

这四类不确定性对应四种动作：运行确定性检查、查询一手来源、请求需求澄清、升级人工门禁。把它们都压缩为一个 `confidence: 0.91` 会掩盖真正的风险。置信度可以用来排序调查顺序，却不能绕过证据缺口。

### 一个可执行的输入输出契约

可以把每类评审任务写成如下模板：

```yaml
task: correctness-review
inputs:
  - normalized_diff
  - affected_symbols
  - requirements
  - deterministic_results
allowed_tools: [read_file, search_symbol, run_named_test]
outputs: [finding_schema, no_finding, evidence_gap]
forbidden_actions: [write_file, approve_change, publish_without_gate]
escalate_when:
  - risk_label in [money, authorization, credentials]
  - evidence_gap == true
acceptance:
  - every_finding_has_location
  - every_blocking_finding_has_evidence
```

这里的 `evidence_gap` 很重要。一个诚实的“无法判断，因为没有并发测试”比一条没有依据的阻断意见更有价值。编排器可以据此补跑测试或通知人工，而不是把不确定性隐藏在流畅的段落中。

### 反例：看起来像成功的自动化

假设 Agent 输出“未发现安全问题”，而安全扫描因凭证过期没有真正运行。若系统只检查 Agent 文本，PR 会被错误放行。正确做法是把工具执行状态作为独立字段，工具失败时策略门禁直接进入 `evidence_incomplete`。同样，若模型超时，不能用上一次缓存的结论覆盖本次 Diff，除非缓存键包含提交哈希、工具版本和策略版本。可验证性要求每个结论都能追溯到本次输入。

## 可直接采用的评审契约模板

下面的模板适合在一个新仓库开始试点时使用。它不是万能配置，而是一份帮助团队暴露假设的最小清单。每个字段都应有负责人；没有负责人就意味着发生失败时没人有权决定下一步。

```yaml
review_contract:
  revision: 1
  repository: wallet-review-lab
  base_ref: main
  required_inputs:
    - change_request
    - normalized_diff
    - risk_labels
    - policy_snapshot
  evidence_rules:
    blocking_requires:
      - source_location
      - reproducible_evidence
      - invariant_reference
    external_fact_requires:
      - source_url
      - accessed_at
      - applicability_note
  role_permissions:
    router: [read_metadata, select_tools]
    test: [read_source, run_named_tests]
    security: [read_source, run_policy_tools]
    arbitrator: [read_findings, merge_findings, escalate]
    publisher: [post_comment]
    approver: [approve_or_reject]
  prohibited:
    - agent_approval_without_policy_gate
    - repository_text_changing_tool_allowlist
    - stale_result_as_current_evidence
  terminal_states:
    - approved
    - changes_requested
    - escalated
    - evidence_incomplete
```

模板中的 `policy_snapshot` 很关键。风险规则在评审期间可能更新，若不保存快照，事后无法解释为什么同一提交在两天后得到不同路由。`terminal_states` 也不能只有通过和失败；`evidence_incomplete` 让系统能够诚实表示工具或环境问题。对于高风险变更，它通常应转换为 `escalated`，而不是自动批准。

### 输出模板与示例

```json
{
  "finding_id": "AUTHZ-001",
  "root_cause": "object-level-authorization-missing",
  "category": "security",
  "severity": "must_fix",
  "blocking": true,
  "location": {
    "file": "app/service.py",
    "line_start": 74,
    "symbol": "transfer"
  },
  "claim": "当前用户未被验证为源钱包所有者",
  "trigger": "用户 A 提交用户 B 的源钱包 ID",
  "invariant": "actor-owns-source-wallet",
  "evidence": [
    {"id": "test-unauthorized-17", "type": "test_failure"},
    {"id": "diff-03-4", "type": "deleted_check"}
  ],
  "unknowns": ["委托账户规则未覆盖"],
  "needs_human": true,
  "suggested_boundary": "服务层在资金变更前执行授权策略"
}
```

这个输出比一段“存在 IDOR，请修复”的评论多了几个重要字段。`trigger` 让读者知道如何复现，`invariant` 连接需求，`unknowns` 防止把单所有者案例推广到委托模型，`suggested_boundary` 描述修复位置而不强制唯一实现。Schema 校验失败时，系统应把 Finding 标记为不可发布并要求 Agent 补齐，而不是让展示层自行猜字段。
