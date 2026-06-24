# Voynich Manuscript — v21 Parser & Dictionary

**Hypothesis:** The Voynich Manuscript (Beinecke MS 408, ca. 1404–1438) is a compressed Latin botanical-medical reference text from the Padua region, encoding plant anatomy and pharmaceutical prescriptions through abbreviated Latin roots with preserved grammar suffixes.

**Interpretation rate (v21):** 98.7% of 31,007 tokens across all six manuscript sections  
**Statistical validation:** Permutation test z = 7.3σ, p < 0.001 (n = 1,000 random root sets)  
**External cross-validation:** Marci alphabet table (f1r multispectral imaging, Davis 2024)

> ⚠️ This is a research hypothesis, not a confirmed decipherment. All code and data are provided for independent verification.

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/voynich-v21.git
cd voynich-v21

# No dependencies beyond Python 3.8+
python examples/translate_sample.py

# Run unit tests
python tests/test_parser.py

# Full corpus analysis (requires ZL transcription file)
python src/analyze.py --input ZL_ivtff_2b.txt

# Translate a single folio
python src/analyze.py --input ZL_ivtff_2b.txt --folio f112r

# Permutation test (takes ~30 seconds)
python src/analyze.py --input ZL_ivtff_2b.txt --permutation 1000
```

---

## Corpus data

The transcription file `ZL_ivtff_2b.txt` (Zandbergen-Landini, 2022-12-25) is **not included** in this repository due to its separate provenance.

Download from: [voynich.nu](https://www.voynich.nu/transcr.html) — look for the IVTFF format file.

---

## Repository structure

```
voynich-v21/
├── src/
│   ├── parser.py        # v21 root dictionary + EVA parser
│   └── analyze.py       # corpus-level statistics and permutation test
├── examples/
│   └── translate_sample.py   # benchmark translation examples
├── tests/
│   └── test_parser.py   # unit tests (parser + Marci cross-validation)
├── docs/
│   └── v21_summary.md   # full research summary (Korean + English)
└── README.md
```

---

## The v21 dictionary

The parser maps EVA (Extended Voynich Alphabet) strings to Latin botanical terms via three mechanisms:

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

## Word-order rules (v20, statistically validated)

Three rules were inductively derived from the plant section (f1–f66) and validated across all sections:

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

### Permutation test

To rule out circular reasoning ("any root set achieves high rates"), 1,000 random root sets of the same size were tested:

| | v21 | Random mean | Random max |
|---|---|---|---|
| Full parser | **98.7%** | 33.5% | 79.8% |
| Roots only (no affixes) | **98.6%** | 10.6% | — |
| z-score | **7.3σ** | — | — |
| p-value | **< 0.001** | — | — |

Random trials reaching v21 level: **0 / 1,000**

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
| **v21** | **98.7%** | `air`/`aiir` bug fix + single-char function words + Marci cross-validation |

---

## Section results (v21)

| Section | Folios | Tokens | Rate |
|---------|--------|--------|------|
| Herbal | f1–f66 | 11,080 | 97.9% |
| Astronomical | f70v–f73v | 283 | 98.2% |
| Biological | f74–f84 | 6,872 | 99.1% |
| Pharma (roots) | f87–f96v | 984 | 99.3% |
| Pharma (Rx) | f99–f102 | 906 | 99.2% |
| Recipes | f103–f116 | 10,882 | 99.1% |
| **Total** | | **31,007** | **98.7%** |

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
