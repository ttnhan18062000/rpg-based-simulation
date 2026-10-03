---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH
phase: done
date: 2026-08-08
tags: [content, world, documentation]
---

# TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH

## Title
Refresh and regenerate `docs/audits/D07_content_depth.md` — the existing content-inventory doc
(items, factions, entity archetypes, recipes, modules, etc.) is stale by ~2 months and no longer
matches real `data/content/` counts

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
User asked for a document tracking the simulation's existing data — item counts, faction counts,
class/archetype counts, and any other data-driven content related to world/entity mechanics.
**A real, directly on-point document already exists**: `docs/audits/D07_content_depth.md`
("Content Depth & Variety" — items, factions, entity archetypes, recipes, world modules,
compositions, quest definitions, all layered and counted). Checked before authoring anything new,
per this repo's own "check before creating redundant content" discipline (the same pattern that
found `corpus_tier_taxonomy.md`'s own stale gap-list sections twice this repo's history).

**Confirmed stale, not just old.** D07's own `Audit date: 2026-06-18`; today is 2026-08-08 — ~7
weeks of real content-authoring work has landed since (this session alone authored
`frontier_marches`, `simq_scale_stress_seed42`, `quest_dense_frontier`, and others). Spot-checked
2 categories directly against real `data/content/`:

| Category | D07's claimed count | Real current count |
|---|---|---|
| World modules | 19 | **20** |
| World compositions (non-generated) | 5 | **7** |
| Items | 34 | **~36** (needs exact re-verification, not just a quick count) |

D07 is a **hand-counted, static snapshot** — no script regenerates it, unlike
`corpus_registry.yaml` (`tools/generate_corpus_registry.py`, "generated from real data, never
hand-transcribed"). This is why it drifted silently for 7 weeks with no staleness signal.

## Scope
1. **Investigate** (mandatory before Plan):
   - Re-count every category in D07's own existing table structure (Foundation, Entity, World,
     Social & Scenario, Module layers) against real, current `data/content/` — confirm which
     categories actually drifted and by how much, not just the 2 spot-checked here.
   - Check whether D07's own 6 Key Findings (F1-F6, several already marked RESOLVED) are still
     accurately resolved given real current content, or whether any regressed/reopened.
   - Decide whether a lightweight `tools/generate_content_inventory.py` script (mirroring
     `tools/generate_corpus_registry.py`'s own "generated, never hand-transcribed" pattern) is
     worth building so this doc — or a machine-readable sibling — never goes stale silently again,
     versus keeping D07 as a periodic manual audit (matching its own existing "audit" framing,
     distinct from `corpus_registry.yaml`'s always-fresh convention).
2. **Plan**: design the refresh — real updated counts, updated Gap Risk scores for any finding
   whose real numbers changed enough to matter, and (if Investigate concludes it's warranted) the
   new generator script's exact scope.
3. **Implement**: the refresh (and generator script, if scoped), verified against real
   `data/content/` counts, not assumed.

## Out of Scope
- Actually authoring new content to close any of D07's own open gap findings (F4 archetype
  distribution, F6 faction relationships, etc.) — this ticket refreshes the *measurement*, not the
  content itself. Any real, still-open gap found here becomes its own follow-up ticket.
- Rewriting D07's own scoring methodology (Content Gap Risk / Layer Content Health formulas) — out
  of scope unless Investigate finds the methodology itself, not just the counts, has drifted.

## Acceptance Criteria
- [ ] investigation.md reports real, current counts for every category D07 tracks, with a real
      diff against the existing doc
- [ ] investigation.md reports whether any RESOLVED finding has regressed
- [ ] plan.md decides generator-script vs. manual-refresh, with real rationale
- [ ] D07_content_depth.md updated with real current data (or superseded by a generated
      equivalent, if that's the real decision)
- [ ] `TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD`'s own Investigate phase can cite this refreshed
      doc directly when surveying reusable content for its own world-composition decision
- [ ] Scoped pytest passes (if a generator script is added)

## Related Tickets
- TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD (a direct consumer of accurate content-inventory
  data — this refresh should land before or alongside that ticket's own Investigate phase)
- TCK-20260619-E13A-QUEST-DEFS, TCK-20260619-E13B-MODULE-TYPES, TCK-20260619-E13C-RECIPES,
  TCK-20260619-E13D-SCENARIOS (the historical tickets that resolved D07's own F1/F2/F3/F5 —
  re-verify their resolutions still hold against real current data)
- TCK-20260627-P2C-ARCHETYPE-DIST, TCK-20260627-P2D-FACTION-RELS (still-open D07 findings F4/F6 —
  confirm current status)

## Related Docs
- `docs/audits/D07_content_depth.md` (the document this ticket refreshes)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (the "generated, never hand-transcribed"
  precedent this ticket's own generator-script option would follow)
- `config/simulation_quality/corpus_registry.yaml`, `tools/generate_corpus_registry.py` (direct
  precedent for a real, regenerable content-metadata artifact)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `data/content/` (the real source of truth this doc counts)
- `tools/generate_corpus_registry.py` (precedent pattern for a generator script, if scoped)

## Assumptions / Open Questions
- Whether a full generator script is worth building now, or whether a manual refresh (matching
  D07's own existing "periodic audit" framing) is sufficient until the next real drift is found —
  not assumed; Investigate should weigh the real cost of silent staleness (7 weeks, undetected)
  against the cost of building and maintaining a new tool.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Real re-count of every category found severe, silent drift: `Recipes` 8→25, `Faction
relationships` 14→75, `Entity archetypes` 21→29 (with a real, substantial distribution
rebalancing — `mage` 0-1→3, `healer` 0→2, `leader` 1→3). Two distinct staleness patterns found:
ordinary content drift since the 2026-06-18 audit, and a separate internal-consistency bug already
in the doc itself (F3/F5's own Gap Risk Summary already said "RESOLVED" with a correct new count
while the per-layer table just above still showed the old number — never reconciled).

Built `tools/generate_content_inventory.py` (mirrors `tools/generate_corpus_registry.py`'s own
"generated, never hand-transcribed" precedent) so this can't silently drift again — re-run via
`make content-inventory`. Refreshed every numeric table in D07, fixed the F3/F5 internal
inconsistency, and re-scored F4 (Gap Risk 9→5/15, real improvement, not fully resolved — 11 of 18
roles still single-entry) and F6 (Gap Risk unchanged as a historical record, but marked RESOLVED —
75 relationships is 62.5% coverage, past the doc's own 50% target). Did not chase the Module
Layer's own finer-grained type-distribution sub-table to full reconciliation (disclosed as stale,
not silently corrected) — a real, deliberate scope boundary given this ticket's own narrower
purpose (top-level catalog counts, not a full module-taxonomy re-audit).

## Test Summary
`pytest tests/tools/test_content_inventory.py -q` — 3/3 passed (all new: category completeness,
real-count spot-checks against 3 independent source files, module/composition file-count
cross-checks).

## Files Changed
- `tools/generate_content_inventory.py` — new
- `tests/tools/test_content_inventory.py` — new
- `config/content_inventory.json` — new, generated
- `Makefile` — new `content-inventory` target
- `docs/audits/D07_content_depth.md` — refreshed with real current data throughout

## Completion Summary
Refreshed a real, existing content-inventory document rather than creating a duplicate — found
severe (3-5x on 2 categories) silent drift and a separate pre-existing internal-consistency bug,
both now fixed with real data. Built a small generator script so future drift can't go undetected
for 7 weeks again. 2 of the doc's own open findings (F4, F6) were re-scored with real evidence;
F6 is now resolved, F4 substantially improved but honestly left open. Directly unblocks
`TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD`'s own Investigate phase.
