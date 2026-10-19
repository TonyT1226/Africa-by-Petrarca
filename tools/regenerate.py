"""Regenerate every derived file from source/.

Usage: python3 tools/regenerate.py
  recite.py      -> data/scansion/NN.tsv      (automatic scansion + reviewed overrides, recitation text)
  elevenlabs.py  -> data/recitation/*.txt     (ElevenLabs-ready text, one block per section)
  export.py      -> data/*.json(l), data/*.tsv, data/tei/, text/
The PDF is built separately: python3 tools/build.py  (needs WeasyPrint and fonts, see README).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import recite  # noqa: E402
import elevenlabs  # noqa: E402
import export  # noqa: E402
from paths import BOOKS  # noqa: E402

if __name__ == "__main__":
    for nn in BOOKS:
        recite.run(nn)
    elevenlabs.export()
    export.main()
    print("regenerated data/ and text/")
