# Test Plan — TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE

| Case | Verification |
|---|---|
| Closing a ticket cannot fail CI via this check | New test `test_closing_a_ticket_moves_the_rate_but_cannot_fail_ci`: synthetic before/after open-ticket population (one ticket removed), confirms the rate genuinely moves, then confirms the CLI's own reporting always exits 0 |
| The citation-resolution rate is still computed and reported | `compute_open_ticket_citation_resolution_rate()` kept unchanged and covered by its own pre-existing tests; `main()`'s MARKER output prints the rate |
| The advisory sweep is unchanged and still tested | `find_potentially_stale_open_tickets()` and its tests untouched — confirmed via diff |
| A comment records why the floor is gone | Module docstring rewritten, naming this ticket and the precedent |
| No other consumer breaks | Grepped for `CITATION_RESOLUTION_FLOOR`/`check_related_code_areas_health` before editing — none outside this module and its own test; full `tests/tools/` suite run after: 2735 passed, 0 failed |

Executed: `pytest tests/tools/test_premise_staleness_check.py -v` — 23 passed.
