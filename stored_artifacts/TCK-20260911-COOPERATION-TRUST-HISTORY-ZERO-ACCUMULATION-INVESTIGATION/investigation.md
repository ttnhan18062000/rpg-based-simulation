# Investigation — TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION

## Step 0: coverage question (answered before anything else, per peer review)
The 2470-cooperation-events / zero-trust-history measurement came from a real, explicitly
**single-episode** 500-tick run (`frontier_living_world`, seed 7) — confirmed directly from
`TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`'s own stored `test_plan.md`, which describes
it as deliberately single-episode specifically because it "doesn't depend on the survivor-
reconstruction bug." No `CampaignOrchestrator` survivor reconstruction ran at all in this
measurement — entities were spawned once via the real `WorldEntitySpawner` path. Identity was
intact. The measurement stands; no re-run was needed before proceeding.

## Step 1: real reproduction, not tracing
Reproduced the exact scenario (same world composition, same seed, same tick count) with direct
monkeypatch instrumentation on every real trust-writing function found — not just the three the
original ticket cited.

**The original ticket's central framing was wrong.** It stated "this is not the usual unwired-
path shape... the chain looks complete end to end." Confirmed, by both static grep and the live
instrumented run: `CooperationLearningService.learn()` — the rich success/rescue/abandoned/
betrayal computation with the 0.08/0.22/-0.25/-0.75 values cited as evidence the chain was real —
has **zero callers anywhere in `src/`**. It is imported into `phase.py`, never invoked. Zero calls
across 500 real ticks in the reproduction. This is exactly the "unwired path" shape this whole
audit arc has repeatedly found elsewhere (`spawn_calamity`, `decay_stale_leads` before its own
fix, etc.) — the ticket's own assumption that it looked different here did not survive checking.

**A second, independent instance of the same shape was found, one hop removed.**
`SocialAppraisalSystem.recalibrate_trust()` (`src/systems/social_systems/appraisal.py`) also
computes a real trust_delta and IS called — but only from
`StrategicIntelligenceSystem.process_outcome()` (`src/systems/strategic_systems/
intelligence.py:1150-1161`), which itself has **zero callers anywhere in `src/`**. Reachable in
principle, dead in practice.

**Exactly two real, live, wired trust-writing call sites exist in the whole codebase:**
1. `CooperationPhase.execute()`'s own party-cohesion-collapse branch (`phase.py:143-160`) — a flat
   `-0.25` toward a group's leader, fires only when `state.groups` is non-empty AND
   `PartyCohesionService.evaluate()` reports `MEMBER_ABANDONING` or `LEADER_LOST` for that group.
2. `SocialAppraisalSystem.process_betrayal()`, called from `src/engine/domain/
   combat_actions.py:83-90` — fires only when a combat attacker and its target share the same
   `identity.group_id` (same-party friendly fire).

**Both require a party/group to exist first.** In the real 500-tick reproduction, `state.groups`
was empty (0 groups) for the entire run. Confirmed via direct instrumentation of the actual
authoritative gateway, not inferred: `SocialPatch.apply()` (`src/engine/patches.py:555-558`, the
sole path any `SocialUpdate` must pass through to reach `entity.social`) was called **zero times**,
and `RelationshipService.process_update()` (the write function itself) was called **zero times
total** — not just zero times with a non-empty trust_delta. Neither of the two live gates got a
single chance to open in this run, because their shared precondition (a party exists) never
occurred.

**`RelationshipService.process_update()`'s own write logic is correct when reached** — confirmed
by direct code read (`src/systems/social_systems/relationships.py:22-40`): it correctly reads
`update.trust_delta.items()` and merges into `trust_history` with proper clamping. Nothing is
computed-and-then-discarded anywhere in this chain; every function that computes a trust_delta
would apply it correctly if it were ever called with one.

## Determination, distinguishing the two failure modes this ticket's own AC requires
- **Genuinely unwired dead code** (not a gate — permanently unreachable regardless of gameplay
  conditions): `CooperationLearningService.learn()`, and `recalibrate_trust()`'s own real intended
  path via `StrategicIntelligenceSystem.process_outcome()`.
- **A gate that never opened in this real run** (not a dropped value — a real, live, correctly-
  wired mechanism whose precondition wasn't met): the party-cohesion-collapse penalty and the
  same-party-betrayal penalty, both gated on party/group formation, which never happened once in
  500 real ticks.

## Open question, not yet chased (scope call for peer review)
Is party formation (the `FORM_PARTY` adventure route) itself ever reachable under any real
conditions, or is it the actual keystone bottleneck behind both live gates? Not investigated here
— potentially a separate, deeper question than this ticket's own scope, not resolved by assumption
either way.

## Reported to peer before deciding fix scope, per explicit instruction
Full finding reported 2026-09-12, before any fix-approach decision — pending peer review's
direction on scope before implementation begins.

## Step 2: are `learn()` and `recalibrate_trust()` alternatives, or complements? (resolved before
touching either, per peer review's explicit "don't pick the plausible one" instruction)
This session's own audit arc has hit the trap of wiring a plausible-looking mechanism without
confirming it was the *intended* one at least twice before (lead_capacity dual-mechanism
preemption; degradation.py/governor.py). Rather than guess which of `learn()`/`recalibrate_trust()`
was "the" real trust mechanism and wire that one, determined the relationship using three
independent lines of evidence:

1. **Git chronology**: `src/systems/social_systems/appraisal.py` (home of `recalibrate_trust()`)
   first committed 2026-04-28. `src/domains/cooperation/services.py` (home of `learn()`) first
   committed 2026-05-30 — about a month later. `learn()` postdates `recalibrate_trust()`, so if
   either superseded the other, it would be `learn()` superseding `recalibrate_trust()` — not
   a complementary pair added together.
2. **Design-doc provenance**: `docs/archive/entity-enhance/entity_enhance_phase7.md`, "Task 11 —
   Implement cooperation outcome learning," describes `CooperationLearningService.learn()` as its
   own deliberate, later, cooperation-specific mechanism. Line 280 states explicitly: "Cooperation
   logic is isolated from raw social contract appraisal" — the design doc itself declares these
   two mechanisms are meant to stay separate, not that one replaces the other.
3. **Test coverage asymmetry**: `learn()` has a dedicated, passing test file
   (`tests/unit/domains/cooperation/test_phase7_cooperation_learning.py`).
   `recalibrate_trust()`/`process_outcome()` has zero test coverage found anywhere in `tests/`.
   Consistent with `recalibrate_trust()` predating a later, more deliberate design (Phase 7's
   cooperation-specific mechanism) and never being revisited once cooperation's own mechanism
   landed — not consistent with two mechanisms meant to run side by side.

**Determination**: not alternatives to choose between, not complements requiring both wired for
this ticket's purpose. `recalibrate_trust()` is a separate, likely generic strategic-intelligence
trust mechanism (unrelated domain to cooperation specifically) that predates `learn()` and was
never revisited — left untouched by this ticket's fix, consistent with peer review's explicit
scope call.

## Step 3: finding `learn()`'s real, non-guessed trigger — not inventing a call site
Rather than pick a plausible call site for `learn()` and wire it there, searched for a call site
that already computes the *same value* `learn()` computes, on the theory that a hand-copied
shortcut leaves an exact numeric fingerprint. Found it: `CooperationPhase.execute()`'s own party-
cohesion-collapse branch (the `MEMBER_ABANDONING`/`LEADER_LOST` handling) hardcoded
`new_trust[leader_id] = ... - 0.25` — an **exact match** to `learn()`'s own `"abandoned"` outcome
type (`trust_delta = -0.25`), while silently dropping `grudge_delta` (`+0.3` for that same outcome
type) and `future_preference_modifier`. This is real evidence of intent, not an assumption: someone
computed `learn()`'s "abandoned" value by hand instead of calling `learn()` itself.

**Fix applied**: replaced the inline hardcode with a real `CooperationOutcomeEvent(tick=state.tick,
partner_id=g_rec.leader_id, outcome_type="abandoned", description=...)` + `CooperationLearningService
.learn(mb, outcome, state)` call, applying both `trust_delta` and `grudge_delta` to the
`SocialUpdate`. `future_preference_modifier` deliberately left unwired and disclosed in a code
comment — no existing `SocialUpdate`/`SocialComponent` field exists for it anywhere in the codebase;
Phase 7's own "future partner preference"/"cooperation memory" design intent was apparently never
built as a real field. A real, out-of-scope gap, not a silent drop.

Deliberately did NOT guess triggers for `learn()`'s other three outcome types
(`"success"`/`"rescue"`/`"betrayal"`) — see Step 4.

## Step 4: investigated and rejected wiring trust through contract-expiry resolution
The closest real candidate for a "success"/"rescue" cooperation-outcome signal was
`ContractService.process_active_contracts()`'s own contract-expiry resolution
(`src/systems/social_systems/contracts.py:293-`), the real, live, only-production caller of
`resolve_contract_outcome()`. Investigated it directly rather than wiring trust through it on the
strength of "it's live and it's an outcome":

- It calls `resolve_contract_outcome(entity, c_id, success=True, tick=current_tick)`
  **unconditionally**, on every contract expiry — never checking whether the contract's actual
  terms were fulfilled, and never detecting betrayal (`betrayal`/`betrayer_id` are never passed
  despite the function supporting them). Self-disclosed as a pre-existing gap in the file's own
  docstring (`compute_betrayal_clan_reputation_update()`, lines 269-280).
- It writes a different social axis entirely (`bonds`/`heroism_delta`/`notoriety_delta` via
  `SocialUpdate.bond_updates`), not `trust_delta`/`trust_history`.

Per peer review's explicit instruction ("Build the abandoned fix. Don't build the contract path" —
wiring trust through an unconditionally-`True` signal "would produce meaningless uniformly-positive
values... the same shape as raiders spawn but walk to (0,0): a fix that passes its own acceptance
criterion while delivering nothing"), this path was not used. Filed as its own separate ticket
(`TCK-20260912-CONTRACT-EXPIRY-ALWAYS-RESOLVES-SUCCESS-REGARDLESS-OF-OUTCOME`) instead of guessing
a trigger the codebase does not actually support yet.

## Final closure determination
This ticket closes on its own real, narrower claim: two dead trust-writing mechanisms identified
with real evidence (not assumed), one confirmed inline-shortcut bug repaired and proven against the
real service's own output, and the cooperation/appraisal separation confirmed as the project's own
intended design via three independent evidence sources — not guessed. It explicitly does not claim
"trust demonstrably accumulates in a real run": the repair, while correct, is itself gated on party
formation, which never occurred once in the real 500-tick reproduction. That acceptance bar is
transferred, as its own explicit AC line (not a footnote), to
`TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`, filed from this investigation's own
findings and framed as the keystone for this whole thread — its resolution would also unblock party
cohesion dynamics, the `FORM_PARTY` adventure route, and both live trust writers this ticket
confirmed.
