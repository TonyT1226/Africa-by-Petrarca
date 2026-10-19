"""Single place for every path the tools read or write.

source/  hand-maintained master files (edit these)
data/    generated from source/ by the tools (never edit by hand)
build/   local build output such as the PDF (not committed)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "source"
LATIN_RAW = SOURCE / "latin" / "raw"            # verbatim capture of the digital text, with its line numbers
LATIN_CLEAN = SOURCE / "latin" / "clean"        # one verse per line: line k = verse k
LATIN_FIXES = SOURCE / "latin" / "fixes.json"   # structural fixes applied raw -> clean
TRANSLATION = SOURCE / "translation"            # NN.txt: Chinese translation, sections, notes, names, corrections
FRONT = SOURCE / "front"                        # front matter of the PDF (HTML fragments)
SCAN_OVERRIDES = SOURCE / "scansion" / "overrides"  # NN.tsv: reviewed scansions that replace the automatic ones
RECITATION_TAGS = SOURCE / "recitation" / "tags"    # NN.tsv: ElevenLabs delivery tags per line

DATA = ROOT / "data"
SCANSION = DATA / "scansion"                    # NN.tsv: scansion + recitation text per verse (generated)
RECITATION = DATA / "recitation"                # ElevenLabs-ready text per book (generated)
TEI = DATA / "tei"
TEXT = ROOT / "text"                            # human-readable parallel text in Markdown (generated)

BUILD = ROOT / "build"

BOOKS = [f"{i:02d}" for i in range(1, 10)]
