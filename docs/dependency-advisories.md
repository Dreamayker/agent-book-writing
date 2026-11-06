# 主线依赖检查与适用性记录

日期：2026-11-05。本记录适用于当前主线；`7a61a4f`、两个教学标签及 ORD 分支保持原始版本，以便重放已记录的实验。

## 补丁更新

在 Spring Boot 3.5.16 的依赖管理之上，主线明确管理以下兼容分支的补丁版本：

| 组件 | 原解析版本 | 主线版本 |
| --- | --- | --- |
| Jackson BOM | 2.21.4 | 2.21.8 |
| Log4j BOM / API | 2.24.3 | 2.25.5 |
| Tomcat embed | 10.1.55 | 10.1.61 |
| Commons Compress（测试依赖） | 1.24.0 | 1.28.0 |
| Commons Lang（Compress 传递依赖） | 3.17.0 | 3.18.0 |

升级后重新执行 19 项 Java 测试和覆盖率检查。冻结版本仍用于历史案例复现，不能用当前主线的依赖检查结论代替其原始证据。

## 扫描差异与补充门禁

OSV Scanner Action v2.5.0 在本地和 GitHub 都识别出锁文件及 SBOM 包，但输出空结果；同一批 Maven 坐标通过 OSV API 查询却返回公告。原因尚未确定，因此没有把扫描器的空结果当作无漏洞证明。

CI 继续保留扫描器，并用 [直接 API 校验脚本](../order-review-lab/scripts/check_sbom_advisories.py) 检查聚合 SBOM 中的全部外部 Java 组件，包括测试依赖。查询额外包含已知受影响的 Commons Compress 1.24.0，必须返回 `GHSA-4265-ccf5-phj5`；响应缺项、网络异常、控制样本漏检、新公告或适用性记录到期均使门禁失败。原始响应和 SBOM 保存在 CI artifact，本次实测快照见 [API 报告](../order-review-lab/evaluation/reports/dependency-api.json)。

## 两项功能适用性判断

当前公开 6.2 分支最高版本仍为 6.2.19。以下为依据代码作出的功能适用性判断，人工业务批准仍保持待审，不代表对框架的通用安全承诺：

| 公告 | 触发条件 | 当前工程依据 |
| --- | --- | --- |
| [GHSA-j9f9-w8pj-32f8](https://osv.dev/vulnerability/GHSA-j9f9-w8pj-32f8) | SSE 中渲染视图片段导致流损坏 | [OrderController](../order-review-lab/order-api/src/main/java/com/xinghe/order/api/OrderController.java) 仅有 JSON REST；无 SSE、SseEmitter 或 FragmentsRendering |
| [GHSA-pc63-qcmh-9cmg](https://osv.dev/vulnerability/GHSA-pc63-qcmh-9cmg) | XsltView、通配视图映射及推导视图名组合 | 无 XsltView、视图解析器、样式表或模板配置；控制器使用 `@RestController` |

[机器可读判断](dependency-assessments.json) 绑定上述公告、Spring WebMVC 6.2.19 的完整 PURL 和全部生产源码/资源的 SHA-256，复查期限为 2026-12-05。生产源码/资源发生变化、增加视图/SSE 或升级依赖时需重新判断；其他包、其他版本和其他公告不会被此记录放行。
