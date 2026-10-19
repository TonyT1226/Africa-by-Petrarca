"""Collect #NAMES across books and report inconsistent Chinese renderings.

Usage: python3 names.py            -> prints conflicts (same Latin name, different Chinese)
       python3 names.py --json F   -> also writes the grouped table to F
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403
sys.path.insert(0, str(ROOT / "tools"))
from validate import parse  # noqa: E402


def clean_zh(z: str) -> str:
    z = re.sub(r"（[^）]*）|\([^)]*\)", "", z)  # drop parenthetical remarks like （注中）
    z = z.split("；")[0].split(";")[0]
    return z.strip(" 　，,")


def latin_keys(la: str) -> list[str]:
    la = re.sub(r"（[^）]*）|\([^)]*\)", "", la)
    keys = [k.strip() for k in re.split(r"[,/，]", la) if k.strip()]
    return keys


def collect():
    table = defaultdict(lambda: defaultdict(set))  # key -> zh -> {books}
    for nn in [f"{i:02d}" for i in range(1, 10)]:
        p = TRANSLATION / f"{nn}.txt"
        if not p.exists():
            continue
        _, _, _, names, _ = parse(nn)
        for la, zh in names:
            z = clean_zh(zh)
            for k in latin_keys(la):
                table[k.lower()][z].add(int(nn))
    return table


if __name__ == "__main__":
    table = collect()
    conflicts = {k: v for k, v in table.items() if len(v) > 1}
    for k in sorted(conflicts):
        print(k, "|", " ; ".join(f"{z}{sorted(b)}" for z, b in sorted(conflicts[k].items())))
    print(f"\n{len(table)} keys, {len(conflicts)} with conflicting renderings", file=sys.stderr)
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        Path(out).write_text(json.dumps({k: {z: sorted(b) for z, b in v.items()} for k, v in table.items()},
                                        ensure_ascii=False, indent=1), encoding="utf-8")
