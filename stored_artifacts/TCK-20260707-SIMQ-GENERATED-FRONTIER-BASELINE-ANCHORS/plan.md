---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
artifact_type: plan
tags: [simulation-quality, corpus, calibration, world]
---

# Implementation Plan — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS

## Summary
This is a data-only ticket: no scorer, hub, engine, or world-content source changes. The plan
establishes `generated_frontier_3_42`'s first-ever grade anchors via the existing
`calibrate_simq.py` → `grade_anchors.json` → `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` mechanism, at
two tiers: a 200t fast tier (reusing the already-existing 3-seed calibration data with a live
determinism spot-check, per Scope item 1's "confirm live, do not assume") and a 1000t slow tier
(a genuinely fresh engine run, since no long-run data exists for this world yet). It updates
`eval_matrix_results.md` to supersede the prior "deliberately no anchor" write-up, corrects the now-
stale `corpus_tier_taxonomy.md:131` line, adds first-time `v2_evidence` notes to `INFRA-240`/
`INFRA-241`, flags (without fixing) `INFRA-250`'s pre-existing anchor-count staleness, and runs the
scoped regression suite plus `make evaluate` (dry-run) as the final full-corpus gate.

**Seed-count decision (investigation.md Risk 3, resolved here per the ticket's own delegation):**
- **200t fast tier: anchor all 3 seeds (42, 123, 456).** The calibration data already exists on disk
  for all three (`data/calibration/generated_frontier_3_42_seed{42,123,456}_200t/`, produced one day
  before this ticket was opened, grades already independently verified stable across all three seeds
  in investigation.md). Reuse is nearly free — no fresh 200t engine run is needed for seeds 123/456 —
  and 3-seed-per-world is the dominant convention already established for this exact tier
  (`frontier_extended`, `frontier_living_world`, `wilderness_survival`, `highland_traverse`,
  `swamp_border_world`, `unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot` are
  all anchored at 3 seeds/200t in the current `FAST_ANCHOR_KEYS`). Anchoring only seed42 here would be
  a narrower, non-standard choice with no cost justification, since the coverage is already paid for.
  This differs from the LONGRUN-HOTPILLAR-ANCHORS sibling ticket's 1-seed rationale, which was driven
  by the recurring cost of *fresh* long-run engine runs compounding onto every future
  `evaluate-full` — that cost concern does not apply to reusing already-existing 200t data.
- **1000t slow tier: seed42 only, minimum required by AC item 3 ("at least one long-run anchor").**
  Unlike the 200t tier, no 1000t data exists yet for any seed — every additional seed here is a
  genuinely fresh, non-free 1000t kernel run that permanently inflates every future
  `evaluate-full` invocation (the same recurring-cost argument the LONGRUN-HOTPILLAR-ANCHORS sibling
  ticket made explicit). This ticket is establishing the world's *first* long-run data point, not
  running a multi-seed hypothesis-testing study — one seed is sufficient to satisfy the AC and give
  the corpus its first long-run signal for this world; a future ticket can add seeds 123/456 at this
  tier if a specific question later requires multi-seed confirmation, exactly as
  `SEQUENCE.md`'s per-ticket seed-count delegation anticipates. seed42 is chosen for direct
  comparability with the existing 200t seed42 anchor and because it is the corpus's universal primary
  seed.

## Steps

### Step 1 — Live-verify compile/run cleanliness and 200t determinism
**Files:** none produced (read-only + one scratch engine run); reads
`data/calibration/generated_frontier_3_42_seed42_200t/quality_report.json` (existing)
**Change:** Run `python3 tools/calibrate_simq.py --name generated_frontier_3_42 --seed 42 --ticks 200`
fresh. Confirm the run completes without exception and produces a non-trivial report (event_count > 0
for FACTION, INFORMATION, COGNITION, COMBAT, PROGRESSION, WORLD, NARRATIVE, per test_plan.md item 4).
Diff the freshly-generated `quality_report.json` against the existing
`data/calibration/generated_frontier_3_42_seed42_200t/quality_report.json` — grades and raw/normalized
scores must match exactly (the engine is deterministic by seed; a mismatch would itself be a genuine
finding to document, not paper over, per Scope item 1's framing). If they match, overwrite the on-disk
artifact with the fresh run (no functional difference, but keeps the artifact's `generated_at`
honest) and treat this as satisfying both Scope item 1 (live compile/run confirmation) and the
Anti-Drift Hazard's "spot-verify determinism" requirement for the existing seed123/seed456 artifacts
(same tooling, same world, same day of origin — the seed42 spot-check stands in for all three; no
separate seed123/seed456 rerun is needed given this outcome).
**Do NOT touch:** Do not modify `data/worlds/generated_frontier_3_42/world.yaml` or
`config/simulation_quality/profiles/generated_frontier_3_42.yaml` to "fix" anything observed here —
Out of Scope explicitly forbids content/catalog changes; if the run does not reproduce cleanly, stop
and document the blocker instead of proceeding to Step 2.
**Verify:** Fresh run's `quality_report.json` matches the existing one's grades exactly; no exception
raised. Maps to AC1.

### Step 2 — Add 200t fast-tier anchors (3 seeds)
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json` (3 new keys),
`tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`, 3 new entries after line 99)
**Change:** Add three keys to `grade_anchors.json`, each with the full 10-pillar grade dict read
directly from the corresponding `data/calibration/generated_frontier_3_42_seed{N}_200t/
quality_report.json` (already on disk; seed123/seed456 untouched by Step 1, reused as-is per that
step's determinism-spot-check reasoning):
- `"generated_frontier_3_42_seed42_200t"`: `{COGNITION: B, AGENCY: C, COMBAT: A, FACTION: S,
  ECONOMY: C, PROGRESSION: B, SOCIAL: C, INFORMATION: B, WORLD: B, NARRATIVE: A}`
- `"generated_frontier_3_42_seed123_200t"`: same 10-pillar shape, values from that seed's report
- `"generated_frontier_3_42_seed456_200t"`: same 10-pillar shape, values from that seed's report
(All three should read identically per investigation.md's already-verified 3-seed table — copy the
literal values from the calibration reports, do not hand-type from the investigation doc, in case of
transcription drift.) Append the same three keys to `FAST_ANCHOR_KEYS` with a
`# new — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` comment, matching the file's existing
per-batch comment convention.
**Do NOT touch:** Do not add these keys to `SLOW_ANCHOR_KEYS`. Do not reorder or remove any existing
`FAST_ANCHOR_KEYS` entries. Do not add a 500t entry — this world's fast tier is 200t per its own
existing data, matching corpus convention for this world.
**Verify:** `test_grade_anchor_file_exists_and_valid` passes (all 3 new entries have exactly 10 pillar
grades, all in `GRADE_ORDER`). `pytest tests/simulation_quality/test_grade_regression.py -v -k
generated_frontier_3_42` passes for all 3 new keys (not skipped — reports exist). Maps to AC2, AC4.
**Depends on:** Step 1 (determinism must be confirmed before trusting the reused seed123/seed456 data).

### Step 3 — Run fresh 1000t long-run calibration
**Files:** `data/calibration/generated_frontier_3_42_seed42_1000t/quality_report.json` (new,
generated; gitignored per `.gitignore:240` — this is a disk artifact, not a git-tracked file, matching
every other `data/calibration/` entry)
**Change:** Run `python3 tools/calibrate_simq.py --name generated_frontier_3_42 --seed 42 --ticks
1000`. Confirm it completes without exception and produces a non-trivial report (same event_count > 0
check as Step 1, for the pillars that were active at 200t). Record the resulting 10-pillar grade dict
for use in Steps 4 and 6. Per investigation.md's Mechanics/Engine Constraints, expect FACTION/
INFORMATION/COGNITION to possibly shift down from their 200t S/B/B values due to `effective_denom`
dilution (front-loaded one-shot events diluting as `floor_tick` grows) — this is architecturally
intentional, not a bug, and must not be "corrected" by re-running with different parameters to chase a
particular grade.
**Do NOT touch:** Do not exceed 1000 ticks (AC item 3 requires exactly this; do not scope-creep toward
the 2000t cap without a documented reason — none exists here). Do not run additional seeds at this
tier (see Summary's seed-count decision).
**Verify:** Run completes cleanly; `quality_report.json` has all 10 pillars with `event_count`
consistent with an active world at 1000t. Maps to AC1, AC3.

### Step 4 — Add 1000t slow-tier anchor
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json` (1 new key),
`tests/simulation_quality/test_grade_regression.py` (`SLOW_ANCHOR_KEYS`, 1 new entry after line 124)
**Change:** Add `"generated_frontier_3_42_seed42_1000t"` to `grade_anchors.json` with the full
10-pillar grade dict from Step 3's report. Append the same key to `SLOW_ANCHOR_KEYS` with a
`# new — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` comment.
**Do NOT touch:** Do not add this key to `FAST_ANCHOR_KEYS`. Do not add a 2000t entry — out of scope
per AC item 3's "1000t" wording and the Summary's seed/tier decision.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m slow -v -k
generated_frontier_3_42` passes (not skipped). Maps to AC3, AC4.
**Depends on:** Step 3.

### Step 5 — Population/entity-health cross-check at 1000t (ad hoc, non-gating)
**Files:** none committed (ad hoc verification only, not a new pytest test — mirrors
test_population_stability's mechanics but extended to 1000t)
**Change:** Using the same pattern as `tests/unit/worldassembly/test_corpus_diversity.py::
test_population_stability` (`WorldCompiler.compile` → `Kernel.tick_once()` loop, seed 42), drive
`generated_frontier_3_42` to 1000 ticks sampling `alive_count` at checkpoints (e.g. every 100-200
ticks) and compare against the same 60%-alive-of-starting floor used by the committed test. This world
is confirmed *not* in `KNOWN_POPULATION_COLLAPSE_WORLDS` (investigation.md, Current Behavior), so no
collapse is expected — but this ticket runs the engine past the previously-exercised 300t ceiling for
the first time, so the check is cheap, traceable due-diligence, not a response to a known defect. If
population holds at or above the floor throughout, note this briefly in Step 6's write-up. If it drops
below the floor at any checkpoint, this is a genuine new finding: still land the 1000t anchor (AC3
requires it), but document the population-erosion finding explicitly and honestly in Step 6's write-up
(mirroring the LONGRUN-HOTPILLAR-ANCHORS sibling ticket's `urban_political` precedent) — do not fix
the underlying cause in this ticket (Out of Scope: no content/catalog changes) and note it as a
candidate follow-up ticket if it occurs.
**Do NOT touch:** Do not modify `test_population_stability`'s 300-tick scope, its `world_id`
parametrization list, or `KNOWN_POPULATION_COLLAPSE_WORLDS` — any of those changes belongs to a
different ticket's scope (`TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`, already done, or a
new follow-up if collapse is found).
**Verify:** Ad hoc check result (holds / erodes) is stated plainly in Implementation Notes and in
Step 6's doc write-up. Maps to AC3 (documentation honesty), test_plan.md's Anti-Drift Test Guard on
`test_population_stability`.
**Depends on:** Step 3 (needs the same seed/world to be meaningful, though it re-drives the kernel
independently rather than reusing calibrate_simq.py's internal state).

### Step 6 — Document results in `eval_matrix_results.md`
**Files:** `docs/simulation_quality/eval_matrix_results.md` (supersede the existing
`generated_frontier_3_42` section at lines 740-761, append new section — do not delete the old text)
**Change:** Following the file's established "supersede, don't rewrite" convention (see lines 254,
280, 381, 599 for precedent), add a new dated section for `generated_frontier_3_42` that:
1. States plainly this section **supersedes** the prior "FACTION + INFORMATION, content-only, NO new
   anchor" section (retain that section's text below, marked superseded, for traceability — same
   pattern as `#### Historical pre-recompile table (superseded, retained for traceability)` at line
   280).
2. Presents the 3-seed 200t table (from Step 2's committed data) and the seed42 1000t table (from
   Step 3), each with the full 10-pillar grades, not just the FACTION/INFORMATION/COGNITION highlights.
3. States explicitly this is the world's first-ever calibration/anchor entry (per AC item 5's exact
   wording).
4. Explains any 200t→1000t grade shifts observed in Step 3, attributing them to `effective_denom`
   dilution (expected, per investigation.md's Mechanics/Engine Constraints) versus a genuine mechanism
   (`diplomacy_dormant`/`faction_monopoly`/`tension_oscillation` for FACTION,
   `belief_system_dormant` for COGNITION) versus a bug — do not default to "normalization" without
   checking the report's event/negative counts, mirroring the LONGRUN-HOTPILLAR-ANCHORS sibling
   ticket's write-up discipline.
5. States Step 5's population-health finding plainly (holds / erodes, with numbers).
6. States the seed-count decision from this plan's Summary (3 seeds @ 200t reused, 1 seed @ 1000t
   fresh) so a future reader understands why the tiers are asymmetric.
**Do NOT touch:** Do not delete or rewrite the existing lines 740-761 — mark superseded, keep as
historical record. Do not touch any other world's section in this file.
**Verify:** Manual review — section present, all 4 numbered items covered, old section retained and
marked superseded. Maps to AC5.
**Depends on:** Steps 2, 3, 4, 5 (needs all data + the population finding).

### Step 7 — Update stale `corpus_tier_taxonomy.md` line
**Files:** `docs/simulation_quality/corpus_tier_taxonomy.md` (line 131 only)
**Change:** Replace the `generated_frontier_3_42` row's Notes text — currently "procedurally
generated; FACTION + INFORMATION content authored but deliberately left outside the anchored
calibration corpus (no `grade_anchors.json` entries)" — with text reflecting the new anchored state,
e.g. "procedurally generated; FACTION + INFORMATION content authored; anchored at 200t (3 seeds) and
1000t (seed42) per TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS." Keep the entity/region
count prefix (`44 entities, 6 regions`) unchanged — only the anchor-status clause is stale.
**Do NOT touch:** Any other row in this table. Do not change the `Tier` column value
(`End-to-end`) — this ticket does not change the world's tier classification, only its anchor status.
**Verify:** Manual review — line 131 no longer claims the world is "deliberately left outside the
anchored calibration corpus." Maps to no single AC directly; closes investigation.md Risk 1
(non-blocking doc-staleness hazard flagged for same-session correction per repo doc-consistency rule).
**Depends on:** Step 4 (anchors must actually exist before the doc claims they do).

### Step 8 — Update parity ledger entries
**Files:** `docs/parity_ledger/infrastructure.yaml` (`INFRA-240`, `INFRA-241`, `INFRA-250` — text/
`v2_evidence` only, no `status` change)
**Change:**
- `INFRA-240` (CognitionScorer coverage): append a `v2_evidence` note citing this ticket's
  `generated_frontier_3_42_seed42_1000t` COGNITION data point (grade, raw_score, event_count, whether
  `belief_system_dormant` fired), following the same citation style as the existing
  `unit_selfmodel_pilot_seed42_1000t` note added by `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`.
- `INFRA-241` (FactionScorer coverage): append a `v2_evidence` note citing this ticket's
  `generated_frontier_3_42` FACTION data across 200t→1000t (grade trajectory, whether it matches the
  `effective_denom`-dilution pattern already documented for `unit_faction_tension`/`dungeon_crawl`, or
  reveals a genuine mechanism).
- `INFRA-250` (full SimQ test suite / anchor counts): the entry's "25 run keys... (14 fast, 11 slow)"
  text is already stale (actual count is ~70 before this ticket, ~74 after: +3 fast, +1 slow). Add a
  brief staleness flag to `v2_evidence` noting the count is out of date as of this ticket too (matching
  the sibling ticket's precedent of flagging rather than fixing) — do not rewrite the full count text,
  that is a separate correction ticket's scope.
Do not change any entry's `status` field — all remain `verified`; this ticket adds evidence, it does
not flip parity state.
**Do NOT touch:** `INFRA-252` (`evaluate_simq.py` full-mode description staleness) — investigation.md
flags it but it is explicitly the sibling ticket's already-logged, still-open staleness item, not new
to this ticket; do not duplicate-fix or duplicate-flag it here. Do not touch `INFRA-237`, `INFRA-255`,
`INFRA-262` — no new evidence from this ticket bears on them (AGENCY/SOCIAL/ECONOMY grades here are
archetype-baseline, not new findings; this ticket adds no profile/flag changes).
**Verify:** `docs/parity_ledger/infrastructure.yaml` remains valid YAML and (if a schema-validation
test exists under `tests/architecture/`) continues to pass it.
**Depends on:** Step 6 (needs the documented findings to write accurate `v2_evidence` text).

### Step 9 — Run scoped regression suite
**Files:** none (verification only)
**Change:** Run, in order:
```
.venv/bin/python3 -m pytest tests/simulation_quality/ -m "not slow" -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -m slow -v
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v -k generated_frontier_3_42
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v
.venv/bin/python3 -m pytest tests/integration/worldassembly/test_e2e_smoke.py -v -k generated_frontier_3_42
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v
.venv/bin/python3 -m pytest tests/unit/strategic/test_opportunities.py -v -k orc_stronghold
```
Confirm zero new failures, and specifically confirm: no drift on any *other* world's existing
fast/slow anchors, `test_population_stability[generated_frontier_3_42]` and
`test_hazard_kind_completeness[generated_frontier_3_42]` still pass (not newly `xfail`), the
feature-flag guardrail shows zero diff.
**Do NOT touch:** Do not run bare `pytest tests/` — stay within the files test_plan.md's Regression
Surface names.
**Verify:** All commands exit 0. Maps to all ACs indirectly (regression safety net) and to
test_plan.md's Anti-Drift Test Guards.
**Depends on:** Steps 2, 4 (keys must be committed first).

### Step 10 — Run `make evaluate` (dry-run, full-corpus gate)
**Files:** none (verification only)
**Change:** Run `make evaluate` (equivalent to `python3 tools/evaluate_simq.py --dry-run`, per
`Makefile:289-290`). Per investigation.md's `INFRA-252` finding, this iterates **every** non-metadata
key in `grade_anchors.json` regardless of `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` membership — this is a
genuine full-corpus check (all ~74 keys after this ticket), not scoped only to the 4 new entries.
Confirm 0 REGRESS results reported.
**Do NOT touch:** Do not run `make evaluate-full` — not required by this ticket's AC item 6 (which
names `--dry-run` explicitly) and would trigger a full engine re-run of the entire corpus, out of this
ticket's scope/cost budget.
**Verify:** `make evaluate` reports 0 regressions across the full corpus. Maps to AC6.
**Depends on:** Step 9 (fix anything the scoped suite catches first).

## Scope Guards
- Do not modify `src/simulation_quality/scorers/*.py`, `src/domains/adventure/*`, or
  `data/content/world/resources.yaml` — this ticket is calibration-data-only.
- Do not modify `data/worlds/generated_frontier_3_42/world.yaml` or
  `config/simulation_quality/profiles/generated_frontier_3_42.yaml` — no content/flag changes, per Out
  of Scope.
- Do not add any anchor beyond 1000t for this ticket (2000t is the epic-wide cap, not a target here —
  AC item 3 asks for 1000t specifically and this plan does not scope-creep toward the cap).
- Do not add `generated_frontier_3_42` to `ANCHORED_WORLD_BANDS` — different, unrelated mechanism.
- Do not touch `POPULATION_STABILITY_WORLDS` or `HAZARD_KIND_COMPLETENESS_WORLDS` membership — already
  contains this world from a prior, completed ticket.
- Do not fix `INFRA-250`'s or `INFRA-252`'s pre-existing staleness beyond the narrow flag added in
  Step 8 — full correction is a separate ticket's scope.
- Do not delete or rewrite any existing content in `eval_matrix_results.md` or
  `corpus_tier_taxonomy.md` beyond the specific superseded-marking (Step 6) and single-line correction
  (Step 7) described above.
- If Step 5's population check reveals a collapse, do not attempt to fix the underlying world-content
  or engine cause in this ticket — document only, per Out of Scope.

## Dependency Map
```
Step 1 (200t live-verify + determinism spot-check) ──> Step 2 (200t fast anchors, 3 seeds)

Step 3 (fresh 1000t run) ──> Step 4 (1000t slow anchor)
                          └─> Step 5 (population cross-check, non-gating)

Steps 2, 3, 4, 5 ──> Step 6 (eval_matrix_results.md write-up)
Step 4 ──> Step 7 (corpus_tier_taxonomy.md correction)
Step 6 ──> Step 8 (parity ledger v2_evidence updates)

Steps 2, 4 ──> Step 9 (scoped regression suite) ──> Step 10 (make evaluate)
```
Steps 1→2 and 3→{4,5} are two independent tracks (fast tier vs. slow tier) that can run in either
order relative to each other; both must complete before Step 6.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: compile/run confirmed cleanly (or blocker documented) | Steps 1, 3 | Fresh-run exception-free + grade match to existing artifact |
| AC2: at least one 200t anchor added, matching corpus convention | Step 2 | `pytest tests/simulation_quality/test_grade_regression.py -v -k generated_frontier_3_42` |
| AC3: at least one long-run anchor (1000t), not exceeding 2000t | Steps 3, 4, 5 | `pytest tests/simulation_quality/test_grade_regression.py -m slow -v -k generated_frontier_3_42` |
| AC4: anchors added via data-only mechanism (artifact + `grade_anchors.json` + key-list) | Steps 2, 4 | `test_grade_anchor_file_exists_and_valid` |
| AC5: `eval_matrix_results.md` documents first-ever calibration entry | Step 6 | Manual review |
| AC6: `make evaluate --dry-run` confirms 0 regressions | Step 10 | `make evaluate` exit status / report |

## Anti-Drift Notes
- `data/calibration/` is fully `.gitignore`d (`.gitignore:240`) and none of the ~70 pre-existing
  calibration directories are git-tracked (`git ls-files data/calibration/` returns zero results,
  confirmed live) — "commit the artifact" in this plan and in `tools/calibrate_simq.py`'s own docstring
  means "write the report to disk at the conventional path," not `git add`. The actual git-tracked
  evidence for each anchor is the `grade_anchors.json` entry plus the `FAST_ANCHOR_KEYS`/
  `SLOW_ANCHOR_KEYS` string. Do not expect `data/calibration/generated_frontier_3_42_*` to appear in
  `git status` after this ticket lands — that is expected, not a gap.
- `effective_denom` growth (`floor_tick = max(1, current_tick // 4)`,
  `effective_denom = max(floor_tick, last_event_tick)`, `docs/simulation_quality/
  quality_scoring_contract.md` §4.4) is architecturally intentional — if FACTION/INFORMATION/COGNITION
  shift down between the 200t and 1000t anchors, attribute it to this mechanism (if the event/negative
  counts support that reading) rather than treating it as a bug, mirroring the already-documented
  `dungeon_crawl` FACTION S→A→B trajectory.
- This world has **no known population-collapse defect** (confirmed absent from
  `KNOWN_POPULATION_COLLAPSE_WORLDS`) — unlike the LONGRUN-HOTPILLAR-ANCHORS sibling ticket's
  `urban_political` confound, Step 5's population check here is due diligence, not a response to a
  known issue. If it does surface a new collapse, that is itself the significant finding — document it
  prominently, do not bury it as a footnote.
- The `orc_stronghold` resource-tag gap and the `POPULATION_STABILITY_WORLDS`/
  `HAZARD_KIND_COMPLETENESS_WORLDS` membership work are both already-closed prerequisites from prior
  tickets — do not re-investigate or re-fix either; Step 9's inclusion of
  `test_resource_opportunities_orc_stronghold_tag_gap` and the corpus-diversity tests is a regression
  check only.
- Cross-check the final `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` additions (3 + 1 = 4 new keys total)
  against this plan before considering the ticket done — a silent extra or missing key passes silently
  (via `pytest.skip`, not a failure) per test_plan.md's Anti-Drift Test Guard, so a manual list diff is
  the only way to catch a miscount.

## Questions Resolved During Planning
**Seed-count grid (investigation.md Risk 3).** Resolved in this plan's Summary: 3 seeds (42, 123, 456)
at 200t (data already exists, reuse is free, matches the dominant corpus convention for this tier);
1 seed (42) at 1000t (no existing data, every seed is a genuinely fresh non-free run whose cost
compounds onto every future `evaluate-full`, and the AC only requires "at least one"). This is a
reuse-vs-freshness cost/coverage tradeoff, not a genuine confound question — no human escalation
needed, consistent with the ticket's own framing of this decision as delegated to the Plan phase.

## Deviations
**Step 9 — unplanned but necessary fix to `tests/unit/worldassembly/test_corpus_diversity.py`.**
Running the plan's own Step 9 command
(`pytest tests/unit/worldassembly/test_corpus_diversity.py -v`, listed explicitly to "confirm no
cross-world regression from touching shared fixtures") surfaced a genuine failure in
`test_module_family_anchored`: that test's `_anchored_world_ids()` helper derives "anchored" status
directly from `grade_anchors.json` key membership, and `moon_cult_ruins` is the sole module composed
by `generated_frontier_3_42`. The prior ticket that introduced the test
(`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`) hard-coded
`STILL_UNANCHORED_MODULE = "moon_cult_ruins"` with an assertion that it must *never* become anchored —
an assumption this ticket's entire purpose (anchoring `generated_frontier_3_42` for the first time)
necessarily breaks. The test's own failure message states this outcome should be handled by updating
the exclusion list, not by reverting the anchoring work.

This plan did not anticipate this specific test (it is not named in any step's "Files" or
"Do NOT touch" list), but fixing it is squarely within the plan's Step 9 intent (verify no regression
after the fixture change) and does not touch anything the Scope Guards protect (`ANCHORED_WORLD_BANDS`,
`POPULATION_STABILITY_WORLDS`, `HAZARD_KIND_COMPLETENESS_WORLDS` membership were all left untouched).
Fix applied: moved `moon_cult_ruins` from the removed `STILL_UNANCHORED_MODULE` constant into
`NEWLY_ANCHORED_MODULES`, and deleted the now-inapplicable assertion. Verified via direct query
against `grade_anchors.json` + every world's `world.yaml` that zero modules remain unanchored
corpus-wide after this change — this was the last one. Full suite re-run: 48 passed, 2 xfailed
(pre-existing, unrelated `dungeon_crawl`/`urban_political` collapses).

No other deviations from the plan's 10 steps.
