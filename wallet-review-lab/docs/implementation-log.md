# 实施日志

> 时区：Asia/Shanghai（UTC+8）  
> 日志建立日期：2026-08-16  
> 证据来源：Git 历史、测试输出、案例 `observed.yaml` 和评测报告。
>
> 本文保留历史实施记录。2026-11-05 已清理被新版书稿和迁移规划取代的旧文件；历史条目中的旧路径可在 Git 提交 `a705616` 查看。当前实施依据为 [订单案例迁移规划](../../docs/order-case-migration-plan.md)。

## 2026-08-16：方案确定

### 决策

- 将原稿中的优惠券案例替换为数字钱包转账服务。
- 将交付目标从概念综述升级为“章节正文 + 可运行仓库 + 教学 PR + 评测报告”。
- 定义四条基础不变量：金额守恒、余额非负、幂等和源钱包授权。

### 产物

- 上层方案文档：`../第9章完善与案例落地方案.md`。
- 决策依据见 `decision-records/ADR-001-wallet-transfer-case.md`。

## 2026-08-16 13:13：建立正确基线

### Git

- 提交：`714ea49 build: establish wallet review lab baseline`。

### 实施

- 创建 FastAPI 教学服务、领域对象、线程安全内存仓储和转账服务。
- 创建 pytest、Hypothesis、Ruff、mypy、coverage 和 GitHub Actions 配置。
- 建立四个 P0 案例的需求与标准答案框架。

### 验证

- 首轮领域测试：8 个测试通过。
- Ruff 首次发现 FastAPI 参数声明、无用导入和导入排序问题，修正后通过。
- mypy 首次发现 `DecimalTuple.exponent` 联合类型问题，改用 `quantize` 比较后通过。

## 2026-08-16 13:23：建立真实教学分支

### Git

- 主线提交：`308b7cf feat: add replayable P0 review cases and policy guard`。
- 案例提交：

  - `612a91c`：PR-02 金额经 `float` 归一化。
  - `7690a22`：PR-03 删除源钱包所有权检查。
  - `8c0db46`：PR-04 移除原子锁并制造稳定竞态窗口。
  - `acc5249`：PR-08 在源码注释中嵌入评审指令。

### 实施

- 每个案例建立独立 `case/pr-*` 分支。
- 使用 `git format-patch` 生成教学补丁，避免手写伪造 Diff。
- 保存 `oracle.yaml`、工具证据和人工裁决。
- 实现 Finding Schema、风险路由和提示注入本地守卫。

### 验证

- PR-02：当时全部测试通过，说明测试通过不能证明货币类型安全。
- PR-03：授权回归测试失败，未抛出 `UnauthorizedTransfer`。
- PR-04：两笔并发转账均成功，稳定复现双花。
- PR-08：本地守卫生成 `AGENTSEC-001` 并要求人工处理。

## 2026-08-16 13:27：多 Agent 离线回放

### Git

- 提交：`7a4f717 feat: add offline multi-agent review replay`。
- 报告提交：`de71cdb docs: record first PR-04 replay result`。

### 实施

- 实现专业 Agent 协议和 Recorded Agent。
- 实现 Finding 去重、证据合并和策略仲裁。
- 实现 `single`、`multi`、`multi_arbitrated` 三种回放模式。

### 结果

- 单 Agent 只报告固定休眠的性能问题，漏掉并发根因。
- 正确性 Agent 和测试 Agent 分别提供源码证据与失败测试证据。
- 仲裁合并重复 Finding；高风险策略输出 `escalate`。
- 详情见 `evaluation/reports/pr04-first-run.md`。

## 2026-08-16：网络与 Clash 排查

### 现象

- `uv` 和 `uvx` 访问 PyPI 时出现 DNS 解析失败。
- 初次从进程监听信息误将 Clash Verge 应用端口 `33331` 当成代理端口，HTTPS CONNECT 返回 404。

### 修正

- 从 Clash Verge 生成配置确认端口：Mixed `7897`、SOCKS `7898`、HTTP `7899`、控制 API `9097`。
- 使用 `curl -x http://127.0.0.1:7897` 访问 PyPI，返回 HTTP 200，确认 Mixed 端口可用。
- 后续只在正常网络失败时临时注入 `HTTP_PROXY` 和 `HTTPS_PROXY`，不写入项目或全局配置。

## 2026-08-16 13:35：Semgrep 与实时模型适配器

### Git

- 提交：`79b63bd feat: add live Responses adapter and static evidence`。

### Semgrep

- 通过 Clash 下载并运行 Semgrep 1.173.0。
- 首次验证发现 `semgrep.yml` 中带冒号的模式没有整体引用，导致 YAML 无效。
- 修正规则后，`semgrep --validate` 确认两条规则有效。
- PR-02 命中 `wallet-float-money`；PR-08 命中 `wallet-review-instruction-in-source`。
- PR-03、PR-04 不在这两条规则的声明能力范围内，分别由授权测试和并发测试负责。

### 实时适配器

- 按官方 OpenAI Structured Outputs 文档实现 Responses API 适配器。
- 使用 JSON Schema 约束 Finding 输出。
- API Key 只从环境变量读取；缺少 Key 时拒绝实时运行。
- 使用注入式假 HTTP 传输完成请求结构和响应解析测试，没有发送真实模型请求。

## 2026-08-16 13:37：四案例评测控制面

### Git

- 提交：`8d1f174 feat: add four-case evaluation control plane`。

### 实施

- 为四个案例补齐录制 Agent 输出。
- 实现基于 Finding ID 的 Precision、Recall、TP、FP、FN 评分。
- 加入环境模板和密钥忽略规则。

### 结果

| 模式 | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| 录制单 Agent | 0 | 1 | 4 | 0.00 | 0.00 |
| 录制多 Agent + 仲裁 | 4 | 0 | 0 | 1.00 | 1.00 |

上述数据仅验证控制面。多 Agent 输出按标准答案录制，不能用作模型能力结论。详情见 `evaluation/reports/recorded-suite-first-run.md`。

## 当前验证快照（更新于 2026-08-25）

截至日志建立时：

- 38 个测试通过。
- Ruff 通过。
- 严格 mypy 通过。
- API 覆盖率 100%，综合覆盖率 89.37%，门槛为 85%。
- Semgrep 配置验证通过，共 2 条教学规则。
- 评测控制面已覆盖五个案例；录制多 Agent + 仲裁可处理 5 个标准 Finding。
- Git `main` 工作区干净。
- 环境未配置模型 API Key，尚无实时模型评测数据。

## 后续日志要求

每次重要实验追加记录：

1. 日期、Git SHA、模型和工具版本。
2. 执行命令、输入案例和运行模式。
3. 成功、失败或跳过状态及原因。
4. Token、延迟、成本和原始结果路径。
5. 与上次结果的差异和处理决定。

## 2026-10-20：第九章扩写收口与遗留事项登记

### 正文与仓库状态

- `docs/chapter-09-rewrite-draft.md` 已扩写至 45,081 中文字符，达到 45,000～55,000 字符目标。
- 扩写内容覆盖 9.1～9.10、七个教学案例、证据链、生产迁移、评分、成本、路由、上线、练习和出版检查。
- 最新主分支提交为 `9912597`，工作区干净。
- 远程 `origin/main` 已确认指向 `9912597cce78a4aa6fed25189c203b48ec4f64c4`。

### 验证结果

- `make check` 通过：Ruff、mypy、38 个 pytest 全部通过。
- 综合覆盖率为 89.73%，超过 85% 门槛。
- GitHub Actions 的 `deterministic-checks` 已通过。
- GitHub Actions 的 `osv-scanner` 仍失败：扫描发现依赖漏洞，且私有仓库未启用 Code Scanning，SARIF 上传失败。

### 遗留事项

- 修复 OSV 依赖与 SARIF 上传策略。
- 获得 API Key 后完成双模型真实评测，保存模型版本、提示词、原始输出、Token、延迟、成本和波动数据。
- 扩展评分器，加入位置、证据、严重性、修复建议和重复率维度。
- 完成 PR-03、PR-04、PR-05、PR-08 截图、实验图表和最终出版编辑。
- 确认扩写稿替换上层原稿，并同步最终稿到 IMA 笔记本“Agent图书写作”。
- 若项目要声称覆盖更广泛安全与工程场景，需要新增案例和 Oracle；当前章节继续保留明确的覆盖边界。

## 2026-08-16：建立仓库内执行基线

### 实施

- 将上位方案提炼为 `docs/execution-plan.md`，纳入本仓库版本管理。
- 定义交付范围、实施原则、角色权限、案例规范、阶段计划和验收规则。
- 建立“方案项 → 实现 → 验证证据 → 报告记录 → Git SHA”追踪矩阵。

### 目的

解决上位方案位于仓库之外、无法随代码版本同步演进的问题。上位方案继续负责图书层面的完整论证，仓库内方案负责工程实施与验收。

## 2026-08-16：API、修复证据、CI 与 PR-05

### API 质量

- 将 API 改为可注入仓储的应用工厂，避免测试共享全局状态。
- 增加正常转账、幂等、身份、越权、金额、未知钱包和余额不足测试。
- API 覆盖率达到 100%，综合覆盖率达到 89.37%，门槛设为 85%。
- 验证快照：36 个测试通过，Ruff 和严格 mypy 通过。

### P0 修复证据

- 为四个 P0 案例建立真实 `fix/pr-*` 分支。
- 通过 `git revert` 生成修复提交，再用 `git format-patch` 生成 `fixed.patch`。
- 四个修复分支对应测试均通过。
- 为测试与 Semgrep 结果保存原始证据快照。

### CI 安全门禁

- 确认 OSV Scanner Action 最新发布为 v2.5.0，并固定官方提交 SHA。
- CI 加入 Semgrep 配置验证、源码扫描、高风险人工升级测试和提示注入策略测试。
- 首次专项测试被全局覆盖率门槛错误阻断；增加 `--no-cov` 后专项步骤通过，完整测试仍单独执行 85% 门槛。
- OSV 与 Semgrep 的远程工作流仍需仓库推送 GitHub 后首次验收。

### PR-05 幂等重试

- 缺陷提交：`dec5045 case: remove idempotent retry lookup`。
- 修复提交：`ef46eb4 Revert \"case: remove idempotent retry lookup\"`。
- 删除幂等命中检查后，同一请求重试产生不同转账 ID，回归测试稳定失败。
- 已补齐需求、Oracle、错误补丁、修复补丁、原始证据、人工裁决和录制 Agent 输出。

## 2026-08-25：PR-01、PR-07 与事实核验

### 状态修正

- 将当前验证快照更新为 38 个测试、API 覆盖率 100%、综合覆盖率 89.37%。
- 历史“四案例”事件保持原样，当前评测控制面更新为六个缺陷 Finding。

### PR-01 低风险文档案例

- 缺陷/变更提交：`9dae8b4 docs: clarify transfer response identifier`。
- 对照撤销提交：`e47f09d Revert \"docs: clarify transfer response identifier\"`。
- 该案例不植入缺陷，Oracle 为空。
- 风险得分为 -3，只运行 `general-review`，零 Finding，最终结论为 `approve`。

### PR-07 依赖降级案例

- 安全审计基线：`requests 2.33.0`。
- 风险提交：`12860d9 case: downgrade requests to vulnerable release`。
- 修复提交：`a704d3d Revert \"case: downgrade requests to vulnerable release\"`。
- OSV Query 对 `2.19.1` 返回多个公告，包括 HIGH `GHSA-x84v-xcm2-53pg / CVE-2018-18074`；对 `2.33.0` 返回空对象。
- OSV Scanner v2.5.1 官方二进制在当前受限环境中以 137 终止，因此本地证据改用同一数据源的 OSV Query API；远程 CI 仍使用官方 Action。
- 相同漏洞的 GHSA、CVE、PYSEC 别名不重复计为多个 Finding。

### 事实核验

- 建立 `references/source-audit.csv`，首批录入 22 条精确数字、厂商能力、模型名称和强结论。
- 明确将错误模型名、图指标混淆和无来源行业阈值标为删除或重写。
- 厂商披露、缓存折扣和工具压缩数据保持 `pending`，未作为事实写入新稿。

## 2026-08-25：第 9 章技术初稿

### 正文

- 新增 `docs/chapter-09-rewrite-draft.md`，保留上层原稿不动，便于技术审校和对照。
- 按十节结构重写能力边界、证据流水线、角色权限、风险路由、仲裁、成本、评测和安全治理。
- 将 PR-01、02、03、04、05、07、08 映射为教学素材，PR-04 作为贯穿实战。
- 加入 Finding JSON 示例、Mermaid 架构图和评审时序图源码。

### 边界

- 未引用 `source-audit.csv` 中处于 `pending`、`rewrite` 或 `remove` 的精确数字和产品断言。
- 录制回放数据只用于说明编排与评分控制面，没有写成真实模型能力。
- 真实模型的 Token、延迟、成本、Precision 和 Recall 保留明确占位，等待 API Key 后填充。

### 验证

- 正常网络因 DNS 失败，沙箱内访问 Clash 又被拒绝；获得单次权限后，仅对 `uv sync --extra dev` 临时设置 `127.0.0.1:7897` 代理，未持久化代理配置。
- `uv run pytest`：38 个测试通过，综合覆盖率 89.37%。
- `uv run ruff check .`：通过。
- `uv run mypy app review_system evaluation`：17 个源文件严格检查通过。
- `git diff --check`：通过。

## 2026-08-25：正文技术审校

- 新增 `docs/chapter-09-technical-review.md`，建立原稿知识点到新稿的覆盖矩阵和替换门槛。
- 修正目标架构与当前 MVP 边界、PR-04 根因位置、高风险 `escalate` 裁决、`credentials` 标签和 `deterministic-only` 实现状态。
- 补入 PR 摘要与影响范围分析方法，明确当前项目不声称已实现跨仓库分析。
- 干净环境首次回放发现 `single` 和 `multi` 模式未应用高风险人工门禁；将风险裁决与评审模式解耦，三种模式现在都会将 PR-04 升级为 `escalate`。

### 干净环境复现

- 从本地 `main` 克隆到新建的 `/private/tmp` 目录，不复用开发工作树的 `.venv`。
- 两次克隆后的首条组合命令都在临时父目录执行 `uv sync`，因找不到 `pyproject.toml` 立即退出；修正工作目录到 `repo/` 后继续，该失败不属于项目缺陷。
- 正常网络仍因 DNS 失败，仅依赖安装步骤临时使用 Clash `127.0.0.1:7897`，未写入任何配置。
- 最终干净克隆使用 Python 3.13.13；Ruff 通过，mypy 严格检查 17 个源文件通过，38 个测试通过，覆盖率 90.65%。
- PR-04 的 `single`、`multi`、`multi_arbitrated` 三种回放均输出 `escalate`；只有仲裁模式合并了重复 Finding 和证据。

## 2026-08-25：状态与事实审计收口

- 修正执行方案中已过期的 API 测试、P1 案例、修复补丁、原始证据和案例计数状态。
- 根据新稿实际内容收口 22 条原稿声明：6 条重写、14 条删除、2 条转为本地实验，不再保留 `pending` 厂商或工具断言。
- 发现 `source-audit.csv` 部分历史行缺少空字段，导致 `status` 与 `action` 错位；已统一修正为 12 列并通过 Ruby CSV 解析校验。
- 再次扫描新稿，未发现 DIDACT、BAZINGA、Calimero、CodeRabbit、RTK、JCodeMunch 或被删除的百分比。

## 2026-08-25：首批出版图片

- 通过 Clash 临时下载 Mermaid CLI 11.16.0，跳过 Puppeteer 自带浏览器下载并复用本机 Chrome；未在仓库或系统中新增持久代理配置。
- 新增 `docs/figures/`，保存图 9-1 证据流水线和图 9-2 PR-04 评审时序的 Mermaid 源码、统一主题和渲染说明。
- 每张图生成 SVG 出版资产和 2 倍 PNG 预览资产；图 9-1 为 1568×164，图 9-2 为 1568×680。
- 首版图 9-1 比例过度扁平，两行布局又被 Mermaid 解释为纵长图；最终改为四阶段紧凑流程并重新渲染。
- 通过文件类型、像素尺寸、SVG 文本检查和 PNG 肉眼验收；两张图中文正常，无裁切或重叠。
## 2026-08-25：按原 9.1–9.10 结构启动案例驱动扩写

### 决策

- 保留原章 9.1–9.10 的知识推进顺序，不再按工程模块重新编号。
- PR-04 并发双花作为贯穿主线；PR-03、PR-05、PR-08 作为完整辅案例；PR-01、PR-02、PR-07 用于低风险、金额精度和外部漏洞事实对照。
- 顶层原稿暂不覆盖，扩写继续落在 `docs/chapter-09-rewrite-draft.md`。

### 本轮结果

- 恢复全部 9.1–9.10 原主题标题。
- 补入钱包案例选择理由、PR-04 并发时序与根因去重、PR-03 对象授权、PR-05 幂等重试、PR-08 提示注入、零缺陷样本和真实模型实验边界。
- 草稿由约 6,000 字符的结构稿扩展到约 9,500 字符；已形成案例驱动初版，但尚未达到 20,000～26,000 中文字符的出版目标。
- 下一轮只补可验证素材：错误 Diff、测试输出、Finding、人工裁决、修复验证和实验表，不用泛化论述填充篇幅。

### 校验

- 9.1–9.10 标题完整。
- 未重新引入事实审计中已标记删除或改写的产品指标与无来源数字。
- `git diff --check` 通过。

## 2026-10-20：第九章拆分为可重复生成的子章节文档

### 结构

- 新增 `docs/chapter-09/00-overview.md` 作为章节概述。
- 新增 `docs/chapter-09/01`～`10`，分别对应 9.1～9.10。
- 新增 `docs/chapter-09/11-project-cases.md`，将七个项目案例、实战练习和生产迁移内容集中为独立子章节。
- 保留 `docs/chapter-09-rewrite-draft.md` 作为唯一内容来源，避免合并稿与拆分稿长期漂移。

### 生成与校验

- 新增 `scripts/split_chapter09.rb`，负责从合并稿生成目录、概述、十个主题文档和项目案例文档。
- 脚本会检查生成文件非空，并校验原稿二级章节均已分配。
- 回读确认：生成 13 份文档；原稿 45,081 字符，拆分稿正文合计 45,304 字符；`git diff --check` 通过。
- 回读确认：完整 PR-03、PR-04、PR-05、PR-08 案例只放在项目案例文档；主题章节保留必要的证据链引用，不重复维护完整案例。

## 2026-11-05：统一新版书稿入口并清理旧资产

- 依据作者指定的 IMA 最新稿和订单案例迁移规划，删除 63 个过时文件：2026-10-20 归档 41 个、旧拆分稿 13 个、旧原稿/合并稿/规划/审校记录 8 个、旧拆分脚本 1 个。
- 最新 IMA 十二节、导语、配套材料、富文本、原始来源和 manifest 均保持原样；保留可运行的钱包代码、测试、案例补丁、工具证据、架构决策及可复用图片。
- 更新根目录、实验工程与文档索引；现行实施方案统一指向订单迁移规划。图片和旧事实核验表注明历史适用范围。
- 被删除内容可在清理前提交 `a705616` 查看；本日志中的历史记录不作为现行书稿入口。
- 校验：40 份 Markdown 中的 51 个本地链接可访问，最新 IMA 目录逐文件与清理前版本一致，`uv run pytest --no-cov -q` 的 38 项测试通过，`git diff --check` 通过。

## 2026-11-05：订单工程与书稿迁移

- 采用 ADR-004，新建 Java 17 四模块订单工程、MyBatis/Flyway 和真实 MySQL 测试；业务口径在订单 ADR-001 冻结。
- 冻结案例基线 `7a61a4f`：8 项核心测试和 10 项集成测试通过。主线补充历史快照格式漂移的人工核对回归后，共 19 项 Java 测试通过；核心/聚合行覆盖率分别为 90%/96.45%。
- 建立 ORD-01～ORD-12 独立错误及修复分支，保存真实测试、依赖公告、静态扫描、版本和哈希。ORD-09 实际少退 200 分；ORD-04 为缺失单位状态门禁，ORD-05 为重试响应协议错误，均按实际结果编写。
- Python 增加项目清单、规则/证据上下文、Finding v2、强制路径门禁、根因去重和逐案例匹配。46 项测试通过，覆盖率 90.23%；业务执行器另有凭据环境隔离测试通过。
- 导语与十二节迁移到订单主线，同步 Markdown/富文本和 manifest，16 份原始 IMA 来源未修改。9.6/9.7 对照继续合并，迁移前结构与审校报告标明历史适用范围。
- 新增章节—案例追踪表、退款图示、Java/书稿 CI 与真实 HTTP 验证记录。临时服务和数据库在验证后停止。
- 真实模型重复实验、人工批准及最终出版审校仍待完成，见 [迁移状态](../../docs/migration-status.md)。

- 依历史 OSV 报告升级 certifi/pytest 并约束教学清单的 idna；重新适配旧 PR-07 补丁上下文。OSV 改为直接扫描两个工程、保留 JSON artifact，继续将漏洞视为失败，避免未启用 Code Scanning 导致报告上传失败。
- 远端 OSV 无法从单个模块 POM 解析 reactor 内部依赖，改为 Maven 生成聚合 CycloneDX SBOM 后扫描传递依赖；教学清单固定版本以便扫描器精确查询。
- OSV Scanner 在本地/远端均返回空结果，直接 API 仍发现 Java 公告，遂补充含已知漏洞控制样本的 API 门禁，并升级可用补丁。两个未使用 Spring 视图功能的公告以完整 PURL、生产源码哈希及 2026-12-05 复查期限限定适用性；不将扫描器空结果表述为无漏洞。

## 2026-11-06：出版改写第一版

- 根据出版视角审阅重写导语与十二节，扩大单 Agent、多角色、主实战、成本和端到端教学；精简外部综述及未追溯数字，统一九项参考来源。
- 新增四张本地架构/时序/状态/安全图，提供 Mermaid、SVG、PNG 与主题。Python 正文示例和录制模式实际执行，成本按十进制复算，图表和章节引用统一。
- Markdown 与富文本同步，16 份原始来源及全部冻结工程证据保持不变；云端 IMA 没有修改。真实模型实验与人工批准仍未完成，见 [本版说明](../../docs/publication-rewrite-2026-11-06.md)。

## 2026-11-06：出版扩写第二版

- 按作者反馈，以图书的认识顺序继续扩写导语与十二节，增加生活场景、概念解释、角色协作、设计选择及迁移说明。
- 部分字段与接口解释前移，合并重复导入；保留现有可运行示例、图表及真实证据边界。
- 同步 Markdown/富文本与来源哈希，记录逐节变化和统计；原始 IMA、业务源码与案例资产保持原样，详见[第二版说明](../../docs/publication-expansion-2026-11-06.md)。
