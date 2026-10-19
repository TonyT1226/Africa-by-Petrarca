"""Export the edition as line-addressed data for people and agents.

Usage: python3 tools/export.py
Reads source/ (and data/scansion/, produced by recite.py) and writes:
  data/books.json          one record per book (titles, line and section counts, summary)
  data/lines.jsonl         one record per verse, id "africa.B.N" (Latin, Chinese, scansion, recitation, notes)
  data/sections.jsonl      one record per section, id "africa.B.sK"
  data/notes.jsonl         commentary and textual notes, id "africa.B.nK" / "africa.B.tK"
  data/names.tsv           proper names: Latin forms -> Chinese rendering, books where they occur
  data/corrections.tsv     misprints of the digital Latin text corrected in this edition
  data/tei/africa_NN.xml   TEI P5 per book (Latin edition + Chinese translation + notes)
  text/NN_liber_*.md       parallel Latin–Chinese text in Markdown, readable on GitHub
Everything here is generated: edit source/ and re-run, never edit the outputs by hand.
"""
import json
import re
import sys
import unicodedata
from xml.sax.saxutils import escape as xesc

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
from validate import parse  # noqa: E402
from build import apply_corrections, group_names, LATIN_TITLES  # noqa: E402
from elevenlabs import load_tts, load_tags  # noqa: E402
from scan import base_units, norm_word  # noqa: E402

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
LATIN_ORD = ["primus", "secundus", "tertius", "quartus", "quintus", "sextus", "septimus", "octavus", "nonus"]
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


def lid(b, n):
    return f"africa.{b}.{n}"


def _base_char(c):
    d = unicodedata.normalize("NFD", c)
    return d[0] if d else c


def pattern_from_feet(feet: str):
    """Derive the D/S pattern from a foot-divided line (used for reviewed lines).

    Whole words are syllabified (so word-level rules apply), then the vowel nuclei are counted
    between the foot bars. Returns None when the result is not a clean six-foot hexameter."""
    cuts, chars = [], []
    for c in unicodedata.normalize("NFC", feet):
        if c == "|":
            cuts.append(len(chars))
        else:
            chars.append(_base_char(c))
    if len(cuts) != 5:
        return None
    text = "".join(chars).replace("v", "t").replace("V", "T")  # written v is always consonantal here
    counts = [0] * 6
    for m in re.finditer(r"[A-Za-z]+", text):
        for u in base_units(norm_word(m.group(0))):
            if u["t"] == "V":
                pos = m.start() + u["i"]
                counts[sum(1 for c in cuts if c <= pos)] += 1
    out = []
    for i, k in enumerate(counts):
        if i == 5:
            if k != 2:
                return None
            out.append("X")
        elif k in (2, 3):
            out.append("SD"[k - 2])
        else:
            return None
    return "".join(out)


def slug(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "x"


def jdump(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def md_cell(s):
    return (s or "").replace("|", "\\|")


def main():
    books, lines_out, sections_out, notes_out, corr_out = [], [], [], [], []
    names_log, names_books = {}, {}
    tei_docs, md_docs = {}, {}
    derived_fail = 0
    for nn in BOOKS:
        b = int(nn)
        meta, sections, textnotes, names, problems = parse(nn)
        if problems:
            raise SystemExit(f"book {nn}: {problems[:3]}")
        latin_src = (LATIN_CLEAN / f"{nn}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
        latin, applied = apply_corrections(latin_src, meta.get("corrections"))
        for k, wrong, right in applied:
            corr_out.append((b, k, lid(b, k), wrong, right))
        scan = load_tts(nn)
        tags = load_tags(nn)
        for la, zh in names:
            names_log.setdefault(la, set()).add(zh)
            names_books.setdefault(la, set()).add(b)
        summary = "\n".join(meta["summary"]).strip()
        books.append({"book": b, "id": f"africa.{b}", "title_la": LATIN_TITLES[b - 1], "title_zh": meta["title"],
                      "lines": len(latin), "sections": len(sections), "summary_zh": summary})
        # notes
        line_notes = {}
        note_recs = []
        for si, s in enumerate(sections, 1):
            for note in s["notes"]:
                nid = f"africa.{b}.n{len(note_recs) + 1:03d}"
                note_recs.append({"id": nid, "book": b, "type": "commentary", "section": f"africa.{b}.s{si:02d}",
                                  "start": note["start"], "end": note["end"], "lemma": note["lemma"] or None,
                                  "text_zh": note["text"]})
        for ti, (rng, lemma, text) in enumerate(textnotes, 1):
            a, _, z = rng.partition("-")
            nid = f"africa.{b}.t{ti:03d}"
            note_recs.append({"id": nid, "book": b, "type": "textual", "section": None, "start": int(a),
                              "end": int(z or a), "lemma": lemma or None, "text_zh": text})
        for r in note_recs:
            for n in range(r["start"], r["end"] + 1):
                line_notes.setdefault(n, []).append(r["id"])
        notes_out.extend(note_recs)
        # lines and sections
        tei_la, tei_zh, md = [], [], []
        md.append(f"# 第{'一二三四五六七八九'[b-1]}卷 · Africa, Liber {LATIN_ORD[b-1].capitalize()}\n")
        md.append(f"> 本卷提要：{summary}\n")
        md.append("拉丁原文与中文译文逐行对照；行号与 PDF 版一致。引用编号格式为 `africa.卷.行`，"
                  "例如本卷第 1 行是 `" + lid(b, 1) + "`。注释见每段之后。\n")
        md.append("## 段落\n")
        for si, s in enumerate(sections, 1):
            md.append(f"- [{s['start']}–{s['end']}　{s['title']}](#s{si:02d})")
        md.append("")
        for si, s in enumerate(sections, 1):
            sid = f"africa.{b}.s{si:02d}"
            sections_out.append({"id": sid, "book": b, "index": si, "start": s["start"], "end": s["end"],
                                 "title_zh": s["title"], "delivery": tags.get(s["start"])})
            zh = dict(s["lines"])
            tei_la.append(f'<div type="textpart" subtype="section" n="{si}" xml:id="{sid}">')
            tei_la.append(f'<head xml:lang="zh-Hans">{xesc(s["title"])}</head>')
            tei_zh.append(f'<div type="textpart" subtype="section" n="{si}" corresp="#{sid}">')
            tei_zh.append(f'<head>{xesc(s["title"])}</head>')
            md.append(f'<a id="s{si:02d}"></a>\n### {s["start"]}–{s["end"]}　{s["title"]}\n')
            md.append("| 行 | Latina | 中文 |\n|---:|---|---|")
            for n in range(s["start"], s["end"] + 1):
                row = scan[n]
                pattern = row["pattern"] or None
                if row["status"] == "man":
                    pattern = pattern_from_feet(row["feet"])
                    if pattern is None and row["feet"].count("|") == 5:
                        derived_fail += 1
                if pattern and (len(pattern) != 6 or not pattern.endswith("X")):
                    pattern = None  # half-lines carry a partial pattern only in data/scansion
                rec = {
                    "id": lid(b, n), "book": b, "line": n, "section": sid,
                    "latin": latin[n - 1],
                    "latin_digital": latin_src[n - 1] if latin_src[n - 1] != latin[n - 1] else None,
                    "zh": zh.get(n, ""),
                    "scansion": {"pattern": pattern, "feet": row["feet"], "status": row["status"]},
                    "recitation": row["tts"],
                    "delivery": tags.get(n),
                    "notes": line_notes.get(n, []),
                }
                lines_out.append(rec)
                met = f' met="{pattern}"' if pattern else ""
                tei_la.append(f'<l n="{n}" xml:id="{lid(b, n)}"{met}>{xesc(latin[n - 1])}</l>')
                tei_zh.append(f'<l n="{n}" corresp="#{lid(b, n)}">{xesc(zh.get(n, ""))}</l>')
                md.append(f"| {n} | {md_cell(latin[n - 1])} | {md_cell(zh.get(n, ''))} |")
            tei_la.append("</div>")
            tei_zh.append("</div>")
            md.append("")
            sn = [r for r in note_recs if r["section"] == sid]
            if sn:
                md.append("**注释**\n")
                for r in sn:
                    rng = f"{r['start']}" if r["start"] == r["end"] else f"{r['start']}–{r['end']}"
                    lem = f" *{r['lemma']}*" if r["lemma"] else ""
                    md.append(f"- **{rng}**{lem}　{r['text_zh']}")
                md.append("")
        tn = [r for r in note_recs if r["type"] == "textual"]
        if tn:
            md.append("## 文本注\n")
            for r in tn:
                rng = f"{r['start']}" if r["start"] == r["end"] else f"{r['start']}–{r['end']}"
                lem = f" *{r['lemma']}*" if r["lemma"] else ""
                md.append(f"- **{rng}**{lem}　{r['text_zh']}")
            md.append("")
        md_docs[f"{nn}_liber_{LATIN_ORD[b-1]}.md"] = "\n".join(md) + "\n"
        tei_docs[nn] = tei_book(b, nn, meta, summary, tei_la, tei_zh, note_recs)
    # names
    names_rows = []
    for keys, zh in group_names(names_log):
        bk = set()
        for la, zhs in names_log.items():
            if any(k in la for k in keys):
                bk |= names_books.get(la, set())
        names_rows.append((", ".join(keys), zh, ",".join(str(x) for x in sorted(bk))))
    # write
    DATA.mkdir(exist_ok=True)
    (DATA / "books.json").write_text(json.dumps(books, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    jdump(DATA / "lines.jsonl", lines_out)
    jdump(DATA / "sections.jsonl", sections_out)
    jdump(DATA / "notes.jsonl", notes_out)
    (DATA / "names.tsv").write_text("latin\tzh\tbooks\n" + "".join("\t".join(r) + "\n" for r in names_rows),
                                    encoding="utf-8")
    (DATA / "corrections.tsv").write_text(
        "book\tline\tid\tdigital_text\tcorrected\n" + "".join("\t".join(map(str, r)) + "\n" for r in corr_out),
        encoding="utf-8")
    TEI.mkdir(parents=True, exist_ok=True)
    for nn, doc in tei_docs.items():
        (TEI / f"africa_{nn}.xml").write_text(doc, encoding="utf-8")
    TEXT.mkdir(exist_ok=True)
    for name, doc in md_docs.items():
        (TEXT / name).write_text(doc, encoding="utf-8")
    print(f"{len(lines_out)} lines, {len(sections_out)} sections, {len(notes_out)} notes, "
          f"{len(names_rows)} names, {len(corr_out)} corrections; "
          f"{derived_fail} reviewed lines without a derivable pattern")


def tei_book(b, nn, meta, summary, tei_la, tei_zh, note_recs):
    notes = []
    for r in note_recs:
        target = " ".join(f"#{lid(b, n)}" for n in range(r["start"], r["end"] + 1))
        lem = f'<term xml:lang="la">{xesc(r["lemma"])}</term> ' if r["lemma"] else ""
        notes.append(f'<note xml:id="{r["id"]}" type="{r["type"]}" target="{target}">{lem}{xesc(r["text_zh"])}</note>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
<fileDesc>
<titleStmt>
<title xml:lang="la">Africa, {LATIN_TITLES[b-1].title()}</title>
<title xml:lang="zh-Hans">阿非利加 · {xesc(meta["title"])}（拉中对照注释本）</title>
<author>Francesco Petrarca</author>
<respStmt><resp>Chinese translation, notes, scansion (AI-generated, AI-reviewed)</resp><name>Claude (Anthropic)</name></respStmt>
</titleStmt>
<publicationStmt>
<publisher>Africa-by-Petrarca project</publisher>
<availability><licence target="{LICENSE_URL}">Translation, notes and annotations: CC BY 4.0. The Latin text is the public-domain poem as transmitted by the Itinera Electronica digital text; see README.</licence></availability>
</publicationStmt>
<sourceDesc><p>Latin text: digital text of Itinera Electronica (Bibliotheca Classica Selecta, UCLouvain); Books I–II in classicising spelling (Pingaud 1872 tradition), Books III–IX in medieval spelling (Festa 1926 tradition). Mechanical misprints corrected and listed in data/corrections.tsv.</p></sourceDesc>
</fileDesc>
<encodingDesc>
<metDecl><p>@met on each verse gives the dactylic hexameter pattern: one letter per foot, D = dactyl, S = spondee, X = final foot. Full foot division in data/scansion/{nn}.tsv.</p></metDecl>
</encodingDesc>
<profileDesc><abstract xml:lang="zh-Hans"><p>{xesc(summary)}</p></abstract></profileDesc>
</teiHeader>
<text>
<body>
<div type="edition" xml:lang="la" n="{b}">
{chr(10).join(tei_la)}
</div>
<div type="translation" xml:lang="zh-Hans" n="{b}">
{chr(10).join(tei_zh)}
</div>
<div type="commentary" xml:lang="zh-Hans">
{chr(10).join(notes)}
</div>
</body>
</text>
</TEI>
"""


if __name__ == "__main__":
    main()
