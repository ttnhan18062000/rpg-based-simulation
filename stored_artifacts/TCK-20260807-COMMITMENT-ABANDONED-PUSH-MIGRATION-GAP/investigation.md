---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# Investigation: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP

Implemented together with the sibling ticket `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-
GAP` — both are the last 2 real push-migration gaps found during
`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own systematic sweep, both `AgencyScorer`, and share
one implementation (`AgencyShaper`). See that ticket's own `investigation.md` for the shared
`rejection_cascade_tick` half.

## Exact construction logic (confirmed, not assumed)

`event_extractor.py`'s `commitment_abandoned` block (in the same per-entity/per-project loop as
`quest_event`): reads `entity.combat.hp`/`max_hp` from `current_state` (post-apply), checks
`ProjectState.status` (the GENERIC field, not `QuestState.quest_status` — applies to any project
kind, quest or not) for a transition into `ProjectStatus.ABANDONED`, calls
`AbandonmentEvaluator.evaluate_abandonment(hp, max_hp, is_party_in_combat=False,
is_greed_driven=False)` (both flags hardcoded `False` — a pre-existing, disclosed simplification
from `TCK-20260627-P1F-ABANDONMENT-TYPE`, unrelated to this ticket, not touched), and emits when
the resulting classification is NOT `AbandonmentCategory.SURVIVAL`.

## Reconstruction path: hp/max_hp without reading current_state

The one real design question: `event_extractor.py`'s version reads `entity.combat.hp` from
`current_state` (post-apply). Shapers never read post-apply `current_state` per this module's own
architecture. Resolved by reconstructing `hp`/`max_hp` the same way `CombatShaper` already
reconstructs its own `new_hp` (`event_shapers.py:84-87`): `prior_ent.combat.hp +
getattr(combat_upd, "hp_delta", 0)`, and analogously `prior_ent.combat.max_hp +
getattr(combat_upd, "max_hp_delta", 0)` using `CombatUpdate.max_hp_delta` (confirmed this field
exists, `src/core/updates.py:106`). Confirmed via a dedicated test
(`test_commitment_abandoned_uses_reconstructed_hp_from_combat_update`) that a same-tick hp_delta
crossing the `SURVIVAL` threshold (0.2 hp_ratio) is correctly reflected — not just a coincidental
pass on unchanged hp.

`_current_projects()` (added by the sibling `quest_event` ticket) is reused directly for the
`projects` diffing — no new reconstruction helper needed.

## Placement decision: own shaper, own flag (not colocated with NarrativeShaper)

`run_shadow_shapers()` gates delivery per-registry, not per-event. `NarrativeShaper`'s own
`ENABLE_PUSH_EVENT_SHAPERS_QUEST` already defaults `ON` (landed the same session). Colocating
`commitment_abandoned` inside `NarrativeShaper` — even though it shares the same
`_current_projects()`-based iteration — would deliver it live immediately with zero independent
verification window, the exact reasoning that already gave `NarrativeShaper` its own flag apart
from `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`. Created a new `AgencyShaper` class (correct pillar-domain
naming, matching `AgencyScorer`) with its own `AGENCY_SHAPER_REGISTRY`/
`ENABLE_PUSH_EVENT_SHAPERS_AGENCY` flag instead — verified directly (real, unmocked state
construction) before defaulting `ON`, same compressed-verification approach already used for
`quest_event`'s own flag.

## Real-kernel-adjacent verification

Built a real `AuthoritativeState`/`StateUpdate`/`StrategicUpdate` pair (via `V2EntityBuilder`)
with a project transitioning `ACTIVE` → `ABANDONED` at hp=80/100 (a non-SURVIVAL classification).
Confirmed: default mode delivers exactly 1 `commitment_abandoned` from the shaper (0 from the
extractor's rollback branch); explicit `ENABLE_PUSH_EVENT_SHAPERS_AGENCY="OFF"` delivers exactly 1
from the extractor (0 from the shaper). No double-fire in either mode.
