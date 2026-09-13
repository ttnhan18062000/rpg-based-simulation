---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-WORKING-LOG-APPEND-HELPER
phase: inprogress
date: 2026-09-12
tags: [data-quality, process-improvement]
---

# TCK-20260912-WORKING-LOG-APPEND-HELPER

## Title
One sanctioned writer for `tickets/working_log.csv` rows — Finalize agents currently hand-roll the append

## Status
INPROGRESS

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (PR #167) fixed a CRLF row writer in
`tools/agent-monitoring/record_hand_orchestrated_closure.py`. Chasing the one row that fix did **not**
explain showed the defect had a second, independent source, and that the real problem is one level up.

**Evidence (2026-09-11/12):** commit `c4d42635` added two working-log rows — one LF, one CRLF. The CRLF
one was written by the Finalize subagent for `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`
(subagent transcript `agent-a29533cff39b93b7c`, session `7276a580`, `agentType: general-purpose`) using an
improvised heredoc:

```
python3 - <<'EOF'
import csv
row = ["2026-09-11T09:06:03Z", "TCK-20260907-...", ...]
```

`csv.writer` defaults to `lineterminator="\r\n"`. The same defect as the closure script's, written on the
fly rather than living in a file — and the mechanism that duplicated `working_log.csv` blocks on 3 of 4
recent batch merges.

**Why a prompt line is not the fix.** `implement-ticket.js`'s Finalize step 4 specifies the row's
*format* ("Append to tickets/working_log.csv (one new row, comma-separated): timestamp,ticket_id,…") but
not *how* to write it, so each agent improvises. Telling them "use LF" fixes `csv.writer`'s default
specifically and leaves the class untouched: the next improvisation can differ in quoting, column order,
or where the row lands. The two CRLF defects were identical *because* two independent write paths
existed; reducing it to one is the durable fix.

**What is not already true** (checked, so this ticket does not rest on a false premise):
- CLAUDE.md's After Work section says only "Append to the **bottom** of `tickets/working_log.csv` (never
  insert after the header)". There is no existing "never hand-roll the write" rule to enforce.
- `record_hand_orchestrated_closure.py` cannot serve as the sanctioned path as it stands: `--events` is
  required and it always writes a monitoring run record plus events. Pipeline runs already record their
  own run via the workflow's `writeMonitoring`, so routing Finalize through it would double-record every
  ticket. It has no log-only mode.
- No other working-log append helper exists in `tools/`; that script's `writerow` is the only one.

## Scope
- Add one small sanctioned writer module owning the working-log row format: LF line endings,
  `QUOTE_MINIMAL`, the documented column order, bottom-append, `newline=""`. Read-side parsing stays in
  `tools/working_log_parser.py`; this is its write-side counterpart.
- Call it from `tools/agent-monitoring/record_hand_orchestrated_closure.py` in place of that script's own
  `csv.writer` call (PR #167 must merge first — it edits the same line).
- Point `implement-ticket.js`'s Finalize step 4 at the helper instead of describing a row for the agent to
  write however it likes.
- Add the rule to CLAUDE.md's After Work bullet: append via the helper, never hand-roll the write.
- Guard it: a test asserting no module other than the helper writes `tickets/working_log.csv`, so a future
  second path fails in CI rather than on the next merge.

## Out of Scope
- The row format itself (columns, timestamp precision, quoting). This ticket centralizes who writes it,
  not what is written.
- Monitoring run/event recording, which stays with `record_hand_orchestrated_closure.py`.
- Retrofitting historical rows. PR #167 already normalized line endings on `main`.
- `agent-monitoring/data/*/*.jsonl` writers: `tools/agent-monitoring/writer.py` already owns those and
  emits LF.

## Acceptance Criteria
- [x] Exactly one module in the repo writes `tickets/working_log.csv` rows; a test enforces it.
- [x] The helper emits LF, `QUOTE_MINIMAL`, the documented column order, and appends at the bottom, with
      unit tests including a field containing a comma, a quote, and an embedded newline.
- [x] `record_hand_orchestrated_closure.py` uses the helper; its existing tests pass unmodified.
- [x] Finalize step 4 in `implement-ticket.js` instructs the helper, pinned by a static test the way
      `TCK-20260907`'s instruction pin is.
- [x] CLAUDE.md's After Work bullet states the rule.
- [x] `tests/integrity/test_merge_union_no_cr_bytes.py` still passes (it is the backstop, not the fix).

### Remediation note for existing branches (2026-09-12)

Any branch cut before PR #167 carries CRLF rows in its **own commits**; `eol=lf` normalizes at commit
time and does not rewrite them. Each such branch needs one pass: merge `origin/main`, then
`git add --renormalize tickets/working_log.csv agent-monitoring/data`, then commit if anything staged.

**Three different objects can disagree. Know which one you are reading.**

| Object | How to read it | What it proves |
|---|---|---|
| Committed blob | `git show HEAD:tickets/working_log.csv \| python3 -c "import sys;print(sys.stdin.buffer.read().count(b'\r'))"` | Whether the merge defect recurs — `merge=union` operates on blobs |
| Bytes on disk | `python3 -c "print(open('tickets/working_log.csv','rb').read().count(b'\r'))"` | What `tests/integrity/test_merge_union_no_cr_bytes.py` reads (`read_bytes()`, line 27) |
| Index | `git show :tickets/working_log.csv` | Nothing durable — this is what `--renormalize` rewrites. **Never verify from this alone.** |

`git add --renormalize` rewrites the **index** and deliberately leaves the working copy alone.
`git checkout HEAD -- <path>` then silently no-ops, because git's normalized comparison already
considers the file unchanged even when its raw bytes differ. Forcing fresh bytes onto disk requires
`rm <path>` followed by `git checkout HEAD -- <path>`.

Evidence: `rpg-implementer` renormalized three active branches after #167 landed and hit this on PRs
#168 and #169 — staged blob at 0 CR while the on-disk file still read 8, and a plain re-checkout
changed nothing until the file was deleted first. In CI the two coincide, since a fresh checkout with
`eol=lf` in effect materializes the blob; local working trees are where they diverge.

(Reported by `rpg-feature-planning` and `rpg-implementer`, 2026-09-12. The single working-tree check
circulated earlier in this thread was not wrong about bytes, but it was the wrong object for deciding
whether the merge defect is gone.)

## Related Tickets
- `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (PR #167) — fixed the first writer; this
  ticket closes the class. **Must merge first.**
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (done) — original duplication incident.
- `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT` (done) — precedent for pinning a workflow
  instruction with a static test.

## Related Docs
- `CLAUDE.md` (After Work)
- `.gitattributes` (the `merge=union` caveat blocks)
- `docs/ai/ticket-lifecycle.md` (Finalize step 3 — updated by Document-Update)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION/`

## Related Code Areas
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (`writerow`, ~line 207)
- `tools/working_log_parser.py` (read side)
- `.claude/workflows/implement-ticket.js` (Finalize step 4)
- `tests/integrity/test_merge_union_no_cr_bytes.py`

## Assumptions / Open Questions
- Whether the helper belongs beside the parser (`tools/working_log_writer.py`) or inside it as a write
  function is an Implement-time call; the constraint is one owner, not a particular file.
- Agents can still bypass any helper by writing the file directly. The enforcement here is the
  instruction plus the CI guard, not a hard lock — state that honestly rather than claiming prevention.
- This is the second domain this week where the fix was consolidating parallel implementations of one job
  rather than correcting each copy (noted by `rpg-feature-planning`, from the RPG side's own deletions).
  Worth recording in the Completion Summary as a pattern, not just this instance.

## Implementation Notes

Implemented plan.md's 7 steps in order, no deviation from its specified mechanisms (AST-based
sole-writer guard, `--data-file` JSON contract, read-full-entry-then-construct-full-dict parity
update).

- **Step 1** — `tools/working_log_writer.py`: `_WORKING_LOG_PATH = Path("tickets/working_log.csv")`
  as a genuine module-level constant; `append_working_log_row(timestamp, ticket_id, title, status,
  summary, artifacts_path, path=_WORKING_LOG_PATH)` opens via `open(path, "a", newline="",
  encoding="utf-8")` + `csv.writer(..., quoting=csv.QUOTE_MINIMAL, lineterminator="\n")`, matching
  the original call byte-for-byte. `main(argv=None)` CLI wrapper reads `--data-file <path>`, parses
  the JSON, and calls `append_working_log_row(**fields)`.
- **Step 2** — `tools/agent-monitoring/record_hand_orchestrated_closure.py`: replaced the inline
  `working_log_path.open("a", ...) / csv.writer(...).writerow(...)` block with a call to
  `append_working_log_row(...)` (imported via the same `sys.path.insert(0, .../parent.parent)` +
  `from working_log_writer import ...` pattern `done_ticket_monitoring_coverage.py` already uses
  for a `tools/`-level sibling). Removed the now-unused `import csv` and the local
  `working_log_path` variable. The existing `try/except OSError` / `log_ok` warning behavior around
  the call is unchanged.
- **Step 3** — `.claude/workflows/implement-ticket.js`'s Finalize step 4 now instructs: (a) use the
  `Write` tool to create a JSON file with the 6 fields, (b) run
  `python3 tools/working_log_writer.py --data-file <path>` via `bash()`. No ticket-authored free
  text passes through shell/Python source-embedding. **One wording deviation from the plan's own
  prose (not its mechanism):** the plan's own Step 3 text uses the literal phrase "python3 -c" to
  explain what not to do; embedding that exact phrase in the Finalize prompt string itself would
  have made the new pin test's negative assertion fail (the prompt would then contain the very
  substring the test forbids). Reworded the in-prompt caution to "never embed this text as a
  Python or shell source string (e.g. an inline `-c` script)" — same guidance, no literal "python3
  -c" substring. Verified directly: `text.find('python3 -c' in scoped_prompt)` is `False` after
  the edit, `True` before it.
- Added `tests/tools/test_finalize_working_log_uses_helper_pin.py`, scoped to the Finalize agent's
  own prompt string via the two anchors plan.md specifies (`` `Finalize ticket ${tid} `` and
  `` Report each step: DONE / SKIPPED (reason).`, ``), verified live against the real file
  (`open_idx=98475, close_idx=101513, open<close`) before writing the test.
- **Step 4** — `tests/tools/test_working_log_writer.py` implements the AST resolver exactly as
  planned: a module-level literal map (top-level `name = "literal"` / `name = Path("literal")`),
  a function-local map (parameter defaults resolving to a literal directly or, single-hop, to a
  module-level name; plus local `name = "literal"` assignments inside the function body, collected
  via `_iter_same_scope_statements` which does not descend into nested function/class scopes),
  `Call`-node matching for both `open(path, mode, ...)` and `<expr>.open(mode, ...)` shapes, and a
  write-mode check (`{"a", "w", "a+", "w+", "x"}`) so the parser's own read-only `open(path,
  newline="")` call (mode omitted, defaults to `"r"`) is correctly excluded. Verified against the
  real repo tree: exactly one hit, `working_log_writer.py:55`. A synthetic-fixture negative test
  (`test_guard_fires_on_a_second_writer`) proves the guard fires on 2 hits when a second writer
  exists. 5 additional resolver unit tests cover the positive single-hop case, the read-only
  exclusion, a same-named-variable/different-file non-match, a docstring-only non-match, and the
  `<expr>.open(...)` method-call shape.
- **Step 5** — Read `INFRA-416`'s full current entry from `docs/parity_ledger/infrastructure.yaml`
  via `yaml.safe_load`, changed only `v2_evidence` (now cites
  `tools/working_log_writer.py::append_working_log_row()` instead of the replaced
  `record_hand_orchestrated_closure.py:207` call site) and `test_path` (added
  `tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer` to the
  existing 2-citation list), and passed the complete dict (preserving `id`, `text`, `status`,
  `priority`, `legacy_evidence`, `proof_type`, `divergence_note`, `support_boundary`,
  `evidence_kind` verbatim) to `write_entry('infrastructure.yaml', entry)`. Verified
  programmatically: every field except `v2_evidence`/`test_path` is `==`-identical to the
  pre-image captured before the write; `entry_count` is unchanged (419 before, 419 after — an
  update, not an insert); `git diff --stat` on the ledger shows only the one entry's two fields
  changed (15 removed / 16 added lines, all within `INFRA-416`'s block).
- **Step 6** — Added one sentence to CLAUDE.md's `Append to the **bottom**...` bullet: append via
  `tools/working_log_writer.py::append_working_log_row()`, never hand-roll the write, citing this
  ticket.
- **Step 7** — Unit tests for the helper (comma/quote/embedded-newline round-trip through
  `working_log_parser.parse_working_log()`, LF-only / zero-CR-byte output, append-only /
  never-truncates, two consecutive appends land in order, CLI `--data-file` mode with the same
  tricky-content case) are in `tests/tools/test_working_log_writer.py` alongside the AST-guard
  tests (both concerns share one file, per the plan's own file-naming discretion).
- Ran `graphify update .` after the code/test changes (repo rule: run after modifying files under
  `src/` or `tests/`; this ticket touched `tests/`). `graphify-out/` is gitignored — no tracked diff.

## Test Summary

Regression command (from test_plan.md), run via
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`:

```
pytest tests/tools/test_working_log_writer.py tests/tools/test_record_hand_orchestrated_closure.py \
       tests/tools/test_finalize_working_log_uses_helper_pin.py \
       tests/integrity/test_merge_union_no_cr_bytes.py tests/tools/test_parity_ledger_writer.py -q
```
Result: **72 passed**, 1 pre-existing unrelated `SyntaxWarning` (an invalid escape sequence inside
some other file under `tools/` encountered while the sole-writer guard's AST walk parses every
`.py` file there — present before this ticket, not introduced by it).

Breakdown:
- `tests/tools/test_working_log_writer.py` — 12 tests (5 resolver unit tests against synthetic
  snippets, 1 negative-fixture guard test, 1 real-repo-tree sole-writer test, 5 writer-behavior
  tests including the CLI) — all pass.
- `tests/tools/test_record_hand_orchestrated_closure.py` — full existing suite (including
  `TestWorkingLogCsvAppended`'s 6 tests) passes **unmodified**, confirming the Step 2 swap
  preserved behavior exactly (including the `test_missing_working_log_parent_dir_warns_but_does_
  not_fail_the_run` case, where `append_working_log_row`'s `open()` call still raises
  `FileNotFoundError` (an `OSError` subclass) when `tickets/` doesn't exist, caught by the same
  `try/except OSError` as before).
- `tests/tools/test_finalize_working_log_uses_helper_pin.py` — 3 new tests, all pass (helper
  mentioned + `--data-file` present; step 4 precedes step 5; no `python3 -c` substring in the
  scoped Finalize prompt).
- `tests/integrity/test_merge_union_no_cr_bytes.py` — passes (the backstop; unaffected by this
  ticket's change, confirming no regression).
- `tests/tools/test_parity_ledger_writer.py` — full existing suite passes unmodified (`write_entry`
  itself wasn't changed, only called with a new entry payload for `INFRA-416`).

Additional one-off verification (not a permanent test, per test_plan.md Step 5's framing as an
Implement-time check rather than a new AC): captured `INFRA-416`'s full entry dict before calling
`write_entry()`, re-read it after, and asserted every field except `v2_evidence`/`test_path` was
unchanged — confirmed `True` for all 9 other fields (`id`, `text`, `status`, `priority`,
`legacy_evidence`, `proof_type`, `divergence_note`, `support_boundary`, `evidence_kind`).

## Files Changed

- `tools/working_log_writer.py` (new) — the sole sanctioned writer module.
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (edited) — Step 2 swap.
- `.claude/workflows/implement-ticket.js` (edited) — Finalize step 4 instruction.
- `CLAUDE.md` (edited) — After Work bullet.
- `docs/parity_ledger/infrastructure.yaml` (edited) — `INFRA-416`'s `v2_evidence`/`test_path`.
- `tests/tools/test_working_log_writer.py` (new) — helper unit tests + AST sole-writer guard
  (Steps 4 and 7).
- `tests/tools/test_finalize_working_log_uses_helper_pin.py` (new) — Step 3's instruction pin.
- `docs/ai/ticket-lifecycle.md` (edited, Document-Update phase, commit `350279eb7`) — Finalize
  step 3 instructions updated from the old hand-rolled csv-quoting example to the Write-tool JSON
  + `--data-file` contract, naming the new AST sole-writer guard test.
- `staging_artifacts/TCK-20260912-WORKING-LOG-APPEND-HELPER/investigation.md`,
  `staging_artifacts/TCK-20260912-WORKING-LOG-APPEND-HELPER/plan.md`,
  `staging_artifacts/TCK-20260912-WORKING-LOG-APPEND-HELPER/test_plan.md` — created/revised during
  this ticket's own Investigate/Plan phases (plan.md through 3 review rounds) earlier in this
  session, prior to this Implement pass; listed here per ticket-hygiene requirements even though
  this Implement pass did not itself edit them further.

## Completion Summary

Added `tools/working_log_writer.py` as the one sanctioned writer for `tickets/working_log.csv`
rows (LF-only, `QUOTE_MINIMAL`, the documented 6-column order, pure bottom-append), switched
`record_hand_orchestrated_closure.py` to call it, and pointed `implement-ticket.js`'s Finalize step
4 at it via a `Write`-tool JSON file + `--data-file` contract (never shell/Python source-embedding
of agent-authored title/summary text). Added an AST-based test
(`test_working_log_csv_has_exactly_one_writer`) that resolves `open()`/`.open()` calls back to
literal path arguments through module-level constants and single-hop parameter-default
indirection — a grep-based guard was rejected in planning because the literal path string never
appears on the same line as the `open(` call it protects. Updated `INFRA-416`'s parity-ledger
entry (full-dict read-modify-write, all other fields preserved) and CLAUDE.md's After Work bullet
to name the helper as mandatory. This is one sanctioned writer plus a CI guard that catches a
second write path appearing in `tools/` — not a hard lock; an agent could still open the file
directly, and nothing in the filesystem prevents that.
