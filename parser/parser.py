"""
voynich_parser.py - Voynich Manuscript v22 Parser
==================================================
Hypothesis: The Voynich Manuscript is a compressed Latin botanical-medical
reference text from 14th–15th century North Italy (Padua region), encoding
plant anatomy and pharmacy using abbreviated Latin roots + preserved grammar
suffixes.

Data source: Zandbergen-Landini (ZL) transcription, ivtff_2b format (2022-12-25)
Transcription system: EVA (Extended Voynich Alphabet)

Strict Full-Token Validation rate: 51.11% (15,848 / 31,007 tokens)
Exploratory Recognition rate: 98.66% (30,590 / 31,007 tokens)

References:
  - Mondino dei Luzzi, Anathomia (1316)
  - Tacuinum Sanitatis (1380–1450, North Italy)
  - Carrara Herbal (Padua dialect, 1390–1405)
  - Marci alphabet table (f1r, multispectral imaging, Davis 2024)

License: MIT
"""

import re
from typing import Optional, Tuple, Dict

# v22 Root Dictionary
# Format: EVA_string -> (Latin_source, Korean_gloss, English_gloss)

ROOTS: Dict[str, Tuple[str, str, str]] = {
    # Structural terms — Mondino Anathomia
    "chol":   ("cortex",    "수피",     "bark/cortex"),
    "chor":   ("cortex",    "수피",     "bark/cortex"),
    "cheol":  ("cortex",    "수피류",   "bark-type"),
    "cheor":  ("cortex",    "수피류",   "bark-type"),
    "cheo":   ("cortex",    "수피",     "bark/cortex"),
    "cho":    ("cortex",    "수피",     "bark/cortex"),
    "ch":     ("cortex",    "수피",     "bark/cortex"),
    "daiin":  ("duramen",   "심재",     "heartwood"),
    "dain":   ("duramen",   "심재",     "heartwood"),
    "dar":    ("duramen",   "심재",     "heartwood"),
    "dair":   ("duramen",   "심재",     "heartwood"),
    "dal":    ("medulla",   "수髓",     "pith/medulla"),
    "dol":    ("medulla",   "수髓",     "pith/medulla"),
    "ol":     ("lignum",    "목질",     "wood/lignum"),
    "al":     ("alburnum",  "변재",     "sapwood/alburnum"),
    "aiin":   ("annulus",   "나이테",   "growth ring"),
    "ain":    ("annulus",   "나이테",   "growth ring"),
    "aiiin":  ("annulus",   "나이테강조","growth ring (emphatic)"),
    "aiir":   ("annulus+radius","나이테+수선","ring+ray"),
    "ar":     ("radius",    "수선",     "medullary ray"),
    "sheol":  ("suber",     "코르크",   "cork/suber"),
    "shor":   ("suber",     "코르크",   "cork/suber"),
    "shol":   ("suber",     "코르크",   "cork/suber"),
    "sheo":   ("suber",     "코르크",   "cork/suber"),
    "sh":     ("suber",     "코르크",   "cork/suber"),
    "okeol":  ("exterior",  "외층",     "outer layer"),
    "okol":   ("exterior",  "외층",     "outer layer"),
    "ok":     ("exterior",  "외층",     "outer layer"),
    "ot":     ("exterior",  "표면",     "surface"),
    "air":    ("aureus",    "황색",     "golden/yellow"),
    "or":     ("aureus",    "황색",     "golden/yellow"),
    "od":     ("odor",      "향기",     "scent/odor"),
    "dor":    ("odor",      "향기",     "scent/odor"),
    "ee":     ("et/eius",   "그리고",   "and/its"),
    # Processing/functional terms
    "chy":    ("chylos",    "즙",       "juice/chyle (Greek χυλός)"),
    "k":      ("coquitur",  "달임",     "decoction/processing"),
    "t":      ("tunica",    "막/층",    "membrane/layer"),
    "s":      ("est",       "이다",     "is/est"),
    # Property terms — Regimen Sanitatis / Tacuinum
    "cthor":  ("phlegma",   "점액질",   "mucilage/phlegm"),
    "otol":   ("pilus",     "선모",     "hair/trichome"),
    "char":   ("spina",     "가시",     "spine/thorn"),
    "ckhy":   ("nocumentum","유해성",   "harmfulness"),
    "cthy":   ("calidus",   "열/자극",  "heat/pungency"),
    # Sap/humour terms
    "sol":    ("succus",    "수액",     "sap/juice"),
    "sain":   ("succus",    "수액",     "sap/juice"),
    "sal":    ("sanguis",   "혈수액",   "blood-sap"),
    "sor":    ("succus-",   "수액감소", "reduced sap"),
    # Environmental terms (inductively derived)
    "shey":   ("humidus",   "수생/습",  "aquatic/moist"),
    "sheey":  ("humidus",   "수생/습",  "aquatic/moist"),
    "sar":    ("saxosus",   "바위토양", "rocky soil"),
    "cthar":  ("durus",     "단단건조", "hard/dry"),
    "chom":   ("umbrosus",  "그늘",     "shaded"),
    # Grammar words
    "dy":     ("de",        "~의",      "of/from"),
    "tol":    ("totus",     "전체",     "whole/total"),
    "am":     ("[verb]",    "[처리]",   "[process/treat]"),
    "om":     ("[verb]",    "[처리]",   "[process/treat]"),
    "dam":    ("[verb]",    "[처리]",   "[process/treat]"),
    "she":    ("suber?",    "코르크?",  "cork? (uncertain)"),
    "p":      ("pro",       "위해",     "for/pro"),
    # Astronomical section terms
    "oteos":  ("exterior (seasonal)", "외층표면(계절)", "outer surface (seasonal)"),
    "okeos":  ("exterior (seasonal)", "외층(계절)",    "outer layer (seasonal)"),
    "oteo":   ("exterior (seasonal)", "외층(계절)",    "outer (seasonal)"),
    "okeo":   ("exterior (seasonal)", "외층(계절)",    "outer (seasonal)"),
    "okody":  ("exterior (directional)","외층방향",    "outer layer (directional)"),
    # Single-character function words (Marci table + statistical basis)
    "o":      ("aut",       "또는",     "or/aut  [standalone only; prefix o- = exterior]"),
    "l":      ("il-",       "관사",     "article il- [standalone]"),
    "r":      ("re-",       "역",       "reverse/re- [standalone]"),
    "d":      ("de",        "~의",      "of/de [standalone]"),
}

# Prefix priority order (highest → lowest)
PREFIXES = ["qo", "op", "r", "l", "p", "y"]

PREFIX_GLOSSES = {
    "qo": ("quod/de", "~의",    "of/from (quod/de)"),
    "op": ("contra",  "대향",   "against (contra)"),
    "r":  ("re-",     "역",     "reverse (re-)"),
    "l":  ("il-",     "관사",   "article (il-)"),
    "p":  ("pro",     "위해",   "for (pro)"),
    "y":  ("그-",     "지시",   "that/the (demonstrative)"),
}

# Suffix priority order (longest match first)
SUFFIXES = [
    "eeody", "eeol", "eeor", "eeos", "eeey", "eeo",
    "eedy", "edy", "eckhy", "ecthy", "ear", "eol", "eor", "eal", "es",
    "odaiin", "ody", "dy",
    "iin", "iiin",
    "eos", "eey", "ey", "y",
    "am", "om",
]

SUFFIX_GLOSSES = {
    "eeody": "-oideus (emphatic)",  "eeol": "+lignum (emphatic)",
    "eeor":  "+aureus (emphatic)",  "eeos": "plural (emphatic)",
    "eeey":  "from (emphatic)",     "eeo":  "conjunction (emphatic)",
    "eedy":  "through (emphatic)",  "edy":  "through (per)",
    "eckhy": "harmful (emphatic)",  "ecthy": "hot (emphatic)",
    "ear":   "+radius (emphatic)",  "eol":  "+lignum",
    "eor":   "+aureus",             "eal":  "+alburnum",
    "es":    "is (emphatic)",       "odaiin": "scent+ring",
    "ody":   "-ward/direction",     "dy":   "of (de)",
    "iin":   "ring-type",           "iiin": "ring-type (emphatic)",
    "eos":   "seasonal plural",     "eey":  "of (emphatic)",
    "ey":    "from/at",             "y":    "adjective",
    "am":    "[process]",           "om":   "[process]",
}


def clean_word(word: str) -> str:
    """Remove ZL transcription markup and normalize to lowercase."""
    word = re.sub(r"\{[^}]*\}", "", word)   # {uncertain readings}
    word = re.sub(r"\[[^\]]*\]", "", word)   # [alternative:readings]
    word = re.sub(r"@\d+;", "", word)        # @glyph_number; references
    word = re.sub(r"[<>!].*", "", word)      # <markup> and !corrections
    return re.sub(r"[^a-z]", "", word.lower())


def parse(word: str, mode: str = "strict") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse an EVA word into (prefix, root, suffix).

    Strict mode requires the full cleaned word to be consumed by the grammar:
      [optional prefix] + root + [optional suffix]

    Legacy mode reproduces the v21 paper/code behavior by falling back to a
    root substring search after prefix/suffix checks. Use it only for comparing
    against published 98.7% figures.

    Priority rules:
      1. Single-character words and exact ROOTS matches → direct lookup
      2. Prefix stripping (qo > op > r > l > p > y)
      3. Suffix matching (longest first, only if remaining stem is in ROOTS)
      4. Legacy only: root substring search (longest match first, 8→1 chars)

    Returns:
      (prefix, root, suffix) — any component may be None if not found.
    """
    if mode not in ("strict", "legacy"):
        raise ValueError("mode must be 'strict' or 'legacy'")

    w = word

    # Rule 1: direct match (handles single-char function words and aiir/air)
    if w in ROOTS:
        return None, w, None

    prefix: Optional[str] = None
    suffix: Optional[str] = None
    root:   Optional[str] = None

    # Rule 2: prefix
    for pfx in PREFIXES:
        if w.startswith(pfx) and len(w) > len(pfx):
            prefix = pfx
            w = w[len(pfx):]
            break

    # Rule 3: suffix (only if remaining stem is a known root)
    for sfx in SUFFIXES:
        if w.endswith(sfx) and len(w) > len(sfx):
            candidate = w[: -len(sfx)]
            if candidate in ROOTS:
                suffix = sfx
                w = candidate
                break

    if w in ROOTS:
        return prefix, w, suffix

    if mode == "strict":
        return None, None, None

    # Rule 4: legacy root substring fallback (longest match).
    for length in range(min(8, len(w)), 0, -1):
        for start in range(len(w) - length + 1):
            sub = w[start : start + length]
            if sub in ROOTS:
                root = sub
                break
        if root:
            break

    return prefix, root, suffix


def interpret(word: str, mode: str = "strict") -> Optional[str]:
    """
    Return a human-readable gloss for an EVA word, or None if unknown.

    Example:
      interpret("qokcheol") → "[~의] 수피류(cortex) +목질(lignum)"
    """
    w = clean_word(word)
    if not w:
        return None

    prefix, root, suffix = parse(w, mode=mode)
    parts = []

    if prefix:
        lat, kor, eng = PREFIX_GLOSSES.get(prefix, (prefix, prefix, prefix))
        parts.append(f"[{kor}({lat})]")

    if root:
        lat, kor, eng = ROOTS[root]
        parts.append(f"{kor}({lat})")
    elif not prefix and not suffix:
        return None  # completely unknown

    if suffix:
        gloss = SUFFIX_GLOSSES.get(suffix, suffix)
        parts.append(gloss)

    return " + ".join(parts) if parts else None


def is_known(word: str, mode: str = "strict") -> bool:
    """Return True if the word can be interpreted under the selected mode."""
    w = clean_word(word)
    if not w:
        return False
    prefix, root, suffix = parse(w, mode=mode)
    return bool(prefix or root or suffix)


def parse_line(zl_line: str, mode: str = "strict"):
    """
    Parse a single ZL transcription line.

    Args:
      zl_line: e.g. '<f112r.10,+P0>     dair.al.chedy.qodain.dam<$>'

    Returns:
      dict with keys: folio, line_num, words, interpretations, hit_rate
    """
    m = re.match(r"<(f(\d+[rv]?)\.\d+)[^>]*>\s*(.*)", zl_line.rstrip())
    if not m:
        return None

    folio, text = m.group(1), m.group(3)
    text = re.sub(r"<%>|<\$>", "", text).strip()
    raw_words = [w for w in re.split(r"[.,]", text) if w.strip()]

    results = []
    for raw in raw_words:
        cleaned = clean_word(raw)
        if cleaned:
            interp = interpret(cleaned, mode=mode)
            results.append({
                "raw":    raw.strip(),
                "clean":  cleaned,
                "interp": interp,
                "known":  interp is not None,
            })

    hits = sum(1 for r in results if r["known"])
    total = len(results)

    return {
        "folio":    folio,
        "words":    results,
        "hits":     hits,
        "total":    total,
        "hit_rate": hits / total if total else 0.0,
    }


# ── Word-order rules (v20, statistically validated) ──────────────────────────

WORD_ORDER_RULES = """
v20 Word-Order Rules (validated on ZL transcription, plant section f1–f66)

Rule 1 — Verb-initial prescription marker (3.8% of am-lines)
  k [BARK] [WOOD] ... am
  'k' (coquitur/decoction) may appear as first word, specifying the
  processing method explicitly. 'am' alone suffices for prescription closure.

Rule 2 — Post-nominal property placement (93.1% compliance)
  [BARK/WOOD]+ PROP
  Property terms (cthor, otol, char, ckhy, cthy) follow the structural
  term(s) they modify — Latin-style post-nominal adjective.
  Exception types:
    A (75% of exceptions): sentence-initial proposition ("point of departure")
       e.g.  cthor [BARK]... = "It is mucilaginous. The bark..."
    B: after FUNC connector (qo introduces new clause)
    C: PROP + PROP (properties modify each other)

Rule 3 — Environmental term placement (82.3% compliance)
  QUAL[front] [BARK...WOOD] PROP QUAL[back] am
  Environmental qualifiers appear at sentence edges, not in the middle:
    humidus (shey):  avg position 0.38 → introductory
    umbrosus (chom): avg position 0.84 → conclusory, directly before am
    saxosus  (sar):  avg position 0.00 → always sentence-initial
    durus    (cthar): avg position 0.64 → late

Translation template:
  prescription line: [ENV?] [parts outer→inner] [property post-nominal] [ENV?] am
  descriptive line:  [ENV?] [parts outer→inner] [property inserted] [parts continued]
"""
