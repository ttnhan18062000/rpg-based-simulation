# Plan — TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE

1. Remove `CITATION_RESOLUTION_FLOOR` and `check_related_code_areas_health()` (the blocking
   floor-comparison function) from `tools/gate_checks/premise_staleness_check.py`.
2. Keep `compute_open_ticket_citation_resolution_rate()` unchanged — the measurement itself is
   genuinely useful and stays available for anyone who wants the number.
3. Keep `find_potentially_stale_open_tickets()` (the close-time advisory sweep) entirely
   untouched — it is a different mechanism that never gated on anything, and out of this
   ticket's scope per its own text.
4. Rewrite the module docstring to record why the floor is gone and must not be rebuilt as a
   threshold.
5. Update `main()` so the CLI reports the rate as an always-PASS informational marker instead of
   gating on it.
6. Remove the four tests tied to the deleted floor/guard from
   `tests/tools/test_premise_staleness_check.py`; add a test proving a population change (a
   ticket closing) moves the rate but cannot fail CI.
7. Reword the `Makefile`'s `premise-staleness-check` target help text to reflect the report-only
   behavior.
8. Run the full `tests/tools/` suite to confirm no other consumer of the removed
   constant/function exists (confirmed via grep before editing: none outside this module and its
   own test).
