---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES
artifact_type: test_plan
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES

- AC1: disposition closure with cited rationale, no staging artifacts, no src/ change: PASS,
  including the full `run_finalize_selfcheck` (temp git repo with an `origin/main` ref).
- AC2: uncited rationale, empty rationale, missing rationale section, unknown value, committed
  `src/` change: each FAILs and names the requirement; a `src/` change from another ticket's commit
  does not count.
- AC3: no Disposition + missing artifacts still FAILs `migration_complete`.
- AC4: `check_ticket_field_values` rejects an unknown Disposition; unchanged shape without one.
- AC5: read-only registry check leaves the file byte-identical and reports a stale file; default
  `run_finalize_selfcheck` still regenerates; CLI writes only with `--regenerate-registry`; the
  module-scoped tracked-path guard stays green.
- AC6/AC7: guide carries the subsection once; two sections parse independently.
- Regression: `test_ticket_field_values.py`, `test_done_checker_static.py`,
  `test_monitoring_consolidation.py`.
