---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP
phase: open
date: 2026-09-08
tags: [architecture, strategy]
---

# TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP

## Title
LEG-RPG-150 time-based lead-staleness decay has never run — decay_stale_beliefs() has zero callers

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by peer review (`rpg-feature-planning`) while diagnosing the `combat_risk` belief-staleness
bug on `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`, independently verified against real code
before filing here rather than fixed inline (out of scope for that ticket, per the peer's own
explicit framing):

`BeliefCycleSystem.decay_stale_beliefs()` (`src/systems/strategic_systems/belief.py:42-79`) — its
name and docstring ("LEG-RPG-150: Beliefs decay over time") both promise it decays
`entity.strategic.beliefs`. It does not: the method body iterates `entity.strategic.leads` only and
never touches `beliefs` at all. Confirmed via grep it also has **zero call sites** anywhere in
`src/` — it is dead code, not merely mis-scoped.

This is a real trap for future work: `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`'s own
correction round needed a producer-side no-threat-belief write specifically because nothing decays
`beliefs`, and the peer's own investigation notes that they initially assumed this method would
cover it — "as I initially did" — before checking. The mismatch between what the name promises and
what the code does invites the same mistake again.

**RE-SCOPED 2026-09-08 (user decision) — this is not dead-code cleanup, it is an unimplemented
documented mechanic.** Follow-up review found the method is covered by a real authoritative
contract, which the original filing did not account for:

- `docs/simulation/belief_and_detour_contract.md` §"Staleness decay (LEG-RPG-150)" states:
  *"`decay_stale_beliefs()` runs each strategic pass. Leads not refreshed within `stale_threshold`
  ticks (default: 50) lose certainty"*, with PRECISE leads decaying slower. The method has zero
  callers, so **this documented behavior has never executed a single time**.
- The same doc (line 20) also states `BeliefEntry` is *"contradiction-tracked, decays toward
  staleness"*. The contradiction half is real (`src/domains/information/contradiction.py` demotes
  leads to `EXHAUSTED` on contradiction); the staleness half does not exist anywhere.

So leads degrade **only** when actively contradicted, never merely by going unrefreshed. Live
gameplay consequence: an entity's leads never age out, so it keeps pursuing stale leads
indefinitely, and `src/engine/pipeline_phases/capacity_enforcement.py` (which scores leads by
certainty when pruning under capacity limits) keeps ranking never-decayed high-certainty stale
leads above genuinely fresh ones.

This is a doc/code parity violation on a compliance-tracked ID (LEG-RPG-150), not a naming nit.

## Scope
**Decision already made (user, 2026-09-08): implement the documented behavior.** The alternatives
considered and rejected were (a) recording it as an accepted divergence without building it, and
(b) extending decay to `BeliefEntry` as well. Do not re-open those without new evidence.

- Wire time-based lead-staleness decay into the real strategic pass, so LEG-RPG-150's documented
  behavior actually executes: leads unrefreshed for `stale_threshold` ticks lose certainty, with
  PRECISE leads decaying slower, exactly as `belief_and_detour_contract.md` specifies.
- Rename the method to match what it operates on (`decay_stale_leads()` or equivalent) and correct
  its docstring — the current name is what caused the misreading that surfaced this.
- Determine during Investigate where in the pipeline it belongs, and confirm the interaction with
  the existing contradiction-driven demotion path (`src/domains/information/contradiction.py`) —
  the two must not double-demote a lead in the same tick.
- Verify the real downstream effect on `capacity_enforcement.py`'s certainty-based lead pruning:
  once decay is live, lead-retention behavior under capacity limits will change. Confirm the new
  behavior is correct rather than merely different, with test evidence.
- Fix `docs/simulation/belief_and_detour_contract.md`'s separate false claim that `BeliefEntry`
  "decays toward staleness" — beliefs are NOT in scope for decay here (see Out of Scope), so the
  doc must be corrected to match, and the parity ledger entry updated.

## Deferred to a follow-up ticket, do not do here
- Any decay of `entity.strategic.beliefs` itself. If Investigate finds beliefs genuinely accumulate
  unboundedly, **file a ticket** and continue — do not expand this one.
- Any performance concern arising from decay running each strategic pass. Per standing user
  direction, a dedicated performance effort follows this epic; record findings as a ticket and fix
  only hard failures.

## Out of Scope
- Any other method in `src/systems/strategic_systems/belief.py`.
- Re-litigating the `combat_risk` staleness fix itself — already fixed and closed on
  `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`.

## Acceptance Criteria
- [ ] Time-based lead-staleness decay actually runs in a real simulation, proven by a test showing
      a lead's certainty demoting purely from going unrefreshed past `stale_threshold` — with no
      contradiction involved, since the contradiction path already worked and must not be the thing
      under test.
- [ ] PRECISE leads demonstrably decay slower than APPROXIMATE/VAGUE, per LEG-RPG-150.
- [ ] The decay path and the contradiction path do not double-demote a lead in the same tick.
- [ ] The method's name matches what it operates on, and no stale references to the old name remain.
- [ ] `docs/simulation/belief_and_detour_contract.md` matches real behavior on both counts: the
      lead-decay claim is now true, and the `BeliefEntry` "decays toward staleness" claim is either
      corrected or recorded as an intentional divergence. Parity ledger updated via
      `tools/parity_ledger_writer.py` (never by hand-editing the YAML).
- [ ] `capacity_enforcement.py`'s lead-pruning behavior under the new decay is verified correct, not
      just changed.
- [ ] Existing strategic/information test suites stay green.

## Related Tickets
- TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (origin of this finding, via its own second
  correction round)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` — the authoritative contract for LEG-RPG-150
  staleness decay; the source of both claims this ticket must reconcile with real behavior.
- `docs/simulation/domains/information_contract.md` — sibling `KnowledgeFact` model (capacity-
  bounded, deliberately no decay); useful to avoid conflating the two models.

## Related Stored Artifacts
None yet — standard tier, so `investigation.md`/`plan.md`/`test_plan.md` are required and will be
created by this ticket's own Investigate/Plan phases.

## Related Code Areas
- src/systems/strategic_systems/belief.py

## Assumptions / Open Questions
- Whether any *current* real need exists for generic belief decay (option 3 above) is not yet
  investigated — left for this ticket to determine; default assumption going in is option 1 or 2
  (delete or rename), since option 3 is speculative without an identified real trigger.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
