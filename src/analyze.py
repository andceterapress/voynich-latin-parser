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
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
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

PAPER_SECTION_LABELS = {
    "herbal": "Botanical",
    "biological": "Biological",
    "astronomical": "Astronomical",
    "pharma_roots": "Pharmaceutical (Roots)",
    "pharma_rx": "Pharmaceutical (Recipes)",
    "recipes": "Recipes",
}

PAPER_SECTION_ORDER = [
    "herbal",
    "biological",
    "astronomical",
    "pharma_roots",
    "pharma_rx",
    "recipes",
]


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


def find_default_corpus_path():
    """Find the ZL transcription when export mode is run without --input."""
    candidates = [
        Path("ZL_ivtff_2b.txt"),
        Path("../ZL_ivtff_2b.txt"),
        Path("work/ZL_ivtff_2b.txt"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def pct(count, total, ndigits=2):
    return round(count / total * 100, ndigits) if total else 0.0


def section_label(sec):
    return PAPER_SECTION_LABELS.get(sec, sec)


def token_records(lines):
    """Return one record per evaluated token using current strict parser output."""
    records = []
    token_index = 1
    for folio, fnum, text in lines:
        sec = section_of(fnum)
        if sec == "other":
            continue
        for raw in re.split(r"[.,]", text):
            token = clean_word(raw)
            if not token:
                continue
            prefix, root, suffix = parse(token, mode="strict")
            strict = bool(prefix or root or suffix)
            legacy = is_known(token, mode="legacy")
            latin_value = ROOTS[root][0] if root else ""
            interp = interpret(token, mode="strict") if strict else ""
            records.append({
                "token_index": token_index,
                "folio": folio,
                "section_key": sec,
                "section": section_label(sec),
                "eva_token": token,
                "prefix": prefix or "",
                "root": root or "",
                "suffix": suffix or "",
                "latin_value": latin_value,
                "interpretation": interp or "",
                "exploratory_recognized": "Yes" if legacy else "No",
                "strict_parsed": "Yes" if strict else "No",
                "failure_reason": "" if strict else "not_full_token_parse",
            })
            token_index += 1
    return records


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_corpus_performance_rows(records):
    total = len(records)
    exploratory = sum(1 for r in records if r["exploratory_recognized"] == "Yes")
    strict = sum(1 for r in records if r["strict_parsed"] == "Yes")
    unresolved = total - strict
    expected = (31007, 30590, 15848, 15159)
    actual = (total, exploratory, strict, unresolved)
    if actual != expected:
        raise ValueError(f"Unexpected v22 corpus counts: got {actual}, expected {expected}")
    return [
        {"metric": "Total tokens", "count": total, "percentage": f"{pct(total, total):.2f}"},
        {"metric": "Exploratory Recognition", "count": exploratory, "percentage": f"{pct(exploratory, total):.2f}"},
        {"metric": "Strict Full-Token Validation", "count": strict, "percentage": f"{pct(strict, total):.2f}"},
        {"metric": "Unresolved tokens", "count": unresolved, "percentage": f"{pct(unresolved, total):.2f}"},
    ]


def build_section_rows(records):
    rows = []
    by_section = defaultdict(list)
    for rec in records:
        by_section[rec["section_key"]].append(rec)
    for sec in PAPER_SECTION_ORDER:
        sec_records = by_section[sec]
        total = len(sec_records)
        strict = sum(1 for r in sec_records if r["strict_parsed"] == "Yes")
        rows.append({
            "section": section_label(sec),
            "total_tokens": total,
            "strict_parsed": strict,
            "strict_percentage": f"{pct(strict, total):.2f}",
        })
    return rows


def build_representative_rows(records):
    representatives = []
    used_tokens = set()
    columns = ["folio", "section", "eva_token", "prefix", "root", "suffix",
               "latin_value", "interpretation", "strict_parsed"]

    for sec in PAPER_SECTION_ORDER:
        candidates = [
            r for r in records
            if r["section_key"] == sec and r["strict_parsed"] == "Yes" and r["eva_token"] not in used_tokens
        ]
        candidates.sort(key=lambda r: (
            -int(bool(r["prefix"]) + bool(r["suffix"])),
            r["token_index"],
        ))
        for rec in candidates[:2]:
            representatives.append({k: rec[k] for k in columns})
            used_tokens.add(rec["eva_token"])

    return representatives[:15]


def build_lexical_stability_rows(records):
    root_counts = Counter()
    root_sections = defaultdict(set)
    for rec in records:
        root = rec["root"]
        if not root:
            continue
        root_counts[root] += 1
        root_sections[root].add(rec["section"])

    rows = []
    for root in sorted(root_counts, key=lambda r: (-root_counts[r], r)):
        sections = sorted(root_sections[root])
        latin_value = ROOTS[root][0]
        rows.append({
            "lexical_family": latin_value,
            "variant": root,
            "latin_value": latin_value,
            "interpretation": ROOTS[root][2],
            "occurrence_count": root_counts[root],
            "section_count": len(sections),
            "sections": "; ".join(sections),
            "context_specific_reassignment": "No",
        })
    return rows


def build_failure_rows(records, unique_only=False):
    rows = []
    seen = set()
    for rec in records:
        if rec["strict_parsed"] == "Yes":
            continue
        key = rec["eva_token"]
        if unique_only and key in seen:
            continue
        seen.add(key)
        rows.append({
            "folio": rec["folio"],
            "section": rec["section"],
            "eva_token": rec["eva_token"],
            "failure_reason": rec["failure_reason"],
        })
    return rows


def build_permutation_rows(all_words, n_trials=10000):
    observed, null_dist, z, p = permutation_test(all_words, n_trials=n_trials, mode="strict")
    mu = sum(null_dist) / len(null_dist)
    std = (sum((x - mu) ** 2 for x in null_dist) / len(null_dist)) ** 0.5
    trials_ge = sum(1 for x in null_dist if x >= observed)
    empirical = "<0.0001" if trials_ge == 0 and n_trials == 10000 else f"{p:.6f}"
    return [
        {"metric": "Permutation trials", "value": str(n_trials)},
        {"metric": "Null mean (%)", "value": f"{mu * 100:.3f}"},
        {"metric": "Null standard deviation (%p)", "value": f"{std * 100:.3f}"},
        {"metric": "Maximum null performance (%)", "value": f"{max(null_dist) * 100:.3f}"},
        {"metric": "Observed strict parsing (%)", "value": f"{observed * 100:.2f}"},
        {"metric": "z-score", "value": f"{z:.2f}σ"},
        {"metric": "Trials >= observed", "value": f"{trials_ge} / {n_trials}"},
        {"metric": "Empirical p-value", "value": empirical},
    ], {
        "trials": n_trials,
        "null_mean_percent": round(mu * 100, 3),
        "null_std_percentage_points": round(std * 100, 3),
        "null_max_percent": round(max(null_dist) * 100, 3),
        "observed_percent": round(observed * 100, 2),
        "z_score": round(z, 2),
        "trials_greater_equal_observed": trials_ge,
        "empirical_p": empirical,
    }


def strict_count_with_roots(words, roots):
    """Count strict full-token parses with a supplied temporary root inventory."""
    return sum(1 for word in words if is_strictly_parsed(word, roots))


def one_char_root_ablation(input_path):
    """Run diagnostic ablation removing one-character ROOT entries only."""
    lines = load_corpus(input_path)
    all_words = list(corpus_words(lines))
    total = len(all_words)
    baseline_count = strict_count_with_roots(all_words, set(ROOTS.keys()))

    removed_roots = sorted(root for root in ROOTS if len(root) == 1)
    ablated_roots = {root for root in ROOTS if len(root) != 1}
    ablated_count = strict_count_with_roots(all_words, ablated_roots)

    baseline_pct = pct(baseline_count, total)
    ablated_pct = pct(ablated_count, total)
    absolute_drop = round(baseline_pct - ablated_pct, 2)
    relative_drop = round((baseline_count - ablated_count) / baseline_count * 100, 2) if baseline_count else 0.0

    expected = (31007, 15848, 51.11)
    actual = (total, baseline_count, baseline_pct)
    if actual != expected:
        raise ValueError(f"Unexpected baseline strict result: got {actual}, expected {expected}")

    rows = [
        {"metric": "Total tokens", "value": str(total)},
        {"metric": "Baseline strict parsed", "value": str(baseline_count)},
        {"metric": "Baseline strict percentage", "value": f"{baseline_pct:.2f}"},
        {"metric": "Ablated strict parsed", "value": str(ablated_count)},
        {"metric": "Ablated strict percentage", "value": f"{ablated_pct:.2f}"},
        {"metric": "Absolute percentage-point drop", "value": f"{absolute_drop:.2f}"},
        {"metric": "Relative drop (%)", "value": f"{relative_drop:.2f}"},
        {"metric": "Removed one-character roots", "value": "; ".join(removed_roots)},
    ]

    tables_dir = Path("paper/tables")
    supp_dir = Path("paper/supplementary")
    write_csv(tables_dir / "Table7_OneCharacterRootAblation.csv", ["metric", "value"], rows)

    supp_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "parser_version": "v22",
        "ablation": "one_character_roots_removed",
        "total_tokens": total,
        "baseline": {
            "strict_count": baseline_count,
            "strict_percentage": baseline_pct,
        },
        "ablated": {
            "strict_count": ablated_count,
            "strict_percentage": ablated_pct,
        },
        "absolute_percentage_point_drop": absolute_drop,
        "relative_drop_percent": relative_drop,
        "removed_one_character_roots": removed_roots,
    }
    with open(supp_dir / "Supplementary_S5_OneCharacterRootAblation.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("One-character ROOT ablation")
    print(f"  total_tokens: {total}")
    print(f"  baseline_strict_count: {baseline_count}")
    print(f"  baseline_strict_percentage: {baseline_pct:.2f}%")
    print(f"  ablated_strict_count: {ablated_count}")
    print(f"  ablated_strict_percentage: {ablated_pct:.2f}%")
    print(f"  absolute_percentage_point_drop: {absolute_drop:.2f}")
    print(f"  relative_drop_percent: {relative_drop:.2f}%")
    print(f"  removed_one_char_roots: {', '.join(removed_roots)}")
    print("  wrote: paper/tables/Table7_OneCharacterRootAblation.csv")
    print("  wrote: paper/supplementary/Supplementary_S5_OneCharacterRootAblation.json")


def short_root_ablation(input_path):
    """Run diagnostic ablation removing one- and two-character ROOT entries."""
    lines = load_corpus(input_path)
    all_words = list(corpus_words(lines))
    total = len(all_words)

    all_roots = set(ROOTS.keys())
    removed_one_char = sorted(root for root in ROOTS if len(root) == 1)
    removed_two_char = sorted(root for root in ROOTS if len(root) == 2)
    one_char_roots = {root for root in ROOTS if len(root) != 1}
    one_two_char_roots = {root for root in ROOTS if len(root) > 2}

    baseline_count = strict_count_with_roots(all_words, all_roots)
    one_char_count = strict_count_with_roots(all_words, one_char_roots)
    one_two_char_count = strict_count_with_roots(all_words, one_two_char_roots)

    baseline_pct = pct(baseline_count, total)
    one_char_pct = pct(one_char_count, total)
    one_two_char_pct = pct(one_two_char_count, total)
    absolute_drop = round(baseline_pct - one_two_char_pct, 2)
    relative_drop = round((baseline_count - one_two_char_count) / baseline_count * 100, 2) if baseline_count else 0.0

    expected = (31007, 15848, 51.11, 12038, 38.82)
    actual = (total, baseline_count, baseline_pct, one_char_count, one_char_pct)
    if actual != expected:
        raise ValueError(f"Unexpected ablation baseline: got {actual}, expected {expected}")

    rows = [
        {"metric": "Total tokens", "value": str(total)},
        {"metric": "Baseline strict parsed", "value": str(baseline_count)},
        {"metric": "Baseline strict %", "value": f"{baseline_pct:.2f}"},
        {"metric": "One-character ablation parsed", "value": str(one_char_count)},
        {"metric": "One-character ablation %", "value": f"{one_char_pct:.2f}"},
        {"metric": "One-two-character ablation parsed", "value": str(one_two_char_count)},
        {"metric": "One-two-character ablation %", "value": f"{one_two_char_pct:.2f}"},
        {"metric": "Absolute percentage-point drop", "value": f"{absolute_drop:.2f}"},
        {"metric": "Relative drop %", "value": f"{relative_drop:.2f}"},
        {"metric": "Removed one-character roots", "value": "; ".join(removed_one_char)},
        {"metric": "Removed two-character roots", "value": "; ".join(removed_two_char)},
    ]

    tables_dir = Path("paper/tables")
    supp_dir = Path("paper/supplementary")
    write_csv(tables_dir / "Table8_ShortRootAblation.csv", ["metric", "value"], rows)

    supp_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "parser_version": "v22",
        "ablation": "one_two_character_roots_removed",
        "baseline": {
            "strict_count": baseline_count,
            "strict_percentage": baseline_pct,
        },
        "one_character_ablation": {
            "strict_count": one_char_count,
            "strict_percentage": one_char_pct,
        },
        "one_two_character_ablation": {
            "strict_count": one_two_char_count,
            "strict_percentage": one_two_char_pct,
            "absolute_percentage_point_drop": absolute_drop,
            "relative_drop_percent": relative_drop,
        },
        "removed_one_character_roots": removed_one_char,
        "removed_two_character_roots": removed_two_char,
    }
    with open(supp_dir / "Supplementary_S6_ShortRootAblation.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("Short ROOT ablation (length <= 2 removed)")
    print(f"  total_tokens: {total}")
    print(f"  baseline_strict_count: {baseline_count}")
    print(f"  baseline_strict_percentage: {baseline_pct:.2f}%")
    print(f"  one_char_removed_count: {one_char_count}")
    print(f"  one_char_removed_percentage: {one_char_pct:.2f}%")
    print(f"  one_two_char_removed_count: {one_two_char_count}")
    print(f"  one_two_char_removed_percentage: {one_two_char_pct:.2f}%")
    print(f"  absolute_drop_vs_baseline: {absolute_drop:.2f}")
    print(f"  relative_drop_vs_baseline: {relative_drop:.2f}%")
    print(f"  removed_one_char_roots: {', '.join(removed_one_char)}")
    print(f"  removed_two_char_roots: {', '.join(removed_two_char)}")
    print("  wrote: paper/tables/Table8_ShortRootAblation.csv")
    print("  wrote: paper/supplementary/Supplementary_S6_ShortRootAblation.json")


def export_paper_data(input_path):
    """Generate reproducible paper tables and supplementary data."""
    lines = load_corpus(input_path)
    records = token_records(lines)
    all_words = [r["eva_token"] for r in records]
    tables_dir = Path("paper/tables")
    supp_dir = Path("paper/supplementary")

    corpus_rows = build_corpus_performance_rows(records)
    section_rows = build_section_rows(records)
    permutation_rows, permutation_json = build_permutation_rows(all_words, n_trials=10000)
    representative_rows = build_representative_rows(records)
    lexical_rows = build_lexical_stability_rows(records)
    failure_rows_unique = build_failure_rows(records, unique_only=True)
    failure_rows_all = build_failure_rows(records, unique_only=False)

    write_csv(tables_dir / "Table1_CorpusPerformance.csv",
              ["metric", "count", "percentage"], corpus_rows)
    write_csv(tables_dir / "Table2_SectionConsistency.csv",
              ["section", "total_tokens", "strict_parsed", "strict_percentage"], section_rows)
    write_csv(tables_dir / "Table3_PermutationStatistics.csv",
              ["metric", "value"], permutation_rows)
    write_csv(tables_dir / "Table4_RepresentativeParsing.csv",
              ["folio", "section", "eva_token", "prefix", "root", "suffix",
               "latin_value", "interpretation", "strict_parsed"], representative_rows)
    write_csv(tables_dir / "Table5_LexicalStability.csv",
              ["lexical_family", "variant", "latin_value", "interpretation", "occurrence_count",
               "section_count", "sections", "context_specific_reassignment"], lexical_rows[:15])
    write_csv(tables_dir / "Table6_FailureCases.csv",
              ["folio", "section", "eva_token", "failure_reason"], failure_rows_unique[:25])

    write_csv(supp_dir / "Supplementary_S1_SectionStatistics.csv",
              ["section", "total_tokens", "strict_parsed", "strict_percentage"], section_rows)
    write_csv(supp_dir / "Supplementary_S2_FullParserOutput.csv",
              ["token_index", "folio", "section", "eva_token", "prefix", "root", "suffix",
               "latin_value", "interpretation", "exploratory_recognized",
               "strict_parsed", "failure_reason"], [
                  {k: r[k] for k in ["token_index", "folio", "section", "eva_token", "prefix",
                                      "root", "suffix", "latin_value", "interpretation",
                                      "exploratory_recognized", "strict_parsed", "failure_reason"]}
                  for r in records
              ])
    write_csv(supp_dir / "Supplementary_S3_LexicalStability.csv",
              ["lexical_family", "variant", "latin_value", "interpretation", "occurrence_count",
               "section_count", "sections", "context_specific_reassignment"], lexical_rows)
    write_csv(supp_dir / "Supplementary_S4_FailureCases.csv",
              ["folio", "section", "eva_token", "failure_reason"], failure_rows_all)

    results = {
        "parser_version": "v22",
        "total_tokens": len(records),
        "exploratory_recognition": {
            "count": int(corpus_rows[1]["count"]),
            "percentage": float(corpus_rows[1]["percentage"]),
        },
        "strict_full_token_validation": {
            "count": int(corpus_rows[2]["count"]),
            "percentage": float(corpus_rows[2]["percentage"]),
        },
        "permutation_test": permutation_json,
        "section_statistics": [
            {
                "section": r["section"],
                "total_tokens": r["total_tokens"],
                "strict_parsed": r["strict_parsed"],
                "strict_percentage": float(r["strict_percentage"]),
            }
            for r in section_rows
        ],
    }
    supp_dir.mkdir(parents=True, exist_ok=True)
    with open(supp_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open(supp_dir / "README.md", "w", encoding="utf-8") as f:
        f.write("""# Supplementary Parser Outputs

Generated by:

```bash
python src/analyze.py --export-paper-data
```

Files:

- `Supplementary_S1_SectionStatistics.csv`: strict parsing counts by manuscript section.
- `Supplementary_S2_FullParserOutput.csv`: token-level strict and exploratory parser output for all evaluated tokens.
- `Supplementary_S3_LexicalStability.csv`: fixed lexical values and section reuse for each parsed root.
- `Supplementary_S4_FailureCases.csv`: all tokens unresolved by strict full-token validation.
- `results.json`: machine-readable summary of v22 corpus and strict permutation results.
""")

    print("Exported paper data:")
    for path in [
        tables_dir / "Table1_CorpusPerformance.csv",
        tables_dir / "Table2_SectionConsistency.csv",
        tables_dir / "Table3_PermutationStatistics.csv",
        tables_dir / "Table4_RepresentativeParsing.csv",
        tables_dir / "Table5_LexicalStability.csv",
        tables_dir / "Table6_FailureCases.csv",
        supp_dir / "Supplementary_S1_SectionStatistics.csv",
        supp_dir / "Supplementary_S2_FullParserOutput.csv",
        supp_dir / "Supplementary_S3_LexicalStability.csv",
        supp_dir / "Supplementary_S4_FailureCases.csv",
        supp_dir / "results.json",
        supp_dir / "README.md",
    ]:
        print(f"  {path}")


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
    ap.add_argument("--input", help="Path to ZL_ivtff_2b.txt")
    ap.add_argument("--folio", help="Translate a single folio (e.g. f112r)")
    ap.add_argument("--permutation", type=int, metavar="N",
                    help="Run permutation test with N trials (e.g. 1000)")
    ap.add_argument("--section", help="Show stats for one section only")
    ap.add_argument("--mode", choices=("strict", "legacy"), default="strict",
                    help="strict consumes the full word; legacy reproduces substring fallback")
    ap.add_argument("--compare-modes", action="store_true",
                    help="print strict and legacy rates side by side")
    ap.add_argument("--export-paper-data", action="store_true",
                    help="export reproducible paper tables and supplementary data")
    ap.add_argument("--ablate-one-char-roots", action="store_true",
                    help="diagnose strict coverage after temporarily removing one-character ROOT entries")
    ap.add_argument("--ablate-short-roots", action="store_true",
                    help="diagnose strict coverage after temporarily removing one- and two-character ROOT entries")
    args = ap.parse_args()

    if args.ablate_short_roots:
        input_path = args.input or find_default_corpus_path()
        if not input_path:
            ap.error("--ablate-short-roots requires --input or a local ZL_ivtff_2b.txt file")
        short_root_ablation(input_path)
        return

    if args.ablate_one_char_roots:
        input_path = args.input or find_default_corpus_path()
        if not input_path:
            ap.error("--ablate-one-char-roots requires --input or a local ZL_ivtff_2b.txt file")
        one_char_root_ablation(input_path)
        return

    if args.export_paper_data:
        input_path = args.input or find_default_corpus_path()
        if not input_path:
            ap.error("--export-paper-data requires --input or a local ZL_ivtff_2b.txt file")
        export_paper_data(input_path)
        return

    if not args.input:
        ap.error("--input is required unless an export or ablation mode is used")

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
