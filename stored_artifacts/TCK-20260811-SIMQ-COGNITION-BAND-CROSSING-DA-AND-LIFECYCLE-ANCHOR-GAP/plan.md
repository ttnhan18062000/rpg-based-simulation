---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP
artifact_type: plan
tags: [simulation-quality, calibration, corpus]
---

# Implementation Plan — TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP

## Summary

Pure recalibration ticket, no source code change. Investigate already proved (15/15 bit-identical
trials, direct `git worktree` bisection to `3d992dd0`) that the 4 COGNITION band-crossing items are
not F6 watchdog jitter but a deterministic, already-reviewed behavior change
(`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, `docs/guidelines/intentional_divergences.md`
§2.40) whose calibration data is simply stale. This plan: (1) re-runs each affected scenario fresh
at Implement time (never reuses Investigate's own numbers as the literal committed value — this
area has 7 sibling tickets landing within ~24h), (2) point-updates `grade_anchors.json` for the 4
items' COGNITION field and the `lifecycle_full_coverage_world_seed42_200t` anchor's 8 drifted
pillars (folding in the newly-discovered ECONOMY drift — same causal cluster, same anchor, matches
established precedent of folding same-cause findings into an active recalibration), (3) updates the
one dependent guard test with its own hardcoded anchor, (4) annotates (does not delete) the now-
inert `score_ceilings.json` ceiling entry, (5) updates the two required docs, and (6) files a
follow-up ticket for the two real-but-out-of-named-scope discoveries (AGENCY drift on
`simq_routing_test_seed42_500t`, and the two stale SLOW-tier COGNITION guards) rather than fixing or
silently dropping them.

## Design Decisions

**Decision 1 — Re-verification is mandatory, not optional.** Investigate's own numbers (captured
this session) are explicitly not to be copied verbatim into `grade_anchors.json`. Evidence:
investigation.md's own Finding (2) table shows ECONOMY moved between the Aug-11 18:17 committed
snapshot and Investigate's own fresh re-check within the same session, and Investigate names 3 more
tier-5 GoalScorer commits that may land in the interim (Risk #1). Every step below that writes a
`grade_anchors.json` value is gated on a fresh Step 1 confirming run at Implement time.

**Decision 2 — AC5's "5 items" does not include the newly-found AGENCY drift or the 1000t guards.**
The ticket's Scope section names exactly 5 things: the 4 COGNITION band-crossing items (Scope §1)
and `lifecycle_full_coverage_world_seed42_200t`'s drift as one unit (Scope §2) — "7-pillar" there is
descriptive of what Investigate found at ticket-filing time, not a hard cap Plan is bound to if
fresh evidence shows an 8th pillar in the *same* anchor is part of the *same* causal cluster.
- **AGENCY on `simq_routing_test_seed42_500t` is OUT of scope.** It is a different pillar, on a
  scenario already named for a different reason (COGNITION only), traced by investigation.md to a
  *different* ticket's *later*-landing change (§2.41 `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`,
  landed after this ticket's originating audit run). Investigation.md's own Anti-Drift Hazards
  section already states this explicitly ("Do not fix the adjacent AGENCY drift ... as part of this
  ticket"). Plan follows that instruction: file a follow-up ticket (Step 8), do not fix here.
- **ECONOMY on `lifecycle_full_coverage_world_seed42_200t` is IN scope, folded into Finding 2's
  recalibration.** Unlike the AGENCY case, this is the *same* anchor/run_key Finding 2 already
  covers, drifting from the *same* causal cluster (SUB-384 + the Finding-1 mechanism, both of which
  this world is directly exposed to via `ENABLE_ADVENTURE_ROUTING=ON`, confirmed in
  investigation.md). This matches established precedent: `docs/parity_ledger/substrate.yaml` SUB-384's
  own `TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION` UPDATE block (line 4712-4714, read
  directly) folded in "2 additional COMBAT keys found while regenerating a guard-fixture gap" under
  the same recalibration pass, rather than spinning up a separate ticket for a same-cause, same-scope
  discovery. Result: Finding 2's recalibration touches 8 pillars (COGNITION, AGENCY, COMBAT, ECONOMY,
  PROGRESSION, SOCIAL, WORLD, NARRATIVE), not 7. FACTION and INFORMATION remain untouched (confirmed
  unchanged in both of Investigate's fresh re-checks).
- **The 2 stale SLOW-tier guard tests are OUT of scope.** `test_simq_routing_test_seed42_1000t_cognition_grade_stability`
  and `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` (`tests/unit/worldassembly/
  test_corpus_diversity.py:585`, `:669`) share Finding 1's exact root cause but for the `_1000t`
  variant of these two worlds — not one of the ticket's named 4 items, and mechanically excluded from
  AC5's own pytest command (`-m "not slow"` never ran `@pytest.mark.slow` tests in the first place, so
  AC5 is satisfiable without touching them). test_plan.md flags this as "Plan should decide ... not
  silently leave them red with no ticket tracking them" — decision: file the same follow-up ticket as
  the AGENCY item (Step 8), do not fix here. Widening this ticket to cover the 1000t tier would be
  scope creep beyond the ticket's own named 4 items.

**Decision 3 — `watchdog_variance` is NOT extended to grade-band crossings.** Investigate's own
15/15-bit-identical, load-insensitive, directly-bisected evidence rules this out; extending the
ceiling mechanism would misclassify a real, understood, intentional behavior change as noise
(investigation.md Anti-Drift Hazards, first bullet). "Implemented" (per AC2) means: recalibrate the
anchors to the new deterministic truth (Steps 2, 4) and annotate the now-permanently-inert existing
`watchdog_variance` entry for this exact (run_key, pillar) so a future reader isn't misled (Step 5) —
not add new ceiling entries or a new `*_grade_stability` tolerance-guard test (also explicitly ruled
out by investigation.md's Anti-Drift Hazards, second bullet, since these 4 items are now perfectly
deterministic, not variable).

## Steps

### Step 1 — Fresh confirming re-run of all 5 items (precondition for every write below)
**Files:** none (verification only; no commit artifact from this step alone)
**Change:** Immediately before writing any `grade_anchors.json` value in Steps 2 or 4, re-run each
of the 5 items fresh via `tools/calibrate_simq.py`'s real internals — the same call sequence
investigation.md used and cited (`_resolve_profile`, `_load_profile_feature_flags`, `_run_engine`,
`_build_hub`, `_replay_jsonl_through_hub`), at least 2 independent trials per item, confirming
bit-identical results before committing a number. Do NOT reuse investigation.md's own trial numbers
as the literal committed anchor value without this confirming run — investigation.md Risk #1
explicitly names 3 more tier-5 GoalScorer commits (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`,
`TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`, `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`) that
may have landed since its own snapshot, and its own two internal re-checks already show ECONOMY
moving between them. If any of Step 1's fresh values disagree with investigation.md's cited numbers,
use Step 1's own fresh value, not investigation.md's — and note the discrepancy in the ticket's
Implementation Notes.
**Do NOT touch:** no file writes in this step — data-gathering only.
**Verify:** N/A (no assertion here; this step's output feeds Steps 2 and 4's edits, and Steps 2/4's
own `pytest` runs are the actual verification).

### Step 2 — Recalibrate `grade_anchors.json` COGNITION for the 4 Finding-1 items
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** Update `COGNITION.grade`/`COGNITION.score` for these 4 top-level entries (current values
confirmed by direct read):
- `simq_routing_test_seed42_500t.COGNITION` — currently `{"grade": "A", "score": 1.3253012048192772}`
- `simq_routing_test_seed456_500t.COGNITION` — currently `{"grade": "A", "score": 0.570264765784114}`
- `hero_guild_routing_seed42_500t.COGNITION` — currently `{"grade": "S", "score": 2.108433734939759}`
- `hero_guild_routing_seed456_500t.COGNITION` — currently `{"grade": "A", "score": 0.9255533199195171}`

Set each to Step 1's fresh-verified value for that run_key (expected, per investigation.md's 15/15
trials: `{"grade": "C", "score": 0.0}` for all 4 — but write Step 1's own confirmed number, not this
expectation blindly).

**Other writers to this file (enumerated):** `grade_anchors.json` is edited by essentially every
SimQ recalibration ticket to date (`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`,
`TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`, the `TCK-20260703/04/05/07/08` corpus
tickets, etc.), always via the same pattern: point-edit sub-fields of an *existing* top-level
`run_key` entry, never touching sibling pillars in the same entry. This step follows that same
pattern exactly (edits only the 4 named `COGNITION` sub-fields). It does **not** add or remove any
top-level `run_key` key, so it cannot collide with `test_grade_anchor_file_exists_and_valid`'s
`scenario_keys == 81` structural assertion (`tests/simulation_quality/test_grade_regression.py:680`,
confirmed by direct read). It also does not touch any `(run_key, pillar)` pair present in
`SCORE_TOLERANCE_OVERRIDES` (`test_grade_regression.py:690-696`, confirmed by direct read — none of
the 4 items/COGNITION appear in that 5-entry table), so `test_score_tolerance_override_table_scoped_to_named_pillars`
and `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` are unaffected. Concurrency risk:
per investigation.md Risk #1, sibling in-flight tickets in this same commit cluster may independently
need their own `grade_anchors.json` edits for *other* pillars/run_keys — after editing, `git diff`
the file and confirm only the 4 named `COGNITION` sub-fields (plus Step 4's 8 lifecycle fields)
changed, nothing else silently reformatted or reordered.
**Do NOT touch:** any other pillar within these same 4 entries — specifically leave
`simq_routing_test_seed42_500t.AGENCY` (currently `{"grade": "A", "score": 0.918}`) untouched even
though investigation.md found it has live-drifted to `0/C` — that is Decision 2's explicitly
out-of-scope item, handled by Step 8's follow-up ticket, not fixed here.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test_seed42_500t or simq_routing_test_seed456_500t or hero_guild_routing_seed42_500t or hero_guild_routing_seed456_500t"`

### Step 3 — Update the dependent guard test's own hardcoded anchor
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py:501-582`
(`test_simq_routing_test_seed42_500t_cognition_grade_stability`)
**Change:** This test carries its own independent inline anchor
(`anchors = {"COGNITION": {"grade": "A", "score": 1.8373, "abs_floor": 0.0521}}`, confirmed by direct
read at the function body) — it does not read `grade_anchors.json`, so Step 2's fixture edit alone
does not fix it; it will keep failing on every `-m slow` run otherwise (investigation.md Anti-Drift
Hazards, third bullet; test_plan.md item 2). Since Step 1 (this session) and investigation.md's own
15/15-trial repro both confirm the value is now provably deterministic (not variable), simplify this
guard from its current 3-trial mean+tolerance shape to a plain bit-identical assertion — matching the
shape already used by `test_urban_political_seed123_500t_cognition_bit_identical_under_load`
(`test_corpus_diversity.py:395`, confirmed present as the established "deterministic" guard pattern
in this same file) — asserting `event_count == 0` and `normalized_score == 0.0` exactly (or
Step 1/Step 2's confirmed value, if it differs from investigation.md's expectation) across 2
independent fresh trials. Update the docstring to remove the now-inapplicable "confirmed
genuinely-variable ... F6/decision_divergence_detected-class" framing and cite this ticket's
bisection to `3d992dd0` / `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` instead, matching how
the file's own module-level comment block (line ~491-497, the "2d." section header) already
distinguishes bit-identical guards (2a) from tolerance-based guards (2b) — this test moves from the
2b class to the 2a class.
**Do NOT touch:** the sibling guard tests `test_simq_routing_test_seed42_1000t_cognition_grade_stability`
(line 585) and `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` (line 669) — Decision
2, out of scope, handled by Step 8's follow-up ticket. Do not touch any of the other guard tests in
this file (`test_unit_selfmodel_pilot_...`, `test_urban_political_...`, etc.) — unrelated anchors.
**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -k "simq_routing_test_seed42_500t and cognition" -m slow -v`

### Step 4 — Recalibrate `grade_anchors.json` for `lifecycle_full_coverage_world_seed42_200t` (8 pillars)
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** Current entry (confirmed by direct read):
`COGNITION` A/1.2878787878787878, `AGENCY` A/1.925, `COMBAT` B/0.010050251256281407, `FACTION`
S/7.5, `ECONOMY` A/0.5303867403314917, `PROGRESSION` A/0.8735632183908046, `SOCIAL` S/29.115,
`INFORMATION` C/0.0, `WORLD` A/0.54, `NARRATIVE` C/0.0.

Update 8 pillars — `COGNITION`, `AGENCY`, `COMBAT`, `ECONOMY`, `PROGRESSION`, `SOCIAL`, `WORLD`,
`NARRATIVE` — to Step 1's fresh-verified values for this run_key (per Decision 2, ECONOMY is folded
in alongside the ticket's original 7). Do not use investigation.md's own snapshot values directly;
Step 1's fresh re-confirmation is authoritative, per investigation.md Risk #1 and #2 (this world's
SOCIAL value was itself still moving between Investigate's own two internal re-checks — 2395 → 496 →
497 events across three successive samples — so a third, Implement-time sample is required before
committing a number, not just Investigate's own two).
**Other writers to this file:** same enumeration as Step 2 (all prior SimQ recalibration tickets,
same point-edit pattern). This step edits 8 sub-fields of the single already-existing
`lifecycle_full_coverage_world_seed42_200t` top-level entry — no new/removed top-level keys, same
`scenario_keys == 81` non-collision reasoning as Step 2 applies. No `(run_key, pillar)` pair here
appears in `SCORE_TOLERANCE_OVERRIDES` either (confirmed, same table checked for Step 2). After Step
2 and this step both land, `git diff tests/simulation_quality/fixtures/grade_anchors.json` should
show changes to exactly 2 top-level entries (the 4-item shared... — actually 5 top-level entries:
the 4 Step-2 entries' COGNITION field, plus this entry's 8 fields) and nothing else.
**Do NOT touch:** `FACTION` (S/7.5) and `INFORMATION` (C/0.0) — both confirmed unchanged/within
tolerance in both of investigation.md's fresh re-verification passes.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "lifecycle_full_coverage_world_seed42_200t"`

### Step 5 — Annotate the now-superseded `score_ceilings.json` entry
**Files:** `tests/simulation_quality/fixtures/score_ceilings.json`
**Change:** The existing entry (`run_key: "simq_routing_test_seed42_500t"`, `pillar: "COGNITION"`,
`ceiling_kind: "watchdog_variance"`, reason citing `194/196/194/193` event-count variance,
`since_ticket: "TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP"` — confirmed present by direct
read) becomes permanently inert once Step 2 recalibrates this pillar's anchor to a deterministic
0-event value: `_format_score_failures`'s ceiling lookup (`test_grade_regression.py:261-285`,
confirmed by direct read — it only appends `[known {ceiling_kind}: ...]` text when a score-tolerance
*failure* occurs) will never fire for this pillar again post-recalibration, since there won't be a
failure to annotate. Leaving the entry verbatim risks misleading a future reader into thinking
COGNITION is still F6-variable here (investigation.md Risk #4). Append a superseded note to the
`reason` field citing this ticket and the `3d992dd0` bisection — matching the file's own existing
precedent for recording a resolved-not-ongoing state (the top-of-file `NARRATIVE`/`ceiling_kind:
"corrected"` entry, whose reason text already reads "the 2026-08-07 recalibration reflects the
honest, corrected value, not an ongoing ceiling", confirmed present by direct read). Do not delete
the entry (preserves audit history of the real watchdog-variance finding that was true at the time)
and do not change `ceiling_kind` or `evidence`.
**Other writers to this file (enumerated):** `score_ceilings.json` has exactly 6 entries, added by
`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` (1 entry, the `NARRATIVE`/`corrected` one) and
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP` (5 `watchdog_variance` entries, confirmed by
direct read of the full file). This step is a 3rd writer, touching only 1 of the 6 existing entries'
`reason` field — no structural change (same 6-entry count, same keys).
**Do NOT touch:** the other 5 entries — `simq_routing_test_seed42_500t/PROGRESSION`,
`simq_routing_test_seed123_500t/PROGRESSION`, `urban_political_seed456_500t/ECONOMY` and
`/PROGRESSION`, and the `NARRATIVE`/`corrected` entry — Out of Scope explicitly preserves these.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` (structural
JSON-validity plus confirms no regression across the full `FAST_ANCHOR_KEYS` sweep — this file is
JSON-loaded by `simq_ceiling.lookup_ceiling`, so a malformed edit would surface as an import/parse
error across the whole suite, not just this one pillar).

### Step 6 — Docs: `eval_matrix_results.md` NOTE blocks
**Files:** `docs/simulation_quality/eval_matrix_results.md`
**Change:** Add a dated NOTE block (`2026-08-12 —
TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`) in the `simq_routing_test`
section (after the "Stability analysis" line, confirmed present at line 424) and near the
`hero_guild_routing` discussion (confirmed present at lines 592-604), matching the file's own
established NOTE format (see the 2026-08-10 SUB-384 NOTE at line ~330, confirmed by direct read: date
+ ticket + root-cause commit + before/after values + cross-reference). Content: root cause =
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` (`3d992dd0`), COGNITION moving A/S → C for all 4
seed/run_key combos in this ticket's scope, explanation that `decision_divergence_detected` was
measuring the frequency of a real interruption-bypass bug rather than a positive diversity signal
(cite `config/simulation_quality/scoring_weights.yaml` `subjective_divergence` weight and
`src/simulation_quality/scorers/cognition.py:106-110`, both confirmed cited in investigation.md), and
cross-reference `docs/guidelines/intentional_divergences.md` §2.40.

`lifecycle_full_coverage_world` has **no existing section in this doc** (confirmed: zero grep matches
for "lifecycle_full_coverage_world" in `docs/simulation_quality/eval_matrix_results.md`) — this is
itself part of the "never registered" gap this ticket is closing. Add a new dated NOTE subsection
(reasonable placement: near the "Newly-Anchored Worlds" section, or immediately following the
`urban_political` SUB-384 NOTE block it parallels) documenting the 8-pillar recalibration, citing
SUB-384 (via `compile_context.json`'s `legacy_roles`/`legacy_factions`, confirmed present) as the base
cause compounding with the Finding-1 mechanism (since `ENABLE_ADVENTURE_ROUTING: "ON"` in this
world's own profile), and the 3 additional tier-5 GoalScorer commits that landed after the original
audit snapshot.
**Do NOT touch:** any other world's section in this doc.
**Verify:** No automated test. Confirm the added blocks follow the established dated-NOTE format
(Definition of Done: "Update related docs").

### Step 7 — Parity ledger: `substrate.yaml` SUB-384 UPDATE block
**Files:** `docs/parity_ledger/substrate.yaml`
**Change:** SUB-384's entry (`id: SUB-384`, lines 4628-4724, confirmed by direct read) already ends
with an "UPDATE (TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION, 2026-08-10)" block at
lines 4706-4724. Append a new block in the same style:
`UPDATE (TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP, 2026-08-12):` adding
`lifecycle_full_coverage_world_seed42_200t` to the set of worlds recalibrated under this cause,
explicitly stating the drift here is **compound, not purely SUB-384** — SUB-384's original
population/RNG-stream cascade *plus* the Finding-1 `PROJECT-SWITCH-BYPASS-GENERALIZATION` mechanism
(this world sets `ENABLE_ADVENTURE_ROUTING: "ON"`) *plus* 3 additional tier-5 GoalScorer commits that
landed after the original audit snapshot. State the 8 recalibrated pillars by name. Leave `status:
verified` and `priority: P0` unchanged (this is a calibration-data update, not a new finding about
SUB-384's own root cause or fix).
**Do NOT touch:** `status`, `priority`, `v2_evidence`, `legacy_evidence`, or any other `id:` entry in
this file.
**Verify:** No automated pytest coverage for prose content; confirm the file still parses as valid
YAML (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/substrate.yaml'))"`).

### Step 8 — File a follow-up ticket for the disclosed, out-of-named-scope findings
**Files:** new ticket file under `tickets/inprogress/` (or `tickets/todos/` if deferred), no
`src/` or fixture changes
**Change:** Per Decision 2, two real, disclosed findings must not be silently absorbed into this
ticket or silently dropped:
1. `simq_routing_test_seed42_500t`'s AGENCY drift (`A/0.918` → `0/C` at current `HEAD`), plausibly
   caused by `docs/guidelines/intentional_divergences.md` §2.41 (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s
   `last_defer_reason`/`defer_with_reason` gap) — a different mechanism than this ticket's Finding 1,
   not yet verified further.
2. Two stale, currently-failing SLOW-tier COGNITION guard tests sharing Finding 1's exact root cause
   for the `_1000t` variant: `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
   `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`
   (`tests/unit/worldassembly/test_corpus_diversity.py:585`, `:669`).

Create one standard-tier, `layer: simulation` follow-up ticket (via the ticket format in
`CLAUDE.md`/`create-tickets` conventions) covering both, citing this ticket's investigation.md as the
disclosure source. Status `OPEN`, not implemented as part of this ticket's own commit.
**Do NOT touch:** do not implement fixes for either finding in this ticket — filing the follow-up is
the full extent of this step's work. Do not proactively re-verify every other `SLOW_ANCHOR_KEYS`
entry for the same root cause (test_plan.md flags only these 2 as confirmed same-cause; broader
sweeping is scope creep beyond what Investigate confirmed).
**Verify:** follow-up ticket file exists with valid frontmatter (`layer`/`tags` from the registries),
Related Tickets section references
`TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP`.

### Step 9 — Full scoped regression sweep
**Files:** none (verification only)
**Change:** Run all 3 scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands" section,
in order:
1. `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` — AC5's exact command;
   confirm 0 unexplained failures across the full `FAST_ANCHOR_KEYS` sweep, not just the 5 touched
   items.
2. `pytest tests/unit/worldassembly/test_corpus_diversity.py -k "simq_routing_test_seed42_500t or hero_guild_routing" -m slow -v`
   — confirms Step 3's updated guard passes and the (out-of-scope, still-red) 1000t guards are
   visible in the output for the follow-up ticket's own reference, not silently hidden.
3. `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow -v` — full corpus-diversity
   guard sweep, confirms no other `*_grade_stability` guard (all of which carry their own
   independent inline anchors, per investigation.md) regressed from the `grade_anchors.json` edits.

Also run the sanity-check test named in test_plan.md's Regression Surface:
`pytest tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
— confirms STRAT-186's own test is still green before finalizing (not modified by this ticket, but
its "already fixed, already verified" framing should be spot-checked once before closing).
**Do NOT touch:** `pytest tests/` (repo-wide) is explicitly disallowed per CLAUDE.md's Testing Rule.
**Verify:** all commands above; this step is the AC5 gate.

## Scope Guards

- Do NOT touch `src/systems/strategic_systems/intelligence.py`, `AdventureDecisionPhase`
  (`src/domains/adventure/phase.py`), or any other source file involved in the already-landed,
  already-reviewed `3d992dd0` fix — this ticket only recalibrates stale test fixtures to match
  already-correct, already-documented behavior.
- Do NOT extend `watchdog_variance` (`score_ceilings.json`) to cover discrete grade-band crossings —
  ruled out by Decision 3's evidence.
- Do NOT add a new multi-trial `*_grade_stability` tolerance-guard test for any of the 4 Finding-1
  items — they are now perfectly deterministic; a plain point-anchor update (Step 2) plus a
  bit-identical guard (Step 3) is correct, not the tolerance-guard shape.
- **Every `grade_anchors.json` write in Steps 2 and 4 MUST be preceded by a fresh Step-1 confirming
  run at Implement time** — never commit a value copied directly from investigation.md's own
  snapshot without this final re-verification (Decision 1). This is the single most important scope
  guard in this plan given the area's active churn.
- Do NOT fix or investigate further the AGENCY drift on `simq_routing_test_seed42_500t`, or the two
  stale `_1000t` SLOW-tier guard tests — file the follow-up ticket (Step 8) instead.
- Do NOT touch `FACTION` or `INFORMATION` on `lifecycle_full_coverage_world_seed42_200t` — confirmed
  unchanged in both of Investigate's fresh re-verification passes.
- Do NOT touch the other 5 entries in `score_ceilings.json`, or any `grade_anchors.json` entry
  outside the 5 named run_keys.
- Do NOT re-open or edit `docs/guidelines/intentional_divergences.md` §2.40's own divergence text —
  it already correctly documents the root-cause code change; this ticket only adds a downstream
  cross-reference in `eval_matrix_results.md`/`substrate.yaml` (Steps 6-7), which is optional
  nice-to-have per investigation.md, not mandatory.
- Do NOT run `pytest tests/` repo-wide — scope every command to the files named in Step 9.
- Do NOT proactively re-verify every `SLOW_ANCHOR_KEYS` entry corpus-wide for the same root cause —
  only the 2 confirmed cases go into the Step 8 follow-up ticket.

## Dependency Map

- Step 1 (fresh re-run) must complete before Steps 2 and 4 (the values it produces are what gets
  written).
- Step 3 (guard test update) logically follows Step 2 (same underlying COGNITION value for
  `simq_routing_test_seed42_500t`) but is a separate file — can be implemented in either order as
  long as both land before Step 9.
- Step 5 (ceiling annotation) follows Step 2 (references the now-recalibrated COGNITION value).
- Step 6 (eval_matrix_results.md) and Step 7 (substrate.yaml) document the final committed values
  from Steps 2 and 4 — implement after those land, not before.
- Step 8 (follow-up ticket) has no technical dependency on the others; can be done at any point, but
  logically follows once Decision 2's scope boundary is fixed (it already is, in this plan).
- Step 9 (full sweep) depends on all of Steps 2-7 being complete — it is the final gate.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — 4 COGNITION items re-sampled with real multi-trial investigation; root cause confirmed/ruled out | Already satisfied by investigation.md (15 trials + bisection to `3d992dd0`); Step 1 adds a final Implement-time reconfirmation | Step 1's fresh trials; `test_simq_routing_test_seed42_500t_cognition_grade_stability` (Step 3, post-update) |
| AC2 — concrete decision made and implemented for extending/not-extending `watchdog_variance` to grade-band crossings, reasoning recorded | Decision 3 (this plan.md) + Step 2/4 (recalibrate instead of extend) + Step 5 (annotate now-inert ceiling) + Step 6 (docs record the reasoning) | `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` (Step 9, cmd 1) |
| AC3 — `lifecycle_full_coverage_world_seed42_200t`'s 7-pillar drift investigated and confirmed/ruled out as SUB-384 cascade | Already satisfied by investigation.md (`compile_context.json` direct inspection); Step 1 reconfirms at Implement time | Step 1's fresh trials |
| AC4 — `grade_anchors.json` recalibrated for `lifecycle_full_coverage_world_seed42_200t` if confirmed, following established methodology | Step 4 (8 pillars, per Decision 2's ECONOMY fold-in) | `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "lifecycle_full_coverage_world_seed42_200t"` |
| AC5 — `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` shows 0 unexplained failures for all 5 items (COGNITION on the 4 items + the lifecycle anchor) | Steps 2, 3, 4, 5 | Step 9's full sweep (all 3 commands) |

## Anti-Drift Notes

- The load-bearing verification for this ticket is the *live repro evidence* (Step 1's fresh trials,
  building on investigation.md's 15/15 bit-identical result and direct bisection), not the pytest
  green checkmark alone — a passing `test_grade_within_anchor_band` only proves the fixture matches
  *some* captured value, not that the value is correct. Do not skip Step 1 because investigation.md
  already looks thorough.
- This area of the codebase (`src/systems/strategic_systems/intelligence.py`,
  `src/domains/adventure/`, tier-5 `GoalScorer` arbitration) is under active, still-landing churn —
  7 sibling tickets touched it within ~24h of investigation.md's own bisection. If a future re-run of
  any of these 5 items drifts again after this ticket closes, that is a new signal worth
  investigating on its own terms, not evidence the "deterministic" classification here was wrong and
  not automatically more F6 noise.
- If a future ticket is tempted to add a `watchdog_variance` entry for any of these 4
  `(run_key, COGNITION)` pairs again, it must first re-run the same idle-vs-load repro (2 idle + 2x/4x
  load) — a single anomalous sample is not sufficient grounds after this ticket's 15-trial
  deterministic-zero finding.
- Nothing in this ticket touches `src/` production code — if Implement finds itself editing anything
  under `src/`, that is a signal the ticket has drifted beyond its Out of Scope boundary (calibration
  data only).
