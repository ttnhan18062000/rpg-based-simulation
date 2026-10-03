---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP
artifact_type: plan
tags: [architecture, strategy]
---

# Plan — TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP

Peer-reviewed and approved before implementation (per this ticket's own P1 authority and the
architecturally-adjacent nature of adding a new pipeline phase).

## Steps

1. **Rename** `BeliefCycleSystem.decay_stale_beliefs()` → `decay_stale_leads()` in
   `src/systems/strategic_systems/belief.py`. Update its docstring ("Leads decay over time", not
   "Beliefs decay over time"). No change to its internal logic — already correct.
2. **Add a per-tick orchestrator**, `BeliefCycleSystem.resolve_lead_staleness(state:
   AuthoritativeState) -> StateUpdate`, in the same module: iterates
   `sorted(state.entities.values(), key=lambda e: e.id)`, filters `combat.alive` and
   `lifecycle.active` (matching `LeadContradictionSystem.enforce()`'s own filter), calls
   `decay_stale_leads(entity, state.tick)` per entity, merges non-empty results into a
   `Dict[int, EntityUpdate]` keyed by entity id, returns `StateUpdate(entity_updates=...)`.
3. **Wire into the pipeline**: add
   `update = run_phase("belief_staleness_decay", update, lambda u: u.merge(
   AuthoritativeApplyPipeline._resolve_lead_staleness(state, u)))` (or equivalent, matching the
   existing `run_phase` call shape) in `src/engine/pipeline.py`, positioned between the existing
   `strategic_intelligence` (line 393) and `lead_contradiction` (line 395) calls — this ordering is
   load-bearing, see investigation.md's own reasoning (contradiction's unconditional EXHAUSTED
   write must win last for a lead that's both stale and contradicted in the same tick). No new
   `PhaseMetadata` entry in `phase_graph.py` — matches `lead_contradiction`'s own unregistered,
   always-run shape (unconditional, no dirty-set gate, since staleness genuinely needs to be
   checked every tick regardless of what else changed).
4. **Doc corrections**:
   - `docs/simulation/belief_and_detour_contract.md` line 20: remove the false "decays toward
     staleness" half of the `BeliefEntry` description, keep "contradiction-tracked" (true).
   - Same doc, lines 66-72 ("Staleness decay (LEG-RPG-150)"): update the method name reference to
     `decay_stale_leads()`.
5. **Parity ledger**: use `tools/parity_ledger_writer.py::write_entry()` to update `STRAT-239` in
   `docs/parity_ledger/strategic_cognition.yaml` — correct `test_path` to point at a real test of
   the actual mechanism (the new pipeline-level test from step 6, or `test_belief_cycle.py`'s own
   existing per-entity tests), and add a `divergence_note`-adjacent history note (or extend `text`)
   recording that this entry previously verified only the `stale_threshold` constant's existence,
   not the behavior, and that the behavioral claim became true only once this ticket wired the
   decay into the real pipeline — not silently swapped as if always correct. Never hand-edit the
   YAML.
6. **Tests**:
   - A new pipeline-level test proving decay fires from a real strategic pass (not
     `decay_stale_leads()` called in isolation, which `test_belief_cycle.py` already covers) —
     construct an entity with a stale APPROXIMATE lead, run it through the real phase sequence
     (or at minimum the new orchestrator function directly against real state), confirm the lead
     demotes with no contradiction involved.
   - A test proving PRECISE leads still don't decay via this path in the same real-pipeline
     context.
   - A test proving decay and contradiction don't produce an inconsistent result when both apply
     to the same lead in the same tick — construct a lead that is both stale AND contradicted,
     confirm the final state is `EXHAUSTED` (contradiction's outcome), not `VAGUE` (decay's
     outcome), verifying the phase-ordering reasoning from investigation.md empirically rather
     than only architecturally.
   - A test proving `capacity_enforcement.py`'s lead-pruning now correctly favors keeping fresh
     leads over newly-decayed ones under capacity pressure, per this ticket's own AC.
7. **Regression**: `tests/unit/strategic/ tests/unit/cognition/ tests/unit/domains/information/
   tests/integration/strategic/ tests/architecture/` (or equivalent real scoped set, confirmed
   during Implement) must stay green.

## Explicitly not in this plan
- Any decay of `entity.strategic.beliefs` (`BeliefEntry`) — deferred per the ticket's own Scope.
- `effective_certainty()`/`KnowledgeFact` — separate, filed ticket
  (`TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`).
- Removing the unused `decay_rate` parameter unless confirmed trivially safe during Implement.
