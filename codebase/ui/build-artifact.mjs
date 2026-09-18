/* Produces artifact/page.html from index.html.
   A published Artifact supplies its own doctype, html, head and body, so the page file must
   contain only the content. Everything else is published alongside it unchanged, which is
   why there is no bundler here and no build output to keep in sync.

   Run: node build-artifact.mjs */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const src = readFileSync("index.html", "utf8");

const page = src
  .replace(/^<!doctype html>\s*/i, "")
  .replace(/<html[^>]*>\s*/i, "")
  .replace(/<\/html>\s*$/i, "")
  .replace(/<head>\s*/i, "")
  .replace(/<\/head>\s*/i, "")
  .replace(/<body>\s*/i, "")
  .replace(/<\/body>\s*/i, "")
  .replace(/<meta charset="utf-8">\s*/i, "")
  .replace(/<meta name="viewport"[^>]*>\s*/i, "")
  .trim();

if (!/<title>/.test(page)) throw new Error("page lost its title");
if (/<body|<html|<!doctype/i.test(page)) throw new Error("wrapper survived the strip");

mkdirSync("artifact", { recursive: true });
writeFileSync("artifact/page.html", page + "\n");
console.log(`artifact/page.html written, ${page.length} chars`);
