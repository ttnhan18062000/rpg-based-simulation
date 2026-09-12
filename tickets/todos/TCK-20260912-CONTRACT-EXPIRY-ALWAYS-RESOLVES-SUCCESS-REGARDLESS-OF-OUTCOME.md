---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260912-CONTRACT-EXPIRY-ALWAYS-RESOLVES-SUCCESS-REGARDLESS-OF-OUTCOME
phase: open
date: 2026-09-12
tags: [cognition, social]
---

# TCK-20260912-CONTRACT-EXPIRY-ALWAYS-RESOLVES-SUCCESS-REGARDLESS-OF-OUTCOME

## Title
`ContractService.process_active_contracts()` — the only production caller of
`resolve_contract_outcome()` — always resolves an expired contract as `success=True`,
never detects betrayal, and never checks whether the contract's actual terms were met

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`'s own
search for a real, live "did this cooperation outcome succeed or fail" signal. Cooperation's own
`REQUEST_HELP`/`HIRE_SUPPORT` postures create real recruitment `ContractState` records
(`CooperationIntentBridge.map_decision()`, `src/domains/cooperation/services.py:178-198`), which
`ContractService.process_active_contracts()` (`src/systems/social_systems/contracts.py:293-`)
resolves on expiry via `ContractService.resolve_contract_outcome()`. This IS a real, live, wired
mechanism — but `process_active_contracts()` calls it with `success=True` unconditionally, for
every contract kind, on every expiry, regardless of whether the contract's actual terms were
fulfilled:

```python
strat_up, bond_ups = ContractService.resolve_contract_outcome(entity, c_id, success=True, tick=current_tick)
```

`resolve_contract_outcome()` itself already supports a real `betrayal`/`betrayer_id` parameter
pair and a proper success/failure branch (`ContractStatus.FULFILLED` vs `.FAILED` vs `.BETRAYED`,
with correspondingly different `sentiment_delta`/`heroism_delta`/`notoriety_delta` consequences) —
this is not a stub. **The gap is entirely at the one real call site**, which never determines
which case actually applies.

The gap is self-disclosed in the file's own docstring
(`compute_betrayal_clan_reputation_update()`'s docstring, lines 269-280): "`process_active_
contracts()`, the only production caller of `resolve_contract_outcome()`, never passes
`betrayal=True`/`betrayer_id` — a pre-existing gap this ticket discloses but does not fix (out of
scope; would require new betrayal-detection decision logic in `process_active_contracts()`)."
That prior disclosure covered betrayal specifically; this ticket covers the full scope, including
that every contract also always resolves as a plain success, never a failure, regardless of
whether e.g. the hired/requested partner actually delivered anything.

**Real consequence, not theoretical**: every recruitment contract cooperation creates writes a
uniformly positive social consequence (`bonds`/`heroism`/`notoriety`) on expiry, whether or not the
cooperation attempt actually worked out. This affects `bonds`/reputation specifically, not
`trust_history` (a separate finding, not conflated here) — but it means the one real, live outcome
signal cooperation's own contract mechanism produces is currently meaningless: uniformly positive
regardless of what happened.

## Scope
- Determine what real signal should decide success vs. failure vs. betrayal for an expiring
  recruitment (and other kind) contract — e.g., did the contracted partner actually deliver on the
  recruitment terms (accompany, defend, complete the shared task) during the contract's active
  window? Real design work, not assumed from this ticket's own framing.
- Wire real success/failure/betrayal detection into `process_active_contracts()`, replacing the
  unconditional `success=True`.
- Confirm the fix with a real multi-tick run showing contracts resolving with real, varied
  outcomes (not uniformly positive) when a contract's terms were genuinely not met.

## Out of Scope
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`'s own `trust_history`
  scope — this ticket's fix affects `bonds`/`heroism`/`notoriety`, a different axis; explicitly not
  extended to also write `trust_delta` unless a future ticket makes that a deliberate design
  decision, not an incidental side effect of this one.
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s own scope — unrelated precondition
  (contracts don't require a party to exist, only a recruitment relationship between two entities).

## Acceptance Criteria
- [ ] Real, evidence-based determination of what signal should drive success/failure/betrayal
      resolution for an expiring contract.
- [ ] `process_active_contracts()` no longer hardcodes `success=True` — resolves each contract
      according to its own real, observed fulfillment.
- [ ] A real test shows at least one contract resolving as failed or betrayed under real
      conditions where terms genuinely were not met, not just the existing always-success path.
- [ ] No regression in existing contract-resolution tests.

## Related Tickets
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` (done — origin of this
  finding, found while searching for a real cooperation-outcome signal; explicitly declined to
  wire trust through this path since it would have produced meaningless uniformly-positive values)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/systems/social_systems/contracts.py` (`ContractService.process_active_contracts()`,
  `resolve_contract_outcome()`, `compute_betrayal_clan_reputation_update()`'s own disclosing
  docstring)
- `src/domains/cooperation/services.py` (`CooperationIntentBridge.map_decision()`, the real
  recruitment-contract creation site this resolution mechanism serves)

## Assumptions / Open Questions
- What real, observable signal should determine contract fulfillment is the central,
  deliberately-unresolved design question this ticket exists to answer — not assumed here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
