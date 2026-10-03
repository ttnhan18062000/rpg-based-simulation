---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK
artifact_type: plan
tags: [agent-monitoring, observability, data-quality]
---

# Implementation Plan — TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK

## Ratified Decisions (both of the ticket's own flagged open questions)

**Decision 1 — Module location: new sibling script, not an extension of
`verify_referential_integrity.py`.** Ratifying investigation.md's recommendation as-is.
`verify_referential_integrity.py`'s module docstring (`tools/agent-monitoring/
verify_referential_integrity.py:1-38`) is scoped specifically to "the 2 documented
foreign-key relationships" — a join between two different `.jsonl` files. This ticket's
check is a single-file, single-record self-consistency check (a record's own timestamp
vs. the ISO week of the folder it physically sits in) — not a join, and does not fit
`ReferentialIntegrityReport`'s dataclass shape (`verify_referential_integrity.py:136-154`,
fields `events_checked`/`events_violations`/`tools_checked`/`tools_violations` — a 2-check,
2-field-pair shape with no natural 3rd/4th bucket for "exempt" or "skipped-unparseable").
Child 6's own ratified precedent (choosing a standalone script over extending
`validate.py`) applies one level down here. New file:
`tools/agent-monitoring/verify_temporal_week_consistency.py`, importing `load_all_weeks`
and `DEFAULT_DATA_DIR` from `verify_referential_integrity.py` (documented reuse, not a
4th independent loader).

**Decision 2 — Status-vocabulary reconciliation: always `PASS`-with-evidence, reusing
the existing `PASS` value.** Ratifying the ticket's own recommended resolution, using
investigation.md's corrected fact: `run_static_precheck`'s real, current vocabulary
inside the `checks` tuple (`tools/gate_checks/done_checker_static.py:560-568`) is
`PASS`/`FAIL`/`NA` — **not** `PASS`/`FAIL`/`CLEANED` as the ticket's Request Summary
originally claimed. `CLEANED` is returned by `clean_data_runs_early`
(`done_checker_static.py:197-245`), a function that is not one of the 7 (soon 8) entries
in the `checks` tuple at all — it is called from a separate orchestrator site
(`implement-ticket.js`, between Test and Parity). `NA` already carries an incompatible,
different meaning ("this condition does not apply at this tier" — used by
`check_staging_artifacts_complete` and `check_docs_to_update_coverage` for the
hotfix-tier skip case, lines 139-140 / 509-510) — not a safe stand-in for "always
informational, never blocking." The new `check_temporal_week_consistency()` function
therefore always returns `("PASS", <evidence string carrying real counts/findings>)`,
never `"FAIL"`, regardless of what the underlying report contains. This is the smaller-
blast-radius option: it reuses an existing, compatible status value already handled by
every downstream consumer of `run_static_precheck()`'s output, instead of introducing a
4th status value (e.g. `INFO`) into this specific aggregation for the first time.

## Summary

Add a new, source-aware, report-only script (`tools/agent-monitoring/
verify_temporal_week_consistency.py`) that checks, for every record in the multi-week
`agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl` corpus, whether the record's
own authoritative timestamp field falls in the same ISO week as the folder it physically
sits in. The check is source-aware by design: a `tools.jsonl` mismatch is a genuine
anomaly (its `ts` is bit-identically the same value as the bucketing key by construction
— `post_tool_hook.py:54-60/149/159`), an `events.jsonl` mismatch is a possible-but-not-
necessarily-buggy divergence (`record_events.py:153` buckets once per batch, independent
of each event's own earlier-set `ts`), and a `runs.jsonl` mismatch is explicitly expected,
legitimate divergence (`record_run.py:85` buckets at write time, independent of
`start_ts`, which can be captured arbitrarily earlier for a long-running/paused-and-
resumed ticket). Each source's classification reuses the sanctioned
`RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` fallback lists imported directly from
`migrate_monitoring_data.py:63-70` and the tolerant `_parse_ts_to_week`/`UNKNOWN_WEEK_KEY`
parser imported from `migrate_tools_shards.py:35-49` — never re-typed. Records in the
`unknown-week` folder are structurally exempt (no real ISO week to compare against);
records in a known folder with no usable/parseable timestamp field are a third,
explicitly distinct "skipped — unparseable" bucket, neither a match nor a mismatch. The
report's `.to_text()` output labels each of the 4 buckets (match / genuine anomaly /
possible divergence / expected divergence / exempt / skipped — 6 total states across 3
sources) so a reader never has to infer which finding means "real problem" vs. "known,
harmless." The check is then wired into `done_checker_static.py::run_static_precheck()`
as an 8th Part A check, `check_temporal_week_consistency()`, always returning `PASS` with
real evidence (Decision 2 above) — extending the automatic Verify-time checklist with
information, never blocking a ticket close on its own.

## Steps

### Step 1 — Scaffold `verify_temporal_week_consistency.py`: loader reuse, field-priority
import, per-source check function, match/genuine-anomaly baseline

**Files:** `tools/agent-monitoring/verify_temporal_week_consistency.py` (new)

**Change:** Create the new module with:
- Module docstring following `verify_referential_integrity.py:1-38`'s own framing,
  explicitly stating this check's source-aware design and its report-only/never-gates
  posture (mirror `verify_referential_integrity.py:25-31`'s wording).
- `import sys; from pathlib import Path` then `sys.path.insert(0, str(Path(__file__).
  resolve().parent))` (same-directory sibling-import pattern already used by
  `migrate_monitoring_data.py:47`), then:
  - `from verify_referential_integrity import load_all_weeks, DEFAULT_DATA_DIR`
    (`verify_referential_integrity.py:45,50` — confirmed signature `load_all_weeks(data_dir:
    Path, source: str) -> list[tuple[dict, str]]`, returns `(record, week_folder_name)`
    pairs for every `agent-monitoring/data/*/<source>.jsonl` file including `unknown-week`,
    unconditionally).
  - `from migrate_monitoring_data import RUNS_FIELD_PRIORITY, EVENTS_FIELD_PRIORITY`
    (`migrate_monitoring_data.py:63-70` — confirmed by direct read this session: `RUNS_
    FIELD_PRIORITY = ["start_ts", "ts", "ts_start", "started_at", "completed_at", "ts_end",
    "finished_at", "timestamp"]`, `EVENTS_FIELD_PRIORITY` same list with `"ts"` first).
  - `from migrate_tools_shards import _parse_ts_to_week, UNKNOWN_WEEK_KEY` (`migrate_tools_
    shards.py:35,38-49` — confirmed `UNKNOWN_WEEK_KEY = "unknown-week"`; `_parse_ts_to_week
    (ts: str) -> str` returns an ISO week string `"{iso_year}-W{iso_week:02d}"` or
    `UNKNOWN_WEEK_KEY` if unparseable, never raises).
- `TOOLS_FIELD_PRIORITY = ["ts"]` — a length-1 list, module-level constant local to this
  new script (not imported, since `tools.jsonl` has never had a legacy timestamp-field
  variant beyond the single already-migrated `unknown-week` row — investigation.md's
  Malformed/Missing section). This is not a duplicate of `RUNS_FIELD_PRIORITY`/`EVENTS_
  FIELD_PRIORITY` (different list, different source, zero overlap risk with the anti-drift
  guard, which only concerns the 2 imported lists) — state this explicitly in a comment so
  a future reader does not mistake it for a re-typed copy.
- `_select_ts_value(record: dict, field_priority: list[str]) -> str | None`: returns
  `next((record.get(f) for f in field_priority if record.get(f)), None)` — same truthy-first
  selection idiom already used by `bucket_lines_by_week_multi_field`
  (`migrate_monitoring_data.py:78`), reused by description not by import (that function
  operates on raw JSONL line strings, this one on already-parsed dicts).
- `SourceFinding` dataclass (fields: `source: str`, `category_label: str` — one of
  `"genuine anomaly"` / `"possible divergence"` / `"expected divergence"`, `checked: int
  = 0` — records in a known folder with a usable, parseable field, `matched: int = 0`,
  `mismatches: list[dict] = field(default_factory=list)`, `exempt_unknown_week: int = 0`,
  `skipped_unparseable: int = 0`).
- `check_temporal_consistency(records: list[tuple[dict, str]], field_priority: list[str],
  category_label: str, source: str) -> SourceFinding`: for each `(record, week_folder)`
  pair — if `week_folder == UNKNOWN_WEEK_KEY`, increment `exempt_unknown_week`, continue;
  else select `ts_value = _select_ts_value(record, field_priority)`; if `ts_value is None`,
  increment `skipped_unparseable`, continue; else `computed_week = _parse_ts_to_week(ts_value)`;
  if `computed_week == UNKNOWN_WEEK_KEY` (value present but unparseable), increment
  `skipped_unparseable`, continue; else if `computed_week == week_folder`, increment
  `matched` and `checked`; else increment `checked` and append a mismatch dict (identifying
  fields per source — `run_id`, `seq` if present, the raw `ts_value`, `computed_week`,
  `week_folder`) to `mismatches`.
- `compute_temporal_week_consistency_report(data_dir: Path = DEFAULT_DATA_DIR) ->
  TemporalWeekConsistencyReport` (dataclass defined in Step 5, forward-declare only its
  3-field shape here as a stub if needed, or defer this function's body to Step 5 — see
  Dependency Map): loads `tools`, `events`, `runs` via `load_all_weeks(data_dir, source)`
  and calls `check_temporal_consistency` 3 times with each source's own field_priority
  and category_label (`"tools"`/`TOOLS_FIELD_PRIORITY`/`"genuine anomaly"`,
  `"events"`/`EVENTS_FIELD_PRIORITY`/`"possible divergence"`,
  `"runs"`/`RUNS_FIELD_PRIORITY`/`"expected divergence"`).

**Do NOT touch:** `verify_referential_integrity.py`'s own `ReferentialIntegrityReport`,
`check_events_to_runs`, `check_tools_to_events`, or `load_all_weeks`'s signature/behavior
— import only, no edits to that file in this step or any later step.

**Verify:** `test_tools_ts_matches_folder_no_finding` (test 1) and
`test_tools_ts_mismatch_flagged_as_genuine_anomaly` (test 2) from test_plan.md.

---

### Step 2 — Runs' "expected divergence" and events' "possible divergence" categorization

**Files:** `tools/agent-monitoring/verify_temporal_week_consistency.py`

**Change:** No new function needed beyond Step 1's `check_temporal_consistency` — this
step is the verification step that the `category_label` parameter, already wired in Step
1, correctly produces a `runs.jsonl` mismatch tagged `"expected divergence"` (never
`"genuine anomaly"`) and an `events.jsonl` mismatch tagged `"possible divergence"`. No
directionality special-case is needed: because `record_run.py:85`'s bucketing key is
always computed at write time (necessarily >= the record's own `start_ts`, which is
captured earlier in the pipeline — `record_run.py:12`, "REQUIRED field... captured at
Scope/Discover/Comprehend phase"), every `runs.jsonl` mismatch this check can ever find
has `computed_week <= week_folder` by construction — there is no legitimate "later" case
to special-case separately.

**Do NOT touch:** `record_run.py`, `record_events.py`, `post_tool_hook.py` — this ticket
verifies the write-path's consequences, never changes write-time bucketing logic
(ticket's own Out of Scope).

**Verify:** `test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly`
(test 3) — asserts the record is present in `runs`'s `SourceFinding.mismatches` with
`category_label == "expected divergence"` and absent from any anomaly-labeled bucket.

---

### Step 3 — `unknown-week` exemption bucket

**Files:** `tools/agent-monitoring/verify_temporal_week_consistency.py`

**Change:** Already implemented as part of Step 1's `check_temporal_consistency` (the
`week_folder == UNKNOWN_WEEK_KEY` branch, checked first, before any field-selection
attempt). This step is the dedicated verification pass confirming the exemption applies
uniformly to all 3 sources and is never conflated with `skipped_unparseable` (a
structurally different "cannot compute a mismatch" case — investigation.md's Anti-Drift
Hazards: "the folder itself has no real ISO week" vs. "the record landed in a real,
dateable folder but carries no timestamp-shaped field at all").

**Do NOT touch:** Do not special-case `unknown-week` inside `load_all_weeks` itself
(`verify_referential_integrity.py:50-78`) — that loader deliberately reads `unknown-week`
unconditionally into its return population for both existing FK checks; the exemption
belongs entirely inside this new script's own classification logic, not the shared loader.

**Verify:** `test_unknown_week_records_exempt_no_finding_either_way` (test 4) — one record
per source placed in `unknown-week`, asserting each lands in `exempt_unknown_week` and in
neither `matched` nor `mismatches`.

---

### Step 4 — "No usable/parseable field in a known folder" skip bucket + field-priority
reuse guard

**Files:** `tools/agent-monitoring/verify_temporal_week_consistency.py`

**Change:** Already implemented as part of Step 1's `check_temporal_consistency` (the two
`skipped_unparseable`-incrementing branches: field absent entirely, or field present but
`_parse_ts_to_week` returns `UNKNOWN_WEEK_KEY`). This step is the dedicated verification
pass confirming: (a) this 3rd bucket is distinct from both `matched` (would falsely imply
"checked and clean") and `mismatches` (would falsely imply "checked and divergent"); (b)
`RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` are genuinely imported, not re-declared —
verify via `import verify_temporal_week_consistency as vtwc; import
migrate_monitoring_data as mmd; assert vtwc.RUNS_FIELD_PRIORITY is mmd.RUNS_FIELD_PRIORITY`
(identity check, catching a copy-pasted-then-diverged list, not just an equality check).

**Do NOT touch:** Do not add a new field name to `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_
PRIORITY` in `migrate_monitoring_data.py` even if a real-corpus/synthetic case seems to
need one — those lists are the sanctioned, already-tested source of truth for where the
real corpus's rows physically landed; any perceived gap is a separate future ticket, not
an in-scope edit here (this ticket only imports and reads).

**Verify:** `test_no_usable_timestamp_field_in_known_folder_skipped_not_counted_as_match_
or_mismatch` (test 5) and `test_field_priority_reused_from_migration_not_reinvented`
(test 6).

---

### Step 5 — `TemporalWeekConsistencyReport` dataclass + `.to_text()` + `main()` CLI

**Files:** `tools/agent-monitoring/verify_temporal_week_consistency.py`

**Change:**
- `TemporalWeekConsistencyReport` dataclass: `tools: SourceFinding`, `events:
  SourceFinding`, `runs: SourceFinding`. `.to_text(sample_size: int = 20) -> str` renders
  one section per source (mirroring `ReferentialIntegrityReport.to_text()`'s structure,
  `verify_referential_integrity.py:156-180`), each section header explicitly naming its
  category label (e.g. `"tools.jsonl — ts vs. folder week (mismatches are GENUINE
  ANOMALIES)"`, `"runs.jsonl — start_ts vs. folder week (mismatches are EXPECTED
  DIVERGENCE, not bugs — see TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY)"`), then lines
  for `checked`, `matched`, `len(mismatches)` with up to `sample_size` sample entries,
  `exempt_unknown_week`, and `skipped_unparseable` — every count labeled with its own
  bucket name so no two of the 6 states (per-source: match/mismatch/exempt/skipped, with
  mismatch's meaning varying by source's `category_label`) can be confused by a reader
  scanning the text alone. Add one final summary line up top or at the end explicitly
  stating total rows checked across all 3 sources (per investigation.md's Risk #3: a
  reader must not conclude "0 mismatches" means the check is inert — carry the checked
  count alongside every violation count).
- `compute_temporal_week_consistency_report` (stub from Step 1) now returns a real
  `TemporalWeekConsistencyReport(tools=..., events=..., runs=...)`.
- `build_parser()`/`main(argv=None)` mirroring `verify_referential_integrity.py:202-226`
  exactly (`--data-dir` argument, prints `report.to_text()`, always exits 0 — report-only,
  no `--strict` flag).

**Do NOT touch:** Do not add a non-zero exit path to `main()` — this tool, like
`verify_referential_integrity.py`, never exits non-zero on violation volume (ticket's own
Out of Scope / Request Summary).

**Verify:** `test_report_distinguishes_anomaly_from_expected_divergence_in_text` (test 7)
— asserts distinct label substrings appear near each category's own counts in `.to_text()`
output, not just that all numbers appear somewhere.

---

### Step 6 — Wire `check_temporal_week_consistency()` into `done_checker_static.py`

**Files:** `tools/gate_checks/done_checker_static.py`, `tests/tools/test_done_checker_
static.py`

**Change:**
- Near the top of `done_checker_static.py`, alongside the existing `_TOOLS_DIR` sys.path
  setup (`done_checker_static.py:37-39`), add:
  ```python
  _MONITORING_DIR = _TOOLS_DIR / "agent-monitoring"
  if str(_MONITORING_DIR) not in sys.path:
      sys.path.insert(0, str(_MONITORING_DIR))

  from verify_temporal_week_consistency import compute_temporal_week_consistency_report  # noqa: E402
  ```
  (`_TOOLS_DIR = Path(__file__).resolve().parent.parent`, `done_checker_static.py:37` —
  confirmed by direct read: `done_checker_static.py` lives in `tools/gate_checks/`, so
  `_TOOLS_DIR` resolves to `tools/`, making `_MONITORING_DIR` resolve to
  `tools/agent-monitoring/`. This mirrors the file's own existing sibling-directory import
  pattern, e.g. `from validate_frontmatter import ...` at line 41, just one directory level
  further.)
- New function, placed in the Part A section alongside the other 7 `check_*` functions
  (after `check_docs_to_update_coverage`, `done_checker_static.py:552`):
  ```python
  def check_temporal_week_consistency(
      data_dir: Path = Path("agent-monitoring/data"),
  ) -> tuple[str, str]:
      """Report-only corpus-health check (TCK-20260904-MONITORING-TEMPORAL-WEEK-
      CONSISTENCY-CHECK): always returns PASS — never blocks a ticket close — but
      carries real per-source findings in its evidence string on every Verify run.
      Reuses the existing PASS status rather than introducing a new status value;
      NA already means "this condition does not apply at this tier," a different
      meaning than "informational, always non-blocking" (see this ticket's plan.md
      Decision 2). Degrades gracefully against a repo with no agent-monitoring/data/
      directory at all (e.g. _scaffold_precheck_repo's fixture) — compute_temporal_
      week_consistency_report's own load_all_weeks() calls return an empty list per
      source in that case, not an exception, matching verify_referential_integrity.
      py's own precedent.
      """
      report = compute_temporal_week_consistency_report(data_dir)
      evidence = (
          f"tools: {report.tools.checked} checked, {len(report.tools.mismatches)} genuine anomalies, "
          f"{report.tools.exempt_unknown_week} exempt, {report.tools.skipped_unparseable} skipped; "
          f"events: {report.events.checked} checked, {len(report.events.mismatches)} possible divergences, "
          f"{report.events.exempt_unknown_week} exempt, {report.events.skipped_unparseable} skipped; "
          f"runs: {report.runs.checked} checked, {len(report.runs.mismatches)} expected divergences, "
          f"{report.runs.exempt_unknown_week} exempt, {report.runs.skipped_unparseable} skipped"
      )
      return ("PASS", evidence)
  ```
- In `run_static_precheck()` (`done_checker_static.py:555-572`): add
  `("temporal_week_consistency", check_temporal_week_consistency()),` as the 8th entry in
  the `checks` tuple, and update the docstring line 556 from `"Aggregate all 7 Part A
  checks."` to `"Aggregate all 8 Part A checks."`.

**Other writers to `run_static_precheck`'s `checks` tuple (enumerated, per fact-
verification requirement 2):** `run_static_precheck()` itself is the sole writer/assembler
of this tuple — no other function in the codebase constructs or appends to it (confirmed
by the tuple being a local literal inside the function body, `done_checker_static.py:
560-568`). The only other code that *reads* the tuple's output shape is: (a)
`.claude/workflows/implement-ticket.js`'s Verify-phase orchestrator call site, which
transcribes each `{condition, status, evidence}` dict into the DoD checklist verbatim (no
transformation of status values); (b) `tests/tools/test_done_checker_static.py`'s 4
`run_static_precheck`-level tests, 3 of which key off specific `by_condition[...]` names
(unaffected by an additive 8th entry) and 1 of which (`test_run_static_precheck_all_pass_
eligible`) hardcodes the total count (must change, see below — this is not a "collision,"
it is the one test whose assertion is *by design* sensitive to the checklist's total
length, and this ticket is expected to update it, not work around it).

**Do NOT touch:** `check_events_to_runs`/`check_tools_to_events`
(`verify_referential_integrity.py`) — unrelated, independent check family per ticket's Out
of Scope. Do not change any of the other 7 `check_*` functions' own logic or return
values.

**Verify:** `test_done_checker_new_check_wired_and_returns_pass_with_evidence` (test 8,
new — add to `tests/tools/test_done_checker_static.py`'s existing `run_static_precheck
(aggregate)` section near line 593, reusing `_scaffold_precheck_repo`). Also update the
existing `test_run_static_precheck_all_pass_eligible` (currently `tests/tools/test_done_
checker_static.py:619`, asserting `len(results) == 7`) to `len(results) == 8`, and update
its explanatory comment tracking the check's own addition history (currently ending at
"...5→6→7"; append "→8"). Re-run `test_run_static_precheck_surfaces_fail_not_masked` and
`test_run_static_precheck_blocks_on_bad_priority` unmodified to confirm the new 8th check
does not disturb existing FAIL-status propagation for the other 7.

---

### Step 7 — Real-corpus smoke run; capture findings in ticket Test Summary

**Files:** `tickets/inprogress/TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-
CHECK.md` (Test Summary section), plus `tests/tools/test_verify_temporal_week_
consistency.py`

**Change:** Add `test_real_corpus_smoke_run` (test 9): calls `compute_temporal_week_
consistency_report()` against the real `agent-monitoring/data/` directory (default
`data_dir`), asserts the call succeeds and returns a well-formed
`TemporalWeekConsistencyReport` (each `SourceFinding`'s `checked`/`matched`/
`exempt_unknown_week`/`skipped_unparseable` are non-negative ints, `mismatches` is a
list) — deliberately does NOT hardcode a zero-mismatch assertion, since the corpus is
live and growing. Then run the script's own `main()` (or the library function directly)
manually against the live corpus and transcribe the actual numbers into the ticket's Test
Summary section, per investigation.md's Real Corpus Findings (Pass 2 table: expect
approximately `runs` 1394 total/5 exempt/0 skipped/~1389 match/0 mismatch, `events` 9024/
28/0/~8996/0, `tools` 186212/1/0/~186211/0 — exact totals will have grown by
implementation time since the corpus accretes a row per tool call). State explicitly in
the Test Summary, per investigation.md's Risk #3, that zero mismatches is the *expected*
first-run result (the corpus's own current week-folder layout was built by the equivalent
of this same field-priority + parser logic) and that this check's real value is
prospective — catching the first genuine future write-time-vs-record-time divergence, not
finding a retroactive problem.

**Do NOT touch:** Do not "fix" or re-bucket anything the real run surfaces — report only,
transcribe honestly (Out of Scope, and this repo's established `TCK-20260810-MONITORING-
NEGATIVE-DURATION-*` precedent for this exact "disclose honestly, never silently bulk-fix"
discipline).

**Verify:** `test_real_corpus_smoke_run` (test 9) passes; ticket's Test Summary section is
filled in with real numbers (not left as a placeholder, not assumed clean without running
it).

---

### Step 8 — `docs/agent-monitoring/schema.md` Known Limitations entry

**Files:** `docs/agent-monitoring/schema.md`

**Change:** Add a new subsection under `## Known Limitations`
(`docs/agent-monitoring/schema.md:507`), placed immediately after the existing
"### Referential Integrity Verification" entry (`schema.md:531-552`, ending at the "Full
evidence:" line 552), titled `### Temporal Week Consistency Verification`, mirroring that
entry's own structure exactly:
- What the new check does (one sentence: verifies each record's own authoritative
  timestamp is consistent with the ISO week of the folder it lives in, source-aware).
- Which fields/priority lists it reads — cross-reference the already-documented
  field-priority lists at `schema.md:119-121` (runs) and `schema.md:152-153` (events)
  rather than re-describing them; state `tools.jsonl` checks `ts` only (bit-identical to
  its own bucketing key by construction, per the write-path design documented earlier in
  this same file).
- The `unknown-week` exemption (structurally no ISO week to compare against).
- The 3-category-label design (`genuine anomaly` for `tools.jsonl`, `possible divergence`
  for `events.jsonl`, `expected divergence` for `runs.jsonl` — the last one explicitly
  legitimate per `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`'s own documented
  write-time-bucketing design, not a bug).
- Real-corpus finding summary: transcribe Step 7's actual captured numbers (not this
  investigation's scratchpad numbers verbatim — pull the implementer's own final run's
  totals from the ticket's finished Test Summary), including the "why zero mismatches is
  expected right now, not proof the check is inert" caveat from investigation.md's Risk #3.
- A pointer to this ticket's stored investigation:
  `stored_artifacts/TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK/
  investigation.md` (path effective after Finalize moves staging_artifacts to
  stored_artifacts).

Exact wording is deferred to implementation time (same precedent investigation.md cites
for child 6's own "Deferred to implementation time" Known Limitations note) — it must
describe the *finished* tool's real behavior and Step 7's real numbers, not this plan's
own draft language.

**Do NOT touch:** Any other section of `schema.md` (the "Legacy schema generations"
entry, the "Manual/ad hoc run_id convention" entry, the field-priority list definitions
themselves at lines 119-121/152-153 — reference them, do not restate or edit them). Do
not touch `docs/mechanics/*.md` or `docs/engine/*.md` — investigation.md confirms no
chapter/contract governs agent-monitoring tooling (already-established conclusion, same
as child 6 and `TCK-20260705-MONITORING-RUNID-JOIN`). Do not touch `docs/parity_ledger/
*.yaml` — no entry anywhere references agent-monitoring tool internals (investigation.md's
Parity Ledger Overlap section, "None").

**Verify:** No dedicated pytest for a doc-only change; verified by `done_checker_static.
py`'s own `check_docs_to_update_coverage` at this ticket's own Verify phase (confirms
`docs/agent-monitoring/schema.md` — the path this plan's own investigation.md flags under
"Docs Requiring Update" — actually shows up in `git status` for this ticket's diff).

## Scope Guards

- Do not modify `post_tool_hook.py`, `record_run.py`, or `record_events.py`'s write-time
  bucketing design — this ticket only verifies the existing design's consequences.
- Do not repair, re-bucket, or backfill any record found to be a genuine anomaly, possible
  divergence, or unparseable — report-only, matching every prior corpus-health tool's own
  precedent in this repo.
- Do not extend `run_static_precheck`'s status vocabulary beyond `PASS`/`FAIL`/`NA` (per
  Decision 2 above — the new check always returns `PASS`).
- Do not modify `check_events_to_runs`/`check_tools_to_events` or `ReferentialIntegrityReport`
  in `verify_referential_integrity.py` — this is an additive, independent check that only
  imports `load_all_weeks`/`DEFAULT_DATA_DIR` from that module, nothing else.
- Do not re-type `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` by hand anywhere — import
  them from `migrate_monitoring_data.py`. Do not add a new field name to either list
  in-scope of this ticket.
- Do not build a 4th independent multi-week loader — reuse `load_all_weeks()`.
- Do not conflate the `unknown-week` exemption bucket with the "no usable field in a known
  folder" skip bucket — they are two structurally different, both-legitimate "cannot
  compute a mismatch" cases and must remain two distinct counters/labels in the report.
- Do not touch `docs/mechanics/*.md`, `docs/engine/*.md`, or `docs/parity_ledger/*.yaml` —
  confirmed by investigation.md that none govern this subsystem.
- Do not modify any of the other 6 existing `check_*` functions in `done_checker_static.py`
  or their tests.

## Dependency Map

- Steps 1 → 2 → 3 → 4 → 5 are sequential within `verify_temporal_week_consistency.py`:
  each extends the same `check_temporal_consistency` function / `SourceFinding` dataclass
  built in Step 1; Steps 2-4 are verification passes over logic largely already written in
  Step 1's single function, but are kept as separate steps because each has its own
  distinct test and correctness guarantee that must be independently confirmed before
  moving on (per Step 2's note: no code changes of its own, purely a targeted-test step;
  same for Step 3).
- Step 5 (report dataclass + `.to_text()` + `main()`) depends on Steps 1-4 being complete
  (`SourceFinding` must carry all 4 buckets before `.to_text()` can render them all).
- Step 6 (done-checker wiring) depends on Step 5 — `check_temporal_week_consistency()`
  imports `compute_temporal_week_consistency_report`, which does not exist in importable
  final form until Step 5.
- Step 7 (real-corpus smoke run + Test Summary) depends on Step 5 at minimum (needs
  `compute_temporal_week_consistency_report` importable); running it after Step 6 is also
  fine and arguably more realistic (confirms the done-checker-wired path end-to-end), but
  is not a hard dependency on Step 6 specifically.
- Step 8 (docs update) depends on Step 7 — the doc entry's real-corpus numbers must come
  from Step 7's actual captured findings, not be drafted before they exist.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Check reads real multi-week corpus and correctly distinguishes, per source, genuine anomalies from expected divergence (`runs.jsonl` must not false-positive on legitimate week-spanning tickets) | Steps 1, 2, 4, 5 | `test_tools_ts_matches_folder_no_finding`, `test_tools_ts_mismatch_flagged_as_genuine_anomaly`, `test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly` |
| `unknown-week` records are structurally exempt, not miscounted | Step 3 | `test_unknown_week_records_exempt_no_finding_either_way` |
| Check wired into `done_checker_static.py::run_static_precheck()`'s Part A checklist, runs automatically at Verify time, never blocks/fails a ticket close on its own | Step 6 | `test_done_checker_new_check_wired_and_returns_pass_with_evidence`, `test_run_static_precheck_all_pass_eligible` (updated to 8) |
| Real findings from a run against the live corpus captured in ticket's Test Summary, not assumed clean | Step 7 | `test_real_corpus_smoke_run` (test executes; Test Summary content is a manual artifact this step also produces) |
| All new tests pass; existing `done_checker_static.py`/`test_done_checker_static.py` tests still pass with new check added to checklist tuple | Step 6 (regression) | Full scoped pytest run: `test_verify_temporal_week_consistency.py` + `test_done_checker_static.py` + `test_verify_referential_integrity.py` + `test_migrate_monitoring_data.py` + `test_migrate_tools_shards.py` |

## Anti-Drift Notes

- **The report-vs-communication risk is the central hazard of this whole ticket.** A
  report that does not clearly separate "this is fine, don't worry" (matched, exempt,
  expected divergence) from "this might be a real bug" (genuine anomaly) defeats the
  entire point of building the check. Every count in `.to_text()`'s output must sit next
  to an explicit label naming its own bucket — never a bare number with an implied
  meaning inferred from position or ordering alone. Test 7 (`test_report_distinguishes_
  anomaly_from_expected_divergence_in_text`) is the primary automated guard for this, but
  it only checks label *presence* near counts — during implementation, actually read the
  rendered `.to_text()` output as a first-time human reader would and confirm it reads
  unambiguously, not just that the assertion passes.
- **`runs.jsonl` "expected divergence" must never be surfaced with anomaly-toned language**
  (words like "violation," "error," "bug," "flagged") anywhere in the report or in
  `check_temporal_week_consistency()`'s evidence string — this is the single most likely
  drift a well-intentioned refactor could introduce later (e.g. someone renaming
  `mismatches` to `violations` uniformly across all 3 sources without noticing the
  connotation shift for `runs.jsonl` specifically).
- **`test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly` (test 3)
  is the single highest-priority test in this suite** — a naive, uniform "flag every
  mismatch the same way" implementation passes every other test in this plan trivially
  while failing this one, and would immediately false-positive on the first real
  long-running/paused ticket that crosses an ISO-week boundary post-migration.
- **`tests/tools/test_done_checker_static.py:619`'s `len(results) == 7` must become `8`
  in the same diff that adds the check to the `checks` tuple** — this is a known, already-
  flagged repeat-failure pattern from an earlier child in this same epic (missed-test-file
  pattern). Do not let Step 6 land without this edit; do not treat it as a pre-existing
  failure to investigate separately.
- **Zero mismatches on the first real run is the expected, correct result — not evidence
  the check is broken or pointless.** State this explicitly in both the ticket's Test
  Summary (Step 7) and the `schema.md` doc entry (Step 8): the corpus's own current
  physical layout was built using the equivalent of this exact same field-priority-lookup
  + tolerant-parser logic, so a clean first run is expected, not a sign the check has
  nothing to catch going forward.
- **Do not let the `TOOLS_FIELD_PRIORITY = ["ts"]` local constant be mistaken for a
  violation of the "import, don't re-type" guard** — that guard applies specifically to
  `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` (the 2 lists from `migrate_monitoring_
  data.py` that determined the real corpus's historical layout); `tools.jsonl`'s
  single-field check is a new, independent constant with no prior-existing canonical
  source to import from.
</content>
