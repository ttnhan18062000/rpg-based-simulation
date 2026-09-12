---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION
phase: done
date: 2026-09-12
tags: [cognition, social]
---

# TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION

## Title
Two live pipeline phases both resolve expiring ACTIVE contracts — determine which one owns contract expiry before wiring the documented consequence model anywhere

**Retitled and re-scoped 2026-09-12** (was "`process_active_contracts()`... always resolves
success"). Investigation found the ticket's own named function and its `success=True` bug are
structurally unreachable in normal, sequential tick-by-tick gameplay — confirmed via real 500-tick
instrumentation, zero calls. A second, earlier-running phase (`ContractLifecyclePhase.
resolve_expirations()`) always resolves the contract first. The real, live defect is that the
reachable phase implements only a subset of the documented consequence model (one-sided,
success-only). An initial attempt to port the missing pieces into the reachable phase was
reverted after a pre-existing test proved the two mechanisms can and do run together under a
condition that isn't provably unreachable (see below) — porting half the model into the reachable
phase would create a **second, parallel implementation of the same documented model**, actively
conflicting with the first when both fire. The real fix is consolidation to one owner, not
porting. This ticket now exists to make that determination.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`'s own
search for a real, live "did this cooperation outcome succeed or fail" signal.
`ContractService.process_active_contracts()` (`src/systems/social_systems/contracts.py:294-`) was
originally found to call `ContractService.resolve_contract_outcome()` with `success=True`
unconditionally, for every contract kind, on every expiry — the ticket's original framing.

**Investigation invalidated that framing.** `src/engine/pipeline.py` wires TWO separate phases
that both process expiring `ACTIVE` contracts:
- `"contracts"` (`pipeline.py:222`) → `ContractLifecyclePhase.resolve_expirations()`
  (`src/engine/pipeline_phases/contracts.py`), runs immediately after `"cooperation"`.
- `"active_contracts"` (`pipeline.py:416`) → `ContractService.process_active_contracts()`, runs
  much later, after `"groups"`.

`resolve_expirations()` runs first: for any `ACTIVE` contract past `expiry_tick`, it transitions
the contract straight to `FULFILLED` via `SocialContractSystem.transition_contract()` — which does
apply a real `heroism_delta=0.05` (confirmed by direct read; an earlier report to peer review
incorrectly claimed "no consequences at all," corrected before any code was written on that
premise), but only to whichever entity's own `strategic.contracts` record holds the contract
(confirmed: contracts are stored only on the offering entity, never mirrored to the target — same
structural fact as the party-formation investigation). No bond/sentiment update to either party,
no failure/betrayal differentiation — every contract is unconditionally treated as fulfilled,
regardless of what actually happened, and the target/recruited party gets nothing.

Because `resolve_expirations()` transitions the contract's status away from `ACTIVE` before
`process_active_contracts()` (`"active_contracts"`, later in the same tick) ever runs, and because
`process_active_contracts()` only processes contracts it finds in `ACTIVE` status,
`process_active_contracts()`'s own `resolve_contract_outcome()` call — the ticket's original named
target — is **structurally unreachable in normal sequential tick progression**. Confirmed via real
instrumentation: a 500-tick `frontier_living_world` campaign run (seed 7) shows
`resolve_expirations()` fulfilling 1,759 real recruitment contracts; `resolve_contract_outcome()`
called **zero** times.

**Declared intent, checked per standing instruction (the same check that made party formation safe
to build):** `docs/mechanics/07_social_political_dynamics.md` (Certified Level 1) and
`docs/simulation/social_systems_contract.md` both document `resolve_contract_outcome()`'s full
sentiment/heroism/notoriety/betrayal, both-parties consequence model as the intended mechanic for
contract-expiry resolution — with a formula table. Both entities' `heroism_delta=0.05` agreeing
across the two independently-derived paths (`transition_contract()`'s own 0.05, and
`resolve_contract_outcome()`'s own 0.05-on-success) is not coincidence — it's the same declared
number, partially wired at the reachable call site and fully wired at the unreachable one. **The
Mechanics Bible's own reachability claim is independently wrong** — it asserts
`process_active_contracts()` → `resolve_contract_outcome()` is "real live path," which the 500-tick
instrumentation now disproves. Corrected separately, filed as its own parity defect (see Related
Tickets) — the declared consequence *model* is still the real design intent, independent of the
Bible's stale reachability claim about which call site executes it.

**Why porting the model into the reachable phase was rejected.** An initial attempt wired
`resolve_expirations()` to also apply bond/sentiment updates to both parties (matching the
documented model, using the same numbers `resolve_contract_outcome()` already uses). Before
pushing, the existing test suite was run — standard practice, not incidental — and
`tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves` failed:
it constructs a state directly at `tick=51` for a contract with `expiry_tick=50`, skipping the
`tick == expiry_tick` boundary tick a real Kernel run would pass through. In that construction,
**both** phases fire in the same `refine()` call — each reads the same unmutated `state.entities`
snapshot and independently sees the contract as `ACTIVE`. Isolated repro confirmed: before any fix,
this produces `heroism_delta=0.10` on the entity holding the contract (0.05 from each mechanism)
and a real, duplicate-consequence conflict — the test is not synthetic-noise, it is existing proof
the code path is reachable under a real (if narrow) condition. Whether that condition (a state
presented with `current_tick` already past a contract's `expiry_tick` on its very first evaluation,
never having passed through the exact boundary tick) can occur in real gameplay — e.g. via
checkpoint restore — is not provably impossible; the survivor carry-forward audit
(`TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD`) confirmed contracts
themselves are not currently carried across Campaign episode boundaries, which rules out that one
specific path, but does not rule out every path. With the attempted fix applied, the double-fire
case produced `heroism_delta=0.15` and duplicate bond updates — the new fix's own logic compounding
with the pre-existing conflict, worsening it in a scenario that cannot be shown unreachable.
Reverted before pushing. **Porting half the documented model into the reachable phase would create
a second, parallel implementation of the same model — the seventh instance of this codebase's
"multiple live implementations of one rule" pattern (after lead-capacity, degradation vs.
governor, biological decay, the two trust writers, the contract-expiry pair itself, and the
optimization package's partial supersessions) — not a fix for it.**

## Scope
- Determine which phase should own contract-expiry resolution:
  1. `resolve_expirations()` owns it — `process_active_contracts()` is deleted (confirmed
     unreachable for its intended purpose), and the full documented consequence model (bond
     updates to both parties, failure/betrayal differentiation once a real signal exists — see
     `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING`) is ported into
     `resolve_expirations()` **after** the duplicate is removed, not alongside it.
  2. `process_active_contracts()` owns it — the phase ordering is fixed so it actually runs before
     `resolve_expirations()` can preempt it (or `resolve_expirations()` is scoped down to stop
     transitioning `ACTIVE` contracts at all), and the full model — already implemented there —
     starts actually executing. This is the path the Mechanics Bible already describes as the real
     mechanic, once its reachability claim is corrected to be true rather than aspirational.
  3. Something else Investigate surfaces — not pre-judged here.
- Whichever option: confirm via real re-instrumentation (the same 500-tick campaign scenario) that
  exactly one mechanism resolves each expiring contract, not both, and that the resulting
  consequences match the documented model with real, evidenced values (not just "some" consequence
  applied).
- Correct `docs/mechanics/07_social_political_dynamics.md`'s stale reachability claim ("real live
  path" for `process_active_contracts()` → `resolve_contract_outcome()`) regardless of which
  mechanism the determination settles on — treat as its own parity defect finding, not a footnote,
  per standing instruction on the Authoritative Mechanics Rule.
- Success/failure/betrayal differentiation (as opposed to the currently-unconditional
  "always fulfilled" outcome) remains blocked on
  `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` regardless of which mechanism wins —
  do not attempt to invent a success criterion in this ticket.

## Out of Scope
- Inventing a success/failure/betrayal detection signal — blocked on
  `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING`, not this ticket's to solve.
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`'s own `trust_history`
  scope — unchanged, not conflated here.
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s own scope — unrelated precondition.
- Widening this determination to other `ContractKind`s beyond confirming the same dual-mechanism
  shape applies generically (both phases iterate all contract kinds identically) — the
  determination is about *which phase*, not per-kind behavior differences.

## Acceptance Criteria
- [x] Real evidence (instrumentation, not code-reading alone) confirms which of the two phases
      actually resolves expiring contracts today, and under what conditions both can fire together
      — 1,759 vs. 0 pre-fix; re-confirmed post-fix via a fresh 500-tick instrumented run
      (`resolve_contract_outcome_called: 335`, now genuinely nonzero).
- [x] A peer-routed determination: which phase owns contract expiry. Grep-level relative-cost
      writeup sent to peer review for both options; peer decided Option A (`resolve_expirations()`
      owns it) directly from the evidence, without escalating to the user — the deciding fact was
      the missing-other-party bug found while costing Option B (see Implementation Notes).
- [x] `process_active_contracts()` (the non-owner) is deleted entirely, not deprioritized —
      genuinely removed from `src/systems/social_systems/contracts.py` and its pipeline
      registration removed from `src/engine/pipeline.py`.
- [x] The full documented consequence model (both-parties bond updates) lands at the one, real,
      reachable owner — verified via `test_contract_expiration_grants_the_other_party_its_own_real_consequence`,
      asserting exact values on both sides.
- [x] `docs/mechanics/07_social_political_dynamics.md`'s stale reachability claim corrected (twice:
      once mid-investigation to record the pre-fix finding, once more to record the post-fix live
      state) — same for `docs/mechanics/04_strategic_cognition.md` and
      `docs/parity_ledger/social_narrative.yaml`'s SOC-272 entry, which repeated the same stale
      claim.
- [x] No regression in existing contract-resolution tests, including
      `test_contract_expiration_resolves_and_dissolves` (updated to reflect the real, single-owner
      resolution — kept its tick-skip construction as a regression guard, updated its assertions
      from the old double-fire value to the real single-fire value, and removed its own unrealistic
      dual-mirrored contract storage since that construction independently caused the same
      mechanism's per-entity loop to double-count, unrelated to the two-mechanism bug just fixed).

## Related Tickets
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` (done — origin of this
  finding)
- `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (new, filed from this ticket's own
  investigation — the prerequisite for any real success/failure/betrayal differentiation,
  regardless of how this ticket's own determination lands)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (a structurally similar
  finding shape from earlier in this arc, though peer review's own correction established this
  ticket's pair encodes one declared design partially wired in two places, not two competing
  designs — the lead-capacity frame does not directly transfer, noted explicitly to avoid
  misapplying it)

## Related Docs
- `docs/mechanics/07_social_political_dynamics.md` §5 (the consequence-model formula table; its
  own reachability claim needs correcting)
- `docs/simulation/social_systems_contract.md` (corroborating documented intent)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION/`
  (`investigation.md`, `plan.md`, `test_plan.md`)

## Related Code Areas
- `src/engine/pipeline_phases/contracts.py` (`ContractLifecyclePhase.resolve_expirations()`, the
  reachable phase)
- `src/systems/social_systems/contracts.py` (`ContractService.process_active_contracts()`,
  `resolve_contract_outcome()`, `SocialContractSystem.transition_contract()`)
- `src/engine/pipeline.py` (the phase ordering itself — lines 222 and 416)
- `tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves` (the
  test that proved the double-fire condition is real, not synthetic)

## Assumptions / Open Questions
- Whether the `tick > expiry_tick` (skipping the exact boundary tick) condition can occur via any
  real production path (checkpoint restore, etc.) is not resolved here — confirmed it does NOT
  happen via Campaign episode carry-forward specifically (contracts aren't carried), but no
  broader claim is made.
- Which phase should be the real owner is the central, deliberately-unresolved question this
  ticket exists to answer — not assumed here, and likely warrants user input given its
  architectural size (this is the kind of decision peer review said it would take to the user
  rather than pick unilaterally).

## Implementation Notes
**Determination (2026-09-13): Option A — `resolve_expirations()` owns contract expiry;
`process_active_contracts()` deleted.**

Relative-cost writeup sent to peer, grep-level per instruction (not a fresh investigation):
- **Option A costs**: a same-file call swap (`SocialContractSystem` in `resolve_expirations()` is
  a 3-line re-export shim pointing at the exact file `ContractService.resolve_contract_outcome()`
  lives in — `src/systems/social_systems/contracts.py`), no later-phase state dependency, and
  every one of the 10 existing tests calling `resolve_contract_outcome()` directly (not through
  the phase) survives unchanged.
- **Option B costs, found while costing it**: (1) `resolve_expirations()`'s `tick >= expiry_tick`
  boundary vs. `process_active_contracts()`'s `tick > expiry_tick` (strict) would need relaxing,
  or contracts sit ACTIVE-but-expired for a full extra tick; (2) `GroupSystem.update_groups()`'s
  new-group-formation gate (`groups.py:272-275`, `status == ACTIVE` only) makes a same-tick-expiry
  new-group-formation edge case concrete, not theoretical; (3) **the decisive finding**:
  `process_active_contracts()` itself only ever applied `bond_ups[0]` (the contract holder's own
  consequence) — never `bond_ups[1]` (the other party's), despite `resolve_contract_outcome()`
  computing both. Option B's entire premise ("the full model is already implemented there, just
  unreachable") was false — it would have cost three real fixes to reach a worse starting point
  than Option A's single-file swap.

Peer decided Option A directly from this evidence (no user escalation needed — the underlying
product question, "should completion carry consequences," was already settled by the Bible's
declared intent; the mechanism question was a real engineering determination, not a product call).

**Implementation, following peer's explicit correction of my own first instinct:** peer flagged
that porting `process_active_contracts()`'s logic "as-is" would carry its `bond_ups[1]` bug into
the surviving path — the fix had to port the model *correctly*, not faithfully copy the bug.
`resolve_expirations()`'s `ACTIVE` branch now calls `ContractService.resolve_contract_outcome()`
directly (replacing the old, narrower `SocialContractSystem.transition_contract()` call) and
applies **both** returned `SocialUpdate`s — the contract holder's own via the existing
`_merge_entity_update()` pattern, and the other party's via a new `other_id` computation
(`contract.target_id` if the entity is the source, else `contract.source_id`), guarded by
`other_id in state.entities` (an entity could theoretically not exist in `state.entities` if
removed same-tick; matches the guard pattern used and reverted from the earlier both-parties
attempt).

`ContractService.process_active_contracts()` deleted from `src/systems/social_systems/contracts.py`
(including its own `bond_ups[0]`-only bug — recorded here explicitly as a found-and-fixed-by-
deletion item, not a clean superseded copy: the deleted code was carrying a real defect, not just
redundant correct logic). Its pipeline registration removed from `src/engine/pipeline.py`'s
`"active_contracts"` phase (`ContractService.reap_expired_offers()`, a separate real function on
the same phase, is unaffected and still runs there).

**Docstring/comment corrections following the deletion** (so nothing still points at the removed
function as a caller): `compute_betrayal_clan_reputation_update()`'s own docstring
(`contracts.py`), the two test-file comments referencing `process_active_contracts()`
(`test_contract_lifecycle.py`, `test_social_phase7.py`), and `docs/mechanics/04_strategic_cognition.md`'s
§10a clan-reputation section (twice: the "Disclosed gap" paragraph and the "Out of scope"
line) — all now correctly attribute `resolve_expirations()` as the sole production caller.

**A genuinely separate, smaller finding surfaced while re-deriving the doc corrections**:
`transition_contract()`'s own `heroism_delta = 0.05` (set when transitioning to `FULFILLED`) is
now confirmed computed-but-always-discarded — its only two callers (`accept_contract()`, which
transitions to `ACTIVE` not `FULFILLED`, and `resolve_contract_outcome()`, which discards the
return value as `_` and computes its own richer `SocialUpdate` independently) never apply it to
any entity. Documented as a disclosed, harmless dead value in the Mechanics Bible table (not worth
its own ticket — genuinely inert, doesn't affect correctness since `resolve_contract_outcome()`'s
own value supersedes it at the only path that matters).

**Test-construction fix, distinct from the two-mechanism bug**: while updating
`test_contract_expiration_resolves_and_dissolves`, found that its own construction (mirroring the
same `ContractState` onto BOTH `leader.strategic.contracts` AND `member.strategic.contracts`) would
independently cause `resolve_expirations()`'s own per-entity loop to process the same contract
twice post-fix — once from each entity's own perspective — reproducing the same `0.1`
double-fire number for an entirely different reason (the loop, not two competing mechanisms).
Confirmed via direct trace: `GroupSystem`'s own group-invalidation check only ever reads the
contract from the leader's own record (`groups.py:135-147`), so the member's mirrored copy served
no purpose. Removed it to match the real "stored only on the offering entity" invariant confirmed
earlier in this investigation and in the party-formation investigation — the test now exercises a
realistic contract shape and genuinely proves single-fire behavior (`0.05`, not `0.1`).

## Test Summary
- `pytest tests/ -k "contract" -q -m "not slow and not extra_slow"`: 390 passed, 1 skipped (389
  pre-existing + 1 new regression test; the previously double-firing test now asserts the correct
  single-fire value).
- `pytest tests/unit/social/ tests/unit/domains/cooperation/ tests/unit/world/test_camp_lifecycle.py
  tests/unit/domains/faction/test_clan_reputation_association.py
  tests/unit/strategic/test_strategic_social_contracts.py tests/unit/core/test_p1_semantic_hardening.py
  tests/unit/kernel/ -q -m "not slow and not extra_slow"`: 426 passed (broader regression sweep —
  social, cooperation, groups, clan reputation, kernel).
- `pytest tests/ -k "pipeline" -q -m "not slow and not extra_slow"`: 163 passed (no phase-ordering
  regression from removing the `"active_contracts"` phase registration).
- New test `test_contract_expiration_grants_the_other_party_its_own_real_consequence`
  (`tests/unit/social/test_social_phase7.py`): real single-owner contract with a genuine
  single-entity storage shape, exact-value assertions on BOTH parties' `heroism_delta`,
  `notoriety_delta`, and `SocialBondUpdate` (`sentiment_delta`, `familiarity_delta`) — the specific
  regression guard for the `bond_ups[1]` bug this ticket found and fixed.
- Real 500-tick `frontier_living_world`/`hero_guild_perspective`/seed-7 campaign instrumentation,
  re-run post-fix: `resolve_contract_outcome_called: 335` (nonzero — confirms the full model is now
  a genuine live path, not merely unit-tested), completed cleanly to tick 500 with no
  contract-related errors.

## Files Changed
- `src/engine/pipeline_phases/contracts.py` — `resolve_expirations()`'s `ACTIVE` branch now calls
  `ContractService.resolve_contract_outcome()` and applies both returned `SocialUpdate`s (to the
  contract holder and the other party); import changed from `SocialContractSystem` to
  `ContractService`; docstring updated.
- `src/systems/social_systems/contracts.py` — `ContractService.process_active_contracts()` deleted;
  `compute_betrayal_clan_reputation_update()`'s docstring updated to name the real caller.
- `src/engine/pipeline.py` — `"active_contracts"` phase's `process_active_contracts()` call removed
  (its sibling `reap_expired_offers()` call, a separate real function, stays); explanatory comment
  added.
- `tests/unit/social/test_social_phase7.py` — `test_contract_expiration_resolves_and_dissolves`
  updated (single-entity contract storage, single-fire assertions); new
  `test_contract_expiration_grants_the_other_party_its_own_real_consequence` added.
- `tests/unit/social/test_contract_lifecycle.py` — stale docstring comment updated.
- `docs/mechanics/07_social_political_dynamics.md` — §4.1 table and §5 "Disclosed gap" paragraph
  updated to reflect the resolved, live state (both mid-investigation and post-fix passes).
- `docs/mechanics/04_strategic_cognition.md` — §10a clan-reputation section's two
  `process_active_contracts()` references updated to `resolve_expirations()`.
- `docs/parity_ledger/social_narrative.yaml` — SOC-272's `v2_evidence` updated to reflect the real
  caller (two passes, matching the Bible doc's own two-pass correction).
- `staging_artifacts/TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION/` →
  `stored_artifacts/` (this file's own move, at Finalize).

## Completion Summary
Two live pipeline phases both resolved expiring `ACTIVE` contracts; the one the ticket originally
named (`process_active_contracts()`) was confirmed structurally unreachable in normal sequential
tick progression, and the reachable one implemented only a subset of the documented consequence
model. Costed both single-owner dispositions at peer's request; Option A
(`resolve_expirations()` owns it, `process_active_contracts()` deleted) won on evidence — Option B's
own premise ("the full model is already implemented there") turned out to be false, since the code
being preserved carried a real bug (never applying the other party's consequence). Implemented
Option A correctly rather than porting the bug forward: both parties now receive real, documented
consequences on contract expiry, verified with exact-value tests. Corrected the Mechanics Bible,
a strategic-cognition cross-reference, and a parity ledger entry that all carried the same stale
reachability claim. Filed the group-linkage gap
(`TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING`) as the real prerequisite for
failure/betrayal differentiation, left explicitly out of scope here. No known material gap left
unstated.
