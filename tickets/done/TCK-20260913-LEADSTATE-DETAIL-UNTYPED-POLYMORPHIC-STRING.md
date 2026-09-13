---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING
phase: done
date: 2026-09-13
tags: [cognition, schema]
---

# TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING

## Title
`LeadState.detail` is one untyped `str` field carrying three mutually incompatible real formats, discriminated by nothing — the root cause `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` patched one instance of, not the shape that made it possible

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` fixed one real producer/consumer
mismatch on `LeadState.detail` (`src/core/strategic.py:274-287`) by making `GuildAction.visit()`
emit a parseable coordinate instead of narrative text. That fix corrected one instance; it did not
change the field's own shape, which is what let the mismatch happen at all and will let a similar
one happen again.

Confirmed via a full sweep of every real (non-test) `.detail` read on `LeadState`, not just the one
path the original ticket named, `detail` currently carries **three mutually incompatible
conventions**, discriminated by nothing — not even always by `kind`, since `kind="location"` alone
covers at least two of them:

1. **A parseable `"x,y"` coordinate string.** Real, load-bearing consumers:
   `src/systems/strategic_systems/intelligence.py:408` and `:597`,
   `src/systems/strategic_systems/redirection.py:92`, `src/ai/goals/scorers.py:220` — all four
   resolve a **material blocker** by parsing `detail` into a navigation target. Precedent:
   `src/certification/scenarios.py:485`'s own fixture (`detail="1.0,0.0"`).
2. **An exact `region_id` string**, previously undocumented until this investigation:
   `src/domains/information/phase.py:148` and `src/domains/information/contradiction.py:60` both
   do `lead.detail == region_id` to detect a "searched here, found it safe" contradiction.
3. **Free narrative/prose text** — real for at least one producer
   (`src/domains/information/normalizer.py`, `src/world/providers/information.py`,
   `src/systems/strategic_systems/belief.py`'s two producers all take `detail` as a caller-supplied
   parameter, so their own conformance depends on their own callers, not a fixed shape).

`kind="location"` is shared by conventions 1 and 2 (and, before the fix, 3) — `kind` does not
discriminate which one a given lead uses. Nothing does. This is durable meaning encoded in a
free-form string, which the project's own Durable State Rule
(`CLAUDE.md` § Architecture Rule) exists to prevent: "Do not store durable meaning in `reason`
strings, free-form `metadata`, comments, or temporary local variables." `detail` isn't a comment or
a `reason` string, but it fails the same test — the field's real meaning lives entirely in which
producer wrote it and which consumer happens to read it, with no declared contract connecting them.

`src/systems/strategic_systems/detour.py`'s own `_subjects_match` used to paper over exactly this —
matching a material blocker to a location lead by scanning `detail` for the blocker's subject as a
substring, which worked only when convention 3's prose happened to contain the right word. That
tolerance is gone now that the one narrative producer was fixed (`detour.py` was updated in the same
change to match on `lead.subject` instead, like the other four real consumers already do) — but the
underlying shape that made a substring-scan-over-prose seem like a reasonable thing to write in the
first place is still there for the next producer.

## Scope
**Narrowed after peer review** (the original full-discriminated-type design question below was
investigated first, per instruction, before any code was written): a fresh producer/consumer count
found that Convention 2 (`detail` as a raw `region_id` string, in
`src/domains/information/phase.py`/`src/domains/information/contradiction.py`) has **live
consumers but zero live producers** — nothing in the codebase ever writes a `detail` that is
already a region id. Every real producer of a `kind="location"` lead (`GuildAction.visit()`, after
`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`'s own fix) emits Convention 1
(a parseable `"x,y"` coordinate). This means Convention 2's comparison could never actually match in
any real run — it wasn't just inaccurate, it was structurally dead on arrival.

Given that, the approved fix is narrower than a full discriminated-type redesign: **eliminate
Convention 2 entirely** by having both consumers derive the region they need from the same
coordinate contract every real producer already emits, via the existing
`LegalityServiceV2.get_region_for_position()` (the same position-to-region lookup every other real
consumer in this codebase already uses), rather than inventing a second field or a schema
migration. Concretely:
- New shared helper `src/domains/information/lead_location.py::resolve_location_lead_region_id()` —
  the single, sanctioned place both consumers resolve a lead's coordinate `detail` to a region id.
  Centralizing this (rather than duplicating the parse in both files) directly closes the door on a
  *fourth* incompatible `detail` convention being invented by accident later — the same way a second
  inline copy of Convention 3's substring-scan invited `detour.py`'s now-fixed bug.
- `phase.py`'s `region_danger_seen` synthesis and `contradiction.py`'s
  `BeliefContradictionService.detect()` both call the new helper instead of comparing `lead.detail`
  directly to a region id.
- `GuildAction.visit()`'s own coordinate-detail producer comment cross-references the new helper, so
  the producer/consumer contract is discoverable from either side.
- `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-230` entry (the parity entry covering this
  exact `lead_contradiction` mechanism) updated to cite the new resolution path — and its stale
  `effective_certainty()` citation removed (that function was already deleted per
  `TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`; checked directly via grep
  before trusting the existing citation, not inherited).

The broader discriminated-type design question — formalizing Convention 1 (coordinates) vs.
Convention 3 (free narrative text, still real for `normalizer.py`/`providers/information.py`'s
producers and `belief.py`'s two rumor producers) under one typed shape — is **not** resolved by this
narrower fix and remains open; see Out of Scope.

## Out of Scope
- The full discriminated-type redesign for Convention 1 vs. Convention 3 (parseable coordinates vs.
  free narrative text) remains unresolved. This ticket only eliminates Convention 2 (the dead
  region-id-string comparison) by deriving it from Convention 1 rather than inventing a new typed
  field. A fresh ticket should be filed if/when Convention 1 vs. 3 needs its own design pass —
  not filed here, since narrowing this ticket to the region_id fix was itself the approved scope
  change, not a mandate to also file the next one.
- Re-litigating `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`'s own already-shipped
  fix (`GuildAction.visit()` now emits parseable coordinates; `detour.py` now matches on subject).
  That fix stands regardless of this ticket's outcome.

## Acceptance Criteria
- [x] Convention 2 (`detail` as a raw region-id string) eliminated: both real consumers
      (`phase.py`, `contradiction.py`) now derive the region from the coordinate `detail` every real
      producer actually emits, via the new shared `lead_location.py` helper.
- [x] The elimination is centralized (one helper, not two inline copies) specifically to prevent a
      fourth incompatible `detail` convention from being invented by accident.
- [x] The narrowed evidence (Convention 2 had live consumers, zero live producers) stays visible in
      this ticket body, not just in the fix's commit message.
- [x] `STRAT-230`'s parity-ledger citation updated to the new resolution path; its independently-found
      stale `effective_certainty()` citation corrected in the same edit.
- [x] Real production-path test coverage: unit tests for the new helper itself, plus the two
      existing production-path integration tests (`test_phase5_information_belief_phase.py`,
      `test_phase5_observation_belief_bridge.py`) updated from the dead region-id-string convention
      to the real coordinate convention (they were asserting against a shape no producer ever emits).
- [ ] The broader Convention-1-vs-3 discriminated-type design question remains genuinely open — not
      claimed as resolved by this ticket (see Out of Scope).

## Related Tickets
- `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` (done — fixed the one live
  instance; this ticket is the root-cause shape question that fix's own investigation surfaced)
- `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` (filed alongside the mismatch fix — a
  different, narrower shape question about `GuildAction.visit()`'s resource-id string specifically)

## Related Docs
- `CLAUDE.md` § Architecture Rule § Durable State Rule (the rule this field's current shape fails)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/strategic.py:274-287` (`LeadState`, the shared type)
- Convention 1 (parseable coords): `src/systems/strategic_systems/intelligence.py:408,597`,
  `src/systems/strategic_systems/redirection.py:92`, `src/ai/goals/scorers.py:220`,
  `src/certification/scenarios.py:485` (precedent fixture)
- Convention 2 (region_id): `src/domains/information/phase.py:148`,
  `src/domains/information/contradiction.py:60`
- Convention 3 (free text, caller-supplied): `src/domains/information/normalizer.py`,
  `src/world/providers/information.py`, `src/systems/strategic_systems/belief.py`
- `src/engine/domain/lead_routing.py:59` (uses `detail` directly as a routing target string,
  whichever convention it happens to be)
- `src/systems/strategic_systems/detour.py:250-268` (`_subjects_match`, already updated to stop
  relying on convention 3's coincidental substring match)

## Assumptions / Open Questions
- Whether a typed discriminated shape needs a real `LeadState` schema/migration change or can be
  layered as a typed accessor is the central open question — not resolved here.

## Implementation Notes
- `src/domains/information/lead_location.py` (new): `resolve_location_lead_region_id(lead, state)`
  parses `lead.detail` as `"x,y"` and resolves it via `LegalityServiceV2.get_region_for_position()`.
  Returns `None` (never raises) on a non-coordinate `detail` (logs a `WARNING` naming the lead) or
  when the resolved position falls outside every declared region.
- `src/domains/information/phase.py`: `region_danger_seen` synthesis's guard changed from
  `lead.detail == actor.navigation.region_id` to
  `resolve_location_lead_region_id(lead, state) == actor.navigation.region_id`.
- `src/domains/information/contradiction.py`: `BeliefContradictionService.detect()`'s
  `region_danger_seen` branch changed the same way, comparing against
  `observation.get("region_id")`.
- `src/town/guild.py`: added a cross-reference comment on `GuildAction.visit()`'s coordinate-`detail`
  producer pointing at the new helper, so the producer/consumer contract is discoverable from
  either side without re-deriving it.
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-230`: `v2_evidence` updated to describe the
  new resolution path; removed the stale `effective_certainty()` citation (verified via grep that
  the function no longer exists anywhere in `src/cognition/knowledge_model.py`, deleted by
  `TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`) — a second, independently
  found stale-citation defect, corrected in the same edit rather than inherited.
- Written via the sanctioned `tools/parity_ledger_writer.py::write_entry()` (schema-validating,
  rebuilds the parity index in-process), not a raw YAML edit.

### Corpus measurement (peer-required: real corpus-world evidence, not a fixture-only proof)
Peer required behavioral evidence in a real corpus world before accepting this as closed, having
declined "correct but unreached" claims from unit tests alone in prior tickets. Two short runs
(`quest_dense_frontier`/300 ticks, `frontier_marches`/100 ticks) showed zero location leads reaching
the untested/VAGUE-APPROXIMATE state at all — not a defect in this fix, but because
`GuildAction.visit()` (the sole real producer of coordinate-shaped location leads) never completed a
visit within those short windows. Per peer's own real evidence (D-10's `frontier_living_world`
measurement recorded 4 visits at 500 ticks) this was a tick-budget question, not a reachability one
— re-ran at the budget known to produce visits:

**`frontier_living_world`, seed 42, 500 ticks, two instrumented passes:**
1. `GuildAction.visit()` call/lead-production count: `{'visit_calls': 4, 'leads_produced': 8,
   'lead_kind_location': 8}` — matches peer's own D-10 evidence (4 visits) exactly.
2. Direct `region_danger_seen` guard-condition count (patched into
   `InformationBeliefPhase.apply()`): `{'candidate_location_leads': 300,
   'detail_resolved_to_a_region': 300}` — every untested VAGUE/APPROXIMATE location lead's
   coordinate `detail` resolved to a real region 300/300 times (100%) across the run. The new helper
   is proven correct and reachable in the real production pipeline, not just in a fixture.

**What did NOT fire in this run:** the resolved region never matched the *observing actor's own*
current region in this particular 500-tick run (the `region_match_condition_true` counter, tracking
`resolved == actor.navigation.region_id`, stayed at 0) — so the full `region_danger_seen` synthesis
(which additionally requires an active local scar in that matching region) never completed end to
end in this specific run. This is a real, disclosed, different finding from what was asked: the fix
itself is confirmed correct and load-bearing (leads are produced, coordinates resolve cleanly, 300
real attempts, zero resolution failures), but the *additional* precondition of the observing actor
standing in the same region a location lead points to, while a scar is active there, is rarer than a
500-tick/49-entity run reliably produces. Not investigated further here (would need a longer run or
a purpose-built scenario, both out of this ticket's scope) — recorded as the honest boundary of what
this measurement shows, per peer's explicit instruction to disclose scope rather than overclaim.
9 unrelated `LAW-OCCUPANCY-COLLISION` errors were logged during the run (entity 18 vs. others at
tile (87,50)) — a real, pre-existing `frontier_living_world` data-quality issue, unrelated to this
ticket's change (confirmed: the collision is a navigation/spawn-placement defect, not anything in
the information/belief pipeline this ticket touches). Not investigated or fixed here.

## Test Summary
- New: `tests/unit/domains/information/test_lead_location.py` (5 tests) — coordinate resolves to
  containing region; coordinate outside every region returns `None`; non-coordinate `detail` returns
  `None` and logs a `WARNING`; empty `detail` returns `None`.
- Updated (dead region-id-string convention → real coordinate convention, since no producer ever
  emitted the old shape):
  - `tests/unit/domains/information/test_phase5_belief_contradiction.py` — added
    `test_region_danger_seen_contradicts_lead_via_coordinate_detail`.
  - `tests/unit/domains/information/test_phase5_information_belief_phase.py` — both existing
    `region_danger_seen` production-path tests switched to coordinate `detail`; added
    `test_region_danger_seen_not_fired_for_pre_fix_region_id_shaped_detail` documenting that a
    region-id-shaped `detail` (the old, dead convention) now fails resolution cleanly rather than
    accidentally matching.
  - `tests/unit/domains/information/test_phase5_observation_belief_bridge.py` — same conversion for
    `test_region_danger_seen_routes_through_belief_contradiction_service`.
- Full scope run: `tests/unit/domains/information/`, `tests/integration/domains/information/`,
  `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`,
  `tests/integration/scenarios/test_information_seeking_wiring.py` — 56 passed (pre-rebase), 107
  passed with `tests/tools/test_parity_index_baseline.py`/`test_parity_ledger_writer.py` added
  (post-rebase onto the merge-resolved `flag-propagation-batch`).
- Real corpus-world behavioral measurement (not a fixture) — see Implementation Notes above.

## Files Changed
- `src/domains/information/lead_location.py` (new)
- `src/domains/information/phase.py`
- `src/domains/information/contradiction.py`
- `src/town/guild.py` (cross-reference comment only)
- `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-230`)
- `tests/unit/domains/information/test_lead_location.py` (new)
- `tests/unit/domains/information/test_phase5_belief_contradiction.py`
- `tests/unit/domains/information/test_phase5_information_belief_phase.py`
- `tests/unit/domains/information/test_phase5_observation_belief_bridge.py`

## Completion Summary
Convention 2 (`detail` as a raw region-id string with live consumers and zero live producers)
eliminated by deriving the region from the coordinate `detail` every real producer already emits,
via a new centralized helper (`lead_location.py::resolve_location_lead_region_id()`), rather than
inventing a fourth convention or a schema migration. `STRAT-230`'s parity-ledger citation corrected
in the same edit (both to describe the new resolution path and to remove an independently-found
stale `effective_certainty()` reference). Real corpus-world measurement at the peer-specified
500-tick budget confirms the fix is genuinely reachable and correct in the live production pipeline
(300/300 real coordinate resolutions succeeded, matching the `frontier_living_world` visit count
peer had already measured) — but also surfaces a real, disclosed finding that the full
`region_danger_seen` synthesis's *other* precondition (actor co-located with an actively-scarred,
lead-matching region) is rarer in practice than this run reliably produces; not chased further, out
of this ticket's narrowed scope. The broader Convention-1-vs-3 discriminated-type design question
remains open and unresolved, as scoped.
