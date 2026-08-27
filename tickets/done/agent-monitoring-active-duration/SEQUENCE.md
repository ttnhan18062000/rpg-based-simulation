# Implementation Sequence — agent-monitoring-active-duration

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT  (no deps in this batch)
2. TCK-20260822-DASHBOARD-DURATION-GAP-AWARE  (depends on: TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT)

## Why This Order Matters

**Written by hand, not auto-generated** — same reason as the `semantic-entity-index` and
`world-grammar-semantic-constraints` batches earlier this session: each ticket's own
`## Related Tickets` section cross-references the other (forward-reference, not a prerequisite),
which would make a naive "any batch ID mentioned is a prerequisite" heuristic misread this
2-ticket batch as circular.

The real, unambiguous direction: `DASHBOARD-DURATION-GAP-AWARE`'s own investigation found a hard,
real coupling on `DURATION-ACTIVE-IDLE-SPLIT` — the dashboard's `SlowRunEntry`/`DurationOutlierEntry`/
`RunSummaryStats` Pydantic models are constructed via `SlowRunEntry(**r)`-style kwargs unpacking
straight from `generate_retro.py`'s `compute_retro_metrics()` output. If `DURATION-ACTIVE-IDLE-SPLIT`
changes that output shape (adding `active_duration_s`/`idle_gap_s`) without the dashboard ticket
following in the same or a closely-sequenced change, `GET /api/stats` breaks outright. Also note:
`duration_utils.py` (the shared computation both tickets build on) does not exist yet — it must
land first regardless of the dashboard question.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
