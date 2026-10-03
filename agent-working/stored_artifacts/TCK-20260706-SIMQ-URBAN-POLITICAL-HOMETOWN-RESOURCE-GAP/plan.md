---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP
artifact_type: plan
tags: [simulation-quality, world, adventure, bug]
---

# Implementation Plan — TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP

## Summary

This ticket resolves via the Scope's "if routing is never enabled" branch: the investigation
establishes, by direct double precedent (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s standing
architectural ruling, and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s explicit
consider-and-reject of `urban_political` as the routing-capable vehicle), that
`urban_political` must never force `ENABLE_ADVENTURE_ROUTING=ON`. The content half of the
`hometown` resource gap is already fixed globally (confirmed live in the catalog file by the
investigation). Therefore this plan's entire deliverable is one new paragraph appended to
`docs/simulation_quality/eval_matrix_results.md`'s existing `## AGENCY — Cross-World Design
Note` section, plus the read-only confirmation steps (test-remains-correct, `grade_anchors.json`
unchanged, `make evaluate` regression check, `make knowledge-index-update`) that this ticket
family's discipline requires before a doc-only close. No code, profile YAML, world-content,
catalog, or test file is modified.

## Steps

### Step 1 — Append the "Third exception class" paragraph to eval_matrix_results.md
**Files:** `docs/simulation_quality/eval_matrix_results.md`

**Change:** Insert a new paragraph immediately after the existing "Second routing-capable
archetype — `hero_guild_routing`" paragraph (currently the paragraph ending "...exactly as
`simq_routing_test` already was." at line 473) and before the section-closing `---` horizontal
rule (currently line 475), inside the `## AGENCY — Cross-World Design Note` section. Preserve
the blank-line paragraph spacing already used between the section's other paragraphs (blank line
before the new paragraph, blank line after, then `---`).

Do **not** wrap the new text in a Markdown blockquote (`>` prefix) — every existing paragraph in
this section (`**Archetype decision...**`, `**Anti-drift:**`, `**Second exception class...**`,
`**Second routing-capable archetype...**`) is a plain paragraph, not a blockquote callout. The
blockquote formatting used in the investigation's drafted text was for legibility inside
`investigation.md` only, not the target file's real style — do not carry it over.

Exact text to insert (bolded lead-in + ticket ID in parens + colon, matching the section's
established pattern exactly):

```
**Third exception class — `urban_political`'s dormant `hometown` gap, accepted as permanent
non-issue (TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP):**
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation (§4(i)) found that
`urban_political` shares both `frontier_village_core` (places `wood_node`/`herb_patch` in
`hometown`) and `hero_adventurers` (spawns all 3 hero-role entities in `hometown`) with
`simq_routing_test` — the same module combination that produced `simq_routing_test_seed456`'s
`defer_with_reason` stasis failure mode before that ticket's catalog fix. That fix (adding
`"hometown"` to `wood_node`/`herb_patch`'s `source_region_tags` in
`data/content/world/resources.yaml`) is global and already covers `urban_political` too, as a
confirmed side effect — verified directly against the current catalog file
(`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`'s investigation). This gap remains
permanently dormant, not merely temporarily inert: per the archetype decision above
(`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s
explicit choice to author a brand-new routing-capable world (`hero_guild_routing`) rather than
enable routing on `urban_political` — the closest existing candidate, having a
`hero_guild`-framed population already — `urban_political` is confirmed to never force
`ENABLE_ADVENTURE_ROUTING=ON`. Its archetype framing (settlement/political, FACTION/ECONOMY/
SOCIAL-weighted, `Regression/baseline` tier per `corpus_tier_taxonomy.md`) was never intended as
adventuring/routing-oriented. No further action is required unless a future ticket explicitly
proposes reversing both `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s Out-of-Scope ruling for `urban_political`.
```

This text cites all four required tickets by ID: this ticket
(`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`, in the bold lead-in and again
mid-paragraph), the content-fix ticket (`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`),
and both precedent rulings (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`,
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`).

**Do NOT touch:** Any other paragraph or section of `eval_matrix_results.md` (in particular, do
not edit the AC6 section, the `simq_routing_test` tables, or the "Second exception class"/"Second
routing-capable archetype" paragraphs already present in this section — they are correct as-is
and out of scope). Do not create a new top-level section — the paragraph must land inside the
existing `## AGENCY — Cross-World Design Note` section per the investigation's Anti-Drift
Hazards.

**Verify:** Manual diff review confirming the paragraph lands at the correct insertion point with
correct Markdown rendering (no stray blockquote markers, correct bold/backtick pairing). No
automated test covers doc prose content directly; Step 5 (`make evaluate`) and Step 4 (existing
guard test) provide the behavioral regression check that this doc claim is consistent with actual
system state.

### Step 2 — Confirm no code/content/profile change is needed
**Files:** None changed. Confirmation only.

**Change:** No edit to `data/content/world/resources.yaml` (already fixed by
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`, verified live in investigation.md), no
edit to `config/simulation_quality/profiles/urban_political.yaml` (must continue to omit
`ENABLE_ADVENTURE_ROUTING`, which resolves to OFF by default), no edit to
`data/worlds/urban_political/world.yaml` or any `world_modules/*.yaml`.

**Do NOT touch:** `config/simulation_quality/profiles/urban_political.yaml` — adding
`ENABLE_ADVENTURE_ROUTING: "ON"` here is the specific anti-drift hazard flagged in
investigation.md; it would silently break `test_agency_da_anti_drift_guard` (T3) and contradict
this ticket's own decision.

**Verify:** `git diff` shows no changes under `data/content/`, `config/simulation_quality/
profiles/`, or `data/worlds/urban_political/` after this ticket's work is complete.

### Step 3 — Confirm no grade_anchors.json change is needed
**Files:** None changed. Confirmation only.

**Change:** `tests/simulation_quality/fixtures/grade_anchors.json`'s 7
`urban_political_seed{42,123,456}_{200t,500t,1000t}` entries stay `AGENCY: "C"` — unchanged,
since `ENABLE_ADVENTURE_ROUTING` stays OFF and no world content changes for `urban_political`.
The ticket's own AC line "`grade_anchors.json` updated if a new `urban_political` calibration run
changes any pillar's grade" does not trigger, because this ticket's disposition (routing never
enabled) means no new calibration run is required for `urban_political`.

**Do NOT touch:** `grade_anchors.json`.

**Verify:** `tests/simulation_quality/test_grade_regression.py`'s `urban_political_*` anchor
assertions pass unchanged (see Step 5's scoped test command).

### Step 4 — Confirm the existing anti-drift guard test needs no modification
**Files:** `tests/integration/test_world_profile_feature_flag_guardrail.py` (read-only
confirmation — no edit).

**Change:** None. `test_agency_da_anti_drift_guard` (starting at line 123) already reads
`_FIXTURE["_meta"]["agency_da_non_routing_worlds"]` (line 132) and asserts every listed world,
including `urban_political`, resolves `ENABLE_ADVENTURE_ROUTING` to OFF; it also asserts
`_FIXTURE["_meta"]["agency_da_routing_worlds"]` (line 143, `simq_routing_test`,
`hero_guild_routing`) resolves to ON. This ticket's decision (`urban_political` stays
non-routing, permanently) is exactly the outcome this test already encodes — no new assertion,
parametrization, or fixture-list edit is needed. The test_plan.md's optional
`test_urban_political_stays_non_routing_per_agency_da_precedent` suggestion is **not** adopted by
this plan (see Anti-Drift Notes below for rationale) — it is redundant with the existing
name-specific list membership the test already checks via `agency_da_non_routing_worlds`
containing `urban_political` by name.

**Do NOT touch:** `tests/integration/test_world_profile_feature_flag_guardrail.py`,
`tests/simulation_quality/fixtures/expected_world_flag_state.json`.

**Verify:** `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q` passes,
specifically `test_agency_da_anti_drift_guard` and `test_flag_state_matches_expected_per_world`.

### Step 5 — Run the scoped regression suite (make evaluate discipline)
**Files:** None changed. Verification only.

**Change:** Run the scoped pytest commands from test_plan.md to confirm zero regressions from
the doc-only change (a doc edit cannot itself break tests, but this ticket family's established
discipline — per `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s own precedent of
live-verifying rather than assuming — requires running the check anyway):

```
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q
pytest tests/integration/test_scenario_feature_flag_defaults.py -q
pytest tests/simulation_quality/test_weights.py -k urban_political -q
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
pytest tests/integration/worldassembly/test_e2e_smoke.py -k urban_political -q
```

If the project's `make evaluate` target runs a broader SimQ evaluation harness pass, run it too
per the ticket's own instruction, scoped to `urban_political` if the target supports scoping;
otherwise the full `make evaluate` run is acceptable since this is a doc-only ticket and the run
is expected to be a true no-op. Do not run bare `pytest tests/`.

**Do NOT touch:** Any file as a result of this step — it is verification-only. If any test
unexpectedly fails, stop and escalate (do not silently patch code to force a pass) — an
unexpected failure here would mean the investigation's "already fixed, content half closed"
claim is wrong and this plan's premise needs re-examination, not a workaround.

**Verify:** All listed commands report 0 failures, 0 errors.

### Step 6 — Update the knowledge index
**Files:** Regenerated index artifacts under the knowledge-search tool's index location (per
`make knowledge-index-update`'s target).

**Change:** Run `make knowledge-index-update` since `docs/simulation_quality/
eval_matrix_results.md` was modified in Step 1, per the project's After-Work workflow rule
("If any files under `docs/` were created or modified: run `make knowledge-index-update`").

**Do NOT touch:** Any other doc file — only the index needs regenerating; no other doc content
changes.

**Verify:** `make knowledge-index-update` completes without error; the index reflects the new
paragraph (spot-check via `search_docs` for a phrase from the new paragraph, e.g. "Third
exception class").

## Scope Guards

- Do not add `ENABLE_ADVENTURE_ROUTING: "ON"` to `config/simulation_quality/profiles/
  urban_political.yaml` under any circumstance in this ticket — the routing-capability question
  is settled (never enable), per the investigation's precedent chain.
- Do not re-touch `data/content/world/resources.yaml`'s `wood_node`/`herb_patch`
  `source_region_tags` — already fixed globally; out of scope per this ticket's own Out of Scope
  section.
- Do not touch the broader non-hero-role resource-tag/spawn-region coverage pattern — tracked by
  `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`, a separate ticket.
- Do not change the `FORM_PARTY` `sociability >= 0.2` gate value in
  `src/domains/adventure/generator.py` — a separate design/balance question, explicitly out of
  scope.
- Do not modify `grade_anchors.json`'s `urban_political_*` entries — no calibration run is
  triggered by this ticket's disposition.
- Do not modify `tests/integration/test_world_profile_feature_flag_guardrail.py` or
  `tests/simulation_quality/fixtures/expected_world_flag_state.json` — the existing guard already
  covers this ticket's decision correctly.
- Do not create a new top-level section in `eval_matrix_results.md` — the new paragraph must live
  inside the existing `## AGENCY — Cross-World Design Note` section.
- Do not wrap the new paragraph in blockquote (`>`) syntax — match the section's plain-paragraph
  style.

## Dependency Map

All steps are independent of each other except ordering for narrative clarity:
- Step 1 (doc edit) has no dependency on Steps 2–4 (all are confirmation-only, not prerequisites
  to the doc edit).
- Step 5 (test run) should follow Step 1 so that if `make knowledge-index-update` or the doc
  change itself introduced any unexpected issue it is caught before finalization, but Step 5's
  pytest commands do not technically depend on Step 1's content (a doc-only change cannot affect
  test outcomes).
- Step 6 depends on Step 1 (index update only makes sense after the doc content it indexes is
  final).
- Recommended execution order: 2, 3, 4 (confirmations, can run first or in parallel) → 1 (doc
  edit) → 5 (regression run) → 6 (index update).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Explicit decision recorded (with rationale) on whether `urban_political` should ever force `ENABLE_ADVENTURE_ROUTING=ON` | Step 1 (doc paragraph records the "no, permanently" decision with full rationale and citations) | Manual review of inserted paragraph; no automated test covers doc prose |
| If enabled: re-run calibration, confirm AGENCY grade | N/A — not taken; routing is never enabled per Step 1's decision | N/A |
| If not enabled: `eval_matrix_results.md` updated with explicit "dormant, accepted" note, cross-referencing this ticket and the parent content-fix ticket | Step 1 | Manual diff review; `make knowledge-index-update` (Step 6) confirms doc is indexed |
| `grade_anchors.json` updated if a new calibration run changes any pillar's grade | Step 3 (confirms no update needed — no new run occurs) | `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` |

## Anti-Drift Notes

- **The routing-capability question for `urban_political` is closed by precedent, not by this
  ticket.** Do not reopen or re-litigate `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` or
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s rulings while implementing this plan. If new
  evidence during implementation suggests those rulings should be reversed, stop and escalate —
  do not decide it unilaterally inside this ticket, since both prior tickets explicitly required
  a "user direction"-equivalent decision to reverse.
- **`test_agency_da_anti_drift_guard` is the load-bearing guard for this ticket's entire
  disposition.** Any future edit that removes `urban_political` from
  `expected_world_flag_state.json`'s `_meta.agency_da_non_routing_worlds` list without a ticket
  that explicitly reverses the two precedents above would silently invalidate this ticket's doc
  claim. This plan does not touch that list — confirming it stays untouched is itself part of
  Step 4's verification.
- **The optional new test suggested in test_plan.md
  (`test_urban_political_stays_non_routing_per_agency_da_precedent`) is deliberately not added by
  this plan.** Rationale: `test_agency_da_anti_drift_guard` already asserts
  `urban_political`-by-name membership in `agency_da_non_routing_worlds` (test_plan.md's own
  description of T3 confirms this is "a name-specific assertion," not a generic "some world"
  check) — adding a second test asserting the identical fact would be duplicate coverage, not new
  protection, and this ticket's Acceptance Criteria only requires the doc note for the
  "not enabled" branch, not a new test. If a future reviewer disagrees, that is a one-line
  addition to make at review time, not a blocker to closing this ticket.
- **Effort-vs-tier observation (for the record, not a ticket-field change):** the ticket declares
  `standard` tier, but the actual realized work under the "not enabled" branch is a single
  doc-paragraph addition plus read-only confirmation steps — closer in shape to a `hotfix`-tier
  ticket (no code/content/test changes, self-evident intent already fully derived by the
  investigation). This plan does not change the ticket's `Tier` field — that is not this plan's
  call — but notes it here per the task's request, consistent with test_plan.md's own observation
  that `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (the direct precedent for this kind of doc-only
  closure) was itself filed and executed as hotfix-tier.

## Unresolved Questions

None. The investigation's precedent chain (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` +
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`) fully resolves the ticket's sole Scope decision
point (whether to ever enable routing for `urban_political`) with a definitive "no, permanently."
No implementation-approach fork remains open.
