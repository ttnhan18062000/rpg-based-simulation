---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-MYPY-BASELINE-ADVISORY
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-MYPY-BASELINE-ADVISORY

## Title
M4c: mypy baseline with mypy-baseline, advisory until the soak ends

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The CI typecheck job runs `mypy src/ ... || true` with continue-on-error, so nothing is gated. Roadmap 6.2 chose mypy + mypy-baseline to make it blocking without src/ edits; owner decision 2026-10-03: it soaks two weeks with the ratchet and flips in the same follow-up ticket. Measured 2026-10-03: 1,569 errors in 236 files.

## Scope
- Add `mypy-baseline` pinned exactly to a dependency group the typecheck job syncs; regenerate uv.lock and the requirements.txt export
- Generate the baseline from main at a stable path (e.g. registries/mypy_baseline.txt) and record its path and entry count in the code-health registry or snapshot per roadmap 6.3
- CI typecheck step: `mypy src/ --config-file pyproject.toml | mypy-baseline filter`, still advisory (keep `continue-on-error`; `|| true` removal is the flip ticket's job); job summary states new-error count
- `make typecheck-py` uses the same filter; document regenerating the baseline (`mypy-baseline sync`) and when it is allowed
- Update INFRA-TYPE-001 (docs/parity_ledger/infrastructure.yaml) evidence and tests/static/test_typecheck_gate_configured.py, listing each edit with its reason

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- Changing [tool.mypy] strictness, python_version or excludes
- Fixing any type error (the 104 name-defined errors are routed to the rpg domain separately)

## Acceptance Criteria
- [ ] Baseline committed; `mypy src/ ... | mypy-baseline filter` reports 0 new errors on main
- [ ] Investigate shows how mypy-baseline normalises line numbers, and a test or recorded demo proves an unrelated edit above an existing error does not resurface it, while a genuinely new error is reported
- [ ] CI typecheck step uses the filter, remains advisory, and its summary shows the new-error count
- [ ] `pytest tests/static/test_typecheck_gate_configured.py` passes; INFRA-TYPE-001 updated with v2_evidence
- [ ] `uv lock --check` passes and the export reproduces requirements.txt
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20260623-TYPE-CHECKER
- TCK-20261002-UV-REMAINING-CI-JOBS

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/parity_ledger/infrastructure.yaml (INFRA-TYPE-001)
- docs/audits/D13_type_safety.md
- docs/archive/plans/open_audit_findings_backlog.md (Section 1G, cited by the CI comment)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260623-TYPE-CHECKER/

## Related Code Areas
- .github/workflows/test.yml (typecheck job)
- pyproject.toml, uv.lock, requirements.txt
- Makefile (typecheck-py)
- tests/static/test_typecheck_gate_configured.py
- docs/parity_ledger/infrastructure.yaml

## Assumptions / Open Questions
- Baseline churn: other domains edit src/ daily; the soak measures how often the baseline needs a sync. Record that rate for the flip decision
- Which dependency group: `dev` (typecheck job already syncs it) unless Investigate finds a reason for its own group

## Implementation Notes
- Dependency: `mypy-baseline==0.7.4` in the `dev` group (the typecheck job and `make typecheck-py` already use it). Planner condition B: the `uv.lock` diff adds exactly one package, `mypy-baseline` 0.7.4 (11 lines), with no dependencies of its own and no version moves; `requirements.txt` gains one line (`mypy-baseline==0.7.4`) and `uv lock --check` passes.
- Config in `[tool.mypy_baseline]`: `baseline_path = "registries/mypy_baseline.txt"`, `allow_unsynced = true`, `hide_stats = true`, `sort_baseline = true` (planner nit, taken: the committed baseline is sorted, same 1,569 entries, so re-sync diffs stay minimal and two syncs are byte-comparable; the gate still exits 0 against it), `ignore_categories = ["note", "annotation-unchecked"]`.
- Notes (planner condition A): mypy emitted 1,716 lines for 1,569 errors; the other 147 are `note:` lines. With `ignore_categories = ["note"]` the baseline held 1,586 lines, because 17 remaining notes are standalone `annotation-unchecked` notes that carry their own category; ignoring that category too gives a baseline of exactly **1,569 entries, all errors, 0 notes**. Demonstrated (scratch dir, real output) and tested (`tests/tools/test_mypy_gate.py`): a reworded note alone does not count as new; a new error with an attached note reports only the error; a standalone `annotation-unchecked` note is neither baselined nor reported.
- Baseline: `registries/mypy_baseline.txt`, generated from main's source with `make typecheck-baseline-sync` (1,569 lines, line numbers normalised to `:0:`). `mypy src/ ... | mypy-baseline filter` reports 0 new errors, exit 0, on this tree. Planner: the baseline is re-synced as the last step before the batch push (after merging origin/main) together with the code-health reseed; both counts get recorded here.
- **Final re-sync (planner), last step before the batch push, on the head merged with `origin/main`** (`make typecheck-baseline-sync` after clearing `.mypy_cache`, 20 s): 1,569 entries before and 1,569 after; `registries/mypy_baseline.txt` is byte-identical to the committed version (sorted, errors only); `python3 -m tools.code_health.mypy_gate` reports `0 new errors (baseline holds 1569 entries)`, exit 0. Both counts are therefore the same: 1,569 (first sync) and 1,569 (final).
- **Second final re-sync (planner: origin/main moved again, with `src/` changes), on the head merged with it:** the gate against the committed baseline already reported `0 new errors (baseline holds 1569 entries)`; `make typecheck-baseline-sync` then produced 1,569 entries, byte-identical to the committed `registries/mypy_baseline.txt` (nothing changed). So the baseline needed no new sync for #303.
- Gate `tools/code_health/mypy_gate.py` (condition C): runs mypy, pipes it through `mypy_baseline filter`, prints the new errors, appends a summary stating the new-error count and the current baseline entry count to `--summary-out` on every run, prints `::warning::mypy-baseline: N new errors (advisory); see job summary` with `--annotate`, returns the filter's exit code (0/1), and on any failure to run (mypy crash, missing baseline, missing tool) writes a "could not run" summary line and warning and returns 2. This summary replaces a snapshot metric.
- Roadmap 6.3 amended (one paragraph, the same pattern as the complexipy note): mypy-baseline's path and entry count are recorded in `python_code_standard.md` and the gate summary, not in the registry; this departs from the original 6.3 wording on purpose.
- CI: the `typecheck` job's `mypy` step now runs the gate; the step keeps its name and `continue-on-error: true` (the step-level setting carries the advisory behaviour; the old `|| true` is gone because the gate's exit codes are meaningful). `make typecheck-py` pipes into `mypy_baseline filter || true` (the `|| true` stays until the flip ticket). New `make typecheck-baseline-sync`.
- Re-sync policy (planner condition D): `allow_unsynced = true` in CI and `make typecheck-py`; `typecheck-baseline-sync` only on main, by the codebase domain, together with the code-health reseed, never to hide a new error and never by a domain fixing one error. Recorded in `python_code_standard.md`, in the target's help text, and as a soak-review checklist line in the flip ticket ("how many syncs were needed").
- Measurements (reproduced, mypy 2.1.0, 2 GB cap): 1,569 errors, 1,716 output lines, 239 file paths, 38 s uncached, 407 MB peak RSS (the planner measured 48 s and about 400 MB).
- Demo of the proof criteria on real output (scratch dir): every line number shifted by +40 -> `filter` exit 0, nothing printed; one new error -> exit 1, only that error; an identical message repeated in the same file -> exit 1; a fixed error with a stale baseline -> exit 0 with `allow_unsynced`, exit 1 without it. The same behaviours are tests in `tests/tools/test_mypy_gate.py`, including one that runs real mypy on a tiny project.

## Test Summary

## Files Changed
`pyproject.toml` (dev group, `[tool.mypy_baseline]`), `uv.lock`, `requirements.txt` (generated), `registries/mypy_baseline.txt` (new), `tools/code_health/mypy_gate.py` (new), `.github/workflows/test.yml` (typecheck `mypy` step), `Makefile` (`typecheck-py`, new `typecheck-baseline-sync`), `docs/parity_ledger/infrastructure.yaml` (INFRA-TYPE-001 text, v2_evidence, test_path), `docs/guidelines/python_code_standard.md`, `docs/plans/codebase_health/python_code_craft_roadmap.md` (6.3), the flip ticket (soak-review line, mypy step wording).

Edits to existing tests: none were weakened. `tests/static/test_typecheck_gate_configured.py` keeps its three original tests unchanged and passing (the Makefile target still contains `mypy src/` and `pyproject.toml`; the workflow still has a step named `mypy` and the text `mypy src/`, now in the comment that explains the gate) and gains three tests (baseline config and file, Makefile filter and sync target, CI step runs the gate and is advisory). New: `tests/tools/test_mypy_gate.py`.

## Completion Summary
