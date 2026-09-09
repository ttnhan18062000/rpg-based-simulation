---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP
artifact_type: investigation
tags: [architecture, strategy]
---

# Investigation — TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP

## The method itself is already correct — the entire gap is that nothing calls it

`BeliefCycleSystem.decay_stale_beliefs(entity, current_tick, decay_rate=0.02, stale_threshold=50)`
(`src/systems/strategic_systems/belief.py:42-79`) already implements LEG-RPG-150 exactly as
`belief_and_detour_contract.md` describes: iterates `entity.strategic.leads`, skips leads younger
than `stale_threshold` ticks (measured from `discovered_tick`), skips `EXHAUSTED` (already dead),
skips `PRECISE` (never decays via this path — matches the doc's "decay SLOWER" framing; in this
implementation "slower" is, in practice, "not at all"), demotes `APPROXIMATE→VAGUE` and
`VAGUE→EXHAUSTED`. `tests/unit/strategic/test_belief_cycle.py::TestBeliefDecay`'s 4 tests already
cover this exactly (fresh leads untouched, APPROXIMATE→VAGUE, VAGUE→EXHAUSTED, PRECISE untouched)
— these tests already pass, and this ticket does not need to change the method's own decay logic.
`decay_rate` (0.02) is an unused parameter — the method's real logic is a step-function on the
`LeadCertainty` enum, not a continuous rate; confirmed no caller of the current dead method passes
it either. Leave as a vestige unless removing it is trivially safe (check no external caller
depends on the parameter's presence during Implement).

`grep -rn "decay_stale_beliefs" src/` (excluding tests) confirms zero call sites — the finding that
opened this ticket is accurate and current.

## Where it belongs in the real pipeline

`src/engine/pipeline.py`'s own phase sequence already runs, back to back, unconditionally every
tick (neither is registered in `PhaseDependencyGraph.PHASES`, so `should_run_phase()`'s own
"phase_name not in PHASES → always run" branch applies to both):

```
line 393: strategic_intelligence  (StrategicIntelligenceSystem.fused_strategic_pass — where
                                    leads get created via rumors/observations/detours)
line 395: lead_contradiction      (LeadContradictionSystem.enforce — LEG-RPG-125)
```

The new decay phase belongs **between these two**, for one concrete, verified reason:

**Ordering vs. `lead_contradiction` — no double-decrement risk, but ordering still matters for
correctness.** `StrategicUpdate.merge()` (`src/core/updates.py:584-627`) concatenates
`leads_add_or_update` lists rather than deduplicating; `src/engine/patches.py:442-450`'s
`merge_dict()` applies them to `entity.strategic.leads` via `for item in add_list: res[item.id] =
item` — a plain dict overwrite in list order, so if two phases both touch the same lead ID in the
same tick, the **last-applied entry wins outright**, not a stacked double-decrement. Both phases
read from the same frozen `state` (not from each other's proposed update), so there's no risk of
literally decrementing certainty twice for one lead. The real question is which phase's result
should win when a lead is *both* stale and contradicted in the same tick: `LeadContradictionSystem.
enforce()` (`lead_contradiction.py:183-189`) always jumps a contradicted lead straight to
`EXHAUSTED` unconditionally, regardless of its current certainty — a stronger signal than mere
one-step staleness decay. Running decay **before** contradiction means contradiction's own
unconditional `EXHAUSTED` write is the one that lands last and wins, which is the correct outcome
(contradiction is decisive evidence; staleness is a weaker, gradual signal). Running decay after
contradiction would risk a stale-but-not-yet-EXHAUSTED lead's decay write silently overwriting a
same-tick contradiction's EXHAUSTED write — the actual failure mode the ticket's own AC is
concerned about, now root-caused precisely rather than just flagged.

Implementation shape: add a per-tick orchestrator alongside the existing pure per-entity
`decay_stale_beliefs()` (renamed — see below) in `belief.py` itself, mirroring
`LeadContradictionSystem.enforce()`'s own deterministic-iteration pattern (`sorted(state.entities.
values(), key=lambda e: e.id)`, alive+active filter, merge into a `Dict[int, EntityUpdate]`), then
wire it into `pipeline.py` via the same `run_phase("belief_staleness_decay", update, ...)` pattern
— no new `PhaseMetadata` entry needed (matches `lead_contradiction`'s own unregistered,
always-run shape).

## `capacity_enforcement.py`'s own lead-pruning interaction — verified structurally correct by
construction, real test still required per the ticket's own AC

`CapacityEnforcementPhase.enforce()` (`src/engine/pipeline_phases/capacity_enforcement.py:44-57`)
runs much later in the pipeline (after `lifecycle`/`groups`/`clan_lifecycle`/etc.), and only prunes
leads when `len(entity.strategic.leads) + len(strat_upd.leads_add_or_update) > profile.max_leads`,
scoring each candidate lead via `_score_lead()`
(`PRECISE:1.0, APPROXIMATE:0.7, VAGUE:0.3, EXHAUSTED:0.0`) and trimming the lowest-scored via
`CapacityService.trim_dict()`. Because decay's own phase runs earlier in the same tick and merges
its demoted leads into `update.entity_updates` before capacity_enforcement reads `ent_upd.
strategic`, a lead demoted this same tick (e.g. APPROXIMATE→VAGUE) is scored at its *new*, lower
value when pruning decisions are made — stale leads become more likely to be pruned under capacity
pressure than fresher ones, which is the intended, correct effect of a real staleness mechanism.
This is a structural consequence of phase ordering, not something that needs its own new
integration code — but the ticket's own AC explicitly wants this verified with a real test, not
merely inferred, so a real test constructing an over-capacity entity with a mix of fresh and stale
leads and confirming the stale one is the one pruned is still required.

## Doc/parity corrections required

`docs/simulation/belief_and_detour_contract.md`:
- Line 20: `"(this file's BeliefEntry, contradiction-tracked, decays toward staleness)"` — the
  "decays toward staleness" half is false. `BeliefEntry.certainty` is only ever changed by
  `apply_contradiction()`'s own belief-degradation branch (`certainty -= 0.3` per contradiction,
  `belief.py:181-187`) — there is no time-based decay of `BeliefEntry` anywhere, confirmed by grep
  (no other write site to `BeliefEntry.certainty` exists). Correct to state only the true half
  ("contradiction-tracked"), per this ticket's own Out of Scope (`BeliefEntry` decay is explicitly
  NOT being added here — see Scope's "Deferred to a follow-up ticket" note in the ticket body).
- Lines 66-72 ("### Staleness decay (LEG-RPG-150)"): update the method name reference once renamed
  (see below); the rest of the section's description (`APPROXIMATE→VAGUE`, `VAGUE→EXHAUSTED`,
  PRECISE decays slower, EXHAUSTED skipped) is already accurate to the real implementation and
  becomes newly *true in practice* (not just true-in-isolation) once this ticket wires it in — no
  wording change needed there beyond the method name.

`docs/parity_ledger/strategic_cognition.yaml`, entry `STRAT-239` — **found broken independent of
this ticket's own changes, and worse than a wrong citation once its own `v2_evidence` is read
closely (per peer review)**: the entry is `status: verified`, `priority: P1`, and its `text`
correctly describes `BeliefCycleSystem.decay_stale_beliefs`'s `stale_threshold=50` behavior
(APPROXIMATE→VAGUE, VAGUE→EXHAUSTED) — but its own `v2_evidence` only cites
`belief.py:47 — stale_threshold: int = 50 (default)`, which verifies that **a constant exists**,
not that the behavior it gates ever executes. Its `test_path` compounds this by citing
`tests/unit/cognition/test_information_seeking.py::TestKnowledgeStalenessDecay::
test_lead_staleness_decay_reduces_confidence` — a test that verifies a **different, unrelated**
function, `effective_certainty()` in `src/cognition/knowledge_model.py`, operating on
`KnowledgeFact` (a continuous multiplicative formula, `certainty * max(0.1, 1.0 -
elapsed*0.0001)`, nothing to do with `LeadState`'s enum step-down decay). **So this P1 entry has
been reading `verified` for a behavior that, until this ticket, had never executed once** — on the
strength of evidence that only ever confirmed a default argument. Corrected as part of this
ticket's own required parity update (see plan.md), with the history recorded honestly (what was
previously verified vs. what became true only once this ticket wired the decay in) — not silently
swapped as if the entry had always been correct.

**Adjacent finding, routed to peer review before acting, then filed rather than chased here per
this repo's standing "file it, don't fix it inline" rule**: `effective_certainty()` is itself real,
correctly unit-tested, and has **zero callers anywhere in `src/`** — the 7th instance this
session's own batch of work has found of real, tested code with no live caller. Peer review
corrected my own initial framing: `belief_and_detour_contract.md`'s claim that `KnowledgeFact` has
"no decay" is **accurate** — with zero callers, no decay genuinely happens, so the doc correctly
describes live behavior and is not flagged here. The real open question (not resolvable from code
alone) is whether this is *abandoned* intent (decay for `KnowledgeFact` was considered and
deliberately dropped) or *unfinished* intent (meant to be wired in and never was) — those imply
opposite dispositions. Filed as
`TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`, not this ticket's own
scope (`KnowledgeFact` is the sibling model, not `LeadState`/`BeliefEntry`).

## Adjacent finding while writing the `capacity_enforcement.py` interaction test — flagged, not
chased or fixed here

Constructing a real, over-capacity entity to test decay's interaction with `capacity_enforcement.
py` surfaced that `StrategicIntelligenceSystem.fused_strategic_pass()` (which runs much earlier
in the pipeline, before `belief_staleness_decay`/`lead_contradiction`/`capacity_enforcement`)
already calls `DetourSuggestionSystem.enforce_bandwidth()`
(`src/systems/strategic_systems/detour.py:147-172`), which **independently duplicates**
`capacity_enforcement.py`'s own `max_leads` pruning — same concept ("drop lowest-scoring excess
leads over `profile.max_leads`"), different scoring function (`_certainty_score` vs.
`CapacityEnforcementPhase._score_lead`), different trigger condition (`len(active_leads) >
profile.max_leads` against the frozen pre-tick `state.entities[...].strategic.leads` only, vs.
`capacity_enforcement.py`'s own merge-then-check against `state` + this tick's own
`leads_add_or_update`). Confirmed real via direct tracing: an entity constructed with 9
pre-existing leads gets pruned by `enforce_bandwidth()` during `strategic_intelligence` itself,
before `capacity_enforcement.py`'s own dedicated phase ever runs — the two systems are not
coordinated, and whichever runs first effectively wins for pre-existing over-capacity states. Not
this ticket's own scope (`enforce_bandwidth()` predates and is unrelated to LEG-RPG-150 decay) —
noted here and flagged to peer review rather than filed unilaterally, since it may already be a
known, accepted redundancy rather than a new finding.

## Rename

`decay_stale_beliefs` → `decay_stale_leads` (operates on `entity.strategic.leads`, never touches
`entity.strategic.beliefs` — the current name is exactly what caused the original misreading that
opened `TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN`'s own correction round). Update the
docstring to say "Leads decay over time" rather than "Beliefs decay over time". Grep confirms the
only references to the old name are: its own definition, its own 4 unit tests in
`test_belief_cycle.py`, and the STRAT-239 parity-ledger `text` field (a prose description, not a
code reference — will read correctly either way, but updating it to the new name keeps it current).
