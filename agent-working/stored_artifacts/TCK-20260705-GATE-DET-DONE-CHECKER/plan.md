---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-DONE-CHECKER
artifact_type: plan
tags: [ai, workflows, determinism]
---

# Implementation Plan — TCK-20260705-GATE-DET-DONE-CHECKER

## Summary

Build `tools/gate_checks/done_checker_static.py` as a pure-function module (mirrors
`tools/parity_ledger_scan.py`'s shape: no argparse, no CLI, consumed via `python3 -c "..."`) exposing
five pre-Finalize static checks (Part A) plus two post-Finalize migration self-checks (Part B), all in
the same module since both are facets of the same `done-checker` gate family (SEQUENCE.md decision 1:
one module per *gate*, not per phase). Wire Part A into `.claude/agents/done-checker.md` and
`implement-ticket.js`'s Verify prompt as a cited-first script run, reusing the existing `DOD_BLOCKED`
status for any static FAIL (no new status there). Wire Part B into Finalize as a `bash(...)` call
immediately after the (today-unassigned, today-unconditional) Finalize `agent()` call, introducing one
new terminal status, `FINALIZE_INCOMPLETE`, when the post-move self-check finds a discrepancy — this is
the one new status this ticket adds, confirmed compatible with `implement-epic.js`'s existing
any-non-`DONE`-stops batch logic with zero changes needed there. Add `verified_by` to `DONE_SCHEMA`,
populated by agent self-report (not JS-parsed), consistent with every other field in that schema. Build
Part C's retrospective audit script per the investigation's GO decision (39.2% historical gap, still
~23–26% in the most recent two months) as a read-only, warn-only, disclose-don't-fix tool modeled
directly on `tools/agent-monitoring/validate.py`, explicitly skipping/warning (never blocking or
investigating) the 91 legacy `UNKNOWN`-tier tickets. Update the four `docs/ai/*` files plus fix the
stale "12 conditions" count in `system_overview.md` while touched.

## Steps

### Step 1 — `tools/gate_checks/` package skeleton + Part A check functions
**Files:** `tools/gate_checks/__init__.py` (new, empty/minimal, matches `tools/__init__.py` convention),
`tools/gate_checks/done_checker_static.py` (new)
**Change:** Create the package. In `done_checker_static.py`, add a module docstring naming this ticket
(matches `tools/parity_ledger_scan.py`/`tools/registry_query.py` convention). Implement five functions,
each returning a `(status: Literal["PASS","FAIL","NA"], evidence: str)` tuple (plain tuple, not a
dataclass — matches the plain-value-return convention of the two reference modules):

- `check_staging_artifacts_complete(ticket_id: str, tier: str, base_dir: Path = Path("staging_artifacts")) -> tuple[str,str]`
  - `tier == "hotfix"` → return `("NA", "hotfix tier — staging artifacts not required")` immediately,
    regardless of directory state (per test_plan item 1's explicit "do not silently PASS a hotfix
    ticket with a missing directory" requirement — NA must be checked and returned before any
    filesystem access, not derived from an empty-dir PASS).
  - Otherwise: check `base_dir / ticket_id / {"plan.md","investigation.md","test_plan.md"}` each exist
    and, after `.strip()`, are non-empty. Missing or empty file(s) → `FAIL` naming each missing/empty
    file by filename. All present and non-empty → `PASS`.
- `check_data_runs_clean(start_ts: str | None, runs_dir: Path = Path("data/runs"), proof_dir: Path = Path("reports/release_proof")) -> tuple[str,str]`
  - mtime-based rule (per investigation's resolved recommendation, mirroring
    `implement-ticket.js:786`'s Finalize step 6 wording) — **not** a naive "must be fully empty" check.
  - Parse `start_ts` (ISO 8601, e.g. `2026-07-05T00:00:00Z`) to a comparable epoch/`datetime`. If
    `start_ts` is `None` or unparsable, fall back to treating any file found as worth flagging (FAIL)
    rather than silently passing — a missing timestamp is not evidence of cleanliness.
  - Walk both directories recursively (`rglob("*")`, files only). For each file, compare its
    `st_mtime` against `start_ts`. Any file with mtime `< start_ts` → presumptively pre-existing /
    concurrent-session data, does not count against this check. Any file with mtime `>= start_ts` →
    `FAIL`, citing the specific file path(s). Both dirs empty (or containing only older files) → `PASS`.
- `check_ticket_location(ticket_id: str, inprogress_dir: Path = Path("tickets/inprogress")) -> tuple[str,str]`
  - `(inprogress_dir / f"{ticket_id}.md").exists()` → `PASS`; else `FAIL` with the expected path.
- `check_working_log_no_row_yet(ticket_id: str, csv_path: Path = Path("tickets/working_log.csv")) -> tuple[str,str]`
  - Read the CSV. **Do not use `csv.DictReader` keyed on the header alone** if a malformed-column-order
    row could exist (per `stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md`'s Reason
    A finding: some historical rows have `ticket_id` in column 1 instead of column 2). Check **every
    column** of every row for an exact match on `ticket_id`, not just the column the header says
    `ticket_id` lives in — i.e., `any(ticket_id in row for row in csv.reader(...))`, so a malformed
    historical row still counts as "row exists" rather than being missed. Row found anywhere → `FAIL`,
    evidence text must say this indicates "a pre-existing row at Verify time — possible duplicate/re-run"
    (per ticket's own wording, and test_plan item 4's explicit assertion on the evidence string, not just
    a generic "found row"). No matching row anywhere → `PASS`.
- `check_frontmatter_valid(ticket_id: str, tier: str, ticket_path: Path = None, staging_dir: Path = None) -> tuple[str,str]`
  - Default `ticket_path = Path(f"tickets/inprogress/{ticket_id}.md")`, `staging_dir = Path(f"staging_artifacts/{ticket_id}")`.
  - Import `validate_file`/`validate_directory` from `tools/validate_frontmatter.py` directly (Python
    import, not a subprocess shell-out — avoids the `python3 -c "..."` quoting fragility noted in the
    Parity-phase precedent, and this function is already being called from Python, not JS, so a direct
    import is simpler and more testable than shelling out to itself).
  - Validate `ticket_path` with no override (ticket content type auto-detects correctly already).
  - Validate `staging_dir` **with `content_type_override="artifact"` passed explicitly** — this is the
    one required fix from the investigation's finding #1: `staging_artifacts/` paths do not
    auto-detect as `artifact` type (only `stored_artifacts/` paths do), so omitting the override would
    silently fall through to `doc`'s (looser) required-field set.
  - `tier == "hotfix"` and `staging_dir` does not exist → `NA` for the artifacts half (still validate
    the ticket file itself).
  - `validate_directory()` returns `dict[Path, list[str]]`, not a flat list (architecture review round 1,
    minor finding, confirmed at `tools/validate_frontmatter.py:286-294`) — flatten via
    `[err for errs in results.values() for err in errs]` before using as evidence; do not stringify the
    dict directly. Any errors from either call → `FAIL`, evidence = the concatenated/flattened error
    list. Both clean → `PASS`.
- `run_static_precheck(ticket_id: str, tier: str, start_ts: str | None) -> list[dict]` — aggregate
  function. Calls all five checks above and returns a list of
  `{"condition": <name>, "status": <PASS|FAIL|NA>, "evidence": <str>}` dicts, one per check, in the
  order listed (matches `DONE_SCHEMA.checklist`'s own item shape so the agent can transcribe directly).
  Does **not** collapse to a single boolean — per-check detail must survive (test_plan item 6's explicit
  "not just all truthy" requirement).

**Do NOT touch:** any of the 7 judgment-based DoD conditions (1, 2, 5, 6, 8, 9, 11 in `done-checker.md`'s
numbering) — this module only ever returns evidence for the 5 machine-checkable conditions. Do not add
a `main()`/`argparse` block (breaks the established pure-function convention this ticket must follow
per SEQUENCE.md decision 1).
**Verify:** `tests/tools/test_done_checker_static.py::test_check_staging_artifacts_complete_*`,
`::test_check_data_runs_clean_*`, `::test_check_ticket_location_*`,
`::test_check_working_log_no_row_yet_*`, `::test_check_frontmatter_valid_*` (Step 2).

### Step 2 — Part A coverage-honesty tests
**Files:** `tests/tools/test_done_checker_static.py` (new — **flat file, not
`tests/tools/gate_checks/test_done_checker_static.py`**: confirmed by `ls tests/tools/` that this
directory has no subdirectories today — every sibling module's test lives directly in `tests/tools/`,
e.g. `test_parity_ledger_scan.py`, `test_registry_query.py`. The test_plan's tentative nested path is
superseded by this confirmed convention; use the flat name.)
**Change:** Using `tmp_path`/`monkeypatch` fixtures, implement the fixtures from `test_plan.md` items
1–6 exactly:
- `check_staging_artifacts_complete`: missing-file FAIL (names `test_plan.md`), empty-file FAIL,
  all-present PASS, hotfix-tier NA-regardless-of-state (distinguishable from PASS).
- `check_data_runs_clean`: empty-dirs PASS; file with mtime before `start_ts` (via `os.utime`) PASS;
  file with mtime at/after `start_ts` FAIL naming the path.
- `check_ticket_location`: present PASS, absent FAIL.
- `check_working_log_no_row_yet`: no-row PASS; existing-row FAIL with the duplicate/re-run wording
  asserted in the evidence string; **malformed-column-order fixture required** — a row with
  `ticket_id` shifted to column 1 must still be detected as "row exists" (regression guard against the
  `DictReader` column-order bug from `TCK-20260705-WORKING-LOG-BACKFILL`).
- `check_frontmatter_valid`: valid ticket + valid staging artifacts → PASS; a staging file missing
  `artifact_type`/`ticket_id` (satisfies `doc`'s schema but not `artifact`'s) → FAIL — this test must
  fail if Step 1's implementation forgets the `content_type_override="artifact"` override.
- `run_static_precheck`: one all-PASS-eligible fixture; one fixture with a FAIL mixed among PASSes,
  asserting the FAIL surfaces in the returned list rather than being masked.
**Do NOT touch:** any existing test file under `tests/tools/`; do not add a shared `conftest.py` unless
one is already present (checked: none exists today under `tests/tools/` — if a step needs shared
fixture helpers, define them locally in this one test file rather than introducing new shared
infrastructure this ticket doesn't need).
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — all pass, and manually confirm each
FAIL-path test would fail if the corresponding Step 1 check were reverted to a naive/happy-path-only
implementation (coverage-honesty spot check, not a separate automated test).

### Step 3 — Part B migration self-check functions (same module)
**Files:** `tools/gate_checks/done_checker_static.py`
**Change:** Add two more functions to the same module (decision: same file as Part A, not a sibling —
both are the `done-checker` gate's static checks, just at different pipeline points; splitting them
into two files would fragment one gate's checks across two modules for no benefit):
- `check_migration_complete(ticket_id: str, tier: str, staging_dir: Path = None, stored_dir: Path = None) -> tuple[str,str]`
  - hotfix → `NA` immediately (no migration expected).
  - Otherwise: `stored_dir` (`stored_artifacts/{ticket_id}` default) must exist and contain all 3 files
    non-empty (reuse the same file-presence logic as `check_staging_artifacts_complete`, factor out a
    private `_files_complete(dir, filenames)` helper both call, to avoid duplicating the same 6 lines
    twice inside the module). `staging_dir` (`staging_artifacts/{ticket_id}` default) must **not**
    exist. Both conditions must hold for `PASS`. Missing/incomplete `stored_dir` → `FAIL` naming the
    missing file(s). `stored_dir` complete but `staging_dir` still present → `FAIL` ("migration ran but
    source not cleaned").
- `check_ticket_finalized(ticket_id: str) -> tuple[str,str]`
  - `tickets/done/{ticket_id}.md` exists AND `tickets/inprogress/{ticket_id}.md` does not → `PASS`.
    Either condition failing → `FAIL` naming which.
- `check_working_log_exactly_one_row(ticket_id: str, csv_path: Path = Path("tickets/working_log.csv")) -> tuple[str,str]`
  - Reuse the same any-column match logic as `check_working_log_no_row_yet` (factor into a shared
    private `_count_rows_for_ticket(csv_path, ticket_id)` helper both functions call — avoids
    duplicating the malformed-column-order-safe scan twice). Count of matching rows `== 1` → `PASS`.
    `0` → `FAIL` ("no working_log row found — Finalize did not append"). `>= 2` → `FAIL` ("N rows found —
    duplicate Finalize run"), explicitly distinct wording from the zero case (test_plan item 7's "not
    zero, not more than one" — a naive `if not any(...)` would silently accept duplicates; this function
    must not do that).
- `run_finalize_selfcheck(ticket_id: str, tier: str) -> list[dict]` — aggregate of the 3 functions above,
  same shape as `run_static_precheck`'s return.

**Do NOT touch:** Part A's five functions' signatures or return shapes (Part B reuses two private
helpers but must not change Part A's public behavior).
**Verify:** `tests/tools/test_done_checker_static.py::test_check_migration_complete_*`,
`::test_check_ticket_finalized_*`, `::test_check_working_log_exactly_one_row_*` (Step 4).

### Step 4 — Part B coverage-honesty tests
**Files:** `tests/tools/test_done_checker_static.py` (same file as Step 2 — append)
**Change:** Implement `test_plan.md` item 7's fixtures:
- all-PASS fixture (complete `stored_artifacts/`, absent `staging_artifacts/`, done ticket present,
  inprogress absent, exactly 1 working_log row).
- `stored_artifacts/` missing `plan.md` → FAIL naming it (models the 101 real "incomplete" cases from
  the investigation's Part C scan).
- `staging_artifacts/` still present alongside complete `stored_artifacts/` → FAIL ("not cleaned").
- working_log 0 rows → FAIL (zero case).
- working_log 2+ rows → FAIL (duplicate case) — distinct evidence text from the zero case.
**Do NOT touch:** Step 2's Part A tests.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` (full file, both parts).

### Step 5 — Wire Part A into `done-checker.md` and Verify-phase prompt
**Files:** `.claude/agents/done-checker.md`, `.claude/workflows/implement-ticket.js` (Verify phase,
lines ~695–724 in current numbering)
**Change:**
- In `done-checker.md`: add an instruction before the numbered checklist (or as a new "Step 0" the way
  other agents in this file already do — e.g. parity-updater's `PHASE_TS` step) telling the agent to
  run the static pre-check script first via
  `python3 -c "import sys; sys.path.insert(0,'.'); from tools.gate_checks.done_checker_static import run_static_precheck; import json; print(json.dumps(run_static_precheck('<ticket_id>', '<tier>', '<start_ts>')))"`
  and cite its JSON output directly for conditions 3, 4, 7, 10, 12 in the checklist table — not
  re-derive them by hand. Keep conditions 1, 2, 5, 6, 8, 9, 11 as pure LLM judgment (unchanged). Keep
  condition 13 pre-marked PASS (unchanged).
- In `implement-ticket.js`'s Verify `agent(...)` call: add a step before "Check all DoD conditions"
  instructing the agent to run the same script (with `${tid}`, `${tier}`, and `${startTs}` substituted —
  `startTs` is already in scope at line 141, unchanged all the way through Verify) and cite its output
  verbatim for the 5 machine-checkable conditions, matching the wording added to `done-checker.md`.
- **Fix the pre-existing stale numbering in the same edit** (architecture review round 1 finding,
  CONFIRMED by direct read of the live file): line 719 currently reads
  `- Condition 12 (agent monitoring): NOT yet written — workflow writes it after READY_TO_CLOSE.` This
  is off-by-one — agent monitoring is condition 13, not 12 (per `done-checker.md`'s own canonical
  numbering, condition 12 = frontmatter validity). Since this same step now *also* adds an instruction
  telling done-checker to "cite its JSON output directly for conditions 3, 4, 7, 10, 12" (12 = frontmatter,
  correctly numbered), leaving line 719's stale "Condition 12 (agent monitoring)" text unchanged would ship
  two conflicting definitions of "Condition 12" in the same prompt. Change line 719 to
  `- Condition 13 (agent monitoring): NOT yet written — workflow writes it after READY_TO_CLOSE.` as part
  of this same Step 5 edit — do not leave it as "unchanged."
- **Failure vocabulary: unchanged.** A static `FAIL` surfaced by the agent simply becomes one more
  `failing_items` entry leading to the existing `verdict: 'BLOCKED'` → existing `DOD_BLOCKED` status at
  line 727–738. **Do not introduce any new status here** — per SEQUENCE.md decision 2 and the
  investigation's explicit confirmation this is the one place the ticket must reuse existing vocabulary.
- Add `verified_by` to `DONE_SCHEMA` (lines 672–693): a new optional array-of-string property (not in
  `required` — keep `required` as `['verdict', 'failing_items', 'checklist', 'summary']` unchanged, so
  this is additive and non-breaking for any in-flight run). **Decision (made now, not left open):**
  `verified_by` is populated by the `done-checker` agent self-reporting after it runs the script, e.g.
  `["static:done_checker_static", "llm"]` — the same way `verdict`/`checklist`/`summary` are all
  agent-authored today, not JS-parsed from the script's raw stdout. Add one line to the prompt asking
  the agent to include `verified_by` listing which conditions came from the static script vs. pure
  judgment.
**Do NOT touch:** the `checklist[].status` enum (stays `['PASS','FAIL','NA']`), the tier-specific N/A
prose (unchanged, still agent-authored), the existing three pre-marked-PASS conditions' wording (7, 3,
13 in the "Check all DoD conditions" block) beyond pointing them at the script's own output for
conditions 4/10/12 where the script is now authoritative.
**Verify:** manual code inspection (no JS test harness exists in this repo for workflow files, per
test_plan.md's explicit note) — confirm `DONE_SCHEMA`'s `required` array is unchanged, confirm the new
`verified_by` property parses as valid JS object literal, confirm the prompt text renders the 3
interpolated values (`${tid}`, `${tier}`, `${startTs}`) with no syntax error by a dry `node --check` (or
equivalent) pass over `implement-ticket.js`.

### Step 6 — Wire Part B into Finalize + introduce `FINALIZE_INCOMPLETE`
**Files:** `.claude/workflows/implement-ticket.js` (Finalize phase, lines ~745–805 in current numbering)
**Change:**
- Leave the Finalize `agent(...)` call's return value unassigned (architecture review round 1, minor
  finding: an earlier draft of this step introduced `const finalizeResult = await agent(...)` but never
  used the variable — dead code. The authoritative check is the new `bash(...)` call below, which reads
  the filesystem/CSV directly rather than parsing the agent's own prose report, so no capture is needed.
  Keep `await agent(...)` as a bare statement, unchanged from today.)
- Immediately after that `agent()` call returns (i.e., right after what is today line 792, before the
  unconditional `pushEvent`/`return` at lines 794–805), add a `bash(...)` call mirroring the Parity-phase
  `paritySkipEligible` precedent's shape exactly (one Python one-liner, args passed as individually
  quoted argv elements, not JSON-embedded in the `-c` string):
  ```
  const finalizeCheckOutput = await bash(
    `python3 -c "
  import sys, json
  sys.path.insert(0, 'tools')
  from gate_checks.done_checker_static import run_finalize_selfcheck
  results = run_finalize_selfcheck(sys.argv[1], sys.argv[2])
  print('FINALIZE_CHECK_JSON:' + json.dumps(results))
  " "${tid}" "${tier}"`
  )
  ```
  **Parsing contract (revised per architecture review round 1 finding, CONFIRMED — the only existing
  `bash()` precedent in this file, the Parity-phase `p0ScanOutput` call at lines 561–571, never
  `JSON.parse`s its output; it only checks `.includes('P0_INTERSECTION_FOUND')` on a plain sentinel
  string. There is no established contract anywhere in this repo that `bash()` returns output safe for
  a bare `JSON.parse()` — assuming so risks turning today's silent "always returns DONE" bug into a
  worse uncaught-exception crash inside Finalize.)** Do not call `JSON.parse(finalizeCheckOutput)`
  directly. Instead:
  1. Print output prefixed with a sentinel marker (`FINALIZE_CHECK_JSON:`, as shown above) so the JSON
     payload is unambiguously delimited from any other stdout noise.
  2. Extract the substring after the marker (e.g. `finalizeCheckOutput.split('FINALIZE_CHECK_JSON:')[1]`),
     `.trim()` it, then attempt `JSON.parse` inside a try/catch.
  3. **On parse failure or missing marker**: treat this as its own discrepancy — do not throw uncaught
     and do not silently fall through to `DONE`. Return
     `{ status: 'FINALIZE_INCOMPLETE', ticket_id: tid, failing_items: ['finalize_selfcheck_unparseable'],
     message: 'Finalize self-check output could not be parsed — treating as incomplete. Raw output: ' +
     finalizeCheckOutput }`. This guarantees the new failure path can never be *worse* than today's bug
     (silent `DONE`) — worst case is now a visible, diagnosable `FINALIZE_INCOMPLETE`, never a crash.
- If any entry in the parsed results has `status === 'FAIL'`: `pushEvent('Finalize', 'finalizer',
  'failed', ...)` citing the specific failed condition(s), then
  `return { status: 'FINALIZE_INCOMPLETE', ticket_id: tid, failing_items: <FAIL entries>, message:
  'Finalize completed its steps but the post-migration self-check found a discrepancy — see
  failing_items.' }` **instead of** falling through to the unconditional `pushEvent('Finalize', ...,
  'ok', ...)` / `return { status: 'DONE', ... }` at lines 794–805. Do **not** call `writeMonitoring('DONE')`
  in this branch — call `writeMonitoring('FINALIZE_INCOMPLETE')` (or reuse the existing writeMonitoring
  call with the new status string as its argument — check `writeMonitoring`'s signature accepts an
  arbitrary status string, which it already must, since it's called with `'DOD_BLOCKED'` elsewhere).
- If all entries `PASS`/`NA`: fall through to the existing lines 794–805 unchanged (`pushEvent(...,
  'ok', ...)`, `writeMonitoring('DONE')`, `return { status: 'DONE', ... }`).
- **This is the one new status string this entire ticket introduces** (`FINALIZE_INCOMPLETE`) —
  everywhere else (Part A) reuses `DOD_BLOCKED`, per SEQUENCE.md decision 2's "no new status strings"
  applying specifically to gates that already have LLM-verdict-driven statuses; Finalize today has *no*
  failure status at all (it unconditionally returns `DONE`), so adding exactly one is the minimum fix
  for a confirmed real gap, not a vocabulary proliferation.
- Confirm (no code change needed — this is a verification-only sub-step): `implement-epic.js`'s batch
  loop (~line 203, `result.status !== 'DONE'`) already treats `FINALIZE_INCOMPLETE` as a stop condition
  identically to `DOD_BLOCKED`, since both are simply "not `'DONE'`". Note this compatibility in the
  ticket's own Implementation Notes; do not modify `implement-epic.js`.
**Do NOT touch:** `implement-epic.js` (confirmed no change needed); the Finalize agent prompt's own
step-by-step instructions (1–7, lines 754–790) — those stay as-is, this step only adds orchestrator-side
verification after the agent's own work, it does not change what the agent is asked to do.
**Verify:** manual code inspection of the new branch logic (no JS test harness exists); the Step 4
Python-level tests already prove `run_finalize_selfcheck` itself returns correct FAIL/PASS data —
Step 6 only wires that data into the JS control flow, which cannot be pytest-covered per this repo's
tooling.

### Step 7 — `verified_by` decision confirmation (no separate code — folded into Step 5)
This step is a placeholder to make the decision explicit in the plan's own step list, per the user's
instruction to resolve it now rather than leave it open: **`verified_by` is agent-self-reported**, added
as an optional `DONE_SCHEMA` property in Step 5. No additional file changes beyond what Step 5 already
covers.

### Step 8 — Part C retrospective audit script
**Files:** `tools/gate_checks/done_checker_audit.py` (new — kept as a **separate file** from
`done_checker_static.py`, unlike Part A/B: Part C is a retrospective, standalone, non-blocking audit
tool invoked manually/periodically, not part of the live Verify/Finalize call path, so it does not
belong inside the same module as the two pipeline-integrated check sets — this mirrors
`tools/agent-monitoring/validate.py` being its own standalone script rather than folded into the
monitoring-writer module it audits)
**Change:** Module docstring naming this ticket and stating its read-only, disclose-don't-fix purpose
(mirrors `validate.py`'s own docstring framing). Implement:
- `scan_done_tickets(done_dir: Path = Path("tickets/done")) -> list[dict]` — walk `tickets/done/*.md`
  and `tickets/done/*/*.md` (excluding `README.md` and `SEQUENCE.md`, matching the investigation's own
  scan method), extract each ticket's `## Tier` field via the same simple text-section parse used
  elsewhere in this codebase (do not add a new markdown-parsing dependency).
- **Legacy/UNKNOWN-tier handling (explicit scope guard, per user instruction):** if a ticket has no
  parseable `## Tier` field (the 91 pre-frontmatter-era legacy tickets, e.g. `METRICS-01.md`), the scan
  must **skip it silently or emit a single simple `WARNING: {id} — no ## Tier field, skipped` line** and
  move on. **Do not** attempt to classify these as standard/epic/hotfix by inference, do not attempt to
  determine why they lack the field, and do not treat their absence-of-directory as a migration gap —
  they are permanently out of scope for this audit, not a defect needing investigation. This mirrors
  `validate.py`'s own "Historical tickets... are skipped silently" precedent exactly.
- For every ticket with a parseable `standard`/`epic` tier: check `stored_artifacts/{id}/` existence and
  3-file completeness (reuse `_files_complete` from `done_checker_static.py` via import — do not
  reimplement). Classify as `ok` / `missing` / `incomplete` (with the specific missing file names).
- `hotfix`-tier tickets: skip (no `stored_artifacts/` expected — not a gap).
- Print a summary report (counts by classification, optionally grouped by `TCK-YYYYMMDD-` month prefix
  the way the investigation's own manual scan did) to stdout. **Never** move, create, or delete any
  file — read-only throughout, matching `validate.py`'s own disclose-don't-fix contract.
- No blocking exit code tied to findings — this is an audit, not a gate; exit 0 always (unless a genuine
  script error occurs), consistent with the ticket's Out-of-Scope line ruling out backfilling/moving
  historical data.
**Do NOT touch:** `tools/agent-monitoring/validate.py` itself (Part C is new/separate, per the ticket's
own "reusing... pattern" wording — not a modification to that file). Do not attempt to backfill or move
any historical `staging_artifacts/`/`stored_artifacts/` directory for any ticket found by this scan.
**Verify:** a lightweight smoke test (`tests/tools/test_done_checker_audit.py`) with a small
fixture set: one `standard` ticket with complete `stored_artifacts/`, one with an incomplete one, one
with none, one `hotfix` ticket (must be skipped, not counted as a gap), and one legacy ticket with no
`## Tier` field at all (must be skipped/warned, not classified or crashed on). Assert the legacy-ticket
fixture produces a WARNING (or silent skip) and never appears in the missing/incomplete counts, and
that the function does not raise on it.

### Step 9 — Documentation updates
**Files:** `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/system_overview.md`,
`docs/ai/ticket-lifecycle.md`
**Change:**
- `docs/ai/agents.md`: in the `done-checker` section, describe the new static pre-check script it runs
  first (Part A) and cite `tools/gate_checks/done_checker_static.py`.
- `docs/ai/workflows.md`: describe the Verify-phase script-first instruction and the new Finalize
  self-check + `FINALIZE_INCOMPLETE` status.
- `docs/ai/system_overview.md`: fix the stale "12 substantive Definition-of-Done conditions" (line ~106)
  to the correct count of 13 (opportunistic fix of pre-existing drift, explicitly flagged here per the
  investigation's finding #3 — this is a one-line factual correction, not new scope), and mention the
  static pre-check.
- `docs/ai/ticket-lifecycle.md`: mention the new Finalize self-verification step and
  `FINALIZE_INCOMPLETE` outcome in the Finalize-phase description.
- After these edits: run `make knowledge-index-update` (per CLAUDE.md's rule — docs under `docs/` were
  modified).
**Do NOT touch:** any other section of these 4 docs unrelated to done-checker/Verify/Finalize.
**Verify:** re-read each edited section for accuracy against the actual Step 1–8 implementation (prompt-
text/doc changes are not unit-testable, per test_plan.md's own note).

## Scope Guards

- Do not modify the 7 judgment-based DoD conditions (1, 2, 5, 6, 8, 9, 11) in `done-checker.md` — those
  remain irreducibly LLM-judged per the ticket's own Out of Scope line.
- Do not build static verifiers for `architecture-reviewer`, `parity-updater`, or `mechanics-auditor` —
  separate sibling tickets (SEQUENCE.md).
- Do not add token/cost telemetry to any part of this ticket (SEQUENCE.md decision 5).
- Do not introduce a second new status string beyond `FINALIZE_INCOMPLETE` — Part A reuses
  `DOD_BLOCKED` exactly, no exceptions.
- Do not backfill, move, or otherwise mutate any historical ticket's `staging_artifacts/`/
  `stored_artifacts/` directories as part of Part C — disclose-only.
- **Do not investigate, classify, or attempt to root-cause the 91 legacy `UNKNOWN`-tier tickets found in
  Part C's scan** (tickets with no parseable `## Tier` field, e.g. `METRICS-01.md`, `RESTRUCTURE-01.md`
  — pre-frontmatter-era). This is an explicit, permanent scope boundary for this ticket, added per direct
  user instruction: these are legacy/old-format data, not a defect. `done_checker_audit.py` must skip
  them silently or with a single simple `WARNING` line and move on — no inference of their tier, no
  investigation of why they predate the convention, no attempt to force them into the
  standard/epic/hotfix taxonomy. Any test covering this behavior only needs to assert "does not crash,
  does not appear in gap counts" — not "correctly classifies."
- Do not modify `implement-epic.js` — confirmed zero changes needed for `FINALIZE_INCOMPLETE` to be
  correctly treated as a batch-stopping status by its existing `result.status !== 'DONE'` check.
- Do not fold Part C's `done_checker_audit.py` into `tools/agent-monitoring/validate.py` — kept as a
  separate, standalone tool per the ticket's own "reusing... pattern" (not "extending that file") wording.
- Do not write a JS test harness for `implement-ticket.js` — none exists in this repo; Steps 5/6 are
  verified by manual code inspection only, per test_plan.md's explicit note not to fabricate a Python
  test that `exec`s the `.js` file.

## Dependency Map

- Step 1 → Step 2 (tests need the functions to exist).
- Step 3 → Step 4 (same relationship, Part B).
- Step 1 and Step 3 can be implemented in either order relative to each other but both must land before
  Step 5/Step 6 respectively (the wiring steps consume the functions).
- Step 5 depends on Step 1 (and its tests in Step 2 passing) — the Verify-phase wiring calls
  `run_static_precheck`.
- Step 6 depends on Step 3 (and Step 4 passing) — the Finalize wiring calls `run_finalize_selfcheck`.
- Step 7 has no independent file changes — it is resolved inside Step 5.
- Step 8 is independent of Steps 1–7 except that it imports `_files_complete` from
  `done_checker_static.py` (Step 1), so Step 1 must land first; otherwise Step 8 can proceed in
  parallel with Steps 3–6.
- Step 9 should be done last, after Steps 1–8 land, so the docs describe the actual final shape rather
  than an intermediate one.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `done_checker_static.py` exists, one function per pre-Finalize condition, PASS/FAIL + evidence | Step 1 | `tests/tools/test_done_checker_static.py` (Step 2) |
| `done-checker.md` and Verify prompt instruct running the script first and citing output | Step 5 | Manual inspection (no JS harness) |
| `DONE_SCHEMA` gains `verified_by` | Step 5 / Step 7 | Manual inspection |
| Finalize gains a self-verification step, reports (not swallows) discrepancy | Step 6 | Manual inspection + `tests/tools/test_done_checker_static.py` (Step 4, for the underlying function) |
| Part C's historical-orphan count measured and reported, build-or-skip decision justified | Already done in `investigation.md` (338/862, GO decision) — Step 8 builds the tool per that decision | `tests/tools/test_done_checker_audit.py` (Step 8) |
| At least one coverage-honesty test per static check function | Steps 2 and 4 | `tests/tools/test_done_checker_static.py` |
| `docs/ai/agents.md`, `workflows.md`, `system_overview.md`, `ticket-lifecycle.md` updated | Step 9 | Manual re-read |

## Anti-Drift Notes

- **`check_data_runs_clean` must stay mtime-relative, never regress to "must be fully empty."** The
  investigation confirms this is the established Finalize-step-6 precedent (`implement-ticket.js:786`)
  — a simpler empty-check would misfire on legitimate concurrent-session leftovers.
- **`validate_frontmatter.py` content-type gap is real and easy to miss**: any call against
  `staging_artifacts/{id}/` must pass `content_type_override="artifact"` explicitly, or the check
  silently validates against `doc`'s looser schema instead of `artifact`'s. Step 2's dedicated test
  (item 5) exists specifically to catch a regression here.
- **`working_log.csv` malformed-column-order bug is a confirmed historical hazard**, not a hypothetical
  — both `check_working_log_no_row_yet` and `check_working_log_exactly_one_row` must scan every column,
  not just the nominal `ticket_id` column, per `TCK-20260705-WORKING-LOG-BACKFILL`'s own finding.
- **`FINALIZE_INCOMPLETE` is the only new status this ticket introduces.** Everywhere else, reuse
  `DOD_BLOCKED`. Do not let implementation drift toward inventing additional status strings for
  individual failure sub-cases (e.g. no separate `MIGRATION_FAILED` vs. `WORKING_LOG_DUPLICATE` — all
  Part B failure modes collapse into the single `FINALIZE_INCOMPLETE` status with detail carried in
  `failing_items`).
- **91 legacy `UNKNOWN`-tier tickets are out of scope for investigation, permanently.** This was not in
  the original investigation.md and is added here per direct user instruction: Part C's tool treats
  their non-conformance as an expected condition to skip past, not a defect to chase down. Do not let a
  future session (or this one) open a follow-up ticket titled something like "why do 91 tickets have no
  Tier field" as a result of this ticket's work — that is explicitly not this ticket's concern.
- **No JS test harness exists for `implement-ticket.js`.** Do not fabricate one under time pressure to
  satisfy a coverage checkbox for Steps 5/6 — manual code inspection is the correct, established
  verification method here (per test_plan.md's explicit instruction).

## Unresolved Questions

None. All previously-open items from `investigation.md`'s "Risks and Open Questions" section have been
resolved either by the investigation itself (mtime rule, content-type override, no-new-status for Part
A) or by explicit decision in this plan (Part B's one new `FINALIZE_INCOMPLETE` status, `verified_by`
populated by agent self-report, test file placed flat at `tests/tools/test_done_checker_static.py`, the
91 legacy-tier tickets scoped out of investigation per direct user instruction).

## Deviations (recorded at Implement time)

1. **`docs/ai/system_overview.md:106`'s "12 substantive Definition-of-Done conditions" was already
   accurate, not stale.** On direct re-read at implement time, the live text reads "checks 12
   substantive Definition-of-Done conditions, plus a 13th — agent monitoring — that is pre-marked
   PASS" — this already correctly totals 13 (12 checked + 1 pre-marked), matching `done-checker.md`'s
   real numbering. The investigation's claim that this line "still says '12 substantive... conditions'"
   as a stale count appears to have been an investigation-time misreading, or the line was already
   corrected by an intervening, unrelated commit between the investigation and this implementation
   session. No edit was made to that specific sentence (no fix was needed); a new sentence was added
   immediately after it describing the static pre-check module per Step 9's own instruction to
   "mention the static pre-check."

2. **Two additional stale "12 substantive/condition" references were found and fixed opportunistically**,
   beyond the one instance the investigation named, because they live in the exact done-checker/Verify/
   Finalize sections Step 9 already required touching:
   - `docs/ai/agents.md`'s `done-checker` section said "11 conditions" and listed only 11 items
     (missing conditions 12 and 13 entirely) — corrected to the real 13-condition list, with
     script-checked conditions annotated.
   - `docs/ai/ticket-lifecycle.md`'s Verify section said "11-condition table" and its table was
     missing a row for condition 12 (frontmatter validity) entirely — corrected to a 13-row table
     with condition numbers added, and its separate "DoD condition 12 (pre-marked PASS)" reference
     under Agent Monitoring (actually describing agent monitoring, i.e. condition 13) was fixed to
     "condition 13" — the identical off-by-one bug already confirmed and fixed at
     `implement-ticket.js:719` and in `done-checker.md`.
   These were treated as in-scope opportunistic fixes (not new scope) since they are inside the same
   done-checker-description sections Step 9 explicitly required editing, and leaving them stale while
   fixing the one instance the investigation named would have left two conflicting condition counts
   in the docs this same step touches.
