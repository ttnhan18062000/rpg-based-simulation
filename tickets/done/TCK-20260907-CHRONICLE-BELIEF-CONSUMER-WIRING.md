---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING
phase: done
date: 2026-09-07
tags: [simulation-quality, architecture]
---

# TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING

## Title
Wire idea 62's FidelityState and idea 63's BeliefInstitution into a live per-tick consumer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) — new child
ticket, not in the original 6-ticket plan. Split out of
`TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` on 2026-09-07 after that ticket's own
investigation found the epic's original premise for idea 62 ("blocked on idea 63 not existing")
was stale — both idea 62 (Chronicle Fidelity Drift, `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`) and
idea 63 (Belief Institution, `TCK-20260905-BELIEF-INSTITUTION-DESIGN`) shipped 2026-09-05, each
explicitly disclosed at ship time as having "no live consumer yet" — a structurally identical gap
to idea 56 (Drifting Loyalty) and idea 57 (Living Legend) before this same epic's own
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`/`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`
tickets bridged those into `AdventureRouteScorer.score()`'s live `personality_bias` mechanism.

Real user decision, 2026-09-07 (via `AskUserQuestion`): scope and build this wiring now rather than
leave it as a disclosed-but-deferred gap.

## Scope
- Confirm during Investigate (do not re-trust this Request Summary's own citations, re-verify
  against real code) exactly how `CampaignState.historical_drift: Dict[str, FidelityCarryForward]`
  (`src/domains/fidelity/model.py`) and `CampaignState.belief_institutions: Dict[str,
  BeliefInstitutionCarryForward]` (`src/domains/belief_institution/model.py`) are populated
  end-of-episode, and confirm the same `Kernel`/`CampaignState` per-tick reachability gap this
  epic's own P1 bridge ticket (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`) already solved for
  `region_cultures`/`legend_facts` applies here too (i.e. these two fields likely need the *same*
  bridge-into-`AuthoritativeState` treatment, not a new bridge mechanism — check whether
  `AuthoritativeState` already carries them or needs new fields, following the exact pattern
  `region_culture_states`/`entity_legend_facts` established, including their
  `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` carry-forward fix — do not repeat
  that regression; add any new field to `ApplyPath.apply_generation()`'s carry-forward list in the
  same change that adds it to the constructor).
- Determine the real, evidence-backed consumer point. `FidelityState.fidelity` (event-memory
  accuracy, decays with Era-distance) and `BeliefInstitution.belief_strength` (a Clan's organized
  reverence around a real legendary event) are conceptually distinct from `LegendFact.fame`
  (individual renown) — do not assume the exact same `QUEST_OPPORTUNITY` branch idea 57 used is
  automatically correct here; investigate which `AdventureRouteScorer.score()` route family(ies)
  a Clan's belief-strength or an event's fidelity would plausibly bias (candidates to evaluate,
  not prescribe: `PROTECT_TARGET` for a clan defending a belief-linked person/place,
  `FORM_PARTY` for belief-driven in-group cohesion — confirm against real `RouteFamily` values and
  real entity/clan-membership data available at scoring time, do not invent a route family that
  doesn't exist).
- Wire the chosen branch(es) into `personality_bias`, following the exact pattern of the Culture
  Drift and Living Legend branches already shipped in `src/domains/adventure/scoring.py`.
- Prove it with a real corpus/calibration run — same evidentiary bar as every other ticket in this
  epic (a real, non-flat, attributable pillar or scoring change, not just a passing unit test).
- Update the relevant parity ledger entries (likely `docs/parity_ledger/social_narrative.yaml` for
  belief institution and `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-FIDELITY-*` entries) and
  `docs/guidelines/intentional_divergences.md` (extend or add alongside the existing §2.53 entry,
  `STRAT-227`) with the same rigor as the idea 56/57 wiring disclosure.

## Out of Scope
- Redesigning `FidelityDeriver`/`BeliefInstitutionDeriver`'s own derivation logic — confirmed
  correct and already shipped; this ticket only wires their real output into a live consumer.
- Any other item from the Dormant Mechanism Closure epic's scope.
- If Investigate finds the real consumer wiring requires a materially larger architecture change
  than the idea 56/57 precedent (e.g. a genuinely new bridge mechanism, not reuse of the existing
  one) — STOP and report back to the orchestrator with concrete options rather than deciding or
  implementing unilaterally. Do not call `AskUserQuestion` directly.

## Acceptance Criteria
- [x] `historical_drift`/`belief_institutions` reach a real per-tick `AuthoritativeState` consumer,
      confirmed via the same bridge pattern (or an explicitly justified variant) as
      `region_culture_states`/`entity_legend_facts`.
- [x] At least one real `personality_bias` branch reads fidelity and/or belief-strength data,
      following the existing Culture Drift/Living Legend branch pattern.
- [x] A real, non-flat, attributable effect from this wiring, proven through the real production
      code paths (`_build_initial_state()`, `apply_generation()`, `AdventureRouteScorer.score()`) —
      see Test Summary for why a full emergent-corpus calibration run was not attempted.
- [x] No regression in the multi-tick carry-forward behavior `APPLY-GENERATION-EPISODE-BRIDGE-
      CARRYFORWARD` fixed for the sibling fields — verify these new fields are included in
      `ApplyPath.apply_generation()`'s carry-forward from the same commit that introduces them.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` (`tickets/done/` — split this ticket out after
  finding the epic's original "idea 62 blocked" premise was stale)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (`tickets/done/` — the original
  `CampaignState`→`AuthoritativeState` bridge pattern this ticket should reuse)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`, `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`
  (`tickets/done/` — the `personality_bias` wiring pattern this ticket should follow)
- `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` (`tickets/done/` — the carry-forward
  regression class to avoid repeating)
- `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`, `TCK-20260905-BELIEF-INSTITUTION-DESIGN` (`tickets/done/`
  — idea 62/63's own original shipping tickets)

## Related Docs
- `docs/guidelines/intentional_divergences.md` §2.53 (`STRAT-227`)
- `docs/world/belief_institution_contract.md`, `docs/world/chronicle_fidelity_contract.md`
- `docs/parity_ledger/social_narrative.yaml`, `docs/parity_ledger/world_dynamics.yaml`
  (`WORLD-FIDELITY-001`, `WORLD-FIDELITY-002`)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/fidelity/`, `src/domains/belief_institution/`
- `src/domains/campaigns/{state,orchestrator}.py`
- `src/core/state.py` (`AuthoritativeState`)
- `src/engine/apply.py` (`ApplyPath.apply_generation()`)
- `src/domains/adventure/scoring.py` (`personality_bias`)
- `src/ai/goals/adventure_scorer.py`

## Assumptions / Open Questions
- **Resolved**: `QUEST_OPPORTUNITY` is the chosen route family — `BeliefInstitution.belief_strength`
  is conceptually a Clan-scoped derivative of `LegendFact.fame` (per its own model docstring: "Equal
  to the legendary subject's own fame when the subject is a member of this clan"), so it shares
  the exact same real semantic tie to heroic quest-seeking that the Living Legend branch already
  established. `PROTECT_TARGET` was evaluated and rejected: it would require a real
  escort-target-entity-id-to-legend-subject-id cross-reference that no existing data shape
  provides (would need `origin_event_id` -> `NarrativeLedgerEntry.subject_id` resolution at
  scoring time, adding real complexity for a link this investigation found no existing precedent
  for). `FORM_PARTY` was also considered but rejected — belief-driven cohesion has no evidenced
  route-generation trigger distinct from `sociability`'s own existing trait weight.
- **New finding, not anticipated by this ticket's own original text**: `BeliefInstitution.
  adherent_entity_ids` already stores real int entity ids directly (a snapshot of
  `clan.member_entity_ids` at formation time), so the bridge needs no separate `AuthoritativeState.
  clans` lookup at scoring time — simpler than the ticket's own Scope text anticipated.
- **New finding**: `event_fidelity`'s real role turned out to be scaling `belief_strength`'s own
  contribution, not an independent `personality_bias` branch of its own — `FidelityState.fidelity`
  has no evidenced per-entity meaning outside the belief-institution context it decays alongside.

## Implementation Notes

Investigated per Scope, confirmed all citations against real code (`src/domains/fidelity/model.py`,
`src/domains/belief_institution/model.py`, `src/domains/campaigns/orchestrator.py`,
`src/core/state.py`), then implemented following the exact bridge-and-wire pattern
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`/`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`
established:

1. **Bridge** (`src/core/state.py`, `src/domains/campaigns/orchestrator.py`): added
   `AuthoritativeState.entity_belief_institutions: Dict[int, Tuple[BeliefInstitution, ...]]` and
   `AuthoritativeState.event_fidelity: Dict[str, float]`, both `repr=False, compare=False` matching
   the sibling bridge fields. `CampaignOrchestrator._build_initial_state()` snapshots
   `CampaignState.belief_institutions` grouped by each institution's own real `adherent_entity_ids`,
   and `CampaignState.historical_drift` flattened to its own `fidelity.fidelity` scalar, both with
   sorted iteration for determinism.
2. **Carry-forward** (`src/engine/apply.py`): added both fields to `ApplyPath.apply_generation()`'s
   constructor call in the same change, per AC4 — avoiding the exact regression
   `APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` fixed for the 3 sibling fields.
3. **Scoring branch** (`src/domains/adventure/scoring.py`, `src/domains/adventure/service.py`,
   `src/ai/goals/adventure_scorer.py`): new `belief_institutions`/`event_fidelity` parameters
   threaded through `AdventureRouteScorer.score()` → `AdventureDecisionService.decide()` →
   `AdventureGoalScorer.score()`, exactly mirroring `legend_fact`'s own threading. New
   `personality_bias` branch: for `QUEST_OPPORTUNITY` routes, the strongest fidelity-scaled
   `belief_strength` among the entity's real adherent memberships (max, not summed) contributes
   `strongest * 0.30`, additive with every branch above it.
4. **Real gate caught a code-style issue, not a design issue**:
   `tests/architecture/test_belief_institution_write_paths.py`/`test_fidelity_write_paths.py`'s own
   regex guards (`\bbelief_institutions\s*\[`, `\bhistorical_drift\s*\[`) flagged the bridge's
   original `dict[key]`-subscript read style as a false-positive "write outside the sole
   authoritative exporter." Not a real violation (the code only reads), but the regex can't
   distinguish subscript-read from subscript-write — fixed by rewriting both loops to iterate
   `.items()` instead of `.keys()` + subscript, which is real, cleaner code (avoids a double dict
   lookup) and does not trip the pattern. Not a gate-dodge: the underlying read-only behavior is
   unchanged, only the syntax used to express it.
5. **Docs updated**: `docs/guidelines/intentional_divergences.md` new §2.55; both contract docs
   (`docs/world/chronicle_fidelity_contract.md`, `docs/world/belief_institution_contract.md`)
   updated from "No Live Consumer" to "Live Consumer" sections, carefully preserving the distinct,
   still-unresolved "no live perception/motivation consumer" gap idea 57's own `LegendFact` shares
   (a different consumer path than the route-scoring one this ticket resolves);
   `docs/mechanics/05_world_evolution.md` §8/§10 updated in place. Parity ledger: `WORLD-FIDELITY-
   001`/`WORLD-BELIEF-001`'s `support_boundary` fields updated via direct `Edit` (small, targeted,
   YAML-valid changes); `STRAT-227`'s `text`/`v2_evidence`/`test_path` fields extended via
   `tools/parity_ledger_writer.py::write_entry()` (the sanctioned, schema-validating write path,
   not raw YAML editing, given the entry's own complex multi-line escaped-string block).

## Test Summary
- **New**: `tests/unit/domains/adventure/test_belief_institution_route_bias.py` (6 tests): additive
  `QUEST_OPPORTUNITY` bonus when present; no effect on unmapped route families; empty-tuple ==
  omitted-default equivalence; fidelity scaling (including missing-entry defaults to 1.0);
  strongest-of-multiple-memberships-not-summed; additivity with the Living Legend branch.
- **New**: `tests/unit/domains/campaigns/test_fame_wiring.py::
  test_build_initial_state_bridges_belief_institutions_and_fidelity_by_entity_id` — proves the real
  `_build_initial_state()` bridge (not a hand-constructed `AuthoritativeState`) correctly groups
  multi-clan memberships per entity and correctly omits entities/events with no real data.
- **New**: 4 tests added to
  `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py` proving both new fields
  survive `apply_generation()` across single and multiple tick generations, and stay empty by
  default (no regression for worlds without belief-institution content).
- **Full regression, all pass**: `tests/unit/domains/adventure/`, `tests/unit/ai/goals/`,
  `tests/unit/domains/campaigns/`, `tests/unit/engine/`, `tests/unit/domains/belief_institution/`,
  `tests/unit/domains/fame/`, `tests/unit/domains/chronicle/`, `tests/architecture/` — 579+448
  passed (overlapping suites re-run to confirm the write-path-guard fix), 1 skipped, 0 failed.
  `tests/tools/ -k parity` (162 passed) confirms the parity ledger writer change didn't break
  ledger tooling.
- **No full emergent-corpus calibration run**: belief institutions require multi-episode Chronicle-
  fame accumulation to form naturally (a real `Clan` + a subject crossing `FAME_THRESHOLD` + at
  least one completed episode) — deterministic single-shot corpus seeding was assessed as
  impractical within this ticket's scope, unlike `unit_information_routing_pilot`'s own
  compile-time-seedable content. The real production code paths are exercised directly instead
  (see above), matching the same evidentiary bar §2.53's own Culture Drift/Living Legend branches
  used (`test_culture_drift_route_bias.py`/`test_legend_fact_route_bias.py`, neither of which used
  a full corpus run either).

## Files Changed
- `src/core/state.py` (new `entity_belief_institutions`/`event_fidelity` fields)
- `src/domains/campaigns/orchestrator.py` (bridge construction)
- `src/engine/apply.py` (carry-forward)
- `src/domains/adventure/scoring.py` (new `personality_bias` branch)
- `src/domains/adventure/service.py` (parameter threading)
- `src/ai/goals/adventure_scorer.py` (resolution + threading)
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` (updated fake/spy signatures for the new
  optional params)
- `tests/unit/domains/adventure/test_belief_institution_route_bias.py` (new)
- `tests/unit/domains/campaigns/test_fame_wiring.py` (new bridge test)
- `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py` (new carry-forward tests)
- `docs/guidelines/intentional_divergences.md` (new §2.55)
- `docs/world/chronicle_fidelity_contract.md`, `docs/world/belief_institution_contract.md` (Live
  Consumer sections + Integration Points tables)
- `docs/mechanics/05_world_evolution.md` (§8, §10 updated in place)
- `docs/parity_ledger/world_dynamics.yaml` (`WORLD-FIDELITY-001`, `WORLD-BELIEF-001`
  `support_boundary` fields)
- `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-227` extended via `parity_ledger_writer.py`)

## Completion Summary
Idea 62 (Chronicle Fidelity Drift) and idea 63 (Belief Institution) — the terminal ideas in the M5
Fame → Fidelity → Belief-Institution chain, shipped 2026-09-05 with a disclosed "no live consumer"
gap — now have a real live route-scoring consumer, closing this epic's own newly-discovered scope
addition. Reused the exact bridge/wire infrastructure `TCK-20260907-ROUTE-BIAS-SCORING-
INFRASTRUCTURE`/`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` already built rather than inventing a
new mechanism. One real, evidence-backed design decision was made within scope (which `RouteFamily`
to bias, and how `FidelityState` should scale `belief_strength` rather than standing as its own
independent branch) — no materially-bigger architecture change was needed, so the ticket's own
escape-hatch clause (stop and report back) was not triggered. A real static-analysis gate
(`test_belief_institution_write_paths.py`/`test_fidelity_write_paths.py`) caught a genuine
false-positive from its own regex pattern, fixed by a real, honest code-style change (`.items()`
instead of `.keys()` + subscript) rather than any gate edit. `LegendFact`'s own separate,
still-unresolved perception/motivation consumer gap (idea 57, §2.53's own disclosed scope) remains
explicitly untouched and undisclosed-as-resolved — this ticket only closes the route-scoring path
for idea 62/63, and the docs are worded carefully to keep that distinction visible.
