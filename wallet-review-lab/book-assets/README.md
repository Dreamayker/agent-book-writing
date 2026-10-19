# 教学 PR 素材

这里保存第 9 章使用的可回放案例。每个案例最终应具备：

- `requirement.md`：开发者收到的需求和验收标准。
- `oracle.yaml`：由作者与技术审校确认的缺陷标准答案。
- `diff.patch`：待审查的错误变更。
- `tool-evidence/`：测试与静态工具的原始输出。
- `runs/`：单 Agent、多 Agent、仲裁模式的结构化输出。
- `human-verdict.yaml`：人工最终裁决。
- `fixed.patch`：修复后的变更。

以下七个教学案例应在仓库远程分支中保持可切换：

| 案例 | 分支 | 主要证据 |
|---|---|---|
| PR-01 文档说明 | `case/pr-01-documentation-only` | 低风险、零 Finding、自动通过 |
| PR-02 金额精度 | `case/pr-02-money-precision` | 测试通过但静态策略拒绝 `float` 金额 |
| PR-03 对象越权 | `case/pr-03-object-authorization` | 授权回归测试失败 |
| PR-04 并发双花 | `case/pr-04-concurrent-double-spend` | 并发回归测试稳定失败 |
| PR-05 幂等重试 | `case/pr-05-idempotency-retry` | 幂等回归测试失败 |
| PR-07 依赖降级 | `case/pr-07-vulnerable-dependency` | OSV 漏洞公告与适用性仲裁 |
| PR-08 提示注入 | `case/pr-08-prompt-injection` | `AGENTSEC-001` 策略发现 |

每个目录中的 `0001-*.patch` 均由对应真实提交通过 `git format-patch` 生成，不是手写 Diff。

回放示例：

```bash
git switch case/pr-04-concurrent-double-spend
uv run pytest tests/test_transfer_invariants.py::test_concurrent_transfers_cannot_double_spend -q
git switch main
```
