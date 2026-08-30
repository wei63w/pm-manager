#!/usr/bin/env node
/**
 * Optional Node init for PM Manager. Scaffolds .pm/ + git exclude.
 * Vue repos get the same frontend seed as `pm init`. Does not port arch/review/dashboard.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MODULES = [
  "bugs",
  "architecture",
  "engineering",
  "environments",
  "integration",
  "testing",
  "release",
  "database",
  "operations",
  "cost",
];
const VUE_PACKAGES = new Set(["vue", "nuxt", "nuxt3"]);
const DEFAULT_DOCS =
  "[DOC-agents, DOC-prd, DOC-design, DOC-api, DOC-deploy, DOC-trouble]";
const VUE_DOCS = "[DOC-agents, DOC-prd, DOC-design, DOC-api, DOC-deploy]";
const VUE_SCAN_EXTRA = [".nuxt", ".output", "coverage"];

function templatesPm() {
  const bundled = path.join(__dirname, "templates", "pm");
  const fromRepo = path.resolve(
    __dirname,
    "..",
    "..",
    "..",
    "skills",
    "pm-manager",
    "templates",
    "pm",
  );
  if (fs.existsSync(path.join(fromRepo, "project.yaml"))) return fromRepo;
  if (fs.existsSync(path.join(bundled, "project.yaml"))) return bundled;
  throw new Error(
    "templates/pm missing. Run from the pm-manager repo or reinstall @wei63w/pm-manager.",
  );
}

function copyIfMissing(src, dst) {
  if (fs.existsSync(dst) || !fs.existsSync(src)) return;
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
}

function mkdirp(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function ensureGitExclude(root) {
  const gitDir = path.join(root, ".git");
  if (!fs.existsSync(gitDir) || !fs.statSync(gitDir).isDirectory()) {
    return "skipped (not a git repo)";
  }
  const exclude = path.join(gitDir, "info", "exclude");
  mkdirp(path.dirname(exclude));
  const existing = fs.existsSync(exclude)
    ? fs.readFileSync(exclude, "utf8")
    : "";
  if (existing.split(/\r?\n/).some((x) => x.trim() === ".pm/")) {
    return "already present";
  }
  const prefix =
    existing && !existing.endsWith("\n") ? "\n" : existing ? "" : "";
  fs.appendFileSync(
    exclude,
    `${prefix}\n# PM governance workbench (local only)\n.pm/\n`,
  );
  return `appended to ${exclude}`;
}

function packageDeps(root) {
  const p = path.join(root, "package.json");
  if (!fs.existsSync(p)) return {};
  let data;
  try {
    data = JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return {};
  }
  const out = {};
  for (const key of ["dependencies", "devDependencies", "peerDependencies"]) {
    const block = data[key];
    if (block && typeof block === "object") {
      for (const [name, spec] of Object.entries(block)) {
        out[name] = spec == null ? "" : String(spec);
      }
    }
  }
  return out;
}

function isVueProject(root) {
  const deps = packageDeps(root);
  return [...VUE_PACKAGES].some((n) => n in deps);
}

function major(spec) {
  const m = String(spec || "").match(/(\d+)/);
  return m ? Number(m[1]) : null;
}

function vueHints(root) {
  const deps = packageDeps(root);
  if (![...VUE_PACKAGES].some((n) => n in deps)) {
    return { isVue: false, runtime: "", build: "" };
  }
  const hints = { isVue: true, runtime: "vue3", build: "" };
  if ("nuxt" in deps || "nuxt3" in deps) {
    hints.runtime = "nuxt";
    hints.build = "nuxt";
    return hints;
  }
  if (major(deps.vue) === 2) hints.runtime = "vue2";
  const viteCfg = [
    "vite.config.ts",
    "vite.config.js",
    "vite.config.mts",
    "vite.config.mjs",
  ].some((n) => fs.existsSync(path.join(root, n)));
  if ("vite" in deps || viteCfg) hints.build = "vite";
  else if (
    fs.existsSync(path.join(root, "vue.config.js")) ||
    fs.existsSync(path.join(root, "vue.config.ts"))
  ) {
    hints.build = "vue-cli";
  }
  return hints;
}

function seedVueDefaults(root) {
  const dest = path.join(root, ".pm", "config", "project.yaml");
  if (!fs.existsSync(dest)) return [];
  const hints = vueHints(root);
  if (!hints.isVue) return [];
  let text = fs.readFileSync(dest, "utf8");
  const changed = [];

  if (/^\s*type:\s*(unknown|"")\s*$/m.test(text)) {
    text = text.replace(/^(\s*type:\s*).*$/m, "$1vue");
    changed.push("project.type");
  }
  if (/^\s*lifecycle:\s*(unknown|"")\s*$/m.test(text)) {
    text = text.replace(/^(\s*lifecycle:\s*).*$/m, "$1existing");
    changed.push("project.lifecycle");
  }
  if (hints.runtime && /^  runtime:\s*(?:""|'')\s*$/m.test(text)) {
    text = text.replace(/^  runtime:\s*(?:""|'')\s*$/m, `  runtime: ${hints.runtime}`);
    changed.push("stack.runtime");
  }
  if (hints.build && /^  build:\s*none\s*$/m.test(text)) {
    text = text.replace(/^  build:\s*none\s*$/m, `  build: ${hints.build}`);
    changed.push("stack.build");
  }
  for (const key of ["database", "operations", "cost"]) {
    const re = new RegExp(`^  ${key}:\\s*true\\s*$`, "m");
    if (re.test(text)) {
      text = text.replace(re, `  ${key}: false`);
      changed.push(`modules.${key}`);
    }
  }
  const docsRe = new RegExp(
    `^  required:\\s*${DEFAULT_DOCS.replace(/[[\]]/g, "\\$&")}\\s*$`,
    "m",
  );
  if (docsRe.test(text)) {
    text = text.replace(docsRe, `  required: ${VUE_DOCS}`);
    changed.push("docs.required");
  }
  const scanM = text.match(/^  exclude_dirs:\s*\[([^\]]*)\]\s*$/m);
  if (scanM) {
    const items = scanM[1]
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
    const extra = VUE_SCAN_EXTRA.filter((x) => !items.includes(x));
    if (extra.length) {
      text = text.replace(
        scanM[0],
        `  exclude_dirs: [${[...items, ...extra].join(", ")}]`,
      );
      changed.push("scan.exclude_dirs");
    }
  }
  if (!/^profile:/m.test(text)) {
    if (text && !text.endsWith("\n")) text += "\n";
    text += "profile: frontend\n";
    changed.push("profile");
  }
  if (changed.length) {
    fs.writeFileSync(dest, text.endsWith("\n") ? text : `${text}\n`);
  }
  return changed;
}

function scaffold(root) {
  const tpl = templatesPm();
  const pm = path.join(root, ".pm");
  for (const rel of [
    "config",
    "state",
    "charter",
    "outline",
    "prd",
    path.join("inbox", "stacks"),
    path.join("evidence", "scans"),
    path.join("bugs", "incidents"),
    "architecture",
    "dashboard",
    "engineering",
  ]) {
    mkdirp(path.join(pm, rel));
  }
  const copies = [
    ["project.yaml", path.join(pm, "config", "project.yaml")],
    ["local.yaml", path.join(pm, "config", "local.yaml")],
    ["overview.md", path.join(pm, "state", "overview.md")],
    ["todo.md", path.join(pm, "state", "todo.md")],
    ["completed.md", path.join(pm, "state", "completed.md")],
  ];
  for (const [src, dst] of copies) {
    copyIfMissing(path.join(tpl, src), dst);
  }
  for (const name of ["charter.md", "requirements.md", "nfr.md", "dod.md", "sources.md"]) {
    copyIfMissing(path.join(tpl, "charter", name), path.join(pm, "charter", name));
  }
  for (const name of ["project-outline.md", "epics.md", "milestones.md"]) {
    copyIfMissing(path.join(tpl, "outline", name), path.join(pm, "outline", name));
  }
  copyIfMissing(path.join(tpl, "prd", "prd.md"), path.join(pm, "prd", "prd.md"));
  for (const mod of MODULES) {
    const d = path.join(pm, mod);
    mkdirp(d);
    for (const name of ["checklist.md", "findings.md", "todo.md", "completed.md"]) {
      copyIfMissing(path.join(tpl, "module", name), path.join(d, name));
    }
  }
  const overview = path.join(pm, "architecture", "overview.md");
  if (!fs.existsSync(overview)) {
    fs.writeFileSync(
      overview,
      "# Architecture overview\n\n_Run `pm arch` or `/pm-arch` to generate Mermaid diagrams from this project._\n",
    );
  }
  const stub =
    "flowchart LR\n  %% Placeholder — regenerate with: pm arch\n  A[Project] --> B[Dependency]\n";
  for (const name of [
    "system-context.mmd",
    "service-dependencies.mmd",
    "request-flow.mmd",
    "deploy-flow.mmd",
  ]) {
    const p = path.join(pm, "architecture", name);
    if (!fs.existsSync(p)) fs.writeFileSync(p, stub);
  }
  fs.writeFileSync(path.join(pm, "evidence", "scans", ".gitkeep"), "");
  copyIfMissing(
    path.join(tpl, "engineering", "reviews.md"),
    path.join(pm, "engineering", "reviews.md"),
  );
  copyIfMissing(
    path.join(tpl, "engineering", "rules.md"),
    path.join(pm, "engineering", "rules.md"),
  );
  const docIndex = path.join(pm, "state", "doc-index.md");
  if (!fs.existsSync(docIndex)) {
    copyIfMissing(path.join(tpl, "doc-index.md"), docIndex);
    if (!fs.existsSync(docIndex)) {
      fs.writeFileSync(docIndex, "# Document index\n\n_Fill via `/pm-init` core-doc check._\n");
    }
  }
  const audit = path.join(pm, "state", "audit.jsonl");
  if (!fs.existsSync(audit)) fs.writeFileSync(audit, "");
  const dialogue = path.join(pm, "state", "dialogue.md");
  if (!fs.existsSync(dialogue)) {
    fs.writeFileSync(
      dialogue,
      "# 开发对话记录\n\n> 脱敏后落盘。运行 `pm log` 或 `/pm-journal` 追加本轮意图。\n\n",
    );
  }
  const dash = path.join(pm, "dashboard", "overview.md");
  if (!fs.existsSync(dash)) {
    fs.writeFileSync(
      dash,
      "# Governance dashboard\n\n_Run `pm dashboard` or `/pm-all` to populate._\n",
    );
  }
  return pm;
}

function usage() {
  console.log(`Usage: pm-manager init [path]

Scaffolds local .pm/ governance (same tree as Python \`pm init --scaffold-only\`).
Vue/Nuxt package.json deps also receive frontend seed defaults.
Preferred full CLI remains \`pm init\` (Python). Next: open Cursor and run /pm-init.
`);
}

function main(argv) {
  const args = argv.slice(2);
  if (args.length === 0 || args[0] === "-h" || args[0] === "--help") {
    usage();
    process.exit(args.length === 0 ? 1 : 0);
  }
  if (args[0] !== "init") {
    console.error(`Unknown command: ${args[0]}`);
    usage();
    process.exit(1);
  }
  const root = path.resolve(args[1] || ".");
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    console.error(`Not a directory: ${root}`);
    process.exit(1);
  }
  console.log(`项目: ${root}`);
  const pm = scaffold(root);
  const exclude = ensureGitExclude(root);
  console.log(`完成 已搭建 ${pm}`);
  console.log(`完成 Git exclude: ${exclude}`);
  if (isVueProject(root)) {
    const seeded = seedVueDefaults(root);
    const extra = seeded.length ? seeded.join("、") : "无（已有配置未覆盖）";
    console.log(`完成 Vue 前端默认值（写入: ${extra}）`);
  }
  console.log("下一步：在 Cursor 里开对话，输入 /pm-init");
}

main(process.argv);
