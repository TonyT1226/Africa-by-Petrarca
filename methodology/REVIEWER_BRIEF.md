# Reviewer brief

You are the independent reviewer of one book of a Chinese verse translation of Petrarch's Latin epic *Africa*. Someone else translated it; your job is to check it against the Latin, line by line, and fix what is wrong. Work in the repository root.

## Read first, completely
1. `STYLE.md` and `GLOSSARY.md` — the conventions the translation must follow.
2. `TRANSLATOR_BRIEF.md` — what the translator was told (spelling of the Latin, scanning errors, unfinished lines).
3. `source/latin/clean/NN.txt` (line k = verse k) and `source/translation/NN.txt` (the translation, in the format of STYLE.md §5).

## What to check, section by section
For every section, read the Latin lines and the Chinese lines side by side.
1. **Accuracy.** Re-construe each Latin sentence yourself (subject, verb, case, agreement, tense/mood, negation, what each relative clause or participle refers to, who is speaking). Fix mistranslations, wrong referents, inverted meanings, missed negations or conditionals, wrong tense where it matters, misread words (watch for medieval spellings: *que* = quae, *michi* = mihi, *celum* = caelum, *nephas*, *Penus* = Poenus, *menia* = moenia, *cunta* = cuncta …).
2. **Completeness.** No omitted phrases, no padding or invented content. Similes, epithets, apostrophes and rhetorical questions must survive.
3. **Line correspondence.** Each Chinese line should carry its own Latin line's content as closely as Chinese syntax allows. Fix drift.
4. **Speech marks.** Quotation marks open and close where speeches actually begin and end (the Latin source's own quote marks are sometimes wrong).
5. **Names.** Follow GLOSSARY.md; one rendering per person/place throughout the book.
6. **Notes.** Factual errors, wrong identifications, citations you cannot confirm (delete precise book.chapter references you are not sure of rather than keep a possibly false one), notes that merely paraphrase the line. Add a note where a reader clearly needs one and none exists (an unexplained name or allusion).
7. **Corrections list.** Each `#CORRECTIONS` entry must be a genuine mechanical scanning/typing error, with the wrong string present in that Latin line and the right string being the evident intended word. Remove entries that "correct" medieval orthography or make editorial choices; move doubtful ones to `#TEXTNOTES`. Add obvious scanning errors the translator missed.
8. **Summary.** Make `#SUMMARY` a single coherent book summary of 200–350 Chinese characters (it may currently be several part summaries joined together).
9. **Style.** Fix clumsy, unidiomatic or wrongly registered Chinese (no 文言, no 网络语, no "您"), but do not rewrite merely for taste.
10. **Books translated in parts.** If the book was translated by several people and joined, harmonize across the joins: one rendering per name, consistent register and quotation conventions, and remove duplicated "first-mention" notes (keep the first; keep a later one only if it adds something specific).
11. **Orthography.** The *cunt-* spelling (cunta, cuntos …) is the source's consistent orthography for *cunct-*; it is not a scanning error. Likewise *michi, nichil, que, celum, Penus, menia, Ytalia, Hyspania*, etc.

## Decisions already made (apply them)
- Tuneta = 突尼斯 (note at first mention: ancient Tunes, modern Tunis). Cn. Octavius = 屋大维乌斯 (distinct from Octavian = 屋大维).
- Bomilcar in VI.512 stays 波米尔卡, with the note that Livy (22.51) gives Maharbal.

## How to work
- Edit `source/translation/NN.txt` in place (use the Edit tool for targeted fixes; keep the format exactly).
- Keep a log at `review/NN.md`: for each substantive change, one line `行号：原译 → 新译（理由）`; for note changes, `注 行号：……`. Small punctuation fixes can be summarized in one line. At the end, list any passages you still consider doubtful.
- Run `python3 tools/validate.py NN` at the end; it must print OK.
- Do not edit the Latin files, STYLE.md, GLOSSARY.md, tools, or other books' files.

## Final reply
Under 150 words: the validator's OK line, the number of lines you changed, the number of notes added/removed/changed, and the most important problems you found (by line number).
