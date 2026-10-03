---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS
artifact_type: investigation
tags: [simulation-quality, economy, adventure]
---

# investigation.md — TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS

## Current Behavior (file:line refs)

`AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py:232-233`):
```python
final_score = urgency + benefit + personality_bias + plan_advance_bonus + confidence_bonus - risk_penalty - blocker_penalty
final_score = round(max(0.0, final_score), 4)
```

`blocker_penalty` (`scoring.py:227-229`): flat `2.0` whenever `route.blockers` is non-empty — no
partial credit, no gradient. Given craft/buy routes' typical benefit (~0.3) + personality_bias
(~0.1-0.2) + confidence_bonus (~0.15), a 2.0 blocker penalty always drives the raw score deeply
negative, and `max(0.0, ...)` clamps it to exactly `0.0` — this is the mechanism behind the
observed "craft_upgrade/buy_upgrade always score 0.0" pattern from
`TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`'s Factor 2 finding (0/492, 0/342 selections).

**Where `route.blockers` gets set** (`AdventureRouteGenerator.generate()`,
`src/domains/adventure/generator.py:54-68`): for each opportunity's `requirements`, only two
requirement kinds are actually checked and can add a blocker string:
- `has_gold`: blocked if `entity.inventory.gold < req.quantity`
- `has_item`: blocked if the entity's inventory doesn't hold enough of `req.subject`

A third requirement kind, `recipe_known`, is attached to every craft opportunity
(`src/world/providers/services.py:55`) but is **never checked** by the generator's blocker loop —
silently ignored, not a bug affecting this ticket's question (it just means recipe-knowledge is
never itself a blocker; gold/materials are the only real gating requirements).

**Where craft/buy opportunities actually come from** (`src/world/providers/services.py:50-111`):
- `craft_item`: requires `has_gold: recipe.gold_cost` + `has_item: {material_id: qty}` for every
  material the recipe needs (`recipe.requires_items`).
- `buy_item`: requires `has_gold: 15` + `inventory_space: 1` (inventory_space is not one of the two
  blocker-checked kinds, so it never blocks on its own).

**The causal chain, traced concretely from a real sample** (2026-08-05, `hero_guild_routing`
seed=42, DEBUG-mode `decision_trace.jsonl`, entity 23, tick 0): `craft_upgrade` route present with
`benefit=0.3` (`estimated_reward=30.0` — the `has_material_blocker=False` branch of
`services.py:66`, i.e. this entity had no active material blocker at generation time) but
`score=0.0`. Working the formula backward: `0.3 (benefit) + ~0.125 (industry×0.25 personality_bias)
+ 0.15 (confidence_bonus) - 0 (risk, craft has estimated_risk=0.0) - blocker_penalty = 0.0` only
holds if `blocker_penalty=2.0` — i.e. `route.blockers` was non-empty for this specific recipe
(entity 23 lacked the gold or materials for *that* recipe, even though it had no *general* material
blocker recorded in `entity.strategic.blockers`).

## Mechanics/Engine Constraints

None from the Mechanics Bible directly — `AdventureRouteScorer` is calibration/tuning logic
(`docs/simulation_quality/quality_scoring_contract.md`'s domain, not `docs/mechanics/`). The
relevant constraint is architectural: `docs/guidelines/design_patterns.md`'s general "decision
logic reads state, does not fabricate it" principle applies directly to this ticket's central
question — a fix must not make the scorer *pretend* an entity has resources it doesn't.

## Docs Requiring Update
- `docs/simulation_quality/current_state.md`: Finding 2's Factor 2 description needs to be replaced
  with this ticket's root-cause finding (crafted/bought are blocked by lack of gold/materials, not
  scorer bias) once this investigation's conclusion is confirmed via Plan.
- `docs/audits/D20_simq_quality_status_review.md`: same Factor 2 update, Item B2 candidate entry.

## Parity Ledger Overlap

None. This is calibration-domain logic (`src/domains/adventure/`), not a parity-ledger-tracked
subsystem — confirmed via `docs/parity_ledger/` grep for `AdventureRouteScorer`/`craft_upgrade`:
no hits.

## Prior Work

- `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (done) — established the 0/492, 0/342
  empirical finding this ticket investigates the cause of.
- `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` (done) — found content-volume additions don't move
  ECONOMY, consistent with this investigation's finding that the blocker is resource *possession*
  (gold/materials), not opportunity *availability*.
- `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` (done) — fixed the harvest arrival-transition
  bug; confirmed (this session, 2026-08-05) to have zero corpus-wide effect, since
  `resource_harvested` never fires at all. This investigation's finding explains *why* that matters
  for craft/buy specifically: without harvesting, entities never accumulate the gold/materials
  craft/buy opportunities require, so those routes are correctly, not spuriously, blocked.

## Risks and Open Questions

**Primary finding, high confidence:** craft_upgrade/buy_upgrade's 0-selection pattern is a
**correct reflection of entity state**, not a scorer miscalibration. Entities that never harvest
resources or earn gold (the same root cause `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`'s
Factors 1/3 already track) never satisfy craft/buy's `has_gold`/`has_item` requirements, so the
flat `blocker_penalty=2.0` correctly zeroes their score every time. This is the scorer working as
designed — a blocked route should score low.

**Open question not fully resolved by this investigation:** is `blocker_penalty=2.0`'s flat,
non-gradient shape itself defensible, independent of the harvesting question? E.g. an entity
missing 1 gold of a 50-gold requirement scores identically to one missing all 50 — arguably a real
design question (should "almost affordable" score higher than "wildly unaffordable" to guide
entities toward achievable goals?) but this is a general property of the blocker-penalty mechanism
affecting *every* route family with requirements, not specific to craft/buy — **explicitly out of
this ticket's scope** (Out of Scope: "Any scoring change to form_party/gather_resource themselves").
Noted for a possible future ticket, not pursued here.

**Consistent with the user's explicit 2026-08-05 guidance** (no forced routes): this finding
confirms a fix should NOT touch `AdventureRouteScorer`'s weights or blocker logic — doing so would
force craft/buy to be selected by entities that genuinely cannot afford them, manufacturing an
unrealistic route exactly as warned against. The real, upstream fix (if pursued) is getting
entities to harvest/earn gold in the first place — already tracked as Factor 1
(`ENABLE_ADVENTURE_ROUTING` default) and the broader goal-generation chain, not new work for this
ticket to duplicate.
