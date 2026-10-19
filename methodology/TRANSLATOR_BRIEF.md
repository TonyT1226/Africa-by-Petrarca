# Translator brief (read with STYLE.md and GLOSSARY.md)

You are translating part of Petrarch's Latin epic *Africa* directly from Latin into Chinese, as annotated line-by-line verse, for a Latin–Chinese parallel edition. Work in the repository root.

## Read first, completely
1. `STYLE.md` — conventions and the exact file format. Follow it strictly.
2. `GLOSSARY.md` — mandatory Chinese renderings of proper names.
3. `source/latin/clean/NN.txt` — the Latin text. Line k of the file is verse k. Never modify it.

## About the Latin text
The digital text (Itinera Electronica, UCLouvain) comes from different printed editions in different books. Books I–II use classicized spelling; from Book III on the text uses Festa's medieval orthography (*michi* = mihi, *que* = quae/-que, *celo* = caelo, *nichil*, *Ytalia*, *Hyspania*, *Lelius*, *Penus* = Poenus, *thogati*, *sompnus* …). That spelling is not an error — do not "correct" it.
From Book III on, the digital text also contains many **scanning errors**, e.g. *file* for *ille*, *ilium* for *illum*, *boras* for *horas*, *banc* for *hanc*, *lure* for *iure*, *louis* for *Iouis*, *Tura* for *Iura*, *aime* for *alme*, *tune* for *tunc*, *0* for *O*, *Tonga* for *longa*, *Bibi* for *sibi*, words split by a stray space (*iuu enilibus*, *no bis*), braces like *cele{b}rabat*. Translate the intended word and list each such error under `#CORRECTIONS` (line | exact wrong string | right string) so the printed Latin can be fixed. Only list clear mechanical errors; doubtful readings go in `#TEXTNOTES` only.
Petrarch left the poem unfinished: some lines are genuinely incomplete (half-lines, gaps marked `< >` or `- - -` or `…`). Translate what is there, keep the gap visible in the Chinese (use ……), and add a short note. Do not invent the missing words.

## Method
- Read your whole assigned range first and plan the sections.
- Before translating each sentence, construe the Latin carefully (subject, verb, agreement, what each relative clause/participle attaches to). Petrarch's syntax is dense and enjambed; accuracy comes first, then dignity of style.
- Exact line correspondence: every Latin line gets exactly one Chinese line with the same number. Rearranging inside a sentence across neighbouring lines is fine; moving sense far away is not.
- Notes: about one per 8–15 lines (more where allusions are dense), in Chinese, in your own words. No invented citations — only give book.chapter references you are sure of. Silius Italicus' *Punica* was unknown to Petrarch.
- Draft in several pieces (e.g. `source/translation/work/NN_partK.txt`, each a run of whole sections) to avoid one enormous write, then concatenate with a shell command into your output file.
- Run the validator (command given in your assignment) and fix everything until it prints OK.
- Then reread your Chinese against the Latin once, section by section, for omissions, mistranslations, drift out of line correspondence, and glossary consistency; fix and validate again.

## Part assignments
If you are assigned only part of a book, your output file is a *part file*: it contains only your sections (they must start exactly at your first line and end exactly at your last line), followed by `#TEXTNOTES`, `#CORRECTIONS`, `#NAMES`, `#END`. No `#BOOK`, `#TITLE` or `#SUMMARY`. Instead, put a 100–200 character summary of your part as the first lines of the file, like this:
```
#PARTSUMMARY
……
#ENDPARTSUMMARY
```
(The validator ignores it; the editor uses it to write the book summary.) Validate with `python3 tools/validate.py NN source/translation/parts/FILE START-END`.

Do not edit STYLE.md, GLOSSARY.md, the Latin files, or any other translator's files.

## Final reply
Reply with a short report (under 150 words): the validator's OK line, and a list of passages (by line number) where the Latin was doubtful or your rendering is uncertain.
