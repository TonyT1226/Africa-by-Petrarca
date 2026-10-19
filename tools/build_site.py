"""Build the web reader (static HTML for GitHub Pages) from data/.

Usage: python3 tools/build_site.py [--out DIR]
Reads data/books.json, data/lines.jsonl, data/sections.jsonl, data/notes.jsonl and source/front/*.html,
plus the templates, styles, script and fonts in web/. Writes build/site/ (or DIR):
  index.html        title page, the nine books with their summaries
  1.html … 9.html   one page per book: Latin and Chinese in parallel, notes after each section;
                    every verse has the anchor #N, so africa.9.123 is 9.html#123
  about.html        preface, conventions and principal persons (the PDF's front matter)
Standard library only. The output is not committed; .github/workflows/pages.yml builds and deploys it.
"""
import argparse
import json
import shutil
import sys
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import BUILD, DATA, FRONT  # noqa: E402

WEB = ROOT / "web"
REPO = "https://github.com/yiyuanli939/Africa-by-Petrarca"
PDF = REPO + "/raw/main/dist/africa-petrarca-la-zh.pdf"
ZH_NUM = "一二三四五六七八九"
FOOT_NAMES = {"D": "扬抑抑", "S": "扬扬", "X": "末音步"}


def e(s):
    return escape(s or "", quote=True)


def load():
    books = json.loads((DATA / "books.json").read_text(encoding="utf-8"))
    lines, sections, notes = {}, {}, {}
    for name, store in (("lines", lines), ("sections", sections), ("notes", notes)):
        for raw in (DATA / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rec = json.loads(raw)
                store.setdefault(rec["book"], []).append(rec)
    return books, lines, sections, notes


def book_nav(current=None):
    out = []
    for i, z in enumerate(ZH_NUM, 1):
        cur = ' aria-current="page"' if i == current else ""
        out.append(f'<a href="{i}.html"{cur} title="第{z}卷">{z}</a>')
    return "".join(out)


CONTROLS = """<div class="controls" hidden>
  <div class="seg" role="group" aria-label="显示的文字">
    <button type="button" data-set="text" data-value="both">对照</button>
    <button type="button" data-set="text" data-value="la">拉丁</button>
    <button type="button" data-set="text" data-value="zh">中文</button>
  </div>
  <button type="button" class="tog" data-toggle="notes" aria-pressed="true">注释</button>
  <button type="button" class="tog" data-toggle="scan" aria-pressed="false" title="音步划分与重拍；D 扬抑抑，S 扬扬">格律</button>
  <button type="button" class="tog toc-open" aria-expanded="false" aria-controls="toc">段落</button>
</div>"""


def page(tpl, *, title, description, page_id, body, current=None, controls=False):
    return tpl.substitute(
        title=e(title), description=e(description), page=page_id, body=body,
        booknav=book_nav(current), controls=CONTROLS if controls else "", repo=REPO, pdf=PDF,
    )


def feet_html(feet):
    parts = [e(p) for p in feet.split("|")]
    return '<span class="fd" aria-hidden="true">|</span>'.join(parts)


def pattern_html(pattern):
    if not pattern:
        return ""
    title = "　".join(FOOT_NAMES[c] for c in pattern)
    return f'<span class="pat" title="{title}">{e(pattern)}</span>'


def verse_html(v, first):
    n = v["line"]
    latin = e(v["latin"])
    if first and latin:
        latin = f'<span class="initial">{latin[0]}</span>{latin[1:]}'
    corr = ""
    if v.get("latin_digital"):
        corr = f' data-digital="{e(v["latin_digital"])}" title="数字底本作：{e(v["latin_digital"])}"'
    sc = v["scansion"]
    scan = feet_html(sc["feet"]) if sc.get("feet") else latin
    shown = " shown" if n % 5 == 0 else ""
    return (
        f'<div class="v" id="{n}">'
        f'<p class="la" lang="la"><span class="t{" corr" if corr else ""}"{corr}>{latin}</span>'
        f'<span class="sc">{scan}{pattern_html(sc.get("pattern"))}</span></p>'
        f'<a class="n{shown}" href="#{n}" aria-label="第 {n} 行">{n}</a>'
        f'<p class="zh">{e(v["zh"])}</p>'
        f"</div>"
    )


def note_html(nt):
    rng = str(nt["start"]) if nt["start"] == nt["end"] else f'{nt["start"]}–{nt["end"]}'
    kind = '<span class="kind">校</span>' if nt["type"] == "textual" else ""
    lemma = f'<i class="lem" lang="la">{e(nt["lemma"])}</i>　' if nt.get("lemma") else ""
    nid = nt["id"].split(".")[-1]
    return (f'<p class="note" id="{nid}">{kind}<a class="nr" href="#{nt["start"]}">{rng}</a>　'
            f'{lemma}{e(nt["text_zh"])}</p>')


def book_page(tpl, b, lines, sections, notes):
    num = b["book"]
    by_line = {v["line"]: v for v in lines}
    # commentary notes carry their section; textual notes go to the section holding their first verse
    sec_notes = {s["id"]: [] for s in sections}
    for nt in notes:
        sid = nt["section"] or next(s["id"] for s in sections if s["start"] <= nt["start"] <= s["end"])
        sec_notes[sid].append(nt)
    toc, body = [], []
    for s in sections:
        sid = s["id"].split(".")[-1]
        rng = f'{s["start"]}–{s["end"]}' if s["start"] != s["end"] else str(s["start"])
        toc.append(f'<li><a href="#{sid}"><span class="r">{rng}</span>{e(s["title_zh"])}</a></li>')
        verses = "\n".join(verse_html(by_line[n], n == 1) for n in range(s["start"], s["end"] + 1))
        ns = sorted(sec_notes[s["id"]], key=lambda x: (x["start"], x["type"] == "textual"))
        aside = f'<aside class="notes" aria-label="注释">{"".join(note_html(x) for x in ns)}</aside>' if ns else ""
        body.append(
            f'<section class="sec" id="{sid}" aria-labelledby="{sid}h">'
            f'<h2 id="{sid}h"><span class="r">{rng}</span>{e(s["title_zh"])}</h2>'
            f'<div class="verses">\n{verses}\n</div>{aside}</section>'
        )
    prev_link = f'<a rel="prev" href="{num - 1}.html">← 第{ZH_NUM[num - 2]}卷</a>' if num > 1 else "<span></span>"
    next_link = f'<a rel="next" href="{num + 1}.html">第{ZH_NUM[num]}卷 →</a>' if num < 9 else "<span></span>"
    html = f"""<div class="book" data-book="{num}">
<nav class="toc" id="toc" aria-label="段落目录">
  <p class="toc-head">第{ZH_NUM[num - 1]}卷　段落</p>
  <ol>{"".join(toc)}</ol>
</nav>
<main id="main">
<header class="book-head">
  <p class="la-title" lang="la">{e(b["title_la"])}</p>
  <h1>第{ZH_NUM[num - 1]}卷</h1>
  <p class="count">{b["lines"]} 行，{b["sections"]} 段</p>
  <div class="argument"><p>{e(b["summary_zh"])}</p></div>
</header>
{"".join(body)}
<nav class="pager" aria-label="上一卷与下一卷">{prev_link}{next_link}</nav>
</main>
</div>"""
    first = b["summary_zh"].split("。")[0] + "。"
    return page(tpl, title=f"第{ZH_NUM[num - 1]}卷 · 彼特拉克《阿非利加》拉中对照", description=first,
                page_id="book", body=html, current=num, controls=True)


def index_page(tpl, books):
    total = sum(b["lines"] for b in books)
    items = []
    for b in books:
        n = b["book"]
        items.append(
            f'<li><a href="{n}.html"><span class="bk">第{ZH_NUM[n - 1]}卷</span>'
            f'<span class="la-title" lang="la">{e(b["title_la"])}</span><span class="cnt">{b["lines"]} 行</span></a>'
            f'<p>{e(b["summary_zh"])}</p></li>'
        )
    html = f"""<main id="main" class="cover">
<header class="title">
  <p class="author" lang="la">Francesco Petrarca</p>
  <h1><span class="t-la" lang="la">Africa</span><span class="t-zh">阿非利加</span></h1>
</header>
<div class="lede">
  <p>彼特拉克用拉丁文写的史诗，九卷 {total:,} 行，讲第二次布匿战争中大西庇阿击败汉尼拔。他自己最看重这部诗，1341 年在罗马加冕桂冠诗人，靠的主要就是它；可他至死没有写完，也没有发表。</p>
  <p>这里是拉丁原文与中文译文的逐行对照，附注释和全诗格律标注。每一行都有固定编号，例如第九卷第 123 行写作 <code>africa.9.123</code>，网址是 <a href="9.html#123">9.html#123</a>。</p>
  <p class="status">译文、注释与格律标注由 AI（Anthropic 的 Claude）完成，并由另一组 AI 逐行审校，<strong>尚未经过拉丁语学者审读</strong>。发现错误，欢迎在 <a href="{REPO}/issues/new?template=correction.yml">GitHub</a> 上指出。</p>
  <p class="links"><a href="about.html">前言、体例与人物</a>　<a href="{PDF}">下载 PDF（363 页）</a>　<a href="{REPO}">源文件与数据</a></p>
</div>
<ol class="booklist">{"".join(items)}</ol>
</main>"""
    return page(tpl, title="彼特拉克《阿非利加》拉中对照注释本",
                description=f"彼特拉克拉丁文史诗《阿非利加》九卷 {total:,} 行，拉丁原文与中文译文逐行对照，附注释和格律标注。",
                page_id="home", body=html)


def about_page(tpl):
    parts = []
    for name in ("preface", "conventions", "persons"):
        p = FRONT / f"{name}.html"
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
    html = f'<main id="main" class="about">\n{"".join(parts)}\n</main>'
    return page(tpl, title="前言、体例与人物 · 彼特拉克《阿非利加》", description="译者前言、底本与体例、主要人物。",
                page_id="about", body=html)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=BUILD / "site")
    out = ap.parse_args().out
    books, lines, sections, notes = load()
    tpl = Template((WEB / "page.html").read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    (out / "fonts").mkdir(parents=True)
    for f in ("style.css", "reader.js"):
        shutil.copy(WEB / f, out / f)
    for f in (WEB / "fonts").iterdir():
        shutil.copy(f, out / "fonts" / f.name)
    (out / "index.html").write_text(index_page(tpl, books), encoding="utf-8")
    (out / "about.html").write_text(about_page(tpl), encoding="utf-8")
    for b in books:
        n = b["book"]
        html = book_page(tpl, b, lines[n], sections[n], notes.get(n, []))
        (out / f"{n}.html").write_text(html, encoding="utf-8")
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"site: {out} ({len(books) + 2} pages, {size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
