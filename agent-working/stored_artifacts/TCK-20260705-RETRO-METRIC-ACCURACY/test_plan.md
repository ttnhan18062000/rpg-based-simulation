---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-RETRO-METRIC-ACCURACY
artifact_type: test_plan
tags: [agent-monitoring, retro, data-quality, schema-fallback]
---

# Test Plan — TCK-20260705-RETRO-METRIC-ACCURACY

## Regression Surface

`tools/agent-monitoring/generate_retro.py` has **no existing automated test coverage** — confirmed by searching the repo for any `tests/*agent_monitoring*` or `tests/*agent-monitoring*` path (none found) and by cross-referencing the sibling ticket `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`'s own Test Summary, which states the same for `validate.py`, `record_run.py`, `record_events.py`, `pre_tool_hook.py`, `post_tool_hook.py`: "No automated test harness exists for `tools/agent-monitoring/*.py` anywhere in this repo... a pre-existing, documented convention gap, not introduced or fixed by this ticket." This ticket inherits that same convention — the absence of pytest coverage here is not a gap unique to this work, and this ticket should not be the one to introduce a new testing pattern unilaterally for the whole tool family. Verification for this tool family is consistently done via direct CLI runs + manual/scripted diff of before/after output (as `validate.py`'s sibling ticket did: "warning count went from 54 to 62 ... confirmed via diff of the full warning list before/after").

Regression surface if the fix is implemented incorrectly:
- `generate()` (`tools/agent-monitoring/generate_retro.py:53-188`): Run Summary, Gate Failure Breakdown, Tier Distribution, Summary Quality sections.
- `_update_index()` (`tools/agent-monitoring/generate_retro.py:235-256`): `agent-monitoring/retro/index.md` per-week DONE/fails columns — has its own independent DONE/fails computation, separate code path from `generate()`, must be fixed in lockstep or it will silently diverge from the main report (see investigation.md Anti-Drift Hazards).
- Any other tool reading `runs.jsonl`/`events.jsonl` directly is out of this ticket's blast radius (`validate.py` already fixed under its own ticket; `query.py`, `retro_nudge_hook.py` are unaffected — confirmed by reading `retro_nudge_hook.py` which already has the fallback pattern independently).

## New Tests Required (per AC)

No pytest test files should be created for this ticket — matching the established no-test-harness convention for `tools/agent-monitoring/*.py` (same precedent as `validate.py`'s sibling ticket, `record_run.py`, `record_events.py`). Verification below is via direct CLI execution and output diffing, not new automated tests.

### AC1/AC2 — empty-summary count computed over current-schema events only, legacy records reported separately
- Run `python3 tools/agent-monitoring/generate_retro.py --all` before the fix; capture the current Summary Quality section verbatim (baseline: `Empty summary | 246`, warning text "check agent prompts for `summary` field").
- Apply the fix (predicate: `agent` field present/not-`None` distinguishes current from legacy schema for events.jsonl — matches the discriminator confirmed in investigation.md, i.e. do NOT reuse the `final_status`/`status` discriminator, that's runs.jsonl's Finding 3 concept).
- Re-run `python3 tools/agent-monitoring/generate_retro.py --all` after the fix. Expect:
  - `Empty summary (current schema)` == 0 (measured directly against live data: 0 of 1707+ current-schema events are empty).
  - A new, separately labeled row/line for legacy records, e.g. "Legacy-format records (summary field not applicable): ~246-258" (exact wording decided at Plan/Implement time) — must not be phrased as an "issue" or trigger the "check agent prompts" warning.
  - The `_⚠ ... check agent prompts for summary field_` warning line must NOT fire when the current-schema empty count is 0, even though the legacy bucket is non-zero.

### AC3 — truncated-summary (>200 char) count unchanged
- Diff the `Truncated (>200 chars)` value before/after the fix — must remain identical (measured directly: 38 for current-schema-only if the fix scopes truncation the same way as empty-summary; confirm at Plan time whether truncation was already implicitly current-schema-only or needs the same explicit filter — currently line 86 counts over ALL events with no filter, so if `long_summaries` moves to a current-schema-only computation, expect 38, not 46; ticket's AC4 says "unchanged" which most likely means the number the ticket-filer already observed and expects the display, so confirm which of 38/46 was the number already surfaced in `RETRO-ALL.md`/`RETRO-2026-W27.md`'s existing committed Notes before locking behavior).

### AC4 — epic tier DONE-rate excludes EPIC_SCOPED
- Run `python3 tools/agent-monitoring/generate_retro.py --all` before the fix; capture `| epic | 58 | 26 | 44% |` (baseline).
- Apply the fix (exclude `EPIC_SCOPED`-classified runs, using the fallback-aware status resolution per Finding 3, from the epic-tier denominator, or add a separate "scoped only" column).
- Re-run. Expect epic tier row to read approximately `| epic | 39 | 31 | 79% |` (or equivalent split-column presentation) — verified directly against live data as 31/39 = 79.49%, `fmt_pct`'s integer-floor formatting renders "79%" not "80%".
- Confirm no other tier's DONE count changes as a side effect of touching `tier_done`/`tier_counts` logic (hotfix/standard tiers have no `EPIC_SCOPED` values — spot check via `Counter(r.get("tier") for r in runs if r.get("final_status")=="EPIC_SCOPED")` returns only `epic`).

### Newly-confirmed scope (Finding 3) — `final_status`/`status` fallback, if added to this ticket's Scope
- Before fix: `done_count` (Run Summary "Completed (DONE)") over ALL runs (not just epic) undercounts by however many non-epic runs also carry legacy `status`-only DONE records. Re-run the same `(final_status, status)` pair-distribution check used in investigation.md across the FULL `runs.jsonl` (not just epic tier) to get the exact all-tier undercount, and assert the fixed `done_count` matches `sum(1 for r in runs if (r.get("final_status") or r.get("status")) == "DONE")`.
- `gate_fails`/`gate_counter` (Gate Failure Breakdown): assert no run with legacy `status: "DONE"` and `final_status: None` appears in the post-fix `gate_counter` (currently it does, misclassified as a `None`-status gate failure).
- `_update_index()` lines 252-253: re-run `make agent-monitoring-retro` (or the direct `--all`/`--week` invocation that triggers `_update_index()`) and diff `agent-monitoring/retro/index.md`'s `done`/`fails` columns before/after — must reflect the same fallback-aware counts as the main report for the corresponding week/label, i.e. the two artifacts must agree with each other post-fix (this is the two-code-path consistency hazard flagged in investigation.md).
- Confirm via direct measurement (already done in this investigation) that the corrected epic rate is 31/39 = 79%, matching AC3's literal target number — i.e. treat "AC3 passes" as contingent on Finding 3 also being fixed, not achievable by Finding 2 alone (67%).

## Scoped Pytest Commands

None applicable — no pytest suite exists for this tool. Do not invent one unless the user/Plan phase explicitly decides to establish a new testing convention for `tools/agent-monitoring/` as a separate, intentional scope decision (out of scope for this ticket per its own Out of Scope section, which limits itself to `generate_retro.py`'s metric computation and reporting).

If any adjacent Python test suite exists that imports or shells out to this tool indirectly (none found in this investigation — confirmed via repo-wide search for `agent_monitoring` / `agent-monitoring` under `tests/`), it would need to be re-run; none currently do.

## Anti-Drift Test Guards

- **Guard against conflating the two legacy-schema discriminators.** A test/verification step must confirm the events.jsonl fix (Finding 1, keyed on `agent is None`) and the runs.jsonl fix (Finding 3, keyed on `final_status is None`) are applied independently and do not share a single boolean helper that silently applies the wrong field's absence-check to the wrong file's records.
- **Guard against `_update_index()` drifting from `generate()`.** After any fix to `done_count`/`gate_fails`/`tier_done` in `generate()`, re-generate at least one dated week report AND run `_update_index()` (implicitly triggered by `main()`), then confirm `agent-monitoring/retro/index.md`'s `done`/`fails` numbers for that week match what the corresponding `RETRO-<week>.md` report shows for `done_count`/`len(gate_fails)` — currently these two code paths (lines 59-60 vs 252-253) are independently maintained and could silently diverge if only one is patched.
- **Guard against re-breaking AC4's already-preserved truncation count.** Any refactor that scopes `empty_summaries` to current-schema-only must not accidentally apply the same schema filter to `long_summaries` in a way that changes its displayed value from whatever is already committed in `RETRO-ALL.md`'s existing Notes section (38 vs 46 — confirm which was already reported before this ticket, to avoid an unintended AC4 regression).
- **Guard the "no silent exclusion" requirement.** A post-fix report run must show the legacy-events bucket count explicitly in the rendered Markdown (not just in code/logs) — grep the generated `RETRO-ALL.md` for the new legacy-bucket line to confirm it renders, not just that the empty-summary number went to 0.
- **Do not delete or alter the underlying `agent-monitoring/runs.jsonl` / `events.jsonl` records** — both files are read-only inputs per the ticket's Related Code Areas; all fixes are confined to `generate_retro.py`'s (and possibly `_update_index()`'s) computation/rendering logic only.
