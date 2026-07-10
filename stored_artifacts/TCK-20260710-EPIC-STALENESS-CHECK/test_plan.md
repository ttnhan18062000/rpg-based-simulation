---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EPIC-STALENESS-CHECK
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement, workflows, hooks]
---

# Test Plan — TCK-20260710-EPIC-STALENESS-CHECK

## Regression Surface

Unit:
- `tests/tools/test_validate_agent_monitoring.py` — must keep passing unmodified. It contains the
  single-source-of-truth vocabulary guard (imports from `tools/agent-monitoring/vocabulary.py`); if
  the new check imports any agent/phase vocabulary, it must go through the same module, not a
  parallel copy, or this guard's intent is silently defeated even though the test itself still passes.
- `tests/tools/test_generate_retro.py` — must keep passing unmodified; unrelated to this change but
  shares the `agent-monitoring/` directory tree the new script will read from, so a regression here
  would indicate an accidental shared-state or fixture collision.

Integration / behavioral (no pytest coverage today — precedent, not a gap to fix here):
- `tools/agent-monitoring/retro_nudge_hook.py` has zero automated tests (confirmed in its own
  Completion Summary: "No automated test suite exists for `.claude/` hooks in this repo... manual/
  behavioral"). This ticket's new hook-wrapper glue (stdin JSON parsing → `additionalContext` print)
  inherits the same no-pytest-coverage precedent for the *wrapper* — do not treat this as a
  regression gap; it is consistent with the existing pattern. The *staleness logic itself* (see New
  Tests Required) must be pytest-covered, unlike the wrapper.
- `.claude/settings.json` must remain valid JSON after the new hook entry is added — verify manually
  via `python3 -c "import json; json.load(open('.claude/settings.json'))"`, matching
  `TCK-20260704-RETRO-LOOP-ENFORCEMENT`'s own verification method (no dedicated test file for this;
  it's a settings file, not test-collected code).

Architecture guard (pre-existing, must still pass):
- Any test asserting `.claude/settings.json`'s existing `PreToolUse`/first-two-`PostToolUse` hook
  entries are byte-identical before/after a change (informal precedent set by
  `TCK-20260704-RETRO-LOOP-ENFORCEMENT`'s manual re-read verification, not an automated test) —
  reproduce the same manual check here: existing hook entries must not be modified, reordered, or
  removed, only appended to.

## New Tests Required

All new tests live in a new file, e.g. `tests/tools/test_epic_staleness_check.py`, importing the
staleness-detection logic as plain functions from `tools/agent-monitoring/epic_staleness_check.py`
(or wherever Plan decides to put it) — mirroring `validate.py`'s `compute_drift_report(runs, events)
-> str` shape so the logic is testable without going through the hook's stdin-JSON glue at all.

1. **`test_does_not_flag_never_started_real_obsiso_epic`** (revised — see plan.md Decision 5)
   - Category: integration (reads real repo files, no mocking)
   - **Reframed from the original plan.** The original test asserted `TCK-20260702-OBSISO-EPIC` should
     be flagged *stale*. That framing is now known to be wrong: OBSISO has **zero** matches for
     `obsiso` anywhere in `tickets/working_log.csv`, `agent-monitoring/runs.jsonl`, or
     `agent-monitoring/events.jsonl` (confirmed live evidence, investigation.md) — i.e. it was never
     started, not started-and-abandoned. Per Decision 5, "zero activity ever" is never flagged as
     stale, so the correct, corrected assertion is the opposite of the original: OBSISO must **NOT**
     appear in `find_stale_epics(...)`'s return value.
   - Verifies: running the check against the actual live repo state correctly (a) does **NOT** include
     `TCK-20260702-OBSISO-EPIC` in the stale result set, and (b) **does** include it in the
     `is_epic_never_started`-classified / informational result (i.e. `compute_stale_epics_report`'s
     "Informational: never-started epics" section contains its ID), using real
     `tickets/working_log.csv` / `agent-monitoring/runs.jsonl` data — no mocked fixtures required,
     since both conditions are already live.
   - Location: `tests/tools/test_epic_staleness_check.py`

2. **`test_does_not_flag_recently_active_epic`**
   - Category: unit (synthetic fixture — no live non-stale epic exists in the repo today, per
     investigation's Risks section)
   - Verifies: given a synthetic epic ticket (temp dir, `## Tier` → `epic`, one child ticket ID) plus
     a synthetic `working_log.csv`/`runs.jsonl` row for that child ticket with a timestamp inside the
     staleness window (e.g. yesterday), the check does NOT flag it as stale.
   - Location: `tests/tools/test_epic_staleness_check.py`

3. **`test_identifies_epic_tickets_vs_regular_tickets`**
   - Category: unit
   - Verifies: discovery correctly distinguishes `## Tier` → `epic` ticket files from `standard`/
     `hotfix` tickets in the same directory (synthetic fixture: one of each tier in a temp
     `tickets/inprogress/`-shaped dir) — only the epic-tier ticket is returned as a candidate.
   - Location: `tests/tools/test_epic_staleness_check.py`

4. **`test_handles_hybrid_folder_shape`**
   - Category: unit
   - Verifies: the `tickets/todos/{folder}/` discovery path correctly handles the confirmed-live
     hybrid shape (both a `SEQUENCE.md` AND an epic-tier ticket file directly inside the same folder,
     as `obs-isolation/` actually is) — not just a folder with only `SEQUENCE.md` or only an epic
     ticket file assumed in isolation.
   - Location: `tests/tools/test_epic_staleness_check.py`

5. **`test_handles_missing_or_malformed_sequence_md`**
   - Category: unit / failure-mode
   - Verifies: a `tickets/todos/{folder}/` directory with a `SEQUENCE.md` that is empty, contains no
     parseable `TCK-...` IDs, or is entirely absent (folder just created, epic ticket present but no
     `SEQUENCE.md` yet) does not crash the check and does not flag the folder as stale "by omission"
     (per AC #5's explicit "zero children found yet ... not flagged as stale by omission" case).
   - Location: `tests/tools/test_epic_staleness_check.py`

6. **`test_epic_with_all_children_stale`** (rewritten — see plan.md Decision 5)
   - Category: unit
   - **Reframed from the original plan.** The original fixture gave all children *zero* matching rows
     and relied on an `epic_date` fallback to flag the epic. That fallback has been removed entirely
     (Decision 5) — "zero activity ever" is now the never-started case (test 7 below), never flagged.
     This test must instead exercise the actual "started, then went idle" shape: give at least one
     child ticket ID a real, matching `working_log.csv` row and/or `runs.jsonl` record whose timestamp
     is **older** than the staleness window (e.g. 8–10 days ago, no more-recent record for any child),
     modeled on the real 8-day gap length observed in `TCK-20260702-OBSISO-EPIC`'s folder-date-to-today
     span even though OBSISO itself no longer qualifies as this case.
   - Verifies: synthetic epic whose most-recent-found child activity (across both sources) is older
     than the staleness window is flagged stale (per AC #5's first required case).
   - Location: `tests/tools/test_epic_staleness_check.py`

7. **`test_does_not_flag_never_started_epic`** (new — added per Decision 5 / user feedback)
   - Category: unit
   - Verifies: synthetic epic with non-empty child ticket IDs that have **zero** matching rows in
     either `working_log.csv` or `runs.jsonl` for **any** child, ever — with the epic ticket's own
     `date` field set deliberately old (e.g. 30 days ago) to prove age alone cannot trigger a stale
     flag — is **NOT** flagged stale by `is_epic_stale()`/`find_stale_epics(...)`, regardless of how
     old `epic_date` is. Distinct from `test_does_not_flag_recently_active_epic` (test 2), which covers
     *recent* activity; this test covers the *complete absence* of activity. Additionally assert
     `is_epic_never_started(...)` returns `True` for this candidate, confirming it is correctly
     classified as informational rather than silently dropped.
   - Location: `tests/tools/test_epic_staleness_check.py`

8. **`test_advisory_only_no_file_mutation`**
   - Category: architecture guard
   - Verifies: running the check against a real or synthetic ticket directory does not change any
     ticket file's bytes (hash file contents before/after) and never raises an exception that would
     propagate past the check's own entry point (per AC #2, mirroring `retro_nudge_hook.py`'s
     `try/except: pass` non-raising contract). Also assert no `Status:`/`## Status` field is ever
     rewritten.
   - Location: `tests/tools/test_epic_staleness_check.py`

9. **`test_working_log_dictreader_not_column_index`** (anti-drift / regression-prevention guard)
   - Category: unit
   - Verifies: the activity-lookup function correctly resolves a child ticket ID's timestamp using
     `csv.DictReader`-style field-name access, tolerating rows with non-canonical column counts (a
     synthetic malformed row, e.g. an extra unescaped comma) without misattributing a timestamp to
     the wrong ticket ID — directly targets the 25%-non-canonical-rows risk flagged in
     investigation.md's Risks section.
   - Location: `tests/tools/test_epic_staleness_check.py`

10. **(If a hook wrapper is added to `.claude/settings.json`) `test_settings_json_still_valid`**
   - Category: integration / config validity
   - Verifies: `.claude/settings.json` parses as valid JSON after the new hook entry is added, and
     that the existing `PreToolUse` array and the first two `PostToolUse` entries are unchanged
     (string-diff against a pre-change snapshot) — matching the manual verification precedent from
     `TCK-20260704-RETRO-LOOP-ENFORCEMENT`. This can be a plain script/assert run at Test phase rather
     than a permanent pytest file, consistent with hooks having no pytest-collected precedent in this
     repo — but the specific "existing entries unchanged" check should still be recorded as run
     evidence in Test Summary.

## Scoped Pytest Commands

```bash
# New test file for this ticket
pytest tests/tools/test_epic_staleness_check.py -v

# Full regression surface for the agent-monitoring tooling domain this touches
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py tests/tools/test_epic_staleness_check.py -v

# Do NOT run: pytest tests/   (repo-wide — out of scope for this domain)
```

If Plan decides to add any `record_events.py`/`record_run.py`-adjacent write path (unlikely — this
check is read-only/advisory per Scope), also scope-in
`pytest tests/tools/ -k "record" -v` at that point, not before.

## Anti-Drift Test Guards

- **No-mutation guard (test 8)** doubles as the enforcement mechanism for the ticket's Out of Scope
  item "do not automatically close/reopen/mutate any epic ticket" — a regression here would mean the
  check silently grew write behavior, which is the single most important boundary this ticket must
  not cross.
- **Never-started guard (tests 1 and 7)**, added per Decision 5 / explicit user feedback: an epic with
  zero child activity ever must never be flagged stale, no matter how old its `date:` field is — this
  is the corrected behavior, not a gap. Test 1 confirms it against the one real live epic in the repo
  (`TCK-20260702-OBSISO-EPIC`); test 7 confirms it synthetically with a deliberately old `epic_date` to
  prove age alone cannot trigger the flag. Together they are the regression guard against
  reintroducing the `epic_date` fallback branch the original plan had (see plan.md's Anti-Drift Notes).
  A future change that makes test 1 fail by flagging OBSISO as stale again is the single clearest
  signal that this exact regression has recurred.
- **Vocabulary single-source guard**: if the new script imports anything from
  `tools/agent-monitoring/vocabulary.py`, `tests/tools/test_validate_agent_monitoring.py`'s existing
  single-source guard already covers drift-prevention — no new guard needed, but confirm at
  Implement time that no parallel `WORKFLOW_AGENTS`-shaped dict gets hand-copied into the new script.
- **DictReader guard (test 9)** specifically catches the silent-false-negative failure mode
  identified in investigation.md — a naive positional CSV read that "looks correct" on the canonical
  6-column rows but silently miscounts 25% of real rows would pass a superficial smoke test and only
  fail this targeted guard.
- **Hybrid-folder guard (test 4)** exists because `obs-isolation/` is not a "clean" example of either
  documented discovery mode (`epic_id` vs. `folder`) in isolation — it is both simultaneously. A
  future refactor that "simplifies" discovery to assume mutual exclusivity between the two modes
  would silently stop detecting the repo's one real live case; this test pins that down.
- **Non-stale control guard (test 2)** exists specifically because no real epic showing genuine
  "started, then went idle within-window" activity currently exists in the repo (per investigation.md)
  — without a synthetic control test, a future change could make the check flag *every* epic
  indiscriminately (a false-positive-only detector), and neither the real OBSISO test (test 1, which
  now asserts *not* stale) nor test 7 (also asserts *not* stale) would catch that specific regression
  class, since both are "not stale" assertions. Test 2 (recently-active, not flagged) and test 6
  (old-activity, flagged) together are now the only tests exercising the actual stale/not-stale window
  boundary — no real repo data exists for either side of it as of this ticket, per investigation.md's
  Risks section, so both must remain synthetic (`tmp_path`-based) fixtures.
