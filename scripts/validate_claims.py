"""
Validate high-level claims after freezing the v21 dictionary.

This script does not retrain the dictionary. It evaluates fixed parser rules on:

1. deterministic blind folio holdouts;
2. all herbal folios for the three botanical IDs claimed in the paper;
3. simple Latin-like word-order heuristics under strict parsing.

Run:
  python scripts/validate_claims.py --input ../ZL_ivtff_2b.txt
  python scripts/validate_claims.py --input ../ZL_ivtff_2b.txt --mode legacy
"""

import argparse
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analyze import load_corpus, section_of  # noqa: E402
from parser import ROOTS, clean_word, parse, is_known  # noqa: E402


PROPERTY_ROOTS = {
    "cthor": "phlegma",
    "otol": "pilus",
    "char": "spina",
    "ckhy": "nocumentum",
    "cthy": "calidus",
}

ENV_ROOTS = {
    "shey": "humidus",
    "sheey": "humidus",
    "sar": "saxosus",
    "cthar": "durus",
    "chom": "umbrosus",
}

STRUCTURAL_ROOTS = {
    "chol", "chor", "cheol", "cheor", "cheo", "cho", "ch",
    "daiin", "dain", "dar", "dair", "dal", "dol",
    "ol", "al", "aiin", "ain", "aiiin", "aiir", "ar",
    "sheol", "shor", "shol", "sheo", "sh", "okeol", "okol", "ok", "ot",
}

CLAIMED_PROFILES = {
    "f5v": {
        "label": "Malva sylvestris",
        "weights": {"phlegma": 4, "humidus": 1},
    },
    "f28r": {
        "label": "Urtica dioica",
        "weights": {"pilus": 4, "calidus": 2, "nocumentum": 2},
    },
    "f55r": {
        "label": "Rosa canina",
        "weights": {"spina": 4, "nocumentum": 3, "odor": 2, "aureus": 1},
    },
}


def folio_words(lines):
    grouped = defaultdict(list)
    for folio, fnum, text in lines:
        for raw in re.split(r"[.,]", text):
            word = clean_word(raw)
            if word:
                grouped[folio].append((fnum, word))
    return grouped


def root_latin(root):
    if not root:
        return None
    return ROOTS[root][0]


def token_roots(words, mode):
    roots = []
    for _, word in words:
        _, root, _ = parse(word, mode=mode)
        if root:
            roots.append(root)
    return roots


def interpretation_summary(grouped, folios, mode):
    hits = 0
    total = 0
    for folio in folios:
        for _, word in grouped[folio]:
            total += 1
            if is_known(word, mode=mode):
                hits += 1
    return hits, total, hits / total if total else 0.0


def holdout_report(grouped, lines, mode, seed, fraction):
    eligible = sorted({
        folio for folio, fnum, _ in lines
        if section_of(fnum) != "other" and folio in grouped
    })
    rng = random.Random(seed)
    sample_size = max(1, round(len(eligible) * fraction))
    holdout = sorted(rng.sample(eligible, sample_size))
    rest = sorted(set(eligible) - set(holdout))

    train_hits, train_total, train_rate = interpretation_summary(grouped, rest, mode)
    hold_hits, hold_total, hold_rate = interpretation_summary(grouped, holdout, mode)

    return {
        "eligible": len(eligible),
        "holdout": holdout,
        "train": (train_hits, train_total, train_rate),
        "holdout_stats": (hold_hits, hold_total, hold_rate),
    }


def profile_counts(roots):
    counts = Counter()
    for root in roots:
        latin = root_latin(root)
        if latin == "odor":
            counts["odor"] += 1
        elif latin == "aureus":
            counts["aureus"] += 1
        elif root in PROPERTY_ROOTS:
            counts[PROPERTY_ROOTS[root]] += 1
        elif root in ENV_ROOTS:
            counts[ENV_ROOTS[root]] += 1
    return counts


def score_profile(counts, weights):
    return sum(counts[key] * weight for key, weight in weights.items())


def botanical_rankings(grouped, mode):
    herbal_folios = sorted(
        folio for folio, words in grouped.items()
        if any(1 <= fnum <= 66 for fnum, _ in words)
    )
    folio_counts = {
        folio: profile_counts(token_roots(words, mode))
        for folio, words in grouped.items()
        if folio in herbal_folios
    }

    rankings = {}
    for claimed_folio, profile in CLAIMED_PROFILES.items():
        scored = []
        for folio in herbal_folios:
            score = score_profile(folio_counts[folio], profile["weights"])
            scored.append((score, folio, folio_counts[folio]))
        scored.sort(key=lambda item: (-item[0], item[1]))
        rank = next((idx + 1 for idx, item in enumerate(scored) if item[1] == claimed_folio), None)
        rankings[claimed_folio] = {
            "label": profile["label"],
            "rank": rank,
            "total": len(scored),
            "top": scored[:10],
            "claimed_counts": folio_counts.get(claimed_folio, Counter()),
        }
    return rankings


def word_order_report(lines, mode):
    property_after_struct = 0
    property_total = 0
    env_edge = 0
    env_total = 0

    for _, _, text in lines:
        words = [clean_word(raw) for raw in re.split(r"[.,]", text) if clean_word(raw)]
        parsed = [(word, parse(word, mode=mode)[1]) for word in words]
        roots = [root for _, root in parsed]
        for idx, root in enumerate(roots):
            if root in PROPERTY_ROOTS:
                property_total += 1
                if idx > 0 and roots[idx - 1] in STRUCTURAL_ROOTS:
                    property_after_struct += 1
            if root in ENV_ROOTS:
                env_total += 1
                position = idx / max(len(roots) - 1, 1)
                if position <= 0.2 or position >= 0.8:
                    env_edge += 1

    prop_rate = property_after_struct / property_total if property_total else 0.0
    env_rate = env_edge / env_total if env_total else 0.0
    return property_after_struct, property_total, prop_rate, env_edge, env_total, env_rate


def print_rankings(rankings):
    for folio, data in rankings.items():
        print(f"\n{folio} claimed as {data['label']}")
        print(f"  rank: {data['rank']} / {data['total']}")
        print(f"  claimed counts: {dict(data['claimed_counts'])}")
        print("  top profile matches:")
        for score, top_folio, counts in data["top"]:
            marker = " <- claimed" if top_folio == folio else ""
            print(f"    {top_folio:5s} score={score:3d} counts={dict(counts)}{marker}")


def main():
    ap = argparse.ArgumentParser(description="Validate v21 claims after dictionary freeze")
    ap.add_argument("--input", required=True, help="Path to ZL_ivtff_2b.txt")
    ap.add_argument("--mode", choices=("strict", "legacy"), default="strict")
    ap.add_argument("--holdout-seed", type=int, default=20260630)
    ap.add_argument("--holdout-fraction", type=float, default=0.2)
    args = ap.parse_args()

    lines = load_corpus(args.input)
    grouped = folio_words(lines)

    print(f"Validation mode: {args.mode}")
    print(f"Lines loaded: {len(lines)}")
    print(f"Folios loaded: {len(grouped)}")

    holdout = holdout_report(grouped, lines, args.mode, args.holdout_seed, args.holdout_fraction)
    train_hits, train_total, train_rate = holdout["train"]
    hold_hits, hold_total, hold_rate = holdout["holdout_stats"]
    print("\nBlind folio holdout after dictionary freeze")
    print(f"  eligible folios: {holdout['eligible']}")
    print(f"  holdout folios ({len(holdout['holdout'])}): {', '.join(holdout['holdout'])}")
    print(f"  non-holdout: {train_hits}/{train_total} = {train_rate*100:.2f}%")
    print(f"  holdout:     {hold_hits}/{hold_total} = {hold_rate*100:.2f}%")

    print("\nBotanical identification whole-herbal ranking")
    print_rankings(botanical_rankings(grouped, args.mode))

    prop_hit, prop_total, prop_rate, env_hit, env_total, env_rate = word_order_report(lines, args.mode)
    print("\nLatin-like word-order heuristics")
    print(f"  property after structural token: {prop_hit}/{prop_total} = {prop_rate*100:.2f}%")
    print(f"  environmental token at line edge: {env_hit}/{env_total} = {env_rate*100:.2f}%")


if __name__ == "__main__":
    main()
