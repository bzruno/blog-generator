#!/usr/bin/env node
import fs from "fs";
import MarkdownIt from "markdown-it";
import taskLists from "markdown-it-task-lists";
import footnote from "markdown-it-footnote";
import deflist from "markdown-it-deflist";
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
import emoji from "markdown-it-emoji";
import attrs from "markdown-it-attrs";
import katex from "katex";

const KATEX_OPTS = {
  throwOnError: false,
  errorColor: "#cc0000",
  strict: "ignore",
  output: "html",
};

const KATEX_BLOCK_TAG = "data-katex-block";
const KATEX_INLINE_TAG = "data-katex-inline";

/** Extrai fórmulas $$...$$ e $...$, substitui por placeholders HTML (preservados pelo markdown). */
function extractMath(text) {
  const blockMaths = [];
  const inlineMaths = [];
  let out = text;

  out = out.replace(/\$\$([\s\S]*?)\$\$/g, (_, latex) => {
    const i = blockMaths.length;
    blockMaths.push(latex.trim());
    return `<span ${KATEX_BLOCK_TAG}="${i}"></span>`;
  });

  out = out.replace(/\$([^$\n]+)\$/g, (_, latex) => {
    const i = inlineMaths.length;
    inlineMaths.push(latex.trim());
    return `<span ${KATEX_INLINE_TAG}="${i}"></span>`;
  });

  return { text: out, blockMaths, inlineMaths };
}

/** Substitui placeholders no HTML pelo resultado do KaTeX (usa o pacote katex 0.16 do projeto). */
function injectMath(html, blockMaths, inlineMaths) {
  let out = html;
  const blockRe = new RegExp(`<span\\s+${KATEX_BLOCK_TAG}="(\\d+)"\\s*></span>`, "g");
  out = out.replace(blockRe, (_, n) => {
    const i = parseInt(n, 10);
    const latex = blockMaths[i];
    if (latex == null) return _;
    try {
      return katex.renderToString(latex, { ...KATEX_OPTS, displayMode: true });
    } catch (e) {
      return `<span class="katex-error" title="${escapeHtml(String(e.message))}">$$${escapeHtml(latex)}$$</span>`;
    }
  });
  const inlineRe = new RegExp(`<span\\s+${KATEX_INLINE_TAG}="(\\d+)"\\s*></span>`, "g");
  out = out.replace(inlineRe, (_, n) => {
    const i = parseInt(n, 10);
    const latex = inlineMaths[i];
    if (latex == null) return _;
    try {
      return katex.renderToString(latex, { ...KATEX_OPTS, displayMode: false });
    } catch (e) {
      return `<span class="katex-error" title="${escapeHtml(String(e.message))}">$${escapeHtml(latex)}$</span>`;
    }
  });
  return out;
}

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
      } catch {
        /* fallback: render escaped */
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  }
});

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
  .use(anchor, {
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
    format: (heading, htmlencode) =>
      htmlencode(heading.replace(/^\d+\.\s*/, ""))
  })
  .use(multimdTable, { multiline: true, rowspan: true, headerless: true })
  .use(implicitFigures, { figcaption: true })
  .use(video, {
    youtube: { width: 640, height: 390 },
    vimeo: { width: 500, height: 281 }
  })
  .use(imsize)
  .use(linkAttrs, {
    matcher: href => /^https?:\/\//.test(href),
    attrs: { target: "_blank", rel: "noopener noreferrer" }
  })
  .use(attrs);

const defaultBlockquote =
  md.renderer.rules.blockquote_open ||
  ((t, i, o, e, s) => s.renderToken(t, i, o));

md.renderer.rules.blockquote_open = (t, i, o, e, s) => {
  t[i].attrPush(["class", "blockquote"]);
  return defaultBlockquote(t, i, o, e, s);
};

const defaultTableOpen =
  md.renderer.rules.table_open ||
  ((t, i, o, e, s) => s.renderToken(t, i, o));

md.renderer.rules.table_open = (t, i, o, e, s) => {
  t[i].attrPush(["class", "markdown-table"]);
  return `<div class="table-wrapper">${defaultTableOpen(t, i, o, e, s)}`;
};

const defaultTableClose =
  md.renderer.rules.table_close ||
  ((t, i, o, e, s) => s.renderToken(t, i, o));

md.renderer.rules.table_close = (t, i, o, e, s) =>
  `${defaultTableClose(t, i, o, e, s)}</div>`;

/** Escapa HTML para evitar XSS em conteúdo de spoiler. */
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Aplica spoilers !!text!! apenas fora de <pre> e <code>, para não afetar blocos de código.
 */
function processSpoilers(text) {
  const excludedRanges = [];
  let m;
  const preRe = /<pre[^>]*>[\s\S]*?<\/pre>/gi;
  while ((m = preRe.exec(text)) !== null) excludedRanges.push([m.index, m.index + m[0].length]);
  const codeRe = /<code[^>]*>[\s\S]*?<\/code>/gi;
  while ((m = codeRe.exec(text)) !== null) {
    const start = m.index;
    const end = m.index + m[0].length;
    const insidePre = excludedRanges.some(([s, e]) => start >= s && end <= e);
    if (!insidePre) excludedRanges.push([start, end]);
  }
  function isExcluded(index, len) {
    const end = index + len;
    return excludedRanges.some(([s, e]) => index < e && end > s);
  }
  let result = "";
  const re = /!!([^!]+)!!/g;
  let lastEnd = 0;
  while ((m = re.exec(text)) !== null) {
    const inner = escapeHtml(m[1]);
    const repl = isExcluded(m.index, m[0].length) ? m[0] : `<span class="spoiler">${inner}</span>`;
    result += text.slice(lastEnd, m.index) + repl;
    lastEnd = m.index + m[0].length;
  }
  return result + text.slice(lastEnd);
}

try {
  const input = fs.readFileSync(0, "utf8");
  if (!input.trim()) process.exit(0);

  const { text, blockMaths, inlineMaths } = extractMath(input);
  let html = md.render(text);
  html = injectMath(html, blockMaths, inlineMaths);
  html = processSpoilers(html);

  process.stdout.write(html);
} catch (err) {
  process.stderr.write(`Erro ao processar Markdown: ${err.message}\n`);
  process.exit(1);
}
