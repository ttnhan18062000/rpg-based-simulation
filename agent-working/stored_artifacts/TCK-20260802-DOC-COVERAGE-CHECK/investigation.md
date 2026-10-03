---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-DOC-COVERAGE-CHECK
artifact_type: investigation
tags: [workflows, documentation]
---

# Investigation — TCK-20260802-DOC-COVERAGE-CHECK

## Current Behavior

`tools/gate_checks/done_checker_static.py::run_static_precheck` (lines 306-322) aggregates 6 checks
in a fixed tuple, each a plain `(status, evidence)`-returning function. Condition 6 ("Docs updated")
in `docs/ai/ticket-lifecycle.md`'s 13-condition table has **no** static function backing it at all —
unlike conditions 3 (`ticket_location`), 4 (`staging_artifacts_complete`), 7
(`working_log_no_row_yet`), 10 (`data_runs_clean`), 12 (`frontmatter_valid`), and the unnumbered 6th
check `ticket_field_values_valid` (added by `TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM` as an "extra
check beyond the numbered 5" — same precedent this ticket follows).

`_extract_section_text(ticket_text, heading)` (lines 80-92) already exists and is exactly what's
needed to pull a `## {heading}` body out of a markdown file up to the next `## ` heading — reused
unmodified for reading `investigation.md`'s "## Docs Requiring Update" section.

`tools/gate_checks/parity_updater_static.py::cross_reference_touched` is the closest existing
precedent for "compare a required-doc list against what git shows as touched" — but it takes
pre-fetched `touched_ledger_files` lines as a parameter; the *caller* (`implement-ticket.js`'s Parity
phase) is the one that runs `git status --porcelain -- docs/parity_ledger/` via `bash()` and passes
the raw output in. This convention exists because the Parity phase already makes multiple separate
`bash()` calls around its `agent()` call, so pre-fetching there is cheap.

`run_static_precheck`'s own call site is different: it's invoked as **one** self-contained
`python3 -c "..."` one-liner embedded directly in `done-checker`'s agent prompt
(`implement-ticket.js:1262`), with no surrounding orchestrator `bash()` calls to pre-fetch git state.
Extending that call site to also thread through pre-fetched git output would mean restructuring the
Verify-phase prompt block. `check_data_runs_clean`/`clean_data_runs_early` — in this *same* file —
already establish the alternative precedent: a `done_checker_static.py` function doing its own
direct filesystem I/O (`Path.rglob`) rather than depending on the orchestrator to pre-fetch anything.
Given `run_static_precheck`'s single-call-site shape, the new check follows that in-file precedent
instead: it shells out to `git status --porcelain` itself via `subprocess`, fail-open (empty set) on
any error — no `implement-ticket.js` change needed for this data-fetching, only for the two prompt-
text edits (Investigate section format instruction, Verify condition-6 citation).

## Mechanics / Engine Constraints

None — process/orchestration tooling, not simulation mechanics.

## Docs Requiring Update

- `docs/ai/ticket-lifecycle.md`: Investigate section (format requirement) and Verify section
  (Step 0b's check count 6→7, condition 6's real backing) both describe exactly what's changing
  here.

## Parity Ledger Overlap

None. Not a simulation-mechanics subsystem.

## Prior Work

- `TCK-20260802-DOC-UPDATE-DISCIPLINE`: introduced `docs_to_update` (Investigate) and its
  Implement-phase advisory cross-check — this ticket's direct predecessor and the source of the
  `investigation.md` "## Docs Requiring Update" section this ticket now tightens the format of.
- `TCK-20260705-GATE-DET-DONE-CHECKER`: introduced `done_checker_static.py` and
  `run_static_precheck` itself.
- `TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM`: added `ticket_field_values_valid` as a 6th check —
  direct precedent for "an extra check beyond the originally-numbered 5, not itself mapped to a
  dedicated DoD condition number, but still cited from the Verify prompt."

## Risks and Open Questions

- **Test fixture compatibility**: `tests/tools/test_done_checker_static.py`'s existing
  `_write_artifact_dir` fixture writes `investigation.md` with frontmatter only, no
  "## Docs Requiring Update" section at all. Confirmed this is safe: `_extract_section_text` returns
  `""` when the heading is absent, and the new check treats an empty section the same as an explicit
  "None." — `required_docs == []` — returning `PASS` *before* ever calling the git subprocess. This
  means `test_run_static_precheck_all_pass_eligible` (which `monkeypatch.chdir`s into a `tmp_path`
  that is **not** a git repository) still passes: the git subprocess call is never reached in that
  test's scaffolded fixture.
- **Fail-open on git subprocess failure**: if `git status --porcelain` fails (missing binary, not a
  repo, etc.) `_git_touched_paths()` returns an empty set — meaning any *actually*-flagged required
  doc would then show as "missing" (FAIL). This is a deliberate fail-closed choice at the
  "doc-was-flagged-but-nothing-touched" level, consistent with `_find_flagged_data_run_files`'s own
  existing "an unparsable start_ts is not evidence of cleanliness — flags any file found" philosophy
  — not a new inconsistent risk pattern.
- **Concurrent-session residual risk**: `git status --porcelain` reflects the *whole* working tree,
  not just this ticket's own changes — a concurrent session's edit to the same doc path would read
  as "touched" even though this ticket's own implementer didn't touch it. This mirrors
  `clean_data_runs_early`'s already-documented, already-accepted "Residual Risk: Concurrent-Session
  Overlap Window" — observed directly in this same working session (a second, unrelated session was
  found actively editing `tickets/todos/parity-ledger-sqlite-context/` while this work was
  happening). Not a new risk class to solve here.

## Anti-Drift Hazards

- Do not make this new check apply retroactively to the Implement-phase advisory's design — that
  one stays advisory (non-blocking) per the earlier, separate design decision. This ticket adds a
  second, independent, later checkpoint — it does not change the first one's blocking behavior.
- Do not let the bullet-format regex become so strict that a reasonable, otherwise-correct
  investigator output gets misclassified as a "format regression" FAIL — the regex only needs to
  reliably extract backtick-wrapped `docs/...` paths from the start of each bullet line; free-text
  reasoning after the path is irrelevant to parsing and must not be validated.
- Keep `check_docs_to_update_coverage` read-only (git status only, never `git add`/`git commit`/
  mutating calls) — mirrors every other `check_*` function in this file except
  `check_registry_entry_regenerated`, which is documented as a deliberate, singular exception.
