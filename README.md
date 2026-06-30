# Voynich Manuscript — v22 Strict Validation Parser

**Hypothesis:** The Voynich Manuscript (Beinecke MS 408, ca. 1404–1438) is a compressed Latin botanical-medical reference text from the Padua region, encoding plant anatomy and pharmaceutical prescriptions through abbreviated Latin roots with preserved grammar suffixes.

**Strict Full-Token Validation Mode:** 51.11% of 31,007 tokens across all six manuscript sections  
**Exploratory Recognition Mode:** 98.66% of 31,007 tokens, reproducing the original v21 legacy claim  
**External cross-validation:** Marci alphabet table (f1r multispectral imaging, Davis 2024)

> ⚠️ This is a research hypothesis, not a confirmed decipherment. All code and data are provided for independent verification.
>
> **Important validation update:** the original v21 98.7% figure counts exploratory partial substring matches as interpreted. In the default Strict Full-Token Validation Mode introduced here, an EVA token must be fully consumed as `optional prefix + root + optional suffix`. Under that primary validation criterion, corpus coverage is 51.11%.

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/voynich-v21.git
cd voynich-v21

# No dependencies beyond Python 3.8+
python examples/translate_sample.py

# Run unit tests
python tests/test_parser.py

# Full corpus analysis in strict mode (requires ZL transcription file)
python src/analyze.py --input ZL_ivtff_2b.txt

# Compare Strict Full-Token Validation Mode with Exploratory Recognition Mode
python src/analyze.py --input ZL_ivtff_2b.txt --compare-modes

# Translate a single folio
python src/analyze.py --input ZL_ivtff_2b.txt --folio f112r

# Reproduce the original v21 exploratory substring-based rate
python src/analyze.py --input ZL_ivtff_2b.txt --mode legacy

# Run validation checks after dictionary freeze
python scripts/validate_claims.py --input ZL_ivtff_2b.txt --mode strict

# Official strict permutation test
python src/analyze.py --input ZL_ivtff_2b.txt --mode strict --permutation 10000

# Export reproducible paper tables and supplementary files
python src/analyze.py --export-paper-data
```

---

## Corpus data

The transcription file `ZL_ivtff_2b.txt` (Zandbergen-Landini, 2022-12-25) is **not included** in this repository due to its separate provenance.

Download from: [voynich.nu](https://www.voynich.nu/transcr.html) — look for the IVTFF format file.

---

## Repository structure

```
voynich-latin-parser/
├── src/
│   ├── parser.py        # root dictionary + strict/legacy EVA parser
│   └── analyze.py       # corpus-level statistics and permutation test
├── examples/
│   └── translate_sample.py   # benchmark translation examples
├── scripts/
│   └── validate_claims.py    # blind holdout + botanical ranking checks
├── paper/
│   ├── tables/               # reproducible paper tables
│   └── supplementary/        # token-level supplementary parser outputs
├── tests/
│   └── test_parser.py   # unit tests (parser + Marci cross-validation)
├── docs/
│   └── v21_summary.md   # full research summary (Korean + English)
└── README.md
```

---

## The v21 dictionary

The parser maps EVA (Extended Voynich Alphabet) strings to Latin botanical terms via three mechanisms. Two parse modes are available:

- `strict` (default): Strict Full-Token Validation Mode. A token must be fully consumed as `optional prefix + root + optional suffix`.
- `legacy`: Exploratory Recognition Mode. Reproduces the original v21 behavior by allowing a root to match any substring inside the remaining token.

Strict Full-Token Validation Mode is the primary validation criterion. Exploratory Recognition Mode is retained only for reproducing the originally published 98.7% result.

### Experimental compound candidates

Compound morpheme rules such as `ok/ot/ch/sh + root` are promising experimental candidates because many currently unparsed tokens appear to contain recurring structural pieces. They are **not** merged into the main v22 parser yet. Broad two-root compounding is intentionally not adopted here because it risks reintroducing overfitting and inflating recognition rates.

### 1. Root matching (68 roots)

| EVA | Latin | Meaning | Source |
|-----|-------|---------|--------|
| `chol` / `ch` | cortex | bark | Mondino Anathomia (1316) |
| `daiin` / `dar` | duramen | heartwood | Mondino |
| `aiin` | annulus | growth ring | Mondino |
| `sheol` / `sh` | suber | cork | Mondino |
| `ol` | lignum | wood | Mondino |
| `al` | alburnum | sapwood | Mondino |
| `ar` | radius | medullary ray | Mondino |
| `dal` / `dol` | medulla | pith | Mondino |
| `chy` | chylos (χυλός) | juice/chyle | Greek botanical tradition |
| `cthor` | phlegma | mucilage | Regimen Sanitatis |
| `shey` | humidus | moist/aquatic | Tacuinum Sanitatis |
| `am` / `om` | [verb] | [process] | prescription terminal |

See `src/parser.py` for the complete dictionary.

### 2. Prefix system (6 prefixes, priority order)

| Prefix | Latin | Meaning |
|--------|-------|---------|
| `qo-` | quod/de | of/from |
| `op-` | contra | against |
| `r-` | re- | reverse |
| `l-` | il- | article |
| `p-` | pro | for |
| `y-` | — | demonstrative |

### 3. Suffix system (26 suffixes)

| Suffix | Meaning |
|--------|---------|
| `-dy` | de (of) |
| `-edy` | per (through) |
| `-am` / `-om` | [process verb] — 70% line-final |
| `-y` | adjective |
| `-iin` | ring-type |
| `-eol` | + lignum |
| `-eor` | + aureus (golden) |

---

## Word-order rules

The original paper proposed three word-order rules derived from the plant section (f1–f66). In this validation branch, independent checks are reported separately from the original claim:

**Rule 1 — Optional verb-initial marker (3.8% of prescription lines)**  
`k [BARK] [WOOD] ... am`  
`k` (coquitur = decoction) may front the line; `am` alone suffices for closure.

**Rule 2 — Post-nominal property placement (93.1% compliance)**  
`[BARK/WOOD]+ PROP`  
Property terms follow the structural terms they modify.  
Exception A (75%): sentence-initial proposition ("mucilaginous. The bark…")

**Rule 3 — Environmental term placement (82.3% compliance)**  
Environmental qualifiers appear at sentence edges only:  
- *humidus* (shey): avg position 0.38 → introductory  
- *umbrosus* (chom): avg position 0.84 → conclusory, before `am`  

---

## Benchmark translations

### f112r.10 — simplest prescription (100% known)
```
EVA:   dair . al . chedy . qodain . dam
Parse: heartwood | sapwood | bark(through) | of-heartwood | [process]
Trans: Heartwood and sapwood, through bark, of heartwood — process.
```

### f5v.2 — Malva (mallow), botanically validated
```
EVA:   dchol . chol . otaiin . dain . cthor . chots . ychopordg
Parse: bark  | bark | surface-ring | heartwood | mucilage | bark | [bark]
Trans: Bark and bark's surface ring, heartwood: mucilaginous.
Note:  Mallow (Malva) is genuinely mucilaginous — independent botanical confirmation.
```

### f3r.15 — dual environmental terms (word-order rule 3)
```
EVA:   chol . shor . shey . chor . dor . chols . chom . am
Parse: bark | cork | [moist] | bark | scent | bark | [shaded] | [process]
Trans: Bark, cork — moist bark, fragrant bark. Shaded. [Process].
Note:  shey at position 0.29 (front) + chom at 0.86 (back) — both obey Rule 3.
```

---

## Statistical validation

### Mode comparison

Run:

```bash
python src/analyze.py --input ZL_ivtff_2b.txt --compare-modes
```

Result:

| Mode | Hits | Tokens | Rate | Meaning |
|---|---:|---:|---:|---|
| Strict Full-Token Validation | 15,848 | 31,007 | 51.11% | Primary validation criterion |
| Exploratory Recognition | 30,590 | 31,007 | 98.66% | Original v21 substring fallback behavior |

### Permutation test

The original v21 permutation test is reproducible in Exploratory Recognition Mode. In v22, the official permutation test uses the same Strict Full-Token Validation criterion as the production strict parser.

Run:

```bash
python src/analyze.py --input ZL_ivtff_2b.txt --mode strict --permutation 10000
```

Result:

| Metric | Strict permutation result |
|---|---:|
| Random trials | 10,000 |
| Observed strict rate | 51.111% |
| Null mean | 2.112% |
| Null std | 1.629 percentage points |
| Null max | 15.900% |
| z-score | 30.07σ |
| Trials >= observed | 0 / 10,000 |
| Empirical p | < 0.0001 |

The older 98.7% figure should therefore be described as exploratory/legacy recognition coverage, not full-token parsing.

### Reproducible paper data export

Run:

```bash
python src/analyze.py --export-paper-data
```

This regenerates the following files from the current v22 parser and the ZL transcription:

| File | Description |
|---|---|
| `paper/tables/Table1_CorpusPerformance.csv` | Total tokens, exploratory recognition, strict validation, and unresolved-token counts |
| `paper/tables/Table2_SectionConsistency.csv` | Section-level strict parsing counts and percentages |
| `paper/tables/Table3_PermutationStatistics.csv` | Official 10,000-trial strict permutation statistics |
| `paper/tables/Table4_RepresentativeParsing.csv` | Deterministically selected successful strict parses from actual parser output |
| `paper/tables/Table5_LexicalStability.csv` | Representative fixed root-to-Latin lexical assignments |
| `paper/tables/Table6_FailureCases.csv` | Representative unresolved strict-validation tokens |
| `paper/supplementary/Supplementary_S1_SectionStatistics.csv` | Full section statistics |
| `paper/supplementary/Supplementary_S2_FullParserOutput.csv` | Token-level parser output for all 31,007 evaluated tokens |
| `paper/supplementary/Supplementary_S3_LexicalStability.csv` | Full lexical stability table |
| `paper/supplementary/Supplementary_S4_FailureCases.csv` | All strict-validation failure cases |
| `paper/supplementary/results.json` | Machine-readable v22 summary and permutation result |
| `paper/supplementary/README.md` | Supplementary file guide |

### External cross-validation: Marci alphabet table

Lisa Fagin Davis (2024) published multispectral images of folio f1r revealing a 17th-century decoding attempt by Johannes Marcus Marci (manuscript owner 1662–1665). His Roman-to-Voynich glyph table shows:

- Direct correspondences d→d, s→s, t→t, r→r, k→k, l→l align with v21 function words
- c→sh correspondence supports sh = *suber* (initial /s/ phoneme)
- Marci's failure confirms the encoding is **not** a simple substitution cipher — consistent with our word-level abbreviation hypothesis

---

## Version history

| Version | Rate | Key addition |
|---------|------|-------------|
| v7 | 26.0% | Basic root set |
| v11 | 53.9% | 2-character roots |
| v14 | 65.9% | 4-level recursive parser |
| v19 | 82.1% | Emphasis prefix `e-` |
| v20 | 95.6% | Word-order rules + ZL transcription |
| v21 | 98.7% legacy | `air`/`aiir` bug fix + single-char function words + Marci cross-validation |
| **v22 strict validation** | **51.11% strict / 98.66% legacy** | Removes substring fallback from default parser; adds validation scripts |

---

## Section results (strict mode)

| Section | Folios | Tokens | Rate |
|---------|--------|--------|------|
| Herbal | f1–f66 | 11,080 | 48.4% |
| Astronomical | f70v–f73v | 283 | 49.1% |
| Biological | f74–f84 | 6,872 | 57.7% |
| Pharma (roots) | f87–f96v | 984 | 45.7% |
| Pharma (Rx) | f99–f102 | 906 | 57.8% |
| Recipes | f103–f116 | 10,882 | 49.7% |
| **Total** | | **31,007** | **51.11%** |

---

## Primary references

- Mondino dei Luzzi, *Anathomia* (1316)
- Tacuinum Sanitatis (1380–1450, North Italy)
- Carrara Herbal (Padua dialect, 1390–1405)
- Fasciculus Medicinae (Ketham, 1491)
- Davis, L.F. (2024). Multispectral Imaging and the Voynich Manuscript. *Manuscript Road Trip* blog.
- Montemurro, M.A. & Zanette, D.H. (2013). Keywords and Co-Occurrence Patterns in the Voynich Manuscript. *PLOS ONE* 8(6).
- Bowern, C. & Lindemann, L. (2021). The Linguistics of the Voynich Manuscript. *Annual Review of Linguistics* 7:285–308.
- Zandbergen, R. (2022). ZL Interlinear File (ivtff_2b format). [voynich.nu](https://voynich.nu)

---

## How to contribute

Critical feedback is especially welcome. The most valuable contributions would be:

1. **Refutation attempts** — show that the root-to-meaning mappings are incorrect
2. **Entropy analysis** — measure entropy at the root-sequence level and compare to medieval Latin
3. **Independent botanical validation** — verify (or disprove) the f5v Malva identification
4. **Yale original image review** — check word boundaries on high-error pages (e.g. f7r)

Please open a GitHub Issue or post to [voynich.ninja](https://voynich.ninja) with any findings.

---

## License

MIT — use freely, cite the source.
