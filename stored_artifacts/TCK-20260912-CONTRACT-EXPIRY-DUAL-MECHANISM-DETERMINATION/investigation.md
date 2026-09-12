# Investigation — TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION

## The ticket's own original target is unreachable

Instrumented a real 500-tick `frontier_living_world` campaign run (seed 7) before designing any
fix, per standing instruction: patched `ContractLifecyclePhase.resolve_expirations()`,
`ContractService.process_active_contracts()`, and `ContractService.resolve_contract_outcome()`
directly.

```
resolve_expirations_fulfilled_a_contract: 1759
process_active_contracts_found_real_ACTIVE_expired_candidates: (never incremented -- 0)
resolve_contract_outcome_called: (never incremented -- 0)
```

`resolve_expirations()` (`src/engine/pipeline_phases/contracts.py`, wired as the `"contracts"`
phase, `pipeline.py:222`, running right after `"cooperation"`) transitions every expiring `ACTIVE`
contract straight to `FULFILLED`. Since it runs *before* `"active_contracts"`
(`pipeline.py:416` → `ContractService.process_active_contracts()`), and since
`process_active_contracts()` only ever processes contracts it finds in `ACTIVE` status, the
contract is never `ACTIVE` by the time `process_active_contracts()` looks — confirmed empirically,
not from phase-ordering reasoning alone.

## Corrected claim: `resolve_expirations()` is not "no consequences"

Initially reported to peer review that `resolve_expirations()` applies no social consequences at
all. Wrong — caught and corrected before implementing on the wrong premise.
`SocialContractSystem.transition_contract()` (`src/systems/social_systems/contracts.py:19-47`)
*does* apply `heroism_delta=0.05` on transition to `FULFILLED`. The real gap: this only ever
applies to whichever entity's own `strategic.contracts` record holds the contract (confirmed
contracts are stored only on the offering entity, never mirrored to the target — same structural
fact the party-formation investigation established). No bond/sentiment update to either party, no
failure/betrayal differentiation.

## Declared intent: the Mechanics Bible

Checked for declared design intent before treating this as an open product question, per standing
instruction (the same check that made party formation safe to build without inventing gameplay
design). `docs/mechanics/07_social_political_dynamics.md` (Certified Level 1, authoritative) and
`docs/simulation/social_systems_contract.md` both document `resolve_contract_outcome()`'s full
sentiment/heroism/notoriety/betrayal, both-parties consequence model as the real, intended
mechanic — with a concrete formula table. `transition_contract()`'s own `heroism_delta=0.05` and
`resolve_contract_outcome()`'s own `heroism_delta=0.05`-on-success agreeing is not coincidence: the
same declared number, partially wired at the reachable call site (`resolve_expirations()`) and
fully wired at the unreachable one (`resolve_contract_outcome()`). This settles the "should
completion carry social consequences" question — yes, the design declares it should.

**The Mechanics Bible's own reachability claim is independently wrong**, a separate finding: it
states `process_active_contracts()` → `resolve_contract_outcome(success=True)` is "real live path"
(`07_social_political_dynamics.md` line 194). The 500-tick instrumentation above disproves this —
zero calls. This is a Certified Level 1 doc asserting a false reachability claim, worse than the
same class of error in a code comment (this batch's fourth instance of that error class: after
`invalidate_read_model`, the survivor-branch placement claim, and `campaigns.py`'s
`register_campaign()` claim) because it's the definitive source, not incidental prose. Corrected as
its own parity defect (see Files Changed), independent of this ticket's own determination — the
declared *model* is still real design intent; only the reachability claim about which call site
executes it was wrong.

## Why porting the model into `resolve_expirations()` was rejected

Implemented an initial fix: wired both-parties bond updates (`sentiment_delta=0.2`,
`familiarity_delta=0.1`, matching `resolve_contract_outcome()`'s own numbers exactly, not
invented) into `resolve_expirations()`. Ran the existing test suite before pushing — standard
practice, and what caught this.

`tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves`
constructs a state directly at `tick=51` for a contract with `expiry_tick=50` — skipping the
`tick == expiry_tick` boundary tick a real, sequential Kernel run would pass through (where
`resolve_expirations()` alone would fire, per the 500-tick instrumentation above). In this
construction, **both** phases fire in the same `refine()` call: each independently reads the same
unmutated `state.entities` snapshot and sees the contract as `ACTIVE`.

Isolated repro (no test-fixture mirroring artifacts) confirmed, **before** any fix: the entity
holding the contract gets `heroism_delta=0.10` (0.05 from `resolve_expirations()`'s own
`transition_contract()`, 0.05 from `process_active_contracts()`'s own `resolve_contract_outcome()`
firing independently) — a real, pre-existing double-fire conflict, not test noise. **With** the
attempted fix applied: `heroism_delta=0.15` and a duplicate bond update to the other party — the
new fix's own both-parties logic compounding with the pre-existing conflict, making it worse in a
scenario that cannot be proven unreachable (checked: Campaign episode carry-forward does not
currently carry contracts across episode boundaries, per `TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-
PROGRESSION-NOT-CARRIED-FORWARD`'s own field audit, ruling out that one specific path — no broader
claim is made about e.g. checkpoint restore).

Reverted before pushing. Porting half the documented model into the reachable phase would have
created a second, parallel implementation of the same documented model — actively conflicting with
the first whenever both fire — the seventh instance of this codebase's "multiple live
implementations of one rule" pattern this arc has found (lead-capacity, degradation vs. governor,
biological decay, the two trust writers, this contract-expiry pair itself, and the optimization
package's partial supersessions).

## Why the lead-capacity three-way frame doesn't transfer

Peer review's own initial framing (apply the lead-capacity supersede/complementary/sequencing-bug
frame) was corrected mid-investigation: lead-capacity was two implementations of *one rule*
differing only in quality/timing-awareness. This pair encodes *one declared design*
(`resolve_contract_outcome()`'s full model), partially wired in one reachable place and fully
wired in one unreachable place — closer to the party-formation shape (a declared, undone wiring)
than the lead-capacity shape (two competing qualities of the same computation). Recorded explicitly
so a future reader doesn't misapply the wrong precedent to this pair.

## Disposition: genuinely open, real determination needed

Two coherent end states, neither implemented here:
1. `resolve_expirations()` owns contract expiry — delete `process_active_contracts()` (confirmed
   unreachable for its intended purpose), port the full documented model into
   `resolve_expirations()` *after* the duplicate is gone, not alongside it.
2. `process_active_contracts()` owns contract expiry — fix the phase ordering (or scope
   `resolve_expirations()` down to stop transitioning `ACTIVE` contracts), so the phase with the
   full model already implemented actually runs. This is the path the Mechanics Bible's own
   documentation already points at, once its reachability claim is corrected to be true rather
   than aspirational.

Not decided here — real architectural size, the kind of decision peer review's own standing
practice routes to the user rather than picking unilaterally.
