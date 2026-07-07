---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, world, corpus, documentation, taxonomy]
---

# SimQ Corpus Tier Taxonomy

**Ticket:** TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC
**Parent epic:** TCK-20260704-SIMQ-CORPUS-TIERS-EPIC
**Date:** 2026-07-06

---

## Why this taxonomy exists

The driving product philosophy behind the `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` initiative: world
data should eventually exercise every feature the simulation engine supports — not just the
features that already look good — across worlds of deliberately varied scale and composition, so
SimQ scoring becomes an honest diagnostic across the whole corpus, surfacing what's weak rather
than only confirming what's already strong.

Applied naively, this would mean turning every feature on in every world. That makes
troubleshooting *harder*, not easier: if every world exercises every mechanic simultaneously, a
pillar regression can no longer be attributed to a specific mechanic — it could be the mechanic
itself, or an interaction between it and everything else running at the same time.

The fix is to treat the calibration corpus like a test pyramid, mirroring the standard
unit/end-to-end/stress/regression split used for code test suites — but applied to *worlds*
instead of test functions. Each tier has a distinct job:

| Tier | Job | What "good" looks like |
|---|---|---|
| **Unit** | Isolate exactly one gated mechanic | Clean, single-variable attribution when a pillar regresses — you know immediately which mechanic caused it |
| **End-to-end** | Exercise a coherent, realistic scenario combining several systems the way they'd actually interact | Archetype-appropriate richness; interaction effects are expected and meaningful, not noise |
| **Stress** | Push scale/composition to extremes | Confidence the engine holds up outside the "comfortable middle" of entity/region/resource counts |
| **Regression / baseline** | Stay stable | A control group — if this tier's grades move, something genuinely regressed, since nothing about these worlds should be changing |

---

## Tier definitions

### Unit tier

New, small, **synthetic-content-OK** worlds. Each isolates exactly ONE compile-time-gated or
feature-flag-gated mechanic, with everything else left at its inert/default baseline. Narrative
coherence is explicitly not a goal here — these are controlled experiments, not gameplay
archetypes. Template or synthetic content is acceptable and often preferable, since it keeps the
isolation clean.

**Classification criterion:** a world belongs in this tier if it isolates exactly one
Pattern-6-style gated field (see `docs/guidelines/design_patterns.md`'s "Compile-Time Pillar
Activation Pattern") or exactly one feature flag, with every other gated mechanic left at its
existing corpus-wide default.

### End-to-end tier

Existing (or new) **archetype** worlds — the ones meant to represent a real, shippable gameplay
scenario. These get richer, bespoke, archetype-matched content rather than templated content: if a
world's description says "settlement-heavy urban politics," its FACTION/INFORMATION content should
read as urban political content, not a copy-paste of another world's values.

**Classification criterion:** a world belongs in this tier if it extends an existing archetype
world's content richness, or introduces a new world explicitly authored to represent a coherent
gameplay scenario (not an isolated mechanic test, not a scale stress test).

### Stress tier

New worlds specifically authored to fill a **named scale-diversity gap** identified by investigation
— e.g. a world combining a high distinct-faction count with a small map, or resource-node density
decoupled from map size, or gated content combined with a large-scale population. The goal is
coverage of scale/composition combinations that don't occur naturally as a byproduct of other
worlds' authoring, not narrative coherence.

**Classification criterion:** a world belongs in this tier if its primary authoring justification is
"this fills scale-diversity gap X," citing a specific gap named in an investigation document (see
§ below for the gaps currently on record).

### Regression / baseline tier

Worlds that already have committed calibration anchors (`tests/simulation_quality/fixtures/
grade_anchors.json`) and are treated as a stable control group. **This is a "do not touch" policy,
not an oversight or a placeholder waiting to be upgraded.** If a ticket needs to add content to a
regression-tier world, that content addition should be deliberate and tracked (as
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` does for the end-to-end tier), not an incidental
side effect — and any resulting anchor drift must be re-verified and re-committed with attribution,
following the precedent `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4a established.

**Classification criterion:** a world belongs in this tier by default the moment it has at least one
committed entry in `grade_anchors.json`, unless and until a ticket deliberately promotes it into
active end-to-end-tier content work.

---

## Current tier mapping (as of 2026-07-07)

The original 10 worlds under `data/worlds/` are **Regression / baseline tier**. Two new
**Unit-tier** worlds now exist (`unit_faction_tension`, `unit_information_source`, added by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`) — see
`docs/simulation_quality/eval_matrix_results.md`'s "Unit-Tier Isolation Worlds" section for their
grade tables. No world has yet been promoted into deliberate end-to-end-tier content expansion
(scoped by ticket 7 of this epic, not yet implemented), and no stress-tier world exists yet (scoped
by ticket 8, not yet implemented).

| World | Tier | Notes |
|---|---|---|
| `wilderness_survival` | Regression/baseline | 11 entities, 4 regions — smallest world in the corpus |
| `sandbox_world` | Regression/baseline | 18 entities, 3 regions |
| `highland_traverse` | Regression/baseline | 18 entities, 5 regions |
| `urban_political` | Regression/baseline | 30 entities, 3 regions — the only world with any FACTION/INFORMATION/self-model content populated today |
| `dungeon_crawl` | Regression/baseline | 32 entities, 4 regions |
| `swamp_border_world` | Regression/baseline | 26 entities, 4 regions |
| `simq_routing_test` | Regression/baseline | 30 entities, 3 regions — the only world with `ENABLE_ADVENTURE_ROUTING=ON`, purpose-built as a minimal AGENCY calibration world (not a shipped gameplay archetype) |
| `frontier_living_world` | Regression/baseline | 46 entities, 7 regions |
| `generated_frontier_3_42` | Regression/baseline | 44 entities, 6 regions — procedurally generated |
| `frontier_extended` | Regression/baseline | 56 entities, 10 regions — largest world in the corpus |
| `unit_faction_tension` | Unit | 18 entities, 3 regions — isolates FACTION only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO) |
| `unit_information_source` | Unit | 16 entities, 1 region — isolates INFORMATION only (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO) |

Full per-world entity/region/resource/quest counts and module composition are documented in
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2 — this doc cites that
table as its evidentiary source rather than duplicating it, since the investigation's numbers are
the audited, evidence-backed original and should not risk drifting out of sync with a second copy.

---

## Named scale-diversity gaps (stress-tier candidates)

Per `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2, the following
scale/composition combinations are **not currently represented** by any world in the corpus, and are
the concrete candidates a stress-tier world should cite when justifying its authoring:

1. **Large faction count + small entity/region footprint.** No world combines a high distinct-faction
   count (6-9) with a small map — faction density and world size currently move together.
2. **High resource-node density with a small map** (or the inverse: a sprawling map with sparse
   resources). Node-per-region density is currently roughly flat (1.3-1.75) across the corpus
   regardless of overall scale.
3. **Pattern-6 gated content (FACTION/INFORMATION/self-model) combined with a large-scale
   population.** The only world with any of this content populated (`urban_political`) is
   mid-scale; there's no data point for how these mechanics behave at `frontier_extended`'s scale
   (56 entities, 10 regions) or `wilderness_survival`'s (11 entities, near-zero settlement
   structure).
4. **A routing-capable (AGENCY-active) world that is also a "real" gameplay archetype**, as opposed
   to `simq_routing_test`'s purpose-built minimal-calibration framing.
5. **Quest density decoupled from entity count.** Quest-def count currently scales almost linearly
   with entity count across the corpus; no world deliberately decouples these axes.

`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` is scoped to address a subset of these gaps — it is not
required to close all five in one ticket.

---

## Classifying a future world addition

When authoring a new world (or substantially extending an existing one), classify it using this
decision order:

1. **Does it isolate exactly one gated mechanic, with everything else at baseline, using
   template/synthetic content?** → **Unit tier.**
2. **Does it fill one of the named scale-diversity gaps above (or a newly-investigated one)?** →
   **Stress tier.**
3. **Does it extend an existing archetype world's content richness, or introduce a new world meant
   to represent a coherent, shippable gameplay scenario?** → **End-to-end tier.**
4. **Does it already have a committed `grade_anchors.json` entry, with no ticket currently
   deliberately extending its content?** → **Regression/baseline tier** — leave it alone unless a
   ticket explicitly promotes it.

A world should not straddle multiple tiers at once. If a stress-tier world happens to also exercise
a Pattern-6 mechanic (gap 3 above explicitly combines scale with gated content), classify it as
stress tier and note the mechanic it also happens to exercise — the primary tier is determined by
its *authoring justification*, not by every mechanic it happens to touch.

---

## Related documents

- `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` — full evidentiary
  source for the mechanic inventory (§1) and scale diversity tables/gap analysis (§2) this doc
  summarizes
- `docs/guidelines/design_patterns.md` — Pattern 6, "Compile-Time Pillar Activation Pattern"
- `docs/simulation_quality/eval_matrix_results.md` — calibration grade tables and AC6/exception
  history for the regression-tier worlds
- `docs/simulation_quality/quality_scoring_contract.md` — SimQ 10-pillar scoring contract
- `docs/plans/audit_fix_plan.md`
- `tickets/todos/simq-corpus-tiers/SEQUENCE.md` — ordering rationale for this epic's 10 child
  tickets, several of which author worlds this taxonomy classifies
