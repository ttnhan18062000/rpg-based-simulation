# Test Plan — TCK-20260612-LOCAL-CTX-EVAL

PHASE_TS: 2026-06-12T00:00:00Z

## What to test

`tools/eval_search.py` is a developer tool that calls a subprocess. Unit tests mock the subprocess call to avoid requiring a live index.

## Test cases

| ID | Description | How |
|---|---|---|
| T-LOAD-01 | queries.json loads and has 40 entries | json.load + len check |
| T-LOAD-02 | Each entry has required keys: query, expected_doc_ids, notes | All entries validated |
| T-LOAD-03 | Query categories balanced: ≥15 semantic, ≥15 exact-term, ≥5 cross-section, ≥5 edge-case | count by notes prefix |
| T-METRICS-01 | Recall@K=1 when expected in top-1 | mock subprocess returns 1 matching row |
| T-METRICS-02 | Recall@K=0 when expected not in results | mock returns rows without expected |
| T-METRICS-03 | MRR correct for rank 1 (1.0), rank 2 (0.5), rank 3 (0.333) | unit test the function directly |
| T-METRICS-04 | Zero-result rate counted when subprocess returns empty output | mock empty string |
| T-EXIT-01 | Exit 0 when all queries hit | mock all hits |
| T-EXIT-02 | Exit 1 when Recall@5 below threshold | mock no hits |
| T-NOINDEX-01 | Prints actionable error and exits 1 without traceback when knowledge-index missing | monkeypatch subprocess to raise or return error |

## Location

`tests/tools/test_eval_search.py`
