---
artifact_type: investigation
ticket_id: TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION
date: 2026-09-07
---

# Investigation — TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION

## Current Behavior (file:line refs)

- `src/core/state.py:1360`: `information_source_profiles: List[Any] = field(default_factory=list, repr=False, compare=False)`.
- `src/engine/apply.py:415-474` (`ApplyPath.apply_generation()`): the `AuthoritativeState(...)`
  constructor call rebuilding state each tick has **no** `information_source_profiles=` kwarg —
  confirmed via direct read, not present anywhere in that call. It therefore silently resets to `[]`
  (the dataclass default) on every tick advancement, not just after tick 1. Same for
  `pending_information_responses` (also absent from the constructor call) — that omission is
  intentional and documented (see below).
- `src/engine/pipeline.py:199-201`: `source_profiles = getattr(state, "information_source_profiles", [])`
  and `pending_resps = getattr(state, "pending_information_responses", [])` are read fresh from
  `state` every tick and passed into `InformationBeliefPhase.apply(state, source_profiles,
  pending_resps)`.
- `src/domains/information/phase.py:86-107` (Branch 3, `route_new_query`): fires only when
  `actor.id not in entity_updates` (i.e. Branch 2/pending-response processing did not already write
  this actor this tick) AND `actor.self_model.knowledge.unknowns` is non-empty. It calls
  `InformationQueryRouter.route(actor, q, state, profiles)` where `profiles` is exactly the
  `source_profiles` list read above.
- `src/domains/information/phase.py:48-84` (Branch 2, response assimilation): gated purely on
  `resp_by_actor`, derived from the `pending_responses` argument (`state.pending_information_
  responses`) — has **no** dependency on `information_source_profiles` whatsoever. Confirmed by
  direct read: `information_source_profiles`/`profiles` is referenced nowhere in Branch 2's code
  path (lines 48-84).

## Mechanics/Engine Constraints

- `docs/guidelines/intentional_divergences.md` §2.23 ("Single-Fire Compile-Time-Seeded Response",
  `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`) is the **original, authoritative source** of the
  "Bounded" rationale this ticket's Option 1 partially reverses. Read in full: it documents BOTH
  `pending_information_responses` AND `information_source_profiles` as sharing "the same single-fire
  trait" — but the load-bearing verification (`tests/integration/scenarios/
  test_phase5_information_belief_scenarios.py::test_pending_information_response_fires_exactly_once_
  not_carried_forward`, and parity ledger `INFRA-257`) asserts **only**
  `pending_information_responses == []`, never `information_source_profiles`. No existing test
  or parity entry pins `information_source_profiles` to single-fire behavior specifically.
- This means: reclassifying `information_source_profiles` as persistent does NOT contradict any
  existing test assertion, and does NOT require touching `pending_information_responses`'s own
  correct, still-valid Bounded/single-fire treatment (confirmed separately and independently by
  `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD`, which deliberately left both fields
  untouched — its own finding stands for `pending_information_responses`; this ticket narrows the
  scope to `information_source_profiles` only, per its own Out of Scope section).
- **Branch 2/Branch 3 independence, verified directly**: since Branch 2 never reads
  `information_source_profiles`, making that field persistent cannot cause Branch 2 to double-fire —
  Branch 2's firing condition is entirely a function of `pending_information_responses`, which stays
  single-fire. The ticket's own stated risk ("a persistent catalog should not double-fire Branch 2")
  is confirmed structurally impossible given the current code, not merely unlikely.

## Docs Requiring Update

- `docs/guidelines/design_patterns.md`: Pattern 6's "known pitfall" section, cited by this ticket's
  own Related Docs, currently groups `information_source_profiles` under the same Bounded/single-fire
  umbrella as `pending_information_responses` — must be corrected to reflect the split.
- `docs/guidelines/intentional_divergences.md`: §2.23's own text ("The same single-fire trait applies
  to `information_source_profiles`... noted here for traceability only") is now factually superseded
  for `information_source_profiles` specifically — needs a forward-reference correction, plus a new
  entry recording this decision (the reversal itself is a new intentional divergence from the
  original §2.23 framing).
- `docs/parity_ledger/social_narrative.yaml` (or wherever the `route_new_query`/Branch 3 rule is
  tracked — confirmed via `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO`'s own investigation that
  this SimQ rule is `src/simulation_quality/scorers/information.py`'s territory) — must record that
  Branch 3 is now reachable.

## Parity Ledger Overlap (IDs + status)

- `INFRA-257` (`docs/parity_ledger/infrastructure.yaml`): verifies `pending_information_responses`
  single-fire behavior via real calibration (`calibration_hits == 1`). **Not affected** — this
  ticket does not touch `pending_information_responses`.
- No existing parity entry pins `information_source_profiles` specifically to single-fire behavior
  (confirmed via grep across `docs/parity_ledger/*.yaml` for `information_source_profiles` — zero
  hits with a `status` binding it to Bounded).

## Prior Work

- `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` (`tickets/done/`): built
  `data/worlds/unit_information_routing_pilot/` and its matching SimQ profile specifically to prove
  whichever fix this ticket picks — already built, does not need to change.
- `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` (`tickets/done/`): added the 3-field
  carry-forward pattern (`region_loyalty_pressure`/`region_culture_states`/`entity_legend_facts`)
  this ticket's own fix follows structurally — same constructor call site, same
  `prior_state.<field>` passthrough shape.

## Risks and Open Questions

- None outstanding — the real user ratified Option 1 via `AskUserQuestion` (recorded in the ticket's
  own `## Assumptions / Open Questions`). This investigation confirms the chosen fix is safe: Branch
  2/Branch 3 independence rules out the double-fire risk the ticket itself flagged as needing
  verification.

## Anti-Drift Hazards

- Do NOT add `pending_information_responses` to the same carry-forward kwarg list — that would
  violate the still-valid §2.23/INFRA-257 rationale and break
  `test_pending_information_response_fires_exactly_once_not_carried_forward`.
- Do NOT modify `unit_information_routing_pilot`'s world/profile content — it is already correctly
  built to exercise this fix; only recalibration commands should touch it.
