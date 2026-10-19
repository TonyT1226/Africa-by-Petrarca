# AGENTS.md — working on this repository

Petrarch's *Africa* (Latin epic, 9 books, 6,730 hexameters) with a Chinese verse translation made directly from the
Latin, notes, a full metrical scansion and an ElevenLabs recitation script. Everything is addressed by line, so
people and agents can cite, check, extend and reuse any verse.

Read this file before changing anything. Chinese conventions for translation and notes are in
`methodology/STYLE.md`; proper names in `methodology/GLOSSARY.md`.

## Ground rules

1. **Edit `source/`, never the generated files.** `data/` and `text/` are produced by the tools from `source/`.
   After any change in `source/`, run `python3 tools/regenerate.py`, then `python3 tools/check_all.py` (must
   exit 0). Commit source and regenerated files together.
2. **Never change line alignment.** Line *k* of `source/latin/clean/NN.txt` is verse *k* of book NN, and every
   other file keys on that number. Do not add, remove, split or merge Latin lines.
3. **Do not edit the Latin text directly.** A mechanical misprint of the digital text is fixed by adding a
   `#CORRECTIONS` entry in the translation file (`line | wrong | right`; `wrong` must occur verbatim in the line).
   Variant readings and conjectures are *not* corrections: discuss them in `#TEXTNOTES` or a note.
   Medieval spellings (*michi, nichil, que* = quae, *celum, Penus*) are not errors.
4. **Be honest about provenance.** The translation, notes and scansion were produced and reviewed by AI agents
   (Claude, Anthropic). No human Latinist has reviewed them yet. Never describe AI review as human review; when you
   are unsure, say so in a note or in `KNOWN_ISSUES.md` instead of guessing.
5. **Do not invent sources.** Cite Livy, Vergil etc. by book/chapter only when certain. Do not copy text from
   modern translations or commentaries.

## Layout

```
source/                         hand-maintained masters (edit these)
  latin/raw/NN.txt              verbatim capture of the Itinera Electronica digital text (do not edit)
  latin/clean/NN.txt            one verse per line, line k = verse k (made from raw/ by tools/clean_latin.py)
  latin/fixes.json              structural fixes raw -> clean (III.87 merge, VII numbering offset)
  translation/NN.txt            Chinese translation, sections, notes, text notes, corrections, names
  scansion/overrides/NN.tsv     reviewed scansions that replace the automatic ones
  recitation/tags/NN.tsv        ElevenLabs delivery tags (English) per line
  front/*.html                  front matter and appendix guide of the PDF
data/                           GENERATED — line-addressed data (see data/README.md)
text/                           GENERATED — parallel Latin–Chinese Markdown, one file per book
tools/                          Python 3.10+ tools, standard library only (the PDF also needs WeasyPrint)
tts/                            stand-alone ElevenLabs voicing script
methodology/                    the briefs and style guides the agents worked from
reviews/                        per-book review logs (translation, scansion)
dist/                           the typeset PDF (rebuilt only for releases)
```

## Identifiers

- Verse: `africa.B.N` (book 1–9, line number), e.g. `africa.9.123`.
- Section: `africa.B.sKK` (1-based index within the book), e.g. `africa.9.s05`.
- Note: `africa.B.nKKK` (commentary, in reading order) and `africa.B.tKKK` (textual notes).
Verse IDs are permanent. Section and note IDs follow the current order: if you insert a section or note, later
IDs in that book shift, so cite verses when you need stable references.

## File formats

**Translation `source/translation/NN.txt`** (UTF-8; parsed by `tools/validate.py`):

```
#BOOK 9
#TITLE 第九卷
#SUMMARY
book summary (Chinese)
#ENDSUMMARY

@1-9 section title            section header: first-last verse, then title
1 Chinese line 1             one line per verse: number, one space, text (≤ 40 characters)
2 ...
>>1-9 | Latin lemma | note    notes follow the verses of their section; no "|" inside the note text

#TEXTNOTES
109 | cele{b}rabat | textual remark
#CORRECTIONS
534 | mu1ta | multa          applied to the printed Latin
#NAMES
Scipio = 西庇阿               every proper name used in the book
#END
```

**Scansion overrides `source/scansion/overrides/NN.tsv`**: `N<TAB>feet text`. The feet text is the recitation
text of the verse with `|` between the six feet: acute accent on the first vowel of every foot (the ictus),
elided vowels dropped with an apostrophe (`Fort'etiám`), consonantal u written `v`, `ae/oe` written `e`, `y→i`,
`ph→f`, `th→t`, ` — ` at the main caesura when no punctuation stands there. `NOSCAN plain text` for verses that
cannot be scanned. Full conventions: `methodology/SCAN_BRIEF.md`.

**Delivery tags `source/recitation/tags/NN.tsv`**: `N<TAB>tag` (English, lowercase, 1–4 words, no brackets).
Every section's first verse must have one.

**Generated scansion `data/scansion/NN.tsv`**: `line, status, pattern, notes, feet, recitation`; status is
`ok` (unique automatic scansion), `amb` (best of several), `var` (needed synizesis/hiatus etc.), `man`
(reviewed override), `frag` (half-line or lacuna), `irr` (not scannable).

## Commands

```bash
python3 tools/check_all.py              # all checks; exit 1 on any problem (CI runs this)
python3 tools/regenerate.py             # rebuild data/ and text/ from source/
python3 tools/validate.py 09            # check one translation file
python3 tools/check_manual.py 09        # check one book's scansion overrides and tags
python3 tools/build.py                  # typeset the PDF to build/africa.pdf (WeasyPrint + fonts)
python3 tools/names.py                  # list proper names rendered differently across books
python3 tools/harmonize.py 01 02 ...    # apply the canonical renderings in tools/harmonize.py
echo "Arma virumque cano" | python3 tools/render.py   # scan any hexameter
```

## Recipes

- **Fix a translation line or note**: edit `source/translation/NN.txt`, keep the line number and the 40-character
  limit; regenerate; check.
- **Fix a misprint in the Latin**: add a `#CORRECTIONS` entry (and a `#TEXTNOTES` entry explaining it).
- **Fix a scansion**: add or replace the verse in `source/scansion/overrides/NN.tsv`; run
  `python3 tools/check_manual.py NN`. If the error comes from a general rule, fix `tools/scan.py` instead and check
  with `git diff data/scansion` that every changed verse is better.
- **Rename a proper name everywhere**: add the mapping to `CANON` in `tools/harmonize.py`, run it on all books,
  update `methodology/GLOSSARY.md`.
- **Voice the poem**: `tts/` (see `tts/README.md`). Recitation text per book is in `data/recitation/`.
- **Add another language**: not wired into the tools yet. Proposed layout: `source/translation-<lang>/NN.txt` in
  the same format, translated from the Latin (use the Chinese only as a crib), with its own `STYLE` file. Open an
  issue first.
- **Creative reuse** (adaptations, games, comics, audio drama, teaching material): read from `data/` (stable IDs);
  keep attribution (CC BY 4.0) and say that the translation is AI-made.

## Before you finish

- `python3 tools/check_all.py` exits 0.
- Commit message / PR description lists the affected verse IDs and why.
- New doubts go into `KNOWN_ISSUES.md` or a note, not silently into the text.
