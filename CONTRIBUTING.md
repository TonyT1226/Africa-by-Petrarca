# 参与 · Contributing

欢迎指正和补充，无论是一个字的错误、一条注释，还是整卷审读。
Corrections and additions of any size are welcome.

## 报告问题 · Reporting
开一个 issue（可用 “Correction” 模板），写明：
- 诗行编号，如 `africa.6.395`；
- 问题是什么，应当怎样改；
- 理由（拉丁语法、史实、版本依据等）。

Open an issue with the verse ID, what is wrong, the proposed fix and your reasoning.

## 修改 · Changing files
1. 只改 `source/` 下的文件。`data/` 和 `text/` 是自动生成的。
   Edit only files under `source/`. `data/` and `text/` are generated.
2. 运行 · Run:
   ```bash
   python3 tools/regenerate.py
   python3 tools/check_all.py
   ```
3. 提交 Pull Request，说明改了哪些行、为什么。
   Open a pull request listing the verse IDs you changed and why.

格式和规则见 [`AGENTS.md`](AGENTS.md)，中文译文的体例见 [`methodology/STYLE.md`](methodology/STYLE.md)，专名见
[`methodology/GLOSSARY.md`](methodology/GLOSSARY.md)。

## 原则 · Principles
- 不改动拉丁原文的分行；录入错误用 `#CORRECTIONS` 更正，异文和推测写进注释。
- 不编造出处，不抄录现代译本或注本的文字。
- 拿不准的地方写出来（注释或 `KNOWN_ISSUES.md`），不要悄悄改掉。
- 用 AI 代理参与修改的，请在 PR 中说明；不要把 AI 审校说成人工审校。
- Do not change line alignment. Cite sources only when certain. Flag doubts instead of hiding them. Say when a
  change was made with an AI agent.
