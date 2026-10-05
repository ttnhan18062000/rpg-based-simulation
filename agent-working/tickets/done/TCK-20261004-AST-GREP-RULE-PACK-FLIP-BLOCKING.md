---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING
phase: done
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

## Title
M5f: After its own two-week soak, make the ast-grep rules (N3, N4, E3) block new violations

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Roadmap decision 8.10: a new check is advisory for two weeks before it blocks. The `ast_grep` tool joined the code-health ratchet under `TCK-20261004-AST-GREP-RULE-PACK-ADVISORY`; the M4 flip (`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`, 2026-10-17) excludes it. This ticket promotes it to blocking. BLOCKED until its soak ends: soak start is the merge date of the PR carrying the rule pack, end is start + 14 days; both are written here at that merge.

## Scope
- Soak review first: false positives per rule (N3 counts imported names, E3 counts `except` bodies of only `pass`), rows deleted as debt was paid, how many `ast_grep` rows were reseeded or added
- Remove the exclusion of `ast_grep` from the blocking set the M4 flip created (the ratchet then fails a PR on a new or worse `ast_grep` finding)
- Ask the owner to confirm the required-check setting (owner action; record it)
- Announce the date to the other planners before flipping: it makes N3, N4 and E3 violations in new code fail a PR for every domain that edits `src/`

## Out of Scope
- Any file under src/
- New rules, T3, autofix

## Acceptance Criteria
- [ ] Soak start and end dates recorded here
- [ ] Soak review written with dates, counts and dispositions
- [ ] A PR that adds a new `ast_grep` violation fails and one that does not passes (demonstrated on real PR runs)
- [ ] Owner confirmed the required-check setting
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/guidelines/python_code_standard.md (N3, N4, E3)

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/rules/
- codebase/health/
- .github/workflows/test.yml

## Assumptions / Open Questions
- Soak start 2026-10-04 (PR #315 merged 2026-10-04T06:26:43Z), end 2026-10-18 (start + 14 days). Roadmap decision 8.18: ships in the one flip batch, merged on or after 2026-10-18; the soak review is drafted now and finalized after the window
- N4 leaves a trailing digit to the reviewer; the standard's Enforcement cell says so

## Implementation Notes
- `REPORT_ONLY_TOOLS` is now `{"jscpd"}`; `SKIPPABLE_TOOLS` is untouched (still a subset), and a missing `ast-grep` binary still exits 2. A new or worse `ast_grep` finding makes `check` exit 1 with the `::error::` annotation.
- Flipped pins in `test_code_health_blocking_policy.py` (policy set, blocking parametrization with `ast_grep`, new-ast_grep test now exit 1). Mutation proof: re-adding `ast_grep` to the report-only set fails 3 tests on the assertions, not on imports.
- Docs: N3, N4, E3 cells read "blocking in the `Code health` ratchet"; environment guide, Makefile help, CI comment and the `ratchet.py` comment name only jscpd as report-only.
- Live demo (step 5): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37213577739 : `Code health` failed at the `Code health ratchet` step on one `ast_grep e3-silent-except` finding; `Type check` passed. The E3 demo uses a typed silent `except OSError: pass` rather than a bare `except: pass`: a bare `except:` would also trip ruff `E722`, and the proof would not isolate ast-grep.
- Precondition (2026-10-04, `origin/main` 053f459e4): `check` gives 0 new, 0 worse including the 111 `ast_grep` rows. Repeat right before merge; both runs are recorded in `python_code_craft_structure_soak_review.md`.

## Test Summary
- PR #329's CI at merge: 19 checks pass, 3 skipped (Scenario lane, SimQ grade-anchor drift, Slow regression), none failing. Final soak measurement and the local `check`/`validate`/`mypy_gate` runs on `c8c355459` (all exit 0) are in the soak reviews.

## Files Changed
- `codebase/health/ratchet.py`, `codebase/health/scan.py`, `.github/workflows/test.yml`, `Makefile`
- `tests/codebase/test_code_health_blocking_policy.py`
- `docs/guidelines/python_code_standard.md` (N3, N4, E3 cells), `docs/guidelines/agent_working_environment.md`
- `docs/plans/codebase_health/python_code_craft_structure_soak_review.md`

## Completion Summary
The ast-grep rules N3, N4 and E3 are blocking in the `Code health` ratchet and merged early by owner decision on 2026-10-05T14:47:13Z (PR #329), about 1 of the planned 14 soak days. `REPORT_ONLY_TOOLS` is `{jscpd}`. The soak review notes the per-rule spot-check was not re-filled (annotations carry counts, not rule names); the 111 `ast_grep` rows were 0 new or worse on `c8c355459`; demo step 5 (PR #331) failed `Code health` on one `e3-silent-except` finding.
