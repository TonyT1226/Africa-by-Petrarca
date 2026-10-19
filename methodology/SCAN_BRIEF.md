# Brief: hexameter check + delivery tags for the ElevenLabs recitation text

You are working on Petrarch's *Africa* (Latin dactylic hexameter, medieval orthography). An automatic scanner has
scanned every verse and produced a recitation text for the ElevenLabs text-to-speech engine (an Italian voice will
read the Latin). Your book is given in the task. Work only on files for your book.

## Files (paths relative to the repository root)
- `data/scansion/NN.tsv` — one row per verse, TAB-separated: `line`, `status`, `pattern`, `notes`, `feet`, `tts`.
  - `status`: `ok` (unique scansion), `amb` (several scansions fit; the best by penalty was chosen; notes = top
    candidates), `var` (needed a special assumption: synizesis, hiatus, consonantal/vocalic i/u, "relax" = a vowel
    before a vowel treated as long; notes say which word), `irr` (no hexameter found; text left plain),
    `frag` (half-line or lacuna).
  - `pattern`: feet 1–6, D = dactyl, S = spondee, X = final foot; half-lines end in `h` (one long) / `t`.
  - `feet`: the recitation text with `|` between feet (proof-reading view). `tts`: the same without `|`.
- `source/latin/clean/NN.txt` — the original Latin, line k = verse k (a few misprints are corrected in the pipeline).
- `source/translation/NN.txt` — the Chinese translation with section structure: lines `@START-END title` start sections,
  verse lines are `N | 中文`, notes start with `>>`. Use it to understand content and mood.

## Conventions of the recitation text (keep them exactly)
1. Ictus: the first syllable of every foot carries an acute accent on its vowel (á é í ó ú). Exactly one accent per
   foot, six per complete verse, nothing else accented. For a diphthong, accent its first letter (áu, éu); `ae/oe`
   are already written `e` (é).
2. Elision: the elided vowel (or vowel + m) is dropped and replaced by an apostrophe, and the word is joined to the
   next one (`Fort'etiam`, `Victor'atque`); if punctuation stands between them it is kept (`Tuqu', ó`).
   Prodelision of est/es: `vána'st`, `palám'st`. Hiatus (no elision) is allowed where the metre needs it.
3. Spelling for an Italian voice: consonantal u is written `v` (`virum`, `silvis`, `adversos`), vocalic V at a word
   start is `U` (`Ut`, `Una`); `y`→`i`, `ph`→`f`, `th`→`t`, `ae/oe`→`e`; `qu`, `gu`, consonantal `i` unchanged.
   Medieval spellings (michi, nichil, que = quae, celum, Penus) stay.
4. Main caesura: ` — ` (spaced em dash) is inserted at the main caesura when no punctuation already stands there.
   Order of preference: penthemimeral, then (with punctuation) any legitimate caesura, trochaic in the 3rd foot,
   hephthemimeral. At most one inserted dash per verse.
5. The `|` marks: placed before the onset consonant of the foot's first syllable (`cónspicu|úm`, `|vúlnera`).
   Inside an elided junction place it where it falls (`Práta quid'|ét`). Only for proof-reading; they are removed
   for the final text.

## Task A — check the scansion
Go through the whole book. Give special attention to `var`, `amb`, `irr`, `frag` rows, but skim every row: wrong
u/v decisions (e.g. `carvisse` must be `caruisse`; `volvit` vs `voluit`), wrong monosyllables, wrong elisions, a
caesura dash in an absurd place, or an impossible quantity (a naturally short vowel under ictus without position or
another licence) are errors.
Petrarch's prosody is mostly classical, with medieval licences: Greek names often scanned freely, `e` for `ae`
keeps the long quantity, occasional hiatus, lengthening at the caesura, synizesis (omnia, aurea, praemio,
Hispania), `cui`/`huic`/`dein(de)` monosyllabic. When several scansions are possible, choose the one with a dactyl
in the 5th foot and natural quantities.

For every verse you would change, write ONE line in `source/scansion/overrides/NN.tsv`:
`N<TAB>corrected feet text` — the full verse in the `feet` format (with `|`, accents, apostrophes, dash), built from
the current `feet` text. Do not list verses that are already right.
- Half-lines (`frag`): mark the feet that exist (ictus accent on the first syllable of each, `|` between).
- Verses that cannot be scanned at all (lacuna, corrupt): write `N<TAB>NOSCAN ` followed by the plain text with
  `v` spelling and NO accents (or leave the row alone if the plain text in `tts` is already fine).
- Verses with an extra word beyond the sixth foot (e.g. VI.395 `… ruinam Fatorum.`): scan the hexameter and let the
  extra word ride, unaccented, inside the sixth segment: `…ru|ínam Fatorum.` (still exactly 6 segments, one accent
  each).
Run `python3 tools/check_manual.py NN` and fix every problem it reports for the manual file.

## Task B — delivery tags
ElevenLabs Eleven v3 understands short "audio tags" in square brackets that steer delivery. One voice reads the whole
book; the recitation is solemn epic narration. Write `source/recitation/tags/NN.tsv` with lines `N<TAB>tag` (tag WITHOUT brackets):
- a tag at the FIRST line of EVERY section (sections from `@START-END` in source/translation/NN.txt) giving the delivery of
  that passage;
- optionally further tags inside a section at the first line of a speech or a strong change of mood (the tag is
  placed before that verse); on average no more than one inner tag per ~15 verses; never two tags on one verse.
Tag wording: English, lowercase, 1–4 words, about emotion/delivery for a single narrator, e.g.
`solemn`, `reverent`, `calm narration`, `grave`, `hushed`, `awed`, `tender`, `wistful`, `sorrowful`, `grieving`,
`bitter`, `indignant`, `angry`, `fierce`, `urgent`, `tense`, `menacing`, `defiant`, `proud`, `triumphant`,
`pleading`, `desperate`, `weary`, `ironic`, `exultant`, `stately`, `vigorous`, `majestic`, `foreboding`.
Combine two with a comma when useful (`grave, foreboding`). No character names, no sound effects, no voice/accent
changes (no "old man voice"), no stage directions longer than four words.
Run `python3 tools/check_manual.py NN` again until it prints `NN OK`.

## Report
Write `reviews/scansion/NN.md`: how many verses you corrected and why (grouped), anything uncertain, and the tag
choices in brief. Your final message: 3–6 lines summarising the same. Do not edit any other files and do not run `tools/recite.py` (it rewrites the scan files other agents read).
