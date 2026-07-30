---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY
date: 2026-07-30
tags: [dashboard, observability, api-design]
---

# Investigation — TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY

## Current Behavior (file:line refs)

- `src/api/agent_ops_dashboard/ingest.py:620` builds `facets["tags"]` via
  `_distinct_sorted(tag for r in filtered for tag in r["tags"])` — derived from `filtered` (the
  post-filter ticket list), unlike `tiers`/`layers`/`statuses`/`priorities` (lines 617-619), which
  read `sorted(TIER_VALUES)`/`sorted(LAYER_VALUES)`/etc., fixed canonical sets independent of
  `filtered`. This means `tags` is both corpus-derived (only tags actually present appear) AND
  filter-affected (narrowing by another facet also narrows which tags show up) — the comment block
  at lines 605-611 documents this asymmetry as deliberate, dated `TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL`.
- Precedent for the target pattern already exists in the same file: `get_glossary()` (line 902)
  imports `layer_registry` (line 51) and calls `layer_registry.load_registry(self._repo_root)`
  directly — a fresh, uncached read of a small registry file, not participating in `_rebuild()`'s
  mtime-cache cycle (see that method's own docstring rationale: "all three sources are small and
  change far less often than tickets/runs").
- `tools/tag_registry.py:124`'s `load_registry(root)` returns `{tag: entry_dict}`, raising
  `ValueError` on a duplicate tag line — confirmed no try/except wraps the equivalent
  `layer_registry.load_registry()` call in `get_glossary()`, so this ticket's plan follows that
  same no-try/except precedent rather than inventing new error handling.
- `registries/tag_registry.jsonl` (relocated by `TCK-20260720-TAG-REGISTRY-RELOCATE`, landed
  earlier in this session) currently has 52 registered tags — confirmed via
  `python3 tools/tag_registry.py list | wc -l`.
- `docs/parity_ledger/infrastructure.yaml` INFRA-275 (checked directly) documents `facets['tags']`
  as "the one facet that remains corpus-derived" — this entry's `text`/`v2_evidence` must be
  updated to reflect the new registry-derived behavior.

## Mechanics/Engine Constraints

None — dashboard/observability tooling, `layer: observability`, no simulation engine or Mechanics
Bible relevance.

## Parity Ledger Overlap (IDs + status)

- INFRA-275 (`docs/parity_ledger/infrastructure.yaml`) — currently `status: verified` describing
  the old corpus-derived-only behavior. This ticket updates its `text`/`v2_evidence` to describe
  the new registry-derived behavior; status stays `verified` (still true, just for new evidence).

## Prior Work

- `TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL` made `tiers`/`layers`/`statuses`/`priorities`
  canonical/registry-derived and explicitly left `tags` corpus-derived at the time (its own
  reasoning, quoted in the current code comment: tags is "genuinely open-vocabulary and
  multi-value ... not a small closed enum the way the other four are"). This ticket's Request
  Summary treats that reasoning as now-outdated since `tag_registry.jsonl` (now
  `registries/tag_registry.jsonl`) has existed as a real closed-ish registry since
  `TCK-20260706-TAG-REGISTRY-DATA` — "open-vocabulary" was true before the registry existed, not
  after.

## Risks and Open Questions

- **Deliberate behavior change (AC #5)**: legacy/pre-taxonomy free-text tags present on real
  tickets but absent from the registry will disappear from the filter facet; open-ended phase-N
  tags (`Scope`, `Investigate`, etc., per `is_phase_milestone_tag()`) also won't appear in a pure
  registry-keys facet since phase-milestone tags are exempt from registration entirely. This is
  recorded here as the ticket's own required explicit, non-silent decision: both are accepted
  consequences of switching to registry-derived, not a regression to silently work around.
- **Facet count growth**: verified live — registry has 52 tags vs. whatever smaller corpus-derived
  set currently renders; `TicketsView.tsx`'s existing `MAX_VISIBLE_TAGS(40)` + search-narrowing
  already exists and its own tests tolerate larger synthetic counts (confirmed by reading
  `TicketsView.test.tsx` — no hardcoded assumption of a small tag count found). No frontend change
  needed; verified rather than assumed, per the ticket's own Out of Scope note.

## Anti-Drift Hazards

- `facets["tags"]` must become fully independent of `filtered`/any active query filter — reading
  directly from `tag_registry.load_registry()`, exactly mirroring how `tiers`/`layers`/`statuses`/
  `priorities` already read from fixed sets rather than `filtered`.
- Do not touch `TicketsView.tsx` — Out of Scope, verified rather than assumed to need no change.
- Do not touch `tag_registry.py` itself — this ticket only changes a *consumer*.
