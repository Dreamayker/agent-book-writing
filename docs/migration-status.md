# 订单案例迁移状态与验证

日期：2026-11-05。业务基线：`7a61a4f`；规则：`order-rules-v1`。实施依据见 [规划](order-case-migration-plan.md)。当前交付为可运行工程及章节工程迁移稿，尚非完成真实模型实验的出版定稿。

## 已交付

| 范围 | 实际交付 | 验证 |
| --- | --- | --- |
| 规则契约 | [ADR-001](../order-review-lab/docs/ADR-001-business-contract.md) | 十规则、金额、选券、数量退款、旧订单及事务口径 |
| Java 工程 | core/infra/api/test 四模块 | JDK 17、真实 MySQL Testcontainers、Flyway/MyBatis |
| 计价 | 三类券、顺序、互斥择优、资格、封顶、整分分摊 | 8 项核心测试，含 1000 组确定种子分摊样例 |
| 订单状态 | 不可变快照、幂等、授权、退款、拆单与共享单位账本 | 11 项 MySQL/HTTP 集成测试，均不跳过 |
| 反例及修复 | [ORD-01～12](../order-review-lab/book-assets/README.md) | 每案错误/修复版本、原始日志、命令与哈希 |
| 评审适配 | Finding v2、项目清单、版本证据门禁、Java 风险路由、逐案例评分 | Python 46 项测试通过，覆盖率 90.23% |
| 书稿 | [导语与 9.1～9.12](../wallet-review-lab/docs/ima-sources/2026-11-05/README.md) | Markdown/富文本同步，原始来源保持不变 |
| CI | Java 构建、格式、覆盖率、静态规则、录制回放与报告 artifact | 独立 order-checks；原 Python 检查继续保留 |

## 运行证据

- Java：冻结案例基线 18 项测试通过，见 [基线构建日志](../order-review-lab/evaluation/reports/baseline-java.txt)；主线补充历史快照格式漂移回归后共 19 项通过，核心行覆盖率 180/200 = 90%，聚合行覆盖率 380/394 = 96.45%，见 [主线构建日志](../order-review-lab/evaluation/reports/main-java.txt)。
- Python：46 项测试通过、90.23% 覆盖率；Ruff 和 mypy 通过。见 [测试日志](../order-review-lab/evaluation/reports/baseline-python.txt)。
- ORD-09：错误版本实际 6400 分，预期 6600 分；修复版本实际 6600 分，退款期间实时计价调用为 0。见 [失败输出](../order-review-lab/book-assets/ORD-09/tool-evidence/raw/buggy.txt)、[修复输出](../order-review-lab/book-assets/ORD-09/tool-evidence/raw/fixed.txt)。
- 12 个案例全部完成验证。ORD-01 无缺陷，其余为 11 个独立根因；依赖与静态案例分别核验依赖树/公告及扫描结果。
- 录制多角色加规则仲裁得到 11 TP、0 FP、0 FN；这是夹具一致性结果，不能解释为模型准确率。见 [控制夹具报告](../order-review-lab/evaluation/reports/recorded-multi-arbitrated.json)。
- 可执行 JAR 通过真实 HTTP 连接本地 MySQL 完成试算、下单、退款与同键重放：实付 33000 分、退 C 为 6600 分。见 [HTTP 验证记录](../order-review-lab/evaluation/reports/http-smoke.json)。临时服务与数据库已在验证后停止。
- 运行器的独立测试确认业务子进程不继承 API 凭据；书稿校验检查 16 篇文档的 48 个正文/富文本/来源哈希，Markdown 与富文本重渲染一致。本地文档链接检查通过。
- [退款证据流程图](../order-review-lab/docs/figures/refund-evidence.svg) 同时提供 Mermaid 源码与 PNG，图示对应已执行的 ORD-09 流程。

## 依赖与扫描维护

修复历史 OSV 检查指出的 certifi、idna 和 pytest 版本问题：开发锁文件更新到 certifi 2026.10.23、pytest 9.2.0，隔离教学清单约束 certifi>=2026.10.18、idna>=3.15。旧 PR-07 补丁已适配新增约束并验证错误/修复补丁可依次应用，历史证据版本保持不变。OSV 检查覆盖两个工程，报告保存为 artifact；漏洞仍使检查失败，报告上传不再依赖仓库的 Code Scanning 开关。

## 相对规划的明确取舍

先实现完整叠加正确基线，再冻结 ORD-09 作为 `legacy/order-v0`，没有另行创建单券旧系统。`order-baseline-v1` 和 `order-stacking-v1` 指向同一个已验证业务提交；case/order/ORD-* 与 fix/order/ORD-* 保留独立变更历史。

固定适配器提供商品价、券和新人资格；提交后视为教学已付状态，退款仅保存内部记录。Redis、真实支付、异步 outbox、签名来源证明、模型仲裁、并行调度和跨仓库影响分析尚未实现。

退款采用数据库用户行锁与根订单锁，并补充单位条件更新及累计额度保护。同用户写入被串行化，这是一项教学取舍；worktree 用于保持代码版本独立，不构成恶意构建的系统沙箱。

ORD-04 构造的是缺失单位状态门禁：即使锁还存在，两个请求仍会把同一 C 退两次。ORD-05 构造的是重试响应协议错误：单位门禁挡住二次效果，但合法重试错误返回业务冲突。正文按实测行为解释，没有将二者写成未观察到的竞态或重复扣款。

## 尚未完成的验收

1. 真实双模型、3～5 次重复实验，以及模型调用预算、成本台账和失败分析。环境存在兼容 API 凭据，但没有配置评测模型；未擅自选择模型进行批量付费调用。
2. 实际业务/技术审阅者的人工批准。案例文件均保留 pending-human-review，不伪造人员与签名。
3. 外部工业数据的一手来源复核、最终图表编号、篇幅和出版语言审校。既有 9.6/9.7 对照继续保留来源限定，历史审校报告不自动变成新版验收结果。
4. 更大规模保留变体与生产环境适用性验证。现有测试和覆盖率不证明生产资金系统正确，也不涵盖全部安全场景。

全书其他章节尚未取得最终正文，只提供共享案例版本和 [章节追踪表](chapter-case-map.csv)，没有宣称改写未提供的章节。后续先配置真实评测的模型和预算，再按规划执行 M5 与出版收口。
