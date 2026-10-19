# Semgrep 首轮扫描报告

> Semgrep：1.173.0  
> 规则配置：`semgrep.yml`  
> 扫描对象：四个 P0 案例分支的 `app/` 目录

| 案例 | 规则命中 | 位置 | 结果 |
|---|---|---|---|
| PR-02 金额精度 | `wallet-float-money` | `app/service.py:31` | 命中 |
| PR-03 对象越权 | 无 | — | 应由授权回归测试发现 |
| PR-04 并发双花 | 无 | — | 应由并发测试和正确性 Agent 发现 |
| PR-08 提示注入 | `wallet-review-instruction-in-source` | `app/service.py:17` | 命中 |

首次运行先发现 `semgrep.yml` 中未引用的冒号导致 YAML 无效；修复后 `semgrep --validate` 确认两条规则有效。这个过程保留在实施记录中，用来说明安全工具配置本身也需要回归验证。

该结果不能解释为 Semgrep 对四个案例的 Recall 为 50%。现有规则集只声明覆盖金额浮点和评审指令，并未声明覆盖对象授权或并发事务；评测工具时必须先定义其任务边界。
