# Plan — TCK-20260612-LOCAL-CTX-EVAL

PHASE_TS: 2026-06-12T00:00:00Z

## Steps

1. Create `tools/eval/queries.json` — 40 curated queries (15 semantic, 15 exact-term, 5 cross-section, 5 edge-case)
2. Create `tools/eval_search.py` — evaluation runner (subprocess + TSV parse + metrics)
3. Update `Makefile` — add `eval-search` target
4. Update `.gitignore` — add `reports/`

## eval_search.py design

- Load `tools/eval/queries.json`
- For each query: run `python3 tools/knowledge_search.py query "{q}" --top-k 10` via subprocess
- Parse stdout: split lines by `\t`, col 0 is doc_id
- Hit check: `doc_id in expected_doc_ids` for any result
- Recall@5: hits in positions 0-4 / total
- Recall@10: hits in positions 0-9 / total
- MRR@10: mean(1/(rank+1) for first hit in top-10), 0.0 if no hit
- Zero-result rate: queries with 0 lines output
- Print per-query table + summary line
- Save `reports/eval_search_YYYYMMDD.json`
- Exit 0 if Recall@5 >= threshold (default 0.80), else exit 1
