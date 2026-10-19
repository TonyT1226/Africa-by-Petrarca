"""Assemble the ElevenLabs-ready chunks (one per section) and export plain-text files.

Usage: python3 elevenlabs.py            -> writes build/elevenlabs/Africa_NN_*.txt and Africa_all.txt
Library: chunks(nn) -> list of dicts {start, end, title, text, chars}
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
sys.path.insert(0, str(ROOT / "tools"))
from validate import parse  # noqa: E402

GLOBAL_TAG = "measured epic recitation"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def load_tts(nn):
    rows = {}
    for l in (SCANSION / f"{nn}.tsv").read_text(encoding="utf-8").splitlines():
        f = l.split("\t")
        rows[int(f[0])] = {"status": f[1], "pattern": f[2], "feet": f[4], "tts": f[5]}
    return rows


def load_tags(nn):
    tags = {}
    p = RECITATION_TAGS / f"{nn}.tsv"
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if "\t" in l and not l.startswith("#"):
                n, t = l.split("\t", 1)
                if n.strip().isdigit():
                    tags[int(n)] = t.strip().strip("[]").strip()
    return tags


def chunks(nn):
    rows = load_tts(nn)
    tags = load_tags(nn)
    meta, sections, *_ = parse(nn)
    out = []
    for s in sections:
        lines = []
        head = f"[{GLOBAL_TAG}]"
        if s["start"] in tags:
            head += f" [{tags[s['start']]}]"
        lines.append(head)
        for n in range(s["start"], s["end"] + 1):
            t = rows[n]["tts"]
            if not t.strip() or t.strip() == "…":
                t = "…"
            if n in tags and n != s["start"]:
                lines.append(f"[{tags[n]}]")
            lines.append(t)
        text = "\n".join(lines)
        out.append({"start": s["start"], "end": s["end"], "title": s["title"], "text": text, "chars": len(text)})
    return out


def export():
    outdir = RECITATION
    outdir.mkdir(parents=True, exist_ok=True)
    allparts = []
    for i in range(1, 10):
        nn = f"{i:02d}"
        parts = []
        for c in chunks(nn):
            sep = f"===== Africa {ROMAN[i-1]}.{c['start']}–{c['end']} | {c['title']} | {c['chars']} chars ====="
            parts.append(sep + "\n" + c["text"] + "\n")
        body = "\n".join(parts)
        (outdir / f"Africa_{nn}_Liber_{ROMAN[i-1]}.txt").write_text(body, encoding="utf-8")
        allparts.append(body)
    (outdir / "Africa_all_books.txt").write_text("\n".join(allparts), encoding="utf-8")
    return outdir


if __name__ == "__main__":
    d = export()
    mx = max((c["chars"], nn, c["start"]) for nn in [f"{i:02d}" for i in range(1, 10)] for c in chunks(nn))
    print("exported to", d, "largest chunk", mx)
