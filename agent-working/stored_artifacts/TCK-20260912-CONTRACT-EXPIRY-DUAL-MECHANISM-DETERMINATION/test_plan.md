# Test Plan — TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION

## Resolution (2026-09-13)

All five "Required test evidence once a plan is chosen" items below were delivered: single-fire
proof (500-tick re-instrumentation, `resolve_contract_outcome_called: 335`, nonzero and via the
single surviving mechanism), both-parties consequence proof
(`test_contract_expiration_grants_the_other_party_its_own_real_consequence`, exact values both
sides), `test_contract_expiration_resolves_and_dissolves` updated to the real single-fire value
(`0.05`, not the old double-fire `0.1`) — plus a distinct fix to that test's own construction (see
the ticket's Implementation Notes: its dual-mirrored contract storage independently caused a
second, unrelated double-count within the single surviving mechanism's own per-entity loop), no
regression across the full contract/social/cooperation/kernel/pipeline sweep, and betrayal
confirmed to remain unreachable (unchanged, explicitly stated, not silently left ambiguous). See
the ticket's own Test Summary for exact commands and counts.

## Status (historical, pre-resolution): blocked pending determination — no new tests written yet

No implementation has landed (the attempted both-parties fix was reverted — see
`investigation.md`). This file records what evidence already exists and what a real fix, once a
plan is chosen, must prove.

## Evidence already gathered (pre-implementation)

- `scratchpad/instrument_contract_resolution.py` (real 500-tick `frontier_living_world` /
  `hero_guild_perspective` / seed-7 campaign): confirms `resolve_expirations()` fulfills 1,759
  contracts over the run; `process_active_contracts()` never finds a real `ACTIVE`-past-expiry
  candidate; `resolve_contract_outcome()` is never called. This is the ticket's own core
  before-any-fix evidence.
- Isolated repro (manual, not committed as a test — used to characterize the double-fire
  precisely): confirmed the existing `test_contract_expiration_resolves_and_dissolves` fixture's
  `tick=51`-for-`expiry_tick=50` construction causes both phases to fire in one `refine()` call
  even without any code change — pre-existing, `heroism_delta=0.10` (two independent `0.05`
  contributions). With the (reverted) both-parties fix applied, this became `0.15` plus a
  duplicate bond update — confirming the fix compounded rather than resolved the conflict.
- Existing test `tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves`
  left unmodified, per peer instruction — it is documented evidence of the real conflict, not
  something to weaken. Full suite `pytest tests/ -k "contract" -q -m "not slow and not extra_slow"`
  confirmed at 389 passed / 1 skipped baseline (pre- and post-revert, identical).

## Required test evidence once a plan is chosen (not yet written)

Applies to either candidate plan in `plan.md`:

1. **Single-fire proof**: re-run the 500-tick instrumentation pattern (or a scoped equivalent)
   showing exactly one mechanism processes each expiring contract — no double-fire, in both the
   real sequential-tick case and the existing test's tick-skip construction.
2. **Both-parties consequence proof**: a contract with a real leader and a real member, asserting
   exact `heroism_delta`/`sentiment_delta`/`familiarity_delta` values on BOTH entities after
   expiry resolves — the same "both sides, exact values, no half-fix" standard applied to the
   survivor-progression ticket's acceptance bar.
3. **Updated `test_contract_expiration_resolves_and_dissolves`**: new assertions matching the
   single-owner mechanism's real output (not the old dual-fire `0.10` figure) — an intentional,
   documented behavior change, not a gate edit to dodge a failure.
4. **Regression guard**: no change in `tests/unit/social/`, `tests/integration/social/`,
   `tests/unit/domains/cooperation/` beyond the intentionally updated assertion(s) above.
5. **Betrayal branch**: confirm whether it's newly reachable under the chosen plan; if still
   unreachable, that's an explicit, stated fact in the ticket's Completion Summary, not silently
   left ambiguous.

## Out of scope for this ticket's own test evidence

Real failure/betrayal differentiation keyed off `PartyCohesionService`'s cohesion signal — blocked
on `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING`, tested there once that lands.
