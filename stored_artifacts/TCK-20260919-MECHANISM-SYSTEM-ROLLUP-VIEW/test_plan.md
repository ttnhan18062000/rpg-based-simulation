---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW

## Normal flow
- `build_system_rollup()` on the real registry produces one row per registered system plus
  `unassigned`, each with a full state breakdown and bound/verified counts — smoke-tested directly,
  then covered by the real-file-up-to-date regression test.

## Edge cases
- A 0-member group (`unassigned` on the real registry today): rates must not render a misleading
  delta against baseline. Covered by the renderer's `n/a` branch and exercised on the real file.
- Multi-system mechanisms (8 of 93, from the foundation ticket): counted once per system they
  declare, exactly as `mechanisms_by_system()` already does — no double-counting logic needed here
  since this ticket consumes that function's output unmodified.

## Failure modes / regression-prone paths
- **The counts-vs-badge boundary** (AC #1): `test_rollup_reports_counts_not_a_single_status` checks
  no `status`/`badge`/`verdict`/`summary_status` key ever appears on a rollup row. A future change
  adding a derived summary field would fail this test by design — the whole point of the assertion
  is to make that regression impossible to add silently.
- **The baseline-not-isolated boundary** (AC #2): `test_rollup_baseline_computed_live_not_hardcoded`
  proves the baseline is computed from whatever data is passed in, not a fixed number — this is the
  test that would catch someone "optimizing" the function by hardcoding a snapshot baseline for
  speed, which would silently go stale the way the value investigation's own 74%/30% already have.
- **Ranking-from-membership** (AC #5): `test_rollup_computes_nothing_that_reads_as_a_ranking` uses
  systems named to sort differently by rate than alphabetically (`zeta` has the higher bound rate,
  `alpha` sorts first) and asserts alphabetical order wins — would catch a future "sort by
  interesting-ness" change that silently reintroduces a derived ranking.

## Coverage delivered
10 new tests in `tests/unit/tools/test_mechanism_system_rollup_view.py`, plus the standard
generator-CLI trio (staleness detection, Make target, real-file regression) matching
`test_mechanism_registry_view.py`'s own structure. Full `tests/unit/tools/` suite: 216 passed (206
pre-existing + 10 new). `registry.py::validate()` passes clean against the real, unmodified-by-this-
ticket registry (93 mechanisms) — this ticket touches no `mechanisms.yaml` data, only adds a new
read-only consumer of it.
