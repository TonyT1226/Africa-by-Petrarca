"""Produce the scanned / ElevenLabs-ready Latin for every book.

Usage: python3 recite.py [NN ...]
Writes data/scansion/NN.tsv with columns: line, status, pattern, notes, feet, tts
status: ok | amb | var (needed a variant: synizesis, hiatus ...) | irr (no hexameter found) | frag (half line / lacuna)
        | man (manual override from source/scansion/overrides/NN.tsv)
Manual overrides: source/scansion/overrides/NN.tsv lines "N<TAB>feet display" (feet display = tts text with | between feet).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
sys.path.insert(0, str(ROOT / "tools"))
from scan_all import load_latin  # noqa: E402
from render import render_line  # noqa: E402

LACUNA = re.compile(r"\(\s*-(\s*-)+\s*\)|-(\s*-){2,}|<\s*>")


def tts_clean(s: str) -> str:
    s = LACUNA.sub("…", s).replace("...", "…")
    s = re.sub(r"(^|[\s(«])'(?=\w)", r'\1"', s)  # single quotation marks -> double (apostrophe is the elision sign)
    s = re.sub(r"(?<=[\w.,;:!?])'(?=\s|$|[.,;:!?])", "'", s)
    s = re.sub(r"\s+([:;?!»])", r"\1", s)
    s = re.sub(r"«\s+", "«", s)
    s = re.sub(r" {2,}", " ", s).strip()
    s = re.sub(r"…\s*\.", "…", s)
    return s


def fix_quotes(raw: str) -> str:
    # single quotes used as quotation marks in Book VII -> double, before scanning
    return re.sub(r"(?<![A-Za-z])'|'(?![A-Za-z])", '"', raw)


def load_manual(nn):
    p = SCAN_OVERRIDES / f"{nn}.tsv"
    out = {}
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if not l.strip() or l.startswith("#"):
                continue
            n, feet = l.split("\t", 1)
            out[int(n)] = feet.strip()
    return out


def syllable_count_short(line):
    from scan import scan_line
    r = scan_line(line)
    return len(r.get("syllables", [])) < 12


def run(nn):
    latin = load_latin(nn)
    manual = load_manual(nn)
    rows = []
    stats = {}
    for n, raw in enumerate(latin, 1):
        line = fix_quotes(raw)
        lacuna = bool(LACUNA.search(line))
        frag = lacuna or syllable_count_short(line)
        d = render_line(line)
        if n in manual:
            feet = manual[n]
            status, pattern, notes = "man", "", "manual"
        else:
            feet = d["feet"]
            pattern = d["pattern"] or ""
            notes = " ".join(d["notes"])
            if frag:
                status = "frag"
                if lacuna:
                    feet = d["tts"].replace("|", "")
            elif d["status"] != "ok":
                status = "irr"
            elif d["notes"]:
                status = "var"
            elif d["ambiguous"]:
                status = "amb"
                notes = json.dumps(d["candidates"][:3])
            else:
                status = "ok"
        if feet.startswith("NOSCAN"):
            feet = feet[len("NOSCAN"):].strip()
        tts = tts_clean(feet.replace("|", ""))
        if (status == "irr" or lacuna or (status == "frag" and not d["pattern"])) and n not in manual:
            # no reliable feet: keep the words plain (v-normalised) without ictus marks
            tts = tts_clean(d["tts"])
        stats[status] = stats.get(status, 0) + 1
        rows.append((n, status, pattern, notes, tts_clean(feet), tts))
    out = SCANSION / f"{nn}.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join("\t".join(map(str, r)) for r in rows) + "\n", encoding="utf-8")
    return stats


if __name__ == "__main__":
    books = sys.argv[1:] or [f"{i:02d}" for i in range(1, 10)]
    tot = {}
    for nn in books:
        s = run(nn)
        print(nn, s)
        for k, v in s.items():
            tot[k] = tot.get(k, 0) + v
    print("total", tot)
