import fs from "node:fs";
import path from "node:path";

const IMPORT_RE = /^\s*@import\s+(?:url\()?["']([^"']+)["']\)?\s*;?\s*$/;

export function readCombinedCssSource(filePath, seen = new Set()) {
  const resolvedPath = path.resolve(filePath);
  if (seen.has(resolvedPath)) {
    return "";
  }

  seen.add(resolvedPath);

  const source = fs.readFileSync(resolvedPath, "utf8");
  const directory = path.dirname(resolvedPath);
  const pieces = [];

  for (const line of source.split(/\r?\n/)) {
    const match = line.match(IMPORT_RE);
    if (!match) {
      pieces.push(line);
      continue;
    }

    const importTarget = match[1];
    if (/^(?:[a-z]+:)?\/\//i.test(importTarget)) {
      pieces.push(line);
      continue;
    }
    const nextPath = importTarget.startsWith("/")
      ? path.resolve(directory, `.${importTarget}`)
      : path.resolve(directory, importTarget);
    pieces.push(readCombinedCssSource(nextPath, seen));
  }

  return pieces.join("\n");
}
