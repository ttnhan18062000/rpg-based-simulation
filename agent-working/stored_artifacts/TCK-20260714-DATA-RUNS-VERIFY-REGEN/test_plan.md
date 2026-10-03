---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260714-DATA-RUNS-VERIFY-REGEN
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260714-DATA-RUNS-VERIFY-REGEN

## Regression Surface

All existing coverage for `tools/gate_checks/done_checker_static.py` must keep passing unchanged — this
ticket must not weaken `check_data_runs_clean`'s or `clean_data_runs_early`'s mtime/`start_ts`
definition of "clean" (Out of Scope, unchanged from the prior ticket).

**Unit:**
- `tests/tools/test_done_checker_static.py` — all 52 existing tests, in particular:
  - The four `check_data_runs_clean`-specific tests (`test_data_runs_clean_empty_dirs_passes`,
    `test_data_runs_clean_file_before_start_ts_passes`,
    `test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path`,
    `test_data_runs_clean_unparsable_start_ts_flags_any_file`).
  - The four `clean_data_runs_early`-specific tests
    (`test_clean_data_runs_early_detects_and_removes_leftover_artifacts`,
    `test_clean_data_runs_early_preserves_files_older_than_start_ts`,
    `test_clean_data_runs_early_reuses_check_data_runs_clean_definition`,
    `test_clean_data_runs_early_returns_fail_on_deletion_error`) — pin the exact PASS/CLEANED/FAIL
    contract any new call site (agent-prompt Step 0 or a second orchestrator block) must reuse without
    modification.
  - `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` — the existing doc-guard
    pattern this ticket's new doc-guard test (see below) should mirror, not duplicate.
  - `test_run_static_precheck_all_pass_eligible` / `test_run_static_precheck_surfaces_fail_not_masked` —
    confirm `run_static_precheck`'s 5-check aggregation is untouched; this ticket must not add
    `clean_data_runs_early` as a 6th check inside it (same Out-of-Scope boundary the prior ticket set).

**Integration / architecture guard:**
- Still none for `.claude/workflows/implement-ticket.js` itself — reconfirmed via
  `grep -rl "implement-ticket.js\|implement_ticket" tests/` (zero hits). This investigation's own
  finding (the file is LLM-transcribed pseudocode, not JS-runtime-executed) makes this permanent, not
  just a current gap: no JS test harness can ever meaningfully assert "this bash() call actually ran
  during a live orchestrated session," because no runtime executes the file as code. Any coverage of
  "does the checkpoint actually fire" must be a *static, deterministic* proxy (see New Tests Required)
  or a live-run monitoring signal (the ticket's own AC #7, "next 5 runs show zero Verify-phase
  failures"), never a unit test asserting on live LLM-agent behavior.

**Arena-combat:** Not applicable.

## New Tests Required

Per acceptance criteria, and per this investigation's finding that the primary defect is *non-execution*
of an otherwise-correct function, not incorrect logic:

1. **Test name:** `test_<new_call_site>_<behavior>` (exact name depends on Plan's fix-location decision —
   e.g. `test_done_checker_static_precheck_cleans_before_reporting` if cleanup is folded into
   `run_static_precheck`'s call site or a sibling function called immediately before it; or
   `test_clean_data_runs_early_second_call_site_reuses_same_definition` if implemented as a genuinely
   separate second orchestrator-block function).
   - **Category:** unit
   - **Verifies:** whatever new Python call site Plan introduces for the pre-Verify sweep produces the
     same CLEANED/PASS/FAIL contract as `clean_data_runs_early`, using the existing `tmp_path` +
     `os.utime()` fixture pattern. If Plan reuses `clean_data_runs_early` directly (no new function),
     this test may be redundant with the existing four `clean_data_runs_early` tests — confirm at
     implementation time and skip creating a near-duplicate if so; this AC is about a new *call site*,
     not necessarily new *logic*.
   - **Location:** `tests/tools/test_done_checker_static.py`, alongside the existing
     `clean_data_runs_early` test block (lines 201-304).

2. **Test name:** `test_data_runs_clean_documented_in_orchestrator_operating_instructions` (or similarly
   named — a static doc-content guard, not a behavioral test).
   - **Category:** unit / documentation guard (architecture guard in spirit)
   - **Verifies:** this investigation's root-cause finding directly motivates a **new** test class not
     anticipated by the ticket's own draft AC list: assert that whichever fix-location Plan chooses is
     *discoverable* by the orchestrating agent's actual operating instructions —
     - If the fix lands as a second orchestrator-`.js` block: assert
       `.claude/skills/implement-ticket/SKILL.md` contains prose narrating it (mirroring how the
       existing Parity "Step 0" bash() calls are narrated in SKILL.md's "### Parity" section) — a
       substring/section-presence check against the SKILL.md file, matching the existing
       `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` pattern (string
       presence, not literal `.js` prompt-text assertion — no violation of the prior ticket's Anti-Drift
       guard against testing `.js` prose).
     - If the fix lands inside `done-checker`'s own agent prompt: assert
       `.claude/agents/done-checker.md` contains the new Step 0/pre-check instruction text (same
       string-presence pattern already used for the Failure Recovery Reference table row).
   - **Location:** `tests/tools/test_done_checker_static.py` (new small test, same file — no separate
     doc-test file needed for one additional assertion, consistent with the prior ticket's own reasoning
     for `test_data_runs_clean_status_appears_in_failure_recovery_reference_table`).
   - **Rationale:** this test exists specifically to prevent a repeat of this ticket's own root-cause
     failure mode — a correct Python function whose call site is invisible to the orchestrating agent's
     actual instructions. Without this guard, a future edit to SKILL.md or `done-checker.md` could
     silently drop the narration this ticket adds, reintroducing the exact defect being fixed here with
     no test catching it.

3. **Test name:** `test_data_runs_clean_status_still_appears_in_failure_recovery_reference_table`
   (extend, do not duplicate, the existing test if the row's wording changes) or leave the existing test
   untouched if `DATA_RUNS_CLEAN_FAILED`'s row text is not modified by this ticket.
   - **Category:** unit / documentation guard
   - **Verifies:** if Plan's fix changes anything about the `DATA_RUNS_CLEAN_FAILED` status's meaning
     (e.g. it can now also fire from a pre-Verify call site, not only post-Test), the Failure Recovery
     Reference table row (`docs/ai/ticket-lifecycle.md:528`) still accurately describes when it fires.
     If the status's trigger conditions are unchanged, no new test is needed here — reuse the existing
     one unmodified (Anti-Drift guard).
   - **Location:** `tests/tools/test_done_checker_static.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_done_checker_static.py -v
```

If Plan's fix touches a new sibling module instead of extending `done_checker_static.py` directly:

```
pytest tests/tools/test_done_checker_static.py tests/tools/test_<new_module>.py -v
```

Never `pytest tests/` and never a bare `pytest tests/tools/` — scope to the exact file(s) touched, per
the Testing Rule.

## Anti-Drift Test Guards

- **All 52 existing tests in `tests/tools/test_done_checker_static.py` must pass unmodified** — any diff
  to the existing `check_data_runs_clean` or `clean_data_runs_early` tests (lines 135-304) signals scope
  drift into redefining "clean," which remains explicitly Out of Scope for this ticket, same as the
  prior one.
- **`run_static_precheck`'s existing 5-check aggregation tuple must not grow to 6** — the new pre-Verify
  sweep is a separate call site, not a new DoD condition folded into the static precheck's own aggregate
  return shape (mirrors the prior ticket's identical guard for `clean_data_runs_early` itself not being
  added to `run_static_precheck`).
- **The new doc-guard test (New Test #2 above) is not optional** — it is the direct, evidence-motivated
  countermeasure to this investigation's root-cause finding (a correct function with an invisible call
  site). Skipping it would leave this ticket's own fix vulnerable to the exact same silent-non-execution
  failure mode its own investigation diagnosed.
- **No test should assert on `.claude/workflows/implement-ticket.js`'s literal prompt/code text as a
  proxy for "this executes correctly."** This investigation reconfirms and strengthens the prior
  ticket's identical guard: since the file is read and hand-transcribed by an LLM orchestrator rather
  than run by any interpreter, a pytest assertion on its source text proves only that the text exists,
  never that a live orchestrating agent will act on it. Static string-presence checks against SKILL.md /
  `done-checker.md` (New Test #2) are the closest testable proxy available and should not be oversold as
  more than that in test docstrings or PR descriptions.
- **The AC #7 "next 5 completed runs show zero Verify-phase failures citing uncleaned `data/runs/`"
  follow-up signal must be tracked at the next weekly retro** (`agent-monitoring-retro` skill) — this is
  the only mechanism that can actually confirm the fix executes in a live orchestrated run, given that no
  unit test can simulate LLM-orchestrator behavior. Do not treat this ticket as validated by green pytest
  alone; the retro follow-up is load-bearing for this specific ticket given its own root-cause finding.
