# 彼特拉克《阿非利加》拉中对照注释本

**Petrarch's *Africa*: a Latin–Chinese parallel edition, made with AI agents and built for reuse**
(English summary below)

[![validate](https://github.com/yiyuanli939/Africa-by-Petrarca/actions/workflows/validate.yml/badge.svg)](https://github.com/yiyuanli939/Africa-by-Petrarca/actions/workflows/validate.yml)

彼特拉克（Francesco Petrarca，1304–1374）的拉丁文史诗《阿非利加》（*Africa*），九卷 6,730 行，讲述第二次布匿战争中大西庇阿击败汉尼拔的故事。本仓库收录：

- **拉丁原文**，按行编号，校改了数字版的 88 处录入错误；
- **中文译文**，直接从拉丁文译出，不押韵的分行诗体，一行对一行；
- **1,381 条注释**，涉及人物、史实（对照李维）、古典典故、文本问题；
- **全诗格律标注**：每行六音步的扬抑抑格（dactylic hexameter）划分；
- **ElevenLabs 朗读稿**：按格律标出节拍重音、元音省略、停顿，配朗读语气标签，可直接用于语音合成；
- **排印好的 PDF**（363 页）：[`dist/`](dist/)。

> **重要说明**：译文、注释、格律标注都由 AI（Anthropic 的 Claude 模型）完成，并经过另一组 AI 代理逐行独立审校，**尚未经过人工（拉丁语学者）审读**。欢迎指正，见 [参与](#参与)。制作过程见 [`methodology/`](methodology/)。

## 怎么用

| 你想…… | 去这里 |
|---|---|
| 读 | PDF：[`dist/`](dist/)；在 GitHub 上逐卷对照阅读：[`text/`](text/) |
| 引用某一行 | 每行有固定编号 `africa.卷.行`，如 `africa.9.123`（第九卷第 123 行） |
| 拿数据做研究、做应用、做创作 | [`data/`](data/)：`lines.jsonl`（逐行：拉丁、中文、格律、朗读稿）、注释、专名、TEI XML；说明见 [`data/README.md`](data/README.md) |
| 用 ElevenLabs 配音 | 朗读稿 [`data/recitation/`](data/recitation/)，一键配音脚本 [`tts/`](tts/) |
| 让 AI 代理参与修改或扩展 | 先读 [`AGENTS.md`](AGENTS.md) |
| 重新排印 PDF | `python3 tools/build.py`（需要 WeasyPrint 和字体，见下） |

## 仓库结构

```
source/        手工维护的正本：拉丁原文、中文译文与注释、格律修订、朗读语气标签、PDF 前言
data/          由工具自动生成的逐行数据（不要手改）
text/          自动生成的拉中对照 Markdown，一卷一个文件
tools/         Python 工具：校验、格律扫描、导出、排版
tts/           ElevenLabs 配音脚本
methodology/   翻译、审校、格律检查所用的简报与风格指南
reviews/       每卷的审校记录
dist/          排印好的 PDF
```

修改 `source/` 之后运行：

```bash
python3 tools/regenerate.py   # 重新生成 data/ 和 text/
python3 tools/check_all.py    # 全部校验，必须通过
```

只需要 Python 3.10 以上，不用安装其他库。排印 PDF 另需 `pip install weasyprint`，以及 TeX Gyre Pagella 和 Noto Serif CJK SC 两种字体。

## 参与

- **指出错误**：开一个 issue，写明行号（如 `africa.6.395`）、问题和理由。
- **直接修改**：改 `source/` 里的文件，运行上面两条命令，提交 Pull Request。详见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
- 尚待解决的问题见 [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)，下一步计划见 [`ROADMAP.md`](ROADMAP.md)。特别欢迎懂拉丁语的读者审读译文和格律。

## 许可与来源

- **译文、注释、格律标注、朗读稿与全部数据**：[CC BY 4.0](LICENSE)。使用时请注明出处，并说明译文由 AI 生成。
- **代码**（`tools/`、`tts/`）：[MIT](LICENSE-CODE)。
- **拉丁原文**：彼特拉克的诗作本身属于公有领域。本书录入的是比利时鲁汶天主教大学 *Itinera Electronica*（*Bibliotheca Classica Selecta*）发布的数字文本：第一、二卷属 Pingaud 1872 年刊本一系，第三至九卷属 Festa 1926 年国家版一系。本项目对拉丁原文不主张任何权利，对它的改动只有 [`data/corrections.tsv`](data/corrections.tsv) 所列的录入错误更正。如权利方对转载有异议，请开 issue 联系。

## 引用

见 [`CITATION.cff`](CITATION.cff)。引用具体诗行时用 `africa.卷.行` 编号。

---

## English summary

Francesco Petrarca's Latin epic *Africa* (9 books, 6,730 hexameters) on Scipio's victory over Hannibal, with:

- the Latin text, line-numbered, with 88 misprints of the digital text corrected;
- a **Chinese verse translation made directly from the Latin**, line for line, and **1,381 notes**;
- a **metrical scansion of every verse** (dactylic hexameter: foot division and pattern);
- an **ElevenLabs recitation script** (ictus accents, elisions, caesura pauses, delivery tags) and a voicing
  script;
- a typeset PDF in [`dist/`](dist/).

**Status:** translation, notes and scansion were produced and cross-reviewed by AI agents (Claude, Anthropic).
They have **not yet been reviewed by a human Latinist**. Corrections are welcome.

**For machines and agents:** every verse has a permanent ID `africa.B.N`. Line-addressed data are in
[`data/`](data/) (JSONL, TSV, TEI P5); start with [`data/README.md`](data/README.md). Agents should read
[`AGENTS.md`](AGENTS.md) first. Python 3.10+ with no dependencies: `python3 tools/check_all.py` validates
everything, and `python3 tools/regenerate.py` rebuilds the derived files.

**License:** translation, notes, annotations and data are CC BY 4.0 (please state that the translation is
AI-made). Code is MIT. The Latin poem is in the public domain. The digital Latin text comes from
*Itinera Electronica* (UCLouvain); this project claims no rights in it.
