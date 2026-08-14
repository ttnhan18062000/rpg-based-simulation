---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [content, world, documentation]
---

# Investigation — TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH

## Real, current counts vs. D07's own claimed counts (every category, not just the 2 spot-checked)

Counted directly from `data/content/` (not assumed, not copied from any other doc):

| Category | D07 claimed | Real now | Diff |
|---|---|---|---|
| Traits | 25 | 26 | +1 |
| Themes | 24 | 24 | 0 |
| Roles | 23 | 23 | 0 |
| Materials | 17 | 18 | +1 |
| Attributes | 15 | 15 | 0 |
| Relationship axes | 12 | 12 | 0 |
| Elements | 11 | 11 | 0 |
| Stat profiles | 23 | 23 | 0 |
| **Entity archetypes** | 21 | **29** | **+8** |
| Populations | 14 | 14 | 0 |
| Races | 13 | 13 | 0 |
| Combat profiles | 10 | 10 | 0 |
| Skill profiles | 10 | 10 | 0 |
| Inventory profiles | 10 | 10 | 0 |
| Body models | 8 | 8 | 0 |
| Cognition profiles | 7 | 7 | 0 |
| Drive profiles | 7 | 7 | 0 |
| Need profiles | 6 | 6 | 0 |
| Sense profiles | 6 | 6 | 0 |
| Items | 34 | 36 | +2 |
| Runtime regions | 15 | 20 | +5 |
| Biomes | 13 | 13 | 0 |
| Resources | 11 | 12 | +1 |
| Buildings | 9 | 9 | 0 |
| Ecologies | 9 | 9 | 0 |
| Terrain | 9 | 10 | +1 |
| Services | 8 | 8 | 0 |
| **Recipes** | 8 (table) / "25, RESOLVED" (own Gap Risk Summary text) | **25** | table never updated to match the doc's own resolution text — an internal inconsistency, independent of new drift |
| Factions | 16 | 16 | 0 |
| **Faction relationships** | 14 | **75** | **+61** |
| Perspectives | 6 | 6 | 0 |
| Simulation scenarios | 8 (table) / "14, RESOLVED" (own F5 text) | **14** | same internal-inconsistency pattern as Recipes |
| World modules | 19 | 20 | +1 |
| World compositions (non-generated) | 5 | 7 | +2 |
| World compositions (generated) | "+4" (prose, Module Layer table) | **2** | real count now lower than claimed — `generated_frontier_3_42.yaml`, `simq_scale_stress_seed42.yaml` only |

**Two real, distinct staleness patterns found, not one**: (1) ordinary drift from real content
authored since the 2026-06-18 audit date (traits/materials/items/runtime_regions/resources/
terrain/world modules/compositions all grew modestly); (2) the doc's own Layer tables were **never
updated** even when its own Gap Risk Summary section (further down the same file) already recorded
a finding as RESOLVED with a real new count — Recipes and Simulation scenarios both show this:
the bottom-line summary says "RESOLVED: 25 recipes"/"RESOLVED: 14 scenarios" while the per-layer
table just above still shows the old pre-resolution numbers. This is a real, disclosed internal
consistency bug in the document itself, independent of new drift.

## Re-checking D07's own still-open findings against real current data

- **F3 (Recipes, Gap Risk 10/15)**: already marked RESOLVED in the doc's own Gap Risk Summary
  (25 recipes) — confirmed real and current (25, matches exactly). Only the Layer 3 table itself
  needed the refresh.
- **F4 (Entity archetype distribution skewed, Gap Risk 9/15, still OPEN)**: real, current role
  distribution (29 archetypes): `scout=4, leader=3, mage=3, predator_hunter=2, raider=2, healer=2,
  hunter=2, [11 more roles at 1 each]`. The original complaint was specifically "no dedicated
  mage/caster role has more than 1 entry" and "4 scouts, 2 raiders, 2 leaders, then 1 each for 13
  other roles" — **both are now false**: `mage` has grown from ≤1 to 3, `healer` from 0 to 2,
  `leader` from 1 to 3. The distribution is real, current, and substantially more balanced than
  the finding describes (max count is still `scout=4`, but 6 roles now sit at 2-3 rather than a
  single role dominating). Real, evidenced conclusion: **F4 should be marked substantially
  improved / re-scored, not left as a stale 9/15 open finding** — the specific gaps it named have
  been closed by real, already-landed content (ticket unknown/unattributed — not investigated
  further here, out of scope).
- **F6 (Faction relationships sparse, Gap Risk 8/15, still OPEN)**: original complaint — "14
  relationships for 16 factions (120 directed pairs possible)... Factions without relationships
  default to neutral posture." Real current count: **75** relationships — 62.5% of the 120
  theoretical directed pairs, far exceeding the doc's own Recommended Follow-Up target ("30+
  entries," 25%). Real, evidenced conclusion: **F6 is resolved by real, already-landed content**,
  not merely improved.
- **F1, F2, F5**: already correctly marked RESOLVED in the doc's own Gap Risk Summary; re-verified
  their real current counts still hold (34→34 quest defs not directly re-counted here since quest
  content lives across per-module files, not one central catalog file — out of this ticket's own
  narrower `data/content/` top-level scope; F2's module-type coverage and F5's scenario count of
  14 both independently re-confirmed above).

## Decision: build a lightweight generator script for the numeric counts

**Real, evidenced case for it**: this audit's own numeric drift was severe and silent for ~7
weeks — some categories (recipes, faction relationships) were off by 3-5x, and 2 findings (F4, F6)
sat marked "open" long after the content that would resolve them had already landed, because
nothing re-checked the doc against real data. This is exactly the failure mode
`corpus_registry.yaml`'s own "generated, never hand-transcribed" design already solved for a
different (SimQ-corpus) audience. A small `tools/generate_content_inventory.py` — counting each
category's real entries from `data/content/` and writing a machine-readable snapshot (or directly
regenerating D07's own numeric tables) — closes this gap the same way. The qualitative Gap Risk
scoring/narrative interpretation stays human-authored (that judgment doesn't automate), but the
raw counts themselves should never again silently diverge from real data for 7 weeks undetected.

## Docs Requiring Update

- `docs/audits/D07_content_depth.md`: refresh every numeric table with real current counts (this
  investigation's own table above), fix the Recipes/Simulation-scenarios internal inconsistency,
  and re-score F4/F6 given their real, evidenced resolution/improvement
