# Voynich Latin Parser

This repository accompanies the manuscript:

**A Reproducible Computational Framework for Corpus-Wide Morphological Evaluation of the Voynich Manuscript**

## Release

This release corresponds to parser version v22 and the manuscript version prepared for Zenodo archival.

## Repository Structure

- `paper/` - manuscript files
- `parser/` - parser implementation corresponding to parser version v22
- `data/` - notes on lexical resources and evaluation input data
- `results/` - parser outputs and evaluation results
- `supplementary/` - supplementary tables cited in the manuscript
- `archive/` - older drafts or non-release materials, if present

Additional folders:

- `examples/` - small parser demonstration script
- `scripts/` - validation helper scripts
- `tests/` - parser unit tests

## Reproducibility

The Zenodo archive for this GitHub release should be treated as the fixed reference snapshot for the manuscript.

The GitHub repository may continue to contain later development versions after this release.

## Parser Version

All results reported in the manuscript correspond to parser version v22.

The parser version is recorded in `parser/VERSION.txt`.

## How To Reproduce

The Zandbergen-Landini EVA transcription file `ZL_ivtff_2b.txt` is not included in this repository because it has separate provenance. Place a local copy of `ZL_ivtff_2b.txt` in the repository root, or pass its path with `--input`.

Run the parser and validation scripts with Python 3:

```bash
python tests/test_parser.py
python parser/analyze.py --input ZL_ivtff_2b.txt --compare-modes
python parser/analyze.py --input ZL_ivtff_2b.txt --mode strict --permutation 10000
python parser/analyze.py --input ZL_ivtff_2b.txt --ablate-one-char-roots
python parser/analyze.py --input ZL_ivtff_2b.txt --ablate-short-roots
python parser/analyze.py --input ZL_ivtff_2b.txt --export-paper-data
```

The archived release includes exported results for inspection and independent verification:

- `results/results.json`
- `results/tables/`
- `supplementary/`

## Main Reported Values

All values below are exported from parser version v22:

- Total evaluated tokens: 31,007
- Exploratory Recognition Mode: 30,590 / 31,007 = 98.66%
- Strict Full-Token Validation Mode: 15,848 / 31,007 = 51.11%
- One-character root ablation: 12,038 / 31,007 = 38.82%
- One- and two-character root ablation: 6,317 / 31,007 = 20.37%

Strict Full-Token Validation Mode is the primary validation criterion. The older 98.7% figure refers to exploratory legacy recognition, not full-token parsing.

## Citation

If you use this repository, please cite the Zenodo DOI associated with the release.

DOI: to be added after Zenodo archives the GitHub release.
