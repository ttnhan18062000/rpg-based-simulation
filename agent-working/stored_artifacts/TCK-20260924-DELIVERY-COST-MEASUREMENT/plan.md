---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-DELIVERY-COST-MEASUREMENT
date: 2026-09-24
tags: [delivery, agent-monitoring, benchmarking]
---

# Plan — TCK-20260924-DELIVERY-COST-MEASUREMENT

## Extension to `tools/agent-monitoring/bash_command_mix.py`
Add `gh_subcommand_key(input_summary) -> str` and `GH_OBSERVATION_SUBCOMMANDS`/
`GH_ACTION_SUBCOMMANDS` frozensets (investigation.md decision 1). No existing function's behavior
changes — purely additive, called only on rows `bash_command_mix.bash_head(summary) == "gh"`.

## New module: `tools/delivery/delivery_cost_measurement.py`
- `build_delivery_cost_report(rows, since_week, through_week, measured_ref, measured_sha) -> dict`
  — filters `tool == "Bash"`, classifies each via `bash_command_mix.bash_head` +
  (for `gh` rows) `gh_subcommand_key`; computes `gh_calls_total`, `gh_pr_create_count`,
  `gh_calls_per_pr`, observation/action split, `gh_unparseable_count`, and reuses
  `bash_command_mix.build_bash_mix_report`'s own `git status`/`git diff` share for the git-side
  context figure (Scope item 1's last bullet) rather than recomputing it.
- `measure_subject_traceability(run_command, since_week, through_week, measured_ref) -> dict` — `git
  log <measured_ref> --since/--until <week-range-as-dates>` (ISO week bounds converted to calendar
  dates) `--format=%s`; share of subjects containing a `TCK-` ID (investigation.md decision 2).
- `build_report(...) -> dict` — top-level function combining both, always carrying
  `measured_ref`/`measured_sha` (AC2) and the snapshot caveat string (AC4). Requires `ref` — no
  silent working-tree fallback (AC3): omitting `--ref` on the CLI prints an unmistakable
  working-tree-snapshot label in the same field `--ref` would have populated, matching
  `bash_command_mix.py`'s own existing `render_markdown` precedent for that exact distinction,
  rather than refusing to run.
- `main()` CLI: `--ref`, `--since-week`, `--through-week`, `--json`. Read-only; never opens
  `agent-monitoring/data/` for writing (matches the module it extends).

## Tests: `tests/tools/test_delivery_cost_measurement.py`
1. AC1 — fixture rows produce the `gh`-calls-per-PR figure, observation/action split, and subject
   traceability in one `build_report()` call.
2. AC2 — `measured_ref`/`measured_sha` present in output; asserted via a fixture ref.
3. AC3 — no `--ref` given: output unmistakably labeled a working-tree snapshot, never silently
   presented as equivalent to a pinned reading.
4. AC4 — the snapshot caveat string is present in every report, ref or no ref.
5. AC5 — import-structure test: `delivery_cost_measurement.py` imports `bash_head`/
   `bash_subcommand_key`/`load_tools_rows_from_ref` from `bash_command_mix`, and a source-scan test
   asserts no duplicate head-classification logic (no second `if head ==` command-name ladder)
   exists in the new file.
6. AC6 — same fixture rows classified twice produce byte-identical JSON output.
7. AC7 — recorded in `## Test Summary`/`## Completion Summary`: a real run against `origin/main`
   over W30–W39, with its resolved SHA.
8. AC8 — a real run against `origin/main` W30–W39 compared to plan §1.1's cited figures (1,796 `gh`
   / 106 `gh pr create` / 16.9 per PR at `75ab942b4`); any difference attributed to ref drift
   (`origin/main` has advanced past `75ab942b4`), not treated as a bug to chase.
9. Recorded once run.

## Out-of-scope guardrails
- No "after" measurement attempted or presented anywhere in this ticket's output or tests — per
  design's explicit warning, this batch's own corpus is not a valid after-datapoint.
- No token-cost attribution, no per-agent breakdown, no blocking threshold.
