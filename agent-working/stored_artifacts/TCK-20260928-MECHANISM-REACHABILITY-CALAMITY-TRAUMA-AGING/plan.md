---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING
artifact_type: plan
tags: [simulation-quality, world, root-cause]
---

# Implementation Plan — TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING

## Summary
This is a bounded assessment ticket, not a fix — `investigation.md` has already produced the
four-level answer and single exit claim for each of J1 (`calamity_intensity`), J2
(`regional_trauma`), and J3 (`aging_death`/`succession`). The plan's job is to (1) transcribe those
already-derived findings into the ticket body's own sections (not re-derive them), (2) add the five
regression-pinning tests `test_plan.md` specifies (four new files/additions, one already-existing
test cited by reference only), (3) confirm no `registries/mechanisms.yaml` write is warranted by
this ticket itself — J1's write is explicitly deferred to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-
RESIDUE-RESOLUTION`, and J2/J3 already carry accurate registry evidence — and record that as an
explicit "no write performed here, by design" statement rather than a silent skip, and (4) route
findings to the systemic-world roadmap track per AC7, using the exact same append target and
sub-bullet pattern the immediately-preceding sibling ticket in this wave
(`TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY`) already used for byte-identical AC
wording: `docs/plans/systemic_world/roadmap.md`. No `src/` production code changes.

## Steps

### Step 1 — Record J1/J2/J3's four-level answers and exit claims in the ticket body
**Files:** `tickets/inprogress/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING.md`
**Change:** Populate `## Implementation Notes` with the three mechanisms' four-level answers,
transcribed from `investigation.md` (not re-derived): J1 §"J1 — `calamity_intensity`" (lines 21-70),
J2 §"J2 — `regional_trauma`" (lines 72-113), J3 §"J3 — `aging_death`/`succession`" (lines 115-183).
For each mechanism, state explicitly which level fails (J1: Level 1, structurally — zero callers,
re-confirmed independently in this planning pass via `grep -rn "apply_calamity_consequences"
src/`, which returns only the definition at `src/world/calamity.py:80` and the unrelated comment at
`src/world/displacement.py:27`, matching investigation.md's own claim exactly; J2: Level 1, by
composition/geometry, not code defect; J3: no level fails — Level 2 is a horizon-reachability
condition, not a failure) and the single exit claim per mechanism (J1: DEFECT, recorded as
recommendation only per Out of Scope; J2: CONDITION; J3: CONDITION). Also record AC3's required
statement of where each adopted ticket's existing scope does not fit, transcribed from
investigation.md lines 63-70 (J1) and 107-113 (J2).
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets` — no
change to ticket framing, only the notes/summary sections get filled in.
**Verify:** No test — this is a documentation-only step. Verified by re-reading the filled section
against `investigation.md`'s own content for fidelity (no invented claims).

### Step 2 — Record the shared-root-cause-hypothesis-checked-not-confirmed finding
**Files:** `tickets/inprogress/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING.md`
**Change:** In `## Assumptions / Open Questions`, resolve the existing "Shared-root-cause
hypothesis, flagged not assumed" bullet (ticket lines 133-136) with the answer investigation.md
already reached (lines 263-273, "Risks and Open Questions"): checked, **not confirmed**. J2's cause
is spatial isolation (`moon_cave` has no hostile faction within combat range); the out-of-scope
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` has the opposite cause — entities are correctly
co-located and deaths do occur there, but `resolve_lifecycle()`'s own death-outcome filter only
checks `outcome_kind in ("KILL", "PERMADEATH")`, missing `"DEFEAT"` (20/20 of that ticket's sampled
deaths were `"DEFEAT"`). State this plainly as a finding and stop — do not absorb the other ticket
(explicit ticket instruction, Out of Scope, and `docs/plans/world_composition_precondition_gap_
finding.md`'s own "instance 4, the exception" framing, cited at investigation.md line 255).
**Do NOT touch:** `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` itself, or its ticket file —
zero edits to that ticket.
**Verify:** No test — documentation-only. Cross-check against investigation.md lines 263-273 for
accuracy.

### Step 3 — Confirm AC6 is satisfied as "no registry write performed here, by design"
**Files:** `tickets/inprogress/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING.md`
(`## Implementation Notes` and `## Completion Summary`); no `registries/mechanisms.yaml` edit.
**Change:** Add an explicit statement (not a silent omission) that this ticket performs **zero**
writes to `registries/mechanisms.yaml`, and why, per mechanism:
- **J1**: exit claim is DEFECT, but the write is explicitly out of scope (ticket's own Out of Scope
  section, lines 71-79) — routed to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` as a
  **recommendation only**, because that ticket already owns `calamity_intensity`'s `state`
  reconciliation and two tickets must not write the same entry (confirmed by `tools/open_ticket_
  overlap.py`'s own top-hit finding, investigation.md line 78, which this plan does not re-run).
- **J2**: exit claim is CONDITION; the current registry label (`state: done`, `verified.verdict:
  contradicted`, dated 2026-09-17) already states this accurately per investigation.md line 106 —
  no correction needed.
- **J3**: exit claim is CONDITION; the registry's `aging_death`/`succession` entries already carry
  accurate, dated 2026-09-28 evidence added by the now-closed dual-writer-race ticket
  (investigation.md lines 180-183) — no correction needed.

This step touches **only prose in the ticket's own `Implementation Notes`/`Completion Summary`
sections**; it does not open `registries/mechanisms.yaml` at all. Enumerating the file's other
writers for completeness, since AC6 concerns a shared registry resource even though this ticket
does not write to it: the mechanism registry is also written by
`tools/mechanism_registry_writer.py`-driven ticket closures generally (the sanctioned write path
for any ticket that does correct a label), by `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-
RESOLUTION` once it picks up J1's recommendation (a future, independent write, not concurrent with
this ticket), and by the now-closed `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s already-
landed 2026-09-28 addenda for `aging_death`/`succession` (a completed prior write this ticket reads
but does not touch). Since this ticket writes nothing to the file, there is no ordering/race/
double-write risk to resolve — the only requirement is that the "why no write" reasoning is stated
in the ticket body rather than left implicit, satisfying AC6's own text ("any label correction is
written through the registry process... not only into planning docs" — read literally, this
applies only when a correction is made; none is made here, and that fact is now explicit rather
than a silent skip).
**Do NOT touch:** `registries/mechanisms.yaml` itself — zero byte changes to this file by this
ticket.
**Verify:** `tests/unit/tools/test_mechanism_registry.py` still passes unmodified (per test_plan.md
Registry/tooling row) — confirms registry integrity is undisturbed by a ticket that touches zero
bytes of it.

### Step 4 — Add architecture-guard test pinning J1's zero-real-callers finding
**Files:** `tests/architecture/test_calamity_intensity_producer_unwired.py` (new file)
**Change:** Add `test_calamity_producer_has_zero_real_callers`, following the source-text-scan
technique already used by `tests/architecture/test_displacement_write_paths.py:1-41` (confirmed by
direct read: it reads `src/world/displacement.py` via `Path(...).read_text()` and regex-scans for a
forbidden pattern). This new test scans every `.py` file under `src/` (via `pathlib.Path("src").
rglob("*.py")`, excluding `src/world/calamity.py` itself) for the literal call pattern
`apply_calamity_consequences(` and asserts zero matches, matching the already-verified fact (this
planning pass re-ran `grep -rn "apply_calamity_consequences" src/` directly and confirmed only the
definition at `src/world/calamity.py:80` and one comment at `src/world/displacement.py:27` exist —
no real call site anywhere). Docstring must state this test pins J1's Level-1 DEFECT finding and is
expected to start failing (in a good way) the moment a real caller is wired, per
`test_plan.md`'s own "Anti-Drift Test Guards" section.
**Do NOT touch:** `src/world/calamity.py`, `src/world/world_dynamics.py`, or any other production
file — this step adds one test file only, zero production code changes.
**Verify:** `pytest tests/architecture/test_calamity_intensity_producer_unwired.py -m "not slow"`
passes (per test_plan.md's fourth scoped pytest command).

### Step 5 — Add integration test pinning J2's moon_cave spatial-isolation CONDITION
**Files:** `tests/integration/world/test_lair_region_trauma_reachability.py` (new file)
**Change:** Add `test_moon_cave_region_records_zero_trauma_across_full_corpus_run`, running a real
`Kernel.tick_once()` loop against the `generated_frontier_3_42` world for 5000 ticks (matching the
already-cited run length in investigation.md line 83, `src/engine/world_dynamics.py`'s "Death-
triggered Trauma" block, and `RegionalConsequenceService.process_recovery()` real caller at
`src/engine/apply_plan.py:101` per investigation.md line 77 — read the actual `Kernel.tick_once()`
signature and `generated_frontier_3_42` fixture/world-loading path before writing the test, since
this plan has not independently re-verified their exact call shape; if either does not exist under
that exact name, treat as a blocker for this step specifically, not the whole ticket, and flag it
rather than fabricating a substitute). Assert `moon_cave.trauma_score == 0.0` at the end of the run.
Mirror this repo's existing corpus-run integration test structure (e.g.
`tests/integration/scenarios/test_demographics.py`, already in the regression surface) for
fixture/setup conventions rather than inventing a new harness pattern.
**Do NOT touch:** `src/world/consequences.py`, `src/engine/world_dynamics.py`, or any region/world
composition data (e.g. `moon_cave`'s `grid_bounds` or faction placement) — no attempt to "fix" the
isolation.
**Verify:** `pytest tests/integration/world/test_lair_region_trauma_reachability.py -m "not slow"`
passes (per test_plan.md's fourth scoped pytest command). This test is allowed to be slower than
typical unit tests (a 5000-tick real kernel run) — do not mark it `slow` unless it genuinely exceeds
this repo's own `slow` threshold; check `pytest.ini`/`conftest.py`'s marker definition before
deciding.

### Step 6 — Add unit test pinning J3's Level-2 horizon arithmetic
**Files:** `tests/unit/entities/test_lifecycle_horizon_constants.py` (new file)
**Change:** Add `test_default_lifespan_exceeds_corpus_run_horizon`, asserting
`LifecycleComponent().max_age_ticks == 70 * TICKS_PER_FANTASY_YEAR == 20_160_000` — confirmed
directly by this planning pass: `src/core/state.py:165` reads `max_age_ticks: int = 70 *
TICKS_PER_FANTASY_YEAR`, and `src/core/calendar.py:13` reads `TICKS_PER_FANTASY_YEAR =
TICKS_PER_DAY * DAYS_PER_SEASON * SEASONS_PER_YEAR` with `TICKS_PER_DAY = 2400`, `DAYS_PER_SEASON =
30`, `SEASONS_PER_YEAR = 4` at lines 10-13 of the same file, giving `288,000` — both read directly,
not inferred. Also assert this value exceeds a stated corpus-run-length reference constant
(`5000`) by at least three orders of magnitude (`20_160_000 / 5000 == 4032`), matching AC4's
required arithmetic exactly (ticket line 90: "roughly 20M ticks... against corpus runs of
1k-5k ticks").
**Do NOT touch:** `src/core/state.py`, `src/core/calendar.py` — no constant changes; this step only
adds an assertion that pins the current values.
**Verify:** `pytest tests/unit/entities/test_lifecycle_horizon_constants.py -m "not slow"` passes.

### Step 7 — Confirm J3's Level-4 observer-evidence test coverage, add only if a gap exists
**Files:** possibly `tests/integration/economy/test_economic_vacancy_signal.py` or
`tests/unit/observability/test_event_extractor_world_dynamics.py` (extend one, whichever is found
to not already assert the exclusion)
**Change:** Read both existing files first to confirm which (if either) already asserts (a) an
`OLD_AGE`-reason death does not produce a `CombatKillEvent`, driven by
`src/observability/event_extractor.py:462-503`'s deliberate `death_reason == "COMBAT"` gate
(investigation.md lines 162-164), and (b) a `SHOPKEEPER`/`WORKER` role-holder's `OLD_AGE` death
produces `WorldEvent(category=PRODUCTION_ROLE_VACATED)` via `EconomicVacancyService.check_and_emit()`
(`src/economy/vacancy.py:24-70`, investigation.md lines 167-169). test_plan.md item 5 (lines 98-109)
already flags this as "add only if neither already asserts the exclusion half explicitly" — do the
confirmation read before writing anything; if both assertions already exist, this step is a no-op
(state that explicitly in `## Test Summary`, do not add a duplicate test to manufacture busywork).
**Do NOT touch:** `src/observability/event_extractor.py`, `src/economy/vacancy.py` — no production
change; at most one assertion added to an existing test file.
**Verify:** Whichever scoped pytest command from test_plan.md's third group covers the extended
file passes.

### Step 8 — Route findings to the systemic-world roadmap track (AC7)
**Files:** `docs/plans/systemic_world/roadmap.md`
**Change:** `docs/plans/systemic_world/roadmap.md` §11 item 5 (lines 859-884, read directly during
planning) is the exact place Card J's three-mechanism set was originally defined — it names J1/J2/J3
by id, states the four-level method, and lists the roadmap's own exit-claim vocabulary ("acts in
ordinary runs"; "legitimately rare or conditional, with the condition stated"; "defect, routed to
separate work"; "registry label corrected"; `BLOCKED_WITH_REASON`) and is marked "*Decision point*:
owner memo decision 1." Append a new sub-bullet directly after item 5's existing content (before
item 6), titled "**Resolved for Card J (TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-
AGING, 2026-09-29)**", mirroring the exact pattern item 3 already uses for its own "Resolved for the
combat-death path" sub-bullet (lines 839-849, read directly during planning). Content: J1 maps to
"defect, routed to separate work" (recommendation only, per this ticket's Out of Scope — the actual
write belongs to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`); J2 and J3 both map to
"legitimately rare or conditional, with the condition stated" (J2: spatial isolation; J3: horizon
reachability, ~4,032x-20,160x beyond corpus run length) — neither needs a registry write. State the
shared-root-cause-hypothesis result (Step 2) in the same sub-bullet: checked, not confirmed, and
name why (opposite causes — composition-isolation for J2 vs. a death-outcome-kind filter gap for
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`).

This precedent — using `docs/plans/systemic_world/roadmap.md` as the reachable artifact for the AC
phrase "systemic-world roadmap track (`world-rule-catalog-design`)" — was independently confirmed
during planning, not assumed: `tickets/done/TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-
ENCOUNTERABILITY.md` carries the byte-identical AC wording ("Findings are routed back to the
systemic-world roadmap track (`world-rule-catalog-design`)", its own AC9) and its own Completion
Summary (lines 323-325, read directly) states it satisfied that AC by routing findings "into
`docs/plans/systemic_world/roadmap.md` §7.2.1 (new) and §11 item 3 (appended bullet)". `world-rule-
catalog-design` is otherwise a distinct name used elsewhere in this repo (e.g.
`docs/plans/simulation_semantic_control_plane/finding_triage_log.md:118-120`) for the session that
owns `docs/world_rules/` (the frozen Rule Catalog) specifically — this ticket's AC7, like its
sibling's AC9, is satisfied by the roadmap doc append, not a `docs/world_rules/` edit; note this
distinction explicitly in the ticket body so a future reader does not conflate the two.
**Do NOT touch:** `docs/world_rules/` (the frozen Rule Catalog — explicitly out of this ticket's
reach), `docs/plans/systemic_world/roadmap.md` §7.2.1 or §7.4's existing calamity/trauma bullet
(lines 659-664) — leave that pre-Card-J bounded-search paragraph as-is; it is a point-in-time
record of a different (earlier) search, not something this ticket corrects in place.
**Verify:** No test — documentation-only. Verified by re-reading the appended sub-bullet against
Steps 1-3's own ticket-body content for consistency (same exit claims, same evidence).

### Step 9 — Fill Test Summary, Files Changed, Completion Summary; move ticket to done
**Files:** `tickets/inprogress/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING.md` →
`tickets/done/`
**Change:** Run the four scoped pytest commands from `test_plan.md` (the three regression-surface
groups plus the new-tests group), record pass counts in `## Test Summary`, list every file touched
in `## Files Changed` (the ticket body, the four new/extended test files from Steps 4-7, and
`docs/plans/systemic_world/roadmap.md`), and write `## Completion Summary` following the shape of
the precedent ticket's own Completion Summary (`tickets/done/TCK-20260928-COMBAT-DEATH-TRACE-
SITUATED-ENCOUNTERABILITY.md` lines 313-326) — state plainly that this is an assessment closed by
classification, not a code fix; no `src/` file was changed; `registries/mechanisms.yaml` was read
but not written. Follow the project's standard ticket-close checklist (working log row, agent
monitoring, registry regeneration) per CLAUDE.md's "After Work" section — not detailed further here
since it is process, not implementation.
**Do NOT touch:** Anything beyond the standard closure checklist — no scope expansion at close time.
**Verify:** `done_checker`'s conditions pass, including `frontmatter_valid` and the scoped test
commands from test_plan.md all green.

## Scope Guards
- No fix for any of the three mechanisms (`CalamityService.apply_calamity_consequences`'s missing
  caller, `moon_cave`'s spatial isolation, or the aging-death horizon) — assessment and
  classification only, per the ticket's own Out of Scope.
- No write to `registries/mechanisms.yaml` for `calamity_intensity` — that write belongs to
  `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`; this ticket records a recommendation
  in its own body and in the roadmap doc append (Step 8) only.
- No fourth mechanism added to the J set — exactly J1/J2/J3, per Card J.
- No absorption of `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` or
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, even though Step 2's shared-root-cause check
  directly touches the latter's territory — state the finding (Step 2, Step 8) and stop; zero edits
  to either ticket's own file.
- No cherry-picking from the `pressure-propagation-economy` epic folder (whole-epic exclusion, per
  project convention).
- No edit to `docs/world_rules/` (the frozen Rule Catalog) — AC7's routing target is
  `docs/plans/systemic_world/roadmap.md`, confirmed by direct sibling-ticket precedent (Step 8), not
  the Catalog itself.
- No new `registries/mechanisms.yaml` schema field for Axis C (runtime reach) — `docs/plans/
  status_axis_model.md` §4 already decided against this; all new tests assert against existing
  `state`/`verified` fields and real code paths only (test_plan.md's own Anti-Drift Test Guards,
  last bullet).
- No pickup of `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`'s starvation/sleep-debt
  detection gap — distinct, already-filed follow-up, not part of J3's OLD_AGE-only scope.
- Never run `pytest tests/` (full suite) — use the four scoped commands from test_plan.md.

## Dependency Map
- Steps 1, 2, 3 (ticket-body prose) are independent of each other and of Steps 4-7 (new tests); they
  can be done in any order but are numbered for narrative flow (findings, then shared-root-cause,
  then registry-write confirmation).
- Steps 4, 5, 6, 7 (test additions) are independent of each other and of Steps 1-3 — each pins one
  mechanism's finding and can be written/verified standalone.
- Step 8 (roadmap doc append) depends on Steps 1 and 2 being finalized first, since it restates
  their conclusions — write it last among the content steps so the roadmap append and the ticket
  body never disagree.
- Step 9 (closure) depends on all of Steps 1-8 being complete and all tests passing.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — four-level answer per mechanism, or `BLOCKED_WITH_REASON`, never "fine" | Step 1 | None (documentation); cross-checked against investigation.md for no silent gaps |
| AC2 — exactly one exit claim per mechanism (condition/defect/mislabel) | Step 1 | None (documentation) |
| AC3 — adopted ticket's scope mapped onto four levels, stating where it does not fit (J1, J2) | Step 1 | None (documentation) |
| AC4 — Level 2 answered with minimum evidence, method stated and justified | Step 1 (J1/J2 method already in investigation.md), Step 6 (J3's arithmetic pinned as a test) | `tests/unit/entities/test_lifecycle_horizon_constants.py::test_default_lifespan_exceeds_corpus_run_horizon` |
| AC5 — every J3 finding names the engine commit observed | Step 1 (transcribe investigation.md's `702c3af83` / fix-commit `5d4e4a237` citations verbatim into the ticket body) | None (documentation); cross-checked against investigation.md's own commit citations |
| AC6 — any label correction written through the registry process into `registries/mechanisms.yaml` | Step 3 (explicit "no write, by design" statement covering all three mechanisms) | `tests/unit/tools/test_mechanism_registry.py` (confirms registry untouched/valid) |
| AC7 — findings routed to the systemic-world roadmap track (`world-rule-catalog-design`) | Step 8 | None (documentation); the append itself is the deliverable |

## Anti-Drift Notes
- Do not upgrade J2 or J3 from CONDITION to DEFECT, or vice versa, at implementation time — both
  exit claims are already fully derived in investigation.md; this plan transcribes, it does not
  re-derive. If new evidence during implementation contradicts investigation.md, stop and flag it
  rather than silently reclassifying.
- Do not conflate `STARVED` (Axis C: code correct, wired, data-starved — J2's and J3's shape) with
  `orphan`/dead-code (J1's deeper, zero-callers finding) — investigation.md's own note (lines
  299-301) already distinguishes these; Step 1's transcription must preserve that distinction, not
  flatten both into "condition"-adjacent language.
- J1's exit claim (DEFECT) is a **recommendation only** in this ticket — Step 3 and Step 8 must both
  state this explicitly every time J1's classification is mentioned, so a future reader never
  mistakes it for an applied registry correction.
- Step 5's new integration test (`test_moon_cave_region_records_zero_trauma_across_full_corpus_run`)
  is a "welcome failure" test by design (test_plan.md's own framing) — if it ever starts failing
  because `moon_cave`'s composition changed, that is a signal the CONDITION exit claim needs
  re-examination, not a bug in the test to be silenced or deleted.
- J3's Level-2 "not reachable within real corpus horizon" is a condition, not a defect — Step 1 and
  Step 6 must not frame it as broken code; the mechanism is proven correct via the already-merged
  fix's staged-scenario regression test (`tests/mechanic_scenarios/
  test_natural_aging_old_age_dispatch.py`), which this ticket relies on by reference and does not
  duplicate.
- Step 8's roadmap-doc append target (`docs/plans/systemic_world/roadmap.md` §11 item 5 / new
  sub-bullet) was confirmed by direct precedent, not inferred from the AC's own wording alone — if
  that file has materially changed shape by implementation time (e.g. item 5 renumbered), re-locate
  the anchor by content match ("J1 `calamity_intensity`, J2 `regional_trauma` and J3
  `aging_death`/`succession`") rather than assuming the line numbers cited here still hold.

## Deviations

- **Step 5** — no blocker: `Kernel.tick_once()` and `generated_frontier_3_42` (via
  `WorldRepository("data/worlds").load_world(...)` + `WorldCompiler.compile(spec, seed)`, mirroring
  `tests/unit/worldassembly/test_corpus_diversity.py`'s own construction shape) were directly
  callable in the exact shape needed. A real 5000-tick run was executed during implementation
  (not merely asserted) and confirmed `moon_cave.trauma_score == 0.0`, taking ~188-209s — over the
  default "medium" (60s) resource budget but well under "large" (600s). The new test is marked
  `@pytest.mark.resource_budget_large` (which forces the large budget regardless of CLI default,
  per `tests/conftest.py`), not `@pytest.mark.slow` — using `slow` would have excluded it from the
  `-m "not slow"` scoped command test_plan.md itself specifies for this test, defeating
  verification. This was independently timed and confirmed to work with the *exact* scoped command
  string from test_plan.md (no extra `--resource-budget large` CLI flag needed).
- **Step 7** — a real, narrow gap was found and closed, but in a different file than either of the
  two test_plan.md item 5 named as candidates (`tests/integration/economy/
  test_economic_vacancy_signal.py` or `tests/unit/observability/
  test_event_extractor_world_dynamics.py`). The "does emit `PRODUCTION_ROLE_VACATED`" half was
  already fully covered by the former (`test_ordinary_progression_old_age_death_fires_vacancy_
  one_tick_after_age_reaches_max`, landed by the merged dual-writer-race ticket). The "does NOT
  produce `CombatKillEvent`" half's actual pre-existing coverage lives in a third file test_plan.md
  did not name — `tests/unit/observability/test_event_extractor_world.py` (no `_dynamics` suffix;
  `test_event_extractor_world_dynamics.py` has no OLD_AGE/CombatKillEvent tests at all, confirmed
  by direct grep) — and that coverage was generic (`death_reason=None`), not naming the `"OLD_AGE"`
  literal explicitly. One new test, `test_combat_kill_not_emitted_for_old_age_death`, was added to
  that file to close the narrow, real gap. This file is consequently not part of any of the four
  named scoped pytest commands in test_plan.md verbatim; it was run and verified standalone
  (`24 passed in 0.64s`).

## Unresolved Questions
None. All four of the ticket's own stated Assumptions/Open Questions (Q1-Q4) and the shared-root-
cause hypothesis are already answered in `investigation.md` with evidence; this plan transcribes
those answers (Steps 1-2) rather than deciding anything new. One implementation-time contingency is
flagged (not a decision to make now, but a check to perform before writing code): Step 5's new test
assumes `Kernel.tick_once()` and a `generated_frontier_3_42` world-loading path exist in a directly
callable shape matching the already-passing 5000-tick run investigation.md cites — this plan did not
independently re-verify that exact call signature (unlike the `calamity.py:80` and
`src/core/state.py:165`/`calendar.py:13` citations elsewhere in this plan, which were read directly).
If Step 5's implementer finds no such directly callable path, that is a narrow, Step-5-scoped
blocker to report, not grounds to weaken or skip the test's assertion.
