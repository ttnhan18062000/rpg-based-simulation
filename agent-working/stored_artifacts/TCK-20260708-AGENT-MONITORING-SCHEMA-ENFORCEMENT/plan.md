---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
artifact_type: plan
tags: [agent-monitoring, data-quality, schema]
---

# Implementation Plan — TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT

## Summary

This plan closes the write-time validation gap in `tools/agent-monitoring/` in four layers: (1) make
`record_run.py` and `record_events.py` treat a `None`/`null` value for any `REQUIRED` field identically
to a missing key, with the null-check ordered before any line that assumes the field is a string
(`record_events.py`'s summary truncation); (2) introduce a single canonical-vocabulary Python module,
`tools/agent-monitoring/vocabulary.py`, that both the write-time warn-only check and `validate.py`'s new
drift-report import from — this is the single source of truth the ticket requires, replacing the
already-drifted doc-only vocabulary in `schema.md`; (3) wire a warn-only (never reject) `phase`/`agent`
vocabulary check into `record_events.py`, scoped per-workflow, where the workflow is inferred from the
event's `run_id` prefix (`SIMQ-AUDIT-` → simq-audit, `EPIC-`/`FOLDER-` → implement-epic,
`CREATE-TICKETS-` → create-tickets, else `TCK-` → implement-ticket) — this was confirmed by reading all
four workflow `.js` files' `run_id`-construction code, and it means **no workflow `.js` file needs to
change** to supply workflow context, keeping this ticket's Out-of-Scope guard intact; (4) extract a pure
`compute_drift_report(runs, events)` function in `validate.py` (mirroring `generate_retro.py`'s
`generate()` pattern) that reports null-required-field counts and non-canonical `phase`/`agent`/`tier`
frequency tables, wired into `main()`'s existing output. A minimal one-line pointer is added to
`schema.md` directing readers to `vocabulary.py` as the canonical source, without rewriting or expanding
the rest of the doc's phase tables.

Three of the investigation's four "open questions" are implementation-detail calls resolved directly in
this plan (see each step's rationale) — none require pausing for human input. See "Unresolved
Questions" at the end for the one item that does.

## Steps

### Step 1 — Non-null enforcement in `record_run.py`

**Files:** `tools/agent-monitoring/record_run.py`, `tests/tools/test_record_run.py` (new)

**Change:**
- Extract the validation logic currently inline in `main()` into a pure function
  `validate_record(record: dict) -> list[str]` returning a list of error strings (empty list = valid).
  Replace the current `missing = REQUIRED - set(record.keys())` (line 27) with a check that folds
  `None`-valued keys into the same `missing` set: a field counts as missing if it is absent from the
  dict **or** `record[field] is None`. Keep the existing error message format
  (`f"Missing required fields: {sorted(missing)}"`) unchanged — a `null` value must produce byte-identical
  error text to an absent key, per the investigation's confirmed requirement ("fails the same way").
- `main()` calls `validate_record(record)`; if non-empty, print each as `ERROR: {msg}` to stderr (or the
  single joined message, matching current single-message behavior) and `sys.exit(1)`, exactly as today.
- No change to `REQUIRED`, `RUNS_FILE`, the JSON-parse error path, or the `DONE:` success message.

**Do NOT touch:** Any `phase`/`agent` vocabulary logic — `record_run.py`'s records have no `phase` or
`agent` fields (those live only in `events.jsonl`); this file only ever needs the non-null check, not the
warn-only vocabulary check. Do not add a `tier` vocabulary check here either — the ticket's Scope limits
the write-time warn-only check to `phase`/`agent` in `record_events.py`; `tier` drift is surfaced only in
`validate.py`'s drift report (Step 5).

**Verify:**
- `test_record_run_null_required_field_rejected` — `{"workflow": null, ...}` fails identically to the
  key being absent (same exit code, same `ERROR:` text shape).
- `test_record_run_all_required_fields_present_and_non_null_succeeds` — a valid record with falsy-but-
  non-null values (e.g. an empty-string field, if any ever legitimately is) still succeeds; confirms the
  check is `is None`, not a truthiness check.

---

### Step 2 — Non-null enforcement in `record_events.py`, ordering-safe

**Files:** `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py` (new — this
step adds the first two tests; Step 4 appends more to the same file)

**Change:**
- Extract per-record validation into a pure function `validate_record(record: dict) -> list[str]`
  (mirrors Step 1's shape). Inside it, replace `missing = REQUIRED - set(record.keys())` (current line 31)
  with the same "absent-or-`None`" fold used in Step 1. Keep the existing `record.get("status") not in
  VALID_STATUS` check as-is (already handles `None` correctly today — no change needed there).
- **Ordering fix (the investigation's confirmed hazard):** the existing per-record loop currently runs
  `summary = record.get("summary", "")` then `len(summary)` (lines 36-38) unconditionally, even when the
  record already failed validation. Restructure so that the truncation block only runs
  `if "summary" not in missing` (i.e. only when `summary` is present and non-`None`) — this guarantees a
  `None` summary produces a clean `ERROR:` from `validate_record`, not an unhandled
  `TypeError: object of type 'NoneType' has no len()`. Do not reorder the `VALID_STATUS` check or move it
  before `validate_record` — only the summary-truncation line needs the guard.
- `main()`'s existing `errors.append(...)` / batch-level `sys.exit(1)` control flow (accumulate across all
  records, exit 1 only after the full batch is processed) stays exactly as today; only the two pieces
  above change.

**Do NOT touch:** `VALID_STATUS`'s existing reject-on-bad-value behavior (that pattern is correct
precedent, not something this ticket revises). Do not add the `phase`/`agent` vocabulary warning in this
step — that is Step 4, kept separate so this step's diff is reviewable purely as "null handling," matching
the "each step changes one thing" rule.

**Verify:**
- `test_record_events_null_required_field_rejected` — a batch with one record having `"phase": null` (or
  `"agent"`/`"summary"` null) is rejected the same way a missing key is.
- `test_record_events_null_summary_does_not_crash_before_validation` — `{"summary": null, ...}` produces a
  clean `ERROR:` exit, not a `TypeError`.

---

### Step 3 — Canonical vocabulary sidecar module

**Files:** `tools/agent-monitoring/vocabulary.py` (new)

**Change:** Create a pure-data module with no CLI, no I/O — importable by both `record_events.py` (Step 4)
and `validate.py` (Step 5). This resolves investigation Open Question #1 ("where does the canonical
vocabulary live") in favor of a shared Python module, not a JSON/YAML sidecar or doc-table: a Python
module is directly importable by both consumers with no parse step, and is the same pattern
`generate_retro.py`'s constants already use elsewhere in this directory.

Contents:
```python
# tools/agent-monitoring/vocabulary.py
"""
Canonical phase/agent/tier vocabulary for agent-monitoring writers and validators.
Single source of truth — record_events.py's warn-only check and validate.py's
drift-report both import from here. Do not duplicate these sets elsewhere
(see tests/tools/test_agent_monitoring_vocabulary.py's single-source guard).
"""

CANONICAL_TIERS = {"hotfix", "standard", "epic", "n/a"}

# Keyed by workflow name. Built by reading each workflow's .js file's actual
# phase(...)/pushEvent(...) call sites, not by copying schema.md's prose
# (schema.md's tables are already stale — see investigation.md).
WORKFLOW_PHASES = {
    "implement-ticket": {
        "Scope", "Investigate", "Plan", "Review", "Implement", "Test",
        "Parity", "Security-Review", "Verify", "Finalize",
    },
    "create-tickets": {"Comprehend", "Investigate", "Structure", "Write", "Link"},
    "implement-epic": {"Implement"},
    "simq-audit": {
        "Recalibrate", "Classify Drift", "Update Anchors", "Sync Docs",
        "Parity Check", "Verify", "Report",
    },
}

# Keyed by workflow name. Includes both .claude/agents/*.md subagent
# filenames actually invoked by that workflow AND legitimate orchestrator
# pseudo-agent names (e.g. 'workflow', 'implement-ticket-orchestrator') —
# these are NOT drift, they are the orchestrator itself logging an event
# with no delegated subagent. Confirmed by grep of pushEvent(...) call
# sites in each .claude/workflows/*.js file.
WORKFLOW_AGENTS = {
    "implement-ticket": {
        "ticket-scoper", "investigator", "planner", "architecture-reviewer",
        "implementer", "test-scoper", "parity-updater", "security-reviewer",
        "done-checker", "world-debugger", "implement-ticket-orchestrator",
    },
    "create-tickets": {"ticket-scoper"},  # extend per actual agentName values found in create-tickets.js
    "implement-epic": {"implement-ticket"},
    "simq-audit": {
        "workflow", "drift-classifier", "anchor-updater", "doc-syncer",
        "parity-updater", "done-checker", "ticket-scoper",
    },
}


def infer_workflow(run_id: str) -> str | None:
    """Infer which workflow produced a run_id, from its prefix.

    Confirmed disjoint prefixes (read directly from each workflow's .js file's
    run_id-construction code, not guessed):
      - simq-audit.js:125       runId = 'SIMQ-AUDIT-' + ...
      - implement-epic.js:216   batchRunId = 'EPIC-' + epicId | 'FOLDER-' + folder...
      - create-tickets.js:98    runId = 'CREATE-TICKETS-' + sourceSlug
      - implement-ticket.js     run_id is the literal ticket_id, 'TCK-...'

    Returns None if run_id matches no known prefix (e.g. a future 5th workflow) —
    callers must treat None as "skip the check silently," never as an error.
    """
    if run_id.startswith("SIMQ-AUDIT-"):
        return "simq-audit"
    if run_id.startswith("EPIC-") or run_id.startswith("FOLDER-"):
        return "implement-epic"
    if run_id.startswith("CREATE-TICKETS-"):
        return "create-tickets"
    if run_id.startswith("TCK-"):
        return "implement-ticket"
    return None
```

The implementer must complete `WORKFLOW_AGENTS["create-tickets"]` by grepping
`create-tickets.js` for every literal value ever assigned to the `agentName` variable used at its
`pushEvent`/`agent:` call sites (line 108's `agent: agentName` is a variable, not a literal — trace its
assignments), the same way this plan traced `simq-audit.js`'s and `implement-ticket.js`'s literal
`'workflow'` / `'implement-ticket-orchestrator'` pseudo-agent usages. Do not guess; grep and confirm.

**Do NOT touch:** `.claude/workflows/*.js` files themselves — this module only *reads* their literal
`run_id`/`phase`/`agent` values via grep during construction; it does not change how those files call
`record_events.py`/`record_run.py`.

**Verify:** No standalone test required for this step alone (it is inert data with one pure helper); its
correctness is exercised by Step 4's vocabulary-check tests and Step 6's single-source guard test. As a
sanity check before moving to Step 4, confirm `python3 -c "import vocabulary"` (from
`tools/agent-monitoring/`) succeeds with no syntax errors.

---

### Step 4 — Wire warn-only `phase`/`agent` vocabulary check into `record_events.py`

**Files:** `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py` (append)

**Change:**
- Import `WORKFLOW_PHASES`, `WORKFLOW_AGENTS`, `infer_workflow` from `vocabulary.py` (same-directory
  import — mirror however `record_events.py`/`validate.py` already resolve sibling imports, or add
  `sys.path` handling consistent with the existing file's import style if it's invoked as a standalone
  script rather than a package).
- Inside the per-record loop, **after** `validate_record` has confirmed the record has no missing/null
  required fields (this ordering matters — do not vocabulary-check a `None` phase/agent that the null
  check has already flagged as an error; skip the vocabulary check entirely for any record already in the
  error list for this iteration):
  1. `workflow = infer_workflow(record.get("run_id", ""))`.
  2. If `workflow is None` (prefix unrecognized — e.g. a future 5th workflow): skip the check silently,
     no warning, no error. This directly satisfies the "unknown workflow does not crash" test.
  3. Else, if `record["phase"] not in WORKFLOW_PHASES.get(workflow, set())`: print
     `WARNING: unrecognized phase '{record['phase']}' for workflow '{workflow}'` to stderr.
  4. Else-if (independently, not mutually exclusive with 3), if
     `record["agent"] not in WORKFLOW_AGENTS.get(workflow, set())`: print
     `WARNING: unrecognized agent '{record['agent']}' for workflow '{workflow}'` to stderr.
  5. These warnings are printed but never appended to `errors` and never affect `sys.exit` — the record
     still writes to `events.jsonl` normally. This is the ticket's core warn-never-reject guarantee.

**Do NOT touch:** Do not make this check case-sensitive-lenient or add fuzzy "did you mean" suggestion
logic beyond a literal string in the warning (the ticket's AC mentions "(did you mean ...)" phrasing as
illustrative; a plain unrecognized-value warning without a similarity-matching suggestion engine is
sufficient and keeps this step narrow — do not build a Levenshtein-distance suggester, that is scope
creep past this ticket's warn-only requirement). Do not escalate to `sys.exit(1)` under any circumstance
for a vocabulary miss — this is the single most important scope guard in this entire plan (see Anti-Drift
Notes).

**Verify:**
- `test_record_events_vocabulary_warning_unrecognized_phase` — hit case, warning printed, record still
  written (exit 0).
- `test_record_events_vocabulary_no_warning_for_canonical_phase` — miss case (paired), no warning.
- `test_record_events_vocabulary_allows_orchestrator_pseudo_agents` — `agent: "workflow"` (simq-audit) and
  `agent: "implement-ticket-orchestrator"` (implement-ticket) never warn.
- `test_record_events_vocabulary_unknown_workflow_does_not_crash` — an unrecognized `run_id` prefix
  degrades to no-check, no exception.

---

### Step 5 — Drift-report section in `validate.py`

**Files:** `tools/agent-monitoring/validate.py`, `tests/tools/test_validate_agent_monitoring.py` (new)

**Change:**
- Resolves investigation Open Question #3 in favor of the recommended refactor: extract a pure function
  `compute_drift_report(runs: list[dict], events: list[dict]) -> str` (return a formatted multi-line
  string, mirroring `generate_retro.py`'s `generate(runs, events, label) -> str` signature/style exactly,
  for testability parity with that sibling tool — construct `runs`/`events` as plain Python dicts in
  tests, no file I/O, no subprocess).
- `compute_drift_report` computes, using `vocabulary.py`'s `CANONICAL_TIERS`/`WORKFLOW_PHASES`/
  `WORKFLOW_AGENTS`/`infer_workflow`:
  1. Count of `runs` records with any `REQUIRED`-equivalent field (`workflow`, `tier`, `final_status`) set
     to `None` (read-only counting of historical drift — this does NOT gate/reject anything, `validate.py`
     never exits 1 for this; it is purely a reporting count, consistent with the "no backfill, read-side
     accommodation only" precedent from `TCK-20260705-MONITORING-RUNID-JOIN`).
  2. A frequency table (value → count) of every `phase`/`agent` value across `events` that falls outside
     `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` for its inferred workflow (skip entries whose workflow can't be
     inferred, same as Step 4).
  3. A frequency table of every `tier` value across `runs` outside `CANONICAL_TIERS`.
  4. If all three are zero/empty, the section still appears but shows explicit zero counts (per
     `test_validate_drift_report_omitted_or_zeroed_when_no_drift` — do not omit the section entirely on
     clean data; `generate_retro.py`'s precedent for an analogous "nothing to report" case is to show the
     section with a zero/empty state, not suppress it, so a reader can distinguish "checked, found none"
     from "check didn't run").
- `main()` calls `compute_drift_report(runs, events)` after its existing warning/error printing (do not
  reorder existing checks) and prints the returned string before the final `OK: {total_runs} runs, ...`
  line. This is strictly additive — `main()`'s existing exit-code contract (errors → exit 1, else exit 0
  regardless of warnings) does not change; the drift report never adds to `errors`.

**Do NOT touch:** The existing `_record_is_complete`, `LEGACY_COMPLETION_FIELDS`,
`LEGACY_TERMINAL_STATUS_VALUES`, incomplete-run detection, runs-with-no-events check, or working_log
cross-check logic (lines 40-124 in the current file) — this step only adds a new, independent section.
Do not change `validate.py`'s exit-code semantics.

**Verify:**
- `test_validate_drift_report_counts_null_required_fields` — fixture with a known count of
  null-required-field run records matches exactly.
- `test_validate_drift_report_frequency_table_non_canonical_values` — fixture with known non-canonical
  `phase`/`agent`/`tier` values produces exact per-value counts.
- `test_validate_drift_report_omitted_or_zeroed_when_no_drift` — all-clean fixture shows zero counts, not
  a missing section.

---

### Step 6 — Single-source-of-truth wiring confirmation + minimal doc pointer

**Files:** `docs/agent-monitoring/schema.md`, `tests/tools/test_agent_monitoring_vocabulary.py` (new) or
appended to `tests/tools/test_validate_agent_monitoring.py` — implementer's choice, whichever fits the
final module layout; put the single-source guard test wherever `vocabulary.py` is imported by both
consumers under test.

**Change:**
- In `docs/agent-monitoring/schema.md`, add one short note (not a rewrite of the existing phase tables)
  near the top of the "phase values" sections, e.g.: *"Canonical phase/agent values for all four
  workflows are enforced from `tools/agent-monitoring/vocabulary.py` — the tables below are illustrative
  documentation, not the source of truth; if they disagree with `vocabulary.py`, the module wins."* This
  is the minimum addition needed to satisfy AC4 ("documented as single-sourced") without expanding into a
  full `simq-audit`/`implement-epic` documentation pass, which the investigation's Anti-Drift Hazards
  section explicitly warns against as scope creep.
- Add a test asserting `record_events.py` and `validate.py` both import `WORKFLOW_PHASES`/
  `WORKFLOW_AGENTS`/`CANONICAL_TIERS`/`infer_workflow` from the same `vocabulary` module object (e.g.
  compare `record_events.vocabulary is validate.vocabulary` if both do `import vocabulary`, or an
  equivalent identity/equality check appropriate to however Step 3's import mechanics ended up wired) —
  not two independently-typed-out literal copies of the same sets.

**Do NOT touch:** Any other content in `schema.md` beyond this one pointer note — do not add
`simq-audit`'s or `implement-epic`'s phase/agent tables to the doc itself (that documentation gap is
real, per the investigation, but out of scope for this ticket; it would make a good small follow-up
ticket, not part of this one).

**Verify:** `test_canonical_vocabulary_single_sourced`.

---

### Step 7 — Regression pass

**Files:** none changed; verification only.

**Change:** none.

**Do NOT touch:** n/a.

**Verify:** Run, in order:
```bash
pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py -v
pytest tests/tools/test_generate_retro.py tests/tools/test_done_checker_static.py -v
make agent-monitoring-validate   # smoke-test against the real 466-run/1844-event files; confirm exit 0 (or pre-existing warning count) and that the new drift-report section appears and reports the known 98 workflow:null legacy records without changing the exit code
```
Confirm the real-data smoke run's drift-report null-count is 98 (or close, pending exact historical
count) for `workflow` — this is a read-only sanity check that the new counting logic works against real
historical drift, not a new gate. Do not modify `agent-monitoring/runs.jsonl`/`events.jsonl` as a result
of running this — this is a read-only validator, and the plan's scope guard against backfilling applies
here too (running `validate.py` must never write to either file).

## Scope Guards

- Do not modify `.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js`,
  `.claude/workflows/implement-epic.js`, or `.claude/workflows/simq-audit.js` in any way. The
  `infer_workflow(run_id)` prefix-matching design in Step 3 was specifically chosen because it requires
  zero changes to these files — confirmed by reading each file's `run_id`/`runId`/`batchRunId`
  construction code directly.
- Do not backfill, rewrite, or delete any existing record in `agent-monitoring/runs.jsonl` or
  `agent-monitoring/events.jsonl`. The 98 `workflow: null` records and 8-casing `phase` drift stay exactly
  as they are.
- Do not escalate the `phase`/`agent` vocabulary check from warn (stderr print) to reject (`sys.exit(1)`)
  under any circumstance, in any step. This is the single most load-bearing constraint in this plan.
- Do not add a `tier` vocabulary warn-check to `record_run.py`'s write path — the ticket's Scope limits
  the write-time check to `phase`/`agent` only; `tier` drift is surfaced read-only, in `validate.py`'s
  report (Step 5), never gated at write time.
- Do not expand `docs/agent-monitoring/schema.md` beyond the one-line pointer in Step 6 — no new phase
  tables for `simq-audit`/`implement-epic`, no broader documentation pass.
- Do not build fuzzy-matching/"did you mean" suggestion logic for the vocabulary warning — a plain
  unrecognized-value message is sufficient.
- Do not touch `_record_is_complete`, `LEGACY_COMPLETION_FIELDS`, `LEGACY_TERMINAL_STATUS_VALUES`, or any
  of `validate.py`'s three existing checks (incomplete-run, no-events, working_log cross-check).
- Do not add token-count or tool-call-count fields, or any other field not named in this ticket's Scope —
  stay confined to non-null enforcement, vocabulary warning, and drift reporting.
- No `docs/parity_ledger/` entry needs to be added or changed — confirmed in investigation.md, this is
  agent-tooling infrastructure, not simulation-engine behavior.

## Dependency Map

- Step 1 (record_run.py non-null) — independent, can run first or in parallel with Step 2.
- Step 2 (record_events.py non-null) — independent of Step 1; shares no code path.
- Step 3 (vocabulary.py) — independent of Steps 1/2; must complete before Step 4 and Step 5 (both import
  from it).
- Step 4 (record_events.py vocabulary wiring) — depends on Step 3 (imports `vocabulary.py`) and should
  land after Step 2 (both touch `record_events.py`'s per-record loop; sequencing Step 2 first keeps the
  null-check-then-vocab-check ordering explicit and avoids merge friction within the same function).
- Step 5 (validate.py drift report) — depends on Step 3 only; independent of Steps 1, 2, 4.
- Step 6 (doc pointer + single-source test) — depends on Steps 3, 4, and 5 all being in place (the test
  asserts both consumers import the same module).
- Step 7 (regression pass) — depends on all prior steps being complete.

Suggested implementation order: 1, 2, 3, 4, 5, 6, 7 (satisfies all dependencies; Steps 1 and 2 could be
swapped or done in either order relative to each other).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A record with `"workflow": null` (or any `REQUIRED` key = `None`) fails identically to a missing key | Steps 1, 2 | `test_record_run_null_required_field_rejected`, `test_record_events_null_required_field_rejected` |
| A `phase`/`agent` value outside the canonical set warns at write time and still writes | Steps 3, 4 | `test_record_events_vocabulary_warning_unrecognized_phase`, `test_record_events_vocabulary_no_warning_for_canonical_phase`, `test_record_events_vocabulary_allows_orchestrator_pseudo_agents`, `test_record_events_vocabulary_unknown_workflow_does_not_crash` |
| `make agent-monitoring-validate` output includes drift-report section with counts/frequency tables | Step 5 | `test_validate_drift_report_counts_null_required_fields`, `test_validate_drift_report_frequency_table_non_canonical_values`, `test_validate_drift_report_omitted_or_zeroed_when_no_drift` |
| Canonical vocabulary source is single-sourced, documented, no duplicate copy | Steps 3, 6 | `test_canonical_vocabulary_single_sourced` |
| Tests cover null-rejection, vocabulary warning (hit+miss), drift-report counts against a fixture | Steps 1, 2, 4, 5 | all tests listed above |

## Anti-Drift Notes

- **Ordering hazard (record_events.py):** the non-null check (Step 2) must run, and must gate the
  summary-truncation `len(summary)` line, before Step 4's vocabulary check is layered in. If a future edit
  reintroduces the truncation line unconditionally, `test_record_events_null_summary_does_not_crash_before_validation`
  will catch the regression — do not remove or weaken that test.
- **Warn-never-reject is the ticket's central constraint**, driven by the CLAUDE.md hard rule "monitoring
  write failure must never fail the workflow." Every vocabulary-check code path in Step 4 must be
  reachable only via `print(..., file=sys.stderr)`, never `sys.exit`. `test_record_events_vocabulary_warning_unrecognized_phase`
  and its sibling exist specifically to fail loudly if this is ever inverted.
- **Orchestrator pseudo-agent names (`'workflow'`, `'implement-ticket-orchestrator'`, and simq-audit's
  inline delegate labels like `'drift-classifier'`/`'anchor-updater'`/`'doc-syncer'`) are legitimate, not
  drift.** These were confirmed by direct inspection of each workflow's `.js` `pushEvent` call sites, not
  assumed. `WORKFLOW_AGENTS` in `vocabulary.py` must include all of them per-workflow, or the warn-only
  check will be noisy from its very first production run — exactly the failure mode
  `test_record_events_vocabulary_allows_orchestrator_pseudo_agents` guards against.
- **Per-workflow scoping, not a global vocabulary set,** is required — the four workflows have
  non-overlapping phase vocabularies (confirmed: `implement-ticket` 10 phases, `create-tickets` 5,
  `implement-epic` 1 observed, `simq-audit` 7). A single global set would misclassify most of
  `simq-audit`'s and `create-tickets`'s legitimate phases as drift on day one.
- **`run_id`-prefix-based workflow inference is a new design decision made in this plan** (not present in
  investigation.md, discovered by reading each workflow's `run_id` construction code during planning):
  `SIMQ-AUDIT-`, `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`, and bare `TCK-` are confirmed disjoint prefixes
  across the four workflows today. If a future 5th workflow is added with an ambiguous or colliding
  prefix, `infer_workflow` must return `None` for it (never guess wrong) — `test_record_events_vocabulary_unknown_workflow_does_not_crash`
  guards this degrade-gracefully path.
- **Historical data is read-only even in the new drift-report code.** `compute_drift_report` must never
  write to `runs.jsonl`/`events.jsonl`; `validate.py` remains a pure reader. Do not let Step 5's counting
  logic evolve into a "fix-up" pass.
- **`WORKFLOW_AGENTS["create-tickets"]` is intentionally left partially stubbed in this plan** (only
  `"ticket-scoper"` confirmed via a variable trace, not a full grep) — the implementer must complete this
  set by tracing `create-tickets.js`'s `agentName` variable assignments before Step 4 can be verified
  clean against real `create-tickets` events; do not ship a guessed/incomplete set.

## Unresolved Questions

None. The three investigation-flagged open questions (sidecar location, orchestrator pseudo-agent
representation, `validate.py` pure-function refactor) are implementation-detail decisions, resolved
directly in Steps 3, 4, and 5 above with rationale. No item in this plan requires pausing for human
review before Implement begins.

## Deviations

Recorded during Implement, per the "never silently deviate" rule.

1. **`vocabulary.py`'s `WORKFLOW_PHASES["implement-ticket"]` was missing `"Architecture-Verify"`.**
   The plan's stub module (Step 3) listed 10 phases for `implement-ticket`, omitted the distinct
   post-implementation `Architecture-Verify` phase (`.claude/workflows/implement-ticket.js:554`,
   separate from the pre-implementation `Review` phase at line 428 — both use the
   `architecture-reviewer` agent, but are two different `phase()`/`pushEvent` labels). Confirmed by
   grep of every `pushEvent(...)` call site in `implement-ticket.js` before finalizing the module,
   per the plan's own instruction not to guess. Added to the set.

2. **`vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` had `"world-debugger"` where it should
   have `"finalizer"`.** The plan's stub listed `world-debugger` as one of implement-ticket's
   canonical agents. Grepping `implement-ticket.js`'s actual `pushEvent(...)` call sites shows
   `world-debugger` never appears as an `agent:` literal anywhere in that file — it only appears in
   a doc-comment string (`suggested_skills` table entry) describing which subagent to *suggest* for
   debugging tasks, never as a monitoring-event agent value. The file's `Finalize` phase instead
   writes `agent: 'finalizer'` (three `pushEvent('Finalize', 'finalizer', ...)` call sites), which
   the plan's stub omitted entirely. Corrected: removed `world-debugger`, added `finalizer`.

3. **`WORKFLOW_AGENTS["create-tickets"]` required a new `WORKFLOW_AGENT_PREFIXES` mechanism, not
   just a completed static set.** Per the plan's explicit instruction to trace `create-tickets.js`'s
   actual `agentName` assignments (Step 3's "do not guess" note): grepping confirmed the static
   literal agent values are `'create-tickets'`, `'structure'`, `'ticket-scoper'`, `'link-epic'` — but
   the `Investigate` phase's `pushEvent('Investigate', \`investigate:${inv.concern_id}\`, ...)` call
   site (create-tickets.js) uses a *dynamically constructed* label with a stable literal prefix
   (`investigate:`) followed by a per-concern ID, not a fixed literal. A static set cannot represent
   this without either enumerating every historical `concern_id` (unbounded, wrong) or firing one
   spurious warning per concern on every `create-tickets` run (defeats the point of the check). Added
   a small `WORKFLOW_AGENT_PREFIXES` dict + `is_known_agent(workflow, agent)` helper (prefix-match
   fallback after the exact-set check) — this is the same category of "legitimate, confirmed-by-grep,
   not a guess" allowance the plan itself established for orchestrator pseudo-agent names (`'workflow'`,
   `'implement-ticket-orchestrator'`), just prefix-shaped instead of literal-shaped. It is not the
   fuzzy/"did-you-mean" suggestion logic the plan explicitly forbids — it recognizes one already-known
   dynamic literal family, it does not compute similarity against arbitrary input.

4. **Step 7's Makefile smoke test (`make agent-monitoring-validate`) does not currently exercise the
   new drift-report section end-to-end, for a reason unrelated to this ticket.** The live
   `agent-monitoring/runs.jsonl` currently has 6 pre-existing "Run with no events" errors (e.g.
   `FOLDER-phase40-44-cleanup-authoring`, `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN`) that already
   made `validate.py` exit 1 *before this ticket's changes* — confirmed via `git stash` A/B comparison
   producing byte-identical stdout/exit-code on the unmodified file. `compute_drift_report` is called
   after the existing `if errors: sys.exit(1)` check (per Step 5's explicit instruction: "prints the
   returned string before the final `OK:` line," matching the pre-existing pattern that the `OK:` line
   itself is exit-0-only) — so on the current real data it is never reached via the CLI path. This is
   not a bug in the new code; it is the designed behavior applied to a data file that already had an
   unrelated failure. Verified correctness directly instead: calling `compute_drift_report(load_jsonl(RUNS_FILE),
   load_jsonl(EVENTS_FILE))` against the real files reports `workflow: 98` exactly (matching the
   ticket's own cited figure), plus real-data non-canonical `phase`/`agent`/`tier` frequency tables
   (8+ phase casings, `epic-batch`/`epic_batch` tier duplication) consistent with the investigation.
   The 6 pre-existing errors are out of this ticket's scope (`tools/agent-monitoring/validate.py`'s
   run-with-no-events check is untouched, per the plan's scope guard) and are not fixed here.
