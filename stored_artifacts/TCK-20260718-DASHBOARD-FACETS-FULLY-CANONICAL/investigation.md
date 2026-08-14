---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
date: 2026-07-18
tags: [observability]
---

# Investigation — TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Current Behavior (file:line refs)

- `src/api/agent_ops_dashboard/ingest.py`'s `get_tickets()` facets block
  (pre-change): `tiers`/`layers`/`priorities` all computed via
  `_distinct_sorted(r[...] for r in filtered)` — corpus-derived, can shrink
  to exclude a legitimate value when a combined filter yields zero matches.
  `statuses` already fixed to `sorted(WORKFLOW_STATUS_VALUES)` by
  TCK-20260718-STATUS-FACET-CANONICAL/-TIER-PRIORITY-CANONICAL-ENUM.
- `tools/ticket_field_values.py` already exports `TIER_VALUES`,
  `PRIORITY_VALUES`, `LAYER_VALUES` (the latter now registry-backed per
  TCK-20260718-LAYER-REGISTRY-CONVERSION), `WORKFLOW_STATUS_VALUES` —
  confirmed all four importable and correct via direct interpreter check.
- `dashboard-frontend/src/views/TicketsView.tsx`'s `FilterSelect` (lines
  ~95-114): renders `<select value={value}>`, with `options.map(...)`
  populating `<option>`s, plus a synthetic-option fallback (added by
  TCK-20260718-FILTER-SELECT-DROPOUT) for when `value` isn't in `options`.
  Exactly 4 call sites: Tier/Layer/Status/Priority.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry already
  covers the dashboard backend, extended once already by
  TCK-20260718-STATUS-FACET-CANONICAL. Found two now-stale claims in it
  while reading in full: a `list(WORKFLOW_STATUS_VALUES)` code citation
  (superseded by TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM's `sorted(...)`
  change, never corrected there) and a "tiers/layers/priorities/tags...
  still corpus-derived" claim this ticket makes false for 3 of those 4.

## Mechanics/Engine Constraints

None — dashboard tooling, not simulation gameplay.

## Parity Ledger Overlap (IDs + status)

`INFRA-275` — extend in place (see above), including fixing the two stale
claims found, not just appending new text on top of them.

## Prior Work

- TCK-20260718-STATUS-FACET-CANONICAL — the exact pattern this ticket
  generalizes from `statuses` to `tiers`/`layers`/`priorities`.
- TCK-20260718-FILTER-SELECT-DROPOUT — the band-aid fix this ticket's real
  facets change supersedes (its synthetic-option code is investigated for
  removal, see Risks below).
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM,
  TCK-20260718-LAYER-REGISTRY-CONVERSION — both prerequisites, both DONE,
  both confirmed to export the needed canonical sets correctly.

## Risks and Open Questions

- Whether `FilterSelect`'s synthetic-option fallback should be removed now
  that it's unreachable for its 4 real call sites — resolved during
  Implement: kept, re-documented as defensive-only, with a test proving
  it's genuinely unreachable in practice (not just asserted).
- Live verification is explicitly required, not optional, per this
  ticket's own AC — a stale `dashboard-serve` process caused a
  false-negative check once already today (confirmed again during this
  ticket's own Implement phase — a stale process was found and killed
  before the real verification ran).

## Anti-Drift Hazards

- `sorted(TIER_VALUES)`/`sorted(LAYER_VALUES)`/`sorted(PRIORITY_VALUES)` —
  all three are frozensets, must sort explicitly (unordered iteration is
  not guaranteed stable), matching the precedent already set for
  `WORKFLOW_STATUS_VALUES`.
