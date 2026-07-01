# Data

The main EVA transcription input expected by the parser is `ZL_ivtff_2b.txt` (Zandbergen-Landini, IVTFF format).

That transcription file is not included in this repository because it has separate provenance. To reproduce the exported results, place a local copy of `ZL_ivtff_2b.txt` in the repository root or pass its path with `--input`.

The lexical resources used by parser version v22 are encoded in `parser/parser.py` as `ROOTS`, `PREFIXES`, and `SUFFIXES`.
