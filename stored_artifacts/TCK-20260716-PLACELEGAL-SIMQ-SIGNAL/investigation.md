---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-SIMQ-SIGNAL
artifact_type: investigation
tags: [simulation-quality, observability, world]
---

# Investigation — TCK-20260716-PLACELEGAL-SIMQ-SIGNAL

## Current Behavior

**Parent ticket confirmation (`TCK-20260716-PLACELEGAL-HARDLAW`, DONE).** Direct grep of
`src/observability/hard_law_monitor.py` confirms the final `law_id` string is exactly
`"LAW-SPAWN-OCCUPANCY"` (lines 177 and 204 — two emission sites inside
`HardLawMonitor.check_initial_placement()`, one for the multi-occupant tile scan, one for the
reused `LegalityServiceV2.verify_occupancy()` branch). **Not renamed** — the ticket's working
name is the final name, confirmed against real code, not just the parent ticket's prose.
`severity="ERROR"` in both call sites, matching the ticket's claim. `details` always contains
`"object_kind"` (`"entity"`/`"building"`/`"resource_node"`), and either
`{"tile", "colliding_object_kind", "colliding_object_id"}` (multi-occupant branch) or
`{"tile", "reason"}` (terrain/occupancy branch) — **`details` never contains a `"law_id"` key**,
which matters (see Risks below).

**`src/simulation_quality/quality_hub.py::_translate_invariant()`** (lines 59-65): a 2-branch
`str.startswith()` dispatcher on `env.payload.get("law_id", "")`. Branch 1: `COMBAT` prefix →
`"combat_hard_law_violation"`. Branch 2: `CONSERVATION` prefix → `"conservation_law_violated"`.
No branch for `LAW-SPAWN-OCCUPANCY` today — falls through to `return env.event_type`
(pass-through, unscored). This is registered in `_TRANSLATE_CONDITIONAL["InvariantViolation"]`
(line 80), so it only ever runs on envelopes whose engine `event_type == "InvariantViolation"`.

**`src/simulation_quality/scorers/world_dynamics.py::WorldDynamicsScorer`**: `EVENT_TYPES`
(lines 19-35) is a 15-tuple ending in `"building_sabotaged"`. `score()`'s `building_sabotaged`
branch (lines 175-176): `return _rec(self.weights["infrastructure_damaged"], "building took
sabotage damage — real infrastructure consequence", ("infrastructure_damaged",))` — a single
unconditional positive-weight signal, no branching logic inside it (unlike e.g. `calamity_spawned`,
which branches on a "gone dormant" condition). This is the correct shape template for the new
signal's *scorer* code, but **not** for its *weight sign* — see Risks.

**`docs/simulation_quality/quality_scoring_contract.md`**: `building_sabotaged` actually touches
**three** locations in this one file, not one:
1. §5 WORLD DYNAMICS "Event types scored" list, line 908 (comma-separated list, ends
   `..., building_sabotaged`).
2. §5 WORLD DYNAMICS Signal/Delta/Tag table, line 927: `| Building takes sabotage damage
   (hp_delta < 0 on building_updates) | +1 | infrastructure_damaged |`.
3. §6 Scenario Registry, line 1031: `| SQ-23 | Does infrastructure sabotage register as a
   real-world consequence? | WORLD | — | building_sabotaged | Building damage is WORLD-owned
   per building-events-have-no-existing-pillar-owner (§7.3); do not duplicate in FACTION... |`.

The ticket's Scope bullet only names "add one new signal row to the WORLD DYNAMICS pillar table" —
singular. The project's own documented procedure for this exact situation
(§7.2 "Adding a Scoring Rule to an Existing Pillar", lines 1055-1069) is an explicit 6-step
checklist: (1) check §6 for scenario/rule conflicts, (2a) add the weight key to
`config/simulation_quality/scoring_weights.yaml`, (2b) add scorer conditional logic using
`self.weights["key"]` — no numeric literals, (3) add the tag to §5 tag documentation, (4) if the
scenario is new, add a §6 row, (5) add a unit test, (6) if a new event_type, add it to §5's
"Event types scored" list. **`config/simulation_quality/scoring_weights.yaml` is a hard runtime
dependency the ticket's own Related Code Areas list omits** — `PillarWeightsView.__getitem__`
(`src/simulation_quality/weights.py:157-164`) raises `KeyError` for any weight key not present in
that pillar's YAML section, so `self.weights["spawn_occupancy_violation"]` (or whatever key is
chosen) will hard-crash at first score unless this file is also edited. Confirmed the existing
`infrastructure_damaged: 2.0` entry lives at `config/simulation_quality/scoring_weights.yaml:163`,
inside the `WORLD:` block.

**Weight-sign nuance, already correctly anticipated by the ticket's own Scope text but easy to
get wrong by literal copy-paste**: `building_sabotaged` uses a **positive** weight (`+2.0`,
"infrastructure_damaged") even though the underlying event is bad for the building — because for
WORLD DYNAMICS, sabotage happening at all is scored as evidence the world has *real consequences*
(the pillar's core question is "is the world alive or a static backdrop"). The ticket's own Scope
text explicitly overrides this for the new signal: "a negative/penalized signal... unlike some
WORLD signals that have a healthy range, this one is unconditionally bad — zero occurrences is the
correct target." Confirmed via `src/simulation_quality/pillar_accumulator.py::add()` (line 51):
`raw_score += record.delta`, and negative deltas are what populate `worst_events`/`negative_count`
— so a negative weight (mirroring e.g. `ecology_broken: -20.0`, `trauma_hazard_broken: -5.0`, NOT
`infrastructure_damaged: +2.0`) is the mechanically correct choice for "this should never happen."
This is not a contradiction of the ticket, just a precise confirmation worth stating explicitly so
an implementer does not literally mirror `building_sabotaged`'s sign.

## Mechanics / Engine Constraints

- No `docs/mechanics/` chapter governs SimQ scoring directly — SimQ is explicitly a health/gradient
  system, not a mechanics-law system (see Parity Ledger Overlap below for the exact scope-boundary
  quote). The relevant authority here is `docs/simulation_quality/quality_scoring_contract.md`
  itself (§1 scope, §7 extensibility protocol) plus `docs/observability/hard_law_monitor.md` (P1,
  updated by the parent ticket with the `LAW-SPAWN-OCCUPANCY` row — confirmed present).
- `docs/parity_ledger/world_dynamics.yaml` `WORLD-112` (added by the parent ticket, lines
  1421-1430): "Initial spawn placement... is checked for occupancy/terrain legality once at Kernel
  construction..." — `status: verified`, `test_path` points at the parent ticket's regression test
  in `tests/engine/test_hard_law_monitor.py`. This entry is about the *detection* law, not the SimQ
  signal; it does not need to change for this ticket (this ticket doesn't touch
  `check_initial_placement()`), but a **new** parity ledger entry is warranted for the SimQ routing
  behavior itself (see below).

## Parity Ledger Overlap

- **`docs/parity_ledger/world_dynamics.yaml` `WORLD-112`**: read directly, unaffected by this
  ticket's scope (detection-side only); no change needed.
- **No existing parity ledger entry currently documents `_translate_invariant()`'s `law_id`
  dispatch table itself** as a general mechanism (checked `infrastructure.yaml` for `hard_law`
  hits — only `INFRA-238` (`CombatScorer` covers `combat_hard_law` — confirms the `COMBAT*` branch
  *is* live and scored, at least on the scorer side) and `INFRA-270`/nearby entries about
  `combat_hard_law_violation` traceability, both about the COMBAT branch specifically, none about
  `LAW-SPAWN-OCCUPANCY` or WORLD). **A new entry is needed** in `world_dynamics.yaml` (or
  `infrastructure.yaml`, following the `INFRA-238`/`INFRA-270` precedent location for
  scorer-routing behavior) once this ticket's dispatcher branch + scorer logic land — no existing
  entry to "update," this is new behavior.
- **SimQ scope boundary directly cited by the ticket, verified accurate**:
  `stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.2 (read in full,
  lines 140-152): "does not score correctness — that is `hard_law_monitor`; determinism/replay is
  a correctness property, not a health gradient." This is the real quote and the real section; the
  ticket's citation is accurate, not paraphrased incorrectly.
- **§2.6 of the same doc (lines 178-215) is the direct precedent for *this* ticket's shape**,
  more precisely than the ticket's own text states: it establishes that `building_sabotaged`
  required **two separate pieces of work**: "(a) emit a new event type... and (b) add a scoring
  rule consuming it" — because `BuildingSabotageSystem.resolve()` "does not emit any
  `ObservabilityEventEnvelope`/`SimulationEvent` today — it only writes... records directly to
  durable state." **This two-piece pattern is exactly the situation this ticket is in, and it is
  not resolved by this ticket's stated scope** — see the blocking finding below.
- No `P0` parity entries are touched by this ticket's actual scope (quality_hub/world_dynamics
  scorer changes only) — `WORLD-112`/`WORLD-075`/`WORLD-076` (the P0/P1 entries touched by the
  parent ticket) are all in the parent ticket's territory, already closed.

## Prior Work

- **`tickets/done/TCK-20260716-PLACELEGAL-HARDLAW.md`** + its `stored_artifacts/` — parent ticket,
  DONE. Confirmed `law_id="LAW-SPAWN-OCCUPANCY"` final naming (see Current Behavior). Confirmed the
  call site is `Kernel._run_initial_placement_check()`, called once at the end of `Kernel.__init__`
  (`src/engine/kernel.py:321`, inside `__init__` which spans lines 53-3xx — confirmed by direct
  read, `tick_once()` starts at line 334, well after).
- **`tickets/done/TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL.md`** — the literal precedent this
  ticket cites throughout. Confirmed its actual emission mechanism is **not** `_translate_invariant`
  at all: `src/observability/event_extractor.py` lines 909-922 diff `update.building_updates` for
  `hp_delta < 0` and directly construct a `SimulationEvent(event_type="building_sabotaged", ...)` —
  the event_type already matches contract vocabulary, no translation layer involved. This is a
  structurally different route than the `COMBAT*`/`CONSERVATION*` branches this ticket is asked to
  mirror (which go through an intermediate generic `"InvariantViolation"` event_type +
  `_translate_invariant()`'s `law_id`-payload dispatch). The ticket's citation of `building_sabotaged`
  is accurate for the **scorer/contract-table shape**, but the **dispatch mechanism** genuinely
  follows the `COMBAT*`/`CONSERVATION*` precedent instead — worth stating explicitly since the
  ticket blends the two without flagging that they are different code paths.
- **`tests/simulation_quality/test_quality_hub_event_translation.py`** (lines 101-113): exact
  existing unit-test precedent for the `COMBAT*`/`CONSERVATION*` branches — `test_invariant_combat_law`,
  `test_invariant_conservation_law`, `test_invariant_unknown_no_translation`. All three construct an
  envelope directly via a local `_env(event_type, payload)` helper with `law_id` placed straight into
  `payload` — they do **not** go through a real `Kernel`/`HardLawMonitor` call. This is the exact,
  directly reusable template for this ticket's AC #1 ("unit test covers both branches... mirroring
  existing COMBAT* branch test coverage").
- **`tests/simulation_quality/test_world_dynamics_scorer.py`** (lines 148-155): existing
  `building_sabotaged` scorer test block (`assert "building_sabotaged" in
  WorldDynamicsScorer.EVENT_TYPES`; `rec = scorer.score(_env("building_sabotaged", payload={"region_id":
  "r1"}), _ctx())`) — direct template for the new event type's scorer test.
- **`tests/simulation_quality/test_traceability_path.py`** (lines 39-66): `minimal_kernel` fixture
  + `_inject_combat_hard_law_violation()` helper — constructs a real (minimal) `Kernel`, then calls
  `kernel._event_recorder.record(SimulationEvent(event_type="combat_hard_law_violation", ...))`
  directly, bypassing `_translate_invariant()`'s `InvariantViolation`/`law_id` path entirely, to
  prove end-to-end propagation from `EventRecorder` through `QualityHub` to `QualityReport.worst_events`
  and back out to `simulation_events.jsonl`. **This is the established, reusable pattern in this repo
  for testing SimQ scoring without needing the full producing-side pipeline to exist** — directly
  relevant to this ticket's Test Plan given the blocking finding below.
- **`config/simulation_quality/scoring_weights.yaml`** (`WORLD:` section, lines ~145-166) — confirmed
  location for the new weight key; `infrastructure_damaged: 2.0` sits here as the direct sibling entry.
- **`docs/simulation_quality/quality_scoring_contract.md` §7.2** — the project's own documented,
  numbered procedure for exactly this kind of change; used above to cross-check the ticket's Scope
  section for completeness.

## Risks and Open Questions

- **BLOCKING, not resolved by re-reading the ticket — a genuine architecture gap found by direct
  source read, not previously documented anywhere in the ticket, the parent ticket, or the idea
  doc.** `Kernel._run_initial_placement_check()` (`src/engine/kernel.py:740-806`) — the sole producer
  of `LAW-SPAWN-OCCUPANCY` violations — persists violations to `hard_law_violations.jsonl`
  (lines 772-790) and routes them through `AlertsManager` (lines 792-800), but **it never sets
  `self._status.current_tick_violations` and never constructs a `SimulationEvent`**. Compare
  `_run_hard_law_checks()` (the per-tick sibling, lines 808-874): it explicitly sets
  `self._status.current_tick_violations = violations` (line 824). That field is the *only* thing
  `_phase_observability()` reads (line 891: `current_violations = getattr(self._status,
  "current_tick_violations", [])`) to convert violations into `InvariantViolation` `SimulationEvent`s
  (lines 890-903) which then flow to `EventRecorder`/the observability event bus/`QualityHub`.
  `_phase_observability()` is itself only ever called from inside `tick_once()` (line 727) — never
  from `__init__` — so it cannot pick up `_run_initial_placement_check()`'s violations even
  indirectly. **Net effect: `LAW-SPAWN-OCCUPANCY` violations, as currently wired, can never become an
  `InvariantViolation` event, so they can never reach `_translate_invariant()`, `QualityHub`, or any
  SimQ scorer, no matter what dispatcher branch this ticket adds.** Independently confirmed via
  `tools/calibrate_simq.py::_replay_jsonl_through_hub()` (lines 267-291): it replays
  `simulation_events.jsonl` (the `SimulationEvent`/`EventRecorder` stream), **not**
  `hard_law_violations.jsonl` — so the calibration/anchor tooling this ticket's own AC #4 depends on
  (`make evaluate --dry-run` / the anchor-grade-stability check) also cannot see this signal from a
  real `Kernel` run today.
  - This directly conflicts with AC #4 as written ("affected runs show a real, expected grade
    delta") — under current wiring, **no run, however affected by the seed-42 collision, can ever
    produce a grade delta from this signal**, because the producing event is never emitted.
  - This does **not** block AC #1 (unit test on `_translate_invariant()` directly, envelope
    hand-built, per the `test_quality_hub_event_translation.py` precedent) or the `EVENT_TYPES`/scorer
    unit-test AC (`test_world_dynamics_scorer.py` precedent) — those test the dispatcher/scorer in
    isolation and will pass regardless of whether the producing side ever calls them for real.
  - This is squarely the same "two pieces of work" pattern `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`
    §2.6 already identified for `building_sabotaged` ("(a) emit a new event type... (b) add a scoring
    rule consuming it") — but this ticket's own Out of Scope section explicitly forbids piece (a):
    *"Anything in `HardLawMonitor` itself, or the call-site wiring in `Kernel.__init__` — entirely
    owned by `TCK-20260716-PLACELEGAL-HARDLAW`."* `_run_initial_placement_check()` is exactly that
    call-site wiring. **This is a real scope conflict, not a nitpick**: as scoped, this ticket can
    ship a fully correct, fully tested dispatcher + scorer + contract-doc update that is
    unreachable by any real production code path. Flagging rather than assuming an answer, per this
    project's Uncertainty Rule — plausible resolutions (not decided here): (1) accept the gap as a
    documented, intentional two-ticket split and file a small follow-up ticket to add event emission
    to `_run_initial_placement_check()` (the parent ticket is DONE, so this would be new, separately
    scoped work, not a reopening); (2) treat "the call-site wiring in `Kernel.__init__`" narrowly
    enough that adding a `SimulationEvent` emission (not new persistence/mode-gating/alert logic) to
    the *existing* `_run_initial_placement_check()` method falls inside *this* ticket's scope instead,
    since it's needed to make this ticket's own deliverable real; (3) re-scope AC #4 to only cover
    the directly-testable dispatcher/scorer path (per the `test_traceability_path.py`-style injection
    pattern) and explicitly document the "detected but not yet live-scored" state as a known,
    accepted gap. This needs a human/Plan-phase decision — the ticket's own Scope and Out-of-Scope
    sections currently contradict each other once the code is read closely, and Investigate should
    not silently pick one.
- **Confirmed, not blocking**: `make evaluate --dry-run` resolves to `python3 tools/evaluate_simq.py
  --dry-run` (`Makefile:321-322`) — a real, existing target. It diffs `data/calibration/` reports
  against `tests/simulation_quality/fixtures/grade_anchors.json`, **it does not re-run the engine**
  (`evaluate-full`/no `--dry-run` does that). Given the blocking finding above, running
  `--dry-run` before/after this ticket's change will show **no diff at all** for any real anchor
  scenario, regardless of whether the change is correct — because no real run's
  `simulation_events.jsonl` will ever contain a `LAW-SPAWN-OCCUPANCY`-derived event under current
  wiring. This AC needs to be re-scoped alongside the blocking finding above, or the "before/after"
  check will trivially pass by producing zero evidence either way.
- **Confirmed, not blocking**: the `obs-isolation` folder (`tickets/todos/obs-isolation/`,
  `SEQUENCE.md`) is a real, existing precedent for exactly this "grade anchors must not shift"
  discipline — its own dependency notes literally say: *"Grade anchors: tickets 1–3 must not change
  in-process grades (`make evaluate --dry-run` clean). If any diff appears, stop and investigate
  before recalibrating."* Confirms the ticket's citation of this precedent's *intent* (verify no
  unintended grade shift) is accurate, even though the specific tool it names is the same
  `evaluate_simq.py --dry-run` already confirmed above, not a separate isolation-specific script.
- **Weight key naming**: not decided by the ticket ("e.g. `spawn_occupancy_violation`") — needs a
  Plan-phase decision. Whatever tag/key is chosen must be added to *both*
  `config/simulation_quality/scoring_weights.yaml`'s `WORLD:` section *and* used consistently as the
  `ScoreRecord.tags` value in the scorer and the §5 contract table row — the ticket's Related Code
  Areas list should be expanded to include `config/simulation_quality/scoring_weights.yaml`
  explicitly (currently omitted, but a hard `KeyError` dependency per §7.2 step 2a).
- **Scenario Registry (§6) row**: the ticket's Scope section only explicitly requires a "WORLD
  DYNAMICS pillar table" row: read literally, this could mean just the §5 Signal/Delta/Tag table
  (line ~913-935) and skip the §6 Scenario Registry SQ-24-style row (line ~1031 is `building_sabotaged`'s
  SQ-23 entry). Per §7.2 step 4 ("If the scenario is new: add a row to §6 Scenario Registry") and
  the direct `building_sabotaged` precedent (which has all three: Event-types-list + Signal table +
  SQ-23 row), a new §6 row is the correct, complete precedent-following choice — flagging as a scope
  clarification rather than assuming, since the ticket text is genuinely ambiguous between "the WORLD
  DYNAMICS pillar table" (could mean §5 only) vs. the full 3-location `building_sabotaged` pattern.
- **Positive counterpart event**: the ticket's own Assumptions section already defaults to "no
  positive counterpart," matching `building_sabotaged` (no positive twin) rather than
  `CONSERVATION`'s paired `_violated`/`_verified` shape. No new evidence found that changes this
  default — confirmed correct as stated.

## Anti-Drift Hazards

- **Do not touch `HardLawMonitor.check_initial_placement()` or its call site's persistence/alert
  logic** (`Kernel._run_initial_placement_check()`, `hard_law_violations.jsonl` writing,
  `AlertsManager` routing) — that machinery is correct, tested, and owned by the closed parent
  ticket. If the blocking finding above is resolved by adding `SimulationEvent` emission to
  `_run_initial_placement_check()`, that addition should be a minimal, additive change (one new
  `SimulationEvent` construction + `EventRecorder.record()` call, mirroring `_phase_observability`'s
  existing `InvariantViolation` construction shape at lines 892-903) — not a rewrite of the method's
  existing mode-gating/persistence/alert-routing, which must stay byte-identical.
- **Do not touch `EconomyScorer`'s `CONSERVATION` branch** — explicitly out of scope per the
  ticket, confirmed still fully separate code (`_translate_invariant`'s `CONSERVATION` branch and
  `EconomyScorer.EVENT_TYPES`' `conservation_law_violated`/`conservation_law_verified` are untouched
  by anything this investigation found relevant to this ticket).
- **Do not add a new top-level SimQ pillar or standalone determinism-scoring mechanism** — directly
  contradicted by the SimQ scope boundary this ticket itself correctly cites
  (`TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` §2.2/§2.7).
- **Do not literally copy `building_sabotaged`'s positive `+2.0` weight sign** — the new signal
  must use a negative weight (see Current Behavior/Risks above); this is the single most likely
  literal-precedent-copying mistake given how explicitly the ticket says "follow the exact
  precedent of `building_sabotaged`."
- **Do not silently resolve the Out-of-Scope-vs-AC#4 conflict by skipping AC #4** or by quietly
  editing `Kernel.__init__`/`_run_initial_placement_check()` without flagging it — per this
  project's Clarification Rule, this is exactly a "conflict with existing system" case that should
  be surfaced (in `plan.md` or to the requester), not silently decided by Implement.
- **`_translate_invariant()`'s `startswith()` semantics**: confirm the new branch checks
  `law_id.startswith("LAW-SPAWN-OCCUPANCY")` (or equivalently `== "LAW-SPAWN-OCCUPANCY"` — there is
  currently exactly one law with this exact id, no sub-variants), not a shorter/looser prefix like
  `"LAW-SPAWN"` that could accidentally swallow some unrelated future `LAW-SPAWN-*` law. `COMBAT`/
  `CONSERVATION` are deliberately short prefixes because those namespaces don't collide with
  anything else; `LAW-SPAWN-OCCUPANCY` is already namespaced by the existing `LAW-*` convention
  shared with all 7 `HardLawMonitor` laws, so an exact or near-exact match is the safer choice here.
