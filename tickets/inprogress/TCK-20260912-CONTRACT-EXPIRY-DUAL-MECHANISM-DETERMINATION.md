---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION
phase: open
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
BLOCKED

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
- [ ] Real evidence (instrumentation, not code-reading alone) confirms which of the two phases
      actually resolves expiring contracts today, and under what conditions both can fire together
      — already substantially done (1,759 vs. 0 in normal progression; the test's own double-fire
      scenario characterized precisely) but re-confirm as current when picked up.
- [ ] A peer-routed (and, per this whole arc's standing pattern, user-routed for a genuine product/
      architecture decision of this size) determination: which phase owns contract expiry.
- [ ] Whichever phase is NOT the owner is fixed to stop independently transitioning `ACTIVE`
      contracts — not merely deprioritized, actually prevented from double-firing.
- [ ] The full documented consequence model (both-parties bond updates, at minimum) lands at the
      one, real, reachable owner — verified via a real test, including the specific double-fire
      scenario `test_contract_expiration_resolves_and_dissolves` already exercises, confirmed to
      no longer produce duplicate/over-counted consequences.
- [ ] `docs/mechanics/07_social_political_dynamics.md`'s stale reachability claim corrected.
- [ ] No regression in existing contract-resolution tests, including
      `test_contract_expiration_resolves_and_dissolves` (updated to reflect the real, single-owner
      resolution, not deleted or weakened).

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
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
