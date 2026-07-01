"""
translate_sample.py — Quick-start translation examples
=======================================================
Demonstrates the v22 parser on key benchmark lines from the manuscript.
No corpus file required.

Run:  python examples/translate_sample.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "parser"))

from parser import interpret, is_known, clean_word

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  Voynich Manuscript - v22 Parser  Sample Translations       ║
║  Hypothesis: Latin botanical abbreviation system            ║
╚══════════════════════════════════════════════════════════════╝
"""

EXAMPLES = [
    {
        "ref":   "f112r.10  (recipe section — simplest prescription)",
        "eva":   "dair.al.chedy.qodain.dam",
        "notes": "Heartwood + sapwood, through bark, of heartwood — [process].\n"
                 "Clearest single prescription in the corpus.",
    },
    {
        "ref":   "f5v.2  (Malva / mallow — botanically validated)",
        "eva":   "dchol.chol.otaiin.dain.cthor.chots.ychopordg",
        "notes": "Bark and bark's surface-ring, heartwood: mucilaginous [cthor].\n"
                 "Mallow (Malva) is actually mucilaginous — independent botanical match.",
    },
    {
        "ref":   "f5v.6  (Malva summary — 3-word micro-line)",
        "eva":   "otol.chol.dairodg",
        "notes": "Trichome: bark → heartwood. Trichomes connect bark to heartwood.",
    },
    {
        "ref":   "f3r.15  (word-order rule 3 — dual environmental terms)",
        "eva":   "chol.shor.shey.chor.dor.chols.chom.am",
        "notes": "Bark, cork — [moist] bark, fragrant bark. [shaded]. [process].\n"
                 "shey (humidus) at position 0.29 (front) + chom (umbrosus) at 0.86 (back)\n"
                 "→ both obey word-order rule 3 simultaneously.",
    },
    {
        "ref":   "f112r.26  (minimal prescription — 3 words)",
        "eva":   "tockhy.chedy.chedam",
        "notes": "Harmful [tockhy, sentence-initial proposition] bark, through bark — [process].\n"
                 "Demonstrates word-order rule 2 exception type A.",
    },
    {
        "ref":   "f101r.10  (pharma section — summary/closing line)",
        "eva":   "ysho.qykeeol.chol.sho.odor.dor.chees.ykeol.chol.dol.kor.ol.chso.sha.olcheeol.kolshey.okeoly.aiioly",
        "notes": "That cork, and bark — cork — scent, scent; bark [is] — that decoct+lignum,\n"
                 "bark, pith, golden lignum; bark — cork — lignum; moist [humidus], outer-type, lignum-type.",
    },
]


def translate_line(eva_line: str):
    tokens = []
    for raw in eva_line.split("."):
        w = clean_word(raw)
        if not w:
            continue
        interp = interpret(w)
        tokens.append((w, interp))
    return tokens


def main():
    print(BANNER)

    for ex in EXAMPLES:
        print(f"  ── {ex['ref']} {'─'*(55-len(ex['ref']))}")
        print(f"  EVA:  {ex['eva']}\n")

        tokens = translate_line(ex["eva"])
        hits   = sum(1 for _, i in tokens if i)
        total  = len(tokens)

        for w, interp in tokens:
            mark = "✓" if interp else "·"
            print(f"    {mark} {w:22s} → {interp or '?'}")

        print(f"\n  Rate: {hits}/{total} = {hits/total*100:.0f}%")
        print(f"  Note: {ex['notes']}")
        print()

    print("─" * 65)
    print("For full corpus analysis, run:")
    print("  python parser/analyze.py --input ZL_ivtff_2b.txt")
    print("  python parser/analyze.py --input ZL_ivtff_2b.txt --folio f112r")
    print("  python parser/analyze.py --input ZL_ivtff_2b.txt --permutation 1000")


if __name__ == "__main__":
    main()
