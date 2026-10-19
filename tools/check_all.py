"""Run every consistency check. Exit status 1 if anything is wrong.

Usage: python3 tools/check_all.py
  1. each source/translation/NN.txt parses and matches the Latin line count (validate.py)
  2. scansion overrides and delivery tags are well-formed (check_manual.py)
  3. derived files in data/ and text/ are up to date with source/ (regenerated in a temp copy)
"""
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from paths import BOOKS  # noqa: E402
from validate import validate  # noqa: E402
from check_manual import check  # noqa: E402

GENERATED = ["data", "text"]


def main():
    failed = False
    for nn in BOOKS:
        probs = validate(nn)
        if probs:
            failed = True
            print(f"translation {nn}: {len(probs)} problem(s)")
            for p in probs[:20]:
                print("   ", p)
    print("translations:", "FAIL" if failed else "OK")
    bad = False
    for nn in BOOKS:
        probs = check(nn)
        if probs:
            bad = True
            print(f"scansion/tags {nn}: {len(probs)} problem(s)")
            for p in probs[:20]:
                print("   ", p)
    print("scansion overrides and tags:", "FAIL" if bad else "OK")
    failed |= bad
    # regenerate in a temporary copy and compare
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "build", "dist", "__pycache__"))
        r = subprocess.run([sys.executable, str(copy / "tools" / "regenerate.py")], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout, r.stderr)
            print("regeneration: FAIL")
            sys.exit(1)
        stale = []
        for g in GENERATED:
            stale += diff_tree(ROOT / g, copy / g, g)
        if stale:
            failed = True
            print("generated files out of date (run: python3 tools/regenerate.py):")
            for s in stale[:30]:
                print("   ", s)
        print("generated files:", "FAIL" if stale else "OK")
    sys.exit(1 if failed else 0)


def diff_tree(a: Path, b: Path, label: str):
    out = []
    names = {p.relative_to(a) for p in a.rglob("*") if p.is_file()} if a.exists() else set()
    names_b = {p.relative_to(b) for p in b.rglob("*") if p.is_file()} if b.exists() else set()
    for n in sorted(names | names_b):
        pa, pb = a / n, b / n
        if not pa.exists():
            out.append(f"{label}/{n} missing")
        elif not pb.exists():
            out.append(f"{label}/{n} is not produced by the tools any more")
        elif not filecmp.cmp(pa, pb, shallow=False):
            out.append(f"{label}/{n} differs")
    return out


if __name__ == "__main__":
    main()
