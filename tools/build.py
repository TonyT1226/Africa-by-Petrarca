"""Build the Latin–Chinese parallel PDF.

Usage: python3 build.py [--books 01,02,...] [--out build/africa.pdf] [--html-only]
Reads source/translation/NN.txt (validated format), source/latin/clean/NN.txt, source/front/*.html.
"""
import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
sys.path.insert(0, str(ROOT / "tools"))
from validate import parse  # noqa: E402

CN = "一二三四五六七八九"
LATIN_TITLES = ["LIBER PRIMVS", "LIBER SECVNDVS", "LIBER TERTIVS", "LIBER QVARTVS", "LIBER QVINTVS",
                "LIBER SEXTVS", "LIBER SEPTIMVS", "LIBER OCTAVVS", "LIBER NONVS"]

CSS = r"""
@page {
  size: A4;
  margin: 19mm 18mm 19mm 18mm;
  @bottom-center { content: counter(page); font-family: "TeX Gyre Pagella"; font-size: 9pt; color: #444; }
}
@page :left {
  margin-left: 14mm; margin-right: 19mm;
  @top-left { content: string(runhead); font-family: "Noto Serif CJK SC"; font-size: 8.5pt; color: #555; }
}
@page :right {
  margin-left: 19mm; margin-right: 14mm;
  @top-right { content: "阿非利加 · AFRICA"; font-family: "Noto Serif CJK SC"; font-size: 8.5pt; color: #555; }
}
@page front {
  @top-left { content: none; } @top-right { content: none; }
}
@page front:first { @bottom-center { content: none; } }
@page bookopen { @top-left { content: none; } @top-right { content: none; } }

html { font-family: "Noto Serif CJK SC", "TeX Gyre Pagella", serif; font-size: 10pt; color: #1a1a1a; }
body { margin: 0; }
.la, .la * { font-family: "TeX Gyre Pagella", serif; }
i.la { font-style: italic; }
p { margin: 0 0 0.6em 0; line-height: 1.75; text-align: justify; }

/* front matter */
.front { page: front; }
.titlepage { page: front; break-after: page; text-align: center; padding-top: 52mm; }
.titlepage .t1 { font-size: 30pt; letter-spacing: 0.3em; margin-bottom: 6mm; }
.titlepage .t2 { font-family: "TeX Gyre Pagella"; font-size: 20pt; letter-spacing: 0.35em; margin-bottom: 4mm; }
.titlepage .t3 { font-size: 12pt; margin-bottom: 30mm; color: #333; }
.titlepage .t4 { font-size: 11pt; line-height: 2; color: #333; }
.titlepage .t5 { font-family: "TeX Gyre Pagella"; font-size: 10pt; color: #555; margin-top: 40mm; }
h2.fm { font-size: 15pt; font-weight: bold; margin: 0 0 7mm 0; text-align: center; letter-spacing: 0.2em;
        break-before: page; bookmark-level: 1; string-set: runhead content(); }
.front h4 { font-size: 11pt; margin: 5mm 0 2mm 0; }
.toc { list-style: none; padding: 0; margin: 0; }
.toc li { margin: 0 0 2.2mm 0; font-size: 10.5pt; }
.toc li.sub { margin-left: 8mm; font-size: 9pt; color: #333; }
.toc a { color: inherit; text-decoration: none; }
.toc a::after { content: leader('·') target-counter(attr(href url), page); font-family: "TeX Gyre Pagella"; }

/* book openings */
.bookopen { page: bookopen; break-before: right; text-align: center; padding-top: 30mm; }
h1.book { font-size: 22pt; letter-spacing: 0.4em; margin: 0 0 3mm 0; font-weight: bold;
          bookmark-level: 1; string-set: runhead content(); }
.bookopen .latt { font-family: "TeX Gyre Pagella"; font-size: 13pt; letter-spacing: 0.3em; color: #555; margin-bottom: 12mm; }
.summary { text-align: left; margin: 0 6mm; padding: 4mm 6mm; border-top: 0.6pt solid #888; border-bottom: 0.6pt solid #888; }
.summary .lab { font-weight: bold; font-size: 10pt; margin-bottom: 2mm; letter-spacing: 0.2em; }
.summary p { font-size: 9.6pt; line-height: 1.8; }
.bookbody { break-before: page; }
.booktoc { text-align: left; margin: 7mm 6mm 0 6mm; }
.booktoc .lab { font-weight: bold; font-size: 10pt; margin-bottom: 2mm; letter-spacing: 0.2em; }
.booktoc ul { list-style: none; padding: 0; margin: 0; columns: 2; column-gap: 9mm; }
.booktoc li { font-size: 8.6pt; line-height: 1.5; margin: 0 0 0.9mm 0; break-inside: avoid; }
.booktoc a { color: inherit; text-decoration: none; }
.booktoc a::after { content: leader('·') target-counter(attr(href url), page); font-family: "TeX Gyre Pagella"; }
.booktoc .r { font-family: "TeX Gyre Pagella"; color: #666; margin-right: 1.5mm; }
.cols3 { columns: 3; column-gap: 7mm; }
.cols3 p { font-size: 8.4pt; line-height: 1.55; margin: 0 0 0.5mm 0; text-align: left; break-inside: avoid; }

/* sections */
h3.sec { font-size: 10.5pt; font-weight: bold; margin: 6mm 0 2.5mm 0; break-after: avoid;
         bookmark-level: 2; padding-bottom: 1mm; border-bottom: 0.4pt solid #bbb; }
h3.sec .rng { font-family: "TeX Gyre Pagella"; font-weight: normal; color: #666; font-size: 9pt; margin-right: 2mm; }
table.par { width: 100%; border-collapse: collapse; table-layout: fixed; }
table.par col.cla { width: 48.5%; } table.par col.cn { width: 4.5%; } table.par col.czh { width: 47%; }
table.par td { vertical-align: top; padding: 0.35mm 0; }
table.par tr { break-inside: avoid; }
td.vla { font-family: "TeX Gyre Pagella"; font-size: 9.3pt; line-height: 1.5; padding-left: 1.2em !important; text-indent: -1.2em; padding-right: 1mm !important; hyphens: none; }
td.vn { font-family: "TeX Gyre Pagella"; font-size: 7.5pt; color: #777; text-align: center; line-height: 1.95; }
td.vzh { font-size: 9.5pt; line-height: 1.55; padding-left: 1em !important; text-indent: -1em; }
.notes { margin: 2.5mm 0 3mm 0; padding: 2mm 0 0 0; border-top: 0.4pt dotted #999; }
.notes p { font-size: 8.4pt; line-height: 1.65; margin: 0 0 1.1mm 0; padding-left: 1.4em; text-indent: -1.4em; }
.notes .nl { font-family: "TeX Gyre Pagella"; font-weight: bold; color: #333; margin-right: 0.55em; }
.notes .lem { font-family: "TeX Gyre Pagella"; font-style: italic; margin-right: 0.6em; }
.notes .lemzh { font-weight: bold; margin-right: 0.6em; }

/* appendices */
table.apx { width: 100%; border-collapse: collapse; font-size: 8.6pt; }
table.apx td, table.apx th { border-bottom: 0.3pt solid #ccc; padding: 0.8mm 1.5mm; text-align: left; vertical-align: top; }
table.apx th { font-weight: bold; border-bottom: 0.6pt solid #888; }
table.apx tr { break-inside: avoid; }
/* appendix 3: ElevenLabs recitation text */
h3.elbook { font-size: 12pt; font-weight: bold; margin: 0 0 4mm 0; break-before: page; bookmark-level: 2;
            letter-spacing: 0.15em; text-align: center; }
h3.elbook .la { font-weight: normal; font-size: 10pt; color: #555; margin-left: 3mm; letter-spacing: 0.2em; }
.elchunk { break-inside: avoid; margin: 0 0 3.5mm 0; }
.elhead { font-size: 7.8pt; color: #777; border-top: 0.4pt solid #bbb; padding-top: 0.8mm; margin: 0 0 1mm 0; }
.elhead .la { color: #777; }
.elapx .elcols { columns: 2; column-gap: 7mm; }
.eltext { font-family: "TeX Gyre Pagella"; font-size: 8.4pt; line-height: 1.36; hyphens: none; }
.eltext div { padding-left: 1.2em; text-indent: -1.2em; }
.eltext .tg { color: #2f5d8a; }
.guide p { text-align: left; }
.guide h4 { font-size: 10.5pt; margin: 4.5mm 0 1.5mm 0; }
.guide ol { margin: 0 0 0.6em 0; padding-left: 6mm; }
.guide li { line-height: 1.75; margin-bottom: 1mm; }
table.legend { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 1mm 0 2mm 0; }
table.legend td, table.legend th { border-bottom: 0.3pt solid #ccc; padding: 1.1mm 1.5mm; text-align: left; vertical-align: top; line-height: 1.6; }
table.legend th { border-bottom: 0.6pt solid #888; font-weight: bold; }
table.legend td.k { font-family: "TeX Gyre Pagella"; white-space: nowrap; width: 17mm; }
table.legend td.e { font-family: "TeX Gyre Pagella"; white-space: nowrap; }
.example { font-size: 9pt; margin: 1mm 0 2mm 0; border-left: 1.2pt solid #bbb; padding: 0.5mm 0 0.5mm 4mm; }
.example div { line-height: 1.8; }
.example .lab { display: inline-block; width: 14mm; color: #666; }
.cols2 { columns: 2; column-gap: 8mm; }
.cols2 p { font-size: 8.6pt; line-height: 1.6; margin: 0 0 0.6mm 0; text-align: left; break-inside: avoid; }
"""


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def is_latin(s: str) -> bool:
    return bool(s) and not re.search(r"[　-鿿＀-￯]", s)


def apply_corrections(latin: list[str], corrections) -> tuple[list[str], list[tuple]]:
    applied = []
    out = list(latin)
    for k, wrong, right in corrections or []:
        if 1 <= k <= len(out) and wrong in out[k - 1]:
            out[k - 1] = out[k - 1].replace(wrong, right, 1)
            applied.append((k, wrong, right))
    return out, applied


def render_book(nn: str, anchors: list, corrections_log: list, names_log: dict) -> str:
    k = int(nn)
    latin = (LATIN_CLEAN / f"{nn}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    meta, sections, textnotes, names, problems = parse(nn)
    if problems:
        raise SystemExit(f"book {nn}: parse problems: {problems[:5]}")
    latin, applied = apply_corrections(latin, meta.get("corrections"))
    for a in applied:
        corrections_log.append((k,) + a)
    for la, zh in names:
        names_log.setdefault(la, set()).add(zh)
    out = []
    bid = f"b{k}"
    anchors.append((bid, f"第{CN[k-1]}卷", LATIN_TITLES[k - 1], [(f"b{k}s{i}", s["start"], s["end"], s["title"]) for i, s in enumerate(sections)]))
    out.append(f'<section class="bookopen"><h1 class="book" id="{bid}">第{CN[k-1]}卷</h1>')
    out.append(f'<div class="latt">{LATIN_TITLES[k-1]}</div>')
    summ = "".join(meta["summary"]) if meta["summary"] else ""
    paras = [p for p in re.split(r"\s*\n\s*|(?<=。)\s{2,}", "\n".join(meta["summary"])) if p.strip()]
    out.append('<div class="summary"><div class="lab">本卷提要</div>')
    for p in paras or [summ]:
        out.append(f"<p>{esc(p)}</p>")
    out.append("</div>")
    out.append('<div class="booktoc"><div class="lab">本卷段落</div><ul>')
    for i, s in enumerate(sections):
        out.append(f'<li><a href="#b{k}s{i}"><span class="r">{s["start"]}–{s["end"]}</span>{esc(s["title"])}</a></li>')
    out.append("</ul></div></section>")
    out.append('<section class="bookbody">')
    for i, s in enumerate(sections):
        out.append(f'<h3 class="sec" id="b{k}s{i}"><span class="rng">{s["start"]}–{s["end"]}</span>{esc(s["title"])}</h3>')
        out.append('<table class="par"><colgroup><col class="cla"><col class="cn"><col class="czh"></colgroup>')
        zh = dict(s["lines"])
        for n in range(s["start"], s["end"] + 1):
            num = str(n) if n % 5 == 0 else ""
            out.append(f'<tr><td class="vla">{esc(latin[n-1])}</td><td class="vn">{num}</td><td class="vzh">{esc(zh.get(n, ""))}</td></tr>')
        out.append("</table>")
        if s["notes"]:
            out.append('<div class="notes">')
            for note in s["notes"]:
                ln = f'{note["start"]}' if note["start"] == note["end"] else f'{note["start"]}–{note["end"]}'
                lem = note["lemma"]
                if lem:
                    lem_html = f'<span class="lem">{esc(lem)}</span>' if is_latin(lem) else f'<span class="lemzh">{esc(lem)}</span>'
                else:
                    lem_html = ""
                out.append(f'<p><span class="nl">{ln}</span>{lem_html}{esc(note["text"])}</p>')
            out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


def group_names(names_log: dict) -> list:
    """names_log: raw Latin string -> set of raw Chinese strings. Returns [(latin_keys, zh_primary)]."""
    def clean(z):
        z = re.sub(r"（[^）]*）|\([^)]*\)", "", z)
        return z.strip(" 　，,；;")
    groups = {}
    for la, zhs in names_log.items():
        la_c = re.sub(r"（[^）]*）|\([^)]*\)", "", la)
        keys = [k.strip() for k in re.split(r"[,/，;；]", la_c) if k.strip()]
        for z in zhs:
            zc = clean(z)
            if not zc or not keys:
                continue
            primary = re.split(r"[，,；;/]| / ", zc)[0].strip()
            g = groups.setdefault(primary, [])
            for k in keys:
                if k not in g:
                    g.append(k)
    # fold adjective forms (X的) and geographic suffixes (X山/X河/X火山) into the base entry
    for zh in sorted(groups, key=len, reverse=True):
        for suf in ("的", "火山", "山", "河"):
            if zh.endswith(suf) and zh[: -len(suf)] in groups and zh in groups:
                base = groups[zh[: -len(suf)]]
                for k in groups.pop(zh):
                    if k not in base:
                        base.append(k)
                break
    out = []
    for zh, keys in groups.items():
        keys = sorted(set(keys), key=lambda k: (k.lower(), k))
        out.append((keys, zh))
    out.sort(key=lambda x: (x[0][0].lower(), x[1]))
    return out


def render_elevenlabs(books: list[str]) -> str:
    from elevenlabs import chunks, load_tts, ROMAN
    stats = {"lines": 0, "full": 0, "half": 0, "plain": 0}
    for nn in books:
        for n, r in load_tts(nn).items():
            stats["lines"] += 1
            acc = bool(re.search(r"[áéíóúÁÉÍÓÚ]", r["tts"]))
            if not acc:
                stats["plain"] += 1
            elif r["feet"].count("|") >= 5:
                stats["full"] += 1
            else:
                stats["half"] += 1
    guide = (FRONT / "elevenlabs_guide.html").read_text(encoding="utf-8")
    for k, v in stats.items():
        guide = guide.replace("{" + k + "}", f"{v:,}")
    out = ['<section class="front guide">', guide, "</section>", '<section class="front elapx">']
    for nn in books:
        k = int(nn)
        out.append(f'<h3 class="elbook" id="el{k}">第{CN[k-1]}卷<span class="la">{LATIN_TITLES[k-1]}</span></h3><div class="elcols">')
        for c in chunks(nn):
            head = (f'<span class="la">{ROMAN[k-1]}.{c["start"]}–{c["end"]}</span>　{esc(c["title"])}'
                    f'　·　<span class="la">{c["chars"]:,}</span> 字符')
            body = "".join(f"<div>{esc(x)}</div>" for x in c["text"].split("\n"))
            body = re.sub(r"\[[^\]<]+\]", lambda m: f'<span class="tg">{m.group(0)}</span>', body)
            out.append(f'<div class="elchunk"><div class="elhead">{head}</div><div class="eltext">{body}</div></div>')
        out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


def build(books: list[str], out_pdf: Path, html_only: bool):
    anchors, corr_log, names_log = [], [], {}
    body_books = [render_book(nn, anchors, corr_log, names_log) for nn in books]
    front = FRONT

    def frag(name):
        p = front / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    parts = ['<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><title>阿非利加</title>',
             f"<style>{CSS}</style></head><body>"]
    parts.append(frag("title.html"))
    # table of contents
    parts.append('<section class="front"><h2 class="fm" id="toc">目　录</h2><ul class="toc">')
    for fid, ftitle in [("preface", "译者前言"), ("conventions", "底本与体例"), ("persons", "主要人物")]:
        if (front / f"{fid}.html").exists():
            parts.append(f'<li><a href="#{fid}">{ftitle}</a></li>')
    for bid, zt, lt, secs in anchors:
        parts.append(f'<li><a href="#{bid}">{zt}　<span class="la">{lt}</span></a></li>')
    parts.append('<li><a href="#apx-corr">附录一　拉丁原文校改表</a></li>')
    parts.append('<li><a href="#apx-names">附录二　专名译名对照</a></li>')
    parts.append('<li><a href="#apx-el">附录三　ElevenLabs 朗读稿（拉丁原文，按格律标注）</a></li>')
    parts.append("</ul></section>")
    for name in ["preface.html", "conventions.html", "persons.html"]:
        parts.append(frag(name))
    parts.extend(body_books)
    # appendix 1: corrections
    parts.append('<section class="front"><h2 class="fm" id="apx-corr">附录一　拉丁原文校改表</h2>')
    parts.append("<p style=\"text-align:left\">下表列出本书所印拉丁原文中改正的数字版扫描、录入错误（不涉及校勘异文）。“原作”为 Itinera Electronica 数字版的字样。</p>")
    parts.append('<div class="cols3">')
    for b, k, w, r in corr_log:
        parts.append(f'<p>{CN[b-1]}.<span class="la">{k}　<i>{esc(w)}</i> → <i>{esc(r)}</i></span></p>')
    parts.append("</div></section>")
    # appendix 2: names
    parts.append('<section class="front"><h2 class="fm" id="apx-names">附录二　专名译名对照</h2>')
    parts.append("<p style=\"text-align:left\">下表汇集本书所用的人名、地名、神名及拟人化名称的译名，按拉丁字母顺序排列；同一译名的不同拉丁形式（含名词与形容词、中世纪拼写）合为一条。</p>")
    parts.append('<div class="cols2">')
    for keys, zh in group_names(names_log):
        parts.append(f'<p><span class="la">{esc(", ".join(keys))}</span>　{esc(zh)}</p>')
    parts.append("</div></section>")
    # appendix 3: ElevenLabs recitation text
    parts.append(render_elevenlabs(books))
    parts.append("</body></html>")
    doc = "\n".join(parts)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out_html = out_pdf.with_suffix(".html")
    out_html.write_text(doc, encoding="utf-8")
    print("html:", out_html, len(doc))
    if html_only:
        return
    from weasyprint import HTML
    HTML(string=doc, base_url=str(ROOT)).write_pdf(str(out_pdf))
    print("pdf:", out_pdf)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default="01,02,03,04,05,06,07,08,09")
    ap.add_argument("--out", default=str(BUILD / "africa.pdf"))
    ap.add_argument("--html-only", action="store_true")
    a = ap.parse_args()
    build(a.books.split(","), Path(a.out), a.html_only)
