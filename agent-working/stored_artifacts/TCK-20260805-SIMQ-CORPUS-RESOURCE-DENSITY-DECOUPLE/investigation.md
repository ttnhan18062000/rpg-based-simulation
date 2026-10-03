---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE
artifact_type: investigation
tags: [simulation-quality, world, economy, corpus, calibration]
---

# investigation.md — TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE

## Current Behavior (file:line refs)

The ticket's premise, from `corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" (gap #2):
"High resource-node density with a small map (or the inverse...). Node-per-region density is
currently roughly flat (1.3-1.75) across the corpus regardless of overall scale."

**This premise was already false when the ticket was filed** — exactly the same staleness pattern
found and corrected in this session's sibling ticket, `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`
(gap #1). The doc's own per-world table (line 142) already documents:
`resource_dense_basin` | Stress | 23 entities, 3 regions — **fills gap 2
(resource-saturated/small-map)**: the corpus's new resource-node density maximum, ~2.33
nodes/region (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`).

## Verification (real corpus data, not re-reading the doc)

Computed real node-per-region density from every `data/worlds/*/world_compile_report.json` in the
corpus:

| World | Regions | Nodes | Density |
|---|---|---|---|
| `highland_traverse` | 5 | 3 | 0.60 (sparsest) |
| `dungeon_crawl` | 4 | 3 | 0.75 |
| `resource_dense_basin` | 3 | 7 | **2.33 (densest)** |
| `unit_information_density`/`unit_information_source`/`unit_selfmodel_pilot` | 1 | 2 | 2.00 |

The corpus's real density range is **0.60–2.33**, not the "roughly flat 1.3-1.75" the gap text
claims — `resource_dense_basin` (3-region small map, 2.33 density) already sits well outside that
claimed flat band, on the dense-and-small side gap #2 asks for. `highland_traverse` similarly
already covers meaningful sparse-density territory (0.60, on a 5-region map), though not phrased
as deliberately targeting this gap.

## Conclusion

**Gap #2 is already closed** by `resource_dense_basin`, which was authored specifically for this
purpose (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`) and is already correctly documented as doing so
in the per-world table — just not in the gap-list section, which was never updated to match. No
new world is needed; authoring one would duplicate `resource_dense_basin`'s already-established
role, the same redundancy this session's sibling ticket found and avoided for gap #1.

## Docs Requiring Update
- `docs/simulation_quality/corpus_tier_taxonomy.md`: gap #2 in the "Named scale-diversity gaps"
  list marked CLOSED, citing `resource_dense_basin` and the staleness, matching the correction
  pattern already applied to gap #1.

## Parity Ledger Overlap
None.

## Prior Work
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` — authored `resource_dense_basin`, which closes this
  gap (correctly documented in the per-world table, just not the gap-list section).
- `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP` (this session) — found and corrected the
  identical staleness pattern for gap #1; this ticket applies the same correction to gap #2.

## Risks and Open Questions
None outstanding. Verified via real compile-report data across the full corpus, not just a doc
reading.
