"""
test_parser.py - Unit tests for the v22 Voynich parser
=======================================================
Run:  python -m pytest tests/test_parser.py -v
  or: python tests/test_parser.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "parser"))

from parser import clean_word, parse, interpret, is_known, ROOTS

# ── Helpers ───────────────────────────────────────────────────────────────────

def check(word, expected_root=None, expected_prefix=None, expected_suffix=None,
          expect_known=True, mode="strict"):
    pfx, root, sfx = parse(clean_word(word), mode=mode)
    ok = True
    msgs = []
    if expected_root is not None and root != expected_root:
        msgs.append(f"root: got {root!r}, expected {expected_root!r}")
        ok = False
    if expected_prefix is not None and pfx != expected_prefix:
        msgs.append(f"prefix: got {pfx!r}, expected {expected_prefix!r}")
        ok = False
    if expected_suffix is not None and sfx != expected_suffix:
        msgs.append(f"suffix: got {sfx!r}, expected {expected_suffix!r}")
        ok = False
    known = is_known(clean_word(word), mode=mode)
    if expect_known and not known:
        msgs.append("expected known but got unknown")
        ok = False
    if not expect_known and known:
        msgs.append("expected unknown but got known")
        ok = False
    return ok, f"{word}: " + "; ".join(msgs) if msgs else f"{word}: OK"


# ── Test cases ────────────────────────────────────────────────────────────────

TESTS = [
    # (word, expected_root, expected_prefix, expected_suffix, expect_known)

    # Basic roots — direct match
    ("chol",    "chol",   None,  None,  True),
    ("daiin",   "daiin",  None,  None,  True),
    ("sheol",   "sheol",  None,  None,  True),
    ("ol",      "ol",     None,  None,  True),
    ("al",      "al",     None,  None,  True),
    ("aiin",    "aiin",   None,  None,  True),
    ("ar",      "ar",     None,  None,  True),

    # retained direct-root checks
    ("air",     "air",    None,  None,  True),
    ("aiir",    "aiir",   None,  None,  True),

    # single-character function words
    ("o",       "o",      None,  None,  True),
    ("l",       "l",      None,  None,  True),
    ("r",       "r",      None,  None,  True),
    ("d",       "d",      None,  None,  True),

    # Prefix stripping. Strict mode requires the remaining stem to be fully consumed.
    ("qochol",  "chol",   "qo",  None,  True),
    ("opchedy", "ch",     "op",  "edy", True),
    ("ycheol",  "ch",     "y",   "eol", True),
    ("pchedy",  "ch",     "p",   "edy", True),

    # Suffix matching
    ("chedy",   "ch",     None,  "edy", True),   # cortex + through
    ("sheody",  "she",    None,  "ody", True),   # suber? + -ward (longest root match)
    ("darindy", None,     None,  None,  False),  # legacy-only substring match

    # Compound prefix + suffix (suffix needs exact stem match after prefix)
    ("qocheol", "ch",    "qo",  "eol", True),

    # Grammar words
    ("am",   "am",    None,  None,  True),
    ("s",    "s",     None,  None,  True),
    ("ee",   "ee",    None,  None,  True),
    ("dy",   "dy",    None,  None,  True),

    # Property terms
    ("cthor", "cthor", None, None, True),
    ("cthy",  "cthy",  None, None, True),
    ("ckhy",  "ckhy",  None, None, True),

    # Environmental terms
    ("shey",  "shey",  None, None, True),
    ("sar",   "sar",   None, None, True),
    ("chom",  "chom",  None, None, True),

    # f112r.10 — benchmark prescription
    ("dair",   "dair",  None, None,  True),
    ("chedy",  "ch",    None, "edy", True),
    ("dam",    "dam",   None, None,  True),

    # f5v — Malva (mallow) benchmark: cthor should appear
    ("dain",   "dain",  None, None,  True),
    ("otaiin", None,    None, None,  False),  # legacy-only substring match

    # Unknown words (should not be known)
    ("xyz",    None, None, None, False),
    ("jeiii",  None, None, None, False),  # EVA transcription artifact
]


def run_tests():
    passed = 0
    failed = 0
    for args in TESTS:
        word = args[0]
        kwargs = {
            "expected_root":   args[1],
            "expected_prefix": args[2],
            "expected_suffix": args[3],
            "expect_known":    args[4],
        }
        ok, msg = check(word, **kwargs)
        status = "PASS" if ok else "FAIL"
        if not ok:
            print(f"  [{status}] {msg}")
            failed += 1
        else:
            passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed / {len(TESTS)} total")
    return failed == 0


def test_legacy_substring_fallback():
    """Published v21 rates depend on these legacy-only partial matches."""
    legacy_only = [
        ("qockhol", "qo"),
        ("otaiin", None),
        ("ychopordg", "y"),
        ("darindy", None),
    ]
    for word, expected_prefix in legacy_only:
        assert not is_known(word), f"{word} should be unknown in strict mode"
        pfx, root, sfx = parse(word, mode="legacy")
        assert root is not None, f"{word} should have a legacy substring root"
        if expected_prefix is not None:
            assert pfx == expected_prefix
    print(f"  [PASS] legacy substring fallback documented ({len(legacy_only)} words)")


# ── Specific validation: f112r.10 full line ───────────────────────────────────

def test_f112r_10():
    """
    f112r.10: dair.al.chedy.qodain.dam
    Expected translation: heartwood and sapwood, through bark, of heartwood — [process]
    This is the clearest single prescription in the recipe section.
    """
    line = "dair.al.chedy.qodain.dam"
    words = [clean_word(w) for w in line.split(".") if clean_word(w)]
    interpretations = [interpret(w) for w in words]

    assert interpretations[0] is not None, "dair should be known"
    assert "duramen" in interpretations[0] or "심재" in interpretations[0]

    assert interpretations[1] is not None, "al should be known"
    assert "alburnum" in interpretations[1] or "변재" in interpretations[1]

    assert interpretations[4] is not None, "dam should be known"
    assert "처리" in interpretations[4] or "verb" in interpretations[4].lower()

    rate = sum(1 for i in interpretations if i is not None) / len(interpretations)
    assert rate == 1.0, f"f112r.10 should be 100% known, got {rate:.0%}"
    print("  [PASS] f112r.10 full-line validation")


# ── Marci table cross-validation ──────────────────────────────────────────────

def test_marci_direct_correspondences():
    """
    Marci's alphabet table (f1r, Davis 2024) shows direct 1:1 correspondences
    for several EVA glyphs. These should all parse as known roots or prefixes.
    Direct Marci correspondences: d→d, e→e, k→k, l→l, r→r, s→s, t→t, y→y
    """
    # Note: 'e' alone is not in ROOTS (ee = et/eius is)
    # Note: 'y' alone parses as unknown (it is a suffix/prefix marker, not standalone root)
    # Marci's direct correspondences that are standalone roots:
    direct = ["d", "k", "l", "r", "s", "t"]
    for glyph in direct:
        assert is_known(glyph), f"Marci-direct glyph '{glyph}' should be known"
    print(f"  [PASS] Marci direct correspondences ({len(direct)} glyphs)")


if __name__ == "__main__":
    print("Voynich v22 Parser - Unit Tests\n")
    ok = run_tests()
    print()
    test_legacy_substring_fallback()
    test_f112r_10()
    test_marci_direct_correspondences()
    sys.exit(0 if ok else 1)
