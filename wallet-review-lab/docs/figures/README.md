# 钱包案例图片

以下图号沿用旧钱包稿的编号，作为已有实验素材保留。新版书稿的最终图号及订单案例图应按迁移规划重新核对。

`source/` 保存 Mermaid 可编辑源码；`svg/` 用于排版；`png/` 用于预览和不支持 SVG 的编辑流程。

## 图片清单

| 图号 | 内容 | 源文件 |
|---|---|---|
| 图 9-1 | AI 代码评审证据流水线 | `source/figure-9-1-evidence-pipeline.mmd` |
| 图 9-2 | PR-04 并发双花评审时序 | `source/figure-9-2-pr04-sequence.mmd` |

## 重新渲染

```bash
npx --yes @mermaid-js/mermaid-cli \
  -p docs/figures/puppeteer-config.json \
  -c docs/figures/mermaid-config.json \
  -i docs/figures/source/figure-9-1-evidence-pipeline.mmd \
  -o docs/figures/svg/figure-9-1-evidence-pipeline.svg \
  -b white

npx --yes @mermaid-js/mermaid-cli \
  -p docs/figures/puppeteer-config.json \
  -c docs/figures/mermaid-config.json \
  -i docs/figures/source/figure-9-1-evidence-pipeline.mmd \
  -o docs/figures/png/figure-9-1-evidence-pipeline.png \
  -b white -s 2
```

其余图片替换输入和输出文件名即可。渲染时需要 Mermaid CLI 和 Chrome/Chromium。

