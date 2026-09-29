---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY
artifact_type: plan
tags: [cognition, simulation-quality, root-cause]
---

# Implementation Plan — TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY

## Summary
This is an assessment ticket: `investigation.md` already contains the substantive findings
(Q1 empirical confirmation, Answer 2's 9-item trace enumeration, Answer 3's situated-
encounterability split, the developer-only-surface enumeration, and the hidden-truth-leak check).
No production code changes are in scope. The plan's job is threefold: (1) pin the investigation's
empirical findings into the ticket body itself so they are the ticket's permanent record, not only
`investigation.md`'s; (2) commit four new regression-pinning tests from `test_plan.md` so the
findings cannot silently regress or be re-derived from scratch later; (3) route the findings into
`docs/plans/systemic_world/roadmap.md` §7.2 and §11 item 3, per AC7/AC9 — this is the one real
`docs/` deliverable this ticket produces, and it must not be skipped just because
`investigation.md`'s own "Docs Requiring Update" section said none (that section was scoped to
Mechanics-Bible/contract/parity-ledger docs only, not the roadmap routing destination AC9 itself
names). No registry correction is needed (AC8 — the `perception` mechanism entry was already
corrected by `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` before this ticket started;
verified below in Step 5, not assumed).

## Steps

### Step 1 — Record Answer 2 / Answer 3 findings in the ticket body (AC1, AC2, AC3, AC4, AC5, AC6)
**Files:** `tickets/inprogress/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY.md`
**Change:** Fill in `## Implementation Notes` with a condensed, ticket-body copy of
`investigation.md`'s findings, kept strictly separated per AC1:
- Q1 result: empirically confirmed (not `BLOCKED_WITH_REASON`) via a real `Kernel.tick_once()`
  forced-attack scenario (`mechanic_scenario_combat_judgement_withdrawal`, goblin id 1 vs orc id 2,
  orc hp forced to 1.0), producing `orc.lifecycle.death_reason == "COMBAT"`,
  `orc.lifecycle.active == False` in the same tick — through the real
  `CombatResolutionSystem.resolve_attack()` → `LifecycleSystem.resolve_lifecycle()` path
  (`src/systems/lifecycle_systems/lifecycle.py:202-217`, confirmed by direct read in
  `investigation.md`'s Q1 section). Caveat carried forward: `registries/mechanisms.yaml`'s
  `tactical_decision` entry (`verified: corpus_run, verdict: contradicted`, 2026-09-19) shows real
  unscripted `ATTACK` dispatch is rare (0-2 per 1000-2000 ticks); this is a scripted-but-real proof,
  not a claim combat deaths are common.
- Answer 2 (trace existence, 9 items): lifecycle deactivation+classification
  (`lifecycle.py:206-218`), heir dying-wish/inherited-feud writes (`lifecycle.py:220-239`),
  heirloom/inventory transfer with no provenance marker (`lifecycle.py:241-263`, confirmed by
  direct read of the `ResourceTransferIntent(source_kind="CHEST", transfer_kind="AUTO")`
  construction at `lifecycle.py:252-263` — no field on that intent identifies the transfer as
  inheritance-derived), faction influence shift (`lifecycle.py:268-272`), conquest/stronghold
  lifecycle (`lifecycle.py:273-276`), economic vacancy signal (`lifecycle.py:277-278`), the grief
  trigger for trusted allies (`src/observability/event_extractor.py:1722-1762`, confirmed by direct
  read: `detect_grief_triggers()` walks `current_state.entities`, checks
  `other.social.trust_history.get(eid, 0.0) >= ALLY_TRUST_THRESHOLD`, no proximity/position check
  anywhere in the method), developer-only observability surfaces, and the "§13.7 witnessing combat
  does not exist as a runtime mechanism" finding.
- Answer 3 (situated encounterability, kept separate): the grief trigger is the ONLY real trace any
  runtime consumer legitimately receives, and ONLY for bonded allies (`trust_history >= 0.30`) —
  never for a co-located-but-unbonded observer, since the path has zero proximity check. All other
  traces (inheritance, faction, conquest, economy) exist but are not encounterable by any observer
  today, per `PerceivedEntity`'s narrow schema (`src/core/cognition.py:28-33`, confirmed by direct
  read: fields are exactly `entity_id, kind, position, salience, confidence` — no item/event field)
  and `PerceptionUpdatePhase`'s zero production call sites (cited from
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`, not re-derived, per AC6).
- Developer-only surfaces explicitly enumerated (AC3): `CombatDamageEvent`/`CombatKillEvent`/
  `hero_death_unrecorded` (`event_extractor.py:441-517`), `event_shapers.py::CombatShaper`,
  `GriefUrgencyTriggeredEvent`/`NemesisRelationFormedEvent`, `src/observability/live/*`,
  `src/api/presenters/*`, the `REFINED_UPDATE` replay stream.
- Hidden-truth leak check (AC4): `cognition.motivation.named_intention` — no reader projects it
  outward, no leak found; `strategic.blockers` — not implicated by this event's trace set; the
  grief trigger's location-independence named as a situatedness gap, not a hidden-field leak,
  routed to roadmap §11 item 3 (not fixed here, per Out of Scope).
- AC5 evidence: the Q1 proof was a throwaway scratch script run against a pre-existing test
  fixture; `git status`/`git diff` show no `src/` file modified during this investigation.
- AC6: `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s three-finding breakdown is cited
  verbatim, not re-derived; no contradiction found between this ticket's runtime observation and
  that ticket.
Also fill `## Test Summary` (list the 4 new tests from Step 2-4 plus the regression-surface
command) and leave `## Files Changed` / `## Completion Summary` for ticket close.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets`,
`## Related Code Areas` sections of the ticket — those are already correct and settled; do not
re-litigate Q1/Q2/Q3 framing decisions already resolved in `investigation.md`'s Assumptions
section.
**Verify:** No test — this is a documentation-only step. Verified by re-reading the filled
sections against `investigation.md` for fidelity (no new claims introduced beyond what
`investigation.md` already found).

### Step 2 — Add the Q1 regression-pinning test (AC2)
**Files:** `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py` (new file)
**Change:** Add `test_forced_combat_kill_produces_combat_death_reason_in_one_tick`, following the
exact structure of `tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py`
(same `_compile_world()` pattern, same `WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"`,
`GOBLIN_ID = 1`, `ORC_ID = 2`). Force `orc.combat.hp = orc.combat.max_hp = 1.0`, force goblin's
`TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 2})`, run one
`kernel.tick_once()`, assert `orc.lifecycle.active is False` and
`orc.lifecycle.death_reason == "COMBAT"` on the resulting state. Docstring must explicitly state
this is a scripted forced attack pinning dispatch-routing correctness, not evidence that combat
deaths are common in unscripted corpus play (per test_plan.md's own Anti-Drift Test Guards, so a
future reader does not misread this test as a corpus-frequency claim) — cite
`registries/mechanisms.yaml`'s `tactical_decision` entry directly in the docstring for that caveat.
**Do NOT touch:** the existing `test_combat_attributes_real_fight_outcome_value_differential.py`
file itself — `test_plan.md` explicitly calls for a new file "to avoid embedding a
differently-scoped assertion into the existing differential-value test file."
**Verify:** `pytest tests/mechanic_scenarios/test_combat_death_trace_encounterability.py -q`
(new test passes); `pytest tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py tests/mechanic_scenarios/test_combat_judgement_withdrawal.py -q` (existing regression surface unaffected).

### Step 3 — Add the grief-trigger bonded-vs-co-located regression-pinning test (AC1, AC3)
**Files:** `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py` (same new file
as Step 2)
**Change:** Add
`test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death`. Build a
scenario with three entities: the dying combatant, a trusted-ally observer (not co-located,
`social.trust_history[dead_id] >= ALLY_TRUST_THRESHOLD` from `src.core.social_constants`), and an
unrelated co-located/adjacent entity with no bond. Run the forced-kill tick (reuse Step 2's setup).
Assert the trusted-ally observer's `strategic.concerns` gains a `ConcernState` keyed
`grief_ally_{dead_id}` (per `event_extractor.py:1722-1762`'s `detect_grief_triggers()` →
`Kernel._drain_pending_grief_triggers()` → `GriefUrgencyImporter.build_strategic_update()`), and
assert the unrelated co-located entity's `strategic.concerns` gains nothing. This is the test that
pins Answer 2/Answer 3's own separation in code (test_plan.md's own framing) — if the grief trigger
ever becomes proximity-gated or some other path becomes perception-routed, this test fails loudly
rather than the distinction eroding silently.
**Do NOT touch:** `src/observability/event_extractor.py`, `src/domains/campaigns/grief_urgency.py`,
or `src/engine/kernel.py`'s `_drain_pending_grief_triggers()` — this step observes existing
behavior only; do not add a proximity check even though Answer 3 names it as a gap (that
remediation is explicitly Out of Scope, routed to roadmap §11 item 3 instead, per Step 5).
**Verify:** `pytest tests/mechanic_scenarios/test_combat_death_trace_encounterability.py -q`;
`pytest tests/integration/campaigns/test_mid_episode_grief_trigger.py -q` (existing grief regression
surface — `test_mid_episode_entity_death_triggers_grief_concern_via_apply_path`,
`test_mid_episode_death_does_not_duplicate_episode_boundary_grief`,
`test_death_on_final_tick_still_applies_grief_concern_same_episode` — unaffected).

### Step 4 — Add the inheritance-provenance and PerceivedEntity schema-guard tests (AC4)
**Files:** `tests/unit/progression/test_lifecycle.py` (extend); `tests/unit/domains/perception/test_phase12_perception_filter_service.py` (extend)
**Change:**
1. In `test_lifecycle.py`, add `test_inheritance_transfer_carries_no_provenance_marker`, placed
   near the existing heir-transfer tests (`test_succession_and_heirloom_transfer` at line 80,
   `test_manual_heir_entity_id_transfers_even_if_heir_inactive` at line 114 — same fixtures).
   Assert the `ResourceTransferIntent` built by `resolve_lifecycle()`'s heirloom-transfer branch
   (`lifecycle.py:252-263`) has no field identifying the transfer as inheritance-derived — i.e.
   iterate its dataclass fields (`source_id`, `source_kind`, `items_add`, `transfer_kind`) and
   assert none encodes provenance/origin. This pins Answer 2 item 3 as a named gap, not a bug, so a
   future shape change to the intent is a conscious decision.
2. In `test_phase12_perception_filter_service.py`, add
   `test_perceived_entity_has_no_item_or_event_fields` as a field-set guard: assert
   `{f.name for f in dataclasses.fields(PerceivedEntity)} == {"entity_id", "kind", "position",
   "salience", "confidence"}` (confirmed exact field set by direct read of
   `src/core/cognition.py:28-33`). This is an architecture-guard test, not a behavior test — it
   pins the structural reason Answer 3 found even a fully-wired `PerceptionUpdatePhase` could not
   carry combat-death content today.
**Do NOT touch:** `src/core/cognition.py`'s `PerceivedEntity` dataclass itself, and do not add any
new field to it — that would be building perception capability, explicitly Out of Scope.
**Verify:** `pytest tests/unit/progression/test_lifecycle.py -q`;
`pytest tests/unit/domains/perception/test_phase12_perception_filter_service.py -q`.

### Step 5 — Confirm AC8 (registry correction) is a no-op, cite evidence in the ticket
**Files:** none changed; read-only verification against `registries/mechanisms.yaml`
**Change:** No file edit. Confirm, by direct read of `registries/mechanisms.yaml`'s `perception`
mechanism entry, that it already reflects the "zero production call sites" state (corrected by
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` per `investigation.md`'s own Risks and
Open Questions section) and that no other mechanism entry touched by this investigation's trace set
(`tactical_decision`, `succession`/`aging_death`, `combat_resolution`) now contradicts its recorded
state. Record this confirmation (entry name, current recorded fields) in the ticket's
`## Implementation Notes` alongside Step 1's findings, satisfying AC8 by evidencing "no correction
needed" rather than leaving AC8 unaddressed.
**Do NOT touch:** `registries/mechanisms.yaml` itself — do not write a correction where none is
needed; do not add a new mechanism entry for the grief trigger or the witnessing-combat gap (both
belong to roadmap routing in Step 6, not the mechanism registry).
**Verify:** No test. Verified by citing the exact `registries/mechanisms.yaml` entry read (line
range) in the ticket body.

### Step 6 — Route findings into the systemic-world roadmap (AC7, AC9)
**Files:** `docs/plans/systemic_world/roadmap.md`
**Change:** Two additions, both appended (never rewriting existing settled text):
1. **§7.2** (after the existing "Minimal provisional observer position + evidence packet" content,
   which ends at line 597 with Negative check 2): append a new subsection
   `### 7.2.1 Combat-death trace findings (Epic B0, TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY)`
   summarizing, in the roadmap's own prose style: Q1 empirically confirmed; Answer 2's 9-item trace
   set; Answer 3's split (grief trigger is the only legitimate trace, bonded-only,
   location-independent — named as a tension with the epistemic principle per §2/§3.4, not
   resolved); the inheritance-transfer no-provenance-marker finding (reusing, not duplicating, the
   existing §7.2 aging-death finding for the identical transfer mechanism); the developer-only
   surface enumeration. Explicitly state this closes the combat-specific half of §11 item 3's
   Epic B0 owner note, using the aging-death lineage case (already in §7.2) as the sibling finding.
2. **§11 item 3** (lines 778-792): append a new bullet under the existing "Owner: first-wave Epic
   B0" paragraph (do not edit the existing bullets/paragraph text) recording the resolution:
   perception update phase confirmed still inactive (consistent with, not new evidence beyond,
   `TCK-20260920-...`'s finding); the ONE new finding this ticket adds beyond that ticket is the
   grief trigger's location-independence as a live, real (non-perception) trace path with no
   distance/channel constraint — named as worth a future look under the epistemic principle, not
   remediated. State plainly that this does NOT re-rank Epic B above lineage work per item 3's own
   decision criterion, because the grief trigger is a real, working, bonded-only trace path (not
   evidence that NPCs are non-situated observers across the board) — the broader
   perception-is-an-engine-gap question remains owned by `TCK-20260920-...`, unchanged.
**Do NOT touch:** §7.1, §7.3, §7.4, §8, §9, §10, or any other §11 item (1, 2, 4, 5, 6) — none of
those are implicated by this ticket's findings. Do not touch the Appendix (historical review log).
Do not edit any text inside the existing §7.2 body (lines 553-597) — append only.
**Verify:** No test (docs-only). Verified by re-reading the appended sections against AC7 (no
findings recorded against PERC-01/KNOW-01 anywhere in the diff — grep the diff for those strings
and confirm zero matches) and AC9 (findings present under §7.2 and §11 item 3, in
`world-rule-catalog-design`'s roadmap file).

### Step 7 — Run the full scoped regression surface (all ACs, final gate)
**Files:** none (verification only)
**Change:** Run the exact scoped commands from `test_plan.md`'s "Scoped Pytest Commands" section:
```
pytest tests/unit/progression/test_lifecycle.py \
       tests/unit/observability/test_event_extractor_world.py \
       tests/unit/domains/campaigns/test_grief_urgency.py \
       tests/unit/world/test_sense_perception_gate.py \
       tests/unit/domains/perception/ \
       tests/integration/domains/perception/ \
       tests/integration/scenarios/test_phase12_perception_attention_scenarios.py \
       tests/integration/campaigns/test_mid_episode_grief_trigger.py \
       -q
pytest tests/mechanic_scenarios/test_combat_death_trace_encounterability.py -q
pytest tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py \
       tests/mechanic_scenarios/test_combat_judgement_withdrawal.py -q
pytest tests/simulation_quality/test_social_scorer.py -k Grief -q
pytest tests/simulation_quality/test_heir_inventory_transfer_corpus.py -q
```
Never run `pytest tests/`. Record pass/fail counts in the ticket's `## Test Summary`.
**Do NOT touch:** no file changes in this step.
**Verify:** All commands above exit 0.

## Scope Guards
- No perception wiring: do not add any call site for `PerceptionUpdatePhase`, do not connect
  `PerceptionGate` to the death/lifecycle/grief path.
- No proximity/distance gate added to the grief trigger (`event_extractor.py:1722-1762`) — the
  location-independence finding is named and routed to roadmap §11 item 3, not fixed.
- No new field added to `PerceivedEntity` (`src/core/cognition.py:28-33`) or to
  `ResourceTransferIntent` to carry provenance — both gaps are named findings, not remediated here.
- No change to `registries/mechanisms.yaml`, `registries/rule_mechanism_edges.yaml`, or
  `registries/rule_classifications.yaml` — AC7 forbids recording against `PERC-01`/`KNOW-01`, and
  Step 5 confirms no other entry needs correction.
- No change to any Mechanics Bible chapter, engine contract, or parity ledger entry —
  `investigation.md`'s "Docs Requiring Update" and "Parity Ledger Overlap" sections both confirm
  existing entries (`STRAT-273`, `COMB-309`, `COMB-311`, `SOC-231`, `SOC-246`) already correctly
  reflect current behavior.
- No edit to any existing text inside roadmap.md's §7.2 (lines 553-597) or §11 item 3's existing
  bullets (lines 778-792) — append only, per the roadmap's own "stop revising except to record
  verified results" governance note (§11 item 6).
- No work on `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` or
  `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — both are independent, out-of-scope
  tickets; cite, do not touch.
- No player-facing projection, presentation, or UI work of any kind.
- No claim of `PLAYER-EXPERIENCED` anywhere in the ticket body, tests, or roadmap additions.

## Dependency Map
- Step 1 depends on nothing; can run first or in parallel with Steps 2-5.
- Steps 2, 3, and 4 are independent of each other (different files) but Step 3 reuses Step 2's
  world-compile fixture in the same new test file, so Step 3 should follow Step 2 sequentially
  within that file (not a hard blocking dependency — both could be written together in one pass).
- Step 5 is independent of Steps 1-4 (pure registry read).
- Step 6 is independent of Steps 2-5 (docs-only) but should reflect the same findings written in
  Step 1, so Step 6 should follow Step 1.
- Step 7 depends on Steps 2, 3, and 4 being complete (it runs the tests they add).

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — Answers 2 and 3 reported separately | Step 1 (ticket body), Step 3 (test pins the separation), Step 6 (roadmap) | `test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death` |
| AC2 — specified combat-death event used, not substituted, or BLOCKED_WITH_REASON | Step 1, Step 2 | `test_forced_combat_kill_produces_combat_death_reason_in_one_tick` |
| AC3 — developer-only surfaces enumerated and excluded | Step 1, Step 3 (co-located-unbonded assertion) | `test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death` |
| AC4 — hidden-truth leak check named, min. cognition/strategic fields | Step 1, Step 4 | `test_inheritance_transfer_carries_no_provenance_marker`, `test_perceived_entity_has_no_item_or_event_fields` |
| AC5 — no production behavior altered, evidenced | Step 1 (evidence statement), Step 7 (regression surface green) | full scoped regression run |
| AC6 — TCK-20260920 findings cited not re-derived, contradictions reported | Step 1 | none (documentation check) |
| AC7 — never recorded against PERC-01/KNOW-01 | Step 6 (grep-verified in diff) | none (documentation check) |
| AC8 — registry entry corrected if it differs from real state | Step 5 (confirms no-op, cites evidence) | none (read-only verification) |
| AC9 — findings routed to roadmap §7.2 and §11 item 3 | Step 6 | none (documentation check) |

## Anti-Drift Notes
- Do not let Step 2/3's new tests drift into a claim that combat deaths are common in unscripted
  corpus play — the docstring caveat citing `registries/mechanisms.yaml`'s `tactical_decision`
  entry (`verdict: contradicted`, 0-2 real attacks per 1000-2000 ticks) is load-bearing, not
  optional flavor text.
- Do not fold the grief-trigger location-independence finding into a "fix" during Step 3 or Step 6
  — it is named and routed, per the ticket's Out of Scope and roadmap §11 item 6's governance note
  against unnecessary revision.
- Do not conflate the grief trigger with "perception" anywhere in Step 1's ticket-body writeup or
  Step 6's roadmap additions — it runs through `event_extractor.py`/`GriefUrgencyImporter`, never
  through `PerceptionGate`, `PerceptionFilterService`, or any perception-domain code.
- Step 6's roadmap edit must stay append-only. §11 item 6 explicitly asks this track to "stop
  revising these documents except to record verified results" — rewriting existing §7.2/§11 prose
  instead of appending would itself violate that governance note.
- If Step 5's registry read finds anything contradicting `investigation.md`'s AC8 conclusion (i.e.
  an entry genuinely needs correction), stop and flag it rather than silently correcting it beyond
  what's described here — that would be new information not yet reviewed against AC7's boundary.

## Deviations

All 7 steps were completed as planned; none was skipped or substituted. Two implementation
details were not fully specified by the plan and were resolved during implementation, both
strengthening rather than narrowing the intended pin:

1. **Step 3's test needed two `kernel.tick_once()` calls, not one.** The plan says "run the
   forced-kill tick (reuse Step 2's setup)" without specifying tick count. Following the same
   detect-tick-N / apply-tick-N+1 sequencing `tests/integration/campaigns/
   test_mid_episode_grief_trigger.py` already establishes for this exact code path
   (`Kernel._drain_pending_grief_triggers()`), the implemented test runs tick 1 (death + grief
   trigger detected and queued) and asserts against `kernel._pending_grief_triggers` first, then
   clears the goblin's now-stale forced `ATTACK` task (its target is dead) before tick 2, which
   drains the queue into the real `strategic.concerns` write the plan's own assertion target
   describes. The task-clearing step avoids an unrelated confound (post-death re-targeting
   behavior, out of scope for this test) and is not itself a behavior change — it operates only on
   the test's own staged state between two `tick_once()` calls.
2. **Step 4's provenance-marker test checks a broader field set than the 4 fields the plan names.**
   The plan's own text lists `source_id, source_kind, items_add, transfer_kind` as the fields to
   iterate; `ResourceTransferIntent`'s real dataclass (`src/core/update_models/resources.py:12-38`)
   has additional fields (`items_remove, gold_delta, gold_cost, price_multiplier, xp_reward,
   transaction_id, group_id, is_group_required`, and several contingent-update fields). The
   implemented test iterates ALL real dataclass fields via `dataclasses.fields()` rather than a
   hardcoded subset, and additionally pins `transfer_kind`'s `source_kind == "CHEST"` value
   against the identical value `src/systems/economy_systems/chests.py` uses for an ordinary
   chest-opening transfer (confirmed by direct grep during implementation) — the concrete evidence
   for "an observer could not distinguish inheritance from any other acquisition" that
   investigation.md's Answer 2 item 3 already asserts in prose.

No step was skipped, no acceptance criterion was left unaddressed, and no scope guard was
crossed — see the ticket's own `## Implementation Notes` for the full findings write-up.
