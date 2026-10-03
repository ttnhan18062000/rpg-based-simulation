---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS
artifact_type: plan
tags: [simulation-quality, corpus, calibration, agency, faction, cognition, stasis]
---

# Implementation Plan — TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS

## Summary
This is a data-only ticket: no scorer, hub, engine, or test-infrastructure code changes. The plan
generates six new long-run calibration anchors (1000t/2000t) via the existing
`calibrate_simq.py` → `grade_anchors.json` → `SLOW_ANCHOR_KEYS` mechanism, live-verifies whether
`unit_faction_tension` needs a dedicated profile YAML before anchoring it, documents the four
named hypotheses (AGENCY hold/decay, FACTION decay, COGNITION long-run, SOCIAL persistence)
honestly in `eval_matrix_results.md`, updates five affected parity-ledger entries, and runs the
full regression + evaluate-harness gate. **Seed-count decision (Scope item 2):** this plan uses
**1 seed (seed42) per world/tier combination**, not the existing 3-seed convention used by
`dungeon_crawl`/`urban_political`'s prior anchors — rationale stated explicitly below and required
by the investigation's "do not silently under-sample" anti-drift hazard. The population-collapse
confound flagged in investigation.md Risk 1 for `urban_political_seed42_2000t` was escalated to a
human reviewer, who decided (2026-07-08): **proceed with the anchor, and document the confound
explicitly** alongside the SOCIAL grade (option a) — Step 9's population cross-check is therefore
mandatory, not conditional.

**Seed-count rationale (required disclosure per anti-drift hazard):** This ticket is evidence-gathering
for four specific hypotheses, not a production regression-guard corpus expansion — Scope item 5
explicitly defers any genuine bug found to a follow-up ticket rather than fixing it here, so a single
well-chosen seed is sufficient to answer each hypothesis's "hold / decay / reveal a bug" question and
trigger further investigation if the result is surprising. This matters more than usual because
`evaluate_simq.py`'s full mode re-runs the **entire** anchor corpus, not just new keys (investigation.md,
Current Behavior) — every additional seed compounds onto every future `make evaluate-full` run
indefinitely, not just this ticket's one-time cost. 3 seeds × 6 combinations (18 new 1000–2000-tick
kernel runs) would materially and permanently inflate that recurring cost for marginal evidentiary gain
at the hypothesis-testing stage. seed42 is chosen as the primary seed because it is already the first
seed used across all six worlds' existing fast anchors and all three existing `SLOW_ANCHOR_KEYS`
worlds, keeping this ticket's data directly comparable to existing evidence. If any hypothesis's
single-seed result is ambiguous or surprising, Scope item 5's follow-up-ticket path is the correct
place to add more seeds targeted at that specific pillar — not this ticket.

## Steps

### Step 1 — Confirm prerequisite tickets landed
**Files:** none (verification only; read `tickets/done/` directory listing)
**Change:** Confirm all 4 prerequisite tickets are present in `tickets/done/`:
`TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP`,
`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`,
`TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`,
`TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`. Investigation.md's Prior Work section
already confirms all 4 are present as of the investigation date — this step is a final
re-verification immediately before any calibration run touching `hero_guild_routing` or
`urban_political`, not a fresh investigation.
**Do NOT touch:** Do not open or modify any of these 4 tickets' content — read-only confirmation.
**Verify:** `ls tickets/done/ | grep -E "HERO-GUILD-ROUTING-RESOURCE-TAG-GAP|URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP|CORPUS-RESOURCE-REGION-COVERAGE-AUDIT|CORPUS-POPULATION-STABILITY-COVERAGE-GAP"` returns all 4. Maps to AC1.

### Step 2 — Live-verify `unit_faction_tension` profile need
**Files:** none produced yet except a scratch calibration run (see below); reads
`config/simulation_quality/profiles/` (confirm no `unit_faction_tension.yaml` exists),
`data/worlds/unit_faction_tension/world.yaml`
**Change:** Run `python3 tools/calibrate_simq.py --name unit_faction_tension --seed 42 --ticks 1000`
using the current `default.yaml` fallback (do not create a profile first). Inspect the resulting
`quality_report.json`'s FACTION section: confirm the run completes without engine error, produces a
non-degenerate FACTION score (i.e., not silently 0 from a missing-flag starvation pattern), and that
the S-grade-at-200t behavior is either sustained or shows an interpretable trend (not a cliff to C
that would suggest the 200t result was a `default.yaml` artifact rather than genuine
`faction_tension_overrides` seeding). Record the explicit outcome ("default.yaml confirmed
sufficient — no profile created" or "default.yaml insufficient — profile required, see Step 2b") in
Implementation Notes. This is Scope item 3's live verification; it gates Steps 6–7 below.
**Step 2b (conditional, only if Step 2 finds default.yaml insufficient):** Create
`config/simulation_quality/profiles/unit_faction_tension.yaml` with the minimum flags needed to
restore non-degenerate behavior, and update `tests/simulation_quality/fixtures/
expected_world_flag_state.json` (`INFRA-262` guardrail fixture) in the same change to reflect the
new profile's flag state — per test_plan.md's anti-drift guard, a red `test_world_profile_feature_
flag_guardrail.py` after this ticket would mean a forgotten fixture update.
**Do NOT touch:** Do not create the profile speculatively "just in case" — only if Step 2's live run
actually demonstrates `default.yaml` is insufficient (per the ticket's explicit Out-of-Scope line and
Anti-Drift Hazard). Do not modify `default.yaml` itself.
**Verify:** `tests/integration/test_world_profile_feature_flag_guardrail.py` stays green either way.
Maps to AC4.

### Step 3 — Add `unit_selfmodel_pilot_seed42_1000t` anchor (COGNITION hypothesis)
**Files:** `data/calibration/unit_selfmodel_pilot_seed42_1000t/quality_report.json` (new, generated),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Change:** Run `python3 tools/calibrate_simq.py --name unit_selfmodel_pilot --seed 42 --ticks 1000`.
Commit the generated `quality_report.json` under `data/calibration/unit_selfmodel_pilot_seed42_1000t/`.
Add a `"unit_selfmodel_pilot_seed42_1000t"` key to `grade_anchors.json` with the resulting 10-pillar
grade dict (same shape as existing entries, e.g. `dungeon_crawl_seed42_1000t`). Record the observed
COGNITION grade for later write-up (tests whether the 200t COGNITION=S peak holds, decays via
`belief_system_dormant`/`goal_lock_no_cognition`, or reveals a bug — mechanics laws documented in
investigation.md, §5 COGNITION).
**Do NOT touch:** Do not modify `config/simulation_quality/profiles/unit_selfmodel_pilot.yaml`. Do
not add a 2000t anchor for this world — out of scope (only 1000t requested for this world per Scope
item 2).
**Verify:** `grade_anchors.json` validates against `test_grade_anchor_file_exists_and_valid` (10
pillar grades, all in `GRADE_ORDER`). Maps to AC2.

### Step 4 — Add `hero_guild_routing_seed42_1000t` anchor (AGENCY/NARRATIVE hypothesis)
**Files:** `data/calibration/hero_guild_routing_seed42_1000t/quality_report.json` (new),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Change:** Run `python3 tools/calibrate_simq.py --name hero_guild_routing --seed 42 --ticks 1000`.
Commit the artifact and add the `"hero_guild_routing_seed42_1000t"` key to `grade_anchors.json`.
Record the observed AGENCY and NARRATIVE grades (tests whether the 500t AGENCY=A / NARRATIVE=S peak
holds, decays via `stasis_N`/`population_stasis` (investigation.md §5 AGENCY & ACTION), or reveals a
bug).
**Do NOT touch:** Do not modify `config/simulation_quality/profiles/hero_guild_routing.yaml`
(`ENABLE_ADVENTURE_ROUTING: "ON"` stays as-is). Do not re-touch the resource-tag content fixed by
the prerequisite ticket `TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP`.
**Verify:** Same structural validation as Step 3. Maps to AC2.

### Step 5 — Add `simq_routing_test_seed42_1000t` anchor (AGENCY/NARRATIVE hypothesis)
**Files:** `data/calibration/simq_routing_test_seed42_1000t/quality_report.json` (new),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Change:** Run `python3 tools/calibrate_simq.py --name simq_routing_test --seed 42 --ticks 1000`.
Commit the artifact and add the `"simq_routing_test_seed42_1000t"` key. Record observed AGENCY and
NARRATIVE grades (same hypothesis as Step 4, second data point).
**Do NOT touch:** Do not modify `config/simulation_quality/profiles/simq_routing_test.yaml`.
**Verify:** Same structural validation as Step 3. Maps to AC2.

### Step 6 — Add `unit_faction_tension_seed42_1000t` anchor (FACTION hypothesis)
**Files:** `data/calibration/unit_faction_tension_seed42_1000t/quality_report.json` (new),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Change:** Using whichever profile state Step 2 confirmed (default.yaml, or the new profile from
Step 2b), run `python3 tools/calibrate_simq.py --name unit_faction_tension --seed 42 --ticks 1000`
(this may reuse the Step 2 run's output directly if Step 2 already ran at exactly this seed/tick
count — do not re-run redundantly). Commit the artifact and add the
`"unit_faction_tension_seed42_1000t"` key. Record the observed FACTION grade against the 200t S
baseline (tests whether decay is `effective_denom` dilution, a genuine mechanism —
`diplomacy_dormant`/`faction_monopoly`/`tension_oscillation` — or a bug; investigation.md §5 FACTION
& MILITARY).
**Do NOT touch:** Do not create the profile YAML unless Step 2 already determined it necessary.
**Verify:** Same structural validation as Step 3. Maps to AC2.
**Depends on:** Step 2 (profile decision must be settled first).

### Step 7 — Add `unit_faction_tension_seed42_2000t` anchor (FACTION decay hypothesis)
**Files:** `data/calibration/unit_faction_tension_seed42_2000t/quality_report.json` (new),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Change:** Run `python3 tools/calibrate_simq.py --name unit_faction_tension --seed 42 --ticks 2000`
using the same profile state as Step 6. Commit the artifact and add the
`"unit_faction_tension_seed42_2000t"` key. Compare the 1000t (Step 6) and 2000t FACTION grades
directly against the `dungeon_crawl` A→B (1000t→2000t) precedent already committed in
`grade_anchors.json` — this is the second data point the FACTION hypothesis needs (investigation.md
Request Summary / §4.4 `effective_denom`).
**Do NOT touch:** Do not exceed 2000t (hard cap, out of scope).
**Verify:** Same structural validation as Step 3. Maps to AC2.
**Depends on:** Step 6 (needs the 1000t data point to characterize the trend, and reuses its profile
decision).

### Step 8 — Add `urban_political_seed42_2000t` anchor (SOCIAL persistence hypothesis)
**Files:** `data/calibration/urban_political_seed42_2000t/quality_report.json` (new),
`tests/simulation_quality/fixtures/grade_anchors.json` (new key)
**Status:** Approved for implementation. The population-collapse confound (investigation.md Risk 1)
was escalated to a human reviewer, who decided (2026-07-08): **proceed and document the confound**
(option a) — the known, separately-tracked `urban_political` population-collapse defect
(`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`, OPEN) does not block this anchor, but the SOCIAL
grade must not be read in isolation from it.
**Change:** Run `python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks 2000`.
Commit the artifact, add the `"urban_political_seed42_2000t"` key. Proceed immediately to Step 9's
(now-mandatory) population cross-check before treating the SOCIAL grade as interpretable in Step 11's
write-up.
**Do NOT touch:** Do not attribute any observed SOCIAL decay to normalization or to a "genuine drift
bug" without first ruling out population erosion via Step 9 (per investigation.md Risk 1 and
Anti-Drift Hazards).
**Verify:** Same structural validation as Step 3. Maps to AC2.

### Step 9 — Population-erosion cross-check for `urban_political` (mandatory)
**Files:** none (analysis only, feeds Step 11's write-up); reads the Step 8 calibration run's
underlying `data/runs/{run_id}/` telemetry or `simulation_events.jsonl` for entity-alive counts
**Change:** Extract the entity-alive percentage at whatever tick(s) telemetry supports (at minimum the
final 2000t tick, ideally also ~300t/1000t checkpoints if available) from the same calibration run
used for the SOCIAL grade. Compare against `test_population_stability`'s 60%-alive floor. This is not
a new committed pytest test — it is the test_plan.md-mandated ad hoc check that must be stated
explicitly in the write-up so the SOCIAL grade is not read in isolation from the known
population-collapse confound.
**Do NOT touch:** Do not modify `tests/unit/worldassembly/test_corpus_diversity.py` or its `xfail`
marker — that belongs to `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`, not this ticket.
**Verify:** `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[urban_political]`
remains `xfail` (not newly passing, not newly failing differently). Maps to AC3 (documentation
honesty).
**Depends on:** Step 8.

### Step 10 — Add all new keys to `SLOW_ANCHOR_KEYS`
**Files:** `tests/simulation_quality/test_grade_regression.py` (single edit, after line 117, before
the closing `]` of `SLOW_ANCHOR_KEYS` at line 118)
**Change:** Append all six keys produced by Steps 3–8, each on its own
line with a `# new — TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` comment matching the file's
existing per-batch comment convention (see existing `# new — dungeon_crawl 1000t` etc. comments at
lines 105, 108, 112, 116): `unit_selfmodel_pilot_seed42_1000t`,
`hero_guild_routing_seed42_1000t`, `simq_routing_test_seed42_1000t`,
`unit_faction_tension_seed42_1000t`, `unit_faction_tension_seed42_2000t`,
`urban_political_seed42_2000t`.
**Do NOT touch:** Do not add any key to `FAST_ANCHOR_KEYS` (line 41) — all six of these keys are
1000t/2000t and belong exclusively in `SLOW_ANCHOR_KEYS`. Do not reorder or remove any of the 11
existing `SLOW_ANCHOR_KEYS` entries. Do not add more or fewer keys than what Steps 3–8 actually
produced — cross-check the final list length against this plan before considering the ticket done
(test_plan.md Anti-Drift Test Guard).
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m slow -v` — every key in the
updated list either has a matching `grade_anchors.json` entry + calibration report (asserts within
±1 band) or is correctly skipped if intentionally absent. Maps to AC2.
**Depends on:** Steps 3–8 (all six run).

### Step 11 — Document hypotheses in `eval_matrix_results.md`
**Files:** `docs/simulation_quality/eval_matrix_results.md` (append new section, do not rewrite
existing content)
**Change:** Append a new dated section following the file's established per-world table convention
(`| Pillar | seed42 | Stable? | Note |` — adapted for single-seed since this ticket uses 1 seed, not
3; state that explicitly in the section header, e.g. "single-seed (seed42) evidence — see plan.md
seed-count rationale"). Cover all four hypotheses honestly:
1. **AGENCY** (`hero_guild_routing`, `simq_routing_test` @ 1000t): does A hold, decay toward
   `stasis_N`/`population_stasis`, or oscillate? Cite whichever mechanism (if any) explains the
   observed grade — do not default to "normalization" without checking `stasis_N`/
   `population_stasis` counts in the quality_report.json.
2. **FACTION** (`unit_faction_tension` @ 1000t/2000t): does S hold, decay like `dungeon_crawl`'s
   A→B pattern (pure `effective_denom` dilution), or reveal `diplomacy_dormant`/`faction_monopoly`/
   `tension_oscillation`? Extend the existing `dungeon_crawl` FACTION trajectory write-up rather than
   duplicating it (per investigation.md Prior Work — the file's own "supersede, don't rewrite"
   convention).
3. **COGNITION** (`unit_selfmodel_pilot` @ 1000t): does S hold, decay via `belief_system_dormant`/
   `goal_lock_no_cognition`, or reveal a bug?
4. **SOCIAL persistence** (`urban_political` @ 2000t): document whether SOCIAL=S holds, decays, or
   reveals a bug, including Step 9's population-erosion cross-check result and an explicit statement
   that any observed decay may be confounded by the known, separately-tracked
   `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` defect (human-reviewed decision, 2026-07-08:
   proceed and document rather than defer).
If any hypothesis reveals a genuine bug (not normalization-driven decay, not the known population
confound), file a follow-up ticket per Scope item 5 (mirroring
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`'s pattern) and reference it here — do not fix
it in this ticket.
**Do NOT touch:** Do not rewrite or delete any existing section of this file. Do not fix any
discovered bug in `src/simulation_quality/scorers/*.py` — file a follow-up ticket instead.
**Verify:** Manual review — every one of the 4 hypotheses has an explicit hold/decay/bug verdict with
supporting mechanism citation. Maps to AC3, AC4 (documents the Step 2 profile outcome too).
**Depends on:** Steps 2–9 (needs all data + the profile decision + the population cross-check).

### Step 12 — Update parity ledger entries
**Files:** `docs/parity_ledger/infrastructure.yaml` (`INFRA-237`, `INFRA-240`, `INFRA-241`,
`INFRA-255`, conditionally `INFRA-262`)
**Change:** Per investigation.md's Parity Ledger Overlap section:
- `INFRA-237` — update `support_boundary`/`v2_evidence` to state whether AGENCY=A holds, decays, or
  reveals a `stasis_N`/`population_stasis` bug at 1000t for `hero_guild_routing`/`simq_routing_test`
  (from Step 11's findings).
- `INFRA-240` — add a `v2_evidence` note citing the new `unit_selfmodel_pilot` 1000t COGNITION data
  point.
- `INFRA-241` — add a `v2_evidence` note citing the new `unit_faction_tension` 1000t/2000t FACTION
  data points.
- `INFRA-255` — if `unit_faction_tension`'s FACTION grade decays purely via `effective_denom` growth
  (matching the `dungeon_crawl` pattern), add it as a second confirming data point in this entry's
  rationale text.
- `INFRA-262` — only touch if Step 2b created a profile; otherwise leave unchanged (its existing
  `default.yaml`-fallback fixture entry for `unit_faction_tension` already reflects reality).
Do not change any entry's `status` field (all remain `verified`) unless Step 11 discovers a genuine
bug, in which case follow the same-session parity-update rule for the new follow-up ticket's own
scope, not this one.
**Do NOT touch:** `INFRA-250` and `INFRA-252`'s pre-existing staleness (stale anchor-count text,
stale harness-description mismatch) — investigation.md flags these as "flag for parity-updater" but
explicitly out of this ticket's scope to fix; leave a note in Implementation Notes pointing to them
for a future ticket, do not silently fix them here (would be undocumented scope creep beyond this
ticket's own additions).
**Verify:** `docs/parity_ledger/infrastructure.yaml` still validates against
`docs/parity_ledger/schema.json` (if a validation script exists, e.g. via
`tests/architecture/` parity-ledger schema tests).
**Depends on:** Step 11 (needs the documented findings to write accurate `v2_evidence` notes).

### Step 13 — Run scoped regression suite
**Files:** none (verification only)
**Change:** Run, in order:
```
.venv/bin/python3 -m pytest tests/simulation_quality/ -m "not slow" -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -m slow -v
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v
```
Confirm zero new failures across all four, and confirm the specific anti-drift guards named in
test_plan.md hold: no fast-anchor drift on the 5 target worlds' existing 200t/500t anchors,
`test_timegate_penalties.py::TestAgencyTimegate` stays green, `test_population_stability
[urban_political]` stays `xfail` (not newly passing/failing differently).
**Do NOT touch:** Do not run bare `pytest tests/` — stay scoped to these four invocations plus the
already-listed unit/integration files from test_plan.md's Regression Surface section.
**Verify:** All four commands exit 0 (or expected `xfail`/`skip` only). Maps to all ACs indirectly
(regression safety net).
**Depends on:** Step 10 (keys must be committed first).

### Step 14 — Run `make evaluate` and `make evaluate-full`
**Files:** none (verification only)
**Change:** Run `make evaluate` (dry-run, diffs committed `data/calibration/` reports) then
`make evaluate-full` (re-runs the entire anchor corpus — expect long runtime per investigation.md's
cost-hazard note). Confirm 0 regressions reported across the full corpus, not just this ticket's new
keys.
**Do NOT touch:** Do not interrupt or scope this down with `--scenario` flags for the final AC
check — test_plan.md explicitly warns scenario-scoped runs during development do not substitute for
the final full-corpus check.
**Verify:** Both `make` targets report 0 regressions. Maps to AC5.
**Depends on:** Step 13 (fix anything the scoped suite catches before paying the full-corpus runtime
cost).

## Scope Guards
- Do not modify `src/simulation_quality/scorers/agency.py`, `cognition.py`, `faction.py`,
  `social.py`, or any other scorer/accumulator/hub source file — this ticket only exercises them.
- Do not add any anchor beyond 2000 ticks.
- Do not add any anchor for a world not named in Scope item 2 (`dungeon_crawl`, `sandbox_world`, or
  any flat PROGRESSION/WORLD/ECONOMY/INFORMATION-only world are explicitly out of scope).
- Do not add any key to `FAST_ANCHOR_KEYS`.
- Do not create `config/simulation_quality/profiles/unit_faction_tension.yaml` speculatively — only
  if Step 2's live verification proves it necessary.
- Do not re-fix `hero_guild_routing`'s resource-tag gap or `urban_political`'s hometown gap — already
  closed by the 4 prerequisite tickets; do not duplicate that work.
- Do not fix any genuine drift/decay bug discovered while documenting hypotheses — file a follow-up
  ticket per Scope item 5 instead.
- Do not conflate `urban_political`'s population-collapse defect with a SimQ scoring bug — they are
  different root-cause classes per investigation.md's Anti-Drift Hazards.
- Do not rewrite or delete existing content in `docs/simulation_quality/eval_matrix_results.md` —
  append only, per its established "supersede, don't rewrite" convention.
- Do not fix `INFRA-250`/`INFRA-252`'s pre-existing staleness — flag only, per investigation.md.
- Step 8's population-collapse confound question was resolved by human review (proceed + document,
  option a) — do not re-litigate it; do not attribute any observed SOCIAL decay to a mechanism without
  first checking Step 9's population cross-check.

## Dependency Map
```
Step 1 (prereq check) ─┬─> Step 4 (hero_guild_routing 1000t)
                        ├─> Step 8 (urban_political 2000t)
                        └─> (Steps 3, 5 independent of Step 1's specific gate, but run after
                             for ordering clarity)

Step 2 (unit_faction_tension profile live-verify) ──> Step 6 (unit_faction_tension 1000t)
                                                    ──> Step 7 (unit_faction_tension 2000t)
                                                        [Step 7 depends on Step 6]

Step 3 (unit_selfmodel_pilot 1000t)   ─┐
Step 4 (hero_guild_routing 1000t)      │
Step 5 (simq_routing_test 1000t)       ├──> Step 10 (SLOW_ANCHOR_KEYS update, all keys)
Step 6 (unit_faction_tension 1000t)    │
Step 7 (unit_faction_tension 2000t)    │
Step 8 (urban_political 2000t)         ┘

Step 8 ──> Step 9 (population cross-check, mandatory)

Step 10 ──> Step 13 (scoped regression suite) ──> Step 14 (make evaluate / evaluate-full)

Steps 2, 3, 4, 5, 6, 7, 8, 9 ──> Step 11 (eval_matrix_results.md write-up) ──> Step 12 (parity ledger)
```
Steps 3, 4, 5 are mutually independent and can run in any order. Steps 6–7 are sequential
(2000t needs the 1000t data point). Step 8 proceeds per the human-reviewed decision; Step 9 is
mandatory follow-up, not conditional.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: 4 prerequisite tickets landed before touching `hero_guild_routing`/`urban_political` | Step 1 | `ls tickets/done/` check |
| AC2: New anchors for `unit_selfmodel_pilot`, `unit_faction_tension` (1000t+2000t), `hero_guild_routing`, `simq_routing_test` (1000t), `urban_political` (2000t), ≤2000t each | Steps 3–10 | `pytest tests/simulation_quality/test_grade_regression.py -m slow -v` |
| AC3: `eval_matrix_results.md` documents hold/decay/bug honestly for all 4 hypotheses; follow-up ticket filed if a genuine bug is found | Step 11 | Manual review of doc section |
| AC4: `unit_faction_tension` profile need confirmed live, outcome documented | Step 2, Step 11 | `tests/integration/test_world_profile_feature_flag_guardrail.py` |
| AC5: `make evaluate` and `make evaluate-full` both confirm 0 regressions | Step 14 | `make evaluate`, `make evaluate-full` exit status |

## Anti-Drift Notes
- `evaluate_simq.py`'s full mode re-runs the **entire** anchor corpus (~61+ keys, growing to ~67
  after this ticket), not just fast scenarios — the Makefile comment describing it as "fast (≤500t)
  scenarios only" is stale (flagged as `INFRA-252` staleness, not fixed here). Budget real wall-clock
  time for Step 14; do not substitute a `--scenario`-scoped run for the AC check.
- `stasis_N` (AGENCY) is a one-shot capped escalation at the tick a per-entity DEFER streak first
  crosses `gate + cap` — it does not repeat. Any observed AGENCY decay in Steps 4/5 must be checked
  against `test_timegate_penalties.py::TestAgencyTimegate` before being attributed to this mechanism
  vs. `population_stasis` vs. `effective_denom` dilution vs. a genuine bug.
- `effective_denom` growth (`floor_tick = max(1, current_tick // 4)`,
  `effective_denom = max(floor_tick, last_event_tick)`) is architecturally intentional per
  `docs/simulation_quality/quality_scoring_contract.md` §4.4 and its rationale note
  (`TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`) — do not treat pure denominator-driven grade decay as a
  bug in Step 11's write-up.
- `urban_political`'s population-collapse defect (`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`,
  currently OPEN, not a prerequisite of this ticket) is a world-content/engine-balance issue, not a
  SimQ scorer defect — any SOCIAL decay observed from Step 8 must be triaged against that ticket's
  root cause (via Step 9's cross-check) before being filed as a new, possibly-duplicate SimQ-side
  follow-up.
- The epic's own missing `investigation.md` citation-rot issue (investigation.md Risk 2) is
  non-blocking for this ticket but should be noted in Implementation Notes when staging artifacts move
  to `stored_artifacts/`, so the pattern is visible for the next epic-scoped ticket.
- Cross-check the final `SLOW_ANCHOR_KEYS` list length against this plan's Step 10 before considering
  the ticket done — a silent extra or missing key is the most likely copy-paste failure mode for this
  mechanism (test_plan.md Anti-Drift Test Guard).

## Questions Resolved During Planning
**Step 8 (`urban_political_seed42_2000t` anchor)'s population-collapse confound.** `urban_political`
has a confirmed, unfixed population-collapse defect (56.7% alive at tick 300, seed42, below the 60%
floor — `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`, OPEN, filed after this ticket was scoped
and not one of its 4 hard-dependency tickets). Extending `urban_political` to 2000t is meant to test
whether SOCIAL=S persists (the SOCIAL-persistence hypothesis) — but if population keeps eroding
through 2000t, any observed SOCIAL decay could be caused by entity-count attrition rather than a
genuine SOCIAL mechanism or the already-anticipated `effective_denom` dilution. Escalated to a human
reviewer, who decided (2026-07-08): **proceed and document the confound explicitly** alongside the
SOCIAL grade in Step 11's write-up — Step 9's population cross-check is mandatory as a result.
Implemented by Steps 8–9.

## Deviations
No step's substance deviated from this plan; all 14 steps were executed as specified, in the
specified dependency order, and Step 8's population-collapse confound was documented exactly as the
human-reviewed decision required (proceed + Step 9 mandatory cross-check).

One wording clarification, not a behavioral deviation: Steps 3–8's "commit the calibration artifact"
language (and the ticket's own Scope item 4) describes writing the report to
`data/calibration/{run_key}/quality_report.json` on disk, matching the established convention — it
does **not** mean `git add`/`git commit`. `data/calibration/` is fully `.gitignore`d (line 240,
comment: "transient, regenerated by calibrate_simq.py — analysis lives in
docs/simulation_quality/, anchors in tests/simulation_quality/fixtures/"), and none of the 64
pre-existing calibration directories (including all 11 pre-existing `SLOW_ANCHOR_KEYS` worlds'
reports) are git-tracked either — confirmed via `git ls-files data/calibration/` returning zero
results. The actual git-committed evidence for each new anchor is the `grade_anchors.json` entry +
the `SLOW_ANCHOR_KEYS` string, exactly as `tools/calibrate_simq.py`'s docstring and
`test_grade_regression.py`'s own module docstring describe. This ticket's 6 new calibration reports
follow the identical local-disk-only pattern as every prior anchor ticket; flagging this only so a
future reader of "commit the artifact" doesn't assume `data/calibration/` should appear in `git
status` after this ticket lands.

Step 9's ad hoc population cross-check sampled more checkpoints (300/500/1000/1500/2000) than the
plan's stated minimum ("at minimum the final 2000t tick, ideally also ~300t/1000t checkpoints if
available") — an enhancement within the step's own stated flexibility, not a deviation.
