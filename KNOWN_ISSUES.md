# Known issues · 已知问题

Things that are uncertain, unresolved or not yet done. Each book's full list of doubts is in its review logs:
`reviews/translation/NN.md` (section 仍存疑处) and `reviews/scansion/NN.md` (section *Uncertain*).

## Review status
- **No human review yet.** Translation, notes and scansion were made and cross-checked by AI agents only.
- **Rights in the digital Latin text.** The terms of use of the *Itinera Electronica* digital text could not be
  checked automatically (the site blocks automated access). The poem and the printed editions behind it are old
  (1872, 1926), but the maintainers should confirm the site's terms.

## Text
- **III.78** — lacuna `< >` in the digital text; the line is syntactically incomplete.
- **III.87** — two half-lines of the digital text joined into one verse with " … " (structural fix).
- **III.109** — `cele{b}rabat`: braces read as a deletion (`celerabat`, "sped"); reading `celebrabat` is possible.
- **III.226** — one syllable short; probably a word is missing.
- **III.779** — `finit` does not scan; `init` would scan perfectly. Text left as transmitted.
- **IV.299** — `<aiment>` in the digital text; the word is unknown.
- **VI.395, VI.739** — an extra word (`Fatorum.`, `Exploratores.`) after a complete hexameter.
- **VII.288** — `firment` does not scan; `firmet` would. Text left as transmitted.
- **VII** — the digital text's numbering skips one line near 80; this edition's numbers are +1 from VII.81.
- Many local doubts of interpretation are listed per book in `reviews/translation/`.

## Scansion
- 23 verses could only be scanned with a licence (synizesis, hiatus, a Greek name scanned freely), and 2 not at
  all (III.779, VII.288). They are marked `var` or `irr` in `data/scansion/NN.tsv`.
- 19 reviewed verses have no pattern code in `data/lines.jsonl` (`pattern: null`). In 11 of them the reviewed foot
  division cannot be converted mechanically (Greek names read with hiatus, an extra word after the sixth foot). The
  other 8 are half-lines, lacunae or unscannable lines (I.357, I.361, III.78, III.226, IV.299, IV.388, V.124,
  VI.830).
- Petrarch's own quantities are sometimes irregular (e.g. *Ĭtalus*, *Carthāgŏ*). The reviewers kept his scansion
  rather than normalising it.

## Recitation
- The ElevenLabs script uses an Italian voice and stresses the ictus of each foot. This is one traditional way of
  reading Latin verse, not the only one. Delivery tags can occasionally be read aloud by the model.
