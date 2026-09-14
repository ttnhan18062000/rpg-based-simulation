# Investigation — TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY

## Re-verified origin claim
`region_data`/`enemy_data` still empty at every real `CapabilityContext` construction site.
`travel_regions` still has zero production construction sites — unchanged since the origin ticket.

## Belief-source search (never world truth, per instruction)

Two real, live-code candidates found. Both confirmed unreachable in real runs today.

**Chain 1 — lead-belief path**: `GuildAction.visit()` → `entity.strategic.leads` →
`BeliefCycleSystem.process_observation()` (`src/systems/strategic_systems/intelligence.py:416`,
the sole real caller). Blocked twice:
1. `ENABLE_GUILD_QUEST_GENERATION`'s default doesn't propagate to `state.feature_flags`
   (`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS`) — no lead is
   ever granted in a real run.
2. Even with a lead present, `process_observation()` sits after a `float()` parse on `lead.detail`
   that throws for every guild-produced lead's narrative-text format
   (`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`) — confirmed by reading the
   exact code path in `intelligence.py`.

**Chain 2 — combat-risk belief path**: `CombatEngagementPhase.apply()`
(`src/domains/combat_engagement/phase.py`) writes a real, tested `BeliefEntry`
(`id="combat_risk"`, `claim=<RiskLevel>`, `certainty=<death_risk>`) for the actor's own risk from
the nearest hostile. Gated `ENABLE_COMBAT_ENGAGEMENT`, default `OFF`
(`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`, open, pre-existing, unrelated to this batch).
Shape mismatch even if the flag were on: single per-actor scalar, not the per-`enemy_id`/
per-`region_id` keyed dicts `enemy_data`/`region_data` need.

`KnowledgeFact` (origin ticket's own unproven third candidate): confirmed separately at zero real
writes.

## Disposition (first pass, superseded below)
Do not wire either source now — both would produce code that compiles, has real test coverage, and
never fires in a real run. Stays `BLOCKED` on the two named chains, not `DONE`.

---

## Re-investigation, same day, after Chain 1 actually unblocked

`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` and
`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` both landed;
`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` closed `DONE`. Chain 1 is
genuinely reachable now. Re-checked whether it actually *feeds* either field — reachable and
feeding are different questions, and the answer diverged sharply for the two fields.

### `enemy_data`: no producer exists, on either side

Grepped every real `BeliefEntry(` construction site in `src/` (excluding tests): exactly 3.
- `belief.py:148` (`process_rumor`): `subject=rumor_subject` — caller-supplied, real examples are
  resource/location names (`"iron_ore"`, `"goblin_camp"`), never confirmed to carry an enemy kind.
- `belief.py:181` (`process_observation`, Chain 1's own producer): `subject=lead.subject` — for the
  one real producer of `kind="location"` leads (`GuildAction.visit()`), always `"iron_ore"`.
- `phase.py:68` (`build_combat_risk_belief`, Chain 2): `id="combat_risk"` fixed, single scalar.

None captures "I fought a `<kind>`" anywhere. This isn't a wiring gap — filed
`TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` for the real gap: no mechanism anywhere
produces this data.

### `region_data`: real derivation path exists, but no real caller — and the natural one is dead

A Chain-1 belief's `claim` is a real coordinate string (`lead.detail`, now parseable per this
batch's own ticket 2 fix). `src/engine/legality.py:44`,
`LegalityServiceV2.get_region_for_position(pos, state) -> Optional[RegionState]`, is real, existing,
widely-used machinery (used by `src/world/ecology.py`, `creature_territory.py`, `boss.py`,
`camp.py`, `regional_sovereignty.py`) that resolves a position to a real region. So `region_data`
COULD be derived: `{region_id: {"danger_rating": <from belief certainty/outcome>}}`.

But `context.travel_regions` (`capability_estimate.py:39`) still has zero real construction sites
— re-confirmed via the same grep as the origin investigation, unchanged. Before inventing a caller,
applied the declared-intent test: does an existing route family/decision point already have "going
somewhere" as its whole point? `RouteFamily.SCOUT_LOCATION` (`schema.py:27`) is exactly that shape
— `mapper.py:41` maps it to `ObjectiveKind.REACH_LOCATION` — but grepping every real
`AdventureRouteOption(` construction site (`generator.py`, `service.py`) confirms `SCOUT_LOCATION`
is referenced only in mapping/scoring/impact-tracking tables (`mapper.py`, `scoring.py`,
`src/domains/information/route_impact.py`, `src/domains/campaigns/forbidden.py`) — **never actually
generated**. The one declared, natural caller placement doesn't exist in practice.

`GATHER_RESOURCE`/`CRAFT_UPGRADE` are the only two real route families that consult
`CapabilityEstimateService` today (`scoring.py:368-416`), and neither is about travel.
`DetourSuggestionSystem` (`detour.py`) is a real, live "decide where to go" mechanism (touched in
this batch's own ticket 2) but never consults `CapabilityEstimateService` at all — wiring it in
would be a new connection, not completing a declared one.

**A caution surfaced but not acted on** (per peer review, before this was even reached): a
Chain-1 belief's SUCCESS outcome means "the lead's claim was confirmed" (a hostile was found where
rumored), not "this region is generally safe" — mapping belief outcome to a region danger_rating
would itself be a design decision, not a mechanical derivation. Moot for this closure since no
caller placement survived the prior test, but worth recording for whoever picks this up once a real
caller exists.

## Disposition (final)
Stays `BLOCKED` on both fields, for corrected reasons. `enemy_data`: no producer exists anywhere,
filed as its own ticket. `region_data`: a real derivation path exists, but no real caller does, and
the one route family that would supply one is itself dead — declined to invent a placement.
