"""Normalize raw Itinera Electronica page text into one verse per line.

Usage: python3 clean_latin.py NN   (reads source/latin/raw/NN.txt, writes source/latin/clean/NN.txt)

1. Normalizes exactly as the browser-side check does and prints the line count,
   sha256 and per-50-line chunk hashes of the *raw* normalized text, so the saved
   transcription can be compared with the web page.
2. Applies structural fixes from source/latin/fixes.json (e.g. a half-line verse that the
   web page split over two display lines) and then checks that every line number
   printed on the page (every 5th line, and the [b,50] markers) equals the
   verse's position. Fails loudly if not.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403


def normalize(text: str) -> list[tuple[str, int | None]]:
    out = []
    for line in text.split("\n"):
        line = line.replace(" ", " ").strip()
        num = None
        m = re.match(r"^\[\d+,(\d+)\]\s*", line)
        if m:
            num = int(m.group(1))
            line = line[m.end():]
        m = re.match(r"^(\d+)\s+", line)
        if m:
            num = int(m.group(1))
            line = line[m.end():]
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        if re.match(r"^(LIBER|LIVRE)\b", line):
            continue
        out.append((line, num if num else None))
    return out


def digest(lines: list[str]) -> tuple[str, list[str]]:
    full = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    chunks = []
    for i in range(0, len(lines), 50):
        h = hashlib.sha256("\n".join(lines[i:i + 50]).encode("utf-8")).hexdigest()[:8]
        chunks.append(h)
    return full, chunks


def apply_fixes(nn: str, items: list[tuple[str, int | None]]) -> list[tuple[str, int | None]]:
    fixes_path = LATIN_FIXES
    if not fixes_path.exists():
        return items
    fixes = json.loads(fixes_path.read_text(encoding="utf-8")).get(nn, {})
    # merges: list of 1-based positions in the raw normalized list; line k is joined with k+1
    for k in sorted(fixes.get("merge", []), reverse=True):
        a, na = items[k - 1]
        b, nb = items[k]
        items[k - 1:k + 1] = [(a + " … " + b, na if na is not None else nb)]
    return items


if __name__ == "__main__":
    nn = sys.argv[1]
    raw = (LATIN_RAW / f"{nn}.txt").read_text(encoding="utf-8")
    items = normalize(raw)
    full, chunks = digest([t for t, _ in items])
    print("raw:", len(items), full)
    print(" ".join(chunks))
    items = apply_fixes(nn, items)
    # number_offset: [[from_printed_number, offset], ...] — where the source's own printed
    # numbering skips a line, positions from that printed number on are expected to be n + offset.
    fixes_path = LATIN_FIXES
    offsets = json.loads(fixes_path.read_text(encoding="utf-8")).get(nn, {}).get("number_offset", []) \
        if fixes_path.exists() else []

    def expected(n: int) -> int:
        off = 0
        for start, o in offsets:
            if n >= start:
                off = o
        return n + off

    bad = [(i + 1, n, t[:40]) for i, (t, n) in enumerate(items) if n is not None and expected(n) != i + 1]
    if bad:
        print(f"NUMBERING MISMATCH ({len(bad)}): first few:", bad[:5])
        sys.exit(1)
    (LATIN_CLEAN / f"{nn}.txt").write_text("\n".join(t for t, _ in items) + "\n", encoding="utf-8")
    print(f"clean: {len(items)} verses, numbering OK")
