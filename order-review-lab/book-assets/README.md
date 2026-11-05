# 订单案例与执行证据

12 个案例由正确基线 `7a61a4f` 独立生成，清单见 [cases.yaml](../evaluation/cases.yaml)。案例均为教学构造，错误版本不用于部署。

| 案例 | 主题 | 证据目录 |
| --- | --- | --- |
| ORD-01 | 文档零缺陷 | [运行记录](ORD-01/tool-evidence/observed.yaml) |
| ORD-02 | 分摊尾差 | [运行记录](ORD-02/tool-evidence/observed.yaml) |
| ORD-03 | 对象授权 | [运行记录](ORD-03/tool-evidence/observed.yaml) |
| ORD-04 | 单位退款状态与并发请求 | [运行记录](ORD-04/tool-evidence/observed.yaml) |
| ORD-05 | 幂等重放响应 | [运行记录](ORD-05/tool-evidence/observed.yaml) |
| ORD-06 | 优惠后门槛 | [运行记录](ORD-06/tool-evidence/observed.yaml) |
| ORD-07 | Log4j 漏洞版本与适用性 | [运行记录](ORD-07/tool-evidence/observed.yaml) |
| ORD-08 | Java 注释注入 | [运行记录](ORD-08/tool-evidence/observed.yaml) |
| ORD-09 | 快照退款与实时规则 | [运行记录](ORD-09/tool-evidence/observed.yaml) |
| ORD-10 | 品类资格 | [运行记录](ORD-10/tool-evidence/observed.yaml) |
| ORD-11 | 拆单保留分摊 | [运行记录](ORD-11/tool-evidence/observed.yaml) |
| ORD-12 | 互斥合法路径 | [运行记录](ORD-12/tool-evidence/observed.yaml) |

## 重放

从 `order-review-lab` 运行：

```bash
python3 scripts/replay_cases.py verify --case ORD-09
```

需要完整 Git 历史、JDK 17、Docker；依赖案例需要 Maven/OSV 网络，注入案例需要 uvx Semgrep。脚本从 case.yaml 的基线创建 worktree，检查补丁、提交错误版本、运行目标验证、应用修复并重跑，更新对应 case/fix 分支。不要在没有准备新版本的情况下运行 `prepare`，该操作会重新生成全部案例元数据。

编译失败、缺少 Docker 和超时不会被当作业务缺陷命中。ORD-05 明确识别同键重试产生的预期外业务冲突；其他业务案例要求指定断言失败。ORD-07 取得解析依赖和 CVE 公告，但不宣称已证明可利用链。ORD-08 静态检测不等于模型抗注入实测。

`runs/recorded-agents.json` 是预设控制夹具；general-review 故意为空，专业角色包含预设根因，用来验证漏报、去重与评分。human-verdict.yaml 标为 pending-human-review，未伪造人工批准。

普通评审输入仅含待审版本的源码与日志，manifest 将它们绑定 Case ID、Git 提交及 SHA-256。修复日志、Oracle 和 fixed.patch 保存在案例中，供评分和修复验收使用。
