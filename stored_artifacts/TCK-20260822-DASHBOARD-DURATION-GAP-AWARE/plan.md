# Plan — TCK-20260822-DASHBOARD-DURATION-GAP-AWARE

See investigation.md for the full 6-step plan and the correction to this ticket's own "breaks
outright" claim (empirically overstated — Pydantic's default `extra="ignore"` already tolerates
the new fields; this ticket's real job is surfacing them, not preventing a crash that wasn't
actually happening).

## Explicit non-goals (Out of Scope, restated)
- No independent duration/gap computation in `ingest.py` — strictly consumes the sibling ticket's
  `compute_retro_metrics()` output.
- `RunSummary.duration_s` (the dormant second passthrough) — flagged in a comment only, not fixed.
