import fs from "node:fs";
import vm from "node:vm";

export function readUtf8File(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

export function runInVmContext(source, context, filename) {
  vm.runInContext(source, context, { filename });
}

export function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

export function normalizeWhitespace(source) {
  return source.replace(/\s+/g, " ").trim();
}
