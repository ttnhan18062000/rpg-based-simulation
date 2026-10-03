---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION
artifact_type: plan
tags: [feature-flags, progression]
---

# Implementation Plan — TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION

## Summary
This ticket produces evidence, not code — same shape as its already-closed siblings
(`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`, `TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION`).
investigation.md already performed the Test Coverage Depth Assessment the ticket's Scope demands
("confirm real test depth before trusting a trial's result"); this plan's Step 1 formally carries
that verdict forward rather than redoing it. The plan then runs a real 4-leg (2 worlds x OFF/ON)
`tools/calibrate_simq.py` corpus trial (Steps 2-3), extracts evidence from `metric_counters` and
entity `property_updates` — never from `simulation_events.jsonl` `world_emergence_event`-style
proxies, since `ProgressionConversionPhase` writes no `WorldEvent`s of its own (Step 4), runs a
no-suppression check against that real tally (Step 5), writes the raw record to
`trial_evidence.md` (Step 6), writes the real decision into
`docs/architecture/rollout_flag_decisions_m1.md` (Step 7), updates the ticket's own body (Step 8),
and re-runs the scoped regression suite from test_plan.md (Step 9). No file under `src/` is
touched — this is an evidence-gathering chore ticket. Given investigation.md's single most
load-bearing finding (the reward ledger is never populated by any live producer in `src/`, so
`ConversionOptionGenerator` is structurally very likely to only ever emit the `SAVE_FOR_LATER`
fallback in a real run), the expected trial outcome is a near-zero-effect ON leg. Per
investigation.md's own explicit recommendation ("run the trial as-is first... explicitly flag the
ledger-producer gap as a named blocking prerequisite for any future flip-ON decision"), this plan
does **not** treat that near-zero result as a blocker or as grounds to skip the trial — it runs the
trial for real, honestly reports whatever the real numbers show, and the working recommendation is
**"Keep OFF, deferred — real trial evidence now on file; wiring is safe, but behavioral safety
under real reward flow remains untested because no live reward-ledger producer exists anywhere in
`src/`."** This is the working conclusion Steps 4-6's real data must confirm or overturn, not a
foregone one.

## Steps

### Step 1 — Carry forward the Test Coverage Depth Assessment verdict
**Files:** None changed (this step formally adopts investigation.md's own already-completed
assessment; it does not redo it, per the parent task's explicit instruction).
**Change:** investigation.md's "Test Coverage Depth Assessment" section (lines 270-350 of
`staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/investigation.md`, read in
full this session) already performed the honest split the ticket's first Acceptance Criterion
demands:
- **(a) Dormancy/gating-mechanics-only coverage** is thin: exactly 2 files reference the flag by
  name (`tests/integration/test_scenario_feature_flag_defaults.py`, a pure default-OFF allowlist
  assertion that never touches `ProgressionConversionPhase`; `tests/unit/observability/
  test_event_extractor_equipment.py`, whose only connection is a docstring comment, not a
  behavioral assertion). The one real-kernel-loop test in this family,
  `tests/integration/progression/test_allocate_ap_dormancy.py`, proves the `ALLOCATE_AP` branch
  does NOT fire while OFF (150 real ticks, `sandbox_world`) but never toggles the flag ON, so it
  cannot speak to ON-state behavior.
- **(b) Real domain-logic coverage** is deep: 10 dedicated `test_phase6_*.py` files (confirmed
  present via the file list in test_plan.md's "Regression Surface" section, read this session)
  exercise every constituent service individually plus 7 integrated scenarios, but every one of
  them calls `ProgressionConversionPhase.execute()` or its services directly, bypassing
  `src/engine/pipeline.py`'s `run_phase` flag gate entirely by construction — they would pass
  identically whether the flag is OFF or ON.
- **Verdict (adopted verbatim from investigation.md)**: deep enough to trust the phase's internal
  decision logic is correct in isolation, but **not** deep enough to trust a clean ON trial's
  "no observed risk" conclusion at face value — a clean/near-zero-effect trial result must be
  caveated as likely reflecting the reward-ledger producer gap (a structural wiring absence, not
  validated behavioral safety), not collapsed into a blanket "clean pass." This caveat must appear
  verbatim (not paraphrased away) in Step 6's `trial_evidence.md` and Step 7's doc section.
**Do NOT touch:** investigation.md itself — already complete and historical; this step only
formally references it, per the parent task's instruction not to redo the assessment.
**Verify:** No test — verification is that Step 6's `trial_evidence.md` and Step 7's doc section
both explicitly restate this verdict rather than silently omitting it (checked at Step 6/7's own
Verify).

### Step 2 — Run the `dungeon_crawl` primary trial (OFF then ON)
**Files:** None changed. Writes only to `data/calibration/` and `data/runs/{run_id}/` (temporary,
cleaned at Finalize per Definition of Done — do not clean mid-ticket; Steps 4-6 read this output).
**Change:** `dungeon_crawl` (`monster_only_gauntlet` archetype, 32 entities, confirmed by direct
read of `config/simulation_quality/corpus_registry.yaml:28-55` this session) is the same world the
`ENABLE_COMBAT_ENGAGEMENT` sibling trial used and, per investigation.md's own Candidate
World/Seed section, the best-fit archetype here: a monster-only combat gauntlet is the setting most
likely to grant entities XP/gold/loot (stressing `GrowthGapEvaluator`'s equipment/repair-gap
detection, which reads entity state directly and is *not* ledger-dependent) even though the reward
ledger itself has no live producer. It has a dedicated scoring profile
(`config/simulation_quality/profiles/dungeon_crawl.yaml`, confirmed present via `ls` this session),
so no `--profile default` override is needed. `dungeon_crawl_seed42_2000t` is a real shipped
run_key (confirmed present in `corpus_registry.yaml`'s `run_keys` list), matching the tick budget
the `COMBAT_ENGAGEMENT`/`WORLD_EMERGENCE` sibling trials both used, for direct comparability. Run,
using the interpreter substitution below:
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_progression_evolution_OFF

# ON
ENABLE_PROGRESSION_EVOLUTION=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_progression_evolution_ON
```
`ENABLE_PROGRESSION_EVOLUTION=ON` as an env-var prefix is a real, already-supported override —
confirmed by direct read of `tools/calibrate_simq.py:243-247` this session: `_KNOWN_FLAGS` includes
`"ENABLE_PROGRESSION_EVOLUTION"` explicitly. **Environment note (matching both siblings' own
already-recorded deviation, re-confirmed by direct check this session — bare `python3
-c "import pydantic"` fails in this worktree):** run every command in this plan with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` in place of the bare `python3`
shown, with `cwd` left as the worktree. Record the printed `run_id` for each invocation — Step 4
needs it to locate `data/runs/{run_id}/`'s `chunk_*.json` and any `simulation_events.jsonl`.
**Do NOT touch:** `src/domains/progression/phase.py`, `src/engine/pipeline.py`'s
`progression_conversion` call site, `src/domains/optimization/feature_flags.py` — this step only
runs existing tooling with an env-var override, per this ticket's Out of Scope.
**Verify:** Both commands exit 0 and produce `data/runs/{run_id}/` output (chunk snapshots and/or
`simulation_events.jsonl`, `quality_report.json`) for each leg (4 artifacts total). No separate
pytest assertion for this step, matching test_plan.md's framing ("the real corpus ON/OFF trial
itself... is the primary new evidence this ticket produces... not encoded as a new automated
test").

### Step 3 — Run the `frontier_extended` secondary trial (OFF then ON)
**Files:** Same as Step 2 (temporary `data/calibration/` and `data/runs/` output only).
**Change:** `frontier_extended` (`civilian_settlement` archetype, 59 entities, `quest_density`
0.4237, `resource_density` 1.2727 — confirmed by direct read of `corpus_registry.yaml:56-71` this
session) is the archetype-diversity secondary leg investigation.md's Candidate World/Seed section
recommended (a civilian-settlement world exercises quest-reward gold/item grants and
`GrowthGapEvaluator`'s `material_gap`/`gold_gap` checks that a monster-only gauntlet
under-represents). It has a dedicated scoring profile (`config/simulation_quality/profiles/
frontier_extended.yaml`, confirmed present via `ls` this session, unlike `crowded_frontier`, which
has no profile file — `frontier_extended` is chosen over `crowded_frontier` for this reason, both
being valid civilian-settlement candidates per investigation.md). Its only shipped run_keys are
`*_200t` (confirmed via `corpus_registry.yaml:65-68`, no `1000t`/`2000t` entries) — this plan
extends to 1000 ticks, the same deliberate extension-beyond-shipped-run_keys pattern the
`WORLD_EMERGENCE` sibling used for `resource_dense_basin`, to reduce near-zero-baseline risk a
200-tick window carries. `tools/calibrate_simq.py --ticks` accepts any integer (not restricted to
shipped run_keys), confirmed by the same code path the sibling plan verified.
```
# OFF (baseline)
python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 1000 \
  --output data/calibration/frontier_extended_seed42_1000t_progression_evolution_OFF

# ON
ENABLE_PROGRESSION_EVOLUTION=ON python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 1000 \
  --output data/calibration/frontier_extended_seed42_1000t_progression_evolution_ON
```
Same interpreter substitution as Step 2 applies. `--name frontier_extended` failing to resolve
would raise `FileNotFoundError` rather than silently falling back to a generic world (same
`_load_world_state()` behavior both sibling trials relied on as load-confirmation) — a successful
exit-0 run itself confirms the real compiled world spec loaded. Record the printed `run_id` for
both legs.
**Do NOT touch:** Same scope guard as Step 2.
**Verify:** Both commands exit 0 and produce the same artifact set (chunk snapshots/events/report x
OFF/ON) as Step 2.

### Step 4 — Extract evidence signals from `metric_counters` and entity `property_updates`
**Files:** None changed (analysis only; the durable record is written in Step 6).
**Change:** For each of the 4 run legs (dungeon_crawl OFF/ON, frontier_extended OFF/ON), capture,
per the parent task's explicit instruction (extract from `chunk_*.json` REFINED_UPDATE payloads
and `metric_counters`, **not** from `simulation_events.jsonl` alone):
1. **Run/skip counters** — `metric_counters["run_progression_conversion"]`/
   `["skip_progression_conversion"]`, summed across all ticks in each leg. `run_phase`
   (`src/engine/pipeline.py:102-127`, re-read this session) writes these unconditionally on every
   tick regardless of `PhaseDependencyGraph.should_run_phase()`'s own separate `phase_skips`
   counter, so a 100% `run_progression_conversion` rate on both ON legs (vs. 100%
   `skip_progression_conversion` on both OFF legs) is the structural half of "no suppression" —
   confirms the phase actually executes, not silently starved.
2. **Real mutation events** — any `item_equipped`/`item_unequipped`/`equipment_durability_changed`/
   `progression_conversion_applied` events in each leg's output. `progression_conversion_applied`
   is `EventExtractor`'s observability hook for `unspent_ap` decreasing between ticks
   (`docs/parity_ledger/progression.yaml::PROG-116`, cited by investigation.md), which per the
   investigation's finding is expected to be absent even ON, since the `ALLOCATE_AP` branch's only
   trigger (a ledger XP entry with the `"allocate"` tag) has no live producer.
   `item_equipped`/`item_unequipped`/`equipment_durability_changed` are the `EQUIP_ITEM`/`REPAIR`
   conversion-kind outputs — also structurally gated on `interpretation.meanings`, so also expected
   thin-to-absent on the ON legs per the reward-ledger finding, but must be checked for real rather
   than assumed absent.
3. **`last_progression_decision` sampling** — `ProgressionConversionPhase.execute()`
   (`src/domains/progression/phase.py:76-84`, re-read this session) writes a raw
   `ProgressionDecisionResult` (defined `src/domains/progression/schema.py:110`, confirmed present
   this session) into each entity's `property_updates["last_progression_decision"]` on every ON
   tick. **Other writers to `property_updates` on the same `EntityUpdate`:** `src/engine/
   evolution.py:146-147` and `src/engine/movement.py:290` both also write into `property_updates`,
   but via `EntityUpdate.merge()`'s dict-union semantics (`src/core/updates.py:716`,
   `{**self.property_updates, **other.property_updates}`, confirmed by direct read this session) —
   a later phase's same-key write in the same tick's chain would overwrite an earlier one, but no
   other phase in `src/` writes the `"last_progression_decision"` key specifically (grepped this
   session, only `phase.py:83` sets that literal key), so no collision on this key exists between
   `progression_conversion` and `evolution`/`movement`'s own (different-keyed) property writes.
   Sample a handful of entities' final `property_updates` (or the equivalent post-run state
   snapshot) across each ON leg and tally the distribution of `decision.kind` values — this is the
   single most direct way to confirm or refute investigation.md's "converges entirely on
   `SAVE_FOR_LATER`" prediction.
**Do NOT touch:** No source files — this step only reads generated JSONL/JSON/state-snapshot
artifacts from Steps 2-3.
**Verify:** A written tally (3 sub-signals x 4 legs) exists and explicitly states, per world, the
real values observed, including the real `last_progression_decision.kind` distribution sampled from
the ON legs. This tally is the direct evidence base for Step 5's no-suppression check and Step
6/7's writeups — both must cite these exact numbers, not a paraphrase.

### Step 5 — Run the no-suppression check against the real signal tally
**Files:** None changed (analysis only).
**Change:** Using Step 4's tally, assess whether any other domain's independent signal collapses
on the ON leg relative to OFF, in the same world (the empirical half of "no suppression," matching
both sibling trials' method): compare each ON leg's total non-progression event/metric activity
(combat, cooperation, contracts, XP, gold — whichever categories the run output actually contains)
against its own OFF leg. A collapse toward zero on the ON leg in any independent domain would
indicate `ProgressionConversionPhase.execute()`'s `replace(update, entity_updates=new_entity_updates)`
call (`phase.py:87-90`, re-read this session — replaces only `entity_updates`, carrying forward
every other field of the incoming `update` unchanged) is not behaving as expected in a real run,
contradicting the static code-reading. No collapse is expected given the code's own `replace()`
pattern already reads as safe (not a fresh `StateUpdate()` construction), but this step is the
empirical confirmation, not a re-litigation of the static read. Also record the structural half
from Step 4 signal 1 (100% run-rate on ON legs, 100% skip-rate on OFF legs) as part of this same
pass/fail statement.
**Do NOT touch:** No source files.
**Verify:** An explicit pass/fail statement per world (dungeon_crawl, frontier_extended) covering
both the structural (ran without starvation) and empirical (no other domain's signal collapsed)
halves of "no suppression," citing Step 4's real numbers.

### Step 6 — Write `staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md`
**Files:** `staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md`
(new file, `artifact_type: report`, mirroring `stored_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md`
and `stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`'s exact
shape and rigor — both read this session for format precedent).
**Change:** Write the full raw record: the four commands from Steps 2-3 (verbatim, interpreter path
included), world-loading confirmation for both worlds (tick-0 `entity_count` fingerprint match
against `corpus_registry.yaml`'s documented 32-entity `dungeon_crawl` and 59-entity
`frontier_extended` scale, matching the sibling trials' own fingerprint method rather than relying
on CLI stdout alone), the full Step 4 tally (3 sub-signals x 4 legs, including the real
`last_progression_decision` distribution sampled from both ON legs), Step 5's no-suppression
pass/fail statement per world, and — matching the parent task's explicit requirement — an **Honest
Gap** section carrying forward Step 1's verdict and investigation.md's reward-ledger finding
verbatim: state plainly that `RewardLedgerService` has zero live callers anywhere in `src/`, that
`ProgressionConversionPhase` never persists the ledger back into entity properties, and that any
near-zero/`SAVE_FOR_LATER`-converged result in this trial reflects that structural wiring gap, not
confirmed behavioral safety — "wiring is safe, behavioral safety under real reward flow remains
untested," never reported as a blanket clean pass. Close with a keep/flip recommendation.
**Other writers to this file:** none — new file scoped to this ticket only; no other ticket or
concurrent session writes to this exact path.
**Do NOT touch:** `stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/trial_evidence.md`
and `stored_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md` — reference as
format precedent only, never edit.
**Verify:** Re-read confirms the file's tally matches Step 4/5's real numbers exactly (not
placeholder/hypothetical) and that the Honest Gap section is present with real content (not a
generic caveat), and `python3 tools/validate_frontmatter.py
staging_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/trial_evidence.md` passes.

### Step 7 — Write the real decision into `docs/architecture/rollout_flag_decisions_m1.md`
**Files:** `docs/architecture/rollout_flag_decisions_m1.md`
**Change:** This file's existing table row for `ENABLE_PROGRESSION_EVOLUTION` (confirmed at line 32
of the current file, read directly this session: `| \`ENABLE_PROGRESSION_EVOLUTION\` | **Kept OFF,
deferred** | No production evidence; thinnest test coverage of the 5 deferred flags (2 files) — the
follow-up must assess coverage depth before trusting any trial. Follow-up:
\`TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION\`. |`) currently points at this ticket as an
open follow-up. Update that row's Verdict/Rationale cell in place to reflect the real outcome from
Steps 1-6, and add a new `## ENABLE_PROGRESSION_EVOLUTION — Validation Trial Result (TCK-20260826)`
section immediately after the existing `## ENABLE_WORLD_EMERGENCE — Validation Trial Result
(TCK-20260826)` section (confirmed this session to run lines 204-305, immediately before
`## RolloutProfileManager — Cut` at line 307) and before that `## RolloutProfileManager — Cut`
section — mirroring the 3 existing sibling sections' exact structure: worlds tested, commands run,
evidence tally, no-suppression check result, an Honest Gap disclosure, and the recommendation. This
section must state Step 1's coverage-depth verdict explicitly (deep domain-logic coverage, thin
pipeline-wiring coverage) and Step 6's reward-ledger Honest Gap verbatim, not paraphrased away.
Given zero shipped `config/simulation_quality/profiles/*.yaml` sets `ENABLE_PROGRESSION_EVOLUTION`
today (re-confirm live via `grep -rl "ENABLE_PROGRESSION_EVOLUTION" config/simulation_quality/profiles/`
before writing the row, per DEV-003's standing production-evidence bar both closed siblings were
measured against), the expected recommendation is **"Keep OFF, deferred — real trial evidence now
on file; wiring/perf/suppression confirmed safe, but the reward-ledger producer gap means
behavioral safety under real reward flow remains untested and is a named blocking prerequisite for
any future flip-ON decision."** This is the working conclusion Steps 4-6's real evidence must
confirm, not a foregone one: if Step 5's no-suppression check fails or Step 4's tally surfaces a
genuine new defect, the recommendation must instead disclose that as a new finding requiring a
separate ticket (never fixed inline here).
**Other writers to this shared file:** three sibling tickets already landed their own sections here
(`ENABLE_COMBAT_ENGAGEMENT` lines 35-115, `ENABLE_SELF_MODEL_COGNITION` lines 117-199,
`ENABLE_WORLD_EMERGENCE` lines 204-305, all confirmed present by direct read this session), and
investigation.md names a further sibling ticket in the same batch
(`TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`) expected to add its own row/section
to this same file, potentially concurrently. This step touches **only** the
`ENABLE_PROGRESSION_EVOLUTION` row (line 32) and appends **only** the new
`ENABLE_PROGRESSION_EVOLUTION` section at the position specified above — a row-scoped/
section-appended edit, not a full-file rewrite, to avoid colliding with any sibling ticket's own
concurrent edit to a different row/section. If a `git` conflict arises against a concurrent
sibling edit to this same file, resolve it by keeping both sections (never drop another ticket's
already-landed content).
**Do NOT touch:** Any other row in the 8-flag table, `## RolloutProfileManager — Cut`, `## The
Precedent This Sets`, or `## A Real Correction Made During Implementation` — historical records of
other tickets, not this one.
**Verify:** No automated test covers doc prose content; verification is a re-read confirming the
row and new section accurately reflect Steps 1-6's real findings (not placeholder/hypothetical),
and `python3 tools/validate_frontmatter.py docs/architecture/rollout_flag_decisions_m1.md` still
passes since the file's own frontmatter block is untouched.

### Step 8 — Update this ticket's own Implementation Notes / Test Summary / Files Changed / Completion Summary
**Files:** `tickets/inprogress/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION.md`
**Change:** Fill in `## Implementation Notes` with a condensed version of Steps 1-7's findings and
Step 7's recommendation (link to the doc section rather than duplicate the full tally). Fill in
`## Test Summary` with the scoped pytest command results from test_plan.md's "Scoped Pytest
Commands" section (both command blocks must be run and reported — see Step 9). Fill in `## Files
Changed` listing `docs/architecture/rollout_flag_decisions_m1.md` plus this ticket file itself and
staging-artifact moves at Finalize — no `src/` entries at all (unlike the `WORLD_EMERGENCE` sibling,
this ticket adds no new test file, per test_plan.md's "New Tests Required: None"). Fill in `##
Completion Summary` stating the keep/flip outcome and the reward-ledger Honest Gap finding as a
named prerequisite for any future flip.
**Other writers to this file:** none — this ticket file is scoped to this ticket only; no
concurrent session should be editing it.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets` —
already correct from ticket creation, not implementation output.
**Verify:** Re-read confirms every acceptance criterion checkbox in `## Acceptance Criteria` can be
checked off against what Steps 1-7 actually produced (see Acceptance Criteria Map below).

### Step 9 — Run the scoped regression suite from test_plan.md and clean up trial artifacts
**Files:** None changed. Test execution and cleanup only.
**Change:** Run both scoped pytest command blocks from `staging_artifacts/
TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION/test_plan.md`'s "Scoped Pytest Commands" section
verbatim (using the `.venv/bin/python3` interpreter substitution from Step 2):
```
pytest tests/unit/domains/progression/ tests/integration/domains/progression/ \
  tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py \
  tests/integration/progression/test_allocate_ap_dormancy.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/unit/entity/test_phase6_reward_ledger_component.py \
  tests/unit/observability/test_event_extractor_equipment.py \
  tests/unit/observability/test_event_extractor_progression.py \
  tests/unit/observability/test_event_shapers_progression.py \
  tests/unit/quest/test_progression_regression.py \
  tests/unit/config/test_phase10_feature_flags.py \
  -m "not slow"

pytest tests/perf/test_phase6_progression_conversion_budget.py
```
This confirms the full Phase-6 progression domain surface, the flag-defaults gating test, the
observability/event-shaper adjacent tests, the sibling PROG-068/069 dormant-path regression guard,
the feature-flag config sanity test, and the perf-budget test all still pass unmodified after the
trial's env-var overrides. `ENABLE_PROGRESSION_EVOLUTION` must remain absent from the
`_DELIBERATE_ON_DEFAULT_FLAGS`-style allowlists checked by
`test_scenario_feature_flag_defaults.py`/`test_phase10_feature_flags.py`. After both commands pass,
clean up trial artifacts per Definition of Done: `rm -rf data/runs/* reports/release_proof/*` and
remove the `data/calibration/*progression_evolution*` directories created in Steps 2-3 (do not
remove other sessions' unrelated `data/calibration/` output).
**Do NOT touch:** No test file is modified by this step (no new test file is added by this ticket,
unlike the `WORLD_EMERGENCE` sibling's Step 7). If any test fails for a reason unrelated to
`ENABLE_PROGRESSION_EVOLUTION` (e.g. a concurrent session's work), that is a signal to investigate
separately, not something this ticket absorbs, per test_plan.md's own Anti-Drift Test Guards.
**Verify:** Both pytest invocations pass (report actual pass/skip/deselect counts, matching or
exceeding test_plan.md's documented regression surface), and `git status` shows no leftover
`data/runs/` or `data/calibration/*progression_evolution*` files.

## Scope Guards
- Do not change `src/domains/optimization/feature_flags.py`'s `ENABLE_PROGRESSION_EVOLUTION`
  default (`FeatureMode.OFF`, confirmed at line 47) — recommendation only, per ticket Out of Scope
  ("Actually flipping the flag's default").
- **Do not wire a real `RewardLedgerService` producer into `quest_rewards`/`resource_transactions`/
  `evolution`** (or any other phase) to "make the trial show real activity." This is new production
  logic outside this ticket's evidence-gathering scope, and is exactly the shape of "quietly fixing
  an underlying gap to make a check/trial look clean" that the project's Gate Integrity rule warns
  against, generalized to a trial's evidentiary honesty. The empty-ledger finding must be reported
  honestly in Steps 6-7 as a limitation of the trial's evidentiary value, never papered over.
- **Do not hand-construct a `RewardLedgerComponent` with fake entries directly into the trial
  world's entity state before running `calibrate_simq.py`.** That would defeat the entire purpose of
  a *real* corpus trial (indistinguishable from the existing hand-seeded `test_phase6_
  progression_conversion_scenarios.py` unit-style tests). The trial must run against the corpus
  world's actual, organically-evolving state.
- Do not write any new pytest test file — test_plan.md's "New Tests Required" is explicitly "None,"
  per this ticket's Out of Scope ("Writing new test coverage beyond what's needed to trust the trial
  itself").
- Do not edit `src/domains/progression/phase.py`, its 6 constituent service files
  (`possession.py`/`gaps.py`/`interpretation.py`/`generator.py`/`selector.py`/`resolver.py`),
  `src/engine/pipeline.py`'s `progression_conversion` call site, or the vestigial
  `progression_conversion_enabled` in-function gate at `phase.py:35` — investigation.md disclosed
  the latter as a latent footgun, explicitly out of this ticket's scope to fix.
- Do not touch `docs/parity_ledger/progression.yaml` (including `PROG-116`, `PROG-068`, `PROG-069`)
  unless Steps 4-6's real trial surfaces a genuine new defect in one of those specific mechanisms
  (not expected) — investigation.md's own judgment that none need updates from this evidence-
  gathering ticket is adopted here.
- Do not touch `docs/guidelines/intentional_divergences.md`'s DEV-004 entry — it already correctly
  cites this ticket by ID as its own not-yet-run follow-up; a "keep OFF" outcome does not change
  that text (only a future flip-ON ticket would).
- Do not conflate this ticket's flag (`resolver.py`'s `ConversionKind.ALLOCATE_AP` branch, gated by
  `ENABLE_PROGRESSION_EVOLUTION`) with the sibling dormant `core_actions.py::execute_allocate_ap`
  branch (PROG-068/069, gated by nothing — simply never invoked). This trial does not and cannot
  exercise or fix PROG-068/069.
- Do not treat `test_scenario_feature_flag_defaults.py`'s passing default-OFF assertions as evidence
  about the phase's behavior when ON, per investigation.md's own Anti-Drift Hazards — must not be
  cited in Step 6/7's writeups as behavioral coverage.
- Do not use `simulation_events.jsonl` alone as the evidence source in Steps 4-5 — extract from
  `chunk_*.json` REFINED_UPDATE payloads and `metric_counters` per the parent task's explicit
  instruction.
- Do not silently reuse `data/calibration/`/`data/runs/` output from a different concurrent session —
  Steps 2-3's `--output`/`--name` paths carry this ticket's own unique `progression_evolution` tag.
- Leave `data/runs/*` and `data/calibration/*progression_evolution*` trial output in place until
  Step 9's cleanup — do not clean up mid-ticket, since Steps 4-8 need to read that output.

## Dependency Map
- Step 1 (coverage-verdict carry-forward) is independent of Steps 2-9 — can run any time; already
  complete as of investigation.md.
- Step 2 and Step 3 are independent of each other (different corpus worlds) and can run in either
  order or in parallel.
- Step 4 depends on both Step 2 and Step 3 completing (needs all 4 run legs' output).
- Step 5 depends on Step 4 (needs the real tally to run the no-suppression check against).
- Step 6 depends on Step 1 (states the coverage verdict), Step 4 (the tally), and Step 5 (the
  no-suppression verdict) — the trial_evidence.md write-up needs all three.
- Step 7 depends on Step 6 (references and summarizes the trial_evidence.md file it cites) — write
  Step 7 after Step 6 completes, not in parallel, to avoid the doc's numbers drifting out of sync
  with the staging artifact's numbers.
- Step 8 depends on Step 7 (the ticket's Completion Summary references the doc section Step 7
  wrote).
- Step 9 is independent of Steps 1-8's content (it exercises pre-existing tests, not the trial's own
  output) but is listed last as the final gate before the ticket can be considered complete, and its
  cleanup half must happen only after Steps 4-8 have finished reading the trial output.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Test coverage depth is assessed honestly before the trial, not assumed adequate | Step 1 (carrying forward investigation.md's own assessment) | No pytest — verified by re-reading Step 6/7's writeups for the verdict's presence, verbatim not paraphrased |
| A real corpus-profile ON trial is run and documented | Steps 2, 3, 4, 5, 6 | Steps 2-3: both OFF/ON commands exit 0 with real artifacts produced. Steps 4-6: no pytest — verified by re-reading `trial_evidence.md` against Step 4/5's real numbers |
| A keep/flip recommendation with evidence is produced | Steps 6, 7 | No pytest — verified by re-reading `trial_evidence.md` and the doc section Step 7 writes; recommendation must cite the shipped-profile-absence check and the reward-ledger Honest Gap as its basis |

## Anti-Drift Notes
- **The reward-ledger producer gap is the single most important finding this trial must not paper
  over.** `RewardLedgerService` has zero live callers anywhere in `src/`, and
  `ProgressionConversionPhase` never persists the ledger back into entity properties — so
  `ledger.entries` is always empty in a real pipeline run, `RewardInterpretationService.interpret`
  always produces `meanings=()`, `ConversionOptionGenerator.generate` only ever emits the
  `SAVE_FOR_LATER` fallback, and `ConversionIntentResolver.resolve` no-ops for that kind. A
  near-zero-effect ON trial result is the *expected*, evidentially-honest outcome given this
  structural gap — it must be reported as "wiring is safe, behavioral safety under real reward flow
  remains untested," never as a blanket "no observed risk, safe to flip."
- **This also independently affects DEV-004's `ALLOCATE_AP` divergence**: `ConversionOptionGenerator`
  only emits an `ALLOCATE_AP` option when a ledger XP entry with the `"allocate"` tag exists, which
  never happens live — so that branch is very likely unreachable even with the flag ON, for a reason
  independent of the flag gate itself. This is new information beyond what
  `test_allocate_ap_dormancy.py` (OFF-side only) already proved; disclose it in Step 6/7's writeups,
  do not silently drop it.
- **`ENABLE_PROGRESSION_EVOLUTION`'s vestigial internal gate** (`phase.py:35`,
  `getattr(state, "progression_conversion_enabled", True)`) is a dead no-op branch in every real
  pipeline run (the attribute is never set on `AuthoritativeState` anywhere in `src/`) — disclosed
  for reader awareness, not something this ticket fixes.
- **Do not let a near-zero/`SAVE_FOR_LATER`-converged trial result read as a coverage or trial-design
  failure** — per investigation.md's own recommendation, the trial is still real, informative
  evidence in its own right (proves no crash, no suppression, bounded perf under the existing
  perf-budget test), even though it cannot confirm decision-logic safety under real reward load.
- **Interpreter substitution is expected, not a deviation to re-justify** — both prior sibling trials
  in this batch already hit and resolved the same `pydantic`-missing gap in the bare `python3`;
  Steps 2-3 and 9 specify the `.venv/bin/python3` substitution directly rather than discovering it
  fresh.
- **`frontier_extended` at 1000 ticks is a deliberate extension beyond its shipped 200-tick
  run_keys, not an error** — matching the `WORLD_EMERGENCE` sibling's own `resource_dense_basin`
  precedent for the identical reason (reducing near-zero-baseline risk).
