---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATUS-DRIFT-REPAIR
artifact_type: plan
tags: [data-quality, agent-monitoring, observability]
---

# Implementation Plan — TCK-20260718-STATUS-DRIFT-REPAIR

## Summary

This plan repairs two independent historical data-drift bugs and ships a regression check so
neither recurs silently. Part A rewrites the `## Status` body value to `DONE` on the 71 approved
`tickets/done/*.md` files (single-line diff per file, nothing else touched). Part B normalizes
`final_status` to `"DONE"` on 7 named `agent-monitoring/runs.jsonl` records via line-scoped string
substitution (not a JSON round-trip, to guarantee byte-identical non-target lines), with a short
`docs/agent-monitoring/schema.md` note documenting this as a one-time, audited exception to the
file's stated append-only contract (Step 3b — added per architecture review; the file remains
append-only for all new writes going forward). Part C ships
`tools/gate_checks/status_drift_check.py` — a new, unwired, MARKER-JSON gate check mirroring
`doc_staleness_check.py`'s shape — with full pytest coverage, using structural (value-based /
filename-pattern-based) exemptions rather than a literal allowlist. The plan resolves the one open
question left by investigation.md (whether the 6 same-line colon-suffixed `## Status: X` files are
in scope for Part A) by explicitly excluding them — see "Colon-Suffixed Files Decision" below — and
requires the new checker's regex to be byte-identical to the baseline scan regex so it does not
newly flag those 6 files as regressions against the approved 71/12/83 baseline.

## Colon-Suffixed Files Decision (resolves investigation.md's open question)

**Decision: the 6 same-line colon-suffixed files are excluded from this ticket's Part A fix.**

Files: `TCK-20260322-BWS_PROTO.md`, `TCK-20260401-FINAL-CONVERGENCE.md`,
`TCK-20260401-FINAL-NON-PARTIAL-TASKS.md`, `TCK-20260403-FINAL-CONVERGENCE.md`,
`TCK-20260405-SKILL-SCALING.md`, `TCK-20260407-PH0-FIX.md` (all currently `## Status: INPROGRESS`,
same-line format).

Reasoning:
1. The ticket's own Scope item 1 and every Acceptance Criterion are anchored to an explicit,
   previously-agreed count — "71 files" / "12 documented exceptions" / "83 total" — all derived
   using one specific regex (`^## Status\s*\n+\s*(\S+)`, multiline). These 6 files were discovered
   *during this investigation pass*, via a different, broader regex sweep, after ticket scope was
   already fixed. They are new information, not part of what was scoped.
2. CLAUDE.md's planning rule is explicit: "Never plan more work than the ticket scope. If the
   investigation reveals adjacent problems, note them as future tickets — do not add them to this
   plan." Including these 6 files would silently expand Scope item 1's count from 71 to 77 and
   would require rewriting the ticket's own AC language — an action outside the planner's remit for
   an already-approved ticket.
3. The two formats are structurally different (colon-suffixed single-line vs. two-line). Mixing a
   second substitution pattern into what is designed as one narrow, uniform single-line replace
   increases the risk of an inconsistent diff shape across the 71-file set, threatening AC2's "1
   changed line per file, verified via `git diff --stat`" guarantee if the two patterns are not
   equally trivial to apply and verify.
4. This exclusion is also what keeps Part C's checker regex-compatible with the approved baseline
   (see Anti-Drift Notes) — leaving these 6 files unfixed and undetected by the checker is one
   consistent, intentional position, not two separate judgment calls.

Action: these 6 files are **not touched** by Step 2. They are recorded here as a candidate for a
future, separately-scoped ticket (extend or add a second regex to the checker, plus a matching
Part-A-style bulk fix for the colon-suffixed corpus). This plan does not create that ticket; it only
flags the recommendation.

## Steps

### Step 1 — Derive and freeze the authoritative Part A file list
**Files:** `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/derive_status_drift_scope.py` (new, one-off)

**Change:** Write a standalone script that:
- Scans `tickets/done/*.md` with the exact baseline regex `^## Status\s*\n+\s*(\S+)` (multiline,
  same as investigation.md's re-derivation).
- Excludes files where the captured value (case-insensitive) is `EPIC_SCOPED` or `SCOPED`
  (value-based epic-tier exemption).
- Excludes files whose filename does not start with `TCK-` (pattern-based legacy exemption).
- Prints the remaining in-scope file list, sorted, with current (soon-to-be-replaced) value per
  file, and the total count.
- Separately runs the broader same-line sweep (`^## Status\b(.*)$`) to enumerate the 6 colon-suffixed
  drift files, and asserts they are disjoint from the in-scope list produced above (defensive check
  that the exclusion decision above is actually being honored, not accidentally reversed by a regex
  bug).
- Fails loudly (non-zero exit, clear message) if the in-scope count is not 71, or if any of the 12
  known exceptions is missing from the exception set, or if the disjointness assertion fails —
  surfacing any delta since 2026-07-18 (new ticket closes happen continuously per
  investigation.md's own caveat) so the implementer can reconcile before Step 2 runs.

**Do NOT touch:** No file writes in this step — read-only derivation only. Do not fix or normalize
anything yet.

**Verify:** Manual run of the script; assert printed count is 71 and the exception/colon-suffixed
sets exactly match investigation.md's documented lists (or, if a delta is found, the implementer
reconciles and records the delta before proceeding — this step is the single checkpoint where that
reconciliation must happen, not silently inside Step 2).

---

### Step 2 — Bulk-fix `## Status` on the 71 in-scope `tickets/done/*.md` files
**Files:**
- `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/fix_status_drift_tickets.py` (new, one-off)
- The 71 target files under `tickets/done/*.md` (see investigation.md's authoritative list; re-derive via Step 1's script rather than trusting the static list, per investigation.md's own caveat)

**Change:** Write a script that:
- Consumes Step 1's frozen in-scope list (re-run Step 1's derivation inline or import it — do not
  hand-maintain a second copy of the list).
- For each file, replaces only the captured value token (`\S+` immediately following `## Status`,
  possibly across a blank line) with `DONE`. Must handle both layouts seen in the corpus: value on
  the line immediately after `## Status`, and a blank line between `## Status` and the value (e.g.
  `TCK-20260415-WS-CLEANUP.md`). The substitution must not restructure or normalize the blank-line
  convention — only the token itself changes.
- Asserts, per file, that exactly one substitution was made (fail loudly if 0 or >1 — signals either
  a file already fixed or a format the regex didn't anticipate).
- Before writing any file, asserts the target filename is a member of Step 1's frozen 71-file list
  and is not a member of the 12-exception set or the 6-colon-suffixed set (defense against scope
  creep from a stale or hand-edited file list).
- Writes each file back in place, changing only that one line.

**Do NOT touch:**
- The 7 epic-tier files (`## Status` value `EPIC_SCOPED`/`SCOPED` is correct as-is).
- The 5 `resource_v2_*.md` legacy-naming files.
- The 6 colon-suffixed files (see "Colon-Suffixed Files Decision" above).
- Any frontmatter, any other body section, or any whitespace outside the single value token, in any
  of the 71 files.
- The duplicated `## Tier\n## Tier` heading glitch in the two `E-NARRATIVE-CONSEQUENCE`/
  `E-WORLD-EVOLUTION` epic files — ticket Scope item 4 marks this opportunistic-only and not
  required; this plan does not schedule it as a step. If the implementer happens to be in one of
  those two files for an unrelated reason and the fix is trivially a single added/removed line, it
  may be applied as an incidental aside documented separately in the ticket's Implementation Notes —
  do not seek it out proactively, and do not let it expand the diff footprint of Step 2's 71-file
  change set.

**Verify:** AC1 (re-run the Part A scan post-fix — via Step 1's script again — returns exactly the
12 documented exceptions and zero other non-`DONE` results) and AC2 (`git diff --stat tickets/done/`
shows exactly 71 files changed, each with a 1-line diff).

---

### Step 3 — Line-scoped `runs.jsonl` normalizer for the 7 target records
**Files:**
- `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/fix_runs_jsonl_final_status.py` (new, one-off)
- `agent-monitoring/runs.jsonl` (7 lines edited)

**Change:** Write a script that:
- Reads all lines of `agent-monitoring/runs.jsonl` (expect 641; if the count differs, the file has
  grown since scoping — do not trust the fixed 0-indexed line numbers from investigation.md blindly;
  locate the 7 target lines by `run_id` match and confirm against the expected line-number range as
  a cross-check, since `record_run.py` only appends so existing offsets should be stable, but verify
  rather than assume).
- For each of the 7 target records, confirms the line's `run_id` matches the expected value from the
  ticket's table before touching it (defensive check against a stale line-number assumption).
- Applies exactly one string substitution per line: `'"final_status":"done"'` →
  `'"final_status":"DONE"'` for `TCK-20260610-WORKER-SINGLETON-GUARD`, and
  `'"final_status":"success"'` → `'"final_status":"DONE"'` for the other 6 records. Asserts the
  substituted-count is exactly 1 per target line (fail loudly on 0 or >1 — signals the byte-layout
  assumption from investigation.md no longer holds).
- Does **not** run any `json.loads`/`json.dumps` round trip on any line, target or otherwise — pure
  string substitution only, per investigation.md's explicit recommendation (avoids key-order,
  spacing, and number-formatting risk entirely).
- Writes all lines back via a temp-file-plus-atomic-rename (avoid partial-write corruption).

**Do NOT touch:**
- Any field other than `final_status` on the 7 target lines (no backfilling `ticket_id`,
  `agent_count`, `duration_s`, timestamps, etc.).
- Any of the other ~634 lines in `runs.jsonl`, including the ~98 legacy-shaped `status`/
  `started_at`/`completed_at` records — different schema, out of scope.
- `LEGACY_TERMINAL_STATUS_VALUES` in `tools/agent-monitoring/validate.py` — orthogonal
  completeness-tolerance logic, not this ticket's casing-correctness concern.
- `tools/agent-monitoring/record_run.py` — read for reference only, not modified.

**Verify:** AC3 (JSON-parsing scan confirms all 7 target `run_id`s have `final_status == "DONE"`
exactly), AC4 (line count unchanged, all non-target lines byte-identical pre/post), AC5
(`python3 tools/agent-monitoring/validate.py` exits 0).

---

### Step 3b — Document the append-only exception in `docs/agent-monitoring/schema.md`
**Files:** `docs/agent-monitoring/schema.md`

**Change:** `agent-monitoring/runs.jsonl` is documented at schema.md line 11 as one of "Two
append-only JSONL files, joined by `run_id`," and its sole existing writer,
`tools/agent-monitoring/record_run.py`, is docstring'd "Append a run record..." with its only file
operation being `open(RUNS_FILE, "a")` — confirmed by direct read of both. Every prior commit
touching `runs.jsonl` (e.g. `3ddb7480`, TCK-20260705-WORKING-LOG-BACKFILL: 1 file changed, 1
insertion(+), 0 deletions) has been a pure append. Step 3 of this plan is the first-ever in-place
edit to an existing `runs.jsonl` line, and nothing currently records that departure for a future
reader of schema.md's append-only claim or of `git blame` on those 7 lines.

Add a short paragraph to schema.md's `## agent-monitoring/runs.jsonl` section (or an equally durable
location such as a new "Historical Corrections" note within that same file) stating: 7 records had
their `final_status` casing corrected in place by TCK-20260718-STATUS-DRIFT-REPAIR via an atomic,
audited line-scoped rewrite (not a bulk parse/re-serialize), and that the file remains append-only
going forward for all *new* writes — this is a one-time historical exception, not a change to the
write contract. This is a documentation addition only; it does not change Step 3's script logic,
which is unaffected by this step and may be implemented independently.

**Do NOT touch:** `record_run.py`'s append-only implementation (unaffected — this step documents an
exception to policy prose, it does not add a new writer or a rewrite helper); any other section of
`schema.md` beyond the one paragraph/note being added.

**Verify:** Manual review — `docs/agent-monitoring/schema.md` contains a clear, dated note
explaining the Step 3 in-place edit as a one-time historical correction, distinct from the file's
ongoing append-only contract for new writes. No automated test required (this is documentation
traceability, not behavior); covered by the ticket's "Update docs if behavior changed" Definition of
Done item rather than a new AC.

---

### Step 4 — New regression check: `tools/gate_checks/status_drift_check.py` + pytest coverage
**Files:**
- `tools/gate_checks/status_drift_check.py` (new)
- `tests/tools/test_status_drift_check.py` (new)

**Change:** Mirror `doc_staleness_check.py`'s and `workflow_meta_conformance.py`'s established shape
exactly: docstring citing this ticket and the drift found, one or more aggregate `check_*()`
functions returning `List[dict]` (`{"status": "PASS"|"FAIL", "evidence": "..."}`), a
`MARKER:` + `json.dumps(result)` stdout contract in `__main__`, non-zero exit if any entry is `FAIL`.

Implement three functions:
- `check_ticket_status_drift(done_dir: Path) -> List[dict]` — scans `*.md` files in `done_dir` using
  the **exact baseline regex** `^## Status\s*\n+\s*(\S+)` (multiline; must be byte-identical to the
  regex used in Steps 1-2 and in investigation.md — see Anti-Drift Notes). For each match, flags
  `FAIL` if the captured value's uppercase form is not `DONE`, UNLESS: the value (uppercased) is in
  `{"EPIC_SCOPED", "SCOPED"}` (value-based epic-tier exemption), OR the filename does not start with
  `TCK-` (pattern-based legacy exemption). One `PASS`/`FAIL` entry per flagged file, plus a summary
  `PASS` entry when the corpus is clean.
- `check_runs_jsonl_final_status_drift(runs_path: Path) -> List[dict]` — parses each line of the
  target `runs.jsonl`-shaped file as JSON. Skips (does not evaluate) any record that lacks a
  `final_status` key — this is the legacy `status`/`started_at` schema, out of Part B's scope by
  design, not a parsing failure. For records that do have `final_status`, flags `FAIL` if the value
  is not equal to its own uppercase form.
- `check_status_drift(done_dir: Path, runs_path: Path) -> List[dict]` — aggregate entry point
  combining both scans' results (mirrors the "one aggregate function" shape other `gate_checks`
  scripts use for their public API, while keeping the two scans as separately testable internal
  functions since they cover unrelated corpora).

Docstring must explicitly state:
1. Origin: TCK-20260718-STATUS-DRIFT-REPAIR, the 83/71/12 baseline this check's Part A regex must
   stay consistent with.
2. **Known, intentional limitation**: the ticket-status regex does not detect the same-line
   colon-suffixed `## Status: X` format (12 files use it corpus-wide, 6 currently non-`DONE` as of
   2026-07-18) — this is deliberate, not an oversight, to avoid the checker flagging files the
   originating ticket explicitly did not fix (see this plan's "Colon-Suffixed Files Decision").
   Candidate for a future, separately-scoped ticket.
3. Ships unwired: no `Makefile` target, no `.claude/workflows/*.js` invocation added in this ticket
   — a future ticket decides where/whether to call it, matching `doc_staleness_check.py`'s and
   `workflow_meta_conformance.py`'s own stated precedent.

Test file `tests/tools/test_status_drift_check.py`, `tmp_path`-fixture style (mirror
`test_workflow_meta_conformance.py`'s fixture pattern), covering all 10 cases from test_plan.md:
`test_clean_corpus_passes`, `test_stale_ticket_status_flagged`, `test_lowercase_final_status_flagged`,
`test_epic_tier_exception_ignored_by_value`, `test_legacy_naming_file_ignored_by_pattern`,
`test_legacy_runs_jsonl_shape_ignored`, `test_same_line_colon_status_format_not_newly_flagged`,
`test_check_is_read_only`, `test_marker_json_output_contract`,
`test_exit_code_nonzero_on_any_fail_zero_on_clean`.

**Do NOT touch:**
- `tools/agent-monitoring/validate.py` — read-only reference for shape/constraints, not extended.
  (Investigation's Part C design-choice question is resolved here: new standalone script, per
  investigation.md's own recommendation — it fits `gate_checks/*.py`'s MARKER-JSON pattern more
  closely than `validate.py`'s WARNING/ERROR-print contract, and avoids bolting a ticket-body-text
  scan onto a module whose current concern is `runs.jsonl`/`events.jsonl`/`tools.jsonl`/
  `working_log.csv` only.)
- `Makefile` — no new target added in this ticket.
- `.claude/workflows/*.js` — no wiring added in this ticket.
- `dashboard-frontend/src/components/GanttBar.tsx` — read-only reference only.

**Verify:** `pytest tests/tools/test_status_drift_check.py -v` — all 10 tests pass. Maps to AC6, AC7
(fixture half), AC8.

---

### Step 5 — Full-corpus clean verification and regression suite
**Files:** none changed — verification only.

**Change:**
1. Run `python3 tools/gate_checks/status_drift_check.py` (or its `check_status_drift()` invoked
   against the live `tickets/done/` + `agent-monitoring/runs.jsonl` paths) against the now-fixed
   corpus; assert the `MARKER:` JSON payload is all-`PASS` and process exit code is 0. This is AC7's
   live-corpus half (Step 4 only proved it against fixtures).
2. Run the regression surface from test_plan.md:
   ```
   pytest tests/tools/test_status_drift_check.py -v
   pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_run.py \
          tests/tools/test_doc_staleness_check.py tests/tools/test_workflow_meta_conformance.py \
          tests/tools/test_generate_retro.py tests/tools/test_validate_frontmatter.py -v
   ```
3. Re-run `python3 tools/agent-monitoring/validate.py`; assert exit code 0 (re-confirms AC5 after
   Step 4's new file additions).
4. Manual trace (no `GanttBar.tsx` edit): confirm `classifyFinalStatus('DONE')` — the corrected
   value for all 7 records — returns `'done'` per the function body already read in investigation.md.
   Existing `dashboard-frontend/src/test/GanttBar.test.tsx` fixtures (lines 18, 95) already exercise
   `final_status: 'DONE'`; no new frontend test is required per the AC's "existing/new test, or
   manual trace" language.
5. Final sanity: `git status`/`git diff --stat` across the whole repo shows only: the 71 ticket
   files (Step 2), `agent-monitoring/runs.jsonl` (Step 3), `docs/agent-monitoring/schema.md` (Step
   3b), the two new `tools/gate_checks/` + `tests/tools/` files (Step 4), and the staging-artifact
   scripts/docs for this ticket. Nothing else moved. This list is also what the ticket's own
   `## Files Changed` section should enumerate at close: the 71 `tickets/done/*.md` files,
   `agent-monitoring/runs.jsonl`, `docs/agent-monitoring/schema.md`,
   `tools/gate_checks/status_drift_check.py`, `tests/tools/test_status_drift_check.py`, plus the
   staging-artifact one-off scripts under `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/`.

**Do NOT touch:** Nothing new — this step is verification-only, no file writes.

**Verify:** AC1–AC9 collectively confirmed clean; this is the ticket's final acceptance gate before
moving to `tickets/done/`.

## Scope Guards

- Do not modify the `## Status` value of the 7 epic-tier files (`EPIC_SCOPED`/`SCOPED` is correct).
- Do not modify the `## Status` value of the 5 `resource_v2_*.md` legacy-naming files.
- Do not modify the `## Status` value of the 6 same-line colon-suffixed files — explicitly excluded
  by this plan's decision above, not silently omitted.
- Do not touch any field other than `final_status` on the 7 named `runs.jsonl` records.
- Do not touch any of the ~98 legacy-shaped `status`/`started_at` records in `runs.jsonl`.
- Do not narrow, remove, or otherwise treat `LEGACY_TERMINAL_STATUS_VALUES` in `validate.py` as
  "fixed" by this ticket — it is an orthogonal, intentional tolerance list.
- Do not modify `implement-ticket.js`'s Finalize phase — already correct for new closes.
- Do not modify `dashboard-frontend/src/components/GanttBar.tsx` — `classifyFinalStatus()` is
  correct as written; only the underlying data was wrong.
- Do not wire `status_drift_check.py` into `Makefile` or any `.claude/workflows/*.js` file in this
  ticket — ships unwired, matching `doc_staleness_check.py`/`workflow_meta_conformance.py` precedent.
- Do not use a broader or "cleaner" status-extraction regex in the new checker than the baseline
  `^## Status\s*\n+\s*(\S+)` — doing so would newly flag the 6 colon-suffixed files and break the
  clean-corpus AC.
- Do not hardcode the 7 epic-tier or 5 legacy filenames as literal string lists in the checker — use
  the structural (value-based / filename-pattern-based) exemptions specified in Step 4.
- Do not perform a `json.loads`/`json.dumps` round trip on any line of `runs.jsonl` — line-scoped
  string substitution only.
- Do not run the full `pytest tests/` suite — scope to `tests/tools/` per the project testing rule.
- Do not pursue the duplicated `## Tier\n## Tier` heading glitch as a scheduled step — opportunistic
  only, per ticket Scope item 4.

## Dependency Map

- Step 1 → Step 2 (Step 2 consumes Step 1's frozen/reconciled 71-file list; must not proceed on a
  stale or hand-typed list).
- Step 2 → Step 5 (live-corpus clean-check needs the ticket files already fixed).
- Step 3 → Step 5 (live-corpus clean-check needs `runs.jsonl` already fixed).
- Step 3 → Step 3b (the doc note describes the edit Step 3 performs; write the note after or
  alongside Step 3, not before — it should describe what was actually done, not a plan).
- Step 4 → Step 5 (the checker must exist before it can be run against the live corpus).
- Step 3 is independent of Steps 1–2 (different corpus, `runs.jsonl` vs. `tickets/done/*.md`) and
  may be done in parallel with them.
- Step 3b is independent of Steps 1, 2, and 4 (pure documentation, no shared file or code path);
  it only depends on Step 3 having actually run.
- Step 4's code and its own pytest suite (fixture-based) are independent of Steps 1–3/3b and may be
  developed in parallel; only Step 4's *live-corpus* invocation (folded into Step 5) has a hard
  dependency on Steps 2 and 3 being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Re-running Part A scan returns exactly 12 exceptions, zero other results | Step 1 (derivation), Step 2 (fix) | Step 1/2 script output; re-run post-fix |
| Each of the 71 files shows a single-line diff | Step 2 | `git diff --stat tickets/done/` |
| All 7 named `runs.jsonl` records have `final_status == "DONE"` (JSON-parsing scan) | Step 3 | Manual JSON-parsing scan (test_plan.md item 3) |
| `runs.jsonl` same line count, non-target lines byte-identical | Step 3 | Manual line-by-line diff excluding 7 lines (test_plan.md item 4) |
| `python3 tools/agent-monitoring/validate.py` exits 0 | Step 3, reconfirmed Step 5 | Direct script run |
| (Not a ticket AC — architecture-review-driven traceability requirement) `runs.jsonl`'s in-place edit is documented as an exception to its stated append-only contract | Step 3b | Manual review of `docs/agent-monitoring/schema.md`; covered by Definition of Done's "Docs were updated if behavior changed," not a numbered ticket AC |
| New checker exits non-zero on injected stale-ticket-status and lowercase-`final_status` fixtures | Step 4 | `test_stale_ticket_status_flagged`, `test_lowercase_final_status_flagged` |
| New checker exits 0 against post-fix corpus, correctly ignores 7 epic-tier + 5 legacy files | Step 4 (fixtures), Step 5 (live corpus) | `test_clean_corpus_passes`, `test_epic_tier_exception_ignored_by_value`, `test_legacy_naming_file_ignored_by_pattern`; Step 5 live run |
| New checker has pytest coverage for clean/stale-ticket/lowercase-status/epic-exception/legacy-exception | Step 4 | `pytest tests/tools/test_status_drift_check.py -v` |
| `classifyFinalStatus()` buckets all 7 corrected runs as `'done'` | Step 5 (manual trace, no code change) | Existing `GanttBar.test.tsx` fixtures + manual trace |

## Anti-Drift Notes

- **Regex parity is load-bearing.** The checker's `check_ticket_status_drift()` must use
  `^## Status\s*\n+\s*(\S+)` verbatim — the same regex used to derive the approved 71/12/83 baseline
  in Steps 1–2. A "more correct" or more permissive regex (e.g. one that also matches same-line
  colon-suffixed values) is a real, easy-to-make mistake here: it looks like an improvement but
  silently expands the flagged set to include the 6 colon-suffixed files this ticket deliberately
  left unfixed, which fails the clean-corpus AC. `test_same_line_colon_status_format_not_newly_flagged`
  exists specifically to catch this regression and must not be weakened or removed.
- **Exemptions must stay structural, never a literal filename list.** Hardcoding the 7 epic-tier or
  5 legacy filenames means every future epic closure or legacy backfill silently produces a false
  positive unless the checker is manually updated in lockstep — a second source of truth this ticket
  is explicitly designed to avoid. Use value-based (`{"EPIC_SCOPED", "SCOPED"}`) and pattern-based
  (`not filename.startswith("TCK-")`) checks only.
- **`runs.jsonl` writes must be line-scoped string substitution, never `json.loads`/`json.dumps`.**
  A round trip risks silently reordering keys, reformatting numbers, or changing separator spacing
  on lines the AC requires to stay byte-identical — even though `record_run.py`'s own serialization
  convention (`separators=(",", ":")`) is known, round-tripping through Python's `json` module is
  not guaranteed to reproduce it exactly, and there is no need to take that risk when string
  substitution is strictly simpler and safer.
- **Do not restructure per-file blank-line layout in Step 2.** Some of the 71 files have a blank
  line between `## Status` and the value, others do not — the substitution must only replace the
  captured value token, not normalize this layout, or files will show more than a 1-line diff and
  fail AC2.
- **`LEGACY_TERMINAL_STATUS_VALUES` in `validate.py` is a different concern from this ticket's fix**
  — it tolerates lowercase/legacy values for *completeness* checking (has the run finished), which
  is orthogonal to this ticket's *canonical-casing* checking (is the run's status spelled
  correctly). Do not conflate the two or attempt to "align" them.

## Deviations

**AC5 / Step 3 Verify / Step 5 item 3 — `python3 tools/agent-monitoring/validate.py` does not exit
0 after the `runs.jsonl` edit, and cannot be made to via anything in this ticket's approved scope.**

Confirmed via a before/after comparison (`git stash` the `runs.jsonl` edit, re-run `validate.py`,
compare stdout/stderr and exit code, then restore): the script already exited 1 **before** this
ticket's Part B fix, due to 6 pre-existing `ERROR: Run with no events` findings for run_ids entirely
unrelated to Part B's 7-record scope (`FOLDER-phase40-44-cleanup-authoring`,
`FOLDER-tickets-todos-doc-hardening-`, `run-E43B-1782052024`, `FOLDER-tickets/todos/world-data/`,
`TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN`, `FOLDER-tickets-todos-simq-corpus-tiers`) — none of
which are among the 7 named `final_status` records this ticket touches. `validate.py`'s exit code is
driven exclusively by its `errors` list (line 244-245: `if errors: sys.exit(1)`); this `errors` set
is byte-identical before and after the Part B edit.

The edit does surface 4 new `WARNING: Run marked DONE has no working_log entry` lines (for
`TCK-20260619-E52A/B/C/D`) that were not printed pre-fix — these are new WARNINGs, not new ERRORs.
They appear because those 4 records' `final_status` now literally reads `"DONE"`, which trips a
separate warning check (`Run marked DONE has no working_log entry`) that did not match while the
value was lowercase `"success"`. Per the script's own docstring (line 64-66:
"validate.py's exit-code contract (errors -> exit 1, else exit 0 regardless of warnings) is
unaffected by what this function returns"), warnings never affect the exit code — confirmed the
script's exit code is unchanged (1 before, 1 after this ticket's edit).

Backfilling `tickets/working_log.csv` entries for those 4 runs, or investigating/fixing the 6
pre-existing zero-event run_ids, is out of this ticket's Scope and Out of Scope sections (which
name only the 71 `## Status` files and the 7 `final_status` records) — doing either here would be
scope creep on an already-approved ticket. AC5 as literally worded ("exits 0") is therefore not
achievable within this ticket's approved boundaries; what is verified and true is: **this ticket's
edit introduces zero new ERROR-level findings and does not change `validate.py`'s exit code**
(1 before, 1 after — a pre-existing condition, not a regression this ticket caused or could fix
without expanding scope). Recorded here per CLAUDE.md's "never silently deviate" rule rather than
worked around by loosening AC5 or expanding Part B's file scope unilaterally.
