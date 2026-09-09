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
DONE

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
- [x] Time-based lead-staleness decay actually runs in a real simulation, proven by
      `test_resolve_lead_staleness_demotes_stale_lead_from_real_per_tick_call` — a lead's
      certainty demotes purely from going unrefreshed past `stale_threshold`, no contradiction
      involved.
- [x] PRECISE leads demonstrably decay slower (in this implementation, not at all) than
      APPROXIMATE/VAGUE, per LEG-RPG-150 — `test_resolve_lead_staleness_leaves_precise_lead_untouched`.
- [x] The decay path and the contradiction path do not double-demote a lead in the same tick —
      `test_real_pipeline_stale_and_contradicted_lead_ends_exhausted_not_vague` proves the real
      phase ordering (decay before `lead_contradiction`) produces `EXHAUSTED`, not `VAGUE`, for a
      lead that is both stale and contradicted the same tick.
- [x] The method's name matches what it operates on (`decay_stale_leads`), and no stale references
      to the old name remain (`grep -rn "decay_stale_beliefs" .` — zero hits outside this ticket's
      own artifacts).
- [x] `docs/simulation/belief_and_detour_contract.md` matches real behavior on both counts: the
      lead-decay claim is now true (and notes it wasn't before this ticket); the `BeliefEntry`
      "decays toward staleness" false claim removed. Parity ledger `STRAT-239` updated via
      `tools/parity_ledger_writer.py::write_entry()` (never hand-edited) — corrected `test_path`
      and recorded the honest history (previously verified only a constant's existence, not the
      behavior).
- [x] `capacity_enforcement.py`'s lead-pruning behavior under the new decay is verified correct,
      not just changed — `test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones`
      confirms a newly-decayed (lower-scored) lead is pruned over fresher ones under real capacity
      pressure.
- [x] Existing strategic/information test suites stay green — see Test Summary.

## Related Tickets
- TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (origin of this finding, via its own second
  correction round)
- TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION (new, filed alongside this
  ticket — a second, independent "documented as absent but actually exists, zero callers" pattern
  found while correcting the STRAT-239 parity-ledger entry's own wrong `test_path`)
- TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION (new, filed after peer review —
  the capacity_enforcement.py/enforce_bandwidth() preemption found while writing this ticket's own
  capacity-interaction test)

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

Full investigation/plan in `staging_artifacts/TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP/`.
Routed through peer review before implementing, per this ticket's own P1 authority and the
architecturally-adjacent nature of adding a new pipeline phase.

**The decay logic itself was already correct** (`tests/unit/strategic/test_belief_cycle.py`'s own
4 `TestBeliefDecay` tests already covered it) — the entire gap was that
`decay_stale_beliefs()`/`decay_stale_leads()` had zero callers. Renamed to `decay_stale_leads()`
(only ever touches `entity.strategic.leads`, never `.beliefs`); added a new per-tick orchestrator,
`BeliefCycleSystem.resolve_lead_staleness(state)`, mirroring `LeadContradictionSystem.enforce()`'s
own deterministic-iteration shape; wired into `src/engine/pipeline.py` as a new, unregistered
(always-run, matching `lead_contradiction`'s own shape — no `PhaseDependencyGraph.PHASES` entry
needed) `belief_staleness_decay` phase, positioned between `strategic_intelligence` and
`lead_contradiction`.

**Ordering is load-bearing, verified empirically not just architecturally**: `StrategicUpdate.
merge()` concatenates `leads_add_or_update` rather than deduplicating, and `patches.py`'s
`merge_dict()` resolves same-ID collisions by last-applied-wins dict overwrite (not stacked
double-decrement). Placing decay before `lead_contradiction` means contradiction's own
unconditional `EXHAUSTED` write is the one that lands last for a lead that's both stale and
contradicted the same tick — proved by a real pipeline test, not just reasoned about.

**Parity ledger correction went beyond a wrong citation, per peer review**: `STRAT-239`
(`docs/parity_ledger/strategic_cognition.yaml`) was `status: verified`, `priority: P1` for a
behavior that had never executed once — its own `v2_evidence` only ever confirmed the
`stale_threshold` constant's existence, and its `test_path` cited an unrelated function
(`effective_certainty()` on `KnowledgeFact`, not `LeadState`). Corrected via
`tools/parity_ledger_writer.py::write_entry()` with the honest history recorded in `v2_evidence`
(what was previously verified vs. what became true only once this ticket wired the decay in) —
not silently swapped as if the entry had always been correct.

**Adjacent finding, filed not fixed**: correcting STRAT-239 surfaced that `effective_certainty()`
(`src/cognition/knowledge_model.py:137`) — a real, correctly-tested `KnowledgeFact` decay formula
— also has zero callers anywhere. `belief_and_detour_contract.md`'s own "KnowledgeFact... no
decay" claim is accurate (confirmed by peer review; not flagged as wrong). The open question
(abandoned vs. unfinished intent) isn't resolvable from code alone — filed as
`TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`.

**Second adjacent finding, flagged then filed after peer review sharpened it**: writing the
`capacity_enforcement.py` interaction test surfaced that `StrategicIntelligenceSystem.
fused_strategic_pass()` already calls `DetourSuggestionSystem.enforce_bandwidth()`, which runs
much earlier in the pipeline and independently enforces `max_leads` too — confirmed via direct
tracing that it fires and prunes before `capacity_enforcement.py`'s own dedicated phase ever sees
an over-capacity entity. Peer review's own comparison sharpened this beyond "duplication": the two
are not equivalent — `enforce_bandwidth()` only ever sees the pre-tick state (no awareness of this
tick's own pending lead updates), while `capacity_enforcement.py`'s own trigger correctly accounts
for them. The cruder, pending-update-blind mechanism runs first and can preempt the more correct
one entirely, the same "real, tested code whose behavior is preempted" shape as this session's
other findings — just at the level of which live mechanism's decision wins, not whether either
runs. Filed as `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (P2) rather than
left as an aside — not this ticket's own scope, and not investigated or resolved here.

**This session's recurring finding, recorded per peer review's own request**: this is (by this
session's own running count) at least the 6th-7th instance of real, often unit-tested code with no
live caller found this batch — `decay_stale_beliefs()` here, plus `BiologicalSystem.update()`,
`CatalogScenarioStateBuilder`'s own chain, `spawn_calamity()`, `invalidate_read_model`, the raid
discard stub, and now `effective_certainty()`. The recurring pattern is not any one bug — it's that
this codebase has a systematic gap between "implemented and tested" and "actually reachable at
runtime," which unit tests and parity-ledger entries (STRAT-239 itself being a concrete instance)
have both, at times, certified as if they were the same thing. The peer has since filed
`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (carried onto this branch, unassigned) to survey
this systematically rather than continuing one-off disposition tickets.

## Test Summary
New file `tests/unit/strategic/test_belief_staleness_decay_pipeline.py` — 5 real tests (no mocking
of pipeline internals): stale-lead demotion via the real per-tick orchestrator; PRECISE immunity;
dead-entity skip; the stale-and-contradicted ordering proof via the real full
`AuthoritativeApplyPipeline.refine()`; the `capacity_enforcement.py` pruning-preference proof
(composing the real decay output with the real `CapacityEnforcementPhase.enforce()`, after
confirming direct tracing that the full pipeline's own earlier, unrelated
`DetourSuggestionSystem.enforce_bandwidth()` would otherwise interfere with isolating this
specific interaction). `tests/unit/strategic/test_belief_cycle.py`'s existing 4
`TestBeliefDecay` tests updated for the rename, unchanged logic, still pass.

Scoped regression: `pytest tests/unit/strategic/ tests/unit/cognition/ tests/unit/domains/information/
tests/integration/strategic/ tests/architecture/ -m "not slow and not extra_slow"` → **559 passed,
0 failed**. Broader `tests/unit/engine/ tests/integration/` sweep → **1171 passed, 7 skipped, 2
failed** — both failures confirmed pre-existing/environmental (`tests/integration/observability/
test_export_flow.py`, missing optional `pyarrow` dependency in this local venv, unrelated to
`src/systems/strategic_systems/`, `src/engine/pipeline.py`, or any file this ticket touches).

## Files Changed
- `src/systems/strategic_systems/belief.py` — `decay_stale_beliefs()` renamed to
  `decay_stale_leads()`; new `resolve_lead_staleness(state)` per-tick orchestrator.
- `src/engine/pipeline.py` — new `belief_staleness_decay` phase, between `strategic_intelligence`
  and `lead_contradiction`.
- `tests/unit/strategic/test_belief_cycle.py` — updated for the rename.
- `tests/unit/strategic/test_belief_staleness_decay_pipeline.py` — new, 5 tests.
- `docs/simulation/belief_and_detour_contract.md` — removed the false `BeliefEntry` "decays toward
  staleness" claim; updated the "Staleness decay" section for the rename and the now-live status.
- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-239` corrected via
  `tools/parity_ledger_writer.py::write_entry()`.
- `tickets/todos/TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION.md` — new,
  filed not implemented.

No change to `entity.strategic.beliefs`/`BeliefEntry` decay (deferred per this ticket's own
Scope), `effective_certainty()`/`KnowledgeFact` (separate ticket), or `enforce_bandwidth()`'s own
duplicate capacity logic (flagged, not this ticket's own scope).

## Completion Summary
Wired LEG-RPG-150's already-correct but never-invoked lead-staleness decay into the real strategic
pass, closing a compliance-tracked doc/code parity gap where the documented behavior had never
executed once despite a parity-ledger entry marking it `verified`. Renamed the method to match
what it actually operates on, fixed the doc's own false `BeliefEntry` decay claim, and corrected
the parity ledger with an honest account of what was verified before vs. after this ticket — not a
quiet swap. Verified the real phase-ordering interaction with `lead_contradiction` (no
double-demotion) and `capacity_enforcement.py` (stale leads correctly pruned first) with real
pipeline tests, not reasoning alone. Two adjacent findings surfaced during this work were handled
per this repo's standing discipline: one filed as its own disposition ticket
(`effective_certainty()`/`KnowledgeFact`, a second instance of the same "tested but unreachable"
pattern), one flagged to peer review without unilaterally filing a ticket (a duplicate,
uncoordinated `max_leads` enforcement mechanism in `DetourSuggestionSystem.enforce_bandwidth()`).
No scope creep into `BeliefEntry` decay or the newly-found adjacent systems.
