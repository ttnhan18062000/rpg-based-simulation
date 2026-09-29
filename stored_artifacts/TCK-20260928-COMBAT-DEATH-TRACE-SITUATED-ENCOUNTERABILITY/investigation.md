---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY
artifact_type: investigation
tags: [cognition, simulation-quality, root-cause]
---

# Investigation — TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY

## Current Behavior

### Q1 — Do combat deaths occur in an ordinary corpus run? EMPIRICALLY CONFIRMED (not BLOCKED_WITH_REASON)

Ran a real, deterministic `Kernel.tick_once()` forced-attack scenario, matching this repo's own
established pattern for this exact question (`tests/mechanic_scenarios/
test_combat_attributes_real_fight_outcome_value_differential.py`'s goblin-vs-orc real dispatched
attack via `mechanic_scenario_combat_judgement_withdrawal`, and
`tests/simulation_quality/test_heir_inventory_transfer_corpus.py`'s identical scripted-but-real
`Kernel.tick_once()` proof style for a lethal death). Ran with the main checkout's `.venv`
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`, `PYTHONPATH=.` from this
worktree — this worktree itself has no `.venv`, matching the prior evidence file's own note).

Setup: compiled `mechanic_scenario_combat_judgement_withdrawal`, forced goblin (id 1) into
`TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 2})` adjacent to
orc (id 2) with `orc.combat.hp = orc.combat.max_hp = 1.0` (guarantees a lethal resolution), ran one
`kernel.tick_once()`.

Result (real, not asserted from code reading):
```
goblin atk=8 orc def_stat=8 orc max_hp=120 (pre-override)
orc.lifecycle.active=False
orc.lifecycle.death_reason=COMBAT
orc.combat.hp=0
orc.combat.alive=False
```

**Combat deaths do occur, structurally confirmed in one tick**, through the real
`CombatResolutionSystem.resolve_attack()` → `outcome_kind="KILL"` → `LifecycleSystem.
resolve_lifecycle()` path (`src/systems/lifecycle_systems/lifecycle.py:202-217`). This closes Q1 as
a normal finding, not `BLOCKED_WITH_REASON`.

**Important scope caveat, not a contradiction of the above**: this is a scripted-but-real forced
attack (the same methodology this repo's own prior mechanic-scenario investigations use to prove a
mechanism dispatches through the real pipeline), not proof that combat deaths arise *unprompted*
from AI decision-making at a high rate. `registries/mechanisms.yaml`'s own `tactical_decision`
entry (already `verified: corpus_run, verdict: contradicted`, dated 2026-09-19) independently
establishes that the real `ATTACK`-intent branch is rare in ordinary corpus play: 0–2 real
`CombatResolutionSystem.resolve_attack()` calls per 1000–2000 ticks across three real corpus
worlds, and `hostiles` was non-empty **0 of 1130** real tactical decision calls; on the 2 of 1130
calls that did fire, real `execute_attack()` calls followed (2 and 29 respectively). So combat
deaths are real, reachable, and structurally correct when they occur — but rare in ordinary,
unscripted corpus play. Both facts are recorded, not merged.

### Answer 2 — Trace existence (independent of whether anything can perceive them)

All of the following are produced in the same tick a combat death resolves
(`LifecycleSystem.resolve_lifecycle()`, `src/systems/lifecycle_systems/lifecycle.py:189-295`):

1. **Lifecycle deactivation + death classification** (`lifecycle.py:206-218`): `active=False`,
   `is_permadeath_set=True`, `death_tick_set=state.tick`, `death_reason_set="COMBAT"` (or
   `"PERMADEATH"` routing through the identical deactivation, per COMB-311). Durable, authoritative
   state.
2. **Heir/succession dispatch** (`lifecycle.py:220-239`): `_transfer_inherited_feud()` and
   `_seed_dying_wish()` write to the heir's `cognition.motivation`/`strategic` internal state — pure
   cognition/strategic private state, not player-observable by construction (see Hidden-Truth Leaks
   below).
3. **Heirloom/inventory transfer** (`lifecycle.py:241-263`): a plain
   `ResourceTransferIntent(source_kind="CHEST", transfer_kind="AUTO")` moves the deceased's
   inventory + heirlooms to the heir. **Carries no origin/provenance marker** — an observer seeing
   the heir's new item (if a carrier existed at all, see Answer 3) could not distinguish inheritance
   from any other acquisition.
4. **Faction influence shift** (`lifecycle.py:268-272`, `FactionInfluenceService.
   process_influence_shift()`): `world_updates` on regions/factions.
5. **Conquest/stronghold lifecycle** (`lifecycle.py:273-276`, `FactionInfluenceService.
   process_conquest_lifecycle()`): potential `entities_add`/`entities_remove`.
6. **Economic vacancy signal** (`lifecycle.py:277-278`, `EconomicVacancyService.check_and_emit()`):
   `world_events_add` — concerns the vacated role, not the death or the inheritance itself.
7. **Grief trigger for trusted allies** (`src/observability/event_extractor.py:1722-1762`,
   `EventExtractor.detect_grief_triggers()`, drained via `Kernel._drain_pending_grief_triggers()`,
   `src/engine/kernel.py:709-753`): for every currently-alive entity whose
   `social.trust_history[dead_id] >= ALLY_TRUST_THRESHOLD` (0.30), writes a real
   `ConcernState(kind=SOCIAL_THREAT, id="grief_ally_{dead_id}", urgency=min(1.0, trust*0.8))` into
   `entity.strategic.concerns` via `GriefUrgencyImporter.build_strategic_update()`
   (`src/domains/campaigns/grief_urgency.py`) — a real authoritative `StrategicUpdate`, not an
   observability-only artifact. **Location-independent**: no proximity or perception check anywhere
   in this path; it is keyed purely on `trust_history`.
8. **Developer-only observability surfaces** (see explicit enumeration below): `CombatDamageEvent`,
   `CombatKillEvent`, `hero_death_unrecorded` `SimulationEvent` (`event_extractor.py:461-517`), plus
   the live default-path equivalents in `src/observability/event_shapers.py::CombatShaper` (behind
   `ENABLE_PUSH_EVENT_SHAPERS`, default ON) and `GriefUrgencyTriggeredEvent`
   (`Kernel._phase_observability`, `src/observability/events.py`).
9. **§13.7's "witnessing combat" tier does not exist as a runtime mechanism.**
   `docs/mechanics/04_strategic_cognition.md` §13 is explicitly headed **"Status: declared, not yet
   implemented"** (line 1494), and §13.7 itself ("A third tier: witnessing combat") is a
   specification, not code — it names the shape a witness mechanism *would* take (any entity within
   perception radius of a combat participant's position at the event's tick) but cites no
   implementing function. The entire `src/domains/combat_engagement/` domain this section completes
   is gated behind `ENABLE_COMBAT_ENGAGEMENT` (default `OFF`) and has never run in a real corpus
   profile (§13, lines 1507–1508). Parity ledger `STRAT-273` (`status: missing`, P1) independently
   confirms this. **There is therefore no runtime path today by which any entity other than a
   trusted ally (item 7) receives anything about a combat death.**

### Answer 3 — Situated encounterability (kept strictly separate from Answer 2)

Checked each real runtime data path named in the ticket's Related Code Areas against each trace in
Answer 2:

- **`PerceptionGate` (`src/world/perception/gate.py`)** — live, wired at `src/engine/tactical.py:
  181,196-199` inside `TacticalDecisionSystem`'s own targeting loop. It runs **pre-combat**, to gate
  which *live* neighbor becomes an eligible attack target — it is never invoked after a death, and
  has no call site anywhere in the death/lifecycle/grief path. It cannot carry any post-death trace.
- **`entity.cognition.subjective.perception` (`PerceivedEntity`, `src/core/cognition.py:28-33`)** —
  the perceived-entity record holds only `entity_id`, `kind`, `position`, `salience`, `confidence`.
  No item, inventory, or event field exists on it structurally, so even if it were populated at
  runtime it could not carry inheritance, faction-influence, or grief content. Moot in any case,
  because — citing `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` (adopted per Scope,
  not re-derived) — the salience/attention/budget layer that would write this field
  (`PerceptionUpdatePhase`) has **zero production call sites** and does not run in any production
  tick today (`docs/simulation/domains/perception_contract.md` line 15; independently reconfirmed by
  a real differential `Kernel`-run scenario in that ticket, not merely a grep). The only live
  perception-shaped thing is `PerceptionGate`'s binary sense-channel gate (used for combat targeting
  only, per above) — see that ticket's own three-things finding, cited verbatim below.
- **Grief trigger (`event_extractor.py:1722-1762` → `kernel.py`'s
  `_drain_pending_grief_triggers()`)** — this is the **one** real path by which a runtime consumer
  legitimately receives a trace of the combat death: a bonded observer (an entity with
  `trust_history[dead_id] >= 0.30`) gets a real `ConcernState` in its own `strategic.concerns`
  naming the dead ally's id and an urgency value. **This is a legitimate encounter for the bonded
  category specifically** — it goes through a real authoritative `StrategicUpdate`, not a
  developer-only surface. **It is not legitimate for the co-located category**: it carries no
  proximity/perception check at all, so a co-located-but-not-bonded observer receives nothing, and a
  bonded-but-distant observer receives the same concern as if standing next to the corpse. This
  location-independence is itself flagged (roadmap §7.2, §11 item 3, and the source evidence file)
  as worth review under the epistemic principle (roadmap §2/§3.4) — not remediated here, per this
  ticket's Out of Scope.
- **`lifecycle.py`'s inheritance transfer (`:252-257`)** — no origin marker exists on the
  `ResourceTransferIntent`, and (citing the M2 evidence file directly, not re-derived) **no in-world
  carrier exists** that would let a co-located or bonded observer notice the heir's new item at all:
  `PerceivedEntity` has no item fields, `WorldSignal` has no item fields,
  `KnowledgeModelService` assimilates only paid information facts (`resource_source`,
  `recipe_definition`, `danger_rating`, `lead`), and inventory reads in `src/ai/goals/scorers.py` /
  `src/domains/information/resolver.py` are all self-inventory reads. **Trace exists (Answer 2 item
  3); it is not encounterable by any observer today (Answer 3).**
- **Faction influence shift / conquest lifecycle / economic vacancy signal (Answer 2 items 4–6)** —
  these write world state (`RegionState`/`FactionState`/`world_events_add`) but none of them route
  through `PerceptionGate` or any perception/knowledge consumer; they are read only by the
  observability/scoring layer and by later systems reading raw authoritative state directly (e.g.
  `ResourceOpportunityProvider`, itself already flagged CONFLICTING against PERC-01 for reading raw
  `state.resource_nodes` with no perception gate at all —
  `docs/world_rules/knowledge-agency/perception.md` lines 164–184). **Exist; not legitimately
  encountered by any situated observer under any existing mechanism.**

### Developer-only surfaces (explicitly excluded from any encounterability claim, per AC3 and Q3's own default)

- `CombatDamageEvent`, `CombatKillEvent`, `hero_death_unrecorded` `SimulationEvent`
  (`src/observability/event_extractor.py:441-517`) and their live-default equivalents in
  `src/observability/event_shapers.py::CombatShaper`.
- `GriefUrgencyTriggeredEvent` / `NemesisRelationFormedEvent`
  (`src/observability/events.py`, emitted from `Kernel._phase_observability` and
  `CampaignOrchestrator`) — these are the **SimQ-scoring record** of the grief event (parity
  `SOC-246`), a separate artifact from the real `ConcernState` write itself (parity `SOC-231`,
  Answer 2 item 7 above, Answer 3's one legitimate path). The event log is developer-only; the
  `ConcernState` write is the real in-world trace.
- `src/observability/live/entity_inspector.py`, `event_publisher.py`, `snapshot_provider.py`,
  `anomaly_counter.py` — live observability/telemetry surfaces.
- `src/api/presenters/*` (`state_presenter.py`, `manifest_presenter.py`, `metadata_presenter.py`) —
  API-facing read models.
- The Replay/`REFINED_UPDATE` `TraceEvent` stream (`src/engine/kernel.py`'s
  `_replay.emit(TraceEvent(...))`).

Per Q3's default (stated, not assumed): a trace that exists only in one of these developer-only
logs/inspectors/presenters is **not** counted as encounterable by any in-world observer — none of
them are read by any entity's cognition/decision path; they exist purely for tooling, scoring, and
replay.

### Hidden-truth leak check (AC4)

- **`cognition.motivation.named_intention`** — checked. `LifecycleSystem._seed_dying_wish()`
  (`lifecycle.py`) writes a `NamedIntentionBundle` onto the heir. No system reads
  `NamedIntentionBundle.status` to expose or act on it as a player-observable signal — confirmed by
  that method's own docstring and by the roadmap's own Negative check 1 (§7.2). **No leak found
  today**, because nothing projects this field anywhere outward. This is the same "private-hook
  state, not yet exposed" finding roadmap §7.2 already recorded for the inheritance/lineage case;
  this ticket reconfirms it for the combat-death path specifically (the dying-wish/inherited-feud
  writers are shared code, triggered by the same `resolve_lifecycle()` death branch regardless of
  `death_reason`).
- **`strategic.blockers`** — no combat-death-specific writer found in this path; not implicated by
  this event. Named in Scope as a standing leak-risk for any *future* biography/HUD projection that
  might render it verbatim (roadmap §7.2's own Negative check 2), not a live leak today.
- **Location-independent reads** — the grief trigger (Answer 2 item 7 / Answer 3) is the one
  confirmed location-independent read in this event's own trace set: a bonded entity anywhere in the
  world receives the same grief concern a co-located bonded entity would. This is not a "hidden
  truth" leak in the sense of exposing private cognition fields, but it is a real situatedness gap
  relative to the epistemic principle — named precisely, not fixed (Out of Scope), and routed to
  roadmap §11 item 3 per AC7/AC9.
- No other location-independent or hidden-field read was found in this event's own trace set beyond
  the above.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §13 ("Perceived Power Assessment") governs the entire
  perception→estimate→consideration pipeline this ticket touches. §13.1 states passive observation
  (seeing an entity within perception radius) is the always-on default tier; §13.7 specifically
  names "witnessing combat" as a real, buildable, **not yet built** third tier. The whole section is
  headed "Status: declared, not yet implemented" — the Mechanics Bible itself already documents that
  this capability does not exist at runtime, which this investigation's empirical/code-path check
  confirms rather than contradicts.
- `docs/world_rules/knowledge-agency/perception.md` PERC-01: "Perception is bounded by declared
  constraints; it does not imply complete or perfect knowledge by default." The grief trigger's
  location-independence (Answer 3) is in tension with this Rule's spirit (a legitimate trace
  reaching a bonded observer with zero distance/channel constraint at all), though PERC-01's own
  2026-09-22 revision states declared constraints are *possible*, not a mandatory joint requirement
  — so this is a named tension, not a confirmed Rule violation, consistent with how the same document
  already classifies the *existing* `ResourceOpportunityProvider`/`HarvestScorer` case as
  `CONFLICTING` (an active, unconstrained read) versus the grief trigger, which this investigation
  newly surfaces for the same document's own future consideration.
- `docs/engine/authoritative_apply_contract.md` §5 (Traceability): every applied update is emitted
  as a `REFINED_UPDATE` trace event — this is the replay/observability trace layer, itself a
  developer-only surface (see above), not evidence of in-world encounterability.

## Docs Requiring Update

None.

All of this ticket's findings are routed, per AC7/AC9, into the roadmap tracking documents
(`docs/plans/systemic_world/roadmap.md` §7.2/§11 item 3) rather than into the Mechanics Bible, the
perception contract, or the parity ledger, because none of this investigation's findings change any
of those documents' own current, already-accurate claims:

Mechanics Bible chapter 04 (strategic cognition) is not required to change: its §13 already
states "declared, not yet implemented" for the witnessed-combat tier this ticket investigated, and
this investigation's finding (no runtime witnessing mechanism exists) is consistent with, not
contradictory to, that existing text.

The perception domain contract doc is not required to change: it already states (line 15) that
`PerceptionUpdatePhase` has zero call sites in production, which this investigation's findings
confirm rather than correct.

The knowledge-agency perception world-rules doc is not required to change for this ticket: the
grief-trigger location-independence finding is new detail worth a future look (already flagged so
in the roadmap), but it is a candidate for a *future* revision to that document's own Repository
Findings section, not a correction of anything it currently asserts incorrectly — recording it in
roadmap §11 item 3 (below) satisfies AC9's routing requirement without prematurely editing an
authoritative Rule Catalog document outside this ticket's own scope.

The mechanism/rule registries (mechanisms, rule-mechanism edges, rule classifications) are not
required to change: AC7 explicitly forbids recording this ticket's findings against the `PERC-01`/
`KNOW-01` SCP rows (mapped only to Combat's `tactical_decision`), and this investigation found no
other registry entry whose real state now differs from its recorded state (AC8's correction trigger
is not met — the `perception` mechanism entry was already corrected by `TCK-20260920-...` before
this ticket ran).

Per AC9, this ticket's findings ARE recorded in the following non-Format-1 destinations (prose, not
a doc-coverage bullet, since these are roadmap tracking documents rather than Mechanics
Bible/contract/parity-ledger documents in the sense `check_docs_to_update_coverage` polices, and per
AC7 they must land here, not in the SCP rows):
- `docs/plans/systemic_world/roadmap.md` §7.2 and §11 item 3 — this investigation's Answer 2/Answer 3
  split, the empirical Q1 confirmation, and the grief-trigger location-independence note should be
  appended by whoever closes this ticket (implementer/doc-updater), completing §11 item 3's own
  "Owner: first-wave Epic B0" line, which is exactly this ticket.

## Parity Ledger Overlap

- **`STRAT-273`** (`docs/parity_ledger/strategic_cognition.yaml`) — `status: missing`, P1. Covers
  §13 in full, including the witnessed-combat tier (§13.7). This investigation's finding (no
  witnessing-combat runtime mechanism exists) **confirms** this entry's existing `missing` status;
  no change needed.
- **`COMB-309`** (`docs/parity_ledger/combat_movement.yaml`) — `status: verified`, **P0**. Gates
  `CombatKillEvent` on `entity.lifecycle.death_reason == "COMBAT"`. `test_path`:
  `tests/unit/observability/test_event_extractor_world.py::test_combat_kill_not_emitted_for_hazard_caused_death`,
  `::test_combat_kill_emitted_for_genuine_combat_death` — both exist and are the authoritative-death
  branch this investigation exercised. P0 entry; both test paths confirmed to exist by direct
  inspection.
- **`COMB-311`** (`docs/parity_ledger/combat_movement.yaml`) — `status: verified`, P1. Extends
  `death_reason=="COMBAT"` classification to `PERMADEATH` outcomes. `test_path`:
  `tests/unit/progression/test_lifecycle.py::test_permadeath_death_classification` — exists.
- **`SOC-231`** (`docs/parity_ledger/social_narrative.yaml`) — `status: verified`, P1. The
  episode-boundary grief-urgency mechanism (`GriefUrgencyModifier`/`GriefUrgencyImporter.apply()`).
- **`SOC-246`** (`docs/parity_ledger/social_narrative.yaml`) — `status: verified`, P1. The SimQ/
  observability scoring wiring for both the episode-boundary and mid-episode
  `GriefUrgencyTriggeredEvent` paths — this is the developer-only scoring artifact, distinct from
  the real `ConcernState` write (`SOC-231`'s own mechanism, reused mid-tick per
  `event_extractor.py:1722-1762`).
- No P0 entry among these requires a new/changed test — `COMB-309`'s existing test paths already
  cover the exact `death_reason=="COMBAT"` gate this investigation exercised, and remain passing
  (not re-run destructively here; see Test Plan for the scoped regression command).

## Prior Work

- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` (`tickets/todos/`, open, P1) — **cited,
  not re-derived**, for the perception-liveness question per Scope/AC6. Its three-things finding
  (dead `PerceptionModel` abstraction / live `SpatialQueryService.nearby_entities()` bypass / live
  narrow `PerceptionGate`) is reused verbatim above. **No contradiction found** between that
  ticket's findings and this ticket's own runtime observation — this investigation's empirical check
  exercised the combat-resolution/lifecycle path, not the perception pipeline itself, and everywhere
  this investigation touched perception it found the same "zero production call sites for
  `PerceptionUpdatePhase`" state that ticket already established.
- `docs/plans/systemic_world/evidence/2026-09-27-inheritance-observer-encounter-findings.md` — the
  M2 inheritance-observer check (aging/`OLD_AGE` death, not combat). Its "no in-world carrier"
  conclusion for inheritance is directly reused here (Answer 3, inheritance-transfer bullet) since
  the transfer mechanism and its absence of carriers is identical regardless of `death_reason`.
- `docs/plans/systemic_world/roadmap.md` §7.2, §11 item 3 — the design-check and open-question
  entries this ticket's findings must be routed into (AC7/AC9).
- `docs/plans/systemic_world/first_wave_plan.md` §2 Epic B0 and `docs/plans/systemic_world/
  ticket_planner_handoff.md` Card B0 — this ticket is the "minus Q1" continuation of that card;
  both exist in this worktree (not only on the unmerged `systemic-world-roadmap-proposal` branch),
  confirmed by direct read.
- `registries/mechanisms.yaml`'s `tactical_decision` entry (`verified: corpus_run, verdict:
  contradicted`, 2026-09-19) — the existing corpus-run evidence for real ATTACK-branch rarity, reused
  above to caveat the Q1 empirical proof's own scripted nature.

## Risks and Open Questions

- **§11 item 3 (perception liveness) is explicitly this ticket's own OUT-OF-SCOPE strand, adopted
  from `TCK-20260920-...` per the ticket's own Scope.** No new runtime check was performed for
  general perception liveness here; only the combat-death-specific paths above were traced. If a
  future run finds perception live through some other path not covered by either investigation,
  that would need to be reconciled against both tickets' findings, not silently override either.
- **The grief trigger's location-independence is a named tension with the epistemic principle
  (roadmap §2/§3.4), not resolved here.** Whether to scope it (proximity-gate the concern, or accept
  it as an intentional "bond transcends distance" design) is a design decision for the roadmap
  session, not this ticket.
- **The empirical Q1 proof used a scripted forced attack**, matching this repo's own established
  precedent for proving a mechanism dispatches through the real pipeline (same style as the heir
  inheritance corpus test and the combat-attributes differential test). It is real code executing
  through the real `Kernel`/`AuthoritativeApplyPipeline`, not a mock — but it is not a claim that
  combat deaths are common in unscripted corpus play; `registries/mechanisms.yaml`'s own corpus-run
  evidence (0–2 real attacks per 1000–2000 ticks) already answers that question honestly, and is
  cited rather than re-measured here.
- **No new mechanism/registry entry needs correcting (AC8).** This investigation found no perception
  mechanism whose registry entry now contradicts its real state; the one entry that matters
  (`perception`) was already corrected by `TCK-20260920-...` before this ticket started.

## Anti-Drift Hazards

- **Do not fold this ticket's findings into `PERC-01`/`KNOW-01`'s registry rows.** AC7 is explicit
  and load-bearing: those rows are mapped only to Combat's `tactical_decision` mechanism
  (`registries/rule_mechanism_edges.yaml`); attaching observer-evidence findings there would corrupt
  that mapping's own meaning.
- **Do not treat the grief trigger as "perception."** It is a real, legitimate trace for the bonded
  category, but it does not go through `PerceptionGate`, `PerceptionFilterService`, or any
  perception-domain code at all — conflating it with perception liveness would misattribute which
  mechanism is actually doing the work.
- **Do not expand this ticket into wiring `PerceptionUpdatePhase` or building §13.7's
  witnessing-combat tier.** Both are explicitly Out of Scope; this ticket's job is to report the
  current trace/encounterability state, not to close the gap it found.
- **Do not claim `PLAYER-EXPERIENCED` for anything found here.** This is a feasibility/observation
  finding (roadmap §7.2's own framing), not a player-observation exercise.
- **Do not substitute a different event if a future re-check of Q1 finds combat deaths rarer than
  this investigation's forced-scenario proof suggests.** The ticket's own Scope forbids event
  substitution; any future finding that ordinary (unscripted) runs essentially never reach a combat
  death within a feasible tick budget is itself a reportable finding, not grounds to swap events.
