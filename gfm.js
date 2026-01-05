#!/usr/bin/env node
import fs from "fs";
import MarkdownIt from "markdown-it";
import taskLists from "markdown-it-task-lists";
import footnote from "markdown-it-footnote";
import deflist from "markdown-it-deflist";
import container from "markdown-it-container";
import emoji from "markdown-it-emoji";
import markdownItMark from "markdown-it-mark";
import markdownItSub from "markdown-it-sub";
import markdownItSup from "markdown-it-sup";
import markdownItIns from "markdown-it-ins";
import markdownItAbbr from "markdown-it-abbr";

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
});

md.use(taskLists, { enabled: true });
md.use(footnote);
md.use(deflist);
md.use(emoji);
md.use(markdownItMark);
md.use(markdownItSub);
md.use(markdownItSup);
md.use(markdownItIns);
md.use(markdownItAbbr);

["note", "tip", "warning", "danger", "success", "question"].forEach(name => md.use(container, name));

const input = fs.readFileSync(0, "utf8");
process.stdout.write(md.render(input));
