"""
analyze.py — Corpus-level analysis of the Voynich Manuscript
=============================================================
Usage:
  python analyze.py --input path/to/ZL_ivtff_2b.txt
  python analyze.py --input path/to/ZL_ivtff_2b.txt --folio f112r
  python analyze.py --input path/to/ZL_ivtff_2b.txt --permutation 1000
"""

import re
import argparse
import random
from collections import Counter, defaultdict
from parser import clean_word, parse, interpret, is_known, ROOTS, PREFIXES, SUFFIXES

# Section definitions (folio number ranges)
SECTIONS = {
    "herbal":       (1,   66,  "Plant anatomy + properties + prescriptions"),
    "astronomical": (70,  73,  "Homo Signorum / seasonal herbal calendar"),
    "biological":   (74,  84,  "Sap-flow diagrams (Fasciculus Medicinae style)"),
    "pharma_roots": (87,  96,  "Root cross-section catalogue"),
    "pharma_rx":    (99,  102, "Part-labelled prescriptions"),
    "recipes":      (103, 116, "Dense prescription text (am-terminal lines)"),
}


def folio_num(folio: str) -> int:
    m = re.match(r"f(\d+)", folio)
    return int(m.group(1)) if m else 0


def section_of(fnum: int) -> str:
    for name, (lo, hi, _) in SECTIONS.items():
        if lo <= fnum <= hi:
            return name
    return "other"


def load_corpus(path: str):
    """Load ZL transcription and return list of (folio, fnum, text) tuples."""
    lines = []
    with open(path, "r", encoding="latin-1") as f:
        for raw in f:
            m = re.match(r"<(f(\d+)[rv]?)\.(\d+)[^>]*>\s*(.*)", raw.rstrip())
            if not m:
                continue
            folio, fnum, text = m.group(1), int(m.group(2)), m.group(4)
            text = re.sub(r"<%>|<\$>", "", text).strip()
            lines.append((folio, fnum, text))
    return lines


def corpus_words(lines):
    """Yield cleaned words from corpus lines that fall within a known section."""
    for folio, fnum, text in lines:
        if section_of(fnum) == "other":
            continue
        for w in re.split(r"[.,]", text):
            w = clean_word(w)
            if w:
                yield w


def interpretation_rate(words, mode="strict"):
    total = 0
    hits  = 0
    for w in words:
        total += 1
        if is_known(w, mode=mode):
            hits += 1
    return hits, total


def section_stats(lines, mode="strict"):
    stats = defaultdict(lambda: {"hits": 0, "total": 0, "am_lines": 0, "folios": set()})
    for folio, fnum, text in lines:
        sec = section_of(fnum)
        if sec == "other":
            continue
        words = [clean_word(w) for w in re.split(r"[.,]", text) if clean_word(w)]
        h = sum(1 for w in words if is_known(w, mode=mode))
        stats[sec]["hits"]   += h
        stats[sec]["total"]  += len(words)
        stats[sec]["folios"].add(folio)
        if any(w in ("am", "om", "dam") or w.endswith("am") or w.endswith("om")
               for w in words):
            stats[sec]["am_lines"] += 1
    return stats


def is_strictly_parsed(token, roots, prefixes=PREFIXES, suffixes=SUFFIXES):
    """
    Return True only when the full EVA token is consumed by strict grammar.

    This mirrors parser.parse(..., mode="strict") for arbitrary root sets:
      1. exact token in roots
      2. optional one-prefix stripping using parser prefix priority
      3. optional one-suffix stripping using parser suffix priority
      4. remaining stem must be in roots

    No partial substring match is allowed.
    """
    if token in roots:
        return True

    stem = token
    for pfx in prefixes:
        if stem.startswith(pfx) and len(stem) > len(pfx):
            stem = stem[len(pfx):]
            break

    for sfx in suffixes:
        if stem.endswith(sfx) and len(stem) > len(sfx):
            candidate = stem[: -len(sfx)]
            if candidate in roots:
                return True

    return stem in roots


def is_legacy_recognized(token, roots, prefixes=PREFIXES, suffixes=SUFFIXES):
    """Reproduce exploratory v21 recognition, including substring fallback."""
    if is_strictly_parsed(token, roots, prefixes=prefixes, suffixes=suffixes):
        return True

    stem = token
    for pfx in prefixes:
        if stem.startswith(pfx) and len(stem) > len(pfx):
            stem = stem[len(pfx):]
            break

    for length in range(min(8, len(stem)), 0, -1):
        for start in range(len(stem) - length + 1):
            if stem[start:start+length] in roots:
                return True
    return False


def root_rate_with_mode(words_or_counts, root_set, mode="strict"):
    """Interpret words with a supplied root set under strict or legacy rules."""
    word_counts = words_or_counts if isinstance(words_or_counts, Counter) else Counter(words_or_counts)

    if mode == "strict":
        hits = sum(count for w, count in word_counts.items() if is_strictly_parsed(w, root_set))
    elif mode == "legacy":
        hits = sum(count for w, count in word_counts.items() if is_legacy_recognized(w, root_set))
    else:
        raise ValueError("mode must be 'strict' or 'legacy'")

    total = sum(word_counts.values())
    return hits / total if total else 0.0


def permutation_test(all_words, n_trials=1000, seed=42, mode="strict"):
    """
    Compare v21 interpretation rate against random root sets of the same size.

    Returns:
      (v21_rate, null_distribution, z_score, p_value)
    """
    random.seed(seed)
    word_counts = Counter(all_words)
    vocab = list(word_counts)
    n_roots = len(ROOTS)

    v21_rate = root_rate_with_mode(word_counts, set(ROOTS.keys()), mode=mode)

    null_dist = []
    for _ in range(n_trials):
        rand_roots = set(random.sample(vocab, min(n_roots, len(vocab))))
        null_dist.append(root_rate_with_mode(word_counts, rand_roots, mode=mode))

    null_dist.sort()
    mu  = sum(null_dist) / len(null_dist)
    std = (sum((x - mu) ** 2 for x in null_dist) / len(null_dist)) ** 0.5
    z   = (v21_rate - mu) / std if std > 0 else float("inf")
    p   = sum(1 for s in null_dist if s >= v21_rate) / len(null_dist)

    return v21_rate, null_dist, z, p


def translate_folio(lines, target_folio, mode="strict"):
    """Print word-by-word translation for a single folio."""
    folio_lines = [(fo, fn, tx) for fo, fn, tx in lines if fo.startswith(target_folio)]
    if not folio_lines:
        print(f"Folio '{target_folio}' not found in corpus.")
        return

    print(f"\n{'='*65}")
    print(f"  {target_folio} — v21 translation")
    print(f"{'='*65}")

    for folio, fnum, text in folio_lines:
        words = [clean_word(w) for w in re.split(r"[.,]", text) if clean_word(w)]
        hits  = sum(1 for w in words if is_known(w, mode=mode))
        am    = "★" if any(w in ("am","om","dam") or w.endswith(("am","om"))
                            for w in words) else " "
        print(f"\n  {am}{folio}  ({hits}/{len(words)} = {hits/max(len(words),1)*100:.0f}%)")
        print(f"    EVA: {text}")
        for w in words:
            interp = interpret(w, mode=mode)
            mark = "✓" if interp else "·"
            print(f"    {mark} {w:22s} → {interp or '?'}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Voynich v21 corpus analyzer")
    ap.add_argument("--input", required=True, help="Path to ZL_ivtff_2b.txt")
    ap.add_argument("--folio", help="Translate a single folio (e.g. f112r)")
    ap.add_argument("--permutation", type=int, metavar="N",
                    help="Run permutation test with N trials (e.g. 1000)")
    ap.add_argument("--section", help="Show stats for one section only")
    ap.add_argument("--mode", choices=("strict", "legacy"), default="strict",
                    help="strict consumes the full word; legacy reproduces substring fallback")
    ap.add_argument("--compare-modes", action="store_true",
                    help="print strict and legacy rates side by side")
    args = ap.parse_args()

    print(f"Loading corpus: {args.input}")
    lines = load_corpus(args.input)
    print(f"  {len(lines)} lines loaded\n")

    if args.folio:
        translate_folio(lines, args.folio, mode=args.mode)
        return

    # Default: section summary
    all_words = list(corpus_words(lines))
    hits, total = interpretation_rate(all_words, mode=args.mode)

    if args.compare_modes:
        strict_hits, strict_total = interpretation_rate(all_words, mode="strict")
        legacy_hits, legacy_total = interpretation_rate(all_words, mode="legacy")
        print("Mode comparison:")
        print(f"  strict: {strict_hits}/{strict_total} = {strict_hits/strict_total*100:.2f}%")
        print(f"  legacy: {legacy_hits}/{legacy_total} = {legacy_hits/legacy_total*100:.2f}%")
        print()

    print(f"Section breakdown ({args.mode} mode):")
    print(f"  {'Section':16s} {'Pages':6s} {'Lines':7s} {'Tokens':8s} {'Rate':7s}")
    print(f"  {'-'*50}")
    stats = section_stats(lines, mode=args.mode)
    for sec, (lo, hi, desc) in SECTIONS.items():
        s = stats.get(sec, {})
        h, t = s.get("hits", 0), s.get("total", 0)
        rate = f"{h/t*100:.1f}%" if t else "—"
        pages = len(s.get("folios", set()))
        lines_n = s.get("am_lines", 0)  # reuse field
        print(f"  {sec:16s} {pages:6d} {s.get('am_lines',0):7d}am  {t:7d}  {rate:>7s}")
    print(f"  {'-'*50}")
    print(f"  {'TOTAL':16s} {'':6s} {'':7s} {total:7d}  {hits/total*100:.2f}%\n")

    if args.permutation:
        print(f"Running permutation test (n={args.permutation}, mode={args.mode})...")
        v21_rate, null_dist, z, p = permutation_test(all_words, args.permutation, mode=args.mode)
        mu  = sum(null_dist) / len(null_dist)
        std = (sum((x-mu)**2 for x in null_dist)/len(null_dist))**0.5
        trials_ge = sum(1 for s in null_dist if s >= v21_rate)
        empirical = f"< {1/args.permutation:.6f}" if trials_ge == 0 else f"{p:.6f}"
        print(f"\n  Observed {args.mode} rate: {v21_rate*100:.3f}%")
        print(f"  Null mean:           {mu*100:.3f}%")
        print(f"  Null std:            {std*100:.3f}%p")
        print(f"  Null max:            {max(null_dist)*100:.3f}%")
        print(f"  z-score:             {z:.2f}σ")
        print(f"  empirical p:         {empirical}")
        print(f"  Trials ≥ observed:   {trials_ge}/{args.permutation}")
        verdict = "SIGNIFICANT" if p < 0.001 else f"p = {p:.4f}"
        print(f"  Verdict:        {verdict}")


if __name__ == "__main__":
    main()
