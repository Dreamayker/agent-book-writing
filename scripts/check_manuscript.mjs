#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const directory = path.join(root, "wallet-review-lab/docs/ima-sources/2026-11-05");
const manifest = JSON.parse(fs.readFileSync(path.join(directory, "manifest.json"), "utf8"));
let count = 0;
for (const entry of manifest.exported) {
  const stem = entry.filename.replace(/\.md$/, "");
  for (const [suffix, key] of [[".md", "markdownSha256"], [".ima.json", "richTextSha256"], [".ima.raw.json", "rawSha256"]]) {
    const filename = path.join(directory, stem + suffix);
    const content = fs.readFileSync(filename);
    const digest = createHash("sha256").update(content).digest("hex");
    if (entry[key] !== digest) throw new Error(`Manifest mismatch: ${stem + suffix}`);
    if (suffix.endsWith(".json")) JSON.parse(content.toString("utf8"));
    count++;
  }
}
console.log(`Verified ${manifest.exported.length} documents, ${count} manuscript/source hashes.`);
