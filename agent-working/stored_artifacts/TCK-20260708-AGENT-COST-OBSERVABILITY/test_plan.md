---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-COST-OBSERVABILITY
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality]
---

# Test Plan — TCK-20260708-AGENT-COST-OBSERVABILITY

## Regression Surface

All commands below MUST use `.venv/bin/python3` — the system `/usr/bin/python3` lacks `pydantic`
and fails to even collect `tests/conftest.py` (confirmed in investigation).

### Unit — `generate_retro.py` / retro reporting
- `tests/tools/test_generate_retro.py` — **11 tests, currently all passing** (confirmed live:
  `.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -q` → `11 passed`). Covers reason-
  code aggregation (3 tests) and both Tag Breakdown sections (7 tests) plus workflow-agnostic
  reason-code aggregation (1 test). None of these touch cost/spend logic today — they must remain
  green unmodified; the new spend-by-phase/spend-by-agent section must not alter any existing
  section's rendering or the conditional-render triggers for Reason Codes / Tag Breakdown.
- `tests/tools/test_tag_report.py` — sibling file sharing `categorize_tag`/`collect_completed_tickets`
  imports with `generate_retro.py`. Combined run with the above: **24 passed** (matches
  `TCK-20260708-RETRO-TAG-BREAKDOWN`'s own recorded Test Summary exactly).

### Unit — agent-monitoring write path
- `tests/tools/test_record_events.py` — validates `record_events.py`'s `validate_record`/
  `warn_vocabulary_drift`. Must stay green: `cost_proxy_score` is an unrecognized-but-passed-through
  key relative to `REQUIRED`, and this file's tests assert the exact `REQUIRED` set and rejection
  behavior — a new field must not require any change here, and a passing regression run proves that.
- `tests/tools/test_record_run.py` — unaffected (run-level record, not event-level); include for
  safety since both files were touched together in the sibling `MONITORING-SCHEMA-ENFORCEMENT`
  ticket and share the same directory/import wiring.
- `tests/tools/test_validate_agent_monitoring.py` — `validate.py`'s drift-report; unaffected by an
  additive events.jsonl field, but shares `vocabulary.py` imports — run as a low-cost regression
  check.

### Architecture guard
- `tests/tools/test_validate_agent_monitoring.py`'s single-source-of-truth guard (vocabulary module
  identity check) — confirms this ticket does not introduce a second copy of any phase/agent
  vocabulary logic. Not directly touched by this ticket's scope, but the "single source of truth"
  principle it enforces for `vocabulary.py` is the same principle the new weight constants
  (`w_bash`/`w_agent`/`w_edit`) should follow — define them once, not duplicated between
  `implement-ticket.js` and any doc/test fixture.

## New Tests Required

Per Acceptance Criteria: "Tests cover: proxy score computation against a fixture `tools.jsonl`,
retro report breakdown generation against fixture events."

1. **`test_cost_proxy_score_computation_matches_formula`**
   Category: unit
   Verifies: given a fixture `tools.jsonl` with a known mix of `Bash` (with specific `duration_ms`
   values), `Agent`, and `Read`/`Edit`/`Write`/`MultiEdit` rows for one `(run_id, seq)`, the computed
   `cost_proxy_score` equals `w_bash * Σ(bash duration_ms) + w_agent * count(Agent) + w_edit *
   count(Read|Edit|Write|MultiEdit)` using the concrete starting weights from the investigation
   (`w_bash=0.001, w_agent=50, w_edit=1`). Include a row with `duration_ms: null` (per schema,
   nullable) and confirm it contributes 0, not a `TypeError`.
   Where: since the computation lives inside `writeMonitoring`'s agent-driven Python one-liner in
   `.claude/workflows/implement-ticket.js` (no standalone Python module to unit-test directly against
   unless Plan extracts it into a testable script under `tools/agent-monitoring/`), **Plan should
   decide whether to extract the formula into a small, directly-importable helper** (e.g.
   `tools/agent-monitoring/cost_proxy.py` with a `compute_cost_proxy_score(tool_rows) -> float`
   function) so this test can import and call it directly rather than shelling out to a Python
   one-liner string embedded in a JS template literal (which is much harder to unit-test cleanly).
   Recommended location: `tests/tools/test_cost_proxy.py` (new file) if extracted, or
   `tests/tools/test_record_events.py` if folded inline — extraction is strongly preferred for
   testability and matches the existing `tools/agent-monitoring/*.py` module pattern.
   Tool call groups to fixture: at minimum one group with 0 Bash/0 Agent/N edits (should score
   `N * w_edit` exactly), one with Bash-only, one with Agent-only, one mixed.

2. **`test_cost_proxy_score_excludes_null_duration_bash_rows`**
   Category: unit
   Verifies: a `Bash` row with `duration_ms: null` (schema-documented nullable case — "null if the
   pre-hook temp file was missing") contributes 0 to the Bash-duration sum, not an error and not
   `None` propagating into the final score.
   Where: same file as test 1.

3. **`test_cost_proxy_score_field_written_to_events_jsonl`**
   Category: integration
   Verifies: after a `writeMonitoring`-equivalent run (or a direct `record_events.py --data` call
   with a `cost_proxy_score` key included), the persisted JSONL row in `events.jsonl` contains the
   `cost_proxy_score` field with the expected numeric value, and `record_events.py`'s
   `validate_record` does not reject the record (proving zero required-field or vocabulary-check
   interaction, per Anti-Drift Hazard (b)).
   Where: `tests/tools/test_record_events.py` (extend existing file — mirrors how `tool_call_count`/
   `reason_code` were tested as additive optional fields there).

4. **`test_retro_spend_by_phase_breakdown_renders_with_fixture_events`**
   Category: integration
   Verifies: given a fixture `events` list where several events (spanning >1 `phase` value) carry
   `cost_proxy_score`, `generate()`'s output contains a new spend-by-phase section with per-phase
   aggregate (e.g. sum or average) matching hand-computed expected values.
   Where: `tests/tools/test_generate_retro.py` (extend — follow the exact fixture-construction
   pattern already used by `test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve`
   and the reason-code section's tests: build minimal `runs`/`events` lists inline, call `generate()`
   directly, assert on substrings/table rows in the returned string).

5. **`test_retro_spend_by_agent_breakdown_renders_with_fixture_events`**
   Category: integration
   Verifies: same fixture-based approach, grouped by `agent` instead of `phase` — confirms the
   section (or a second table within the same section) breaks down by agent identity, matching the
   Scope's "spend-by-phase / spend-by-agent" requirement (both axes, not just one).
   Where: `tests/tools/test_generate_retro.py`.

6. **`test_retro_spend_breakdown_omitted_or_zero_safe_when_no_events_have_cost_proxy_score`**
   Category: unit / regression guard
   Verifies: a fixture `events` list where no event has `cost_proxy_score` (i.e., all historical,
   pre-this-ticket events) does not crash `generate()` and either omits the new section (preferred,
   matching the existing conditional-render pattern for Reason Codes / Tag Breakdown) or renders a
   clearly-zero/empty state — must NOT silently average in a coerced `0` for missing values (Anti-
   Drift Hazard (f) / investigation Risk #6). Assert the specific aggregate math excludes missing
   values from the denominator, not just that it "doesn't crash."
   Where: `tests/tools/test_generate_retro.py`.

7. **`test_retro_spend_breakdown_placement_does_not_disturb_tag_breakdown_sections`**
   Category: architecture guard / anti-drift
   Verifies: a fixture combining both tag-resolvable runs (triggering the two Tag Breakdown
   sections) AND cost_proxy_score-carrying events (triggering the new spend section) produces a
   report where all of: Reason Codes (if triggered), Tag Breakdown — Subsystem/Topic, Tag Breakdown
   — Process/Skill-signal, and the new spend section all appear, in the correct relative order
   (spend section after Agent Status Distribution, not interleaved with either Tag Breakdown block),
   and none of the existing sections' row content changed relative to a pre-this-ticket baseline
   fixture (guards against an accidental copy-paste edit landing inside the wrong function scope).
   Where: `tests/tools/test_generate_retro.py`.

8. **(Only if Tier 2 `self_reported_scope` is attempted per ticket's stretch scope)**
   `test_self_reported_scope_optional_field_does_not_break_existing_callers`
   Category: unit
   Verifies: an event dict omitting `self_reported_scope` entirely still validates and writes
   successfully (mirrors `test_verified_by`-style optional-field precedent from
   `TCK-20260705-GATE-DET-DONE-CHECKER`'s `DONE_SCHEMA` addition).
   Where: `tests/tools/test_record_events.py`.

## Scoped Pytest Commands

```bash
# Primary regression + new tests for this ticket's actual scope
.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py tests/tools/test_record_events.py -v

# Full sibling regression (matches the scope of the two directly-related prior tickets)
.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py tests/tools/test_tag_report.py \
  tests/tools/test_record_events.py tests/tools/test_record_run.py \
  tests/tools/test_validate_agent_monitoring.py -v

# If a new tools/agent-monitoring/cost_proxy.py module is extracted per New Tests Required item 1
.venv/bin/python3 -m pytest tests/tools/test_cost_proxy.py -v
```

Never run `pytest tests/` — scope stays inside `tests/tools/` (agent-monitoring/tooling domain);
this ticket makes zero `src/` changes so no simulation-domain test directory is in scope.

## Anti-Drift Test Guards

- **Test 7** above is the direct guard against accidentally colliding with
  `TCK-20260708-RETRO-TAG-BREAKDOWN`'s landed sections — run it as part of every Test-phase pass
  for this ticket, not just once at the end.
- **Test 2 and Test 6** together guard against the two most likely silent-drift failure modes named
  in the investigation: (a) treating a `null` `duration_ms` as `0` vs. crashing vs. correctly
  excluding it, and (b) coercing a missing `cost_proxy_score` to `0` and silently deflating
  historical-phase averages.
- Confirm **no existing test in `test_generate_retro.py` needs modification** — only additions. If
  Implement finds itself editing an existing test's assertions (rather than adding new ones), that
  is a signal the new section's insertion point landed inside the wrong function scope or altered
  shared state (`events_by_run`, `ticket_tag_map`, etc.) — stop and re-check placement against
  Anti-Drift Hazard (a) in the investigation before proceeding.
- Confirm **`REQUIRED` in `record_events.py` (line 11) is byte-for-byte unchanged** after Implement
  — a diff touching that set is an immediate scope violation (Anti-Drift Hazard (b)) and should fail
  review regardless of whether tests still pass (tests might not catch a required-field tightening
  if fixtures happen to always include the new field).
- Confirm **no `src/` file is touched** and **no `docs/parity_ledger/*.yaml` file is edited** — this
  ticket has zero parity-ledger surface (confirmed in investigation); any diff touching either is
  out of scope and should trigger a stop-and-reconsider, not a rationalization.
