# How this edition was made

This folder keeps the working briefs exactly as the AI agents used them (paths updated to this repository). They
are reusable: the same pipeline can produce a translation into another language, or re-review a book.

| File | Role |
|---|---|
| `STYLE.md` | Chinese style guide: verse form, register, notes, file format (Chinese) |
| `GLOSSARY.md` | canonical Chinese renderings of proper names |
| `TRANSLATOR_BRIEF.md` | brief given to each translator agent |
| `REVIEWER_BRIEF.md` | brief given to each independent reviewer agent |
| `SCAN_BRIEF.md` | brief for checking the scansion and writing delivery tags |

## Pipeline

1. **Latin text.** The nine books were captured verbatim from the Itinera Electronica digital text
   (`source/latin/raw/`) and checked against the web pages by checksum. `tools/clean_latin.py` turns them into one
   verse per line (`source/latin/clean/`), applying two structural fixes (`source/latin/fixes.json`): the two
   half-lines of III.87 joined with " … ", and the digital text's numbering slip in Book VII (+1 from line 81).
2. **Translation.** Each book (long books in parts) was translated directly from the Latin by a separate agent
   following `TRANSLATOR_BRIEF.md` and `STYLE.md`, then validated (`tools/validate.py`).
3. **Independent review.** A different agent, which had not seen the translation being made, checked every line
   against the Latin (`REVIEWER_BRIEF.md`) and corrected it; logs in `reviews/translation/`.
4. **Harmonization.** Proper names were unified across books (`tools/names.py`, `tools/harmonize.py`), dates
   normalised, misprints of the digital text collected as `#CORRECTIONS`.
5. **Scansion.** `tools/scan.py` scans every verse as dactylic hexameter (syllabification, position, vowel before
   vowel, elision, synizesis and hiatus as fallbacks; medieval spellings handled), `tools/render.py` writes the
   recitation text. A separate agent per book then checked every verse (`SCAN_BRIEF.md`): 515 verses were corrected
   by hand (`source/scansion/overrides/`) and the systematic errors they found were fixed in the scanner. Logs in
   `reviews/scansion/`.
6. **Delivery tags.** The same agents wrote English delivery tags for every section and for speeches and changes
   of mood (`source/recitation/tags/`).
7. **Typesetting.** `tools/build.py` produces the PDF with WeasyPrint (TeX Gyre Pagella + Noto Serif CJK SC).

All agents were Claude models (Anthropic). No step has yet been checked by a human Latinist; see
`KNOWN_ISSUES.md`.
