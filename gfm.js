#!/usr/bin/env node

import fs from "fs";
import MarkdownIt from "markdown-it";
import taskLists from "markdown-it-task-lists";
import footnote from "markdown-it-footnote";
import deflist from "markdown-it-deflist";
import container from "markdown-it-container";

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

md.use(taskLists, { enabled: true });
md.use(footnote);
md.use(deflist);
md.use(container, "note");
md.use(container, "tip");
md.use(container, "warning");
md.use(container, "danger");
md.use(container, "success");
md.use(container, "question");

const input = fs.readFileSync(0, "utf8");
process.stdout.write(md.render(input));
