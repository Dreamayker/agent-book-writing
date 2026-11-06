# 第 9 章参考资料与阅读入口

本表配合 2026-11-06 出版改写稿。链接及页面标题于当日检查；核对范围为本章保留的机制定义，不包含对厂商效果数字的独立复现。动态产品文档可能变化，正式交稿应固定引用版本或归档。原稿中的检索编号和未复核统计不再作为当前正文引用，原始材料保留在 IMA 来源及 Git 历史。

| 编号 | 作者或机构、标题与版本 | 阅读入口 | 本章引用范围 |
| --- | --- | --- | --- |
| R1 | GitHub Docs，About code owners；动态文档 | [官方文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) | 路径所有者与要求所有者审查的配置；不代表本仓库已配置完成 |
| R2 | Xunzhu Tang、Kisub Kim、Yewei Song 等，CodeAgent: Autonomous Communicative Agents for Code Review，2024，arXiv:2402.02172 | [论文及版本记录](https://arxiv.org/abs/2402.02172) | 多角色与 QA-Checker 监督机制，依据摘要；不采用其效果数字 |
| R3 | OASIS，Static Analysis Results Interchange Format (SARIF) Version 2.1.0 Plus Errata 01 | [标准全文](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) | 结果交换、规则、消息及定位；本项目未实现 SARIF 导出 |
| R4 | OpenSSF SLSA，Provenance，规范 v1.0 | [版本化规范](https://slsa.dev/spec/v1.0/provenance) | 构建来源、输入与产物；不将本地哈希清单描述为供应链认证 |
| R5 | OpenTelemetry，Semantic conventions for generative AI systems，主分支文档 | [官方源码文档](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/README.md) | 模型操作与遥测约定；网页旧入口已迁移，采用官方源码入口，接口稳定性以各属性说明为准 |
| R6 | Stripe Docs，Idempotent requests，API Reference | [官方文档](https://docs.stripe.com/api/idempotent_requests) | 幂等键与首次结果重放；不把 Stripe 的错误缓存和保留窗口当作本工程契约 |
| R7 | OWASP API Security Project，API1:2023 Broken Object Level Authorization | [2023 版条目](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/) | 对象授权风险定义；本工程用跨用户请求检查，不报告外部检测准确率 |
| R8 | OWASP Gen AI Security Project，LLM01:2025 Prompt Injection | [2025 版条目](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | 直接及间接注入与权限边界；不据外部数据推算本地防御成功率 |
| R9 | SWE-bench 项目，官方站点与 Verified 说明 | [官方站点](https://www.swebench.com/) | 执行型修复评测与人工筛选子集；不引用动态榜单名次与分数 |

## 本地执行记录

业务规则见 [订单契约](decision-records/ADR-001-business-contract.md)；错误、修复与测试版本见 [十二个案例](../order-review-lab/book-assets/README.md)；维护期间的工具分歧及适用性记录见 [依赖审阅记录](dependency-advisories.md)。它们是本章本地结论的来源，与上表外部机制区分。

正文中的假设费用、教学分析记录、空白人工复核单及展示性数据摘录均就近标明，不是执行记录。实时模型效果尚未测得。
