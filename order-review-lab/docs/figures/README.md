# 订单书稿图片

2026-11-06 出版改写稿使用四张本地图，源文件、SVG 和 PNG 同名保存。SVG 用于排版，PNG 用于预览。

| 图号 | 文件名 | 正文位置 |
| --- | --- | --- |
| 图 9-1 | chapter09-architecture | 9.3：Java 业务与 Python 评审职责 |
| 图 9-2 | chapter09-review-sequence | 9.5：顺序角色与规则仲裁 |
| 图 9-3 | chapter09-refund-state | 9.7：单位状态、幂等与账本 |
| 图 9-4 | chapter09-trust-boundary | 9.11：仓库数据与执行权限 |

图形主题使用本目录 chapter09-theme.json；复用历史工程的 Chrome 配置，从仓库根目录运行（需安装 Mermaid CLI 与 Chrome）：

```bash
npx --yes @mermaid-js/mermaid-cli \
  -p wallet-review-lab/docs/figures/puppeteer-config.json \
  -c order-review-lab/docs/figures/chapter09-theme.json \
  -i order-review-lab/docs/figures/chapter09-architecture.mmd \
  -o order-review-lab/docs/figures/chapter09-architecture.svg -b white
```

生成 PNG 时将输出后缀改为 `.png`，可加 `-s 1.5`。本次使用 Mermaid CLI 12.2.0；准确本地版本以渲染记录为准。新增图描述现有实现，不把 worktree 当沙箱，不把模型意见当执行命令。退款状态图是业务顺序示意，不是对实际 SQL 位置的逐行映射。

`refund-evidence.*` 为上轮迁移的退款证据总览，作为工程参考保留，不与新版四图混用图号。历史钱包图在另一目录保留原适用范围。
