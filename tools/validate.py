"""Validate a translation file source/translation/NN.txt against source/latin/clean/NN.txt.

Usage: python3 validate.py NN
Prints OK or a list of problems.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import *  # noqa: E402,F401,F403

SEC_RE = re.compile(r"^@(\d+)-(\d+)\s+(\S.*)$")
LINE_RE = re.compile(r"^(\d+) (\S.*)$")
NOTE_RE = re.compile(r"^>>(\d+)(?:-(\d+))?\s*\|\s*([^|]*?)\s*\|\s*(\S.*)$")


def parse(nn: str, path: Path | None = None):
    """Return (meta, sections, textnotes, names, problems)."""
    path = path or (TRANSLATION / f"{nn}.txt")
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    meta = {"book": None, "title": None, "summary": []}
    sections = []
    textnotes = []
    names = []
    problems = []
    mode = "head"
    cur = None
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("#BOOK"):
            meta["book"] = line[5:].strip()
            continue
        if line.startswith("#TITLE"):
            meta["title"] = line[6:].strip()
            continue
        if line.startswith("#SUMMARY"):
            mode = "summary"
            continue
        if line.startswith("#ENDSUMMARY"):
            mode = "body"
            continue
        if line.startswith("#PARTSUMMARY"):
            mode = "partsummary"
            continue
        if line.startswith("#ENDPARTSUMMARY"):
            mode = "body"
            continue
        if mode == "partsummary":
            meta.setdefault("partsummary", []).append(line.strip())
            continue
        if line.startswith("#TEXTNOTES"):
            mode = "textnotes"
            continue
        if line.startswith("#NAMES"):
            mode = "names"
            continue
        if line.startswith("#CORRECTIONS"):
            mode = "corrections"
            continue
        if line.startswith("#END"):
            mode = "end"
            continue
        if mode == "summary":
            meta["summary"].append(line.strip())
            continue
        if mode == "textnotes":
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3 and parts[0].split("-")[0].isdigit():
                textnotes.append(parts[:2] + ["|".join(parts[2:])])
            else:
                problems.append(f"file line {i}: bad TEXTNOTES entry: {line[:60]}")
            continue
        if mode == "corrections":
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3 and parts[0].isdigit() and parts[1] and parts[2]:
                meta.setdefault("corrections", []).append((int(parts[0]), parts[1], parts[2]))
            else:
                problems.append(f"file line {i}: bad CORRECTIONS entry (need 'line | wrong | right'): {line[:60]}")
            continue
        if mode == "names":
            if "=" in line:
                a, b = line.split("=", 1)
                names.append((a.strip(), b.strip()))
            else:
                problems.append(f"file line {i}: bad NAMES entry: {line[:60]}")
            continue
        if mode == "end":
            continue
        # body
        m = SEC_RE.match(line)
        if m:
            cur = {"start": int(m.group(1)), "end": int(m.group(2)), "title": m.group(3).strip(),
                   "lines": [], "notes": []}
            sections.append(cur)
            continue
        m = NOTE_RE.match(line)
        if m:
            if cur is None:
                problems.append(f"file line {i}: note before any section")
                continue
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            cur["notes"].append({"start": a, "end": b, "lemma": m.group(3).strip(), "text": m.group(4).strip()})
            continue
        if line.startswith(">>"):
            problems.append(f"file line {i}: malformed note: {line[:60]}")
            continue
        m = LINE_RE.match(line)
        if m:
            if cur is None:
                problems.append(f"file line {i}: verse line before any section")
                continue
            cur["lines"].append((int(m.group(1)), m.group(2).strip()))
            continue
        problems.append(f"file line {i}: unrecognized: {line[:60]}")
    return meta, sections, textnotes, names, problems


def validate(nn: str, path: Path | None = None, rng: tuple[int, int] | None = None) -> list[str]:
    latin = (LATIN_CLEAN / f"{nn}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    n = len(latin)
    first, last = rng if rng else (1, n)
    meta, sections, textnotes, names, problems = parse(nn, path)
    if rng is None:
        if not meta["book"]:
            problems.append("missing #BOOK")
        if not meta["title"]:
            problems.append("missing #TITLE")
        if not meta["summary"]:
            problems.append("missing or empty #SUMMARY")
    if not names:
        problems.append("missing or empty #NAMES")
    for k, wrong, right in meta.get("corrections", []):
        if not (1 <= k <= n):
            problems.append(f"correction at line {k}: no such Latin line")
        elif wrong not in latin[k - 1]:
            problems.append(f"correction at line {k}: '{wrong}' not found in Latin line: {latin[k - 1]}")
    if not sections:
        problems.append("no sections")
        return problems
    expected = first
    for s in sections:
        if s["start"] != expected:
            problems.append(f"section @{s['start']}-{s['end']} should start at {expected}")
        if s["end"] < s["start"]:
            problems.append(f"section @{s['start']}-{s['end']} has end < start")
        nums = [k for k, _ in s["lines"]]
        want = list(range(s["start"], s["end"] + 1))
        if nums != want:
            missing = sorted(set(want) - set(nums))
            extra = sorted(set(nums) - set(want))
            dup = sorted({k for k in nums if nums.count(k) > 1})
            msg = f"section @{s['start']}-{s['end']}:"
            if missing:
                msg += f" missing {missing[:15]}"
            if extra:
                msg += f" outside-range {extra[:15]}"
            if dup:
                msg += f" duplicated {dup[:15]}"
            if not (missing or extra or dup):
                msg += " lines out of order"
            problems.append(msg)
        for note in s["notes"]:
            if not (s["start"] <= note["start"] <= note["end"] <= s["end"]):
                problems.append(f"note >>{note['start']}-{note['end']} outside section @{s['start']}-{s['end']}")
            if not note["text"]:
                problems.append(f"empty note at {note['start']}")
        for k, t in s["lines"]:
            if len(t) > 40:
                problems.append(f"line {k} is very long ({len(t)} chars) — split the sense more evenly")
        expected = s["end"] + 1
    if expected - 1 != last:
        problems.append(f"sections end at {expected - 1}, but should end at line {last}")
    return problems


if __name__ == "__main__":
    # python3 validate.py NN                      -> whole book, source/translation/NN.txt
    # python3 validate.py NN PATH START-END       -> a part file covering lines START..END
    nn = sys.argv[1]
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    rng = tuple(int(x) for x in sys.argv[3].split("-")) if len(sys.argv) > 3 else None
    probs = validate(nn, path, rng)
    if probs:
        print(f"{len(probs)} problem(s):")
        for p in probs:
            print(" -", p)
        sys.exit(1)
    meta, sections, textnotes, names, _ = parse(nn, path)
    nlines = sum(len(s["lines"]) for s in sections)
    nnotes = sum(len(s["notes"]) for s in sections)
    print(f"OK: book {meta['book']}, {len(sections)} sections, {nlines} lines, {nnotes} notes, "
          f"{len(textnotes)} text notes, {len(names)} names")
