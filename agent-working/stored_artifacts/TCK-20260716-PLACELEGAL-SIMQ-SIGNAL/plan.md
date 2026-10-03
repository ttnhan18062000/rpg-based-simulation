---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-SIMQ-SIGNAL
artifact_type: plan
tags: [simulation-quality, observability, world]
---

# Implementation Plan — TCK-20260716-PLACELEGAL-SIMQ-SIGNAL

## Summary

Add a WORLD DYNAMICS frequency signal for `LAW-SPAWN-OCCUPANCY` violations, following the
`COMBAT*`/`CONSERVATION*` `_translate_invariant()` dispatch precedent (not the structurally
different `building_sabotaged` `EventExtractor` precedent — investigation confirmed these are two
different code paths). Four pieces of work: (1) a new `LAW-SPAWN-OCCUPANCY` branch in
`quality_hub.py::_translate_invariant()`, (2) a new `spawn_occupancy_violation` event type in
`WorldDynamicsScorer`, scored with a **negative** weight mirroring `combat_hard_law`'s per-event
hard-law-violation magnitude (`-30.0`) rather than `building_sabotaged`'s positive
`infrastructure_damaged` sign, (3) the three `quality_scoring_contract.md` touch points
(`building_sabotaged`/SQ-23 pattern: event-types list, §5 signal table, §6 scenario row), and (4) a
narrow, user-approved extension to `Kernel._run_initial_placement_check()` (out of this ticket's
original scope, now explicitly brought in — see Deviations) so the new dispatcher branch is
actually reachable from a real `Kernel` run, not just from hand-built test envelopes. Direct source
inspection during planning found that literally mirroring `_run_hard_law_checks()`'s/
`_phase_observability()`'s existing `payload=v.details` shape would leave the new branch permanently
unreachable even after the scope extension, because no current violation payload ever contains a
`"law_id"` key (`ObservabilityEventEnvelope.from_simulation_event()` copies `payload` verbatim,
adding nothing) — this is documented explicitly in Step 4 and the Deviations section as a
load-bearing, minimal correction, not scope creep. Work closes with the `--dry-run` anchor-stability
check per AC #4, now able to produce a real (not trivially-empty) diff.

## Steps

### Step 1 — Add `LAW-SPAWN-OCCUPANCY` branch to `_translate_invariant()`
**Files:** `src/simulation_quality/quality_hub.py`

**Change:** In `_translate_invariant()` (lines 59-65), add a third branch, after the existing
`COMBAT`/`CONSERVATION` checks and before the final pass-through, mirroring their exact
`str.startswith()` shape:

```python
def _translate_invariant(env: ObservabilityEventEnvelope) -> str:
    law_id = str((env.payload or {}).get("law_id", "")).upper()
    if law_id.startswith("COMBAT"):
        return "combat_hard_law_violation"
    if law_id.startswith("CONSERVATION"):
        return "conservation_law_violated"
    if law_id.startswith("LAW-SPAWN-OCCUPANCY"):
        return "spawn_occupancy_violation"
    return env.event_type  # unknown violation — no translation
```

Use `startswith("LAW-SPAWN-OCCUPANCY")`, not a shorter prefix like `"LAW-SPAWN"` — per
investigation's Anti-Drift Hazards, `LAW-SPAWN-OCCUPANCY` is already namespaced under the shared
`LAW-*` convention (unlike the short, collision-free `COMBAT`/`CONSERVATION` namespaces), so a
near-exact match avoids accidentally swallowing a hypothetical future `LAW-SPAWN-*` law.

**Do NOT touch:** the `COMBAT`/`CONSERVATION` branches, their order, or `_translate_lifecycle`/
`_translate_quest_event`/other translators in this file. Do NOT touch `_TRANSLATE_SIMPLE` or
`_TRANSLATE_CONDITIONAL`'s registration table — `InvariantViolation` is already registered there.

**Verify:** `test_invariant_spawn_occupancy_law`, `test_invariant_spawn_occupancy_no_violation_no_translation`
(new, `tests/simulation_quality/test_quality_hub_event_translation.py`, per test_plan.md items 1-2),
plus existing `test_invariant_combat_law`/`test_invariant_conservation_law`/
`test_invariant_unknown_no_translation` passing unmodified.

---

### Step 2 — Add `spawn_occupancy_violation` to `WorldDynamicsScorer`
**Files:** `src/simulation_quality/scorers/world_dynamics.py`, `config/simulation_quality/scoring_weights.yaml`

**Change (two edits):**

1. `EVENT_TYPES` (lines 19-35): append `"spawn_occupancy_violation"` as a new 16th tuple entry,
   after `"building_sabotaged"`.
2. `score()`: add a new unconditional branch, placed directly after the existing
   `building_sabotaged` branch (lines 175-176), following its exact shape but with the **negative**
   weight key resolved by this plan (see Resolved Decisions below):

```python
        if et == "spawn_occupancy_violation":
            return _rec(self.weights["spawn_occupancy_violation"], "spawn placement violated occupancy/terrain legality — correctness fault, zero occurrences is the target", ("spawn_occupancy_violation",))
```

3. `config/simulation_quality/scoring_weights.yaml`, `WORLD:` section (after `infrastructure_damaged: 2.0`
   at line 163, grouped with the file's existing positive-weights-then-negative-weights ordering —
   place it with the negative block, after `trauma_accumulation_broken: -8.0` at line 171): add
   `spawn_occupancy_violation: -30.0`.

**Do NOT touch:** any other `EVENT_TYPES` entry, any other `score()` branch (`calamity_spawned`,
`ecology_cycle_completed`, `threat_evolved`/`node_recharged`'s `None` returns, etc.), or any other
pillar's section of `scoring_weights.yaml` (`COMBAT:`, `FACTION:`, `NARRATIVE:`, etc.). Do NOT touch
`EconomyScorer`/`CONSERVATION` weight keys.

**Verify:** `test_spawn_occupancy_violation_in_world_dynamics_event_types`,
`test_spawn_occupancy_violation_scores_negative`, `test_scoring_weights_yaml_has_spawn_occupancy_key`
(new, `tests/simulation_quality/test_world_dynamics_scorer.py`, per test_plan.md items 3-5), plus
`test_spawn_occupancy_weight_is_negative` (Anti-Drift Test Guard) asserting the YAML value is `< 0`.

---

### Step 3 — `docs/simulation_quality/quality_scoring_contract.md` and `docs/simulation_quality/event_type_coverage.md` — all four `building_sabotaged`-parallel touch points
**Files:** `docs/simulation_quality/quality_scoring_contract.md`, `docs/simulation_quality/event_type_coverage.md`

**(Added after architecture-review NEEDS_CHANGES round — see Deviations Revision 1.)** The plan
originally scoped only `quality_scoring_contract.md`'s three locations. Architecture review found
the real `building_sabotaged` precedent (`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`) also updated
`docs/simulation_quality/event_type_coverage.md` (registry-tagged `status: authoritative`) — its
§1.3 `_TRANSLATE_CONDITIONAL` table already lists the `COMBAT`/`CONSERVATION` law_id-dispatch rows
this ticket's Step 1 branch sits beside, and line 177 currently claims all `_TRANSLATE_CONDITIONAL`
entries are "correct and complete as of this audit" — a claim Step 1 would make stale/false if this
doc isn't also updated. Four edits total, two files:

1. `quality_scoring_contract.md` §5 WORLD DYNAMICS "Event types scored" list (line 908): append
   `, spawn_occupancy_violation` after `building_sabotaged`.
2. `quality_scoring_contract.md` §5 WORLD DYNAMICS Signal/Delta/Tag table (after the `Building takes
   sabotage damage...` row, line 927, in the negative-signal block alongside `Zero calamity
   events...`): add
   `| Spawn placement violates occupancy/terrain legality (LAW-SPAWN-OCCUPANCY) | −30 | spawn_occupancy_violation |`.
3. `quality_scoring_contract.md` §6 Scenario Registry (new row, `SQ-24`, immediately after the
   `SQ-23` row at line 1031):

   `| SQ-24 | Does illegal spawn placement register as a real correctness fault? | WORLD | — | spawn_occupancy_violation | Frequency signal only — detection/legality is HardLawMonitor's job (LAW-SPAWN-OCCUPANCY); SimQ scores how often it occurs, not whether one placement is legal, per the determinism-exclusion precedent (TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC §2.2) |`

4. `event_type_coverage.md`: append a `spawn_occupancy_violation` row to the §1.3
   `_TRANSLATE_CONDITIONAL` table (mirroring the existing `COMBAT`/`CONSERVATION` rows' shape), bump
   the Summary table's "scored" count (line 27, currently 82 → 83), and update the "Last updated"
   line — mirroring exactly what `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` did for
   `building_sabotaged` (its own row at line 108, Summary/Last-updated at lines 27/34).

**Do NOT touch:** any other pillar's table in either doc, the `building_sabotaged`/SQ-23 row itself,
`quality_scoring_contract.md` §7 Extensibility Protocol's own procedure text or §1/§2 scope sections,
or any other row in `event_type_coverage.md`'s §1.3 table.

**Verify:** manual review that all four locations match the `building_sabotaged` precedent's shape
exactly (per test_plan.md item 7 — no automated doc-parity test exists in this repo today).

---

### Step 4 — Narrow `Kernel._run_initial_placement_check()` extension: emit a `SimulationEvent`
**Files:** `src/engine/kernel.py`

**Scope note:** this step is an explicit, user-approved deviation from this ticket's original
Out-of-Scope line. See the Deviations section below for the full record — do not skip this step's
"Do NOT touch" list, which is what keeps the deviation narrow.

**Change:** In `_run_initial_placement_check()` (`src/engine/kernel.py:740-806`), add exactly one
new block: after violations are found (i.e. after the existing `if not violations: return` early-out
at what is currently the method's line ~756, and it does not matter whether this is placed before or
after the existing `hard_law_violations.jsonl` write / `AlertsManager` routing block — place it
directly after the `AlertsManager` routing `try/except` block, immediately before the final
`mode in (DEBUG, CERTIFICATION)` raise/`LIGHT` log branch, so persistence and alerting are
unaffected by this new code running), construct and record one `SimulationEvent` per violation:

```python
        from src.observability.events import SimulationEvent
        for v in violations:
            payload = dict(v.details)
            payload["law_id"] = v.law_id
            event = SimulationEvent(
                event_type="InvariantViolation",
                event_category="hard_law",
                tick=0,
                severity=v.severity,
                source_system="hard_law_monitor",
                message=v.message,
                entity_id=v.entity_id,
                payload=payload,
            )
            if self._event_recorder is not None:
                self._event_recorder.record(event)
```

**Load-bearing detail, not optional:** `payload["law_id"] = v.law_id` must be added explicitly.
`_phase_observability()`'s own existing per-tick construction (kernel.py:890-903) passes
`payload=v.details` with no `law_id` key merged in, and direct source inspection during planning
confirmed `v.details` never contains a `"law_id"` key for any law (including the pre-existing
`COMBAT`/`CONSERVATION` producers) and `ObservabilityEventEnvelope.from_simulation_event()` copies
`payload` verbatim — so a byte-literal copy of `_phase_observability`'s shape would leave
`_translate_invariant()`'s `law_id.startswith(...)` check permanently unable to match, even after
this step lands, defeating the entire purpose of the scope extension (see Deviations). This is the
smallest possible correction that makes the already-approved feature actually work: one dict merge,
no new detection logic, no change to `HardLawViolation`'s own fields.

Guard `self._event_recorder is not None` mirrors the existing `if self._artifact_repo and
self._run_id:` guard already present a few lines above in this same method for the jsonl-write path
— do not assume `_event_recorder` is always constructed at this point in `__init__` without checking
(confirm via investigation-during-implementation exactly where `self._event_recorder` is assigned
relative to `self._run_initial_placement_check()`'s call site; if it is assigned after, wrap this
block in the same conditional or move nothing else — only this new block's execution is
conditional).

**Do NOT touch:**
- `HardLawMonitor.check_initial_placement()` itself (owned by the closed parent ticket).
- The existing mode-gating (`OFF` early return), `hard_law_violations.jsonl` persistence, or
  `AlertsManager.get_router().route(...)` calls already in this method — byte-identical before and
  after this step.
- The final `mode in (DEBUG, CERTIFICATION)` raise / `LIGHT` log branch's existing logic.
- `Kernel.__init__`'s call site itself (`self._run_initial_placement_check()` is still called exactly
  once, in the same place) — only the method body gains this one new block.
- `_run_hard_law_checks()` or `_phase_observability()` — neither is modified; this step adds an
  independent, additive emission path scoped to the init-time method only.

**Verify:** the new integration test (test_plan.md item 6, e.g.
`test_spawn_occupancy_violation_reaches_world_pillar_via_minimal_kernel`,
`tests/simulation_quality/test_traceability_path.py`), extended per Step 5 below to also cover a
*real* `Kernel()`-construction path (not just the `minimal_kernel` fixture's manual
`_event_recorder.record()` injection) so this step's actual production wiring is exercised, not
only test-injected. Also re-run `tests/engine/test_hard_law_monitor.py` and
`tests/integration/observability/test_initial_placement_check.py` (the parent ticket's own tests)
unmodified to confirm zero collateral change to detection/persistence/alerting.

---

### Step 5 — Integration test: real `Kernel` construction reaches the WORLD pillar
**Files:** `tests/simulation_quality/test_traceability_path.py` (or a new sibling file if fixture
scope doesn't fit — decide during implementation per test_plan.md item 6's own noted contingency)

**Change:** Two tests:

1. **Injection-pattern test** (works regardless of Step 4's real wiring, proves the dispatcher +
   scorer path end-to-end): mirror `_inject_combat_hard_law_violation()`
   (`test_traceability_path.py` lines 58-66) with a new
   `_inject_spawn_occupancy_violation(kernel)` helper that calls
   `kernel._event_recorder.record(SimulationEvent(event_type="InvariantViolation",
   event_category="hard_law", tick=0, severity="ERROR", source_system="hard_law_monitor",
   message="...", entity_id=<id>, payload={"law_id": "LAW-SPAWN-OCCUPANCY", "object_kind": "entity",
   "tile": [1, 1], "colliding_object_kind": "entity", "colliding_object_id": 2}))` directly, then
   assert `kernel._quality_hub.get_quality_report().pillars["WORLD"].worst_events` is non-empty and
   the matching record traces back to `simulation_events.jsonl`, mirroring
   `test_worst_event_id_resolves_in_simulation_events_jsonl` exactly.
2. **Real-wiring test** (proves Step 4's actual production code path, not just the injection
   helper): construct a `Kernel` against a compiled world/seed known from the parent ticket's own
   regression test to reproduce a real `LAW-SPAWN-OCCUPANCY` violation at construction time (the
   parent ticket's `seed=42` / `unit_information_density` collision, per
   `tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision`), then
   assert the same `worst_events`-non-empty / traceability outcome as test 1 — this is the one test
   in the whole ticket that proves the dispatcher branch is reachable from real `Kernel.__init__`,
   not merely reachable from a hand-built envelope or a manually-injected event.

**Do NOT touch:** the existing `_inject_combat_hard_law_violation`/
`test_worst_event_id_resolves_in_simulation_events_jsonl`/
`test_worst_event_id_matches_originating_envelope_exactly` tests — new tests only, added alongside.

**Verify:** both new tests pass; confirms AC #1 and the real-wiring half of AC #4.

---

### Step 6 — Anchor/grade-stability check
**Files:** none (verification only)

**Change:** none — run, before and after Steps 1-5 land:

```bash
python3 tools/evaluate_simq.py --dry-run   # == make evaluate --dry-run (Makefile:321-322)
```

Per investigation: this diffs existing `data/calibration/` reports against
`tests/simulation_quality/fixtures/grade_anchors.json`; it does not re-run the engine. Because Step 4
now gives `LAW-SPAWN-OCCUPANCY` a real production emission path, worlds/seeds that genuinely
reproduce the seed-42-style collision can now show a real grade delta once their calibration reports
are regenerated (`evaluate-full`, or a targeted `tools/calibrate_simq.py` run against the known
colliding seed, per test_plan.md item 8's second bullet) — anchors that do *not* reproduce a
placement collision (e.g. `wilderness_survival`, confirmed clean by the parent ticket at seeds
42/137/999) must show **zero** diff. Run `--dry-run` first with no calibration regeneration to
confirm the pre-change baseline, then regenerate calibration for at least one known-affected seed and
re-run `--dry-run` to confirm the expected delta appears only there.

**Do NOT touch:** any anchor/calibration fixture file (`grade_anchors.json`) directly — if a real,
expected delta appears for an affected seed and the fixture needs updating to reflect the new
intentional signal, that is a separate, explicit recalibration action (per the `obs-isolation`
precedent: "if any diff appears, stop and investigate before recalibrating") — not a silent edit
folded into this verification step.

**Verify:** unaffected anchors show no diff; the known-affected seed (if calibration is regenerated
for it as part of this check) shows a real, negative, non-trivial delta attributable to
`spawn_occupancy_violation`.

## Deviations

**Out-of-Scope override (Kernel call-site extension), decided by the user, not by this plan
unilaterally.**

The ticket's own Out of Scope section states: *"Anything in `HardLawMonitor` itself, or the call-site
wiring in `Kernel.__init__` — entirely owned by `TCK-20260716-PLACELEGAL-HARDLAW`."*
`investigation.md`'s Risks/Open Questions section (the "BLOCKING" finding) found, via direct source
read, that `Kernel._run_initial_placement_check()` (`src/engine/kernel.py:740-806`) — the sole
producer of `LAW-SPAWN-OCCUPANCY` violations — persists to `hard_law_violations.jsonl` and routes
through `AlertsManager`, but never sets `self._status.current_tick_violations` and never constructs a
`SimulationEvent`. `_phase_observability()` (`src/engine/kernel.py:~891`) — the *only* code that
converts violations into `InvariantViolation` `SimulationEvent`s for the observability bus / SimQ —
only reads `current_tick_violations`, and only runs inside `tick_once()`, never `__init__`. Net
effect, confirmed by investigation: as scoped, this ticket could ship a fully correct, fully tested
dispatcher (Step 1) + scorer (Step 2) + contract doc (Step 3) that is **permanently unreachable** by
any real production `Kernel` run, and `tools/calibrate_simq.py::_replay_jsonl_through_hub()` (which
`tools/evaluate_simq.py --dry-run` depends on) replays `simulation_events.jsonl`, not
`hard_law_violations.jsonl`, so the AC #4 anchor check would trivially show zero diff regardless of
whether the change is correct.

This was raised to the user as a blocking decision (investigation.md's three plausible resolutions:
accept the gap as a documented two-ticket split; narrowly extend this ticket's scope to add
`SimulationEvent` emission to the existing `_run_initial_placement_check()` method; or re-scope AC #4
to only cover the directly-testable dispatcher/scorer path). **The user chose the second option:**
"Narrow scope extension" — extend this ticket's scope by one small, explicitly-scoped addition
(Step 4 above) so the dispatcher branch this ticket adds actually fires and AC #4 is verifiable now.

This is scoped narrowly and deliberately, per the user's own framing and investigation's Anti-Drift
Hazards guidance ("if the blocking finding is resolved by adding `SimulationEvent` emission..., that
addition should be a minimal, additive change... not a rewrite of the method's existing
mode-gating/persistence/alert-routing, which must stay byte-identical"):
- Only `_run_initial_placement_check()`'s body gains one new block (Step 4); its existing
  persistence/alert-routing/mode-gating logic is untouched.
- `HardLawMonitor.check_initial_placement()` itself is not touched — no new detection logic, no
  changed law semantics.
- `Kernel.__init__`'s call site (the single `self._run_initial_placement_check()` call) is unchanged
  — still called exactly once, in the same place.
- This is justified as appropriate for a plan-phase (not implementer-phase) decision because the
  parent ticket (`TCK-20260716-PLACELEGAL-HARDLAW`) that the Out-of-Scope line was protecting is now
  **closed** — the override is not reopening or conflicting with in-flight work, it is a small,
  targeted follow-on addition to that ticket's now-stable call site, made necessary only because
  this ticket's own deliverable (Steps 1-3) would otherwise be unreachable dead code.

**Payload shape correction (found during planning, not in investigation.md), documented here since it
is load-bearing for the deviation above to actually work.** Investigation flagged the missing
`SimulationEvent` construction but did not trace `payload` field provenance all the way through.
Direct source read during planning (`src/observability/hard_law_monitor.py`,
`src/engine/kernel.py:890-903`, `src/observability/events.py`'s
`ObservabilityEventEnvelope.from_simulation_event()`) confirmed that literally mirroring
`_phase_observability()`'s existing `payload=v.details` construction shape — which is what "mirroring
`_run_hard_law_checks()`'s existing pattern" most literally means — would **not** include a
`"law_id"` key in the resulting envelope's `payload`, because `HardLawViolation.details` never
carries `law_id` for any law today (confirmed via grep — `law_id` only appears explicitly placed in
test helpers' hand-built payloads, never in production `details` dicts), and envelope construction
does not add it either. Since `_translate_invariant()`'s only signal is
`env.payload.get("law_id", "")`, a literal `payload=v.details` copy would leave Step 1's new branch
just as unreachable as before Step 4, silently defeating the user-approved deviation. Step 4 therefore
explicitly merges `payload["law_id"] = v.law_id` — a one-line, non-optional correction, not new scope.
This does not affect the *existing* `COMBAT`/`CONSERVATION` branches or `_phase_observability()`'s
own per-tick payload construction, neither of which is touched by this ticket; whether those two
existing branches have the same latent unreachability problem in production is a separate, pre-existing
question outside this ticket's scope (not raised here as a new ticket per this plan's own "don't plan
adjacent work" rule, but worth flagging to the requester if not already known).

**Revision 1 (architecture-review NEEDS_CHANGES round).** An architecture-reviewer pass on the
original Step 3 draft (three `quality_scoring_contract.md` edits only) returned NEEDS_CHANGES,
finding that the real `building_sabotaged` precedent this plan claims to fully mirror actually
touched a second, registry-tagged-authoritative doc — `docs/simulation_quality/event_type_coverage.md`
— which this plan's original Step 3 omitted. That doc's §1.3 table and its "all entries correct and
complete" claim (line 177) would go stale/false once Step 1's new `_TRANSLATE_CONDITIONAL` branch
lands, violating the Authoritative Mechanics Rule's "documentation and source code must remain in
100% semantic parity." Fixed by adding a fourth edit to Step 3 (now retitled to cover both files):
append the new row to `event_type_coverage.md`'s §1.3 table, bump its Summary "scored" count, and
update its "Last updated" line. The reviewer's two other observations — the `self._event_recorder is
not None` guard in Step 4 being vestigial (construction order confirms it's always-true, harmless but
not a real optional-dependency check) and the ticket body's `## Implementation Notes`/`## Assumptions`
sections still reading "(pending)" — are non-blocking; the guard is left as defensive code per the
plan's own "smallest possible correction" principle for Step 4, and the ticket body will be filled in
by Implement as usual (not a plan-phase concern). All other steps, Resolved Decisions, and Scope
Guards are unchanged from the original plan.

**Revision 2 (found during Implement — approved plan omitted a parity ledger entry).** The plan's
four-edit Step 3 scope (`quality_scoring_contract.md` + `event_type_coverage.md`) does not include
`docs/parity_ledger/`, but investigation.md's Parity Ledger Overlap section explicitly flagged: "No
existing parity ledger entry currently documents `_translate_invariant()`'s `law_id` dispatch table
itself... A new entry is needed in `world_dynamics.yaml` (or `infrastructure.yaml`)... once this
ticket's dispatcher branch + scorer logic land." Neither review round caught this gap against the
project's Authoritative Mechanics Rule ("If logic changes, update the corresponding doc AND the
parity ledger entry... in the same session"). Implement added `WORLD-113` to
`docs/parity_ledger/world_dynamics.yaml` (status: verified, priority: P2, following the `WORLD-112`
entry's exact shape/location) covering the new dispatcher branch, scorer, weight, and the Step 4
Kernel emission path, with `test_path` pointing at the three new tests added in Steps 1/2/5. This is
a minimal, additive documentation correction — no code behavior changed as a result, no other
parity ledger entry was touched, and it does not alter any of Steps 1-6's actual implementation. Not
flagged as a code-scope deviation (nothing in "Do NOT touch" for any step covers `docs/parity_ledger/`),
but recorded here per the ticket workflow's "never silently deviate" rule since the approved plan's
Step 3 did not call it out explicitly.

## Scope Guards

Reiterated from the ticket's Out of Scope section, with the one explicit, user-approved carve-out
noted:

- `HardLawMonitor` itself (`src/observability/hard_law_monitor.py`,
  `check_initial_placement()`'s own detection algorithm) — untouched by any step in this plan.
- `Kernel.__init__`'s call-site wiring (the single call to `_run_initial_placement_check()`) —
  untouched; only the *body* of the already-existing `_run_initial_placement_check()` method gains
  one additive block (Step 4), per the explicit user-approved deviation above. Do not treat this as
  license to touch anything else in `Kernel.__init__`.
- `EconomyScorer`'s `CONSERVATION` branch (`conservation_law_violated`/`conservation_law_verified`)
  and its `scoring_weights.yaml` keys — completely untouched by any step.
- No new SimQ pillar, no standalone determinism-scoring mechanism — `PillarId` enum membership stays
  at its current 10 values.
- No historical/retroactive re-scoring of past runs' existing `hard_law_violations.jsonl` records.
- No positive/"no violations" counterpart event — matches `building_sabotaged`'s no-positive-twin
  shape, per the ticket's own Assumptions default (no new evidence found that changes this).
- Do not edit `grade_anchors.json` directly as part of Step 6 — any real recalibration is a separate,
  explicit action outside this ticket, per the `obs-isolation` "stop and investigate before
  recalibrating" precedent.

## Dependency Map

- **Step 1** (dispatcher branch) has no dependencies — can start immediately; testable in isolation
  via hand-built envelopes regardless of Steps 2-6.
- **Step 2** (scorer + weight) has no dependency on Step 1 (different file, different unit tests) but
  is logically paired with it — both are needed before Step 5's integration test can pass end-to-end.
- **Step 3** (contract doc) depends on Steps 1-2 only in the sense that the event-type name and
  weight sign must be finalized first (both are fixed by this plan already — Step 3 can proceed in
  parallel with Steps 1-2's implementation).
- **Step 4** (Kernel extension) is independent of Steps 1-3's code (different file) but is required
  for Step 5's real-wiring test and Step 6's non-trivial anchor check to mean anything.
- **Step 5** (integration tests) depends on **Step 1**, **Step 2**, and **Step 4** all being complete
  — it exercises the full dispatcher → scorer → pillar path via both a manual injection and a real
  `Kernel` construction.
- **Step 6** (anchor check) depends on **Step 4** and **Step 5** — meaningless before Step 4 lands
  (would show a trivial zero-diff), and should follow Step 5 so a known-good test already proves the
  wiring before spending a calibration run on it.

Suggested implementation order: Step 1, Step 2, Step 3 (parallelizable), then Step 4, then Step 5,
then Step 6 last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `_translate_invariant()` correctly routes the new law's violations to the new event type; unit test covers both branches | Step 1 | `test_invariant_spawn_occupancy_law`, `test_invariant_spawn_occupancy_no_violation_no_translation` |
| `WorldDynamicsScorer.EVENT_TYPES` includes the new event type; scoring logic produces a real, non-zero grade delta, negative-signal shape | Step 2 | `test_spawn_occupancy_violation_in_world_dynamics_event_types`, `test_spawn_occupancy_violation_scores_negative`, `test_scoring_weights_yaml_has_spawn_occupancy_key` |
| `quality_scoring_contract.md` WORLD DYNAMICS table has a new row, SQ-23 format | Step 3 | manual review (no automated doc-parity test in this repo) |
| Anchor/grade-stability check: unaffected anchors unchanged; affected runs show a real, expected grade delta | Step 4 (makes the signal reachable), Step 6 (runs the check) | `python3 tools/evaluate_simq.py --dry-run` before/after; `test_evaluate_dry_run_unaffected_anchors_unchanged` |
| Depends on `TCK-20260716-PLACELEGAL-HARDLAW` DONE first | N/A — precondition, already satisfied (parent ticket confirmed DONE in investigation.md) | — |
| (Deviation) Dispatcher branch actually reachable from a real `Kernel` run, not just hand-built envelopes | Step 4, Step 5 | real-wiring test in Step 5 (Kernel construction against a seed-42-style colliding world) |

## Anti-Drift Notes

- **Do not literally copy `building_sabotaged`'s positive `+2.0`/`infrastructure_damaged` weight
  sign.** The new signal must be negative (Step 2) — mirroring `combat_hard_law: -30.0`'s
  per-event hard-law-violation magnitude, a closer precedent than `building_sabotaged` since both
  are `HardLawMonitor` violations routed through `_translate_invariant()`, not organic WORLD
  "the world is alive" evidence.
- **Do not literally copy `_phase_observability()`'s `payload=v.details` shape in Step 4** without
  the `payload["law_id"] = v.law_id` merge — see Deviations section; this is the single most likely
  way to ship Step 4 as a no-op that looks correct in code review but never actually fires in
  production.
- **`_translate_invariant()`'s `startswith()` semantics:** use `"LAW-SPAWN-OCCUPANCY"` (near-exact),
  not a shorter `"LAW-SPAWN"` prefix — see Step 1.
- **Do not touch `EconomyScorer`/`CONSERVATION`** — confirmed fully separate code, not touched by
  anything in this plan.
- **Do not add a new SimQ pillar** — `PillarId` enum stays at 10 members; this is a WORLD DYNAMICS
  signal only, per the ticket's own citation of `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` §2.2/§2.7.
- **Weight key / event-type / tag naming, fixed by this plan (was an open question in the ticket):**
  event_type = `spawn_occupancy_violation`; weight key = `spawn_occupancy_violation`; `ScoreRecord`
  tag = `spawn_occupancy_violation` (single consistent name throughout, unlike
  `building_sabotaged`/`infrastructure_damaged`'s split naming — chosen for this signal specifically
  because there is no ambiguity to resolve by splitting the names, and it keeps Steps 1-3 trivially
  greppable as one string).
- **Scenario Registry row is in scope** (Step 3, `SQ-24`) — investigation flagged this as an
  ambiguous reading of the ticket's Scope bullet; resolved here by following the complete
  `building_sabotaged`/SQ-23 3-location precedent, per §7.2 step 4's explicit "if the scenario is
  new" instruction.
- **`config/simulation_quality/scoring_weights.yaml` is a hard runtime dependency**, not optional —
  `PillarWeightsView.__getitem__` raises `KeyError` for any missing key; Step 2 must land the YAML
  edit in the same change as the scorer code, never one without the other.
- Clean up `data/runs/` and `reports/release_proof/` after Step 5/6's test runs, per the project's
  standard After Work cleanup rule, before this ticket is marked done.
