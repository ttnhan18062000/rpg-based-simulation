---
artifact_type: plan
ticket_id: TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION
date: 2026-09-07
---

# Plan — TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION

Implements the real user's ratified decision (Option 1, recorded in the ticket's own
`## Assumptions / Open Questions`): reclassify `information_source_profiles` as persistent.

## Ordered Steps

1. **Code change**: `src/engine/apply.py`, `ApplyPath.apply_generation()`'s `AuthoritativeState(...)`
   constructor call (currently ends at `entity_legend_facts=prior_state.entity_legend_facts,` per
   `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD`) — add
   `information_source_profiles=prior_state.information_source_profiles,` immediately after that
   line. Do NOT add `pending_information_responses` — investigation confirms it must stay Bounded
   (Branch 2 depends on it staying single-fire; not touched by this ticket).
2. **Doc correction**: `docs/guidelines/design_patterns.md` Pattern 6's "known pitfall" section —
   split `information_source_profiles` out of the Bounded/single-fire grouping, note it is now
   carried forward like `region_loyalty_pressure`/`region_culture_states`/`entity_legend_facts`.
3. **Doc correction + new entry**: `docs/guidelines/intentional_divergences.md` — add a forward
   reference note to §2.23 ("information_source_profiles's single-fire framing here is superseded,
   see §2.5x") and a new numbered entry recording this decision (old behavior, new behavior,
   rationale: catalog semantics differ from event-queue semantics, evidence: recalibration + new
   test).
4. **Parity ledger update**: whichever `docs/parity_ledger/*.yaml` entry tracks `route_new_query`/
   Branch 3 (confirm exact file/ID during Parity phase via `expected_subsystems_for_files()`) — mark
   reachable, add real test_path.
5. **New regression test**: a direct multi-tick test proving `information_source_profiles` persists
   past tick 1 (mirrors the shape of the `region_loyalty_pressure` equivalent test added by
   `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` — locate that test file at
   Implement/Test time and add a sibling assertion, or a new dedicated test file if no natural sibling
   location exists).
6. **Real recalibration verification** (required by AC, not a unit test):
   - `urban_political`, `unit_information_source`, `unit_information_density` — confirm no pillar
     regression.
   - `unit_information_routing_pilot` — confirm `route_new_query` fires, INFORMATION pillar moves off
     `grade=C events=0`.
7. **Ticket close**: update ticket's `## Assumptions / Open Questions` (already has the ratified
   decision), `## Implementation Notes`, `## Test Summary`, `## Files Changed`,
   `## Completion Summary`.

## Files to Change

- `src/engine/apply.py` (1-line addition to a single constructor call)
- `docs/guidelines/design_patterns.md` (Pattern 6 correction)
- `docs/guidelines/intentional_divergences.md` (§2.23 forward-reference + new entry)
- `docs/parity_ledger/<subsystem>.yaml` (whichever file tracks Branch 3 — confirmed at Parity phase)
- A new or extended test file under `tests/unit/engine/` or `tests/integration/scenarios/` (confirmed
  at Implement time)

## Explicit Scope Guards

- Do NOT touch `pending_information_responses`'s carry-forward status — stays absent from the
  constructor call, per §2.23/INFRA-257's still-valid rationale.
- Do NOT modify `unit_information_routing_pilot`'s world/profile YAML content.
- Do NOT touch `InformationQueryRouter`/`InformationIntentResolver` matching logic — confirmed
  correct as-is by the prior investigation this ticket was split from.
- Do NOT touch the epic ticket or `SEQUENCE.md` — orchestrator's own job.

## Dependency Map

Step 1 must land before Steps 5-6 (nothing to test/recalibrate without the code change). Steps 2-4
are independent of each other and of Step 1's exact wording, but should reference the final,
merged Step 1 diff. Step 7 last.

## Acceptance Criteria Map

- AC1 ("A real decision is made and recorded") — already satisfied by the ratified
  `## Assumptions / Open Questions` entry; this ticket's job is to implement it, not re-decide it.
- AC2 ("`route_new_query` fires... or unreachability formally disclosed") — Steps 1 + 6 (code fix +
  real recalibration proof against `unit_information_routing_pilot`).

## Unresolved Questions

None — the only open decision (which of 3 options) was already ratified by the real user before this
plan was written.

## Deviations

Steps 1-5 executed as planned. Step 6 (real recalibration verification) surfaced a hard blocker not
anticipated by this plan: `unit_information_routing_pilot` recalibration crashes on a separate,
pre-existing bug in `InformationIntentExecutionPhase`/`StrategicWorkQueue.build()` (full trace in the
ticket's own Implementation Notes). Steps 2-4 (doc corrections, parity ledger update) and Step 7
(ticket close) were NOT executed — closing as BLOCKED instead of DONE, since AC2 cannot be honestly
claimed satisfied while the crash stands. The code change (Step 1) and its tests (Step 5) are real,
verified, and kept regardless of this ticket's own final disposition.
