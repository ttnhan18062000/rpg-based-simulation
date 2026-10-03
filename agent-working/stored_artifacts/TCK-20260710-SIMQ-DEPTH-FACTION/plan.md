---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-FACTION
artifact_type: plan
tags: [simulation-quality, faction, world, corpus, calibration]
---

# Implementation Plan — TCK-20260710-SIMQ-DEPTH-FACTION

## Closure-Mechanism Decision

**Decision: close as "already-satisfied by prior work" directly (investigation's option (b)), not
folded into Phase 5's Coverage Decision Gate (option (c)).**

Rationale, grounded in the roadmap doc's actual text (`docs/plans/simq_development_roadmap.md`):

- **Phase 3's own text already names this exact outcome as valid**, without needing Phase 5 at all:
  "Per the correction note above, 'zero new worlds, coverage already adequate, documented and
  closed' is also a valid acceptance outcome for either ticket — this phase does not require finding
  new candidate worlds if honest investigation finds none remain" (line 331-333). This ticket's
  finding is precisely that outcome. No escalation to a later phase is needed to make it a legitimate
  closure.
- **Phase 5 is explicitly scoped as a later, corpus-wide, multi-phase gate — not a per-ticket
  closure mechanism.** Its own text (line 384-410): "Not a work item — a decision checkpoint...
  **Once Phases 2–4 have landed** (or Phase 4 has reported its investigation-only finding), this
  roadmap's job is done and a new, short decision doc... should answer: given the *actual* observed
  cost-per-world-per-pillar from **the three waves**, is continuing toward full 17-world coverage
  worth it." Phase 4 (`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) has not landed as of this
  ticket. Phase 5's own folder deliberately holds no ticket yet, "filed... so the roadmap's full
  structure is represented... intentionally holds no ticket yet" — it is not ready to fire, and
  firing it early on the strength of one pillar's one-ticket finding would conflate a ticket-scoped
  "is there any remaining work here" question with a roadmap-scoped "is continuing to full coverage
  worth the cost" question. Those are different questions with different evidence bars.
- Folding this ticket into Phase 5 would also incorrectly imply that the 6 tier-purity worlds are
  "not yet covered but could be" — pending a corpus-wide cost/benefit call. That is not what the
  investigation found: those 6 worlds are covered by design (deliberately FACTION-inert to preserve
  single-variable isolation), not by omission. There is no future world of "continuing FACTION
  coverage into them" for Phase 5 to weigh — doing so would break their isolation contracts
  regardless of what Phase 5 eventually decides for the roadmap as a whole. This is a closed
  ticket-level finding, not an open roadmap-level trade-off.

Therefore this plan documents the finding as a durable, discoverable closure (in
`eval_matrix_results.md` and `corpus_tier_taxonomy.md`, not just in `staging_artifacts/`), updates
the roadmap's Phase 3 section to record FACTION-half closure, and closes the ticket. No content
authoring, no recalibration, no engine change, no parity ledger change.

## Summary

This ticket makes **zero code, content, or test changes**. Investigation definitively resolved UQ-1:
of the 17-world corpus, 11 worlds already carry calibrated `faction_tension_overrides` content and
the remaining 6 each have a documented, live-verified tier-purity reason to stay FACTION-inert. The
roadmap's Phase 3 FACTION-half goal is already satisfied by three prior, already-closed tickets
(`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`, `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`,
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`). This plan's job is to record that finding
durably in the two docs that future investigators will actually consult (`eval_matrix_results.md`,
`corpus_tier_taxonomy.md`), update the roadmap doc's Phase 3 section to reflect closure, fill in the
ticket's own Completion Summary, and run a confirmatory verification pass proving no code/content/
test drift occurred during this documentation-only closure.

## Steps

### Step 1 — Record the 17-world FACTION coverage table and UQ-1 resolution in `eval_matrix_results.md`
**Files:** `docs/simulation_quality/eval_matrix_results.md`
**Change:** Append a new top-level section at the end of the file (after the current final line,
~line 1992, following the existing pattern of dated, ticket-cited sections such as "Long-Run
Hot-Pillar Anchors (TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS)"):

```
## FACTION Coverage Closure — Phase 3 (TCK-20260710-SIMQ-DEPTH-FACTION)

[17-row coverage table, copied verbatim from investigation.md's "Corpus-Wide FACTION Coverage
Re-Verification" table — World / Tier / FACTION content? / faction_tension_overrides (live grep) /
Tier-purity rationale]

**Verdict: 11/17 worlds covered, 6/17 deliberately FACTION-inert by tier-purity design (Stress:
crowded_frontier, resource_dense_basin; Regression/baseline: simq_routing_test; Unit:
hero_guild_routing, unit_information_source, unit_selfmodel_pilot). No genuinely uncovered,
tier-appropriate FACTION candidate remains in the corpus.** This closes the roadmap's Phase 3
FACTION-half goal (`docs/plans/simq_development_roadmap.md`) as already-satisfied by prior work —
see that doc's Phase 3 section for the closure record. No content authoring, recalibration, or
grade-anchor changes were made under this ticket; ground truth was re-verified by direct grep against
live `data/worlds/*/world.yaml` (not inferred from docs) on 2026-07-10.
```

Reuse the exact table content from `investigation.md`'s coverage table (rows 1-17) so this becomes
the durable, discoverable copy of that evidence rather than leaving it only in
`staging_artifacts/` (which is ticket-scoped and gets archived to `stored_artifacts/` on close,
making it less discoverable to a future investigator scanning `eval_matrix_results.md` directly).
**Do NOT touch:** any existing grade table, section, or anchor value elsewhere in this file — this is
a pure append, no edits to prior content.
**Verify:** Manual read-back — the new section renders correctly, the table matches
`investigation.md`'s table row-for-row, and `grep -c "^|" ` count on the new table section equals 18
(1 header + 17 world rows). No automated test covers `docs/` content accuracy (confirmed in
`test_plan.md`); this is a documentation-correctness check, not a pytest target.

### Step 2 — Add closure note to `corpus_tier_taxonomy.md`
**Files:** `docs/simulation_quality/corpus_tier_taxonomy.md`
**Change:** Insert one new paragraph after the "Current tier mapping" section's existing intro
paragraph and table (after line 144, before the `---` divider at line 145, i.e. before the "Named
scale-diversity gaps" section). Content:

```
**FACTION coverage closure (2026-07-10, `TCK-20260710-SIMQ-DEPTH-FACTION`):** the roadmap's Phase 3
FACTION-half re-verified this table's tier assignments against live `data/worlds/*/world.yaml`
content and found them accurate (no staleness) — 11/17 corpus worlds carry
`faction_tension_overrides` content; the 6 that do not (`crowded_frontier`, `resource_dense_basin`,
`simq_routing_test`, `hero_guild_routing`, `unit_information_source`, `unit_selfmodel_pilot`, all
already listed in the table above) are each FACTION-inert by deliberate tier-purity design, not by
omission. No tier reassignment resulted. See `eval_matrix_results.md`'s "FACTION Coverage Closure —
Phase 3" section for the full re-verification table.
```

**Do NOT touch:** the "Current tier mapping" table itself (lines 121-139) — no tier assignment
changes; the "Named scale-diversity gaps" section below it — those gaps are about stress-tier scale
diversity, not FACTION content, and are unaffected by this finding.
**Verify:** Manual read-back — paragraph renders in the correct location, does not alter any existing
table row or tier assignment.

### Step 3 — Update `simq_development_roadmap.md` Phase 3 section to record FACTION-half closure
**Files:** `docs/plans/simq_development_roadmap.md`
**Change:** Add a new dated closure note immediately after the existing "Tickets filed (2026-07-10)"
bullet list (after line 341, before the `---` divider at line 343), following the doc's own
established pattern for dated correction/update blockquotes (matching the style of the existing
"Correction (2026-07-10, after ticketing)" block at line 286 and "Update (2026-07-10, after
ticketing)" block at line 402):

```
> **Closure (2026-07-10, `TCK-20260710-SIMQ-DEPTH-FACTION` done) — FACTION half closed as
> already-satisfied.** Investigation re-verified all 17 corpus worlds against live
> `data/worlds/*/world.yaml` content and confirmed 11/17 already carry calibrated
> `faction_tension_overrides`, with the remaining 6 each having a documented, deliberate tier-purity
> reason to stay FACTION-inert (not an oversight — see
> `docs/simulation_quality/eval_matrix_results.md`'s "FACTION Coverage Closure — Phase 3" section).
> Zero content authoring, recalibration, or engine work was needed or performed. This is the "zero
> new worlds, coverage already adequate, documented and closed" outcome this section's Acceptance
> Signal explicitly names as valid. This closure was decided at the ticket level, not deferred to
> Phase 5 — Phase 5 is a later, corpus-wide gate that fires once Phases 2-4 have all landed and asks
> a different question (whether pursuing full 17-world coverage is worth its cost), not whether any
> single pillar's single-ticket scope still has work in it. The INFORMATION half
> (`TCK-20260710-SIMQ-DEPTH-INFORMATION`) is tracked separately and is not affected by this closure.
```

**Do NOT touch:** Phase 2, Phase 4, or Phase 5 sections' own text — this closure note only concerns
Phase 3's FACTION half. Do not mark Phase 3 as fully complete in this edit — INFORMATION half is a
separate, still-open sibling ticket.
**Verify:** Manual read-back — blockquote renders correctly, does not alter the INFORMATION-half
framing or the "Tickets filed" list itself.

### Step 4 — Verify no `docs/plans/audit_fix_plan.md` entry requires closure
**Files:** none (read-only verification step)
**Change:** Confirm via search that `audit_fix_plan.md` has no open entry referencing FACTION
coverage or this ticket's scope. Already checked during planning: `grep -n -i "faction"
docs/plans/audit_fix_plan.md` returns only `P1-C` (Faction & Diplomacy System — already **RESOLVED**,
2026-07-03, an unrelated diplomacy-engine item predating this ticket) and `P2-D` (Faction
relationships sparse — already **RESOLVED**, 2026-07-07, the *global* `faction_relationships.yaml`
catalog density item, explicitly a different content domain per this ticket's own Out of Scope
section). No entry in `audit_fix_plan.md` is open and in-scope for this ticket. Record this
confirmation in the ticket's Implementation Notes (Step 5) rather than editing
`audit_fix_plan.md`, since there is nothing there to close.
**Do NOT touch:** `docs/plans/audit_fix_plan.md` — no entry in that file needs a status change.
**Verify:** `grep -n -i "faction" docs/plans/audit_fix_plan.md` output matches the two already-resolved
entries above; no other output.

### Step 5 — Fill in the ticket's Completion Summary and related sections
**Files:** `tickets/inprogress/TCK-20260710-SIMQ-DEPTH-FACTION.md`
**Change:** Fill in:
- `## Status` → `DONE`
- `## Implementation Notes` — record the closure-mechanism decision (close as already-satisfied, not
  folded into Phase 5) with the rationale from this plan's "Closure-Mechanism Decision" section, and
  the Step 4 audit_fix_plan.md check result.
- `## Test Summary` — record that no code/content changes were made; cite the confirmatory regression
  sweep from Step 6 (test commands + pass result) as proof of zero drift, per `test_plan.md`'s
  "Scoped Pytest Commands".
- `## Files Changed` — list exactly the 3 doc files touched: `docs/simulation_quality
  /eval_matrix_results.md`, `docs/simulation_quality/corpus_tier_taxonomy.md`,
  `docs/plans/simq_development_roadmap.md`.
- `## Completion Summary` — full finding: UQ-1 resolved definitively (0 legitimate candidates among
  the 6 remaining worlds), roadmap Phase 3 FACTION-half closed as already-satisfied by prior work
  (`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`, `-STRESS-WORLDS`,
  `-UNIT-WORLDS-FACTION-INFO`), zero code/content/test changes, closure recorded durably in
  `eval_matrix_results.md` and `corpus_tier_taxonomy.md` rather than left only in
  `staging_artifacts/`.
**Do NOT touch:** the ticket's `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, or
`## Assumptions / Open Questions` sections — those are the historical record of what was originally
asked and found; do not rewrite them to retroactively match the closure outcome.
**Verify:** Ticket file renders with all sections filled; `## Status` reads `DONE`.

### Step 6 — Verification pass: confirm zero code/content/test drift
**Files:** none (verification only)
**Change:** Run a scope-boundary check and a confirmatory regression sweep:
1. `git diff --stat` (or equivalent staged diff) should show changes touching only: this plan's 3 doc
   files (Steps 1-3), the ticket file (Step 5), and `staging_artifacts/TCK-20260710-SIMQ-DEPTH-FACTION/`
   artifacts (this `plan.md` itself, plus whatever `investigation.md`/`test_plan.md` already exist).
   Explicitly confirm **zero** changes under `src/`, `data/worlds/`, `tests/`,
   `tests/simulation_quality/fixtures/grade_anchors.json`, or `docs/parity_ledger/faction.yaml`.
2. Run the confirmatory regression commands from `test_plan.md`'s "Scoped Pytest Commands" section
   (Pattern-6 plumbing, faction domain, corpus diversity/population-stability, integration faction
   campaign, SimQ fast grade-anchor regression) and confirm all pass with 0 regressions — this proves
   the documentation-only closure did not accidentally destabilize anything, even though no code was
   touched.
**Do NOT touch:** anything — this step only runs checks and reports results, no edits.
**Verify:** `git diff --stat` output matches the expected file list above; all pytest commands from
`test_plan.md` exit 0.

## Scope Guards

Explicit list of things this plan must **not** touch, per the ticket's Out of Scope section and the
investigation's Anti-Drift Hazards:

- Do NOT author `faction_tension_overrides` into any of the 6 tier-purity worlds
  (`crowded_frontier`, `resource_dense_basin`, `simq_routing_test`, `hero_guild_routing`,
  `unit_information_source`, `unit_selfmodel_pilot`) — each has a deliberate, documented isolation
  contract that content authoring would break.
- Do NOT touch `docs/parity_ledger/faction.yaml`'s `FAC-012` entry (or any other entry in that file)
  — investigation found no new evidence world to add; `FAC-012` already accurately documents
  `urban_political` + `frontier_marches` and needs no change.
- Do NOT touch any `src/` file — Pattern-6 plumbing (`src/worldbuilding/schema.py`,
  `src/worldassembly/schema.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/resolver.py`)
  is confirmed correct and unmodified; this is a documentation-only closure.
- Do NOT touch `tests/simulation_quality/fixtures/grade_anchors.json` or `FAST_ANCHOR_KEYS` in
  `tests/simulation_quality/test_grade_regression.py` — no recalibration occurred, no new anchor
  entries are warranted.
- Do NOT touch any `data/worlds/*/world.yaml` or `data/worlds/*/resolved/world.resolved.yaml` file
  — no world content changes.
- Do NOT touch `data/content/social/faction_relationships.yaml` — the global relationship catalog is
  a separate, already-closed content domain (`TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`).
- Do NOT touch any existing table row, grade value, or anchor entry in `eval_matrix_results.md` or
  the "Current tier mapping" table in `corpus_tier_taxonomy.md` — Steps 1-2 are pure additions.
- Do NOT touch the Phase 2, Phase 4, or Phase 5 sections of `simq_development_roadmap.md`, and do
  NOT fire/pre-decide Phase 5's Coverage Decision Gate — see "Closure-Mechanism Decision" above for
  why folding into Phase 5 is explicitly rejected.
- Do NOT touch the sibling ticket `TCK-20260710-SIMQ-DEPTH-INFORMATION` or its own staging artifacts
  — INFORMATION is a separate content domain with its own investigation and closure path.
- Do NOT add any new test — `test_plan.md` confirms none are required for this closure path.

## Dependency Map

- Steps 1, 2, 3, and 4 are independent of each other (different files, no shared state) and may be
  done in any order.
- Step 5 (ticket Completion Summary) depends on Steps 1-4 being complete, since it must accurately
  cite what was changed and confirm the audit_fix_plan.md check result.
- Step 6 (verification pass) depends on Steps 1-5 being complete, since it verifies the full diff
  produced by this plan and re-runs regression tests against the final state.

## Acceptance Criteria Map

The ticket's original 8 acceptance criteria all presuppose that content authoring occurs (candidate
worlds selected, `faction_tension_overrides` seeded, recalibration run, `FAC-012` extended). UQ-1
resolved that zero legitimate candidates exist, so those criteria are **satisfied vacuously by prior
work already done under other tickets**, not by any action taken under this ticket. This plan's own
6 steps constitute the actual, verifiable acceptance criteria for **this ticket's closure**. Mapping:

| Original AC from ticket | Status under this closure | Verified by |
|---|---|---|
| Re-verified candidate list of 2-3 archetype-appropriate worlds, stale-premise gap reconciled | Satisfied — list is empty (0 candidates), gap fully reconciled in `investigation.md` and durably recorded in `eval_matrix_results.md` (Step 1) | Step 1 manual read-back |
| Each selected world has >=2 non-zero `faction_tension_overrides` entries | N/A — vacuous, no world selected (by design, not gap) | — |
| Each selected world compiles with 0 warnings, >=60% alive floor | N/A — vacuous, no world selected | — |
| Each selected world's FACTION grade moves off `C` | N/A — vacuous, no world selected | — |
| `make evaluate` full corpus sweep exits 0 | Not required for a no-content-change closure per `test_plan.md`; Step 6's scoped regression sweep substitutes as the confirmatory check | Step 6 |
| `docs/parity_ledger/faction.yaml` FAC-012 extended | N/A — no new evidence world; FAC-012 stays accurate as-is (explicit scope guard) | Step 6 (diff check confirms untouched) |
| `eval_matrix_results.md`/`corpus_tier_taxonomy.md` updated | Satisfied — closure note added to both (not new grade tables, since no new world) | Steps 1, 2 |
| Newly-discovered engine bug filed separately | N/A — no engine bug found | — |

**This plan's own acceptance criteria (the real closure bar for this ticket):**

| This plan's AC | Implemented by step(s) | Verified by |
|---|---|---|
| 17-world coverage table + UQ-1 resolution durably recorded in `eval_matrix_results.md` | Step 1 | Step 1 manual verify |
| Closure note added to `corpus_tier_taxonomy.md`, tier table unchanged | Step 2 | Step 2 manual verify |
| Roadmap Phase 3 section records FACTION-half closure, INFORMATION half unaffected | Step 3 | Step 3 manual verify |
| `audit_fix_plan.md` confirmed to have no open, in-scope entry | Step 4 | Step 4 grep check |
| Ticket's Completion Summary/Status/Test Summary/Files Changed fully filled in | Step 5 | Step 5 manual verify |
| Zero code/content/test drift; regression sweep green | Step 6 | Step 6 `git diff --stat` + pytest commands from `test_plan.md` |

## Anti-Drift Notes

- **The strongest temptation to guard against is "completing" this ticket by forcing content into
  one of the 6 tier-purity worlds to satisfy the letter of the original 8 ACs.** The investigation
  explicitly found this would be wrong: `crowded_frontier` in particular is mechanically capable of
  carrying `faction_tension_overrides` (it populates 6 distinct factions, more than any
  FACTION-covered world) but doing so would defeat its stress-tier single-variable isolation
  contract. Do not do this under any interpretation of "finishing the ticket."
- **Do not conflate `initial_tension_level` presence with `faction_tension_overrides` presence** —
  every resolved world spec shows `initial_tension_level` because it is a schema field on every
  `FactionSpec` defaulting to `0.0`; only a non-empty `faction_tension_overrides` in the *authored*
  `world.yaml` is genuine evidence of seeded tension. If re-verifying at implementation time, grep
  `world.yaml` (authored), not `world.resolved.yaml` (resolved output).
- **Re-verify against live `data/worlds/*/world.yaml` at implementation time, not just against this
  plan's or the investigation's tables**, per the investigation's own hazard: "corpus content can
  change between ticket pickup and implementation." If the live count has changed (e.g. a new world
  was added or an existing one's overrides removed), pause and flag rather than proceeding on stale
  numbers.
- **Do not fire or pre-decide Phase 5's Coverage Decision Gate** as part of this ticket — per the
  Closure-Mechanism Decision above, Phase 5 fires later, once Phases 2-4 have all landed, and asks a
  different (roadmap-wide cost/benefit) question than this ticket answers (ticket-scoped "is there
  remaining work"). Do not create or populate anything under
  `tickets/todos/simq-roadmap-phase5-coverage-gate/` as part of closing this ticket.
- **The sibling ticket `TCK-20260710-SIMQ-DEPTH-INFORMATION` is a separate, still-open decision** —
  do not assume its closure mechanism from this ticket's outcome, even though its own investigation
  reportedly reached a similar "zero candidates" finding (per the roadmap's Phase 3 correction note).
  It has its own investigation/plan/test_plan artifacts and must be closed on its own evidence.

## Deviations

- **Step 6 regression sweep found 2 pre-existing, unrelated test failures** (not the "0 failures"
  the plan and `test_plan.md` anticipated for a documentation-only closure).
  `test_grade_regression.py::test_grade_within_anchor_band` failed for
  `dungeon_crawl_seed42_200t` (COMBAT/PROGRESSION drift) and `urban_political_seed42_200t`
  (PROGRESSION drift). Both are unrelated to FACTION — direct inspection of
  `data/calibration/*/quality_report.json` for both worlds confirms `FACTION.grade == "S"`, well
  within the anchor band, i.e. zero FACTION-related drift. `data/calibration/` is gitignored
  (`.gitignore:240`) and untracked — these are locally-generated leftover artifacts from an
  unrelated prior run in this sandbox, not affected by this ticket's diff (which touched only 3
  doc files + the ticket file). No plan step was altered as a result; this is recorded per the
  plan's own step-6 verify instruction ("confirm all pass with 0 regressions") being honestly
  reported as "0 FACTION-related regressions, 2 pre-existing unrelated environmental failures"
  rather than silently rounding up to a clean pass. See the ticket's Test Summary for full detail.
