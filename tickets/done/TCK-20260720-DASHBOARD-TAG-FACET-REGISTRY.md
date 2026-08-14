---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY
phase: done
date: 2026-07-20
tags: [dashboard, observability, api-design]
---

# TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY

## Title
Make the Agent Ops Dashboard tags facet registry-derived instead of corpus-derived

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
src/api/agent_ops_dashboard/ingest.py currently derives its tags filter facet only from tags actually present on tickets in the filtered corpus, unlike tier/layer/status/priority, which already became fully canonical fixed lists sourced from their registries in TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL. Change the tags facet to read registries/tag_registry.jsonl directly so every registered tag is a selectable filter option regardless of whether any ticket currently uses it.

## Scope
- Change ingest.py's tags facet to read registries/tag_registry.jsonl via tag_registry.load_registry(), mirroring the existing layer_registry.load_registry() pattern already used for get_glossary()
- Rewrite ingest.py's stale comment rationale (around lines 598-604) describing tags as open-vocabulary/corpus-derived to reflect the new registry-backed model
- Update docs/parity_ledger/infrastructure.yaml's INFRA-275 entry in the same session
- Update docs/guides/agent_ops_dashboard.md and docs/observability/agent_ops_dashboard_contract.md's descriptions of the Tickets view's tags filter to describe the registry-derived (not corpus-derived) behavior

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- Frontend changes to TicketsView.tsx — MAX_VISIBLE_TAGS(40)/search-narrowing already exists and is tested against larger synthetic counts; verify live rather than assume, but no change is expected

## Acceptance Criteria
- [ ] get_tickets()'s facets['tags'] equals sorted(tag_registry.load_registry(repo_root).keys()) regardless of which tags appear in the filtered/paginated corpus — a registered tag with zero current tickets still appears
- [ ] facets['tags'] is unaffected by active tier/layer/status/priority/tags query filters (mirrors the existing canonical-facet test pattern)
- [ ] ingest.py imports tag_registry via the same module-level cross-package pattern already used for layer_registry (confirmed at line 51's get_glossary() call) — not a new bespoke import mechanism
- [ ] docs/parity_ledger/infrastructure.yaml's INFRA-275 entry (which currently documents facets['tags'] as "the one facet that remains corpus-derived") is updated in the same session
- [ ] The semantic behavior change — legacy/pre-taxonomy free-text tags present on tickets but absent from tag_registry.jsonl will disappear from the filter facet, and open-ended phase-N tags won't appear in a pure registry-keys facet — is stated as a deliberate, explicitly recorded decision in this ticket, not a silent regression
- [ ] docs/guides/agent_ops_dashboard.md and docs/observability/agent_ops_dashboard_contract.md describe the tags filter as registry-derived, matching how those docs already describe tier/layer/status/priority since TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Related Tickets
- TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
- TCK-20260718-STATUS-FACET-CANONICAL
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260719-TAG-COLLISION-DEDUP
- TCK-20260720-TAG-REGISTRY-RELOCATE

## Related Docs
- docs/parity_ledger/infrastructure.yaml
- docs/guidelines/tag_registry.jsonl
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- tools/ticket_field_values.py
- tools/tag_registry.py
- tools/layer_registry.py
- dashboard-frontend/src/views/TicketsView.tsx
- dashboard-frontend/src/test/TicketsView.test.tsx
- tests/tools/test_agent_ops_dashboard_ingest.py

## Assumptions / Open Questions
- tag_registry.load_registry() raises ValueError on a duplicate JSONL line — the existing get_glossary() layer_registry call has no try/except for this, so this mirrors existing precedent, but get_tickets() is a hotter path and this should be confirmed acceptable
- Facet option count grows from corpus-subset to the full ~52 registered tags — TicketsView.tsx's existing tests already tolerate larger synthetic counts, but this should be verified live rather than assumed
- Phase-N tags won't appear in a pure registry-keys facet — likely fine since they're not typically filter-browsed, but this should be an explicit scope note

## Implementation Notes

Added `import tag_registry` alongside the existing `import layer_registry` in `ingest.py` (same
module-level cross-package pattern already used for `get_glossary()`). Changed
`facets["tags"]` from `_distinct_sorted(tag for r in filtered for tag in r["tags"])` to
`sorted(tag_registry.load_registry(self._repo_root).keys())` — the fifth and last ticket facet to
become fixed/canonical. Rewrote the stale comment block explaining the old rationale, and fixed a
second, already-stale nearby comment (predating this ticket, left over from
`TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM`) that still claimed `tiers`/`layers`/`priorities`
derived from the filtered corpus — both are now accurate. `_distinct_sorted()` had zero remaining
call sites after this change and was deleted rather than left as dead code.

Updated `docs/parity_ledger/infrastructure.yaml` INFRA-275: appended a new evidence paragraph for
this ticket (following the entry's own established accretive-append convention) and added a
"superseded below by TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY" note directly onto the prior
"only tags remains corpus-derived" claim, rather than silently leaving it to mislead a future
reader — mirrors the same entry's own precedent (see its "correcting a stale claim... fixed now
rather than left stale" passage for `WORKFLOW_STATUS_VALUES`).

Updated `docs/guides/agent_ops_dashboard.md` and `docs/observability/agent_ops_dashboard_contract.md`
to describe the tags filter as registry-derived, matching how tier/layer/status/priority are
already described — explicitly stating the deliberate consequence (a legacy/unregistered corpus
tag or an open-ended phase-N tag no longer appears in the facet).

Verified `TicketsView.tsx`/`TicketsView.test.tsx` need no change by reading both directly: the
frontend already tests against synthetic tag lists of 1500 and 50 entries (`MAX_VISIBLE_TAGS=40`
+ `narrowTags()` search-narrowing), far more than the ~52 tags `registries/tag_registry.jsonl`
actually holds; it consumes `optionsFacets.tags` generically regardless of source.

Added 3 new tests to `tests/tools/test_agent_ops_dashboard_ingest.py`: a new
`_write_tag_registry_fixture()` helper, an updated
`test_facets_source_reflects_full_filtered_corpus_not_just_current_page` (now also asserts
registry-sourced tags), a new `test_tags_facet_is_canonical_registry_derived_regardless_of_corpus_content`
(proves the inverse of the old contract — a registered-but-unused tag appears, an
unregistered-but-used corpus tag does not), and a new
`test_tags_facet_unaffected_by_active_filters`.

Parity: `src/api/agent_ops_dashboard/ingest.py` changed and `behavior_changed=true`, so the full
(non-skip) parity path applied — `infrastructure.yaml` was the single expected target per
`expected_subsystems_for_files()`, confirmed touched via `cross_reference_touched()` (PASS).

## Test Summary

`python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -q` → **42 passed**, 0 failed
(39 pre-existing + 3 new).

## Files Changed
- `src/api/agent_ops_dashboard/ingest.py` (`import tag_registry`, `facets["tags"]` now
  registry-derived, 2 stale comment blocks rewritten, dead `_distinct_sorted()` removed)
- `tests/tools/test_agent_ops_dashboard_ingest.py` (new `_write_tag_registry_fixture()` helper, 1
  updated test, 2 new tests)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-275: new evidence paragraph + superseded-claim note)
- `docs/guides/agent_ops_dashboard.md`, `docs/observability/agent_ops_dashboard_contract.md`
  (tags-filter description updated to registry-derived)

## Completion Summary
`facets["tags"]` in the Agent Ops Dashboard's `GET /api/tickets` response is now sourced directly
from `registries/tag_registry.jsonl` (via `tag_registry.load_registry()`, mirroring the existing
`layer_registry.load_registry()` pattern already used for `get_glossary()`), joining
`tiers`/`layers`/`statuses`/`priorities` as a fixed canonical facet independent of active filters,
pagination, or current corpus content — the fifth and last facet to make this transition. The
deliberate consequence (legacy/unregistered corpus tags and open-ended phase-N tags no longer
appear in the facet) is recorded explicitly in this ticket, the parity ledger, and both affected
docs — not a silent regression. 42 tests pass (3 new); the one affected parity-ledger entry
(INFRA-275) was updated and cross-reference-verified.
