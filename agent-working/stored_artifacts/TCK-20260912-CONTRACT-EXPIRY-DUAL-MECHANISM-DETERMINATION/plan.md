# Plan — TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION

## Resolution (2026-09-13): Option A chosen and implemented

Peer decided Option A directly from the relative-cost writeup below (see the ticket's own
Implementation Notes for the full writeup and the decisive finding: Option B's premise — "the full
model is already implemented there" — was false, since `process_active_contracts()` carried its
own missing-other-party bug). Implemented with one correction to Candidate Plan A's own step 2
below: rather than writing new consequence logic into `transition_contract()` or a fresh call,
`resolve_expirations()` now calls `ContractService.resolve_contract_outcome()` directly (the
existing, already-correct model function) and applies both of its returned `SocialUpdate`s — not a
faithful port of `process_active_contracts()`'s own logic, which would have carried its bug
forward. Steps 1, 3, 4, 5 below were followed as written. This file's original candidate-plan
content is kept below for the historical record of what was costed.

## Status (historical, pre-resolution): blocked pending determination — no implementation plan yet

This ticket does not have an implementation plan because it does not yet have a decision to
implement. See `investigation.md` for the full evidence trail. This file records the two
candidate plans so whichever one is chosen can move straight to implementation without
re-investigating.

## Candidate plan A — `resolve_expirations()` owns contract expiry

1. Delete `ContractService.process_active_contracts()` and its wiring at `pipeline.py:416`
   (`"active_contracts"` phase) — confirmed unreachable for its intended purpose, not merely
   redundant.
2. Port `resolve_contract_outcome()`'s full consequence model (sentiment/familiarity/bond updates
   to both parties, notoriety, betrayal branch) into `SocialContractSystem.transition_contract()`
   or a new call from `resolve_expirations()` — only after step 1 removes the duplicate, not
   alongside it.
3. Re-run the 500-tick instrumentation script (`scratchpad/instrument_contract_resolution.py`
   pattern) to confirm exactly one mechanism fires per contract post-fix.
4. Update `test_contract_expiration_resolves_and_dissolves` to assert the new, single-owner
   consequence values (not the old dual-fire `0.10`/`0.15` figures) — this is updating the test to
   match a real, deliberate behavior change, not weakening a gate.
5. Correct the Mechanics Bible's reachability claim to point at the real call path (see
   `investigation.md` — already corrected independent of which plan is chosen).

## Candidate plan B — `process_active_contracts()` owns contract expiry

1. Fix `pipeline.py`'s phase ordering so `"active_contracts"` (currently line 416) runs before
   `"contracts"` (currently line 222) — or scope `resolve_expirations()` down so it no longer
   transitions `ACTIVE` contracts at all (only handles `OFFERED`/`COUNTERED` → `EXPIRED`, which is
   unaffected either way).
2. No model-porting needed — `resolve_contract_outcome()` already has the full documented model;
   this path just makes it reachable.
3. Betrayal branch stays real but likely still practically rare/never-triggered (needs its own
   check — out of scope for this determination, the betrayal-condition wiring is a separate
   question from "which phase resolves expiry").
4. Re-run the 500-tick instrumentation script to confirm `process_active_contracts()` now finds
   real candidates and `resolve_contract_outcome()` is actually called.
5. Update `test_contract_expiration_resolves_and_dissolves` to assert the new values.
6. Mechanics Bible reachability claim correction — already done independent of plan choice.

## Blocking dependency regardless of plan

`TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` — filed separately. Neither plan above
attempts real failure/betrayal differentiation keyed off party cohesion; that requires the
contract→group linkage this ticket does not have. Both plans A and B only get "always resolves as
success" fixed at the mechanism-ownership level, not the "regardless of outcome" half of the
original ticket title — that half is now explicitly transferred to the group-linkage ticket's own
acceptance bar (see that ticket's Related Tickets note).

## Next step

Peer review / user determination on which plan to take (or a third option neither of us has
proposed). Not decided in this file.
