---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION
artifact_type: plan
tags: [feature-flags, world]
---

# Implementation Plan — TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION

## Summary
This ticket produces evidence, not code — same shape as its two already-closed siblings
(`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`, `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`).
The plan decides the trial worlds/seeds/tick-counts (Step 1), runs a real OFF/ON corpus trial on
each (Steps 2-3), extracts and tallies the four real signal groups investigation.md identified as
disqualifying `world_emergence_event` counts and requiring `metric_counters`/`quest_registry`/
entity-`property_updates` inspection instead (Step 4), runs the no-suppression check against those
signals — not against `world_events_add`/`world_emergence_event` (Step 5), writes the raw record
to `trial_evidence.md` (Step 6), adds the `ENABLE_WORLD_CAPABILITY_LAYER` static-inertness
regression guard test_plan.md already specified (Step 7), writes the real decision into
`docs/architecture/rollout_flag_decisions_m1.md` (Step 8), updates this ticket's own body (Step 9),
and re-runs the scoped regression suite (Step 10). No file under `src/` is touched except the one
new test file. Per DEV-003's own "shipped, standing production profile" bar (already applied
identically to both siblings) and the fact that zero shipped `config/simulation_quality/profiles/*.yaml`
turns `ENABLE_WORLD_EMERGENCE` on today (investigation.md's own full-file read of
`corpus_registry.yaml`, confirmed again in this plan's own fact-check — see Step 1), the expected
recommendation is **"Keep OFF, deferred — real trial evidence now on file, no shipped profile turns
it on."** This is the working conclusion Step 4-6's real data must confirm or overturn, not a
foregone one — matching both siblings' own stated posture.

## Steps

### Step 1 — Decide trial worlds, seeds, and tick counts
**Files:** None changed (decision step only; recorded here and repeated verbatim in Step 2's
commands).
**Change:** Per the Uncertainty Rule ("vague leads stay vague until evidence narrows them"),
investigation.md explicitly left world/seed/tick-count selection to Implement/Plan rather than
pre-deciding it. This plan decides it now, using investigation.md's own reasoning plus fresh
verification of `config/simulation_quality/corpus_registry.yaml` (read directly this session,
`_worlds.dungeon_crawl` block and `_worlds.resource_dense_basin` block) and
`config/simulation_quality/profiles/` (directory listing, read directly this session):

1. **Primary — `dungeon_crawl`, seed 42, 2000 ticks.** `dungeon_crawl` is the `monster_only_gauntlet`
   archetype (`corpus_registry.yaml` `_worlds.dungeon_crawl.archetype`, confirmed by direct read),
   32 entities, and already has a dedicated scoring profile
   (`config/simulation_quality/profiles/dungeon_crawl.yaml` exists — confirmed by `ls` this
   session), so no `--profile default` override is needed (matches how the
   `ENABLE_COMBAT_ENGAGEMENT` sibling ran it, `stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/plan.md`
   Step 1). It is likely to produce real `ENTITY_DEATH`/`CAMP_RAID` `WorldEvent`s from its
   purpose-built combat content — the two of `WorldEmergencePhase`'s three event categories
   (`RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID`, `src/domains/world_emergence/phase.py:61-74`,
   read directly this session) that a monster-gauntlet world is best positioned to exercise.
   `dungeon_crawl_seed42_2000t` is also a real shipped run_key (`corpus_registry.yaml`
   `_worlds.dungeon_crawl.run_keys`, confirmed present), giving this leg a standing shipped
   baseline to sanity-check the OFF run against.
2. **Secondary — `resource_dense_basin`, seed 42, 1000 ticks (extended beyond its shipped 200-tick
   run_keys), `--profile default`.** `resource_dense_basin` has the highest `resource_density`
   (2.3333) and `resource_node_count` (7) of any shipped world (`corpus_registry.yaml`
   `_worlds.resource_dense_basin.density`/`.scale`, confirmed by direct read this session) — the
   strongest candidate for exercising the third category, `RESOURCE_DEPLETED`, which
   `dungeon_crawl` (0.75 resource_density, 3 resource_node_count) is unlikely to produce in volume.
   It has no dedicated scoring profile (`ls config/simulation_quality/profiles/` has no
   `resource_dense_basin*.yaml`, confirmed this session), so `--profile default` is required, same
   as investigation.md's Corpus Trial Candidates already specified. Its only shipped run_keys are
   `*_200t` (`corpus_registry.yaml` `_worlds.resource_dense_basin.run_keys`, confirmed present, no
   `1000t`/`2000t` entries) — investigation.md itself flagged 200 ticks as likely too thin, citing
   `tests/integration/scenarios/test_resource_depletion.py`'s own 1000-tick synthetic window as the
   domain's precedent for reliably observing scarcity rise. `tools/calibrate_simq.py`'s `--ticks`
   argument (`calibrate_simq.py:470`, `parser.add_argument("--ticks", type=int, default=100)`,
   confirmed by direct read) is not restricted to a world's shipped run_keys — any integer tick
   count is a legal, already-supported invocation. This plan therefore decides 1000 ticks for
   `resource_dense_basin` rather than the shipped 200, to reduce the near-zero-baseline risk
   investigation.md's own Risks section warned against, at the cost of not matching an existing
   shipped run_key exactly (disclosed as a deliberate, evidence-grounded choice, not an oversight).

**Do NOT touch:** No corpus registry, profile YAML, or world content file — this step only reads
and selects among existing shipped worlds/profiles, per Out of Scope.
**Verify:** No test — this is a decision recorded here and consumed verbatim by Step 2's commands.

### Step 2 — Run the `dungeon_crawl` primary trial (OFF then ON)
**Files:** None changed. Writes only to `data/calibration/` and `data/runs/{run_id}/` (temporary,
cleaned at Finalize per Definition of Done — do not clean mid-ticket; Steps 4-6 read these
outputs).
**Change:** Run, using the interpreter substitution below (see "Environment Note"):
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_OFF

# ON
ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_ON
```
`ENABLE_WORLD_EMERGENCE=ON` as an env-var prefix is a real, already-supported override — confirmed
by direct read of `tools/calibrate_simq.py:238-283` (`_KNOWN_FLAGS` includes
`"ENABLE_WORLD_EMERGENCE"` at line 247, and the surrounding loop at line 272 reads
`os.environ.get(flag, "")` and writes into `state.feature_flags`, which `pipeline.py`'s `refine()`
applies onto the `FeatureFlagManager`). **Environment note (matching both siblings'
already-recorded deviation):** the worktree's bare `python3` lacks `pydantic`; run every command in
this plan with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` in place of the
bare `python3` shown above, with `cwd` left as the worktree, so `data/runs/` and
`data/calibration/` output still lands exactly where these commands specify. Record the printed
`run_id` for each invocation — Step 4 needs it to locate `simulation_events.jsonl` and
`quality_report.json`.
**Do NOT touch:** `src/domains/world_emergence/phase.py`, `src/engine/pipeline.py`,
`src/domains/optimization/feature_flags.py` — this step only runs existing tooling with an env-var
override, per this ticket's Out of Scope.
**Verify:** Both commands exit 0 and produce `data/runs/{run_id}/simulation_events.jsonl` and
`quality_report.json` for each leg (4 files total). No separate pytest assertion for this step,
consistent with test_plan.md ("the real corpus ON/OFF trial itself... is the primary new evidence
this ticket produces... not encoded as a new automated test").

### Step 3 — Run the `resource_dense_basin` secondary trial (OFF then ON)
**Files:** Same as Step 2 (temporary `data/calibration/` and `data/runs/` output only).
**Change:**
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 1000 --profile default \
  --output data/calibration/resource_dense_basin_seed42_1000t_world_emergence_OFF

# ON
ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 1000 --profile default \
  --output data/calibration/resource_dense_basin_seed42_1000t_world_emergence_ON
```
Same interpreter substitution as Step 2 applies. `--name resource_dense_basin` failing to resolve
would raise `FileNotFoundError` rather than silently falling back to the generic hero+goblins world
(`calibrate_simq.py:143-157`'s `_load_world_state()`, cited by investigation.md and not
re-disputed here) — a successful run itself confirms the real compiled
`data/worlds/resource_dense_basin/resolved/world.resolved.yaml` loaded. Record the printed `run_id`
for both legs.
**Do NOT touch:** Same scope guard as Step 2.
**Verify:** Both commands exit 0 and produce the same 4-file set (events/report x OFF/ON) as Step 2.

### Step 4 — Extract and tally the four real signal groups
**Files:** None changed (analysis only; the durable record is written in Step 6).
**Change:** For each of the 4 run legs (dungeon_crawl OFF/ON, resource_dense_basin OFF/ON), capture
the four signal groups investigation.md's "What evidence to capture" section specifies as the
*only* valid evidence for this flag (explicitly **not** `world_emergence_event` counts in
`simulation_events.jsonl` — investigation.md traced that event type to `world_events_add`, produced
by other pipeline phases (`diplomatic_transitions`, `military_conflict`, faction/sovereignty
systems) and consumed, not produced, by `WorldEmergencePhase`; confirmed independently this session
by direct read of `src/domains/world_emergence/phase.py:129-135`'s `replace(...)` call, which sets
only `entity_updates`, `world_updates`, `metric_counters`, and `quest_registry_add` — it never
touches `world_events_add`):
1. **Run/skip counters** — `metric_counters["run_world_emergence"]`/`["skip_world_emergence"]`,
   summed across all ticks in each leg's run. `src/engine/phase_graph.py:69` registers
   `"world_emergence"` with `must_run_every_tick=True` (confirmed by direct read this session) —
   expect ~0% skip-rate on both ON legs; a materially higher skip-rate is itself a new finding to
   disclose, not silently accepted.
2. **Phase telemetry** — `metric_counters["world_emergence_ms"]`/`["aggregates_generated"]`, summed
   or averaged across ticks in the ON legs (both fields are set unconditionally inside
   `WorldEmergencePhase.execute()` per-call, per the `phase.py:129-135` `replace(...)` read above) —
   confirms real work happens on ON ticks, not a no-op pass.
3. **Quest registry growth** — final-state `len(state.quest_registry)` (or an equivalent
   `chunk_*.json`/state-snapshot diff) between each world's OFF and ON leg. `quest_registry_add` is
   merged into `AuthoritativeState.quest_registry` exclusively at `src/engine/apply.py:328-330`
   (`for opp in update.quest_registry_add: new_quest_registry[opp.id] = opp`, confirmed by direct
   read this session). **Other writers to `quest_registry_add` on the same `StateUpdate`:** grepped
   `src/` this session for `quest_registry_add=` — exactly two hits:
   `src/domains/world_emergence/phase.py:134` (`WorldEmergencePhase.execute()`'s own `replace()`,
   the object of this trial) and `src/core/updates.py:1141` (`StateUpdate.merge()`'s own generic
   field-merge, not an independent content producer — it only propagates whatever a phase already
   set). No other phase in `src/` sets `quest_registry_add` — `WorldEmergencePhase` is the sole
   producer, so a change in `quest_registry` growth between OFF and ON legs is attributable to this
   flag alone, not confounded by another concurrent writer.
4. **Entity signal exposure** — whether `exposed_world_signals`/`force_route_reevaluation`
   `property_updates` appear on any entity in each ON leg's final state (bridged per-entity via
   `WorldToEntitySignalBridge`, per investigation.md; not globally logged, requires inspecting final
   entity state/chunk snapshot, not `simulation_events.jsonl`).
5. **Absolute OFF-baseline activity** — real `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID`
   `WorldEvent` counts feeding the aggregator in each world's OFF leg (these events are produced by
   other phases regardless of `ENABLE_WORLD_EMERGENCE`, per the red-herring finding above — count
   them via `recent_world_events`-producing phases' own output, e.g. `world_events_add` entries
   filtered by category in `simulation_events.jsonl`'s underlying `WorldEvent` records, or the
   ON leg's own `aggregates_generated` count as a proxy for how much real material was available to
   aggregate) — confirms neither trial world is degenerate/near-empty for this domain specifically,
   per both siblings' own disclosed near-zero-baseline caveat.
**Do NOT touch:** No source files — this step only reads generated JSONL/JSON/state-snapshot
artifacts.
**Verify:** A written tally (5 sub-signals x 4 legs, matching the numbered list above) exists and
explicitly states, per world, the real values observed. This tally is the direct evidence base for
Step 5's no-suppression check and Step 6/8's writeups — both must cite these exact numbers, not a
paraphrase.

### Step 5 — Run the no-suppression check against the four real signal groups
**Files:** None changed (analysis only).
**Change:** Using Step 4's tally (never `world_emergence_event`/`simulation_events.jsonl` raw
counts — those are unconditionally identical between ON and OFF per the red-herring finding, and
using them would produce a false "no suppression" result proving nothing about this flag, per
investigation.md's own Anti-Drift Hazards and test_plan.md's own Anti-Drift Test Guards), assess:
- The ON legs' run/skip counters (signal 1) show `WorldEmergencePhase` actually executing on
  effectively every eligible tick, not silently starved by
  `PhaseDependencyGraph.should_run_phase()` — this is the *structural* half of "no suppression":
  the phase ran, not just that it produced clean-looking output. (Structurally this ticket is
  already known to be immune to the TCK-20260809 merge-suppression bug class specifically —
  `WorldEmergencePhase.execute()` calls `dataclasses.replace()` on the incoming `update` parameter
  itself, per investigation.md's static confirmation and this plan's own re-read of
  `phase.py:129-135` above — so this step is the *empirical* confirmation investigation.md
  explicitly deferred to Implement, not a re-litigation of the static finding.)
- Quest-registry growth (signal 3) and telemetry (signal 2) on the ON leg are non-zero and the ON
  leg's `quest_registry` size strictly exceeds the OFF leg's for the same world (OFF legs must show
  `run_world_emergence=0`/`skip_world_emergence>0` and no `quest_registry_add`-sourced growth at
  all, since the phase never runs when the flag is OFF — this is the expected, not anomalous,
  OFF-leg signature).
- Entity signal exposure (signal 4) appears on at least some entities in the ON leg where OFF-leg
  absolute activity (signal 5) was non-trivial.
- If the OFF-baseline activity (signal 5) is itself near-zero for a world, that world's ON-vs-OFF
  comparison is disclosed as weak evidence for that world specifically (not silently treated as a
  clean pass) — matching both siblings' own disclosed near-zero-baseline caveat.
**Do NOT touch:** No source files.
**Verify:** An explicit pass/fail statement per world (dungeon_crawl, resource_dense_basin)
covering both the structural (ran without starvation) and empirical (real output diff) halves of
"no suppression," citing Step 4's real numbers.

### Step 6 — Write `staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md`
**Files:** `staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md` (new
file, `artifact_type: report`, mirroring both siblings' exact shape: frontmatter, environment note,
commands run verbatim, world-loading confirmation, the full evidence tally, an explicit
no-suppression pass/fail statement, an "Honest gap" section, a recommendation).
**Change:** Write the full raw record: the four commands from Steps 2-3 (verbatim, interpreter
path included), world-loading confirmation for both worlds (tick-0 `entity_count`/`state_hash`
fingerprint match against `corpus_registry.yaml`'s documented 32-entity `dungeon_crawl` and
23-entity `resource_dense_basin` scale, matching the combat-engagement sibling's own fingerprint
method rather than relying on CLI stdout alone), the full Step 4 tally (5 sub-signals x 4 legs),
Step 5's no-suppression pass/fail statement per world, and an honest disclosure of whatever the
real numbers show — including if OFF-baseline activity turns out thin for either world (do not
smooth over a weak result, per both siblings' own precedent). If the trial surfaces any real bug or
gap unrelated to this ticket's own scope, disclose it in this file's own "Honest gap" section and
stop there — do not fix it inline, do not file a follow-up ticket (the orchestrator decides that
separately), matching the SELF-MODEL-COGNITION sibling's own Honest Gap precedent exactly.
**Other writers to this file:** none — new file scoped to this ticket only; no other ticket or
concurrent session writes to this exact path.
**Do NOT touch:** `stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`
and `stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md` — the
siblings' own files, reference as format precedent only, never edit.
**Verify:** Re-read confirms the file's tally matches Step 4/5's real numbers exactly (not
placeholder/hypothetical), and `python3 tools/validate_frontmatter.py
staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md` passes.

### Step 7 — Add the `ENABLE_WORLD_CAPABILITY_LAYER` static-inertness regression guard
**Files:** New file `tests/architecture/test_world_capability_layer_flag_inert.py`.
**Change:** test_plan.md's "New Tests Required" section already specifies this test in full:
`test_enable_world_capability_layer_has_no_live_gating_call_site`, modeled directly on the sibling
`tests/architecture/test_adventure_routing_flag_inert.py` (read in full this session — confirmed
its exact structure: a module docstring explaining the inertness finding, a `_LIVE_GATING_PATTERNS`
tuple of the 6 quote-style variants of `is_enabled(...)`/`get_flag_mode(...)`/`feature_flag=...`,
an `_EXEMPT_PATH` pointing at `feature_flags.py`'s own registration line, and a single test function
that `rglob`s `src/**/*.py`, skips the exempt path, and asserts zero pattern matches). Build the new
file the same way, substituting `ENABLE_WORLD_CAPABILITY_LAYER` for `ENABLE_ADVENTURE_ROUTING`
throughout (6 patterns: `is_enabled("ENABLE_WORLD_CAPABILITY_LAYER")` /
`is_enabled('ENABLE_WORLD_CAPABILITY_LAYER')` / `get_flag_mode("ENABLE_WORLD_CAPABILITY_LAYER")` /
`get_flag_mode('ENABLE_WORLD_CAPABILITY_LAYER')` / `feature_flag="ENABLE_WORLD_CAPABILITY_LAYER"` /
`feature_flag='ENABLE_WORLD_CAPABILITY_LAYER'`), citing investigation.md's static finding (grep of
`src/ tools/ tests/ config/ docs/` returns exactly 4 hits — the flag's own registration at
`feature_flags.py:14` (confirmed by direct read this session:
`"ENABLE_WORLD_CAPABILITY_LAYER": FeatureMode.OFF,`), a test-scaffold `pressure_signals` dict entry
in `src/testing/scenario_runner.py:101` that maps to nothing since no phase names this flag in a
`run_phase(..., feature_flag=...)` call, `calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist (confirmed
by direct read this session: `"ENABLE_WORLD_CAPABILITY_LAYER"` at line 244) — a known-flag list,
not a gating site, and `tests/integration/test_scenario_feature_flag_defaults.py`'s own
default-OFF allowlist entry) and that no `WorldCapabilityLayer` class/module exists anywhere in
`src/` at all (zero grep matches, per investigation.md, not independently re-run this session since
it is a negative-existence claim already verified by the investigator).
**Other writers to `src/`:** none relevant — this is a read-only grep-based test; it does not
depend on or race with any other writer, since it only inspects committed `src/` files at test-run
time (same reasoning the sibling's own equivalent step used).
**Do NOT touch:** `src/testing/scenario_runner.py`, `src/domains/optimization/feature_flags.py`,
`docs/parity_ledger/*.yaml` — the static finding is already correct; this step only adds a
regression guard, it does not re-verify or re-write the existing citations. Do not schedule or
attempt any empirical `ENABLE_WORLD_CAPABILITY_LAYER` + `ENABLE_WORLD_EMERGENCE` combination trial —
per investigation.md's and test_plan.md's own Anti-Drift Hazards, a trial cannot produce a different
answer than "structurally impossible to interact" since no runtime path exists for
`ENABLE_WORLD_CAPABILITY_LAYER`'s value to reach any code at all.
**Verify:** `pytest tests/architecture/test_world_capability_layer_flag_inert.py -q` passes (new
test, 1 passed). Also confirm
`pytest tests/architecture/test_adventure_routing_flag_inert.py -q` still passes unmodified (the
sibling's own guard, unrelated to this flag, must not be touched or broken by adding the new file
alongside it).

### Step 8 — Write the real decision into `docs/architecture/rollout_flag_decisions_m1.md`
**Files:** `docs/architecture/rollout_flag_decisions_m1.md`
**Change:** This file's existing table row for `ENABLE_WORLD_EMERGENCE` (confirmed at line 31 of
the current file, read directly this session: `| \`ENABLE_WORLD_EMERGENCE\` | **Kept OFF,
deferred** | No production evidence. Follow-up:
\`TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION\`. |`) currently points at this ticket as an open
follow-up. Update that row's Verdict/Rationale cell in place to reflect the real outcome from Steps
4-6, and add a new `## ENABLE_WORLD_EMERGENCE — Validation Trial Result (TCK-20260826)` section
immediately after the existing `## ENABLE_SELF_MODEL_COGNITION — Validation Trial Result
(TCK-20260826)` section (confirmed this session to end at line 199, immediately before
`## RolloutProfileManager — Cut` at line 204) and before that `## RolloutProfileManager — Cut`
section — mirroring both existing sections' exact structure: worlds tested, commands run, evidence
tally, the no-suppression check result, an honest-gap disclosure (if any), and the recommendation.
Also fold in the `ENABLE_WORLD_CAPABILITY_LAYER` static-inertness finding (Step 7) as a subsection
or paragraph within this same new section, since this ticket's own Scope bundles both questions
(mirroring how the SELF-MODEL-COGNITION sibling bundled its own AC2 resolution into its section).
Per DEV-003's own stated standard (this file's own "## The Precedent This Sets" section, confirmed
present this session around line 217: flip ON requires "real, standing evidence the system already
runs safely in production... a live SimQ corpus profile already exercising it") and the fact that
zero shipped `config/simulation_quality/profiles/*.yaml` sets `ENABLE_WORLD_EMERGENCE` (confirmed
independently this session: `grep -rl "ENABLE_WORLD_EMERGENCE" config/simulation_quality/profiles/`
— cross-check this actually returns nothing before writing the row, do not merely cite
investigation.md's own prior claim unverified), the expected recommendation is **"Keep OFF,
deferred — real trial evidence now on file, but still no shipped production profile usage; re-open
only if a shipped profile begins using it."** This is the working conclusion Steps 4-6's real
evidence must confirm, not a foregone one: if Step 5's no-suppression check fails, or Step 4's
tally surfaces a genuine new defect, the recommendation must instead disclose that as a new finding
requiring a separate ticket (never fixed inline here), per Scope Guards.
Do not add a `DEV-00N` entry to `docs/guidelines/intentional_divergences.md` unless the
recommendation is "flip" — investigation.md's Docs Requiring Update section is explicit that a
"stay OFF" outcome requires no new divergence entry.
**Other writers to this shared file:** two sibling tickets already landed their own sections here
(`ENABLE_COMBAT_ENGAGEMENT` at lines 35-115, `ENABLE_SELF_MODEL_COGNITION` at lines 117-199, both
confirmed present by direct read this session) and investigation.md names two further sibling
tickets in the same batch (`TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`,
`TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`) that are each expected to add their own
row/section to this same file, potentially concurrently. This step touches **only** the
`ENABLE_WORLD_EMERGENCE` row (line 31) and appends **only** the new `ENABLE_WORLD_EMERGENCE`
section at the position specified above — a row-scoped/section-appended edit, not a full-file
rewrite, to avoid colliding with any sibling ticket's own concurrent edit to a different row/section.
If a `git` conflict arises against a concurrent sibling edit to this same file, resolve it by
keeping both sections (never drop another ticket's already-landed content).
**Do NOT touch:** Any other row in the 8-flag table, `## RolloutProfileManager — Cut`, `## The
Precedent This Sets`, or `## A Real Correction Made During Implementation` — historical records of
other tickets, not this one.
**Verify:** No automated test covers doc prose content; verification is a re-read confirming the
row and new section accurately reflect Steps 4-6's real numbers (not placeholder/hypothetical), and
`python3 tools/validate_frontmatter.py docs/architecture/rollout_flag_decisions_m1.md` still passes
since the file's own frontmatter block is untouched.

### Step 9 — Update this ticket's own Implementation Notes / Test Summary / Files Changed / Completion Summary
**Files:** `tickets/inprogress/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION.md`
**Change:** Fill in `## Implementation Notes` with a condensed version of Steps 4-8's findings and
Step 8's recommendation (link to the doc section rather than duplicate the full tally). Fill in
`## Test Summary` with the scoped pytest command results from test_plan.md's "Scoped Pytest
Commands" section (all four command blocks must be run and reported — see Step 10). Fill in `##
Files Changed` listing `docs/architecture/rollout_flag_decisions_m1.md`,
`tests/architecture/test_world_capability_layer_flag_inert.py` (new), plus this ticket file itself
and staging-artifact moves at Finalize — no other `src/` entries. Fill in `## Completion Summary`
stating the keep/flip outcome and the `ENABLE_WORLD_CAPABILITY_LAYER` combination-question
resolution.
**Other writers to this file:** none — this ticket file is scoped to this ticket only; no
concurrent session should be editing it.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets` —
already correct from ticket creation, not implementation output.
**Verify:** Re-read confirms every acceptance criterion checkbox in `## Acceptance Criteria` can be
checked off against what Steps 1-8 actually produced (see Acceptance Criteria Map below).

### Step 10 — Run the scoped regression suite from test_plan.md
**Files:** None changed. Test execution only.
**Change:** Run all four scoped pytest command blocks from
`staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/test_plan.md`'s "Scoped Pytest
Commands" section verbatim (using the `.venv/bin/python3` interpreter substitution from Step 2):
```
pytest tests/unit/domains/world_emergence/ tests/integration/domains/world_emergence/ \
  tests/integration/scenarios/test_phase8_world_emergence_scenarios.py \
  tests/integration/scenarios/test_resource_depletion.py \
  tests/perf/test_phase8_world_emergence_budget.py -m "not slow"

pytest tests/unit/quest/test_quest_generation.py tests/unit/quest/test_quest_lifecycle.py \
  tests/unit/world/test_sovereignty_events.py \
  tests/unit/observability/test_event_shapers_world_dynamics.py

pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/certification/test_phase10_enhanced_determinism_parity.py \
  tests/architecture/test_adventure_routing_flag_inert.py \
  tests/architecture/test_world_capability_layer_flag_inert.py

pytest tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off
```
This confirms the 14-file `world_emergence` unit/integration/perf surface, the 8 parity-cited
adjacent tests (`WORLD-098`/`099`/`101`/`104`/`106`/`107`/`115` plus `WORLD-102`'s
`test_quest_registry_wiring.py` inside the first command's own directory glob), the
`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist tests, and both architecture guards (the pre-existing
sibling one and Step 7's new one) all still pass unmodified. `ENABLE_WORLD_EMERGENCE` must remain
absent from the ON-default allowlist under the expected "keep OFF" outcome.
**Do NOT touch:** No test file is modified by this step except the new file created in Step 7. If
any test fails for a reason unrelated to `ENABLE_WORLD_EMERGENCE`/`ENABLE_WORLD_CAPABILITY_LAYER`
(e.g. a concurrent session's work), that is a signal to investigate separately, not something this
ticket absorbs, per test_plan.md's own Anti-Drift Test Guards.
**Verify:** All four pytest invocations pass (report actual pass/skip/deselect counts, matching or
exceeding test_plan.md's documented regression surface).

## Scope Guards
- Do not change `src/domains/optimization/feature_flags.py`'s `ENABLE_WORLD_EMERGENCE` default
  (`FeatureMode.OFF`, confirmed at line 57) or `ENABLE_WORLD_CAPABILITY_LAYER`'s default
  (`FeatureMode.OFF`, confirmed at line 14). **This is a hard constraint from the orchestrator,
  stated verbatim: NEVER flip `ENABLE_WORLD_EMERGENCE`'s or `ENABLE_WORLD_CAPABILITY_LAYER`'s
  actual default in `feature_flags.py` — recommendation only.**
- **If the trial run surfaces any REAL bug or gap unrelated to this ticket's own scope, do NOT fix
  it inline — disclose it in `trial_evidence.md`'s own "Honest gap" style section and stop there
  (matching the sibling SELF-MODEL-COGNITION ticket's own Honest Gap section pattern) — do not
  silently fix, do not file a follow-up ticket yourself (the orchestrator decides that
  separately).** Stated verbatim from the orchestrator's own hard constraint.
- Do not edit `src/domains/world_emergence/phase.py`, `src/engine/pipeline.py`'s `world_emergence`
  call site, or `src/engine/phase_graph.py`'s `PhaseDependencyGraph` metadata — this ticket
  re-validates existing behavior via corpus trial and static analysis, it never edits it.
- Do not remove or "fix" the vestigial `state.world_emergence_enabled`/
  `periodic_due_ticks["world_emergence_disabled"]` in-function gate inside `execute()`
  (`phase.py:34-39`) — investigation.md disclosed it as a latent footgun, explicitly out of this
  ticket's scope to touch (dead in production, exercised by exactly one test).
- Do not add `ENABLE_WORLD_EMERGENCE` to any `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copy
  (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) under any outcome of this
  ticket — that only happens in a future, separate flip ticket.
- Do not create or edit any `config/simulation_quality/profiles/*.yaml` file to turn either flag on
  by default — that would fabricate the "shipped production evidence" this ticket exists to
  honestly assess, not manufacture.
- Do not use `world_emergence_event` counts in `simulation_events.jsonl` as ON/OFF evidence anywhere
  in Steps 4-6 — confirmed to be produced by other systems entirely (`world_events_add`, set by
  `diplomatic_transitions`/`military_conflict`/faction-sovereignty phases, never by
  `WorldEmergencePhase.execute()`'s own `replace()` call) and unconditionally identical between
  legs.
- Do not run an empirical `ENABLE_WORLD_CAPABILITY_LAYER` combination trial — the static
  zero-live-gating-call-site finding (Step 7) already resolves the naming-proximity check the
  ticket's Scope asked for.
- Do not touch any `docs/parity_ledger/world_dynamics.yaml` entry (`WORLD-098/099/101/102/104/106/
  107/115`) unless Steps 4-6's real trial surfaces a genuine new defect in one of those specific
  mechanisms (not expected) — investigation.md's own judgment that none need updates from this
  evidence-gathering ticket is adopted here; if Step 5's no-suppression check or Step 4's tally
  contradicts that judgment with real evidence, update the relevant entry then, citing the real
  evidence, not speculatively.
- Do not touch `docs/engine/known_limitations.md` §1.5's pre-existing staleness (the
  `ENABLE_BELIEF_ASSIMILATION`/`ENABLE_SOCIAL_COOPERATION` flip-drift investigation.md flagged) —
  out of this ticket's scope, a pre-existing condition this ticket did not introduce.
- Do not silently reuse `data/calibration/`/`data/runs/` output from a different concurrent session
  — Steps 2-3's `--output`/`--name` paths already carry this ticket's own unique
  `world_emergence` tag, generating fresh output, never reading another session's.
- Leave `data/runs/*` and `data/calibration/*` trial output in place until the ticket's normal
  Finalize cleanup step (`rm -rf data/runs/* reports/release_proof/*` per Definition of Done) — do
  not clean up mid-ticket, since Steps 4-8 need to read that output.

## Dependency Map
- Step 1 (world/seed/tick decision) precedes everything else — Steps 2-3's commands are copied
  directly from Step 1's decision.
- Step 2 and Step 3 are independent of each other (different corpus worlds) and can run in either
  order or in parallel.
- Step 4 depends on both Step 2 and Step 3 completing (needs all 4 run legs' output).
- Step 5 depends on Step 4 (needs the real tally to run the no-suppression check against).
- Step 6 depends on Step 5 (the trial_evidence.md write-up needs both the tally and the
  no-suppression verdict).
- Step 7 is independent of Steps 1-6 (pure static analysis + a new self-contained test) — can run
  any time, including before Step 1.
- Step 8 depends on Step 6 (references the trial_evidence.md file it summarizes) and Step 7 (folds
  in the `ENABLE_WORLD_CAPABILITY_LAYER` finding) — write Step 8 after both, not in parallel, to
  avoid duplicating numbers that could drift out of sync between the two files.
- Step 9 depends on Step 8 (the ticket's Completion Summary references the doc section Step 8
  wrote).
- Step 10 is independent of Steps 1-9 (it exercises pre-existing tests plus Step 7's new file, not
  the trial's own output) but is listed last as the final gate before the ticket can be considered
  complete — it requires Step 7's new file to exist first (the third pytest command block names it
  directly), so it cannot run before Step 7 completes even though it does not depend on Steps 1-6.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A real corpus-profile ON trial is run and documented | Steps 1, 2, 3, 4, 5, 6, 8 | No pytest — verified by re-reading `trial_evidence.md` and the doc section Step 8 writes against Step 4/5's real numbers (not paraphrased/invented) |
| A keep/flip recommendation with evidence is produced | Step 8 | Same as above; recommendation must cite the shipped-profile-absence check (`grep -rl "ENABLE_WORLD_EMERGENCE" config/simulation_quality/profiles/` returning nothing) as its DEV-003 basis |

(The ticket's Scope also asks to "confirm no unexpected interaction with
`ENABLE_WORLD_CAPABILITY_LAYER`" — not phrased as its own checkbox AC, but tracked here for
completeness: resolved by Step 7's static regression guard, documented in Step 8's section.)

## Anti-Drift Notes
- **`world_emergence_event` counts in `simulation_events.jsonl` are disqualified as ON/OFF evidence
  for this flag** — they are produced by other pipeline phases via `world_events_add` and are
  unconditionally identical between legs; a trial design that used them anyway would produce a
  false "no suppression" result. Steps 4-6 must use `metric_counters`/`quest_registry`
  growth/`exposed_world_signals` instead.
- **This ticket's "no suppression" check has two distinct halves, unlike the `ENABLE_COMBAT_ENGAGEMENT`
  sibling's single-signature check**: (1) structural — the phase actually runs on ON ticks
  (`must_run_every_tick=True` should give ~0% skip-rate, ruling out phase-starvation), and (2)
  empirical — the phase's real output (quest registry growth, entity signal exposure) differs
  measurably between ON and OFF. Investigation.md already confirmed `WorldEmergencePhase.execute()`
  is structurally immune to the TCK-20260809 merge-suppression bug class (it calls
  `dataclasses.replace()` on the incoming `update`, not a fresh `StateUpdate()`) — Step 5 is the
  empirical confirmation of that static finding, not a re-litigation of it.
- **A near-zero OFF-leg baseline invalidates that world's data point, not just its ON leg** — per
  test_plan.md's Anti-Drift Test Guards, if either world's OFF run shows near-zero
  `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` activity, that is not evidence the flag is safe, it
  is evidence the trial world/seed/tick-count needs reconsideration — disclose it in Step 6's
  writeup rather than treat it as a clean pass.
- **The vestigial `world_emergence_enabled`/`periodic_due_ticks` in-function gate is a disclosed
  risk, not a defect to fix** — it is dead in production today (only one test sets it) but not this
  ticket's job to remove; do not let a trial finding tempt cleanup of it inline.
- **`resource_dense_basin` at 1000 ticks is a deliberate extension beyond its shipped 200-tick
  run_keys, not an error** — `tools/calibrate_simq.py --ticks` accepts any integer; this is a
  legitimate, already-supported invocation chosen specifically to reduce the near-zero-baseline
  risk a 200-tick window carries for `RESOURCE_DEPLETED` activity specifically.
- **Do not conflate this ticket with fixing or extending `WorldEmergencePhase` itself** — the
  ticket is purely evidence-gathering; any genuine new bug surfacing during the trial is disclosed
  in `trial_evidence.md`'s Honest Gap section and left there, per the orchestrator's hard
  constraint (Scope Guards above).
- **Interpreter substitution is expected, not a deviation to re-justify** — both prior sibling
  trials in this exact batch already hit and resolved the same `pydantic`-missing gap in the bare
  `python3`; Steps 2-3 and 10 specify the `.venv/bin/python3` substitution directly rather than
  discovering it fresh.

## Unresolved Questions
None. Investigation.md's own "Open question (not resolved by this investigation, Implement's job)"
— whether a single ON/OFF corpus trial is itself sufficient standing evidence to recommend a flip,
or whether "keep OFF, deferred, but now with a real trial on file" remains the honest recommendation
— is resolved by this plan using the same DEV-003 standard both already-closed siblings were
measured against (shipped, standing production profile usage, not a one-off trial). Since zero
shipped profiles turn `ENABLE_WORLD_EMERGENCE` on today (investigation.md's own full-file read,
to be re-confirmed live in Step 8), a one-off trial — however clean — cannot meet that bar by
itself; Step 8 states "Keep OFF, deferred" as the working conclusion, explicitly contingent on
Steps 4-5's real evidence not surfacing a suppression regression or other genuine new defect. This
mirrors both siblings' own resolution of the identical open question in their own investigations,
so it is not left open here as a blocking decision for the orchestrator.
