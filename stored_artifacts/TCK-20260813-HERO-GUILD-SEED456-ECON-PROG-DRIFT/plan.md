---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT
artifact_type: plan
tags: [simulation-quality, calibration, corpus, economy, progression]
---

# Implementation Plan — TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT

## Summary

This is a fixture-only recalibration ticket — no `src/` change is proposed or permitted
(investigation.md Risk #5, Anti-Drift Hazards). The plan re-derives final byte-exact values from a
fresh clean `tools/calibrate_simq.py` run (investigation.md Risk #4 — DEBUG-instrumented runs are
not trustworthy for committed values), then edits exactly three `grade_anchors.json` pillar fields
across two existing run_key entries, adds exactly one new additive `score_ceilings.json`
`watchdog_variance` entry, and adds disclosure-only dated addenda to
`docs/guidelines/intentional_divergences.md` §2.41 and two NOTE blocks to
`docs/simulation_quality/eval_matrix_results.md`. The `simq_routing_test_seed456_500t`/PROGRESSION
anchor value is a genuine open call between two observed natural states (investigation.md Risk #1)
— this plan resolves it in favor of `-0.2359249329758713`, the more-frequently-observed
(3/5 clean draws vs. 2/5) state, matching investigation.md's own recommendation; see "Decision on
Open Question" below for the full justification. No parity ledger edit is required (investigation.md
already checked; confirmed independently in this plan's own fact-verification pass).

## Decision on Open Question (Risk #1)

Investigation.md Finding 2 / Risk #1 found `simq_routing_test_seed456_500t`/PROGRESSION genuinely
bimodal across 6 independent clean-vs-instrumented re-runs: 5 clean trials split 2 at
`-0.15483870967741936` (21 events) and 3 at `-0.2359249329758713` (25 events). This plan **resolves
the anchor value to `-0.2359249329758713`**, for three reasons:

1. It is the empirically modal clean-trial outcome (3/5 vs. 2/5) — a fresh anchor should center on
   the more probable future draw, minimizing the fraction of CI runs that hit the (now-annotated,
   but still red) minority-state failure path.
2. It matches the precedent already set by the existing `simq_routing_test_seed42_500t`/PROGRESSION
   and `_seed123_500t`/PROGRESSION `watchdog_variance` entries (`tests/simulation_quality/fixtures/
   score_ceilings.json:12-25`, `:28-33`): in both precedents the anchor is pinned to one concretely
   observed value while the `score_ceilings.json` entry (Step 4 below) is what absorbs and explains
   the *other* draws, not the anchor itself trying to average or split the difference.
3. Per investigation.md Risk #1's own math, whichever value is chosen, the *other* state's future
   draws will still exceed the default score tolerance (~0.081 gap, versus a floor of
   `max(0.05, 20%*|anchor|)` ≈ 0.047-0.05) — so the choice does not change whether a
   `score_ceilings.json` ceiling annotation is needed (it is needed either way, per Step 4), only
   which state reads as "the anchor" vs. "the annotated deviation."

This is a plan-level decision per this ticket's own instructions (the investigation intentionally
left it open); it is not deferred further. If Implement's fresh clean re-run (Step 1) produces a
different modal split than investigation.md's 5-trial sample, Implement must stop and flag it back
rather than silently picking a value — see Unresolved Questions.

## Steps

### Step 1 — Fresh clean calibration re-run to confirm final byte-exact values
**Files:** none (verification-only step; produces the numbers Steps 2-3 consume)
**Change:** Run `tools/calibrate_simq.py --ticks 500 --seed 456 --name hero_guild_routing` and
`tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test`, each **without** any
DEBUG log handler attached (investigation.md Risk #4 — the one DEBUG-instrumented trial in
Investigate's own 6-trial sample diverged from the other 5 clean trials on both run_keys, plausibly
from per-tick file-I/O perturbing the wall-clock watchdog throttle). Confirm the output matches
investigation.md's cited clean-trial values:
- `hero_guild_routing_seed456_500t`: ECONOMY `events=0, norm=0.0`; PROGRESSION
  `events=11, norm=-0.3025210084033613`.
- `simq_routing_test_seed456_500t`: PROGRESSION lands on one of the two documented states
  (`events=21, norm=-0.15483870967741936` or `events=25, norm=-0.2359249329758713`) — confirm which,
  and proceed with the Step 3 value (`-0.2359249329758713`) regardless of which single draw Step 1
  itself lands on, since the anchor decision (see "Decision on Open Question") is based on the
  aggregate 5-trial modal distribution already established by investigation.md, not on
  re-litigating a single fresh draw. If this run also lands on the `21-event` state, that is
  expected (2/5 historical rate) and not a reason to change the anchor value — the whole point of
  Step 4's `watchdog_variance` entry is that both states are expected and annotated.
- Confirm the other pillars (COMBAT, WORLD, AGENCY, COGNITION, etc. — none of which this ticket
  edits, per Scope Guards) stay otherwise consistent with investigation.md's report shown at
  investigation.md lines 20-36 for `hero_guild_routing_seed456_500t` and lines 50-65 for
  `simq_routing_test_seed456_500t`, as a sanity check that Step 1's run is a clean, representative
  trial and not an anomaly.
**Do NOT touch:** No file edit in this step. Do not attach any `logging.FileHandler` or other DEBUG
instrumentation to `src.systems.strategic_systems.intelligence` or any other logger while producing
these numbers.
**Verify:** Manual comparison of this run's console output against investigation.md's cited clean
values (lines 21-36, 50-65). If ECONOMY/PROGRESSION on `hero_guild_routing_seed456_500t` differ from
`0.0`/`-0.3025210084033613`, or if `simq_routing_test_seed456_500t`'s PROGRESSION lands on a value
outside the two documented states, stop and re-open Risk #1/#4 rather than proceeding to Step 2/3.

### Step 2 — Edit `grade_anchors.json`: `hero_guild_routing_seed456_500t` ECONOMY and PROGRESSION
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** In the `hero_guild_routing_seed456_500t` object (current content confirmed by direct
read, fixture root has 84 total keys = 81 scenario run_keys + 3 metadata keys
`_note`/`_instructions`/`_grade_order`, per `tests/simulation_quality/test_grade_regression.py:678-683`):
- `ECONOMY`: `{"grade": "B", "score": 0.10972568578553615}` → `{"grade": "C", "score": 0.0}`
- `PROGRESSION`: `{"grade": "D", "score": -0.6212534059945504}` → `{"grade": "C", "score":
  -0.3025210084033613}`

Use the exact float values confirmed by Step 1's fresh clean run (falling back to investigation.md's
cited values, which are already known to be clean-trial values, only if Step 1's own run is somehow
unavailable to reproduce — not expected). Do not reformat, reorder, or touch any other key in this
run_key's object (`COGNITION`, `AGENCY`, `COMBAT`, `FACTION`, `SOCIAL`, `INFORMATION`, `WORLD`,
`NARRATIVE` all stay byte-identical to their current values, confirmed by direct read: `COMBAT`
`{"grade": "C", "score": -0.0967741935483871}`, `WORLD` `{"grade": "B", "score": 0.115}`).
**Do NOT touch:** `hero_guild_routing_seed456_500t.COMBAT` or `.WORLD` (Scope Guards — both already
correctly explained by `tools/simq_ceiling.py`'s computed `flag_gated`/`tick_budget` classifiers,
independent of the anchor value; editing them would not change the pytest outcome and is scope
creep per investigation.md Anti-Drift Hazards). Do not touch any other run_key in this file. Do not
add or remove a top-level key (would break `test_grade_anchors_entry_count_unchanged`'s 81-entry
assertion).
**Other writers of this file:** None at runtime — `grade_anchors.json` is a hand-maintained test
fixture, not written by any production or tooling code path. Confirmed by direct grep of `tools/`
and `src/`: `tools/evaluate_simq.py:34`, `tools/generate_corpus_registry.py:23`, and
`tools/simq_audit_gaps.py:31` all only *read* `ANCHORS_PATH`/`DEFAULT_ANCHORS`; none writes it. The
only "writer" is ticket-driven manual edit, sequential across tickets, never concurrent within a
single tick or process — no race/ordering/double-write hazard applies to this edit.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -q -m "not slow"` passes.

### Step 3 — Edit `grade_anchors.json`: `simq_routing_test_seed456_500t` PROGRESSION
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** In the `simq_routing_test_seed456_500t` object (current content confirmed by direct
read: `PROGRESSION` currently `{"grade": "D", "score": -0.6927374301675978}`), change PROGRESSION
to `{"grade": "C", "score": -0.2359249329758713}` — per the Decision on Open Question above. Do not
touch this run_key's `ECONOMY` (`{"grade": "B", "score": 0.09975062344139651}`, confirmed by direct
read — investigation.md's fresh trial found actual ECONOMY `0.09523809523809523`/4 events, within
tolerance of this anchor, and not in the ticket's named 3-pair scope) or `COMBAT`
(`{"grade": "C", "score": 0.0}`, already correctly `[known flag_gated]`).
**Do NOT touch:** `simq_routing_test_seed456_500t.COMBAT`, `.WORLD`, `.ECONOMY`, `.AGENCY`,
`.COGNITION`, or any other pillar on this run_key. Do not touch any other run_key.
**Other writers of this file:** Same as Step 2 — no runtime writer, only sequential ticket-driven
manual edits. Steps 2 and 3 both edit the same file in the same commit; both edits are additive
field-value changes to disjoint pillar keys inside disjoint run_key objects, so they do not collide
with each other.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -q -m "not slow"` passes.

### Step 4 — Add one new `watchdog_variance` entry to `score_ceilings.json`
**Files:** `tests/simulation_quality/fixtures/score_ceilings.json`
**Change:** Append one new object to the `entries` array (currently 6 entries, confirmed by direct
read of the full file), matching the existing `simq_routing_test_seed42_500t`/PROGRESSION
(`score_ceilings.json:11-18`) and `simq_routing_test_seed123_500t`/PROGRESSION
(`score_ceilings.json:27-34`) entries' exact field set and order (`run_key`, `pillar`,
`ceiling_kind`, `reason`, `evidence`, `since_ticket` — no other fields; confirmed these are the only
fields any entry in this file uses):

```json
{
  "run_key": "simq_routing_test_seed456_500t",
  "pillar": "PROGRESSION",
  "ceiling_kind": "watchdog_variance",
  "reason": "Real run-to-run non-determinism confirmed via 6 independent re-runs this session (5 clean, 1 DEBUG-instrumented and excluded from this count): event_count/normalized_score split bimodally across the 5 clean trials -- 21 events/-0.15483870967741936 (trials 1, 5) vs. 25 events/-0.2359249329758713 (trials 3, 4, 6), a reproducible 2/5-vs-3/5 split, not a single stable value. The anchor is recalibrated to the modal (3/5) state, -0.2359249329758713; the minority (2/5) state remains a real, expected, ceiling-annotated deviation, not a code defect. Same watchdog-throttle-driven low-event-count sensitivity as the existing simq_routing_test_seed42_500t and _seed123_500t PROGRESSION entries (kernel.py's tick-budget throttle, D06 F6, intermittently dropping a different number of events run-to-run) -- COMBAT and ECONOMY on this same run_key stayed byte-identical across all 6 trials, confirming the jitter is localized to PROGRESSION specifically, matching the established pattern for this pillar.",
  "evidence": "6 independent same-seed re-runs of tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test this session (5 clean, 1 debug-instrumented); docs/audits/D06_longrun_health.md F6",
  "since_ticket": "TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT"
}
```

**Do NOT touch:** Do not delete, reorder, or edit any of the 6 existing entries (the `NARRATIVE`
`corrected` entry; `simq_routing_test_seed42_500t`'s PROGRESSION and COGNITION entries;
`simq_routing_test_seed123_500t`'s PROGRESSION entry; `urban_political_seed456_500t`'s ECONOMY and
PROGRESSION entries) — this is strictly additive, preserving audit history per the established
precedent (`score_ceilings.json`'s `seed123`/PROGRESSION entry itself demonstrates the pattern:
mark superseded-in-part inline, never delete). Do not add an entry for
`hero_guild_routing_seed456_500t` (no jitter observed there across 5 clean trials — Finding 2 is
explicit that only `simq_routing_test_seed456_500t`/PROGRESSION qualifies).
**Other writers of this file:** None at runtime — confirmed by grep, only `tools/simq_ceiling.py:33`
(`SCORE_CEILINGS_PATH`) *reads* this file (via `lookup_ceiling()`, used by
`test_grade_regression.py:284`'s `_format_score_failures` to append the `[known ...]` annotation).
No production or tooling code writes this file; only ticket-driven manual edits, never concurrent.
**Verify:** `pytest tests/tools/test_score_ceilings.py -q -m "not slow"` — all 6 existing tests stay
green (none references `simq_routing_test_seed456_500t` by name, confirmed by test_plan.md). If
Implement also adds the optional guard test named in test_plan.md
(`test_watchdog_variance_ceiling_present_for_simq_routing_test_seed456_progression`), it must pass
too, but it is optional per test_plan.md's own framing — not required for AC completion.

### Step 5 — `docs/guidelines/intentional_divergences.md` §2.41: add dated addendum disclosing the HARVESTING-starvation finding
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** §2.41 ("Adventure-Route Defer-Reason Observability Gap",
`docs/guidelines/intentional_divergences.md:998-1122`) already contains three dated addenda in this
exact pattern: `**Broadened disclosure (TCK-..., 2026-08-13)**:` (line 1026),
`**Restoration (TCK-..., 2026-08-13)**:` (line 1057). Append a fourth addendum in the same bullet
style, inserted after the existing "Restoration" bullet (line 1057-1112) and before the
`**Verification**:` line (line 1113), reading (content, not exact prose — Implement may tighten
wording but must preserve every cited fact):

> **Related finding — HARVESTING tier-5 starvation on `hero_guild_routing_seed456_500t` /
> `simq_routing_test_seed456_500t` (TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT, 2026-08-13)**:
> the same tier-5-goal-competition-dominance phenomenon this section documents for `ADVENTURE_ROUTE`
> (Restoration addendum above) independently and additionally suppresses `HARVESTING` on these two
> run_keys. DEBUG-trace evidence: `HARVESTING` wins tier-5 goal arbitration exactly 1/371 evaluated
> ticks on `hero_guild_routing_seed456_500t` and 1/335 on `simq_routing_test_seed456_500t` — the
> same two competitors (`COMBAT_ENGAGE`, `REGION_STABILIZATION`) dominate both worlds' tick budgets
> for the same structural reason (§2.43's `REGION_STABILIZATION` scorer floors at 100.0;
> `CombatEngageScorer` floors at 40 and commonly reaches 70-140+; `HarvestScorer`'s distance-decayed
> `50.0/dist` formula rarely exceeds 30). This directly suppresses ECONOMY (harvesting/crafting/trade
> events never fire) on both run_keys and PROGRESSION indirectly (via `capability_growth_stalled` —
> gear/gold growth requires harvesting/crafting, which essentially never runs). Recalibrated in
> `grade_anchors.json` by this ticket (`hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION,
> `simq_routing_test_seed456_500t` PROGRESSION) — see this ticket's own investigation.md Finding 1.
> This is a distinct `GoalKind` (`HARVESTING`, not `ADVENTURE_ROUTE`) and a mechanistically distinct
> formula (distance-decay, not a hard scale cap), but the same downstream starvation *class* as this
> section's existing `ADVENTURE_ROUTE` disclosure. Not fixed here — a recalibrate-and-disclose
> decision, matching this ticket's own scope guards. If `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-
> NEVER-WINS-TIER5` (the open follow-up already tracking the `ADVENTURE_ROUTE` half of this same
> phenomenon) is ever picked up, `HARVESTING`'s distance-decay formula should be considered in the
> same pass, since it loses to the identical two competitors for a structurally analogous reason.

**Do NOT touch:** The existing "Old Behavior", "New Behavior", "Rationale", "Broadened disclosure",
or "Restoration" bullets (lines 998-1112) — append only, do not edit their prose. Do not touch §2.40,
§2.42, or §2.43 (adjacent sections; this finding does not change their own content, only
cross-references them). Do not change the `**Status**:` line (line 1119-1121) — the write-path
restoration status is unaffected by this unrelated HARVESTING finding.
**Verify:** No automated test covers doc prose content; verify via manual re-read that the addendum
is inserted in the correct location (after Restoration, before Verification) and that
`docs/REGISTRY.yaml` regeneration (Finalize phase, automatic) picks up the file's updated mtime — no
action needed here beyond the edit itself since this doc was already modified this session by prior
tickets and is already registered.

### Step 6 — `docs/simulation_quality/eval_matrix_results.md`: dated NOTE blocks in both 500t subsections
**Files:** `docs/simulation_quality/eval_matrix_results.md`
**Change:** Two separate NOTE-block insertions, matching the doc's own established pattern (see
lines 430-459, 461-477, 479-491 for the exact blockquote style: `> **NOTE (2026-08-13 —
` + "`" + `TCK-...` + "`" + `):**` followed by `>`-prefixed prose, inserted directly after the
relevant subsection's table/analysis and before the next `---`/section header):

1. **`simq_routing_test` 500t subsection** (`docs/simulation_quality/eval_matrix_results.md:374-423`,
   ends at the `---` on line 493): insert a new NOTE block after the existing
   `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` NOTE (lines 479-491) and before the
   `---` (line 493), disclosing: `PROGRESSION`'s historical table row (line 388, "norm ≈ -0.06,
   event_count=1, all 3 seeds") is now stale for `seed456` specifically — fresh measurement (this
   ticket) confirms `seed456`'s PROGRESSION is `C`/`-0.2359249329758713` (25 events, one of two
   observed bimodal states, see `score_ceilings.json`'s new `watchdog_variance` entry), root-caused
   to the same tier-5 `HARVESTING`-starvation mechanism disclosed in
   `docs/guidelines/intentional_divergences.md` §2.41's newest addendum (this ticket). Cross-reference
   `grade_anchors.json`'s recalibrated value and this ticket's ID.
2. **`hero_guild_routing` 500t subsection** (`docs/simulation_quality/eval_matrix_results.md:1448-
   1462` table, NOTE blocks at 1498-1512 and 1514-1523): insert a new NOTE block after the existing
   `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` NOTE (lines 1514-1523) and before the
   next `---`, disclosing: the table's `ECONOMY`/`PROGRESSION` row for `seed456` (line 1455/1458,
   both currently read "C"/"stable" — table does not break out per-seed for these rows, but the prior
   `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` NOTE at lines 1498-1512 already
   flagged this exact gap: "`ECONOMY`/`PROGRESSION`... for `seed456` specifically... disclosed but
   deliberately not recalibrated by this ticket, tracked instead by
   `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`") is now recalibrated: ECONOMY `C`/`0.0` (was
   anchored `B`/`0.10972568578553615`), PROGRESSION `C`/`-0.3025210084033613` (was anchored
   `D`/`-0.6212534059945504`). Root cause: same tier-5 `HARVESTING`-starvation mechanism (1/371
   win-rate), disclosed in §2.41's newest addendum. Cross-reference this ticket's ID and confirm the
   prior NOTE's forward-reference is now resolved.
**Do NOT touch:** The historical table rows themselves (lines 382-393, 1450-1462) — per
investigation.md's explicit instruction, do not silently rewrite them; the NOTE blocks are the
mechanism for disclosing staleness, matching every prior NOTE in this doc. Do not touch any other
subsection (`urban_political`, `sandbox_world`, `dungeon_crawl`, stress-tier worlds, long-run
anchors, etc.) — out of this ticket's named 2 run_keys.
**Verify:** No automated test covers doc prose; verify via manual re-read that both NOTE blocks are
inserted in the correct subsection, after the existing 2026-08-13 NOTE chain, and that the stated
recalibrated values exactly match what Steps 2-3 actually wrote to `grade_anchors.json` (copy-paste
the committed values, do not retype them by hand, to avoid a doc/fixture mismatch).

### Step 7 — Run the ticket's scoped verification command and confirm the textual (not exit-code) pass condition
**Files:** none (verification-only)
**Change:** Run, verbatim, the ticket's own AC4 command:
```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k \
  "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"
```
**This command will NOT exit 0** — per investigation.md Risk #3 / test_plan.md's explicit warning,
both parametrizations of `test_grade_within_anchor_band` will still show `FAILED` after this
ticket's edits land, because each run_key carries pre-existing, out-of-this-ticket's-scope
score-tolerance failures this ticket does not touch:
- `hero_guild_routing_seed456_500t`: COMBAT (`[known flag_gated]`) and WORLD (`[known tick_budget]`)
  remain failing.
- `simq_routing_test_seed456_500t`: COMBAT (`[known flag_gated]`) remains failing; PROGRESSION
  itself may also still show failing on an unlucky future draw (`[known watchdog_variance]`, now
  that Step 4's entry exists).

**The correct pass condition is textual**: inspect every line inside each failure's `score_failures`
list (`_format_score_failures`, `tests/simulation_quality/test_grade_regression.py:258-284`) and
confirm every single line carries a trailing `[known <ceiling_kind>: ...]` annotation — zero
*unannotated* lines is "0 unexplained failures" per the ticket's AC4 wording. Do not interpret a
non-zero pytest exit code as incomplete work; do not interpret it as complete work without actually
reading the annotation text on every line. An unannotated `ECONOMY` or `PROGRESSION` line (missing
the `[known ...]` suffix) means Step 1's fresh values were not correctly carried into Steps 2/3, or
were computed against stale/instrumented data — re-derive from a fresh clean run and redo Steps 2/3,
do not hand-edit the fixture to a value that merely happens to pass.
**Do NOT touch:** Do not add a `SCORE_TOLERANCE_OVERRIDES` entry to make this command exit 0 (Scope
Guards) — that is the wrong mechanism and is explicitly forbidden.
**Verify:** Also run the regression/anti-drift guard sweep from test_plan.md:
```
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid \
  tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged \
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars \
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors \
  tests/tools/test_score_ceilings.py \
  -q -m "not slow"
```
All must pass with 0 failures (unlike the AC4 command, this sweep has no pre-existing known-failure
pillars in it — a genuine failure here is a real regression). Additionally run the full
`FAST_ANCHOR_KEYS` sweep before/after (git stash/git stash pop around the two fixture edits, matching
the parent ticket's precedent) to confirm zero unrelated `(run_key, pillar)` pairs newly fail.

### Step 8 — Parity ledger: no edit required
**Files:** none
**Change:** No `docs/parity_ledger/*.yaml` edit is made. investigation.md's "Parity Ledger Overlap"
section already checked `docs/parity_ledger/town_resource.yaml`, `docs/parity_ledger/
progression.yaml`, `docs/parity_ledger/strategic_cognition.yaml` (STRAT-255), and `docs/
parity_ledger/infrastructure.yaml` (INFRA-237) via `search_docs`/`graphify query` plus direct grep
for both run_key names, and found no entry making a specific numeric-grade claim for either run_key's
ECONOMY/PROGRESSION pillar that this recalibration contradicts, and no P0 entry implicated. This
plan independently confirms that finding stands (no new evidence surfaced during planning that
changes this) — Steps 2-6 above are the complete edit set for this ticket, no seventh file.
**Do NOT touch:** Any file under `docs/parity_ledger/`.
**Verify:** N/A (no edit made; nothing to test). If Implement's own re-check of
`docs/parity_ledger/` during implementation surfaces a specific numeric claim investigation.md
missed, stop and flag it rather than silently editing or silently ignoring it.

## Scope Guards

- Do not touch `hero_guild_routing_seed456_500t`'s or `simq_routing_test_seed456_500t`'s COMBAT or
  WORLD fields in `grade_anchors.json` — both already correctly, automatically explained by
  `tools/simq_ceiling.py`'s computed `flag_gated`/`tick_budget` classifiers.
- Do not add a `SCORE_TOLERANCE_OVERRIDES` entry (`tests/simulation_quality/
  test_grade_regression.py:90-96`) for either run_key/pillar — would break
  `test_score_tolerance_override_table_scoped_to_named_pillars`'s exact-5-entry assertion
  (investigation.md Risk #2).
- Do not delete or overwrite the existing `simq_routing_test_seed42_500t`/`_seed123_500t`
  `watchdog_variance` entries, or the `NARRATIVE`/`corrected` or `urban_political_seed456_500t`
  entries, in `score_ceilings.json` — Step 4's new entry is additive only.
- Do not touch AGENCY or COGNITION on either run_key in `grade_anchors.json` — both already
  correctly sit at `C`/`0.0` from the parent ticket's own recalibration.
- Do not edit `src/ai/goals/scorers.py`'s `HarvestScorer`, `src/ai/goals/
  region_stabilization_scorer.py`, `src/systems/strategic_systems/intelligence.py`, or any other
  production code — this is a recalibration-and-disclose ticket only.
- Do not run `tools/calibrate_simq.py` with a DEBUG log handler attached and commit its output as
  the official recalibration numbers (investigation.md Risk #4) — Step 1 must use clean,
  non-instrumented runs only.
- Do not silently rewrite the historical tables in `docs/simulation_quality/
  eval_matrix_results.md` (lines 382-393, 1450-1462) — disclose via new dated NOTE blocks only
  (Step 6).
- Do not add/remove a run_key entry in `grade_anchors.json` (would break
  `test_grade_anchors_entry_count_unchanged`'s 81-entry assertion) or add more than the one
  specified `score_ceilings.json` entry.

## Dependency Map

- Step 1 (fresh clean calibration) must complete before Steps 2 and 3 (both consume its confirmed
  values).
- Steps 2, 3, and 4 are independent of each other (disjoint fields/files) and can be done in any
  order, but all three should land before Step 7 (verification needs all fixture edits present).
- Step 5 and Step 6 are independent of Steps 2-4's mechanics (they disclose the same root cause in
  prose) but should reference the exact final values Steps 2-3 wrote — sequence Step 6 after Steps
  2-3 land so the NOTE blocks can copy-paste the committed numbers rather than retype them.
  Step 5 has no numeric dependency (it discloses the mechanism, not specific score values) and can
  be done any time.
- Step 8 has no dependency on any other step (it is a confirmation that no action is needed).
- Step 7 depends on Steps 1-4 all being complete; it does not depend on Steps 5, 6, or 8.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: Root cause of `hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION drift confirmed via direct evidence | Already satisfied by investigation.md Finding 1 (DEBUG-trace, 371 goal-selection decisions, 1/371 HARVESTING win rate) — no plan step required; this plan's Step 5 discloses it in `intentional_divergences.md` | N/A (investigation-phase evidence, not a runtime test) |
| AC2: Root cause of `simq_routing_test_seed456_500t` PROGRESSION drift confirmed via direct evidence | Already satisfied by investigation.md Finding 1 (1/335 HARVESTING win rate) + Finding 2 (6-trial bimodal watchdog_variance evidence) — no plan step required; Step 5 discloses Finding 1, Step 4 encodes Finding 2 | N/A (investigation-phase evidence) |
| AC3: `grade_anchors.json` and/or `score_ceilings.json` updated to reflect confirmed current, correctly-classified values for both run_keys | Steps 1 (source values), 2, 3 (`grade_anchors.json`), 4 (`score_ceilings.json`) | `test_grade_anchor_file_exists_and_valid`, `test_grade_anchors_entry_count_unchanged`, `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`, all 6 existing `tests/tools/test_score_ceilings.py` tests |
| AC4: scoped pytest command shows 0 unexplained failures | Step 7 (textual interpretation, not exit code) | `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"` — pass condition is "every `score_failures` line carries a `[known ...]` annotation", not exit code 0 |

## Anti-Drift Notes

- **AC4's command will not exit 0 — this is expected, not a leftover gap.** Both run_keys carry
  pre-existing, already-`[known ...]`-annotated failures (COMBAT on both, WORLD on
  `hero_guild_routing_seed456_500t`, and possibly PROGRESSION itself on `simq_routing_test_
  seed456_500t` on an unlucky future draw) that are out of this ticket's scope and correctly
  disclosed by the automated `simq_ceiling.py` classifier or Step 4's new fixture entry. Implement
  and Verify must read the actual `score_failures` text, not the pytest exit code.
- **The `simq_routing_test_seed456_500t`/PROGRESSION anchor value is a judgment call, not a
  mechanically-derived fact** — see "Decision on Open Question" above. If a future re-run's modal
  split flips (e.g. 3/5 becomes the `-0.1548` state instead), that is itself new `watchdog_variance`
  evidence, not proof this plan's choice was wrong; do not react to a single future draw by
  re-flipping the anchor without a comparable multi-trial evidentiary basis.
- **`hero_guild_routing_seed456_500t` and `simq_routing_test_seed456_500t` are two structurally
  distinct findings sharing one root-cause *family*, not one finding**: the former is deterministic
  (Finding 1 only, no watchdog jitter observed), the latter combines Finding 1 (suppression) and
  Finding 2 (jitter on top of the suppression) — do not conflate them into a single "same bug, same
  fix" mental model when writing the disclosure prose in Steps 5-6.
- **This ticket's root cause is the same *family* as, but mechanistically distinct from, the sibling
  `ADVENTURE_ROUTE` finding** (`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`):
  `HARVESTING`'s formula is distance-decayed (`50.0/dist`), not scale-capped
  (`_ADVENTURE_ROUTE_SCORE_MAX=2.9`) — Step 5's prose must preserve this distinction, not blur the
  two into one mechanism.
- **No code-level bug exists or is being proposed** — both findings are downstream consequences of
  already-shipped, already-reviewed strategic-cognition behavior (§2.40/§2.41/§2.42/§2.43's
  GoalScorer-wrapper migrations) interacting with these two worlds' specific danger/hostile density.
  Any future code-level rebalancing is explicitly out of this ticket's scope.

## Unresolved Questions

None blocking Implement. The one open call flagged by investigation.md (Risk #1, the
`simq_routing_test_seed456_500t`/PROGRESSION anchor value) is resolved above under "Decision on Open
Question" — Implement should proceed with `-0.2359249329758713` unless Step 1's fresh confirming run
surfaces evidence materially inconsistent with investigation.md's 5-trial sample (e.g., a third,
previously-unseen state), in which case Implement must stop and escalate rather than deciding
unilaterally.
