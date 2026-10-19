"""Run the hexameter scanner over all books (with printed corrections applied).

Usage: python3 scan_all.py [NN ...]   -> writes build/scan_auto/NN.tsv (automatic scan only) and prints stats
TSV columns: line_no, status (ok|amb|fail|lacuna|manual), pattern, candidates, latin
Manual scansions in source/scansion/overrides/NN.tsv (line_no<TAB>pattern<TAB>optional elision overrides) override automatic ones.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
sys.path.insert(0, str(ROOT / "tools"))
from validate import parse  # noqa: E402
from build import apply_corrections  # noqa: E402
from scan import scan_line  # noqa: E402


def load_latin(nn):
    latin = (LATIN_CLEAN / f"{nn}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    meta, *_ = parse(nn)
    latin, _ = apply_corrections(latin, meta.get("corrections"))
    return latin


def is_fragment(line):
    return "…" in line or "..." in line or "*" in line or len(line.split()) < 4


def run(nn):
    latin = load_latin(nn)
    rows = []
    stats = {"ok": 0, "amb": 0, "fail": 0, "frag": 0}
    for i, l in enumerate(latin, 1):
        if is_fragment(l):
            r = scan_line(l)
            st = "frag"
        else:
            r = scan_line(l)
            st = "fail" if not r["ok"] else ("amb" if r.get("ambiguous") else "ok")
        stats[st] += 1
        rows.append((i, st, r.get("pattern") or "", json.dumps(r.get("candidates", [])[:4]), l))
    out = BUILD / "scan_auto" / f"{nn}.tsv"  # raw automatic scan, for debugging only
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join("\t".join(map(str, row)) for row in rows) + "\n", encoding="utf-8")
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
