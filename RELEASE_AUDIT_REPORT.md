# Release Audit Report

Release target: `v22-paper`

Audit date: 2026-07-01

## Files Included In `paper/`

- `paper/Voynich_Master_Manuscript_v2_CAMERA_READY.pdf`
- `paper/Voynich_Master_Manuscript_v2_final.docx`

Notes:

- The previous tracked manuscript file was moved to `archive/paper_drafts/`.
- No older tracked draft files remain in release-facing `paper/`.

## Files Included In `parser/`

- `parser/VERSION.txt`
- `parser/analyze.py`
- `parser/parser.py`

## Files Included In `data/`

- `data/README.md`

Notes:

- `ZL_ivtff_2b.txt` is not included because it has separate provenance.
- The lexical resources for parser version v22 are embedded in `parser/parser.py` as `ROOTS`, `PREFIXES`, and `SUFFIXES`.

## Files Included In `results/`

- `results/results.json`
- `results/tables/Table1_CorpusPerformance.csv`
- `results/tables/Table2_SectionConsistency.csv`
- `results/tables/Table3_PermutationStatistics.csv`
- `results/tables/Table4_RepresentativeParsing.csv`
- `results/tables/Table5_LexicalStability.csv`
- `results/tables/Table6_FailureCases.csv`
- `results/tables/Table7_OneCharacterRootAblation.csv`
- `results/tables/Table8_ShortRootAblation.csv`

## Files Included In `supplementary/`

- `supplementary/README.md`
- `supplementary/Supplementary_Table_S1_Section_Statistics.csv`
- `supplementary/Supplementary_Table_S2_Full_Parser_Output.csv`
- `supplementary/Supplementary_Table_S3_Lexical_Stability.csv`
- `supplementary/Supplementary_Table_S4_Failure_Cases.csv`
- `supplementary/Supplementary_S5_OneCharacterRootAblation.json`
- `supplementary/Supplementary_S6_ShortRootAblation.json`

## Missing Supplementary Files

None identified for Supplementary Tables S1, S2, and S3.

## Parser Version

Parser version v22 is identifiable in:

- `parser/VERSION.txt`
- `results/results.json`
- `supplementary/Supplementary_S5_OneCharacterRootAblation.json`
- `supplementary/Supplementary_S6_ShortRootAblation.json`

## Release Documentation Checks

- `README.md` updated: yes
- `RELEASE_NOTES_v22-paper.md` exists: yes
- `CITATION.cff` exists: yes
- `LICENSE` exists: yes

## Draft Or Non-Release Files

- Older background summary notes were moved to `archive/background_notes/docs/`.
- Local non-release cache/system files are excluded by `.gitignore`; ignored caches may be recreated by tests.
- No tracked draft files remain in `paper/`, `parser/`, `data/`, `results/`, or `supplementary/`.

## Author Confirmation Still Needed

- Replace the Zenodo DOI placeholder in `CITATION.cff` after Zenodo archives the GitHub release.
- Confirm whether manuscript and data should use MIT, CC BY 4.0, or a separate license statement.
