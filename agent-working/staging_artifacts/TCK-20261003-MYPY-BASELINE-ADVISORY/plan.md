---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-MYPY-BASELINE-ADVISORY
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261003-MYPY-BASELINE-ADVISORY

Same branch (`python-code-craft-gates`), after ticket 1. No `src/`, `.claude/`, `CLAUDE.md` edits; no `[tool.mypy]` change.

1. **Dependency**: add `mypy-baseline==0.7.4` to `dev` in pyproject.toml; `uv lock --system-certs`; the `uv.lock` diff must be the new package(s) only (no version moves); `uv export` reproduces `requirements.txt` plus the new line(s) (regenerate it). Add `[tool.mypy_baseline]` (`baseline_path = "registries/mypy_baseline.txt"`, `allow_unsynced = true`, `hide_stats = true`) with a comment saying why `allow_unsynced`.
2. **Baseline**: generate on this branch from `mypy src/ ...` output (38 s, 407 MB, under the cap) with `python -m mypy_baseline sync`; commit `registries/mypy_baseline.txt` (1,716 lines at today's main). `filter` on the same output must report 0 new errors, exit 0. Re-run `sync` as the last step before the batch push (after merging origin/main), with the code-health reseed, and record both counts in the ticket.
3. **Gate module** `tools/code_health/mypy_gate.py` (not src/): `python3 -m tools.code_health.mypy_gate [--summary-out PATH] [--annotate]` runs mypy with the repo command, pipes it through `mypy_baseline filter`, prints the new errors, appends a Markdown summary (new-error count, or OK) to `--summary-out`, prints one `::warning::mypy-baseline: N new errors (advisory); see job summary` with `--annotate`, and returns the filter's exit code (0 / 1). If mypy cannot run (exit above 1) or the filter itself fails to run, it still writes a "could not run" summary line and warning and returns 2 (the lesson of ticket 1's review: a broken tool must not look like OK). Unit tests drive it with a fake mypy output; an end-to-end test builds a tiny project in tmp_path.
4. **CI**: the `typecheck` job's `mypy` step becomes `python3 -m tools.code_health.mypy_gate --summary-out "$GITHUB_STEP_SUMMARY" --annotate`. Still named `mypy`, still `continue-on-error: true`, the `|| true` stays only if needed: the gate returns 1 on new errors and 2 on could-not-run, so the step-level `continue-on-error` carries the advisory behaviour (removal of the advisory status is the flip ticket). The text `mypy src/` stays in the file (a comment above the step) because INFRA-TYPE-001's test greps for it; I will rather update that test than leave a stale comment.
5. **Makefile**: `typecheck-py` becomes `python3 -m mypy src/ --config-file pyproject.toml --no-error-summary | python3 -m mypy_baseline filter || true`; help text says baseline-filtered and advisory; add a `typecheck-baseline-sync` target (`... | python3 -m mypy_baseline sync`) documented as codebase-domain-only, main-only.
6. **Tests/ledger**: edit `tests/static/test_typecheck_gate_configured.py` (the Makefile target now pipes into `mypy_baseline filter`; the CI step runs the gate) listing each edit with its reason; add tests for the gate and for the config keys and baseline file existing; update INFRA-TYPE-001 `text` and `v2_evidence` (baseline file, filter, gate module, advisory until the flip) and its `test_path` if needed.
7. **Docs**: `python_code_standard.md` (mypy row: "advisory, baseline-filtered: new errors reported, existing 1,716 baseline lines held in registries/mypy_baseline.txt", baseline path and entry count, when `sync` is allowed) and the Makefile help.
8. **Verify**: demo in a scratch dir recorded in the ticket (unrelated edit above an existing error → exit 0; new error → exit 1 and only that error; fixed-but-unsynced → exit 0), plus the end-to-end test; `uv lock --check`; export diff; static tests; INFRA-TYPE-001.
9. **Close** in the batch closure commit after the green PR run (link recorded).

## Scope guards
No type error fixed, no `# type: ignore`, no change to `[tool.mypy]` strictness, python_version or excludes. Nothing becomes blocking.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| Baseline committed; filter reports 0 new on main | 2 |
| Line-shift edit proof and new-error proof | investigation (reproduced on real output), 3 and 8 (tests) |
| CI step uses the filter, advisory, summary shows new-error count | 3, 4 |
| Static test passes; INFRA-TYPE-001 updated | 6 |
| lock check and export | 1 |
| Green PR run link | 9 |
| No src/.claude/CLAUDE.md in diff | scope guards |

## Questions for the planner
- OK to add the small `tools/code_health/mypy_gate.py` module (so the "could not run" case and the summary are testable), instead of inline shell in test.yml?
- Record the baseline path and count in the ticket and `python_code_standard.md` only, not as a new snapshot metric (which changes the snapshot schema and its pins)?
