---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
artifact_type: test_plan
tags: [agent-monitoring, data-quality, schema]
---

# Test Plan — TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT

## Regression Surface

No existing test file targets `tools/agent-monitoring/record_run.py`, `record_events.py`, or
`validate.py` directly (confirmed — none exist under `tests/tools/` or `tests/` today). The
regression surface is therefore the adjacent tool this ticket's change must not break:

- unit: `tests/tools/test_generate_retro.py` — must keep passing unchanged. `generate_retro.py` reads
  the same `runs.jsonl`/`events.jsonl` records this ticket's non-null/vocabulary checks gate at write
  time; if the new checks change record *shape* (e.g. reordering keys, adding new keys to the written
  record) rather than only rejecting/warning, this suite would catch an accidental shape regression.
- unit: `tests/tools/test_done_checker_static.py` — unrelated code path, but shares the
  `tools/gate_checks/` sibling directory and the `docs/agent-monitoring/schema.md` `final_status`
  vocabulary this ticket's drift-report also inspects; run to confirm no accidental cross-import or
  shared-constant breakage if a vocabulary sidecar is introduced under a shared location.
- integration/smoke: manually invoke `make agent-monitoring-validate` against the real
  `agent-monitoring/runs.jsonl`/`events.jsonl` (466 runs, 1844 events, including the 98 known
  `workflow: null` legacy records) and confirm it still exits 0 (or its pre-existing warning count) —
  the new drift-report section must be additive, not change the existing exit-code contract that
  `validate.py`'s `main()` returns (errors → exit 1, else exit 0 regardless of warnings).
- arena-combat: not applicable — this ticket touches only Claude Code agent tooling, no simulation
  engine or combat code.

## New Tests Required

Per Acceptance Criteria, all new — no existing test file to extend for `record_run.py`/
`record_events.py`. Recommended new files (mirrors `tests/tools/test_validate_frontmatter.py`'s
`importlib.util.spec_from_file_location` load pattern for hyphenated-directory imports, since
`tools/agent-monitoring/` is not a dotted-importable path from `tests/`):

1. **`test_record_run_null_required_field_rejected`**
   Category: unit (or subprocess exit-code contract, per `test_validate_frontmatter.py` Group 7 style)
   Verifies: `{"run_id": "X", "start_ts": "...", "workflow": null, "tier": "standard",
   "final_status": "DONE"}` is rejected identically to a record missing the `workflow` key entirely
   (same exit code, an `ERROR:` message on stderr).
   Location: `tests/tools/test_record_run.py` (new file).

2. **`test_record_run_all_required_fields_present_and_non_null_succeeds`**
   Category: unit / regression
   Verifies: a fully-populated valid record still appends and exits 0 — guards against the non-null
   check over-triggering on legitimate falsy-but-non-null values (e.g. `"tier": ""` should not be
   confused with `null` — confirm the check is `is None`, not a truthiness check, since `0`/`""`/`false`
   are valid non-null values for fields that might one day use them).
   Location: `tests/tools/test_record_run.py`.

3. **`test_record_events_null_required_field_rejected`**
   Category: unit
   Verifies: a batch containing one record with `"phase": null` (or `"agent": null`, `"summary": null`)
   is rejected the same way a missing key is — batch-level `sys.exit(1)`, per-record `ERROR:` line.
   Location: `tests/tools/test_record_events.py` (new file).

4. **`test_record_events_null_summary_does_not_crash_before_validation`**
   Category: unit / regression (anti-drift guard, see investigation.md's ordering hazard)
   Verifies: `{"summary": null, ...other required fields present...}` produces a clean `ERROR:` exit,
   not an unhandled `TypeError` from the existing `len(summary)` truncation line — proves the non-null
   check was placed before, not after, any line that assumes the field is a string.
   Location: `tests/tools/test_record_events.py`.

5. **`test_record_events_vocabulary_warning_unrecognized_phase`**
   Category: unit
   Verifies: `{"phase": "IMPLEMENT", "agent": "implementer", ..., "workflow"-implied context:
   "implement-ticket"}` (or however the workflow is threaded into the check) prints
   `WARNING: unrecognized phase 'IMPLEMENT' for workflow 'implement-ticket'` to stderr, and the record
   still writes successfully (exit 0 / no `ERROR:`).
   Location: `tests/tools/test_record_events.py`.

6. **`test_record_events_vocabulary_no_warning_for_canonical_phase`**
   Category: unit (miss case, paired with #5's hit case per AC's "both hit and miss cases")
   Verifies: `{"phase": "Implement", "agent": "implementer"}` for `implement-ticket` produces no
   warning at all.
   Location: `tests/tools/test_record_events.py`.

7. **`test_record_events_vocabulary_allows_orchestrator_pseudo_agents`**
   Category: unit (anti-drift guard — see investigation.md's orchestrator-agent risk)
   Verifies: `agent: "workflow"` (as used by `simq-audit.js`) and
   `agent: "implement-ticket-orchestrator"` (as used by `implement-ticket.js:718`) do NOT trigger a
   vocabulary warning — these are legitimate non-subagent values already in production use. Without
   this test, the vocabulary check could ship correct-on-paper but noisy-in-practice.
   Location: `tests/tools/test_record_events.py`.

8. **`test_record_events_vocabulary_unknown_workflow_does_not_crash`**
   Category: unit (edge case)
   Verifies: an event whose `run_id` doesn't resolve to any known `workflow` (or a workflow name not in
   the canonical vocabulary source at all, e.g. a 5th workflow added later) doesn't raise — degrades to
   "no check performed" or a generic warning, not an exception. Guards the case where the vocabulary
   sidecar lags behind a newly-added workflow (as `simq-audit` currently lags `schema.md` today).
   Location: `tests/tools/test_record_events.py`.

9. **`test_validate_drift_report_counts_null_required_fields`**
   Category: unit
   Verifies: given a fixture `runs`/`events` list with a known count of null-required-field records
   (constructed directly as Python dicts, mirroring `test_generate_retro.py`'s in-memory fixture
   style — no real file I/O), the drift-report section's null-count matches exactly. Requires
   `validate.py` to expose a pure function (e.g. `compute_drift_report(runs, events)` or an extended
   `main`) per investigation.md's refactor recommendation.
   Location: `tests/tools/test_validate_agent_monitoring.py` (new file, mirrors
   `test_generate_retro.py`'s structure).

10. **`test_validate_drift_report_frequency_table_non_canonical_values`**
    Category: unit
    Verifies: a fixture with known non-canonical `phase`/`agent`/`tier` values (e.g. `"IMPLEMENT"` vs.
    canonical `"Implement"`, `"epic-batch"` vs. `"epic_batch"`) produces a frequency table with the
    exact expected counts per distinct drifted value.
    Location: `tests/tools/test_validate_agent_monitoring.py`.

11. **`test_validate_drift_report_omitted_or_zeroed_when_no_drift`**
    Category: unit (regression / anti-drift guard)
    Verifies: an all-canonical, all-non-null fixture produces a drift-report section showing zero
    counts (or the section format `generate_retro.py`'s `test_reason_code_section_omitted_when_no_reason_codes_present`
    established for an analogous "nothing to report" case) — establishes the report doesn't
    false-positive on clean data.
    Location: `tests/tools/test_validate_agent_monitoring.py`.

12. **`test_canonical_vocabulary_single_sourced`** (architecture guard)
    Category: architecture guard
    Verifies: whatever single-source mechanism Plan/Implement choose (sidecar JSON/YAML, or a shared
    Python constants module) is actually imported by both `record_events.py`'s vocabulary check and
    `validate.py`'s drift-report, not independently duplicated — e.g. assert both modules reference the
    same file path / same Python object identity, or (weaker but still useful) assert the vocabulary
    values in each match exactly if literal duplication is chosen. Directly enforces the AC "Canonical
    phase/agent vocabulary source is documented as single-sourced (no duplicate copy between docs and
    code)."
    Location: `tests/tools/test_validate_agent_monitoring.py` or a new
    `tests/tools/test_agent_monitoring_vocabulary.py`, whichever Implement's actual module layout
    favors.

## Scoped Pytest Commands

```bash
# New tests for this ticket
pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py -v

# Regression: adjacent agent-monitoring tool tests that must not break
pytest tests/tools/test_generate_retro.py tests/tools/test_done_checker_static.py -v

# Combined scoped run for this ticket's full affected surface
pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py -v
```

Never `pytest tests/` — scope stays inside `tests/tools/` (the directory housing all agent-tooling
static/unit tests in this repo, per `tests/tools/test_done_checker_static.py`,
`test_generate_retro.py`, `test_validate_frontmatter.py`, `test_tag_registry.py` precedent).

## Anti-Drift Test Guards

- **Non-null vs. missing-key parity test** (#1, #3): asserts the *exact same* error path fires for
  `null` as for absence — prevents a future edit from special-casing `null` handling separately from
  missing-key handling and letting them silently diverge again.
- **Truthy-but-falsy regression test** (#2): explicitly locks in that `""`/`0`/`false` are NOT treated
  as null — guards against an overzealous `if not record.get(field)` implementation (falsy check)
  being substituted for the correct `is None` check, which would newly reject legitimate falsy values
  the ticket never asked to reject.
- **Warn-never-reject guard** (#5, #6): asserts exit code is 0/success even when a warning fires —
  directly enforces the CLAUDE.md hard rule "monitoring write failure must never fail the workflow" and
  the ticket's own Out of Scope ("Escalating the vocabulary check from warn to reject"). If a future
  edit flips this to `sys.exit(1)` on unrecognized vocabulary, this test fails immediately.
- **Orchestrator-pseudo-agent guard** (#7): prevents the vocabulary check from becoming noisy from its
  first real production run — without this test, the feature could pass all "clean" fixture tests
  while breaking on literally every `simq-audit`/`implement-ticket` Test-phase-cleanup-failure event in
  practice.
- **Historical-record non-backfill guard**: no test should assert anything about the shape or content
  of pre-existing `agent-monitoring/runs.jsonl`/`events.jsonl` records changing. Any new test that reads
  the real (non-fixture) `agent-monitoring/` files should assert counts/behavior are unchanged from
  before this ticket, not that the 98 legacy `workflow: null` records now pass validation — they must
  not, since this ticket does not touch historical data.
- **Single-source-of-truth guard** (#12): directly targeted at the idea doc's own stated failure mode
  ("Two copies is exactly the kind of drift this idea is trying to prevent elsewhere") — this test
  exists specifically so that if a future edit updates the vocabulary in one place (e.g. adding a new
  phase to the sidecar) without updating the other copy, a test fails instead of the drift silently
  reappearing in exactly the form this ticket was written to prevent.
