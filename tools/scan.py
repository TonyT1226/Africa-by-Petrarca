"""Dactylic hexameter scanner for the Africa text (medieval orthography aware).

Pipeline per line: tokenize -> per-word phonological units (vowel nuclei V, consonants C)
-> elision -> syllable quantities (L long, S short, C common, ? unknown)
-> enumerate hexameter foot patterns consistent with the quantities -> pick the best.
When no pattern fits, word-level variants are tried (synizesis, consonantal/vocalic i/u,
diphthong split/merge), then relaxation of "vowel before vowel is short" (Greek names,
medieval e = ae), then hiatus instead of elision.

Library use: scan_line(text) -> dict (see bottom).
"""
import itertools
import re
import unicodedata

VOWELS = set("aeiouy")
MUTA = set("pbtdcgf")
LIQUIDA = set("lr")
NO_ELIDE = {"o", "heu", "ah", "io", "ohe", "en", "eheu", "hei"}
SHORT_FINAL_O = {"ego", "modo", "cito", "duo", "homo", "immo", "imo", "quomodo", "dummodo", "postmodo", "nescio"}
ANCEPS_FINAL_I = {"mihi", "michi", "tibi", "sibi", "ubi", "ibi", "nisi", "quasi", "alicubi"}
LONG_MONO = {"me", "te", "se", "de", "ne", "pro", "tu", "si", "qui", "quo", "qua", "mi", "ni", "e", "a", "o",
             "cui", "hi", "di", "dii", "que", "he", "re", "spe", "die", "tue", "sue", "ve", "hec"}
SHORT_MONO_FINAL = {"que", "ne", "ue", "ce"}  # as enclitics (only when attached)
SU_CONSONANT = ("suad", "suasi", "suaso", "suau", "sueu", "suesc", "suet", "suef", "consue", "mansue", "assue", "insue",
                "desue", "persuad", "persuas", "dissuad", "dissuas", "malesuad", "benesuad")
AER_WORDS = ("aer", "aeri", "aeria", "aerio", "aerius", "aerium", "aeriam", "aeriis", "aeriae", "aerii", "aereus",
             "aerea", "aereo", "aeream", "aereum", "aeris", "aera", "aerem", "aere")
HIATUS_AE_PREFIX = ("phaeth", "danae", "laert", "israel", "michael", "raphael", "gabriel", "ismael", "nathanael")
HIATUS_OE_PREFIX = ("poet", "poem", "poes", "coeg", "coem", "coeu", "coei", "coier", "coerc", "coepiss", "coemer")
UE_VOCALIC = {"precipue", "praecipue", "continue", "ardue", "tenue", "exue", "indue", "metue", "statue", "minue", "argue", "imbue", "acue", "perpetue", "strenue",
              "assidue", "annue", "ingenue", "sue", "tue", "due", "fatue", "mortue", "induere", "exuere"}
V_STEMS = ("pulu", "silu", "seru", "neru", "feru", "uolu", "solu", "fulu", "paru", "aru", "ceru", "toru", "curu", "salu",
           "laru", "mineru", "conseru", "obseru", "reseru", "deseru", "inseru", "euolu", "inuolu", "reuolu",
           "resolu", "absolu", "dissolu", "exsolu", "deferu", "efferu", "perferu", "aluo", "alue")
V_STEMS_IN = ("silu", "seru", "neru", "mineru", "uolu", "solu", "fulu")
U_PREFIXES = ("ad", "ob", "sub", "trans", "circum", "in", "con", "per", "dis", "ab", "quam", "quod", "quid", "quot")
I_PREFIXES = ("ad", "ab", "ob", "sub", "con", "in", "dis", "circum", "per", "trans")
NO_INIT_J = ("ion", "iol", "iason", "iapyg", "iapet", "iamb", "iesu", "ioann", "ieronim", "iero")
NO_INIT_J_WORDS = {"io", "iulus", "iuli", "iulo", "iulum", "ias", "ii"}
FI_FORMS = {"fio", "fis", "fit", "fiam", "fias", "fiat", "fiamus", "fiatis", "fiant", "fiunt", "fiet", "fient", "fies",
            "fiebat", "fiebant", "fiebam", "fiens", "fientes"}
SPECIAL_SYLLABLES = {
    # word -> list of (nucleus_char_index, nucleus_len); letters outside nuclei become consonants (h dropped)
    "cui": [(1, 2)], "huic": [(1, 2)], "dein": [(1, 2)], "deinde": [(1, 2), (5, 1)], "deinceps": [(1, 2), (6, 1)],
    "proin": [(2, 2)], "proinde": [(2, 2), (6, 1)], "cuique": [(1, 2), (5, 1)], "hei": [(1, 2)],
    "dii": [(1, 2)], "diis": [(1, 2)], "iis": [(0, 2)], "ii": [(0, 2)], "iisdem": [(0, 2), (4, 1)],
    "iidem": [(0, 2), (3, 1)], "dehinc": [(1, 3)], "quoi": [(2, 2)],
    "proind": [(2, 2)], "deind": [(1, 2)],  # elided forms, as written in the recitation text
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_word(word: str) -> str:
    return strip_accents(word).lower().replace("j", "i").replace("k", "c").replace("w", "u").replace("v", "u")


def V(i, n=1, long=None, diph=False):
    return {"t": "V", "i": i, "n": n, "long": long, "diph": diph}


def C(i, ch, n=1, w=1, **kw):
    d = {"t": "C", "i": i, "n": n, "w": w, "ch": ch}
    d.update(kw)
    return d


def base_units(lw: str):
    """Phonological units of a normalized word."""
    if lw in SPECIAL_SYLLABLES:
        units, pos = [], 0
        for (ni, nl) in SPECIAL_SYLLABLES[lw]:
            for j in range(pos, ni):
                if lw[j] != "h":
                    units.append(C(j, lw[j]))
            units.append(V(ni, nl, long=True if nl >= 2 and lw not in ("hei",) else None, diph=nl >= 2))
            pos = ni + nl
        for j in range(pos, len(lw)):
            if lw[j] != "h":
                units.append(C(j, lw[j]))
        return units
    L = len(lw)
    hidden_j = None
    m = re.match(r"^(ab|ob|sub|ad|con|in|dis)ic[ie]", lw)
    if m:
        hidden_j = len(m.group(1))
    silent = set()
    if lw.startswith(("mich", "nich")):
        silent = {2, 3}

    def isv(j):
        return 0 <= j < L and lw[j] in VOWELS

    units = []

    def prev_V():
        return bool(units) and units[-1]["t"] == "V"

    i = 0
    while i < L:
        c = lw[i]
        if i in silent:
            i += 1
            continue
        if i == hidden_j:
            units.append(C(i, "j", cons_i=True, hidden=True))
        if c in VOWELS:
            nxt = lw[i + 1] if i + 1 < L else ""
            # consonantal i
            if c == "i" and isv(i + 1) and nxt != "i":
                if i == 0 and not lw.startswith(NO_INIT_J) and lw not in NO_INIT_J_WORDS \
                        and not (lw[1:2] == "u" and lw[2:3] in ("i", "e")):
                    units.append(C(i, "j", cons_i=True))
                    i += 1
                    continue
                if prev_V():
                    units.append(C(i, "j", w=2, cons_i=True))
                    i += 1
                    continue
                if any(lw.startswith(p) and i == len(p) for p in I_PREFIXES) and not lw.startswith(("inier", "inii", "inient")):
                    units.append(C(i, "j", cons_i=True))
                    i += 1
                    continue
            # consonantal u
            if c == "u" and isv(i + 1):
                prev = lw[i - 1] if i else ""
                cons, glide = False, False
                if i == 0 or prev_V():
                    cons = True
                elif prev == "g" and i >= 2 and lw[i - 2] == "n":
                    units.append(C(i, "v", w=0, cons_u=True, glide=True))
                    i += 1
                    continue
                elif prev in "lr" and i >= 2 and lw[i - 2] in VOWELS and not (lw[i + 1] == "u" and isv(i + 2)) \
                        and not lw.startswith(("belu", "dissilu", "resilu", "insilu", "exsilu", "absilu", "transilu")) \
                        and not (lw[:i + 1].endswith("silu") and not re.match(r"(a|o|is$|es|ic|ul)", lw[i + 1:])) and (
                        lw[i + 1] in "aou" or lw.startswith(V_STEMS) or any(st in lw[:i + 1] for st in V_STEMS_IN)):
                    cons = True
                elif any(lw.startswith(p) and i == len(p) for p in U_PREFIXES):
                    cons = True
                elif prev == "s" and any(s in lw for s in SU_CONSONANT):
                    units.append(C(i, "v", w=0, cons_u=True, glide=True))
                    i += 1
                    continue
                elif i == L - 2 and lw.endswith("ue") and prev in "mstdrlncx" and lw not in UE_VOCALIC:
                    cons = True
                if cons:
                    units.append(C(i, "v", cons_u=True, glide=glide))
                    i += 1
                    continue
            two = lw[i:i + 2]
            # ae / oe
            if two in ("ae", "oe"):
                hiatus = (two == "ae" and (lw.startswith(HIATUS_AE_PREFIX) or (i == 0 and lw in AER_WORDS))) or \
                         (two == "oe" and lw.startswith(HIATUS_OE_PREFIX))
                if not hiatus:
                    after = lw[i + 2] if i + 2 < L else ""
                    before_vowel = after in VOWELS and not (after in "ui" and isv(i + 3))
                    units.append(V(i, 2, long=None if before_vowel else True, diph=True))
                    i += 2
                    continue
                if two == "ae" and i == 0 and lw in AER_WORDS:
                    units.append(V(i, 1, long=True))
                    i += 1
                    continue
            if two == "au" and not isv(i + 2):
                units.append(V(i, 2, long=True, diph=True))
                i += 2
                continue
            if two == "eu" and not isv(i + 2):
                rest = lw[i + 2:]
                hiatus = rest in ("s", "m") or rest.startswith(("nt", "nd", "sque", "mque", "sue", "mue", "sne", "mne")) \
                    or lw in ("deus", "meus", "reus", "eum")
                if lw in ("ceu", "seu", "neu", "heu", "heus", "eheu") or not hiatus:
                    units.append(V(i, 2, long=True, diph=True))
                    i += 2
                    continue
            units.append(V(i))
            i += 1
            continue
        if c == "h":
            i += 1
            continue
        if c == "q" and i + 1 < L and lw[i + 1] == "u":
            units.append(C(i, "q", n=2))
            i += 2
            continue
        if c in "ptcr" and i + 1 < L and lw[i + 1] == "h":
            units.append(C(i, c, n=2))
            i += 2
            continue
        if c == "x" or (c == "z" and i > 0):
            units.append(C(i, c, w=2))
            i += 1
            continue
        units.append(C(i, c))
        i += 1
    if lw in FI_FORMS:
        for u in units:
            if u["t"] == "V":
                u["long"] = True
                break
    return units


def variants(lw: str, units):
    """Yield (cost, units) alternative analyses of a word (single changes)."""
    out = []
    n = len(units)
    for j, u in enumerate(units):
        nxt = units[j + 1] if j + 1 < n else None
        if u["t"] == "C" and (u.get("cons_i") or u.get("cons_u")) and not u.get("glide"):
            # vocalize
            alt = [dict(x) for x in units]
            alt[j] = V(u["i"])
            out.append((1.0, alt))
        if u["t"] == "V" and not u["diph"] and nxt is not None and nxt["t"] == "V":
            ch = lw[u["i"]]
            if ch in "ieyo":
                alt = [dict(x) for x in units]
                alt[j] = C(u["i"], "j", w=0, synizesis=True)
                out.append((1.0, alt))
            if ch == "u" and j > 0:
                alt = [dict(x) for x in units]
                alt[j] = C(u["i"], "v", cons_u=True)
                out.append((1.2, alt))
            pair = lw[u["i"]:u["i"] + 2]
            if pair in ("ae", "oe", "eu", "ei", "oi", "ui", "au") and nxt["i"] == u["i"] + 1:
                alt = [dict(x) for x in units]
                alt[j:j + 2] = [V(u["i"], 2, long=True, diph=True)]
                out.append((1.0, alt))
        if u["t"] == "V" and u["diph"] and u["n"] == 2:
            alt = [dict(x) for x in units]
            alt[j:j + 1] = [V(u["i"]), V(u["i"] + 1)]
            out.append((1.5, alt))
        if u["t"] == "V" and u["long"] and not u["diph"]:
            alt = [dict(x) for x in units]
            alt[j] = dict(alt[j], long=None)
            out.append((1.0, alt))
    return out


def tokenize(line: str):
    """Return list of (word, start, end) over letter runs (incl. accented letters)."""
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", line)]


def build_syllables(words, elide_off=frozenset(), relax=False):
    """words: list of (word, units, lw). Returns syllables and elision info."""
    n = len(words)
    elided = {}
    for k in range(n - 1):
        if k in elide_off:
            continue
        w, units, lw = words[k]
        w2, units2, lw2 = words[k + 1]
        if not units or not units2:
            continue
        ends_vowel = units[-1]["t"] == "V"
        ends_vm = len(units) >= 2 and units[-1]["t"] == "C" and units[-1]["ch"] == "m" and units[-2]["t"] == "V"
        starts_vowel = units2[0]["t"] == "V"
        if (ends_vowel or ends_vm) and starts_vowel and lw not in NO_ELIDE:
            if lw2 in ("est", "es"):
                elided[k] = "est"
            else:
                elided[k] = "final"
    stream = []
    for k, (w, units, lw) in enumerate(words):
        us = list(units)
        if elided.get(k) == "final":
            last_v = max(j for j, u in enumerate(us) if u["t"] == "V")
            us = us[:last_v]
        if k > 0 and elided.get(k - 1) == "est":
            first_v = min(j for j, u in enumerate(us) if u["t"] == "V")
            us = us[:first_v] + us[first_v + 1:]
        for u in us:
            stream.append((k, u))
    vidx = [j for j, (k, u) in enumerate(stream) if u["t"] == "V"]
    sylls = []
    for a, j in enumerate(vidx):
        k, u = stream[j]
        nxt = vidx[a + 1] if a + 1 < len(vidx) else len(stream)
        cons = [stream[x] for x in range(j + 1, nxt)]
        weight = sum(cu["w"] for _, cu in cons)
        nk = stream[nxt][0] if nxt < len(stream) else None
        q = "L" if u.get("long") else "?"
        if weight >= 2:
            chars = [cu["ch"] for _, cu in cons if cu["w"] > 0]
            if len(chars) == 2 and chars[0] in MUTA and chars[1] in LIQUIDA and all(ck == cons[0][0] for ck, _ in cons):
                if q != "L":
                    q = "C"
            elif all(ck != k for ck, _ in cons) and q != "L" and cons[0][1]["ch"] == "s":
                q = "C"  # short final vowel before s+consonant of next word
            else:
                q = "L"
        elif weight == 0 and nxt < len(stream) and q != "L" and nk == k and not relax:
            q = "S"
        word_final = not any(stream[x][0] == k and stream[x][1]["t"] == "V" for x in range(j + 1, len(stream)))
        sylls.append({"word": k, "unit": u, "q": q, "next_word": nk, "word_final": word_final})
    return sylls, elided


def prior(s, words):
    """Soft preference for unknown syllables: +1 favours long, -1 favours short, 0 none."""
    if s["q"] != "?":
        return 0
    k = s["word"]
    w, units, lw = words[k]
    u = s["unit"]
    v = lw[u["i"]:u["i"] + u["n"]]
    tail = lw[u["i"] + u["n"]:]
    if s["word_final"]:
        if lw in LONG_MONO:
            return 1
        if lw.endswith(("que", "ue", "ne", "ce")) and u["i"] == len(lw) - 1 and len(lw) > 3:
            return -1
        if tail == "":
            if v == "a":
                return -1
            if v == "e":
                return -1
            if v in ("i", "y"):
                return 0 if lw in ANCEPS_FINAL_I else 1
            if v == "o":
                return -1 if lw in SHORT_FINAL_O else 1
            if v == "u":
                return 1
        if tail == "s":
            if v in ("a", "o", "e"):
                return 1
            if v == "u":
                return -1
        if tail in ("t", "d", "r", "l", "n", "c"):
            return -1 if lw not in ("hic", "hoc", "sic", "non", "sol", "uir", "uel", "nil", "nichil") else 0
    else:
        rest = lw[u["i"]:]
        if rest.startswith("ibus"):
            return -1
        if re.match(r"^(o|a)rum$", rest):
            return 1
    return 0


def patterns(nsyl):
    out = []
    for feet in itertools.product("DS", repeat=5):
        cnt = sum(3 if f == "D" else 2 for f in feet) + 2
        if cnt == nsyl:
            out.append("".join(feet) + "X")
    return out


def partial_patterns(nsyl):
    """Half-line patterns: m complete feet plus an optional final long (h) or long+anceps (t)."""
    out = []
    for m in range(0, 6):
        for feet in itertools.product("DS", repeat=m):
            base = sum(3 if f == "D" else 2 for f in feet)
            for tail, extra in (("", 0), ("h", 1), ("t", 2)):
                if base + extra == nsyl and (m or tail):
                    out.append("".join(feet) + tail)
    return out


def pattern_slots(p):
    slots = []
    for fi, f in enumerate(p):
        if f == "h":
            slots += [("L", fi, True)]
        elif f == "t":
            slots += [("L", fi, True), ("L", fi, False)]
        elif f == "D":
            slots += [("L", fi, True), ("S", fi, False), ("S", fi, False)]
        elif f == "S":
            slots += [("L", fi, True), ("L", fi, False)]
        else:
            slots += [("L", fi, True), ("A", fi, False)]
    return slots


def evaluate(p, sylls, words):
    slots = pattern_slots(p)
    if len(p) != 6 or p[-1] != "X":
        slots = slots[:-1] + [("A", slots[-1][1], slots[-1][2])]
    pen = 0.0
    for (req, fi, ic), s in zip(slots, sylls):
        q = s["q"]
        if req == "A":
            continue
        if req == "L" and q == "S":
            return None
        if req == "S" and q == "L":
            return None
        if req == "S" and q == "C":
            pen += 0.05
        if q == "?":
            pr = prior(s, words)
            if req == "L" and pr < 0:
                pen += 1
            if req == "S" and pr > 0:
                pen += 1
    if len(p) == 6 and p[4] == "S":
        pen += 3
    return pen


def try_scan(words, elide_off=frozenset(), relax=False):
    sylls, elided = build_syllables(words, elide_off, relax)
    best = []
    for p in patterns(len(sylls)):
        pen = evaluate(p, sylls, words)
        if pen is not None:
            best.append((pen, p))
    best.sort()
    return sylls, elided, best


def scan_words(words):
    """Search base analysis, then variants. Returns (cost, sylls, elided, cands, words_used, notes)."""
    sylls, elided, cands = try_scan(words)
    if cands:
        return 0.0, sylls, elided, cands, words, []
    found = []
    word_vars = []
    for k, (w, units, lw) in enumerate(words):
        for cost, alt in variants(lw, units):
            word_vars.append((cost, k, alt))
    # single variants
    for cost, k, alt in word_vars:
        ws = list(words)
        ws[k] = (words[k][0], alt, words[k][2])
        s2, e2, c2 = try_scan(ws)
        if c2:
            found.append((cost + c2[0][0], s2, e2, c2, ws, [f"variant:{words[k][0]}"]))
    if found:
        found.sort(key=lambda x: x[0])
        return found[0]
    # relaxation of vowel-before-vowel
    s2, e2, c2 = try_scan(words, relax=True)
    if c2:
        return 2.0, s2, e2, c2, words, ["relax"]
    # hiatus at an elision point
    for k in sorted(elided):
        s2, e2, c2 = try_scan(words, frozenset({k}))
        if c2:
            found.append((2.0 + c2[0][0], s2, e2, c2, words, [f"hiatus:{words[k][0]}"]))
    if found:
        found.sort(key=lambda x: x[0])
        return found[0]
    # pairs of variants
    for (c1, k1, a1), (c2_, k2, a2) in itertools.combinations(word_vars, 2):
        if k1 == k2:
            continue
        ws = list(words)
        ws[k1] = (words[k1][0], a1, words[k1][2])
        ws[k2] = (words[k2][0], a2, words[k2][2])
        s2, e2, c2 = try_scan(ws)
        if c2:
            found.append((c1 + c2_ + c2[0][0], s2, e2, c2, ws, [f"variant:{words[k1][0]}", f"variant:{words[k2][0]}"]))
    if found:
        found.sort(key=lambda x: x[0])
        return found[0]
    # variant + relax
    for cost, k, alt in word_vars:
        ws = list(words)
        ws[k] = (words[k][0], alt, words[k][2])
        s2, e2, c2 = try_scan(ws, relax=True)
        if c2:
            found.append((cost + 2 + c2[0][0], s2, e2, c2, ws, [f"variant:{words[k][0]}", "relax"]))
    if found:
        found.sort(key=lambda x: x[0])
        return found[0]
    return None


def scan_line(line: str):
    toks = tokenize(line)
    words = [(w, base_units(norm_word(w)), norm_word(w)) for w, a, b in toks]
    res = {"line": line, "tokens": toks, "ok": False, "pattern": None, "candidates": [], "irregular": None,
           "notes": []}
    if not words:
        res["irregular"] = "empty"
        return res
    r = scan_words(words)
    if r is None:
        sylls, elided = build_syllables(words)
        if len(sylls) < 12:
            cands = []
            for p in partial_patterns(len(sylls)):
                pen = evaluate(p, sylls, words)
                if pen is not None:
                    cands.append((pen + {"h": 0.0, "t": 0.3}.get(p[-1], 0.2), p))
            cands.sort()
            if cands:
                r = (0.0, sylls, elided, cands, words, ["partial"])
    if r is None:
        sylls, elided = build_syllables(words)
        res.update({"syllables": sylls, "elided": elided, "words": words,
                    "irregular": f"no pattern for {len(sylls)} syllables"})
        return res
    cost, sylls, elided, cands, words, notes = r
    res.update({"syllables": sylls, "elided": elided, "words": words, "notes": notes,
                "candidates": [(round(pen, 2), p) for pen, p in cands], "variant_cost": cost})
    best = cands[0]
    res["pattern"] = best[1]
    res["ok"] = True
    res["ambiguous"] = len(cands) > 1 and cands[1][0] - best[0] < 1.0
    slots = pattern_slots(best[1])
    for (req, fi, ic), s in zip(slots, sylls):
        s["foot"] = fi
        s["ictus"] = ic
    gaps = [line[toks[k][2]:toks[k + 1][1]] for k in range(len(toks) - 1)]
    res["caesura"] = find_caesura(sylls, best[1], elided, gaps, words) if len(best[1]) == 6 else None
    return res


PROCLITICS = {"et", "atque", "ac", "ad", "cum", "in", "ex", "e", "a", "ab", "abs", "de", "per", "sub", "sed", "nec",
              "neque", "aut", "uel", "si", "ut", "uti", "ob", "pro", "prae", "pre", "post", "ante", "super", "inter",
              "sine", "non", "ne", "dum", "quod", "quia", "seu", "siue", "neu", "ceu", "tam", "quam", "iam", "nam",
              "namque", "at", "ast", "o", "en", "per", "trans", "contra", "circum", "propter", "apud", "sic", "ubi",
              "quanquam", "quamquam", "quamuis", "postquam", "priusquam", "antequam", "donec", "nisi", "etsi",
              "quoniam", "quando", "uelut", "ueluti", "sicut", "tamquam", "tanquam", "ceu", "ne"}


def find_caesura(sylls, p, elided=None, gaps=None, words=None):
    """Return index of the word after which the main caesura falls, or None.
    gaps: list of inter-word strings (gap after word k) used to prefer a caesura at punctuation."""
    elided = elided or {}
    starts, idx = [], 0
    for f in p:
        starts.append(idx)
        idx += 3 if f == "D" else 2

    def boundary_after(si):
        if si + 1 >= len(sylls):
            return None
        a, b = sylls[si], sylls[si + 1]
        if a["word"] != b["word"] and a["word_final"]:
            if elided.get(a["word"]) == "est":
                w = a["word"] + 1  # pause after the prodelided est
            elif a["word"] in elided:
                return None
            else:
                w = a["word"]
            if words is not None and words[w][2] in PROCLITICS and not (gaps and w < len(gaps) and gaps[w].strip()):
                return None
            return w
        return None
    order = [starts[2]] + ([starts[2] + 1] if p[2] == "D" else []) + [starts[3]]
    cands = [w for w in (boundary_after(si) for si in order) if w is not None]
    if gaps:
        punct = [w for w in cands if w < len(gaps) and gaps[w].strip()]
        if punct and (not cands or cands[0] not in punct):
            # a sense pause at a legitimate caesura position wins over an unpunctuated penthemimeral
            if cands and cands[0] == boundary_after(starts[2]):
                return cands[0]
            return punct[0]
    if cands:
        return cands[0]
    return None


if __name__ == "__main__":
    import sys
    for l in sys.stdin:
        l = l.rstrip("\n")
        r = scan_line(l)
        print(r["pattern"], r["candidates"][:3], r.get("irregular") or "", r["notes"], "|", l)
