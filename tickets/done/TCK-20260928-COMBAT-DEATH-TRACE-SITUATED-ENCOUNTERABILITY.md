---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY
phase: done
date: 2026-09-28
tags: [cognition, simulation-quality, root-cause]
---

# TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY

## Title
Which traces does a combat death leave in an ordinary corpus run, and which of them could a
co-located or bonded observer legitimately receive?

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Observation of current behaviour only. Given a combat death in an ordinary corpus run, answer two
questions **separately**: which world-state changes or events it leaves behind, and which of those a
specified situated observer could legitimately receive — from where, and when.

A trace that exists but **cannot be encountered** is a valid outcome, reported as such. **This is
not a player-experience proof**, and nothing here claims `PLAYER-EXPERIENCED`.

Implements Card B0 of `docs/plans/systemic_world/ticket_planner_handoff.md` (branch
`systemic-world-roadmap-proposal` @ `43db4a7fc`, PR #249, unmerged) — **minus its first question**,
which is already owned; see Scope.

## Scope
- **Specified event, not substitutable:** a combat death in an ordinary corpus run — an entity
  killed in combat and recorded with `death_reason == "COMBAT"`. It does **not** depend on natural
  aging. If ordinary runs produce no combat death, the event question closes
  `BLOCKED_WITH_REASON`. **Do not substitute another event** — a replacement is a scoping decision
  returned to the roadmap.
- **Answer 2 — trace existence.** Which world-state changes or events does that death leave behind?
- **Answer 3 — situated encounterability.** Which of those traces could a co-located or bonded
  observer legitimately receive, from where, and when?
- Identify which surfaces are **developer-only and must be excluded** — event logs, inspectors, API
  presenters.
- Identify whether any existing path **leaks hidden truth**, e.g.
  `cognition.motivation.named_intention`, `strategic.blockers`, or location-independent reads.

## Out of Scope
- **Card B0's question 1 — "is perception live in production at runtime?" — is NOT in this ticket.**
  It is already owned by the open P1 ticket
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`, which answers it in more depth than a
  fresh runtime check would: it documents **three** distinct perception-shaped things and that
  nothing declares which is meant to be real. Adopt that ticket's findings; do not re-derive them.
  See Assumptions for why this matters.
- **Building or wiring perception.** If perception is inactive at runtime, record it as an engine
  foundation finding and close that strand with that result. The roadmap then proposes a separate
  perception-foundation epic. **Do not expand this ticket into building perception.**
- Turning on or changing perception in production. Any runtime check must observe current behaviour
  without altering it.
- Any player-facing projection, presentation, or UI work.

## Acceptance Criteria
1. Answers 2 and 3 are reported **separately**, never collapsed into one verdict.
2. The specified combat-death event was used, or the strand closed `BLOCKED_WITH_REASON` because an
   ordinary run produced no combat death. No substitute event was used.
3. Developer-only surfaces are explicitly enumerated and excluded from any encounterability claim.
4. Any hidden-truth leak found is named with its path, at minimum covering the private
   cognition/strategic fields listed in Scope.
5. No production behaviour was turned on or altered — the check is observation only, and this is
   evidenced.
6. `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s existing findings are cited for the
   perception-liveness question rather than re-derived, and any place where this ticket's runtime
   observation **contradicts** that ticket is reported as a contradiction rather than silently
   overriding it.
7. **Findings are NEVER recorded against SCP rows `PERC-01` / `KNOW-01`.** Those rows map only
   Combat's `tactical_decision`; observer evidence there would corrupt Combat's mapping. Record in
   roadmap §7.2 and §11 item 3 instead.
8. If a perception mechanism's real state differs from its registry entry, the entry is corrected
   through the registry process.
9. Findings are routed back to the systemic-world roadmap track (`world-rule-catalog-design`).

## Related Tickets
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — **open, P1, adopted for Card B0's
  question 1.** Explicitly framed as a scope-of-concept decision for the roadmap session, and
  deliberately reframed by peer review *away from* "just wire it up". Do not undo that framing.
- `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` — parallel wave item, independent.
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — Card C1; also concerns combat death, but at
  the authority/ordering level rather than the trace level. **Moved out of this folder to
  `tickets/todos/` top level 2026-09-29 and dispatched separately** (see its own Placement Note) —
  it carries a sequencing dependency on the held sovereignty-consolidation ticket that this ticket
  does not. Still independent of this one; do not wait on it.

## Related Docs
- `docs/plans/systemic_world/ticket_planner_handoff.md` — Card B0 (@ `43db4a7fc`).
- `docs/plans/systemic_world/roadmap.md` §7.2.
- `docs/plans/systemic_world/first_wave_plan.md` §2 Epic B0.

## Related Stored Artifacts
- `docs/plans/systemic_world/evidence/2026-09-27-inheritance-observer-encounter-findings.md` (on the
  unmerged branch above).

## Related Code Areas
- `src/core/cognition.py:28-33` — the perceived-entity record: id, kind, position, salience,
  confidence only. **No item fields.**
- `src/observability/event_extractor.py:1722-1762` — the grief trigger for trusted allies;
  location-independent, and carries the death rather than any inheritance.
- `src/systems/lifecycle_systems/lifecycle.py:252-257` — inheritance transfer, which carries **no
  origin marker**.
- `src/domains/perception/` — `filter.py::PerceptionFilterService`, `phase.py::PerceptionUpdatePhase`
  (the abstraction with no production caller).
- `src/world/perception/gate.py::PerceptionGate` — live and wired via `src/engine/tactical.py:181,199`.

## Assumptions / Open Questions
- **Why question 1 was split out rather than scoped here.** Card B0 states its own evidence limit:
  *"'Perception not live' comes from a grep and is `UNKNOWN` until a run confirms it. Perception may
  run through another path."* That other path is **already identified** in
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`: strategic cognition sources situational
  awareness through a direct `SpatialQueryService.nearby_entities()` call, and `PerceptionGate` does
  raw sense-detection for tactical targeting. Scoping question 1 fresh here would re-derive one of
  that ticket's three findings, eight days later and less completely — and risks landing the
  "just wire it up" conclusion it was explicitly reframed to prevent.
- **Q1.** Do combat deaths actually occur in an ordinary corpus run? This gates everything below and
  may itself close `BLOCKED_WITH_REASON`.
- **Q2.** Which traces could a co-located *or bonded* observer legitimately receive — and does the
  distinction between co-located and bonded change the answer? The grief trigger is
  location-independent, which makes this non-obvious.
- **Q3.** Is a trace that exists only in an event log a trace at all, for this ticket's purposes?
  Default: no — that is a developer-only surface. State the reasoning rather than assuming.
- **Contract-level risk.** Any runtime check must not turn on or change perception in production.

## Implementation Notes

This is an observation/assessment ticket. No production code changed. `investigation.md` (in
`staging_artifacts/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY/`) contains the full
evidence trail this section condenses; nothing below is a new claim beyond what that file already
established.

**Q1 — empirically confirmed, not `BLOCKED_WITH_REASON`.** A real, deterministic
`Kernel.tick_once()` forced-attack scenario (`mechanic_scenario_combat_judgement_withdrawal`,
goblin id 1 vs orc id 2, orc `combat.hp`/`max_hp` forced to 1.0) produced
`orc.lifecycle.death_reason == "COMBAT"` and `orc.lifecycle.active == False` in the same tick,
through the real `CombatResolutionSystem.resolve_attack()` -> `LifecycleSystem.resolve_lifecycle()`
path (`src/systems/lifecycle_systems/lifecycle.py:202-217`). Now pinned in
`tests/mechanic_scenarios/test_combat_death_trace_encounterability.py::
test_forced_combat_kill_produces_combat_death_reason_in_one_tick` (previously only a throwaway
scratch script). Caveat carried forward: `registries/mechanisms.yaml`'s `tactical_decision` entry
(`verified: corpus_run, verdict: contradicted`, 2026-09-19) shows real unscripted `ATTACK` dispatch
is rare (0-2 per 1000-2000 ticks across three real corpus worlds) -- this is a scripted-but-real
proof of dispatch-routing correctness, not a claim combat deaths are common in unscripted play.
Both facts recorded, not merged.

**Answer 2 — trace existence (kept strictly separate from Answer 3, per AC1).** All of the
following are produced in the same tick a combat death resolves
(`LifecycleSystem.resolve_lifecycle()`, `lifecycle.py:189-295`):
1. Lifecycle deactivation + death classification (`lifecycle.py:206-218`) -- durable, authoritative.
2. Heir dying-wish/inherited-feud writes (`lifecycle.py:220-239`) -- pure cognition/strategic
   private state, not player-observable by construction.
3. Heirloom/inventory transfer (`lifecycle.py:241-263`) via a plain
   `ResourceTransferIntent(source_kind="CHEST", transfer_kind="AUTO")` -- carries no origin/
   provenance marker; indistinguishable from any other CHEST-sourced transfer
   (`src/systems/economy_systems/chests.py` uses the identical `source_kind`). Now pinned in
   `tests/unit/progression/test_lifecycle.py::test_inheritance_transfer_carries_no_provenance_marker`.
4. Faction influence shift (`lifecycle.py:268-272`).
5. Conquest/stronghold lifecycle (`lifecycle.py:273-276`).
6. Economic vacancy signal (`lifecycle.py:277-278`).
7. Grief trigger for trusted allies (`src/observability/event_extractor.py:1722-1762`,
   `detect_grief_triggers()`, drained via `Kernel._drain_pending_grief_triggers()`) -- a real
   authoritative `StrategicUpdate` write into `entity.strategic.concerns`, keyed purely on
   `trust_history`, with no proximity/perception check anywhere in the path.
8. Developer-only observability surfaces (enumerated below, AC3).
9. `docs/mechanics/04_strategic_cognition.md` §13.7's "witnessing combat" tier does not exist as a
   runtime mechanism -- §13 is explicitly headed "Status: declared, not yet implemented," and
   parity ledger `STRAT-273` (`status: missing`, P1) independently confirms it. There is therefore
   no runtime path today by which any entity other than a trusted ally (item 7) receives anything
   about a combat death.

**Answer 3 — situated encounterability (kept strictly separate from Answer 2, per AC1).** The
grief trigger is the ONLY real trace any runtime consumer legitimately receives, and ONLY for
bonded allies (`trust_history >= ALLY_TRUST_THRESHOLD`, 0.30) -- never for a co-located-but-
unbonded observer. All other traces (inheritance, faction, conquest, economy) exist but are not
encounterable by any observer today: `PerceivedEntity` (`src/core/cognition.py:28-33`) has exactly
`entity_id, kind, position, salience, confidence` -- no item/event field -- and
`PerceptionUpdatePhase` has zero production call sites (cited from
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`, adopted per Scope, not re-derived, per
AC6). Both findings pinned in code:
`tests/mechanic_scenarios/test_combat_death_trace_encounterability.py::
test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death` (a bonded,
non-co-located observer receives the real `ConcernState`; a co-located, unbonded observer receives
nothing) and `tests/unit/domains/perception/test_phase12_perception_filter_service.py::
test_perceived_entity_has_no_item_or_event_fields` (the structural reason a fully-wired perception
phase still could not carry this content).

**Developer-only surfaces, explicitly enumerated and excluded (AC3):** `CombatDamageEvent`,
`CombatKillEvent`, `hero_death_unrecorded` `SimulationEvent` (`event_extractor.py:441-517`),
`src/observability/event_shapers.py::CombatShaper`, `GriefUrgencyTriggeredEvent`/
`NemesisRelationFormedEvent` (`src/observability/events.py`), `src/observability/live/*`
(`entity_inspector.py`, `event_publisher.py`, `snapshot_provider.py`, `anomaly_counter.py`),
`src/api/presenters/*`, and the `REFINED_UPDATE` `TraceEvent` replay stream. None of these are read
by any entity's cognition/decision path; per Q3's stated default, a trace that exists only in one
of these is not counted as encounterable by any in-world observer.

**Hidden-truth leak check (AC4).** `cognition.motivation.named_intention` -- checked; no reader
projects it outward, no leak found (same "private-hook state, not yet exposed" finding roadmap
§7.2 already recorded for the aging-death case, reconfirmed here since the writer is shared code).
`strategic.blockers` -- not implicated by this event's own trace set; named in roadmap §7.2 as a
standing leak-risk for future projection work, not a live leak today. The grief trigger's
location-independence is named as a real situatedness gap relative to the epistemic principle
(roadmap §2/§3.4), not a hidden-field leak -- routed to roadmap §11 item 3 per AC7/AC9, not fixed
here (Out of Scope).

**AC5 evidence (no production behaviour altered).** The Q1 proof was a throwaway scratch script
run against a pre-existing test fixture; `git status`/`git diff` for this ticket touch only new
test files, ticket-body prose, and append-only roadmap additions -- no `src/` file was modified.

**AC6 — `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` cited, not re-derived.** That
ticket's three-things finding (dead `PerceptionModel` abstraction / live
`SpatialQueryService.nearby_entities()` bypass / live narrow `PerceptionGate`) is reused verbatim.
No contradiction found between that ticket's findings and this ticket's own runtime observation --
this investigation's empirical check exercised the combat-resolution/lifecycle path, not the
perception pipeline itself, and everywhere this investigation touched perception it found the same
"zero production call sites for `PerceptionUpdatePhase`" state that ticket already established.

**AC8 — registry correction, confirmed no-op (Step 5, direct read).** `registries/mechanisms.yaml`
lines 1158-1215, the `perception` mechanism entry: `state: orphan`, `verified.instrument: scenario`,
`verified.verdict: contradicted`, `verified.date: "2026-09-20"`. The entry's own note already
documents `PerceptionUpdatePhase` has zero constructors anywhere in `src/` and that
`PerceptionFilterService.filter()`'s only real caller (`phase.py:43`) is itself never invoked in
production -- exactly the "zero production call sites" state this investigation's Answer 3 relies
on. This entry was already corrected by `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`
before this ticket started; no other registry entry touched by this investigation's trace set
(`tactical_decision`, `succession`/`aging_death`, `combat_resolution`) contradicts its recorded
state. No registry file was edited.

**AC7/AC9 — findings routed to the roadmap, never to `PERC-01`/`KNOW-01`.**
`docs/plans/systemic_world/roadmap.md` gained a new `### 7.2.1 Combat-death trace findings` section
(appended immediately before the existing `### 7.3`, no existing §7.2 text touched) and a new
bullet under §11 item 3's existing "Owner: first-wave Epic B0" paragraph (appended before item 4,
no existing item 3/4 text touched). Verified by diff: zero occurrences of `PERC-01`, `KNOW-01`, or
`PLAYER-EXPERIENCED` anywhere in the roadmap diff.

## Test Summary

**New regression-pinning tests added (4), all passing:**
- `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py`
  (new file) --
  `test_forced_combat_kill_produces_combat_death_reason_in_one_tick` (AC2),
  `test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death`
  (AC1, AC3) -- 2 passed.
- `tests/unit/progression/test_lifecycle.py` (extended) --
  `test_inheritance_transfer_carries_no_provenance_marker` (AC4) -- included in the 39 passed
  below.
- `tests/unit/domains/perception/test_phase12_perception_filter_service.py` (extended) --
  `test_perceived_entity_has_no_item_or_event_fields` (AC4) -- included in the 118 passed below.

**Full scoped regression surface (Step 7 / test_plan.md's "Scoped Pytest Commands"), all green:**
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
# 118 passed

pytest tests/mechanic_scenarios/test_combat_death_trace_encounterability.py -q
# 2 passed

pytest tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py \
       tests/mechanic_scenarios/test_combat_judgement_withdrawal.py -q
# 4 passed

pytest tests/simulation_quality/test_social_scorer.py -k Grief -q
# 2 passed, 17 deselected

pytest tests/simulation_quality/test_heir_inventory_transfer_corpus.py -q
# 1 passed
```
Total: 127 passed, 0 failed, across all scoped commands. `pytest tests/` was never run, per
test_plan.md's explicit instruction.

## Files Changed
- `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py` (new) -- Q1 regression
  pin and the grief-trigger bonded-vs-co-located regression pin.
- `tests/unit/progression/test_lifecycle.py` (extended) --
  `test_inheritance_transfer_carries_no_provenance_marker`.
- `tests/unit/domains/perception/test_phase12_perception_filter_service.py` (extended) --
  `test_perceived_entity_has_no_item_or_event_fields`.
- `docs/plans/systemic_world/roadmap.md` (append-only) -- new `### 7.2.1` subsection and a new
  bullet under `## 11` item 3's existing "Owner: first-wave Epic B0" paragraph.
- `tickets/inprogress/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY.md` (this file) --
  Status, Implementation Notes, Test Summary, Files Changed, Completion Summary filled in.
- `staging_artifacts/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY/plan.md` --
  Deviations section appended (see that file).
- `staging_artifacts/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY/investigation.md`,
  `staging_artifacts/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY/test_plan.md` --
  written during this ticket's own prior Investigate/Plan phases (untracked, not yet committed);
  not modified by this Implement pass, listed here because they are part of this run's own
  uncommitted changeset.
- No `registries/mechanisms.yaml` edit (Step 5 confirmed no-op, evidenced above -- not a change).
- No `src/` file changed.

## Completion Summary
Assessment ticket, closed by observation rather than by a code fix. Confirmed empirically (Q1,
via a real forced `Kernel.tick_once()` combat kill) that combat deaths occur and are classified
`death_reason == "COMBAT"` through the real lifecycle path. Enumerated, separately, which
world-state traces a combat death leaves behind (Answer 2, 9 items) and which of those a situated
observer could legitimately receive (Answer 3): only the grief trigger, only for bonded allies,
with no proximity constraint -- every other trace (inheritance, faction, conquest, economy) exists
but is not encounterable by any observer today, because `PerceivedEntity`'s schema has no item/
event field and `PerceptionUpdatePhase` has zero production callers. No hidden-truth leak was
found. Four regression-pinning tests were added to lock these findings into the test suite; the
full scoped regression surface (127 tests across 5 pytest invocations) passes. Findings were
routed into `docs/plans/systemic_world/roadmap.md` §7.2.1 (new) and §11 item 3 (appended bullet),
never against `PERC-01`/`KNOW-01`. No production code was changed; `registries/mechanisms.yaml`'s
`perception` entry was confirmed already correct and left untouched.

**Two post-close near-misses, both caught and corrected before commit, not accommodated.** First,
Verify's own static `docs_to_update_coverage` check correctly BLOCKED once on a real formatting
defect: three "this doc does not need updating" explanations in `investigation.md` were written as
`- \`docs/...\`` bullets, the exact format the parser reads as "this doc DOES require updating" —
fixed by reformatting them as plain prose (no leading bullet), the substantive finding (none of the
3 docs need updating) unchanged. Second, an `agent_count`-correction `record_run.py` call reused a
stale literal `end_ts`, producing a second `runs.jsonl` row indistinguishable from the first
(same `final_status`, same `end_ts`) — the same class of accidental duplicate
`tools/gate_checks/duplicate_run_record_check.py`'s ratchet (ceiling 1, not raised) exists to
catch, resolved the same way as `TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS`'s own
documented incident this session: deleted the stale line from the still-uncommitted per-batch
shard (a data-entry error correcting one real event, not a rewrite of two distinct events), kept
the corrected row, re-verified the ratchet check and its companion pytest both pass at ceiling 1.
