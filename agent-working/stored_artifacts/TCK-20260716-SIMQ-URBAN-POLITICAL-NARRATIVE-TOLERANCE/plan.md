---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE
artifact_type: plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Implementation Plan — TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE

**Plan Amendment (post first Review round):** architecture-reviewer found one fixable
violation, corrected in place below rather than as a separate addendum: Steps 6-7's SOCIAL
finding disclosure was specific and non-vague on the numbers (anchor
`urban_political_seed123_1000t`, pillar SOCIAL, delta 3.8485 vs. tolerance width 3.5931) but
stopped at a prose recommendation ("the next ticket in this chain should be scoped as...")
without actually filing a ticket — the identical gap-shape that blocked the parent ticket's
first Verify pass (`agent-monitoring/events.jsonl` seq 9: "new NARRATIVE pillar gap had no
follow-up ticket reference"). This is now fixed: a concrete stub follow-up ticket has been
filed — `TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`
(`tickets/inprogress/TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP.md`, validated
frontmatter, standard tier, P2), scoped exactly per this plan's own recommendation (full-pillar
sweep of `urban_political_seed123_1000t`: SOCIAL/COMBAT/PROGRESSION/WORLD, applying the same
`SCORE_TOLERANCE_OVERRIDES` mechanism where evidence supports it). Steps 6 and 7 below, and the
SOCIAL Finding Decision section, are updated to cite this concrete ticket ID by name instead of
vague "next ticket in this chain" language. Steps 1-5 (the actual NARRATIVE override
implementation) are unaffected by this fix and remain exactly as they were.

## Summary

Investigation confirmed the `urban_political_seed123_1000t`/NARRATIVE variance is genuine
F6-class cascading divergence (`INFRA-273`'s delta-gated `event_extractor.py` mechanism,
`hero_death_unrecorded` specifically), not a distinct bug, using 6 total real draws (3 from
the parent ticket + 3 fresh this session), max deviation 0.2459. This plan adds a 3rd
`SCORE_TOLERANCE_OVERRIDES` entry — `("urban_political_seed123_1000t", "NARRATIVE"):
0.3197` — derived by the same `1.3x max-observed-deviation` formula already verified against
both existing table entries, confirms it via fresh non-skip calibration data, updates the
anti-drift guard's expected-set assertion, and appends resolution pointers to `INFRA-272`
and `eval_matrix_results.md`. No new `grade_stability` guard is added (confirmed below —
6 real draws already ground the floor, and the guard mechanism is not immune to the same
session-load drift anyway). The investigation's new SOCIAL finding (1/3 fresh draws exceeds
SOCIAL's existing default tolerance for this same anchor) is disclosed in this ticket's
docs/parity-ledger append and Implementation Notes but is **not** folded into this ticket's
diff — see the SOCIAL Finding Decision section below for the reasoned call on scope and on
how the *next* ticket in this chain should be shaped differently to break the
one-new-pillar-per-ticket pattern.

## Steps

### Step 1 — Regenerate fresh calibration data at the default path
**Files:** none (local scratch data only; `data/calibration/` is gitignored)
**Change:** Run `python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks
1000` with no custom `--output`, so the report lands at
`data/calibration/urban_political_seed123_1000t/quality_report.json`. This is a prerequisite
for Step 5's verification — without it, `test_grade_within_anchor_band_long_run[urban_political_
seed123_1000t]` `pytest.skip()`s rather than actually exercising the fix. Confirm the report's
NARRATIVE score lands inside the recommended 0.3197 floor before proceeding (sanity check,
not a hard gate — investigation already confirmed 6/6 draws fit).
**Do NOT touch:** any other anchor's calibration data; do not use a custom `--output` path
(the default path is required for the parametrized test to find it).
**Verify:** `data/calibration/urban_political_seed123_1000t/quality_report.json` exists and
is well-formed JSON with a NARRATIVE pillar entry.

### Step 2 — Add the 3rd `SCORE_TOLERANCE_OVERRIDES` entry
**Files:** `tests/simulation_quality/test_grade_regression.py` (lines 49-68)
**Change:**
- Add `("urban_political_seed123_1000t", "NARRATIVE"): 0.3197` to the
  `SCORE_TOLERANCE_OVERRIDES` dict (currently lines 65-68).
- Update the module comment block immediately above the dict (lines 49-64) to document the
  3rd entry's derivation: unlike the 2 existing entries (reused verbatim from a
  `grade_stability` guard's own `abs_floor`), this entry has no corresponding guard to reuse
  from — it is derived directly from 6 independent fresh calibration draws using the same
  `1.3x max-observed-deviation` formula (`round(1.3 * 0.2459, 4) = 0.3197`, anchor not
  re-centered — matches the ECONOMY precedent, not the frontier_marches-NARRATIVE
  re-centered precedent). Cite this ticket's investigation.md for the full 6-draw table.
- Leave the existing SOCIAL-exclusion sentence (lines 60-64) untouched — do not edit or annotate
  it in this file (see SOCIAL Finding Decision below for why the SOCIAL disclosure channel is
  the parity ledger / eval_matrix doc, not this comment).
**Do NOT touch:** the 2 existing entries' keys or values (`("urban_political_seed123_1000t",
"ECONOMY"): 0.2878` and `("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351` must remain
byte-identical); `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` module constants;
`_score_tolerance_kwargs()` or `_within_score_tolerance()` logic (both already generalize to
an arbitrary number of table entries, no code change needed there).
**Verify:** manual read-diff — 3 dict entries present, first 2 unchanged; no logic function
bodies touched.

### Step 3 — Update the anti-drift guard's expected-entry-set assertion
**Files:** `tests/simulation_quality/test_grade_regression.py`
(`test_score_tolerance_override_table_scoped_to_named_pillars`, lines 605-623)
**Change:** Update the hard-coded `set(SCORE_TOLERANCE_OVERRIDES.keys()) == {...}` assertion
(currently lines 610-613, 2-tuple set) to the 3-tuple set: add
`("urban_political_seed123_1000t", "NARRATIVE")` alongside the existing
`("urban_political_seed123_1000t", "ECONOMY")` and `("frontier_marches_seed42_200t",
"NARRATIVE")`. No other change to this test — the per-entry `abs_floor > default_width` loop
below the set assertion (lines 614-623) already generalizes to 3 entries with no logic edit.
**Do NOT touch:** `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` (lines
626-641) — it is self-adjusting (dynamically skips whatever is currently in the table) and
requires no edit.
**Verify:**
`pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v`
passes.

### Step 4 — Run the fast-tier and structural regression surface
**Files:** none (verification only)
**Change:** Run the fast, no-calibration-data-needed regression surface named in
test_plan.md's Scoped Pytest Commands:
```
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -v
pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -v
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v
pytest tests/simulation_quality/test_grade_regression.py -k "test_grade_within_anchor_band and not long_run" -v
```
**Do NOT touch:** nothing to change here — pure verification. If any of these fail, stop and
re-examine Step 2/3 before proceeding (do not proceed to the slow-tier check on a red fast
suite).
**Verify:** all listed commands pass (or skip where structurally expected, e.g. unrelated
fast-tier keys).

### Step 5 — Exercise the parametrized long-run case against real data
**Files:** none (verification only)
**Change:** Using the calibration data regenerated in Step 1, run:
```
pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v
```
Confirm it reports `1 passed`, not skipped, not failed. This is the AC-mandated proof that
the fix is actually exercised against fresh real data, not just structurally present in the
table.
**Do NOT touch:** do not regenerate calibration data for any other `SLOW_ANCHOR_KEYS` entry
as part of this step (out of scope; only this one anchor's data is required).
**Verify:** the command above shows `1 passed`. Additionally run the 2 named
`grade_stability` guards to confirm they are structurally untouched:
```
pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" -m slow --resource-budget large -v
pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_frontier_marches_seed42_200t_narrative_grade_stability" -m slow --resource-budget large -v
```
both pass unmodified.

### Step 6 — Append `INFRA-272`'s RESOLVED pointer for NARRATIVE and disclose the SOCIAL finding
**Files:** `docs/parity_ledger/infrastructure.yaml` (`INFRA-272` entry, `text` field, after the
existing "HONEST DISCLOSURE, NOT RESOLVED" block currently at lines 4276-4287)
**Change:** Append (do not remove or edit existing text) a new paragraph:
1. A `RESOLVED 2026-07-16 (TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE)` line
   mirroring the existing `RESOLVED` paragraph's style (lines 4269-4275): states
   `SCORE_TOLERANCE_OVERRIDES` now widens `urban_political_seed123_1000t`/NARRATIVE
   (`abs_floor=0.3197`, derived from 6 independent fresh draws, `1.3x` max-observed-deviation
   formula, anchor not re-centered), guarded by
   `test_score_tolerance_override_table_scoped_to_named_pillars` and
   `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`.
2. A new `HONEST DISCLOSURE, NOT RESOLVED (SOCIAL)` paragraph in the same style as the
   existing NARRATIVE disclosure it mirrors: states that this ticket's own fresh-draw
   gathering found 1 of 3 draws showing `urban_political_seed123_1000t`/SOCIAL exceeding its
   existing default tolerance (delta 3.8485 vs. width 3.5931), contradicting the prior
   ticket's "no override needed" finding; that no override or guard was added for it in this
   ticket (out of this ticket's authorized NARRATIVE-only scope); and that it is disclosed
   here with a concrete follow-up ticket already filed rather than dropped as a prose
   recommendation — cite **`TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`** by name (the
   same way this block's own NARRATIVE disclosure, in the existing "HONEST DISCLOSURE, NOT
   RESOLVED" paragraph above, names `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`
   itself as its follow-up), scoped as a full-pillar sweep of
   `urban_political_seed123_1000t`'s remaining untested-for-load-sensitivity pillars (COMBAT,
   PROGRESSION, WORLD — the other pillars `INFRA-273` names as sharing the same confirmed
   delta-gated cascading-divergence mechanism, per this anchor's `grade_anchors.json` entry
   having COGNITION, AGENCY, COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD,
   NARRATIVE as its 10 pillars), not a single-pillar SOCIAL-only ticket, given this is the 2nd
   consecutive investigation of this exact anchor to organically surface exactly one new flaky
   pillar.
**Do NOT touch:** any existing text in `INFRA-272` (the original text, the 2026-07-15 UPDATE,
the RESOLVED paragraph, or the original HONEST DISCLOSURE paragraph) — append-only, per the
project's parity-ledger convention. Do not touch `INFRA-273` (no update strictly required per
investigation — its existing text already covers the mechanism; this ticket's evidence is
consistent with, not contradicting, it).
**Verify:** `git diff docs/parity_ledger/infrastructure.yaml` shows only additive text inside
`INFRA-272`'s `text:` field; YAML still parses (`python3 -c "import yaml;
yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` succeeds).

### Step 7 — Append `eval_matrix_results.md` Part 4
**Files:** `docs/simulation_quality/eval_matrix_results.md` (after "Anchor Reliability
Verification, Part 3" section, currently ending around line 2219, before "FACTION Coverage
Closure — Phase 3")
**Change:** Append a new `## Anchor Reliability Verification, Part 4
(TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE)` subsection, following Part 3's
existing style: summarize the 3rd override entry (NARRATIVE, `abs_floor=0.3197`, 6-draw
evidence base), note the band check was never at risk (all 6 draws stayed within ±1 grade of
the anchor's B grade), and disclose the SOCIAL finding with the same "out of this ticket's
authorized scope to fix" framing Part 3 used for the NARRATIVE disclosure it is now
resolving — including the same concrete follow-up ticket citation from Step 6:
**`TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`** (full-pillar sweep, not
single-pillar), by name, not a vague "next ticket" reference.
**Do NOT touch:** Part 1, 2, or 3 sections, or any other section of this file (FACTION/
INFORMATION coverage closures, etc.).
**Verify:** manual read-diff — only an appended section, no edits to existing sections.

## Scope Guards

Explicit list of things this plan must not touch (derived from the ticket's Out of Scope and
investigation.md's Anti-Drift Hazards):

- `src/engine/kernel.py` — the tick-budget watchdog / mid-tick emergency throttle mechanism.
  F6 is documented, intentional engine behavior; no code-level fix is in scope.
- The 14 existing `grade_stability` guards in `tests/unit/worldassembly/
  test_corpus_diversity.py` (including `test_urban_political_seed123_1000t_social_economy_
  grade_stability` and `test_frontier_marches_seed42_200t_narrative_grade_stability`) — must
  remain byte-identical; no new guard is added for NARRATIVE (see recommendation confirmation
  below) or for SOCIAL (deferred to a future ticket).
- `tests/simulation_quality/fixtures/grade_anchors.json` — no anchor value re-centered, no
  entry added/removed. The NARRATIVE anchor for `urban_political_seed123_1000t` stays at its
  original committed `0.6603206412825652`.
- The 2 existing `SCORE_TOLERANCE_OVERRIDES` entries' keys and values — byte-identical.
- `urban_political_seed123_1000t`/SOCIAL — no override entry, no guard edit, no anchor
  change. Disclosed in docs only (Steps 6-7), per the SOCIAL Finding Decision below.
- `SCORE_TOLERANCE_ABS_FLOOR` / `SCORE_TOLERANCE_REL_PCT` module-level defaults — unchanged.
- `.github/workflows/test.yml`, `Makefile`'s `simq-corpus-diversity-slow-isolated` target,
  `tests/static/test_corpus_diversity_ci_isolation.py` — CI isolation wiring, a separate
  already-closed concern.
- Any anchor/pillar pair not named in this ticket — no corpus-wide sweep.
- Existing text in `INFRA-272`/`INFRA-273`/`eval_matrix_results.md` Parts 1-3 — append-only.

## Dependency Map

- Step 1 (regenerate calibration data) is independent and can run first or in parallel with
  Step 2.
- Step 2 (add override entry) must precede Step 3 (update guard's expected-set assertion) —
  Step 3's assertion will fail against a 2-entry table without Step 2's edit.
- Step 4 (fast-tier verification) depends on Steps 2-3 (exercises the edited table and
  updated guard).
- Step 5 (long-run parametrized verification) depends on Step 1 (needs real calibration data)
  and Steps 2-3 (needs the override wired in and the guard updated) — run after Step 4 passes
  clean, not before.
- Steps 6-7 (doc/parity updates) depend on Step 5 passing — do not claim resolution in
  `INFRA-272`/`eval_matrix_results.md` before the fix is actually verified against real data.
- Steps 6 and 7 are independent of each other and can be done in either order.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| ≥2 additional independent fresh draws collected, NARRATIVE recorded | Pre-planning (investigation.md, already satisfied — 3 fresh draws this session, 6 total) | N/A — evidence already gathered and cited in investigation.md |
| Investigation concludes F6-class vs. distinct root cause, recorded in Implementation Notes | Pre-planning (investigation.md conclusion (a): F6-class, confirmed) | N/A — carry investigation.md's conclusion into ticket's Implementation Notes at close |
| 3rd `SCORE_TOLERANCE_OVERRIDES` entry added with evidence-derived `abs_floor`; parametrized long-run test passes against fresh real data | Steps 1, 2, 5 | `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` (`-m slow --resource-budget large`) |
| If not F6-class: alternative fix designed/implemented/verified | N/A — investigation confirmed F6-class; this branch does not apply | N/A |
| Anti-drift guard tests pass, reflect 3-entry table | Step 3 | `test_score_tolerance_override_table_scoped_to_named_pillars` |
| `test_within_band_default_tolerance_unchanged`, `test_grade_anchors_entry_count_unchanged` unmodified in behavior | Step 4 (verification only, no edit) | both named tests, run in Step 4 |
| `INFRA-272` updated with RESOLVED pointer; `eval_matrix_results.md` updated | Steps 6, 7 | manual read-diff (YAML parse check for Step 6) |
| `git diff --stat` shows no change to `kernel.py`, 14 guards, 2 precedent guards, 2 existing override values, or SOCIAL — unless explicitly justified | All steps (scope discipline); SOCIAL explicitly justified-but-disclosed-not-fixed per Step 6/7 (touches only doc text, not the override table, guard, or anchor) | `git diff --stat -- tests/unit/worldassembly/test_corpus_diversity.py tests/simulation_quality/fixtures/grade_anchors.json src/engine/kernel.py` (must be empty) |

## SOCIAL Finding Decision

**Decision: (b), sharpened — disclose now, do not fold into this ticket's diff, and file a
concrete stub follow-up ticket scoped as a full-pillar sweep rather than a 5th single-pillar
ticket.**

Reasoning:

1. **Folding SOCIAL in (option a) is rejected.** This ticket's title, Scope, and Related
   Tickets framing are all NARRATIVE-specific; SOCIAL's evidence (1 of 3 fresh draws) is
   thinner than NARRATIVE's (6 draws) and was gathered incidentally, not as this ticket's
   primary investigation target. Folding it in would silently expand scope past what the
   ticket document authorizes and would set a precedent that any incidental finding gets
   absorbed rather than named — the opposite of the discipline this exact ticket's own
   existence is supposed to model (it was itself spawned from an incidental disclosure, not
   silently absorbed into its parent).
2. **Pure disclose-and-defer (plain option b) is insufficient on its own.** This is the 2nd
   consecutive ticket in this chain (`CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` → this ticket) to
   organically surface exactly one new flaky pillar on this exact anchor
   (`urban_political_seed123_1000t`) while investigating a different, previously-named
   pillar. `INFRA-273` already establishes that the underlying mechanism (delta-gated
   cascading divergence via `event_extractor.py`) applies to SOCIAL, COMBAT, PROGRESSION,
   NARRATIVE, and WORLD collectively — not just the 2 pillars discovered so far. Of this
   anchor's 10 tracked pillars (`grade_anchors.json`: COGNITION, AGENCY, COMBAT, FACTION,
   ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE), only ECONOMY and (as of this
   ticket) NARRATIVE have verified overrides, and only SOCIAL+ECONOMY have a `grade_stability`
   guard — COMBAT, PROGRESSION, and WORLD, all named by `INFRA-273` as sharing the identical
   confirmed mechanism, have never been swept for this anchor. Continuing to spin out one
   narrowly-scoped ticket per newly-discovered pillar is a demonstrated, repeating pattern
   (not a hypothetical risk) and each single-pillar ticket cycle costs a full
   investigation→plan→implement→test→parity→finalize pass for what is now a mechanical,
   well-understood procedure (gather ~3-6 fresh draws, compute `1.3x max deviation`, add one
   table entry).
3. **Therefore:** disclose the SOCIAL finding fully in `INFRA-272` and
   `eval_matrix_results.md` Part 4 (Steps 6-7), but do not add an override/guard for it in
   this ticket's diff. A stub follow-up ticket has been filed —
   **`TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`**
   (`tickets/inprogress/TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP.md`, validated
   frontmatter, standard tier, P2) — scoped as **"urban_political_seed123_1000t full-pillar
   tolerance sweep"** (SOCIAL, COMBAT, PROGRESSION, WORLD — the remaining `INFRA-273`-named
   cascading-divergence pillars not yet covered by an override) rather than another
   SOCIAL-only ticket. Both Steps 6 and 7's disclosure text cite this ticket ID directly. This
   closes the gap that architecture-review flagged: a prose recommendation alone repeats the
   exact "new pillar gap had no follow-up ticket reference" failure that blocked the parent
   ticket's first Verify pass — a reasoned call against continuing the one-pillar-per-ticket
   pattern now that it has repeated twice in a row on the same anchor with a mechanism already
   known to span multiple more pillars needs a filed ticket, not just a recommendation, to
   actually break the pattern.

## Anti-Drift Notes

- `test_score_tolerance_override_table_scoped_to_named_pillars`'s hard-coded `set(...) ==
  {...}` assertion (line 610) will fail the moment the 3rd entry is added unless Step 3 lands
  in the same change as Step 2 — this is intentional anti-drift design, not a bug to route
  around.
- Every `hero_death_unrecorded` occurrence in the fresh draws was the sole negative NARRATIVE
  contribution; variance is driven by positive-event counts (`quest_started`,
  `chronicle_entry_created`, etc.), not a change in which negative events fire — do not
  mistake this for a scorer defect (`NarrativeScorer.score()` is a deterministic pure
  accumulator per investigation.md; the variance is entirely upstream in
  `event_extractor.py`'s delta-gated event construction, cascading from `kernel.py`'s
  wall-clock-dependent throttle, not something this ticket's test-side fix can or should
  change).
- `data/calibration/` and `data/runs/` are gitignored scratch space — Step 1's regenerated
  data is local-only and will not appear in `git status`; do not attempt to commit it.
- The correct file for the delta-gated event mechanism is `src/observability/
  event_extractor.py`, not `src/engine/event_extractor.py` as the ticket's Related Code Areas
  states (investigation.md flagged this as a minor ticket-text slip, already corrected) — a
  read-only reference either way, not touched by this plan.
- Per the project's Testing Rule, never run `pytest tests/` — all verification commands in
  Steps 4-5 are scoped to `tests/simulation_quality/test_grade_regression.py` and the 2 named
  `test_corpus_diversity.py` guards.

## Unresolved Questions

None. The investigation's open questions (F6-class vs. distinct root cause, whether a new
guard is warranted, the SOCIAL finding's disposition) are all resolved above with cited
evidence: F6-class confirmed (6/6 draws consistent with `INFRA-273`'s mechanism, no scorer
defect found); no new guard added (6 real draws already ground the floor, and the
`frontier_marches` guard's own precedent shows a guard is not immune to the same session-load
drift); SOCIAL disclosed-not-folded with an explicit next-ticket scoping recommendation
(full-pillar sweep, not single-pillar) to break the repeating one-pillar-per-ticket pattern.

## Deviations

None from the plan's substance — all 7 steps were implemented exactly as specified (same
`abs_floor=0.3197` value, same anchor-not-re-centered choice, same follow-up-ticket citation
in Steps 6-7). One observation surfaced during Step 4's verification that is worth recording
here even though it required no plan change: `test_grade_anchor_file_exists_and_valid` fails
locally with `TypeError: 'NoneType' object is not subscriptable` because
`hero_guild_routing_seed42_1000t` calibration data (a different anchor than this ticket's
`urban_political_seed123_1000t`) is not present on this checkout. Verified via `git stash`
that this failure reproduces identically against the pre-ticket, unmodified code — it is a
pre-existing local-calibration-data gap unrelated to this ticket's diff, not a regression
introduced by Steps 2-3's edits. No plan or scope change was needed; noted for traceability
only.
