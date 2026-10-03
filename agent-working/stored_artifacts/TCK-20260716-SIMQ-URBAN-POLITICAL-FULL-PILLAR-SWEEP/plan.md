---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP
artifact_type: plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Implementation Plan — TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP

## Summary

`investigation.md`'s 8-fresh-draw full-pillar sweep of `urban_political_seed123_1000t`
confirms 8 of 10 pillars need no change (AGENCY, COMBAT, ECONOMY, FACTION, INFORMATION,
PROGRESSION, WORLD, NARRATIVE — the last two via their existing overrides, re-validated
adequate) and 2 pillars need new `SCORE_TOLERANCE_OVERRIDES` entries: SOCIAL
(`abs_floor=5.003`, derived from combined 11-draw evidence) and COGNITION
(`abs_floor=2.0435`, derived from this session's 8 draws, applied as a plain override
with an explicit width caveat — see Decision section below). This plan adds exactly
those 2 entries to the existing 3-entry table, updates the table's anti-drift guard and
stale comments to match, proves the fix against fresh real calibration data via the
AC-mandated slow test, and appends (never edits) resolution text to
`docs/parity_ledger/infrastructure.yaml` and `docs/simulation_quality/eval_matrix_results.md`.
No engine code, `grade_anchors.json`, or existing `grade_stability` guard is touched.

## Decision

Both of `investigation.md`'s Risk/Open-Question items are resolved here, using the
ticket's own Scope/Out-of-Scope/Assumptions text as the deciding authority — mirroring
how the parent ticket's plan.md resolved its own "SOCIAL Finding Decision" rather than
escalating.

### Decision 1 — COGNITION remedy shape: plain override (option a), not a new guard

`investigation.md` Risk #1 poses two paths: (a) apply `SCORE_TOLERANCE_OVERRIDES` with
`abs_floor=2.0435` and an honest width caveat, or (b) add a new dedicated 3-trial-mean
`grade_stability` guard instead, since COGNITION's no-dedup-gate refire mechanism is
architecturally distinct from the bounded cascading-divergence mechanism the other
overridden pillars share.

The ticket's own Out of Scope section gates option (b) explicitly: "Adding a new
dedicated `grade_stability` guard for any pillar unless this ticket's own investigation
evidence specifically shows the tolerance-override alone is inadequate." The evidence in
`investigation.md` does not show the override is inadequate — it shows the override
*works* (the derived floor covers the observed spike, `2.0435 > 1.6159` max deviation)
but is wide relative to the anchor. "Wide" and "inadequate" are not the same claim: the
override still discriminates a genuine defect (any score outside roughly [-2.0, +2.08]
would still fail), it just cannot discriminate a *worse* future spike from a moderate
one. That is a real limitation, but it is not evidence the mechanism fails at its actual
job (catching regressions against this test's own AC). Per the Out-of-Scope gate, option
(b) is therefore not authorized by this ticket's evidence; choosing it here would be new
scope requiring separate sign-off, which the ticket explicitly reserves as future work,
not something this planner unilaterally grants itself.

**Decision: apply option (a).** Add `("urban_political_seed123_1000t", "COGNITION"):
2.0435` to `SCORE_TOLERANCE_OVERRIDES`, with the width caveat recorded verbatim in the
ticket's Implementation Notes and in the module comment above the table (see Step 2) so
a future reader does not mistake the wide floor for an unexamined oversight. If a future
draw shows this floor is genuinely inadequate (a spike exceeding `2.0435`), that is new
evidence for a follow-up ticket to consider option (b) — not a retroactive failure of
this decision.

### Decision 2 — SOCIAL evidence base: combined 11-draw (3 historical + 8 fresh), not this-session-only

`investigation.md` Risk #2 notes this session's 8 draws alone (max deviation `3.2135`)
would conclude "no override needed," and only combining with the parent ticket's 3
historical draws (max deviation `3.8485`) crosses the current default tolerance
(`3.5931`).

The ticket's Scope instructs checking each pillar's exposure "against `grade_anchors.
json`... using real evidence," not "using only this session's draws." The Assumptions
section explicitly cites the NARRATIVE override's own derivation — 6 draws, 3 historical
+ 3 fresh — as the established precedent this ticket should follow, and the existing
module comment in `test_grade_regression.py` (lines 62-69) confirms NARRATIVE's
`abs_floor=0.3197` was derived exactly that way. Combining sessions' independent draws
for the same `(run_key, pillar)` pair is therefore the established, sanctioned
methodology in this codebase, not a novel interpretation this planner is introducing.
Discarding the historical draw because it happened in a different session would be
inconsistent with that precedent and would also mean silently ignoring a documented,
real exceedance (`21.814` actual vs `17.9655` anchor) that is sitting in a stored,
citable artifact (`stored_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-
TOLERANCE/investigation.md`).

**Decision: use the combined 11-draw evidence base.** Add
`("urban_political_seed123_1000t", "SOCIAL"): 5.003` to `SCORE_TOLERANCE_OVERRIDES`
(`round(1.3 * 3.8485, 4) = 5.0031` → `investigation.md` states `5.003`; Step 2 below
uses the investigation's stated value and the implementer must re-derive and confirm the
rounding matches before committing — see Step 2's Verify note). Implementation Notes
must record that the evidence basis is the combined 11-draw set, not this session's 8
alone, so a future reader is not misled into thinking this session's data alone
justified it.

## Steps

### Step 1 — Regenerate default-path calibration data for the AC-mandated proof
**Files:** `data/calibration/urban_political_seed123_1000t/quality_report.json`
(generated artifact, gitignored — not a source-code change)
**Change:** Run
`.venv/bin/python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`
with **no** custom `--output`, so the report lands at the default path
`test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` reads from
(currently stale from the parent ticket's own regen — must be fresh so the AC's "not
skipped, against freshly regenerated real calibration data" requirement is met by data
generated *after* Step 2/3's table edit exists, i.e. re-run this after Step 3, not
before — see Dependency Map).
**Do NOT touch:** `data/runs/` cleanup timing — leave `data/runs/` output from this run
in place until all steps are verified; do not `rm -rf` mid-sequence.
**Verify:** File exists and is valid JSON; `normalized_score` present for all 10
pillars.

### Step 2 — Add COGNITION and SOCIAL entries to `SCORE_TOLERANCE_OVERRIDES`
**Files:** `tests/simulation_quality/test_grade_regression.py` (lines ~46-79)
**Change:**
- Add two entries to the `SCORE_TOLERANCE_OVERRIDES` dict (lines 75-79), leaving the 3
  existing entries byte-identical:
  ```python
  SCORE_TOLERANCE_OVERRIDES: dict[tuple[str, str], float] = {
      ("urban_political_seed123_1000t", "ECONOMY"): 0.2878,
      ("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351,
      ("urban_political_seed123_1000t", "NARRATIVE"): 0.3197,
      ("urban_political_seed123_1000t", "COGNITION"): 2.0435,
      ("urban_political_seed123_1000t", "SOCIAL"): 5.003,
  }
  ```
- The module comment block directly above (lines 49-74) contains two now-stale claims
  that must be corrected in the same edit, not left contradicting the table:
  1. The paragraph starting "`urban_political_seed123_1000t/SOCIAL` is intentionally
     NOT in this table..." (lines 71-74) must be replaced — SOCIAL is now in the table.
     Replace with a short paragraph stating the combined-evidence derivation from
     Decision 2 above: 11 independent fresh draws (3 historical from
     `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`, 8 fresh from this
     ticket's session), max observed deviation `3.8485` (from a historical draw),
     `round(1.3 * 3.8485, 4) = 5.003`, anchor not re-centered, citing this ticket ID.
  2. Add a new paragraph documenting COGNITION's derivation and the Decision 1 caveat:
     8 fresh draws this session, max observed deviation `1.6159`,
     `round(1.3 * 1.6159, 4) = 2.0435`, anchor not re-centered, plus one sentence
     stating explicitly that this floor is wide relative to the anchor (`0.0440`)
     because COGNITION's `decision_divergence_detected` event has no dedup gate and
     can refire every tick (cite `src/observability/event_extractor.py:477-496`), so
     the floor bounds this session's observed spikes but is not a hard ceiling on the
     mechanism's worst case — matching Decision 1's reasoning verbatim, not a
     softened restatement.
- Do not reorder the 3 existing dict entries; append the 2 new ones after them so the
  diff is minimal and reviewable.
**Do NOT touch:** The 3 existing entries' keys or values; `SCORE_TOLERANCE_ABS_FLOOR` /
`SCORE_TOLERANCE_REL_PCT` (lines 46-47); `_score_tolerance_kwargs()` (lines 82-86, no
code change needed — it already generically looks up any table entry).
**Verify:** `git diff tests/simulation_quality/test_grade_regression.py` shows only the
comment-block rewrite and the 2 new dict lines; no other lines changed.

### Step 3 — Update the anti-drift guard to the final 5-entry set
**Files:** `tests/simulation_quality/test_grade_regression.py` (lines ~616-627,
`test_score_tolerance_override_table_scoped_to_named_pillars`)
**Change:**
- Update the hard-coded `set(SCORE_TOLERANCE_OVERRIDES.keys()) == {...}` assertion to
  the 5-entry set (3 existing + COGNITION + SOCIAL from Step 2).
- Update the function's docstring, which currently reads "the override table contains
  exactly the 3 evidence-derived entries (SOCIAL intentionally excluded, see module
  comment)" — this sentence is now false on both counts (5 entries, SOCIAL included).
  Replace with a docstring reflecting the 5-entry set and dropping the
  now-inapplicable "SOCIAL intentionally excluded" clause.
- No other test in this file needs edits: `test_score_tolerance_overrides_do_not_affect_
  unlisted_anchors` (lines 638-652) is self-adjusting and requires no change.
**Do NOT touch:** The widen-only invariant assertion body (`assert abs_floor >
default_width`, lines 630-633) — this logic is generic and already covers the 2 new
entries without modification; do not duplicate or special-case it per entry.
**Verify:**
`.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v`
passes.

### Step 4 — Run the fast structural/anti-drift test surface
**Files:** none changed in this step (verification only)
**Change:** Run the fast commands from `test_plan.md`'s "Scoped Pytest Commands"
section:
```bash
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k "test_grade_within_anchor_band and not long_run" -v
```
(`test_grade_anchor_file_exists_and_valid` may fail on the pre-existing, documented
`hero_guild_routing_seed42_1000t` local-data dependency per `test_plan.md` — not a
regression this ticket introduces; do not attempt to fix it.)
**Do NOT touch:** Any file to make the pre-existing `hero_guild_routing` dependency
pass — out of scope, documented pre-existing gap.
**Verify:** All listed commands pass (the pre-existing known exception aside).

### Step 5 — Prove the fix against fresh real calibration data (AC-mandated)
**Files:** none changed (verification only); depends on Step 1's regenerated data being
current as of *after* Step 2/3's table edit
**Change:** Run
```bash
.venv/bin/python3 -m pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v
```
This must report `1 passed` (not skipped). Per `test_plan.md`'s documented residual
risk, if the regenerated draw happens to land in a COGNITION spike case, the new
`abs_floor=2.0435` override should still cover it; if it fails anyway, re-run once
(regenerate via Step 1's command again, since F6-class variance means each run is a
fresh draw) before treating it as a real defect, and record the outcome either way in
Implementation Notes.
Also confirm the untouched precedent guard remains green:
```bash
.venv/bin/python3 -m pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" -m slow --resource-budget large -v
```
**Do NOT touch:** `test_corpus_diversity.py` — run only, never edit.
**Verify:** Both commands above report passing (1 passed each, non-skip for the first).

### Step 6 — Append resolution text to the parity ledger (append-only)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:**
- `INFRA-272` (lines ~4202-4319): append a new dated paragraph to the existing
  `v2_evidence` block (after the existing "RESOLVED 2026-07-16
  (TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE)" / "HONEST DISCLOSURE, NOT
  RESOLVED (SOCIAL)" text at lines ~4288-4312), following the exact append style already
  used there (`RESOLVED 2026-07-16 (TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-
  SWEEP): ...`). Content: full 10-pillar sweep result — SOCIAL (`abs_floor=5.003`,
  combined 11-draw evidence) and COGNITION (`abs_floor=2.0435`, 8-draw evidence, width
  caveat noted per Decision 1) now overridden; AGENCY, COMBAT, FACTION, INFORMATION,
  PROGRESSION, WORLD confirmed need none; ECONOMY and NARRATIVE's existing overrides
  re-confirmed adequate. Cite the guarding tests
  (`test_score_tolerance_override_table_scoped_to_named_pillars`,
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`) and the
  `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` pass result
  from Step 5.
- `INFRA-273` (lines ~4321 onward, `v2_evidence` field): append a short `UPDATE
  2026-07-16 (TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP)` paragraph noting
  (a) COMBAT/PROGRESSION/WORLD were checked for this anchor for the first time and
  confirmed small/bounded (consistent with the existing mechanism-2 claim), and (b) this
  investigation's COGNITION finding is new evidence that mechanism-1 (no-dedup-gate
  refire, previously characterized only by `TCK-20260713-SIMQ-COGNITION-LOOPDET-
  NONDETERMINISM` for a different anchor) can also manifest at large single-draw
  magnitude on an anchor/tier that ticket never swept — cross-reference, do not restate
  or contradict the existing mechanism-1/mechanism-2 distinction already in the entry's
  `text` field.
- Both edits go in the `v2_evidence` field only (matching the file's established
  append-only pattern for these two entries); `text`, `status`, `priority`,
  `divergence_note`, and `support_boundary` fields are not touched for either entry.
**Do NOT touch:** Any other `INFRA-*` entry in this file; do not rewrite or delete any
existing sentence in `INFRA-272` or `INFRA-273`'s `v2_evidence` — append only.
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses cleanly; manual diff review shows only additions (no deletions/edits) inside
`INFRA-272`/`INFRA-273`.

### Step 7 — Append summary to the eval matrix results doc
**Files:** `docs/simulation_quality/eval_matrix_results.md`
**Change:** Append a new `## Anchor Reliability Verification, Part 5
(TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP)` section after the existing
"Part 4" section (ends at line ~2264, immediately before "## FACTION Coverage Closure —
Phase 3"), following Part 4's established prose style (see Part 4, lines 2220-2264, as
the direct style template): state the 8-fresh-draw sweep, the per-pillar table
(reuse `investigation.md`'s table), the two Decision outcomes (SOCIAL combined-evidence
override, COGNITION plain-override-with-caveat), the confirmed-fine pillars, and the
`test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` pass result from
Step 5. This closes out the "SOCIAL... tracked in a named follow-up ticket" reference
Part 4 itself made.
**Do NOT touch:** Any existing section (Part 1-4 or any later section); insert only, do
not renumber or restructure existing Parts.
**Verify:** Manual review — new section present, existing sections byte-identical
(`git diff` shows only an insertion block).

### Step 8 — Cleanup generated/local artifacts
**Files:** `data/calibration/`, `data/runs/`, `reports/release_proof/` (none of these
are committed to git — cleanup is local hygiene only, not a diff-producing step)
**Change:** `rm -rf data/calibration/* data/runs/* reports/release_proof/*` per the
environment note and `test_plan.md`'s post-verification cleanup command, run only after
Steps 1-7 are all verified complete.
**Do NOT touch:** Anything under `stored_artifacts/`, `staging_artifacts/`, or
`tickets/` in this cleanup — scoped exactly to the 3 named generated-data directories.
**Verify:** `git status --porcelain data/ reports/` shows no output (nothing tracked was
touched; these directories are gitignored).

## Scope Guards

- Do not touch `src/engine/kernel.py` (F6 watchdog/throttle — read-only reference only,
  per ticket Out of Scope).
- Do not touch any of the 14 existing `grade_stability` guards in
  `tests/unit/worldassembly/test_corpus_diversity.py`, including
  `test_urban_political_seed123_1000t_social_economy_grade_stability` — run only, never
  edit.
- Do not touch `tests/simulation_quality/fixtures/grade_anchors.json` — no re-centering
  for SOCIAL or COGNITION (Decision 1 and 2 both explicitly keep the anchor as-is; see
  Anti-Drift Notes).
- Do not widen `SCORE_TOLERANCE_ABS_FLOOR` or `SCORE_TOLERANCE_REL_PCT` module-level
  defaults — all changes stay scoped to the per-`(run_key, pillar)` override table.
- Do not modify the 3 existing `SCORE_TOLERANCE_OVERRIDES` entries' keys or values
  (ECONOMY, `frontier_marches_seed42_200t`/NARRATIVE, `urban_political_seed123_1000t`/
  NARRATIVE) — this session's evidence re-confirms all three remain adequate.
- Do not add a new dedicated `grade_stability` guard for COGNITION (Decision 1 above) —
  the ticket's Out of Scope gate for this is not met by the current evidence.
- Do not touch the CI isolation lane (`.github/workflows/test.yml`'s `slow` job,
  `simq-corpus-diversity-slow-isolated` Makefile target,
  `tests/static/test_corpus_diversity_ci_isolation.py`).
- Do not rewrite or delete any existing sentence in `docs/parity_ledger/
  infrastructure.yaml` or `docs/simulation_quality/eval_matrix_results.md` — append
  only, per the established pattern both files already use for this ticket chain.
- Do not sweep any anchor besides `urban_political_seed123_1000t`.

## Dependency Map

- Step 2 and Step 3 must both land before Step 4/5 run (the table and its anti-drift
  guard must agree, or Step 3's own test fails).
- Step 1's calibration regen must be **re-run after** Step 2/3 (not just once at the
  start) so Step 5's proof run consumes both the new override table *and* fresh data —
  order matters: Step 1 (initial, optional early sanity check) → Step 2 → Step 3 → Step
  1 again (fresh regen) → Step 5. The plan numbers Step 1 first for readability, but the
  implementer must regenerate calibration data a second time immediately before Step 5
  if Step 1 was run before Step 2/3.
- Step 4 has no dependency on Step 1's data (fast tests don't touch calibration data)
  and can run any time after Step 2/3.
- Step 6 and Step 7 depend on Step 5's actual pass result (they cite it) — run after
  Step 5, not before.
- Step 8 depends on all prior steps being verified complete.
- All other steps are independent of each other in content (each touches a disjoint
  file/section).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| 5+ independent fresh draws collected, all 10 pillars recorded in investigation.md | Already satisfied by investigation.md (8 draws) — no plan step needed | Manual table review (done) |
| Each pillar's max deviation computed and compared to current tolerance, explicit pass/fail | Already satisfied by investigation.md's determination table | Manual review (done) |
| Every pillar exceeding tolerance gets a `SCORE_TOLERANCE_OVERRIDES` entry via 1.3x formula | Step 2 | `git diff` review of the dict + comment block |
| `test_score_tolerance_override_table_scoped_to_named_pillars` updated to final entry set and passes | Step 3 | `pytest ...::test_score_tolerance_override_table_scoped_to_named_pillars -v` |
| `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` reports `1 passed` against fresh real data | Step 1 (regen) + Step 5 | `pytest ... -m slow --resource-budget large -v` |
| `INFRA-272` appended with resolution paragraph; `INFRA-273` cross-referenced | Step 6 | YAML parse check + manual diff review |
| `eval_matrix_results.md` appended with Part 5 summary | Step 7 | Manual diff review |
| `git diff --stat` shows `kernel.py`/`test_corpus_diversity.py` untouched; any `grade_anchors.json` change justified | Scope Guards (no step touches these files) | `git diff --stat -- src/engine/kernel.py tests/unit/worldassembly/test_corpus_diversity.py tests/simulation_quality/fixtures/grade_anchors.json` shows no output |

## Anti-Drift Notes

- The stale module comment at `test_grade_regression.py` lines 71-74 ("SOCIAL is
  intentionally NOT in this table... Do not add it without new evidence") **must** be
  rewritten in Step 2, not just left alongside the new SOCIAL entry — leaving both would
  make the file self-contradictory and mislead a future reader into thinking the SOCIAL
  entry was added in violation of the file's own stated policy, when in fact new
  evidence (per this ticket) is exactly what that comment said would justify it.
- The docstring on `test_score_tolerance_override_table_scoped_to_named_pillars`
  ("contains exactly the 3 evidence-derived entries... SOCIAL intentionally excluded")
  is equally stale and must be corrected in Step 3, in the same change as the assertion
  itself — do not update the assertion set without updating the docstring that describes
  it, or the two will disagree.
- COGNITION's override (`abs_floor=2.0435`) is deliberately wide (46x the anchor's own
  value). This is a known, documented tradeoff (Decision 1), not an error — do not
  "fix" it by narrowing the value without new evidence, and do not silently drop the
  width caveat from the module comment or Implementation Notes when writing them up.
- SOCIAL's override (`abs_floor=5.003`) is derived from evidence spanning two sessions
  (3 historical + 8 fresh = 11 draws), not this session's 8 draws alone (Decision 2) —
  Implementation Notes must state this plainly so a future reviewer checking only this
  session's raw data does not conclude the override lacks justification.
- Both `infrastructure.yaml` edits (Step 6) and the `eval_matrix_results.md` edit (Step
  7) are append-only by established convention in this file/ticket chain — verify via
  `git diff` that no existing line was altered, only new lines added, before considering
  either step complete.
- `data/calibration/` and `data/runs/` are gitignored; regenerating calibration data
  (Steps 1 and 5's precondition) never produces a stageable diff — do not accidentally
  `git add` anything under `data/`.

## Deviations

- **Step 1's "Do NOT touch: data/runs/ cleanup timing" guard was violated out of
  necessity, not choice.** At the start of implementation the environment had 0 bytes
  of disk free (`df -h /` showed `100% ... 0 Avail`), which made even a small `Edit`
  tool write to `test_grade_regression.py` fail with `ENOSPC`. To unblock any file
  writes at all, `data/calibration/*`, `data/runs/*`, and `reports/release_proof/*`
  (115 stale calibration directories, ~203M, all gitignored generated data from prior
  sessions, none of it this ticket's own in-progress run) were cleared **before** Step 2
  landed, not after Step 5 as the plan's Dependency Map specifies. This is a deviation
  from the plan's literal step ordering, but not from its intent or outcome: Step 1's
  actual calibration regen was still run fresh, still run only once, and still run
  strictly after Step 2/3's table edit landed (per the Dependency Map's core
  requirement), so Step 5's proof test still consumed data generated after the new
  override table existed. No tracked/stageable file was affected by the early cleanup
  (`data/`, `reports/` are gitignored). Step 8's own cleanup was still performed
  separately, after all steps were verified complete, per the plan.
- No other deviation from plan.md's 8 steps, Scope Guards, or Decision sections. All
  derived values (COGNITION `abs_floor=2.0435`, SOCIAL `abs_floor=5.003`) were
  independently re-derived and matched the plan's stated values exactly before
  committing (Step 2's Verify note).
