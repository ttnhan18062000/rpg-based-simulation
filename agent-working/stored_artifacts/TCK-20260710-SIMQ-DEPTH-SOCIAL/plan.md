---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-SOCIAL
artifact_type: plan
tags: [simulation-quality, social, world, corpus, calibration, feature-flags]
---

# Implementation Plan — TCK-20260710-SIMQ-DEPTH-SOCIAL

## Summary

Investigate found the ticket's own candidate premise wrong: none of the three candidates
(`dungeon_crawl`, `frontier_living_world`, `highland_traverse`) compose the `hero_adventurers`
module. Live evidence (single-seed calibration runs, seed 42, 200 ticks) instead shows the real
determinant of SOCIAL viability is settlement/civilian-module presence, because
`HelpNeedEvaluator.evaluate()` hard-gates on `entity.strategic.current_objective_id`, which only
accrues for populations with routine goal-seeking (civilian/guard factions), not pure hostile-faction
spawns. `dungeon_crawl` has no settlement module and produced zero cooperation events (SOCIAL=C);
`frontier_living_world` (545 events) and `highland_traverse` (1496 events) both produced SOCIAL=S.

This plan proceeds with exactly 2 worlds — `frontier_living_world` and `highland_traverse` — and
formally drops `dungeon_crawl` as a rejected candidate. The mechanism is pure feature-flag
activation (`ENABLE_SOCIAL_COOPERATION: "ON"` in each world's calibration profile YAML), no engine
or `WorldCompiler` code changes, consistent with the ticket's own Out-of-Scope guarantee. The plan
also fixes SOC-007's stale `v2_evidence`/`test_path` in the parity ledger (a P0 entry this ticket is
required to extend anyway) rather than propagating the staleness, and folds in a real 3-seed
recalibration (Investigate only empirically ran seed 42; seeds 123/456 must actually be run, not
assumed) against the *committed* profile YAML rather than the env-var override Investigate used for
its feasibility probe.

## Dungeon Crawl Rejection — Confirmed Correct Reading

AQ-2 asks: "If fewer than 2 of the 3 candidates pan out, should the target count drop below 2-3, or
should a considered-and-set-aside candidate (`swamp_border_world`/`frontier_extended`) be promoted?"
Investigate found **2 of 3 candidates DID pan out** (`frontier_living_world`, `highland_traverse`,
both SOCIAL=S) — this is not the "fewer than 2" trigger condition AQ-2 describes, so AQ-2's
promote-a-4th-candidate fallback does not apply. The ticket's own Scope point 3 already frames the
target as "2-3 of the above, final count decided by Investigate," and its Out of Scope section
explicitly reserves "deciding the final 2-vs-3 world count" for Investigate/Plan. Proceeding with
exactly 2 worlds and formally rejecting `dungeon_crawl` (rather than patching it with a forced
population/composition change, which the Anti-Drift Hazards in investigation.md explicitly warn
against) is squarely within scope and does not require promoting a 4th candidate. This reading is
adopted without escalation.

## Steps

### Step 1 — Add `ENABLE_SOCIAL_COOPERATION` flag to the two confirmed-viable worlds' profiles
**Files:**
- `config/simulation_quality/profiles/frontier_living_world.yaml`
- `config/simulation_quality/profiles/highland_traverse.yaml`

**Change:** Both files currently have a `feature_flags:` block with exactly one key:
```yaml
feature_flags:
  ENABLE_BELIEF_ASSIMILATION: "ON"
```
Add `ENABLE_SOCIAL_COOPERATION: "ON"` as a second key in that same block, matching
`urban_political.yaml`'s existing pattern (which has both keys already):
```yaml
feature_flags:
  ENABLE_BELIEF_ASSIMILATION: "ON"
  ENABLE_SOCIAL_COOPERATION: "ON"
```
Do not reorder or reformat the existing `ENABLE_BELIEF_ASSIMILATION` line; add the new key beneath
it, minimal diff.

**Do NOT touch:**
- `config/simulation_quality/profiles/dungeon_crawl.yaml` — rejected candidate, must show zero diff.
- `config/simulation_quality/profiles/urban_political.yaml` — existing control world, must show zero diff.
- Any other profile YAML.
- Any key in the `feature_flags:` block other than adding `ENABLE_SOCIAL_COOPERATION`.

**Verify:** `git diff --stat config/simulation_quality/profiles/` shows exactly 2 files changed, 1
line added each. `python3 -c "import yaml; ..."` (or manual read) confirms both YAML files still
parse and `ENABLE_BELIEF_ASSIMILATION: 'ON'` is unchanged in both.

---

### Step 2 — Recalibrate both worlds across all 3 seeds (42, 123, 456) against the committed profile YAML
**Files (written, not hand-edited):**
- `data/calibration/frontier_living_world_seed{42,123,456}_200t/quality_report.json` (regenerated)
- `data/calibration/highland_traverse_seed{42,123,456}_200t/quality_report.json` (regenerated)

**Change:** Run, for each of the 6 (world, seed) pairs:
```
python3 tools/calibrate_simq.py --name frontier_living_world --seed {42,123,456} --ticks 200
python3 tools/calibrate_simq.py --name highland_traverse --seed {42,123,456} --ticks 200
```
This must run against the **committed** profile YAML from Step 1 (no env-var override) — Investigate's
seed-42 numbers (545/1496 events, both SOCIAL=S) came from an env-var override probe and are directional
evidence only, not canonical anchor values. `--name` resolves the profile via `_resolve_profile()` and
also loads the compiled world spec for that name (`WorldCompiler`), so `--entities` is irrelevant here
(only used for the no-compiled-world fallback path) — do not pass it.

This overwrites the existing `data/calibration/{world}_seed{seed}_200t/` directories in place (they
already exist from the prior FACTION/INFORMATION expansion ticket, currently reflecting
pre-SOCIAL-activation state). Confirm each new `quality_report.json`'s `pillars.SOCIAL.event_count > 0`
and `pillars.SOCIAL.grade` before proceeding — if any of the 6 runs does not show a non-trivial SOCIAL
grade movement off `C`, stop and re-open Investigate rather than editing `grade_anchors.json` to match
a run that didn't actually move.

Then update `tests/simulation_quality/fixtures/grade_anchors.json`'s existing entries — edit the
`SOCIAL` field **in place** for these 6 keys (already present, already in `FAST_ANCHOR_KEYS`, no new
keys to mint):
- `frontier_living_world_seed42_200t`, `_seed123_200t`, `_seed456_200t`
- `highland_traverse_seed42_200t`, `_seed123_200t`, `_seed456_200t`

Set each `SOCIAL` value to the grade actually produced by that seed's regenerated
`quality_report.json` (expected `S` based on Investigate's probe, but use the real per-seed value,
not a blanket copy of the seed-42 result across all three seeds). Every other pillar field
(`COGNITION`, `AGENCY`, `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`, `INFORMATION`, `WORLD`,
`NARRATIVE`) in these 6 entries must remain byte-identical to their current values.

**Do NOT touch:**
- `dungeon_crawl_seed*_*t` and `urban_political_seed*_*t` entries in `grade_anchors.json` — regression
  controls, zero diff expected.
- `FAST_ANCHOR_KEYS` in `tests/simulation_quality/test_grade_regression.py` — all 6 keys already
  listed, no addition needed.
- Any non-`SOCIAL` field of the 6 touched anchor entries.
- `src/engine/apply.py`, `src/domains/cooperation/phase.py` — the two already-fixed engine bugs from
  `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`; zero diff.

**Verify:**
```
pytest tests/simulation_quality/test_grade_regression.py -v
```
`test_grade_within_anchor_band[frontier_living_world_seed{42,123,456}_200t]` and
`test_grade_within_anchor_band[highland_traverse_seed{42,123,456}_200t]` pass with the new anchors;
`test_grade_within_anchor_band[dungeon_crawl_*]` and `[urban_political_*]` remain green with zero
behavioral change. `test_grade_anchor_file_exists_and_valid` passes (10 pillars, valid grade values).

---

### Step 3 — Corpus-wide regression sweep
**Files:** none (verification-only step; may surface findings requiring a follow-up ticket, not code
changes in this ticket per Scope point 9).

**Change:** Run `make evaluate` (or `make evaluate-full`, whichever is the full non-`--dry-run` corpus
sweep per the ticket's own AC). Per the ticket's Pattern-6 warning (COGNITION-alongside-INFORMATION
dual-emission precedent in `eval_matrix_results.md`), check the diff for any pillar movement beyond
`frontier_living_world`/`highland_traverse` SOCIAL. Investigation already found both worlds show a
pre-existing COGNITION=B signal from the earlier `ENABLE_BELIEF_ASSIMILATION` activation (INFORMATION
expansion ticket) — do not misattribute that pre-existing signal to this ticket's SOCIAL flag flip.
Any genuinely new, unattributed cross-pillar drift (in these 2 worlds or any other corpus world) must
be identified and attributed in Implementation Notes, not silently accepted — and per Scope point 9,
any newly-discovered *engine* bug uncovered by this sweep gets filed as its own ticket, not fixed here.

**Do NOT touch:** any world/profile/code outside `frontier_living_world` and `highland_traverse` as a
result of this sweep, even if the sweep surfaces an unrelated pre-existing issue elsewhere in the
corpus — note it, don't fix it.

**Verify:** `make evaluate` exits 0. Diff attributed: only `frontier_living_world` and
`highland_traverse` show SOCIAL movement (and previously-known COGNITION signal); no other world or
pillar shows unattributed drift.

---

### Step 4 — Fix SOC-007's stale parity-ledger evidence and extend it to the two new worlds
**Files:**
- `docs/parity_ledger/social_narrative.yaml` (SOC-007 entry, currently lines 67-77)

**Change:** Current entry:
```yaml
- id: SOC-007
  text: Party/group cooperation is purpose-driven, not just proximity clustering.
  status: verified
  priority: P0
  legacy_evidence: null
  v2_evidence: '`src/systems/groups.py` (`GroupSystem` manages formation, cohesion,
    and intent propagation)'
  proof_type: parity
  test_path: '`tests_v2/parity/test_group_coordination.py`'
  divergence_note: null
  support_boundary: null
```
Two independent problems, both must be fixed:
1. `v2_evidence` path is stale: `src/systems/groups.py` does not exist. Correct it to
   `src/systems/world_systems/groups.py` (class name `GroupSystem` is already correct — confirmed
   present at that path).
2. `test_path` references `tests_v2/parity/test_group_coordination.py`, which does not exist anywhere
   in the repo. Point it at `tests/unit/social/test_social_party_regression.py` — confirmed by direct
   read that `test_no_proximity_only_groups()` (lines 31-45) directly asserts the SOC-007/SOC-164 law
   ("groups do not form just by being near each other," calling
   `GroupSystem.update_groups(state)` and asserting `len(update.groups_add_or_update) == 0` for two
   proximate entities with no contract) and passes (`pytest
   tests/unit/social/test_social_party_regression.py::test_no_proximity_only_groups -q` → 1 passed).

Update `v2_evidence` to also cover the two newly-activated worlds' confirmation of this same law under
live cooperation-driven group formation (not just the unit-test level): append a clause noting that
`frontier_living_world`/`highland_traverse`'s `seed{42,123,456}_200t` calibration runs (Step 2)
exercise `GroupSystem.update_groups()` under real SOCIAL-flag-driven contract-based group formation,
corroborating the law at corpus scale. Example:
```yaml
  v2_evidence: '`src/systems/world_systems/groups.py` (`GroupSystem.update_groups()` — groups form
    only from an already-ACTIVE contract between ungrouped entities within 10.0 units, not proximity
    alone; documented in-code as SOC-164). Corroborated at corpus scale by
    `frontier_living_world`/`highland_traverse` `seed{42,123,456}_200t` calibration runs with
    `ENABLE_SOCIAL_COOPERATION: "ON"` (TCK-20260710-SIMQ-DEPTH-SOCIAL).'
  test_path: '`tests/unit/social/test_social_party_regression.py::test_no_proximity_only_groups`'
```
(Exact wording flexible; the two required facts — corrected file path, corrected/passing test path —
are load-bearing, not the phrasing.)

**Do NOT touch:**
- Any other SOC-* entry in `docs/parity_ledger/social_narrative.yaml` (SOC-001 through SOC-006,
  SOC-008, etc.) — per investigation.md, no other entry overlaps this ticket's scope, and a
  repo-wide stale-path sweep is explicitly out of scope.
- `docs/parity_ledger/social_narrative.yaml`'s schema/structure — edit only the SOC-007 entry's
  `v2_evidence` and `test_path` fields.

**Verify:**
```
pytest tests/unit/social/test_social_party_regression.py::test_no_proximity_only_groups -v
```
passes. Confirm `src/systems/world_systems/groups.py` exists (`ls`). Confirm no other `SOC-*` entry
in the file changed (`git diff docs/parity_ledger/social_narrative.yaml` shows only the SOC-007
hunk).

---

### Step 5 — Update eval matrix and tier taxonomy docs
**Files:**
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`

**Change:** Add grade-table entries/notes for `frontier_living_world` and `highland_traverse`'s
SOCIAL activation, following the existing format used for `urban_political`'s SOCIAL=S activation
writeup (`TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`) as the template — world name, pillar, before/after
grade (`C` → actual Step-2 result, expected `S`), seed matrix, event counts, brief mechanism note
(flag-only activation, `current_objective_id` gate satisfied via settlement-module civilian/guard
population, no compiler-level change). In `eval_matrix_results.md`, add near each world's existing
section (`dungeon_crawl` line ~651, `frontier_living_world` line ~736, `highland_traverse` line
~703 per investigation.md) rather than creating a new standalone section. In
`corpus_tier_taxonomy.md`, update these two worlds' End-to-end tier row/notes to reflect SOCIAL now
active (mirrors how `urban_political`'s row already reflects its SOCIAL activation).

Also add a short explicit note recording `dungeon_crawl`'s rejection as a SOCIAL candidate (structural
reason: no settlement/civilian module → no population ever accrues `current_objective_id` →
`HelpNeedEvaluator` hard gate never opens) so future roadmap tickets don't re-propose it without
re-reading this reasoning.

**Do NOT touch:**
- Any other world's existing grade table entry in either doc.
- `docs/simulation_quality/quality_scoring_contract.md` §5 (SOCIAL pillar weights/thresholds) — out
  of scope per the ticket.

**Verify:** Manual read — new entries present, formatting consistent with existing entries, no
existing entry's numbers altered. Since these files under `docs/` are being modified, run
`make knowledge-index-update` in Finalize per project convention (not part of this step's own
verification, but must not be skipped later).

---

### Step 6 — Regression verification pass and Completion Summary
**Files:** none (verification + ticket documentation only).

**Change:** Run the full scoped regression surface from test_plan.md:
```
pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ -v
pytest tests/unit/social/ -v
pytest tests/unit/observability/test_event_extractor_social_faction.py tests/unit/observability/test_event_extractor_social_memory.py -v
pytest tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py tests/perf/test_phase7_social_cooperation_budget.py -v
pytest tests/simulation_quality/test_grade_regression.py -v
pytest tests/simulation_quality/ -v
```
All must pass (or skip only for legitimately absent calibration data unrelated to the 6 touched
anchor keys). Confirm the Anti-Drift Test Guards from test_plan.md hold: `dungeon_crawl` and
`urban_political` anchors show zero diff; non-SOCIAL pillars in the 6 touched anchor entries show zero
diff; `ENABLE_SOCIAL_COOPERATION` is the only new key in the two profile YAMLs;
`src/engine/apply.py`/`src/domains/cooperation/phase.py` show zero diff.

Write the ticket's Completion Summary explicitly stating:
- `dungeon_crawl` was investigated and rejected as a SOCIAL candidate (with the structural reason and
  empirical zero-event evidence), and that this is *not* an AQ-2 "fewer than 2 candidates" situation —
  2 of 3 candidates panned out, so no 4th candidate was promoted.
- Two follow-up-candidate observations from investigation.md are explicitly **not** actioned in this
  ticket and are candidates for separate small tickets:
  1. `docs/simulation/domains/cooperation_contract.md` is stale relative to live code (missing the
     `current_objective_id` hard-gate in its trigger table; references non-existent file names
     `contract_service.py`/`group_evaluator.py`/`partner_scoring.py`/`posture.py` instead of the live
     `services.py`/`providers.py`/`postures.py`).
  2. The vestigial `state.social_cooperation_enabled` dead-flag check at
     `src/domains/cooperation/phase.py:40` (always defaults `True`, never set anywhere, harmless but
     confusing) is a candidate for a small cleanup ticket — not fixed here since it is an engine-code
     change and this ticket's Out of Scope explicitly excludes engine work.

**Do NOT touch:** the two follow-up items above — note only, do not fix.

**Verify:** All scoped pytest commands green; Completion Summary present in the ticket file with both
follow-up notes recorded.

## Scope Guards

- `config/simulation_quality/profiles/dungeon_crawl.yaml` — do not add the flag; rejected candidate.
- `data/worlds/{dungeon_crawl,frontier_living_world,highland_traverse}/world.yaml` and their
  `resolved/world.resolved.yaml` — no world-composition changes; this ticket does not author content,
  only flips a calibration-profile flag.
- Any `WorldCompiler`/schema/resolver code — confirmed unnecessary by investigation.md; touching it is
  scope creep the ticket's Out of Scope explicitly forbids.
- `docs/simulation_quality/quality_scoring_contract.md` §5 SOCIAL weights/thresholds — no scoring
  changes.
- `src/engine/apply.py` (feature-flag propagation fix) and `src/domains/cooperation/phase.py`'s
  serialization sentinel — both already fixed by `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`; re-touching
  either is an explicit anti-scope violation per the ticket's Out of Scope section.
- `docs/simulation/domains/cooperation_contract.md` — stale doc noted as a follow-up candidate, not
  fixed in this ticket.
- `src/domains/cooperation/phase.py:40`'s vestigial `state.social_cooperation_enabled` check — noted,
  not removed or "fixed"; harmless dead code, out of scope (no engine changes permitted).
- Any other `SOC-*` parity-ledger entry besides SOC-007.
- `FAST_ANCHOR_KEYS` list in `test_grade_regression.py` — no additions; all 6 required keys already
  present.
- Any profile YAML other than `frontier_living_world.yaml`/`highland_traverse.yaml` (in particular
  `urban_political.yaml`, the existing SOCIAL control world).
- Adding SOCIAL content to Stress tier, Unit tier, or `simq_routing_test` worlds.

## Dependency Map

- Step 1 (flag YAML edit) must complete before Step 2 (recalibration reads the committed profile).
- Step 2 must complete before Step 3 (corpus sweep should reflect the updated anchors/calibration
  state) and before Step 5 (doc updates cite Step 2's actual grade/event-count numbers, not
  Investigate's env-var-override probe numbers).
- Step 4 (SOC-007 fix) is independent of Steps 1-3 — it corrects a pre-existing staleness and can be
  done in parallel with or before them — but its extension clause (citing the two newly-activated
  worlds) reads more naturally after Step 2's real numbers exist. Sequence it after Step 2 for
  citation accuracy, though it has no hard technical dependency.
- Step 5 depends on Step 2 (real grades) and benefits from Step 4 being done (consistent parity
  references) but has no hard blocking dependency on Step 3.
- Step 6 depends on all of Steps 1-5 being complete; it is the final gate.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Investigate re-verifies candidate short-list against live state, confirms live-trigger conditions before any profile change | Already satisfied by investigation.md (prerequisite to this plan); Step 1 only proceeds because this AC is already met | N/A (investigation.md is the evidence artifact) |
| 2-3 selected worlds each have `ENABLE_SOCIAL_COOPERATION: "ON"` added to their profile YAML | Step 1 | `git diff` on the two profile YAMLs; manual YAML parse check |
| Each selected world compiles with 0 new warnings and holds its population-alive floor through calibration run length | Step 2 (calibration run itself surfaces compile warnings/population drop) | `pytest tests/simulation_quality/` population-stability test (per test_plan.md item 5); calibration run stdout/stderr clean |
| Each selected world's SOCIAL grade moves measurably off `C` across a 3-seed matrix, with grade-anchor entries updated (+ `FAST_ANCHOR_KEYS` if applicable) | Step 2 | `pytest tests/simulation_quality/test_grade_regression.py -v` (6 touched keys); `quality_report.json` `event_count > 0` per world/seed |
| `make evaluate` exits 0 with 0 unattributed regressions | Step 3 | `make evaluate` exit code + manual diff attribution |
| SOC-007 extended with `v2_evidence` covering newly selected worlds | Step 4 | `pytest tests/unit/social/test_social_party_regression.py::test_no_proximity_only_groups -v` |
| `eval_matrix_results.md` and `corpus_tier_taxonomy.md` updated with newly-activated worlds' grade tables/tier notes | Step 5 | Manual read; `make knowledge-index-update` in Finalize |
| Any newly-discovered engine bug filed as its own ticket, not folded into this one | Step 3 (sweep is where such a bug would surface) + Step 6 (Completion Summary records the discipline) | Manual — confirm no engine-code diff exists outside the two already-permitted fixed files' zero-diff guard |

Note: the ticket's AC language ("2-3 selected worlds") is satisfied by exactly 2 —
`frontier_living_world` and `highland_traverse` — with `dungeon_crawl` formally rejected per the
Dungeon Crawl Rejection section above.

## Anti-Drift Notes

- **Do not re-fix** `apply_generation()`'s feature-flag propagation or `CooperationPhase`'s
  serialization sentinel — both already fixed and confirmed present in live code; any diff to
  `src/engine/apply.py` or `src/domains/cooperation/phase.py` in this ticket's PR is scope creep.
- **Do not assume `hero_adventurers`/hero-guild population is required** for SOCIAL activation — the
  empirical evidence shows the opposite: `frontier_living_world`/`highland_traverse` succeeded via
  non-hero civilian/guard population (settlement modules), and `dungeon_crawl` specifically failed
  because it has *no* civilian population of any kind, hero or otherwise.
- **Do not "fix" `dungeon_crawl` by adding a civilian/settlement module to force activation** — that
  is exactly the kind of forced-population-adjustment the investigation's Anti-Drift Hazards warn
  against; the ticket-consistent choice given 2 strong candidates already exist is to drop it.
- **Do not touch `state.social_cooperation_enabled`** (`phase.py:40`) — dead/vestigial, always
  defaults `True`, unrelated to the real `ENABLE_SOCIAL_COOPERATION` gating at the `run_phase()` call
  site in `pipeline.py:158`. Note as a follow-up candidate only.
- **Do not create new `grade_anchors.json` keys** for the 6 (world, seed) pairs — they already exist
  and are already in `FAST_ANCHOR_KEYS` from the prior FACTION/INFORMATION expansion ticket. Update
  the `SOCIAL` field of the existing entries only.
- **Do not let the SOC-007 stale-path fix expand into a general parity-ledger cleanup** — fix only
  the SOC-007 entry; a repo-wide sweep of other stale entries is out of scope.
- **Watch for the documented COGNITION dual-emission side effect** in Step 3's full sweep — both
  worlds already show a pre-existing COGNITION=B signal from `ENABLE_BELIEF_ASSIMILATION` (prior
  INFORMATION expansion ticket, not this ticket's SOCIAL flag). Do not misattribute it.
- **Recalibrate against the committed profile YAML, not an env-var override** — Investigate's
  545/1496-event numbers came from a scratch env-var probe (`ENABLE_SOCIAL_COOPERATION=ON <cmd>`,
  profile file untouched) used only to decide which candidates to keep. Step 2 must produce the
  canonical anchor values from a real run against the Step-1-edited profile YAML, and seeds 123/456
  must actually be run (not extrapolated) even though they are expected to track seed 42's grade.
- **`docs/simulation/domains/cooperation_contract.md`'s staleness is out of this ticket's scope** —
  note it in Completion Summary as a follow-up candidate; do not edit the doc in this ticket.

## Unresolved Questions

None. The one item flagged for a Plan-phase decision (RQ-2 / AQ-2 in investigation.md — whether 2
worlds is sufficient or a 4th candidate must be promoted) is resolved above under "Dungeon Crawl
Rejection — Confirmed Correct Reading": 2 of 3 candidates panned out, which is not AQ-2's "fewer than
2" trigger condition, so no 4th candidate is promoted. This is a direct application of the ticket's
own stated default resolution, not a new judgment call requiring escalation.

## Deviations

Recorded during Implement, per this project's "update plan.md if any step deviates" rule.

1. **Step 2 — "Every other pillar field... must remain byte-identical" did not hold for
   `frontier_living_world`.** The real 3-seed recalibration against the committed profile YAML
   showed `frontier_living_world_seed123_200t`'s NARRATIVE move B → A and
   `frontier_living_world_seed456_200t`'s PROGRESSION move B → C, in addition to the expected
   SOCIAL C → S on all 6 keys. Both are within the grade-regression suite's ±1 letter band
   tolerance. This plan's assumption of SOCIAL-only movement was too narrow: `CooperationPhase` is
   a genuine per-tick decision phase (not a purely additive scorer like the FACTION/INFORMATION
   flag activations this plan's Anti-Drift Notes drew the "SOCIAL is flag-only" analogy from) —
   once active, it can perturb each seed's downstream entity trajectory, cascading into other
   pillars' event counts. Both fields were updated to their real observed values (per the parent
   task's explicit instruction to update "the SOCIAL field and any other pillar fields that
   shift"), documented in `eval_matrix_results.md`'s new `frontier_living_world` SOCIAL section and
   in the ticket's Implementation Notes, rather than left stale or silently reconciled.
   `highland_traverse` showed no such cascade in any of its 3 seeds — confirming the effect is
   population/composition dependent, not a general SOCIAL-activation side effect.

2. **Step 3's corpus sweep surfaced pre-existing drift this plan did not anticipate**, in worlds
   this plan explicitly scoped out (`dungeon_crawl`, `urban_political`): 3 REGRESS pillars
   (`dungeon_crawl_seed42_200t` COMBAT/PROGRESSION, `urban_political_seed42_200t` PROGRESSION),
   confirmed unrelated to this ticket (zero diff to either world's inputs; reproduces in standalone
   isolation). Filed as `tickets/todos/TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT.md` per Scope
   point 9 rather than fixed — this plan's Step 3 anticipated only the already-known COGNITION
   dual-emission side effect, not a fresh, unrelated drift in the control worlds.

3. **Step 6's regression pass surfaced 2 additional pre-existing, unrelated failure categories**
   not anticipated by this plan: a stale `EXPECTED_KEYS` assertion in
   `test_group_lifecycle_fields.py` and 2 scenario-test assertions in
   `test_phase7_social_cooperation_scenarios.py` still checking a pre-serialization-fix API shape.
   Both confirmed unrelated to this ticket (no diff touches the relevant code). Filed as
   `tickets/todos/TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS.md` rather than fixed in this
   ticket's scope.

None of these deviations required any change to the plan's core mechanism (pure profile-YAML flag
activation, 2 worlds, `dungeon_crawl` rejected) — they are additive findings, not changes to what
was implemented.
