#!/usr/bin/env node
import fs from "fs";
import MarkdownIt from "markdown-it";
import taskLists from "markdown-it-task-lists";
import footnote from "markdown-it-footnote";
import deflist from "markdown-it-deflist";
import container from "markdown-it-container";
import mark from "markdown-it-mark";
import sub from "markdown-it-sub";
import sup from "markdown-it-sup";
import ins from "markdown-it-ins";
import abbr from "markdown-it-abbr";
import anchor from "markdown-it-anchor";
import imsize from "markdown-it-imsize";
import toc from "markdown-it-toc-done-right";
import hljs from "highlight.js";
import multimdTable from "markdown-it-multimd-table";
import implicitFigures from "markdown-it-implicit-figures";
import video from "markdown-it-video";
import linkAttrs from "markdown-it-link-attributes";
import kbd from "markdown-it-kbd";
import spoiler from "markdown-it-spoiler";
import emoji from "markdown-it-emoji";
import attrs from "markdown-it-attrs";

const md = new MarkdownIt({
  html: true,
  xhtmlOut: true,
  linkify: true,
  typographer: true,
  breaks: false,
  langPrefix: "language-",
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`;
      } catch {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  }
});

// Plugins
md.use(emoji)
  .use(taskLists, { enabled: true, label: true, labelAfter: true })
  .use(footnote)
  .use(deflist)
  .use(mark)
  .use(sub)
  .use(sup)
  .use(ins)
  .use(abbr)
  .use(kbd)
  .use(spoiler)
  .use(anchor, {
    level: [1, 2, 3, 4, 5, 6],
    permalink: anchor.permalink.ariaHidden({
      symbol: "#",
      placement: "after",
      class: "header-anchor"
    })
  })
  .use(toc, {
    containerClass: "toc",
    listType: "ol",
    level: [2, 3, 4],
    format: (heading, htmlencode) => htmlencode(heading.replace(/^\d+\.\s*/, ""))
  })
  .use(multimdTable, { multiline: true, rowspan: true, headerless: true })
  .use(implicitFigures, { figcaption: true })
  .use(video, { youtube: { width: 640, height: 390 }, vimeo: { width: 500, height: 281 } })
  .use(imsize)
  .use(linkAttrs, {
    matcher: href => href.startsWith("http"),
    attrs: { target: "_blank", rel: "noopener noreferrer" }
  })
  .use(attrs);

// Containers customizados
["note", "tip", "warning", "danger", "success", "info", "example", "caution", "important"].forEach(name => {
  md.use(container, name, {
    validate: params => params.trim().startsWith(name),
    render(tokens, idx) {
      if (tokens[idx].nesting === 1) {
        const title = tokens[idx].info.trim().match(new RegExp(`^${name}\\s*(.*)$`))?.[1] || "";
        return `<div class="container-${name}">${title ? `<div class="container-title">${title}</div>` : ""}\n`;
      }
      return "</div>\n";
    }
  });
});

// Blockquote com classe
const defaultBlockquote = md.renderer.rules.blockquote_open || ((t, i, o, e, s) => s.renderToken(t, i, o));
md.renderer.rules.blockquote_open = (t, i, o, e, s) => {
  t[i].attrPush(["class", "blockquote"]);
  return defaultBlockquote(t, i, o, e, s);
};

// Tabelas com wrapper
const defaultTableOpen = md.renderer.rules.table_open || ((t, i, o, e, s) => s.renderToken(t, i, o));
md.renderer.rules.table_open = (t, i, o, e, s) => {
  t[i].attrPush(["class", "markdown-table"]);
  return `<div class="table-wrapper">${defaultTableOpen(t, i, o, e, s)}`;
};

const defaultTableClose = md.renderer.rules.table_close || ((t, i, o, e, s) => s.renderToken(t, i, o));
md.renderer.rules.table_close = (t, i, o, e, s) => `${defaultTableClose(t, i, o, e, s)}</div>`;

// I/O
try {
  const input = fs.readFileSync(0, "utf8");
  process.stdout.write(md.render(input));
} catch (err) {
  process.stderr.write(`Erro ao processar Markdown: ${err.message}\n`);
  process.exit(1);
}