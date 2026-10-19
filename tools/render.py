"""Render a scanned hexameter line for ElevenLabs (and a foot-divided display for checking).

render_line(line) -> dict(tts=..., feet=..., pattern=..., status=...)
  tts : ictus vowels with acute accent, elided vowels dropped with apostrophe (words joined),
        consonantal u -> v, diphthongs ae/oe -> e, y -> i, ph -> f, th -> t, caesura " — "
  feet: same text with "|" between feet (for proof-reading only)
"""
import re
import unicodedata

from scan import scan_line, norm_word, tokenize, base_units

CAESURA = " — "


def _case(src: str, out: str) -> str:
    return out.upper() if src.isupper() and len(src) == 1 else (out[0].upper() + out[1:] if src[:1].isupper() else out)


def word_repl(word, units, ictus_idx, elide_from=None, drop_first_vowel=False):
    """Return (list of output strings per original char index, onset positions dict nucleus_i -> char index)."""
    lw = norm_word(word)
    from scan import strip_accents
    rep = [strip_accents(c) for c in word]
    # orthographic simplification for an Italian voice
    for i, ch in enumerate(lw):
        if ch == "y":
            rep[i] = _case(word[i], "i")
    for m in re.finditer(r"ph|th|rh", lw):
        i = m.start()
        rep[i] = _case(word[i], {"p": "f", "t": "t", "r": "r"}[lw[i]])
        rep[i + 1] = ""
    for m in re.finditer(r"ch(?![ei])", lw):
        if not lw.startswith(("mich", "nich")):
            rep[m.start() + 1] = ""
    for u in units:
        if u["t"] == "C" and u.get("cons_u") and not u.get("glide"):
            rep[u["i"]] = _case(word[u["i"]], "v")
        elif u["t"] == "V" and lw[u["i"]] == "u" and word[u["i"]] in "Vv":
            rep[u["i"]] = _case(word[u["i"]], "u")
        if u["t"] == "V" and u.get("diph") and lw[u["i"]:u["i"] + 2] in ("ae", "oe"):
            rep[u["i"]] = _case(word[u["i"]], "e")
            rep[u["i"] + 1] = ""
    # v written as u inside consonant contexts that the scanner treated as vowel-less (e.g. initial "u" + vowel)
    for i in ictus_idx:
        if 0 <= i < len(rep) and rep[i]:
            rep[i] = unicodedata.normalize("NFC", rep[i] + "́")
    if elide_from is not None:
        for i in range(elide_from, len(rep)):
            rep[i] = ""
    if drop_first_vowel:
        for u in units:
            if u["t"] == "V":
                for i in range(u["i"], u["i"] + u["n"]):
                    rep[i] = ""
                break
    return rep


def render_line(line: str):
    r = scan_line(line)
    toks = r["tokens"]
    if not toks:
        return {"tts": line, "feet": line, "pattern": None, "status": "empty", "notes": []}
    words = r.get("words")
    sylls = r.get("syllables", [])
    elided = r.get("elided", {}) if r["ok"] else {}
    ictus = {}
    if r["ok"]:
        for s in sylls:
            if s.get("ictus"):
                ictus.setdefault(s["word"], []).append(s["unit"]["i"])
    # foot starts (syllable index -> foot number) for display
    foot_start_units = {}
    if r["ok"]:
        idx = 0
        for fi, f in enumerate(r["pattern"]):
            s = sylls[idx]
            foot_start_units[(s["word"], s["unit"]["i"])] = fi
            idx += {"D": 3, "S": 2, "X": 2, "h": 1, "t": 2}[f]
    out_tts, out_feet = [], []
    pos = 0
    caes = r.get("caesura") if r["ok"] else None
    for k, (w, a, b) in enumerate(toks):
        gap = line[pos:a]
        units = words[k][1] if words else base_units(norm_word(w))
        prev_join = k > 0 and (k - 1) in elided
        if prev_join and not gap.strip():
            gap = ""
        if k > 0 and (k - 1) == caes and not gap.strip(" "):
            gap = CAESURA
        elide_from = None
        if elided.get(k) == "final":
            vs = [u for u in units if u["t"] == "V"]
            elide_from = vs[-1]["i"]
        rep = word_repl(w, units, ictus.get(k, []), elide_from, drop_first_vowel=(k > 0 and elided.get(k - 1) == "est"))
        wt = "".join(rep)
        # feet display: insert "|" before the onset of a foot-initial syllable
        rep_f = list(rep)
        for u in units:
            if u["t"] == "V" and (k, u["i"]) in foot_start_units and foot_start_units[(k, u["i"])] > 0:
                on = onset(units, u)
                rep_f[on] = "|" + rep_f[on]
        wf = "".join(rep_f)
        if elided.get(k):
            wt += "'"
            wf += "'"
        out_tts.append(gap + wt)
        out_feet.append(gap + wf)
        pos = b
    tail = line[pos:]
    tts = "".join(out_tts) + tail
    feet = "".join(out_feet) + tail
    # "|" placed before a word start should sit before the space: normalise " |" spacing
    feet = re.sub(r"(\S)\|", r"\1|", feet)
    status = "ok" if r["ok"] else "irregular"
    return {"tts": tts, "feet": feet, "pattern": r["pattern"], "status": status, "notes": r["notes"],
            "ambiguous": r.get("ambiguous", False), "candidates": r.get("candidates", [])}


def onset(units, v):
    """Char index where the syllable whose nucleus is v begins (within the word)."""
    j = units.index(v)
    cons = []
    t = j - 1
    while t >= 0 and units[t]["t"] == "C":
        cons.append(units[t])
        t -= 1
    if not cons:
        return 0 if j == 0 else v["i"]
    if t < 0:
        return cons[-1]["i"]  # word-initial consonants
    cons = cons[::-1]
    if len(cons) >= 2 and cons[-2]["ch"] in "pbtdcgf" and cons[-1]["ch"] in "lr":
        return cons[-2]["i"]
    return cons[-1]["i"]


if __name__ == "__main__":
    import sys
    for l in sys.stdin:
        l = l.rstrip("\n")
        d = render_line(l)
        print(d["pattern"], "|", d["feet"])
        print("      ", d["tts"])
