"""Check manual scansion overrides (source/scansion/overrides/NN.tsv) and tag files (source/recitation/tags/NN.tsv).

Usage: python3 check_manual.py NN [NN ...]
Reports: bad format, wrong number of feet, foot without exactly one ictus accent at its first vowel,
text drifting from the source line, tags at unknown lines / missing section-start tags.
"""
import difflib
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
sys.path.insert(0, str(ROOT / "tools"))
from validate import parse  # noqa: E402
from scan_all import load_latin  # noqa: E402
from recite import LACUNA, fix_quotes, syllable_count_short  # noqa: E402
from render import render_line  # noqa: E402

ACC = "áéíóúýÁÉÍÓÚÝ"
VOW = "aeiouyAEIOUY" + ACC


def plain(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower().replace("v", "u").replace("j", "i")
    return re.sub(r"[^a-z]", "", s)


def first_vowel_ok(seg):
    s = unicodedata.normalize("NFC", seg)
    i = 0
    while i < len(s):
        c = s[i]
        if c in VOW:
            low = c.lower()
            prev = s[i - 1].lower() if i else ""
            nxt = s[i + 1] if i + 1 < len(s) else ""
            if low == "u" and prev in ("q", "g", "s") and nxt in VOW:
                i += 1
                continue
            if low == "i" and (i == 0 or not s[i - 1].isalpha()) and nxt in VOW and nxt.lower() != "i":
                i += 1
                continue
            return c in ACC
        i += 1
    return False


def check(nn):
    probs = []
    auto = {}
    for l in (SCANSION / f"{nn}.tsv").read_text(encoding="utf-8").splitlines():
        f = l.split("\t")
        auto[int(f[0])] = f
    latin = load_latin(nn)
    mp = SCAN_OVERRIDES / f"{nn}.tsv"
    if mp.exists():
        for ln, l in enumerate(mp.read_text(encoding="utf-8").splitlines(), 1):
            if not l.strip() or l.startswith("#"):
                continue
            if "\t" not in l:
                probs.append(f"manual:{ln}: no TAB")
                continue
            n, feet = l.split("\t", 1)
            if not n.isdigit() or int(n) not in auto:
                probs.append(f"manual:{ln}: bad line number {n!r}")
                continue
            n = int(n)
            segs = feet.split("|")
            src = fix_quotes(latin[n - 1])
            short = bool(LACUNA.search(src)) or syllable_count_short(src)
            if not short and len(segs) != 6 and "NOSCAN" not in feet:
                probs.append(f"{n}: {len(segs)} feet (expected 6)")
            for si, seg in enumerate(segs):
                nacc = sum(1 for c in unicodedata.normalize("NFC", seg) if c in ACC)
                if "NOSCAN" in feet:
                    break
                if nacc != 1:
                    probs.append(f"{n}: foot {si+1} has {nacc} ictus accents: {seg!r}")
                elif not first_vowel_ok(seg):
                    probs.append(f"{n}: foot {si+1} accent not on its first vowel: {seg!r}")
            a = plain(render_line(src)["feet"])
            b = plain(feet.replace("NOSCAN", ""))
            r = difflib.SequenceMatcher(None, a, b).ratio()
            if r < 0.9:
                probs.append(f"{n}: text differs from source (ratio {r:.2f}): {src!r} vs {feet!r}")
    tp = RECITATION_TAGS / f"{nn}.tsv"
    if tp.exists():
        meta, sections, *_ = parse(nn)
        starts = {s["start"] for s in sections}
        tagged = set()
        for ln, l in enumerate(tp.read_text(encoding="utf-8").splitlines(), 1):
            if not l.strip() or l.startswith("#"):
                continue
            if "\t" not in l:
                probs.append(f"tags:{ln}: no TAB")
                continue
            n, tag = l.split("\t", 1)
            if not n.isdigit() or int(n) not in auto:
                probs.append(f"tags:{ln}: bad line number {n!r}")
                continue
            if "[" in tag or "]" in tag:
                probs.append(f"tags:{ln}: write the tag without brackets")
            if len(tag.split()) > 6:
                probs.append(f"tags:{ln}: tag too long ({tag!r})")
            if int(n) in tagged:
                probs.append(f"tags:{ln}: two tags for line {n}")
            tagged.add(int(n))
        miss = sorted(starts - tagged)
        if miss:
            probs.append(f"tags: section starts without a tag: {miss}")
    else:
        probs.append("tags file missing")
    return probs


if __name__ == "__main__":
    for nn in sys.argv[1:]:
        p = check(nn)
        print(nn, "OK" if not p else f"{len(p)} problem(s)")
        for x in p:
            print("  ", x)
