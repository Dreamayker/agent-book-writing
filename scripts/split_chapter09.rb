#!/usr/bin/env ruby

require "fileutils"
require "pathname"

ROOT = Pathname.new(__dir__).parent
SOURCE = ROOT / "wallet-review-lab/docs/chapter-09-rewrite-draft.md"
OUTPUT = ROOT / "wallet-review-lab/docs/chapter-09"

lines = SOURCE.readlines

def blocks(lines, level)
  marker = "#" * level + " "
  starts = lines.each_index.select { |index| lines[index].start_with?(marker) && !lines[index].start_with?(marker + "#") }
  starts.each_with_index.to_h do |start, position|
    finish = starts[position + 1] || lines.length
    title = lines[start].delete_prefix(marker).strip
    [title, lines[(start + 1)...finish]]
  end
end

def body(blocks, title)
  blocks.fetch(title).join.sub(/\A\n+/, "").sub(/\s+\z/, "")
end

def section(blocks, title)
  "## #{title}\n\n#{body(blocks, title)}"
end

def split_examples(content, titles)
  pieces = content.split(/(?=^### (?:#{titles.map { |title| Regexp.escape(title) }.join('|')}))/)
  [pieces.first.strip, pieces.drop(1).map(&:strip)]
end

def deep_body(publication_lines, number)
  start_pattern = /^### #{Regexp.escape(number)} / 
  start = publication_lines.index { |line| line.match?(start_pattern) }
  raise "Missing deep section #{number}" unless start

  finish = ((start + 1)...publication_lines.length).find do |index|
    publication_lines[index].match?(/^### 9\.\d+ /)
  end || publication_lines.length

  selected = publication_lines[start...finish]
  heading = selected.shift.sub(/^### #{Regexp.escape(number)}\s*/, "").strip
  content = selected.join.sub(/^#### /, "### ").gsub(/^#### /, "### ").strip
  "## #{heading}\n\n#{content}"
end

def join_sections(*sections)
  sections.flatten.compact.reject(&:empty?).join("\n\n") + "\n"
end

def promote_base_headings(content)
  content.gsub(/^#### /, "@@@ ").gsub(/^### /, "## ").gsub(/^@@@ /, "### ")
end

def document(title, *sections)
  join_sections("# #{title}", "[返回第 9 章目录](README.md)", sections)
end

h2 = blocks(lines, 2)
publication = h2.fetch("出版扩展：把每一次评审变成可验证的任务")
publication_intro = publication.take_while { |line| !line.start_with?("### 9.1 ") }.join.strip

chapter_titles = {
  "9.1" => "AI 适合评审什么，不适合评审什么",
  "9.2" => "评审 Agent 的四类任务",
  "9.3" => "多 Agent 协同评审",
  "9.4" => "测试、评审、安全 Agent 的协同",
  "9.5" => "投票制、仲裁制和人工裁决",
  "9.6" => "PR 摘要、影响分析和风险标注",
  "9.7" => "误报率和漏报率",
  "9.8" => "多 Agent 成本边界",
  "9.9" => "Token 成本与触发策略",
  "9.10" => "如何评测代码评审 Agent"
}

extras = {
  "9.1" => ["可直接采用的评审契约模板"],
  "9.2" => [],
  "9.3" => ["评审数据的隐私与保留"],
  "9.4" => ["生产实施参考：证据对象与运行目录", "证据阅读方法：先读事实，再读解释", "附录：一次完整评审的交付清单"],
  "9.5" => ["人工裁决样例与责任边界"],
  "9.6" => [],
  "9.7" => ["指标解释：数字背后必须有分母"],
  "9.8" => [],
  "9.9" => [],
  "9.10" => ["实验设计参考：从回放到可发表结果", "上线检查与回滚剧本", "运行失败时的决策树", "给评审团队的复盘问题", "团队落地路线：四周试点法"]
}

overview_sections = [
  lines.take_while { |line| !line.start_with?("## ") }.drop(1).join.strip,
  section(h2, "开篇：先定义“正确”，再讨论“智能”"),
  "## 出版扩展：把每一次评审变成可验证的任务\n\n#{publication_intro}",
  *["章末检查表", "最终检查表", "反模式目录：看似合理但会破坏证据闭环",
    "维护计划：章节、工程和案例如何长期同步", "章节成果的验收方法",
    "章节边界声明", "最终出版前的机械检查", "迁移前的风险问卷",
    "章节结束语：把速度花在证据上"].map { |title| section(h2, title) }
]

case_sections = [
  *["实战案例阅读路线", "扩展实战：一套可重复的盲审练习",
    "本章新增读者产出", "案例档案一：PR-01 为什么“没有问题”也需要证据",
    "案例档案二：PR-02 金额精度不是显示格式问题",
    "案例档案三：PR-03 从认证成功到对象授权",
    "案例档案四：PR-04 用确定性时序复现并发双花",
    "案例档案五：PR-05 幂等性是服务端状态协议",
    "案例档案六：PR-07 依赖漏洞需要适用性分析",
    "案例档案七：PR-08 仓库内容不能成为控制指令",
    "从七个案例抽象出的工程不变量", "生产迁移：教学钱包与真实系统的差距",
    "七个案例的对照矩阵", "章末练习与讨论题",
    "读者练习参考答案要点"].map { |title| section(h2, title) }
]

case_snippets = {}
{"9.3" => ["PR-04：从错误 Diff 到评审结论"],
 "9.4" => ["PR-03：对象级授权绕过", "PR-05：幂等重试导致重复扣款"],
 "9.10" => ["PR-08：评审系统也需要被评审"]}.each do |number, titles|
  source = body(h2, "#{number} #{chapter_titles.fetch(number)}")
  base, snippets = split_examples(source, titles)
  if number == "9.4"
    # The Finding Schema follows the two case examples and stays with the tool chapter.
    finding = snippets.last.split(/(?=^### 统一 Finding Schema)/)
    snippets[-1] = finding.first.strip
    base = join_sections(base, finding.last.strip).strip
  elsif number == "9.10"
    experiment = snippets.last.split(/(?=^### 从回放走向真实模型实验)/)
    snippets[-1] = experiment.first.strip
    base = join_sections(base, experiment.last.strip).strip
  end
  case_snippets[number] = { base: base, snippets: snippets }
end

case_sections = case_sections.flat_map do |section|
  case_excerpt = if section.start_with?("## 案例档案三：")
           case_snippets.fetch("9.4")[:snippets].first
         elsif section.start_with?("## 案例档案四：")
           case_snippets.fetch("9.3")[:snippets].first
         elsif section.start_with?("## 案例档案五：")
           case_snippets.fetch("9.4")[:snippets].last
         elsif section.start_with?("## 案例档案七：")
           case_snippets.fetch("9.10")[:snippets].first
         end
  case_excerpt ? [section, case_excerpt.sub(/\A### /, "## ")] : [section]
end

assigned = overview_sections.map { |section| section[/\A## (.+)$/, 1] }.compact
assigned += chapter_titles.map { |number, title| "#{number} #{title}" }
assigned += case_sections.map { |section| section[/\A## (.+)$/, 1] }.compact
assigned += extras.values.flatten
missing = h2.keys - assigned
raise "Unassigned source sections: #{missing.join(', ')}" unless missing.empty?

FileUtils.mkdir_p(OUTPUT)

File.write(
  OUTPUT / "00-overview.md",
  document("第 9 章概述：AI 代码评审与多 Agent 协同", overview_sections)
)

chapter_titles.each_with_index do |(number, title), index|
  base = case_snippets.dig(number, :base) || body(h2, "#{number} #{title}")
  deep = deep_body(publication, number)
  appended = extras.fetch(number).map { |name| "## #{name}\n\n#{body(h2, name)}" }
  filename = format("%02d-%s.md", index + 1, {
    "9.1" => "capability-boundaries",
    "9.2" => "review-task-types",
    "9.3" => "multi-agent-collaboration",
    "9.4" => "tool-agent-evidence-chain",
    "9.5" => "arbitration-human-decision",
    "9.6" => "summary-impact-risk",
    "9.7" => "false-positive-false-negative",
    "9.8" => "cost-boundaries",
    "9.9" => "routing-trigger-strategy",
    "9.10" => "evaluation-and-rollout"
  }.fetch(number))
  File.write(OUTPUT / filename, document("#{number} #{title}", promote_base_headings(base), deep, appended))
end

File.write(
  OUTPUT / "11-project-cases.md",
  document("9.11 项目案例：Wallet Review Lab", case_sections)
)

entries = [
  ["00-overview.md", "章节概述"],
  ["01-capability-boundaries.md", "9.1 AI 适合评审什么，不适合评审什么"],
  ["02-review-task-types.md", "9.2 评审 Agent 的四类任务"],
  ["03-multi-agent-collaboration.md", "9.3 多 Agent 协同评审"],
  ["04-tool-agent-evidence-chain.md", "9.4 测试、评审、安全 Agent 的协同"],
  ["05-arbitration-human-decision.md", "9.5 投票制、仲裁制和人工裁决"],
  ["06-summary-impact-risk.md", "9.6 PR 摘要、影响分析和风险标注"],
  ["07-false-positive-false-negative.md", "9.7 误报率和漏报率"],
  ["08-cost-boundaries.md", "9.8 多 Agent 成本边界"],
  ["09-routing-trigger-strategy.md", "9.9 Token 成本与触发策略"],
  ["10-evaluation-and-rollout.md", "9.10 如何评测代码评审 Agent"],
  ["11-project-cases.md", "9.11 项目案例：Wallet Review Lab"]
]

index = <<~MARKDOWN
  # 第 9 章拆分稿

  本目录按出版子章节拆分。`00-overview.md` 是章节概述，`01`～`10` 分别对应 9.1～9.10，`11-project-cases.md` 是独立的项目案例子章节。

  合并稿 `../chapter-09-rewrite-draft.md` 保留为内容来源。合并稿变化后，在仓库根目录运行 `ruby scripts/split_chapter09.rb` 重新生成本目录，避免两套稿件漂移。

  ## 阅读顺序

  #{entries.map { |file, label| "- [#{label}](#{file})" }.join("\n")}

  ## 编辑规则

  - 内容修改优先落到合并稿，再运行拆分脚本。
  - 不在拆分稿中单独维护重复内容。
  - 项目案例的需求、Oracle、证据和补丁仍以 `../../book-assets/` 为准。
  - 录制回放不得写成真实模型能力；未完成的真实模型实验继续明确标注。
MARKDOWN

File.write(OUTPUT / "README.md", index)

generated = entries.map(&:first) + ["README.md"]
empty = generated.select { |file| (OUTPUT / file).size.zero? }
raise "Generated empty files: #{empty.join(', ')}" unless empty.empty?

puts "Generated #{generated.length} files in #{OUTPUT}"
generated.each { |file| puts format("%7d  %s", (OUTPUT / file).size, file) }
