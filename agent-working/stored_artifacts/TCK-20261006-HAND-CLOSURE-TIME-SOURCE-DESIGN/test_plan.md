# Test Plan — TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN

Design-only ticket; no code. Checks:
1. `design.md` coverage table has rows A/B/C, a named set (238 hand closures W40-W41), run_ids in `coverage_by_run.csv`, ref 7ddcd4526 (AC1).
2. One source and one join key are chosen; rejected options carry a one-line reason (AC2).
3. Schema delta lists field, type, nullability, vocabulary (AC3).
4. `measure_sources.py` re-runs and reproduces the headline counts (238 / 14 / 130 / 235).
5. Children 2-4 contain the design's acceptance criteria (AC5).
