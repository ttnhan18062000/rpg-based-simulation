---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260922-CODEX-TICKETS-TO-BACKLOG
phase: done
date: 2026-09-22
tags: [ai, process-improvement]
---

# TCK-20260922-CODEX-TICKETS-TO-BACKLOG

## Title
Remove the duplicate Codex ticket copy and move the Codex runtime-activation epic to `tickets/backlogs/`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
User-requested directly. `tickets/todos/` carried a stale, redundant snapshot of the Codex
runtime-activation work: the epic and pilot ticket lived flat in `tickets/todos/` (the pilot ticket
in its real, current form — the "moved back to the backlog, 2026-09-20" note, the BLOCKED
condition, and the 2026-08-02 deferral decision), while `tickets/todos/codex-runtime-activation/`
held an older, redundant folder snapshot of just the pilot ticket, missing all three of those
passages, plus `SEQUENCE.md`. This ticket removes the stale duplicate and moves the real work to
`tickets/backlogs/codex-runtime-activation/`, matching the folder's own already-established
"moved back to the backlog" lifecycle decision physically, not just in prose.

## Scope
- Diff the two `TCK-20260730-CODEX-CONTROLLED-PILOT.md` copies to confirm the older one has
  nothing the newer one lacks before deleting it.
- Move (via `git mv`, so history follows) the epic, the newer pilot copy, and `SEQUENCE.md` into
  `tickets/backlogs/codex-runtime-activation/`.
- Delete the older, redundant folder copy outright (not moved).
- Check `validate_frontmatter.py`'s location-consistency rule for `tickets/backlogs/` and fix the
  three files' `status`/`phase` to match the real established convention for that directory.
- Convert `tests/tools/test_epic_staleness_check.py::test_real_codex_runtime_activation_folder_is_
  status_aware` to a synthetic fixture (the real path it read no longer exists), preserving the
  regression it guards (`TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP`).
- Confirm `make agent-monitoring-epic-staleness` no longer flags
  `FOLDER-tickets-todos-codex-runtime-activation`.
- Update live (non-historical) references to the old path.

## Out of Scope
- Any change to the Codex tickets' own substance (Scope, Acceptance Criteria, Assumptions) — this
  is a lifecycle/location move only, per the user's own direct instruction.
- Historical records: `stored_artifacts/`, `tickets/done/*`, `docs/plans/archive/*`,
  `tickets/working_log.csv` — left exactly as they are.
- `tickets/backlogs/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s own reference to the old
  path — investigated, found to be a historical snapshot ("as of this decision", inside a
  `RESOLVED` decision-log entry describing 2026-07-30 repo state), not a live pointer. Left
  untouched — see Implementation Notes for the reasoning.
- `tests/tools/test_epic_staleness_check.py::test_real_codex_runtime_activation_epic_is_status_
  aware` — a second, separate real-path-dependent test discovered incidentally (it reads
  `tickets/inprogress/TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md`, which already left
  `tickets/inprogress/` before this ticket started, so it is already a silent no-op, independent of
  this move). Not named in this ticket's own scope; flagged for a follow-up rather than fixed here.

## Acceptance Criteria
- [x] The older folder-copy pilot ticket confirmed (via direct diff) to contain nothing the newer
      copy lacks, before deletion.
- [x] All three files (epic, pilot, `SEQUENCE.md`) moved via `git mv` into
      `tickets/backlogs/codex-runtime-activation/`; `tickets/todos/` has no Codex files and no
      empty `codex-runtime-activation/` folder left behind.
- [x] `status`/`phase` frontmatter on the epic and pilot tickets matches the real, established
      `tickets/backlogs/` convention (`status: active`, `phase: backlog`, confirmed against
      `tickets/backlogs/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s own real precedent —
      `validate_frontmatter.py`'s location-consistency rule does not currently enforce anything for
      `tickets/backlogs/` at all, confirmed by reading `TICKET_LOCATION_RULES`, so this is matching
      a real applied convention, not satisfying an automated check).
- [x] `test_real_codex_runtime_activation_folder_is_status_aware` converted to a fully synthetic
      fixture, preserving the same `discover_candidate_epics`/`find_stale_epics`/
      `compute_stale_epics_report` pipeline coverage the original real-file test exercised.
- [x] `make agent-monitoring-epic-staleness` confirmed clean of
      `FOLDER-tickets-todos-codex-runtime-activation` — it no longer appears in any section of the
      report (stale, never-started, or BLOCKED), since the folder no longer exists.
- [x] Live references to the old path updated in `docs/ai/context_packet_exposure_mechanism_
      decision.md` (2 occurrences) and `tools/agent-monitoring/epic_staleness_check.py`'s own
      illustrative docstring example (found incidentally while checking the named files — it was
      stale on two counts, not just the folder path). Historical records left untouched.

## Related Tickets
- `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`, `TCK-20260730-CODEX-CONTROLLED-PILOT` (both moved,
  not closed — still open backlog work, per the user's own 2026-09-20 lifecycle decision recorded
  in their own bodies).
- `TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP` — the regression the converted synthetic
  test still guards.
- `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP` — precedent for the synthetic-fixture
  conversion pattern this ticket reuses (the obs-isolation replacement already in the same test
  file).

## Related Docs
- `docs/ai/context_packet_exposure_mechanism_decision.md` — 2 live path references updated.

## Related Stored Artifacts
- None — hotfix tier, self-evident intent captured here.

## Related Code Areas
- `tests/tools/test_epic_staleness_check.py` — synthetic fixture conversion, module docstring
  line-16 fix.
- `tools/agent-monitoring/epic_staleness_check.py` — one stale illustrative docstring example
  fixed (found incidentally, not part of the peer's original named scope, but genuinely stale
  active-code documentation).

## Assumptions / Open Questions
- `test_real_codex_runtime_activation_epic_is_status_aware` (a second, separate real-path-dependent
  test in the same file) is already a silent no-op independent of this move — flagged as a
  follow-up candidate, not fixed here since it wasn't named in this ticket's own scope.

## Implementation Notes
Diffed the two pilot-ticket copies directly before deleting either: the older
`tickets/todos/codex-runtime-activation/` copy is missing exactly three passages the newer flat
`tickets/todos/` copy has (the 2026-09-20 "moved back to the backlog" note, the BLOCKED condition
line, and the 2026-08-02 deferral decision paragraph) — confirmed via `diff`, not assumed; the
older copy has nothing the newer one lacks.

Checked `validate_frontmatter.py`'s `TICKET_LOCATION_RULES` directly rather than assuming: only
`tickets/done/` and `tickets/inprogress/` are currently enforced (the module's own comment says
`tickets/todos/` — and by extension `tickets/backlogs/` — is "left for a future ticket"). So there
is no automated check to satisfy for `tickets/backlogs/` today. Matched the real convention anyway
by reading an existing `tickets/backlogs/` ticket
(`TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`: `status: active`, `phase: backlog`) and
applying the same values, since `phase: backlog` is already a registered `PHASE_VALUES` enum member
clearly intended for exactly this directory, even though nothing currently enforces it there.

Converted the target test following the exact precedent already established in the same file (the
obs-isolation → synthetic-never-started-folder-epic replacement, `TCK-20260817-TESTS-TOOLS-LANE-
STALE-REFERENCE-SWEEP`): kept the same assertions and pipeline coverage
(`discover_candidate_epics`/`is_epic_blocked`/`find_stale_epics`/`compute_stale_epics_report`), but
built the fixture from `_write_ticket()` + a synthetic `SEQUENCE.md` instead of copying real repo
files. Also fixed the module docstring's line-16 mention (now stale — the folder it named is no
longer under `tickets/todos/` at all).

While checking the two named "other references" files, found the reference in
`tickets/backlogs/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` is inside a `RESOLVED`
decision-log entry explicitly framed "as of this decision" (2026-07-30) — a historical snapshot,
not a live pointer describing current state. Left it untouched, matching the "leave historical
records alone" instruction's spirit even though this specific file wasn't named in that exclusion
list verbatim. Separately found `epic_staleness_check.py`'s own illustrative docstring example
(not named in the original scope) was stale on two counts — the folder path, and its claim that the
real governing epic "lives in tickets/inprogress/", which was already false before this move — and
fixed it too, since it's live, maintained source-code documentation, not a historical record.

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_epic_staleness_check.py tests/tools/test_validate_frontmatter.py -q
# 132 passed
```
`make agent-monitoring-epic-staleness` run against the real repo: `FOLDER-tickets-todos-codex-
runtime-activation` confirmed absent from all three report sections (stale, never-started,
BLOCKED). `python3 tools/validate_frontmatter.py` run individually against both moved ticket
files: clean. `make knowledge-index-update` run (docs/ changed). `graphify update .` run (tools/
`.py` changed).

## Files Changed
- `tickets/todos/TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md` → `tickets/backlogs/codex-runtime-
  activation/TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md` (git mv; `phase: open` → `phase:
  backlog`; one dated move note added).
- `tickets/todos/TCK-20260730-CODEX-CONTROLLED-PILOT.md` → `tickets/backlogs/codex-runtime-
  activation/TCK-20260730-CODEX-CONTROLLED-PILOT.md` (git mv; `phase: open` → `phase: backlog`; one
  dated move note added).
- `tickets/todos/codex-runtime-activation/SEQUENCE.md` → `tickets/backlogs/codex-runtime-
  activation/SEQUENCE.md` (git mv, unchanged content).
- `tickets/todos/codex-runtime-activation/TCK-20260730-CODEX-CONTROLLED-PILOT.md` — deleted (the
  older, redundant duplicate).
- `tests/tools/test_epic_staleness_check.py` — synthetic fixture conversion, module docstring fix.
- `tools/agent-monitoring/epic_staleness_check.py` — one stale docstring example fixed.
- `docs/ai/context_packet_exposure_mechanism_decision.md` — 2 stale path references updated.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of this closure.

## Completion Summary
Removed the stale, redundant Codex-pilot duplicate and physically moved the real Codex runtime-
activation work (epic, pilot ticket, sequence file) to `tickets/backlogs/`, matching the lifecycle
decision the tickets' own bodies already recorded in prose since 2026-09-20. Matched the real,
established `tickets/backlogs/` frontmatter convention even though no automated check currently
enforces one for that directory (confirmed by reading the validator's own rule table, not
assumed). Converted the one named real-path-dependent test to a synthetic fixture preserving its
full pipeline coverage, and fixed the stale docstring references this move exposed — both the
named test-file line and one incidentally-found stale example in the check module's own live
source. Confirmed live via `make agent-monitoring-epic-staleness` that the folder-mode candidate
is fully gone, not just relabeled. Left every historical record (`stored_artifacts/`, `tickets/
done/`, `docs/plans/archive/`, `working_log.csv`, and one `RESOLVED`-decision-log reference)
untouched. Flagged one adjacent, already-broken (independent of this move) test as a follow-up
candidate rather than silently expanding this ticket's own scope to fix it.
