#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";

const IMA_CLI = process.env.IMA_CLI_PATH || path.join(os.homedir(), ".agents/skills/ima-skill/ima_api.cjs");
const NOTEBOOK = "Agent图书写作";
const OUTPUT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../wallet-review-lab/docs/ima-sources");
const requestedDate = process.argv[2];
const timeZone = process.argv[3] || "Europe/Istanbul";
const dryRun = process.argv.includes("--dry-run");

if (!/^\d{4}-\d{2}-\d{2}$/.test(requestedDate || "")) {
  throw new Error("Usage: export_ima_notes.mjs YYYY-MM-DD [TIME_ZONE] [--dry-run]");
}

function api(endpoint, body) {
  const output = execFileSync(
    process.execPath,
    [IMA_CLI, endpoint, JSON.stringify(body)],
    { encoding: "utf8", maxBuffer: 100 * 1024 * 1024, env: process.env },
  );
  const response = JSON.parse(output);
  if (response.code !== 0) throw new Error(response.msg || `IMA API error ${response.code}`);
  return response.data;
}

function page(endpoint, initialBody, itemsKey, cursorStart) {
  const items = [];
  let cursor = cursorStart;
  const seen = new Set();
  do {
    if (seen.has(cursor)) throw new Error(`Repeated pagination cursor: ${cursor}`);
    seen.add(cursor);
    const data = api(endpoint, { ...initialBody, cursor });
    items.push(...(data[itemsKey] || []));
    if (data.is_end) break;
    cursor = data.next_cursor || String(Number(cursor || 0) + (data[itemsKey] || []).length);
  } while (true);
  return items;
}

function localDate(milliseconds) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(Number(milliseconds)));
}

function localTime(milliseconds) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(Number(milliseconds))).replace(":", "");
}

function inline(nodes = [], marks = ["bold", "italic", "strike"]) {
  if (marks.length) {
    const [mark, ...rest] = marks;
    const groups = [];
    for (const node of nodes) {
      const enabled = Boolean(node[mark] || (mark === "strike" && node.strikethrough));
      if (!groups.length || groups.at(-1).enabled !== enabled) groups.push({ enabled, nodes: [] });
      groups.at(-1).nodes.push(node);
    }
    return groups.map((group) => {
      const value = inline(group.nodes, rest);
      if (!group.enabled || !value.trim()) return value;
      const marker = { bold: "**", italic: "*", strike: "~~" }[mark];
      return value.replace(/^(\s*)([\s\S]*?)(\s*)$/, (_, before, body, after) => `${before}${marker}${body}${marker}${after}`);
    }).join("");
  }
  return nodes.map((node) => {
    if (node.type === "br") return "  \n";
    let value = node.text ?? inline(node.children || []);
    if (node.code) {
      const fence = "`".repeat(Math.max(0, ...(value.match(/`+/g) || []).map((run) => run.length)) + 1);
      const padding = value.startsWith("`") || value.endsWith("`") ? " " : "";
      value = `${fence}${padding}${value}${padding}${fence}`;
    }
    const href = node.href || node.url || node.link;
    if (href) value = `[${value}](${href})`;
    return value;
  }).join("");
}

function textContent(node) {
  if (typeof node?.text === "string") return node.text;
  return (node?.children || []).map(textContent).join("");
}

function table(node, unknownTypes) {
  const rows = (node.children || []).filter((child) => child.type === "tr").map((row) =>
    (row.children || []).filter((cell) => cell.type === "td" || cell.type === "th").map((cell) =>
      (cell.children || []).map((child) => renderBlock(child, unknownTypes)).join("<br>")
        .replaceAll("\n", " ").replaceAll("|", "\\|").trim(),
    ),
  );
  if (!rows.length) return "";
  const width = Math.max(...rows.map((row) => row.length));
  const normalized = rows.map((row) => [...row, ...Array(width - row.length).fill("")]);
  return [
    `| ${normalized[0].join(" | ")} |`,
    `| ${Array(width).fill("---").join(" | ")} |`,
    ...normalized.slice(1).map((row) => `| ${row.join(" | ")} |`),
  ].join("\n");
}

function renderBlock(node, unknownTypes) {
  const content = inline(node.children || []);
  switch (node.type) {
    case "h1": return `# ${content}`;
    case "h2": return `## ${content}`;
    case "h3": return `### ${content}`;
    case "h4": return `#### ${content}`;
    case "h5": return `##### ${content}`;
    case "h6": return `###### ${content}`;
    case "p": {
      if (node.listStyleType === "disc" || node.listStyleType === "circle" || node.listStyleType === "square") {
        return `${"  ".repeat(Math.max(0, (node.indent || 1) - 1))}- ${content}`;
      }
      if (node.listStyleType === "decimal") {
        return `${"  ".repeat(Math.max(0, (node.indent || 1) - 1))}${node.listStart || 1}. ${content}`;
      }
      return content;
    }
    case "blockquote":
    case "quote": return content.split("\n").map((line) => `> ${line}`).join("\n");
    case "hr": return "---";
    case "table": return table(node, unknownTypes);
    case "code":
    case "code_block": {
      const language = node.language || node.lang || node.attrs?.language || "";
      const code = (node.children || []).some((child) => child.type === "code_line")
        ? node.children.map(textContent).join("\n") : textContent(node);
      const fence = "`".repeat(Math.max(2, ...(code.match(/`+/g) || []).map((run) => run.length)) + 1);
      return `${fence}${language}\n${code}\n${fence}`;
    }
    case "image": {
      const url = node.url || node.src || node.attrs?.url || node.attrs?.src || "";
      const alt = node.alt || node.attrs?.alt || "图片";
      return url ? `![${alt}](${url})` : "";
    }
    default:
      unknownTypes.add(node.type || "<missing>");
      return content || textContent(node);
  }
}

function markdownFromRichText(content) {
  const document = JSON.parse(content);
  const unknownTypes = new Set();
  const markdown = document.map((node) => renderBlock(node, unknownTypes)).filter(Boolean).join("\n\n") + "\n";
  return { markdown, unknownTypes: [...unknownTypes].sort() };
}

function safeName(title) {
  return title.normalize("NFKC").replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ").trim();
}

if (process.argv.includes("--from-local")) {
  const directory = path.join(OUTPUT_ROOT, requestedDate);
  const files = fs.readdirSync(directory).filter((filename) => filename.endsWith(".ima.json"));
  for (const filename of files) {
    const rendered = markdownFromRichText(fs.readFileSync(path.join(directory, filename), "utf8"));
    if (rendered.unknownTypes.length) throw new Error(`Unsupported nodes in ${filename}`);
    if (!dryRun) fs.writeFileSync(path.join(directory, filename.replace(/\.ima\.json$/, ".md")), rendered.markdown);
  }
  console.log(JSON.stringify({ status: "rerendered", count: files.length }));
  process.exit(0);
}

const folders = page(
  "openapi/note/v1/list_notebook",
  { limit: 20 },
  "note_folder_infos",
  "0",
);
const folder = folders.find((item) => item.name === NOTEBOOK);
if (!folder) throw new Error(`Notebook not found: ${NOTEBOOK}`);

const notes = page(
  "openapi/note/v1/list_note",
  { folder_id: folder.folder_id, sort_type: 1, limit: 20 },
  "note_book_list",
  "",
).filter((note) => localDate(note.create_time) === requestedDate)
  .sort((left, right) => Number(left.create_time) - Number(right.create_time));

if (!notes.length) throw new Error(`No notes created on ${requestedDate} in ${NOTEBOOK}`);

const exported = notes.map((note) => {
  const data = api("openapi/note/v1/get_doc_content", {
    note_id: note.note_id,
    target_content_format: 2,
  });
  const rendered = markdownFromRichText(data.content);
  return {
    richText: JSON.parse(data.content),
    title: note.title,
    createTime: note.create_time,
    filename: `${localTime(note.create_time)}-${safeName(note.title)}.md`,
    ...rendered,
  };
});

const unknown = exported.filter((note) => note.unknownTypes.length);
if (unknown.length) {
  const details = unknown.map((note) => `${note.title}: ${note.unknownTypes.join(", ")}`).join("\n");
  throw new Error(`Unsupported rich-text node types:\n${details}`);
}

if (!dryRun) {
  const outputDirectory = path.join(OUTPUT_ROOT, requestedDate);
  fs.mkdirSync(outputDirectory, { recursive: true });
  for (const note of exported) {
    fs.writeFileSync(path.join(outputDirectory, note.filename), note.markdown, "utf8");
    fs.writeFileSync(path.join(outputDirectory, note.filename.replace(/\.md$/, ".ima.json")), JSON.stringify(note.richText, null, 2) + "\n", "utf8");
  }
  const index = [
    `# IMA「${NOTEBOOK}」${requestedDate} 新建文章`,
    "",
    `共 ${exported.length} 篇，按创建时间排序。正文由 IMA JSON 富文本导出为 Markdown，保留标题、列表、表格、代码和行内样式。同名 .ima.json 保存原始富文本结构、单元格和布局属性，便于完整回溯。`,
    "",
    ...exported.map((note) => `- [${note.title}](${encodeURI(note.filename)})`),
    "",
  ].join("\n");
  fs.writeFileSync(path.join(outputDirectory, "README.md"), index, "utf8");
}

console.log(JSON.stringify({
  status: dryRun ? "validated" : "exported",
  date: requestedDate,
  timeZone,
  count: exported.length,
  files: exported.map((note) => note.filename),
}, null, 2));
