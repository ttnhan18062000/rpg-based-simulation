---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260709-REGISTRY-REGEN-ON-CLOSE
artifact_type: plan
tags: [observability, testing]
---

# Implementation Plan — TCK-20260709-REGISTRY-REGEN-ON-CLOSE

## Summary

Registry regeneration currently only happens via manual `make docs-registry`, so `docs/REGISTRY.yaml`
drifts every time a ticket closes without someone remembering to run it by hand (confirmed drift:
3 recently-closed tickets missing from the checked-in registry). This plan wires regeneration into
the existing post-Finalize self-check machinery rather than adding a new invocation site: a new
function, `check_registry_entry_regenerated`, is added to `tools/gate_checks/done_checker_static.py`
as a 4th condition of `run_finalize_selfcheck`. That function (a) regenerates `docs/REGISTRY.yaml` by
calling `generate_registry()` directly, tolerating a nonzero return non-fatally, then (b) checks the
freshly-written file for an entry matching the closing `ticket_id`, returning FAIL only on a missing
entry. Because `run_finalize_selfcheck` is already invoked unconditionally for every tier (including
hotfix) from the existing `finalizeCheckOutput` `bash()` call in `implement-ticket.js` — which runs
*after* the Finalize `agent()` call has moved the ticket to `tickets/done/` and migrated
`stored_artifacts/` — no new `bash()` call, no new invocation site, and no new blocking status are
needed: the existing generic "any FAIL → `FINALIZE_INCOMPLETE`" logic in `implement-ticket.js`
(lines 1108–1118) already handles the new condition's failure the same way it handles the other 3.
This resolves the plan's two open design questions by precedent-match: the tool's own nonzero exit
is absorbed non-fatally inside the new function (mirroring the "write never fails" shape), while the
entry-presence check is folded into the existing *blocking* `run_finalize_selfcheck` family (mirroring
that family's existing purpose — verifying the current run's own Finalize work actually landed —
rather than the separate non-blocking `check_monitoring_write_recorded` pattern, which exists only
because of a monitoring-specific Hard Rule that has no registry equivalent). CLAUDE.md's "After Work"
section gets a documentation-only update; `generate_registry.py` itself is not touched.

## Steps

### Step 1 — Add `check_registry_entry_regenerated` to `done_checker_static.py`
**Files:** `tools/gate_checks/done_checker_static.py`

**Change:** Add a new module-level function, placed near the other `check_*` functions (after
`check_monitoring_write_recorded`, before `run_finalize_selfcheck`, around line 402):

```python
def check_registry_entry_regenerated(
    ticket_id: str,
    root: Path = Path("."),
    registry_output: Path = Path("docs/REGISTRY.yaml"),
) -> tuple[str, str]:
```

Behavior:
1. Resolve `registry_output` relative to `root` if not absolute — reuse the exact same
   resolution snippet `generate_registry.py`'s own `main()` uses (lines 462–465), do not
   duplicate/modify `generate_registry.py` itself.
2. Import `generate_registry` from the sibling module the same way this file already imports
   `validate_file`/`validate_directory` from `validate_frontmatter` (lines 32–36: `_TOOLS_DIR`
   is already on `sys.path`), i.e. `from generate_registry import generate_registry  # noqa: E402`
   at the top of the file, alongside the existing `validate_frontmatter` import.
3. Call `exit_code = generate_registry(root, registry_output)` inside a `try/except Exception`
   block. Never let a raised exception propagate — on exception, treat it the same as a nonzero
   exit (capture the exception text into a local `regen_note` string) and continue to step 4;
   this is the non-fatal "write never fails" handling for AC #2. Do NOT branch on `exit_code`
   to decide PASS/FAIL — only note it for the evidence string if nonzero.
4. Read `registry_output` (YAML) and check whether any entry has `ticket_id == ticket_id`
   (tickets are the entries with `type: ticket` in `generate_registry.py`'s schema — reuse
   `yaml.safe_load`, do not hand-roll parsing).
5. If found: return `("PASS", f"{registry_output} contains an entry for {ticket_id}" +
   (f" (note: regen exited nonzero: {regen_note})" if regen_note else ""))`.
6. If not found: return `("FAIL", f"{registry_output} has no entry for {ticket_id} after
   regeneration" + (f" (regen also exited nonzero: {regen_note})" if regen_note else ""))`.

Deliberately **no `tier` parameter** — same design choice as `check_monitoring_write_recorded`
(line 372–387): AC #1 requires this to run "on every ticket close, all tiers including hotfix,"
so the absence of a tier-skip branch is itself the mechanism, not an oversight. Add a docstring
on the new function explaining this, mirroring `check_monitoring_write_recorded`'s docstring style
and explicitly citing this ticket ID.

**Do NOT touch:** `generate_registry.py`, `_SKIP_DOC_SUBDIRS`, `collect_docs`, `collect_tickets`,
`sort_entries`, or any other `generate_registry.py` internals (ticket Out of Scope). Do not add a
`--check` CLI flag anywhere (that is `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`'s scope).

**Verify:** New unit tests from Step 5 covering: nonzero-tool-exit-does-not-raise/does-not-FAIL
(AC #2), entry-present-passes (AC #3), entry-missing-fails naming the ticket_id (AC #3),
no-tier-skip-under-hotfix (AC #1).

---

### Step 2 — Fold as a 4th condition into `run_finalize_selfcheck`
**Files:** `tools/gate_checks/done_checker_static.py`

**Change:** In `run_finalize_selfcheck` (lines 404–414), add a 4th entry to the `checks` tuple:

```python
("registry_entry_regenerated", check_registry_entry_regenerated(ticket_id)),
```

Update the function's docstring (line 405, currently `"""Aggregate all 3 Part B checks. Same
return shape as run_static_precheck."""`) to say "4 Part B checks". Also update the module-level
docstring at the top of the file (lines 13–17, "Part B (`run_finalize_selfcheck`): the 3
post-Finalize conditions...") to say "4 post-Finalize conditions" and add one clause naming the
new condition (regenerates `docs/REGISTRY.yaml` and confirms the closing ticket's entry landed).

Because Python evaluates all elements of a tuple literal eagerly, `check_registry_entry_regenerated`
executes (and therefore regenerates `docs/REGISTRY.yaml`) every time `run_finalize_selfcheck` is
called, regardless of whether the other 3 conditions pass or fail — this is what makes the regen
"unconditional" per AC #1 without needing a separate call site.

**Do NOT touch:** `run_static_precheck` (Part A, pre-Finalize, a different function entirely) — the
new condition is inherently post-Finalize (the registry entry cannot exist until the ticket is
in `tickets/done/`), so it belongs only in Part B.

**Verify:** `test_run_finalize_selfcheck_all_pass` (updated in Step 5) asserts `len(results) == 4`
and all four `PASS`.

---

### Step 3 — Document the side effect at the existing `finalizeCheckOutput` call site
**Files:** `.claude/workflows/implement-ticket.js`

**Change:** No new `bash()` call, no new branching logic. The existing `finalizeCheckOutput`
`bash()` call (lines 1072–1080) already invokes `run_finalize_selfcheck(sys.argv[1], sys.argv[2])`
and already prints `FINALIZE_CHECK_JSON:` + the results array; the existing generic failure
handling (lines 1108–1118: `finalizeResults.filter(r => r.status === 'FAIL')` →
`FINALIZE_INCOMPLETE`) already treats any FAIL condition identically, so a FAIL on the new
`registry_entry_regenerated` condition automatically produces `FINALIZE_INCOMPLETE` with that
condition's evidence text in `failing_items`, with zero code changes required to that block. This
is the direct consequence of Question 2's resolution: reuse the existing `python3 -c "..."` +
`MARKER:json` call site rather than adding a parallel one, since the check now lives inside the
function that call site already invokes.

Update only the comment block immediately above the call (lines 1069–1071, "Post-Finalize
migration self-check — confirms the agent's own migration work above actually landed...") to add
one sentence noting that, as of this ticket, the same call also regenerates `docs/REGISTRY.yaml`
as a side effect and verifies the closing ticket's entry landed — so a future reader is not
surprised that a "self-check" bash call mutates a tracked file.

**Do NOT touch:** the Finalize `agent()` prompt's numbered step list (lines 1022–1066) — the
registry file does not exist in its regenerated form until *after* the agent() call returns (the
`bash()` checkpoint runs afterward), so a `git add docs/REGISTRY.yaml` step cannot be placed inside
the agent's own step list without acting on a stale/pre-regen file. Do not add a step there. Do not
touch the JSON-marker parsing/guard logic (lines 1082–1106) or the failure-branching logic
(lines 1108–1118) — both are already generic over the conditions array and require no edits.
Do not touch `monitoringCheckOutput`/`check_monitoring_write_recorded` (lines 1123–1151) — that
is a separate, deliberately non-blocking check governed by a different Hard Rule; this ticket does
not change it.

**Verify:** No new pytest coverage possible for this file (confirmed in test_plan.md — no JS test
harness exists in this repo). Verified by: (a) Step 1/2's Python unit tests proving
`run_finalize_selfcheck` now returns 4 conditions and that a FAIL on the new one is shaped exactly
like the other 3 (same `{"condition", "status", "evidence"}` dict), which is what the JS
generically consumes; (b) a manual reasoning trace during Verify/Architecture-Verify confirming the
call site and ordering are unchanged.

---

### Step 4 — Document the trigger in CLAUDE.md's "After Work" section
**Files:** `CLAUDE.md`

**Change:** In the "After Work" section, add one new bullet (placed near the existing "Always
stage `agent-monitoring/` (including `tools.jsonl`) in every commit" bullet, since it is the
closest existing precedent for an unconditional, every-tier auto-behavior documented in prose):

> `docs/REGISTRY.yaml` is regenerated unconditionally as part of Finalize's post-migration
> self-check (all tiers, including hotfix) — no manual `make docs-registry` step is needed.
> Always stage the regenerated file (`git add docs/REGISTRY.yaml`) as part of ticket close,
> alongside `agent-monitoring/`.

Keep this purely descriptive of what the code now does (per Step 1–3) — do not introduce any new
behavioral rule in CLAUDE.md that isn't backed by the code change.

**Do NOT touch:** the `make knowledge-index-update` bullet (conditional on `docs/` changes) — that
is a separate, unrelated trigger and must not be merged with or reworded to cover this one. Do not
alter any other section of CLAUDE.md.

**Verify:** AC #4's own required test, `test_claude_md_documents_registry_regen_trigger` (Step 5),
asserting both the unconditional-regen sentence and the `git add docs/REGISTRY.yaml` instruction
are present in `CLAUDE.md`'s text — mirrors the existing `DATA_RUNS_CLEAN_FAILED` doc-content
regression guard precedent (`test_data_runs_clean_status_appears_in_failure_recovery_reference_table`).

---

### Step 5 — Tests
**Files:** `tests/tools/test_done_checker_static.py`

**Change:**
1. Import `check_registry_entry_regenerated` alongside the existing imports from
   `gate_checks.done_checker_static`.
2. Update `_scaffold_finalize_repo` (line 647) — or add a new sibling helper,
   `_scaffold_finalize_repo_with_registry`, if changing the shared helper's default behavior would
   perturb unrelated existing tests — to also write a minimal `docs/REGISTRY.yaml` (or rely on the
   new function's own regen step to produce one from a scaffolded `docs/` + `tickets/done/` tree)
   such that a ticket entry for the fixture's `ticket_id` will exist post-regen. Prefer scaffolding
   real `docs/`/`tickets/done/{ticket_id}.md` content (same fixture shape
   `tests/tools/test_generate_registry.py` already uses) over hand-writing a fake
   `docs/REGISTRY.yaml`, since the new function performs an actual regen, not just a read.
3. Update `test_run_finalize_selfcheck_all_pass` (line 659): change `assert len(results) == 4` and
   confirm the `registry_entry_regenerated` condition is `PASS`.
4. Add `test_run_finalize_selfcheck_surfaces_missing_registry_entry` (mirrors
   `test_run_finalize_selfcheck_surfaces_incomplete_stored_artifacts`, line 668): scaffold a repo
   where the ticket's `docs/`/`tickets/done/` content is such that regen will not produce an entry
   for it (e.g. ticket file itself missing required frontmatter, or ticket still in
   `tickets/inprogress/` — see test 7 below), assert `by_condition["registry_entry_regenerated"]["status"] == "FAIL"`.
5. Add direct unit tests for `check_registry_entry_regenerated` in its own section (mirroring the
   `check_monitoring_write_recorded` section, line 702 onward):
   - `test_check_registry_entry_regenerated_passes_when_entry_present` — scaffold a `tmp_path`
     repo with a valid `tickets/done/{tid}.md` (frontmatter-valid) and no doc frontmatter errors;
     assert `PASS` and that the ticket_id appears in evidence.
   - `test_check_registry_entry_regenerated_fails_when_entry_absent` — scaffold with the ticket
     absent from `tickets/done/` entirely (or present but frontmatterless, whichever exercises
     `collect_tickets`'s existing WARNING-only-not-error path per investigation.md's Current
     Behavior — confirm which by reading `collect_tickets`, lines 239+, do not guess); assert
     `FAIL` and that the ticket_id is named in the evidence string.
   - `test_check_registry_entry_regenerated_nonzero_tool_exit_does_not_fail` — scaffold a `docs/`
     tree with one unrelated doc file missing frontmatter (same fixture shape as
     `tests/tools/test_generate_registry.py`'s `TestEdgeCases` missing-frontmatter fixture) *and* a
     valid `tickets/done/{tid}.md` for the ticket under test; assert the function still returns
     `PASS` (entry present) and does not raise, proving a repo-wide unrelated frontmatter gap does
     not turn into a false block — this directly exercises AC #2's non-blocking requirement.
   - `test_check_registry_entry_regenerated_applies_under_hotfix_tier` — mirrors
     `test_check_monitoring_write_recorded_applies_under_hotfix_tier` (line 753): documents that
     the function takes no `tier` argument, so there is no hotfix-skip branch to test around;
     assert it runs and returns a result regardless of tier context (call it directly with no tier
     argument available, same as the monitoring precedent's test shape).
   - `test_registry_entry_check_ordering_guard_fails_if_ticket_still_inprogress` — the ordering
     guard from test_plan.md item 5: scaffold a `tmp_path` repo where the ticket file is still
     under `tickets/inprogress/` (not yet moved to `tickets/done/`) when the check runs; assert
     `FAIL`, proving the check would catch a future regression where the call site is
     accidentally moved to run before the Finalize `agent()`'s move step.
6. Add `test_claude_md_documents_registry_regen_trigger` to
   `tests/tools/test_done_checker_static.py` (co-located with the existing
   `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` precedent per
   test_plan.md's guidance — check that file's location first; do not create a new
   `test_claude_md_content.py` file unless one already exists) — reads `CLAUDE.md` from repo root
   and asserts it contains both the unconditional-regen sentence and the literal string
   `git add docs/REGISTRY.yaml`.

**Do NOT touch:** `tests/tools/test_generate_registry.py` (must pass unmodified — proves
`generate_registry.py` internals were not touched), `test_run_static_precheck_*` tests (Part A is
untouched), any test asserting a specific numeric entry count in `docs/REGISTRY.yaml` (explicitly
forbidden per test_plan.md's Anti-Drift Test Guards — `TCK-20260709-REGISTRY-COUNT-STALE-DOCS`
just removed a hardcoded count for this exact reason).

**Verify:**
```
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_generate_registry.py -v --tb=short
```
All tests pass, `test_run_finalize_selfcheck_all_pass` at `len(results) == 4`.

---

### Step 6 — Parity ledger check (verification-only, likely no edit)
**Files:** `docs/parity_ledger/infrastructure.yaml` (read-only check; edit only if warranted)

**Change:** Confirm `INFRA-183`'s `text`/`v2_evidence` still accurately describe
`generate_registry.py`'s output (they do — this ticket does not change what the tool produces,
only when it's invoked). Per investigation.md's Parity Ledger Overlap section, this is a judgment
call belonging to the ticket's Parity workflow phase (the `parity-updater` agent), not a mandatory
Implementer edit. If the Parity phase agent judges a `v2_evidence` addendum noting the new
invocation site (`done_checker_static.py::check_registry_entry_regenerated`) is warranted, that
edit is in scope for that phase; if it judges no edit is needed, that is also an acceptable
outcome and must be stated explicitly (not silently skipped) in the ticket's Implementation Notes.

**Do NOT touch:** `INFRA-183`'s `status` (`verified`) or `priority` (`P2`) — this ticket doesn't
change verification status, and P2 doesn't require a passing `test_path` gate.

**Verify:** No new test required; this step is a documentation-accuracy confirmation, not a
behavior change.

## Scope Guards

- Do not modify `generate_registry.py` in any way — not `_SKIP_DOC_SUBDIRS`, not `collect_docs`,
  not `collect_tickets`, not `sort_entries`, not its CLI/`argparse` surface, not its exit-code
  semantics. This ticket only adds a new caller.
- Do not implement the `--check`/CI drift-detection flag or any `.github/workflows/` change — that
  is `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`'s explicitly separate scope.
- Do not backfill frontmatter on any currently-frontmatterless docs or tickets to make the tool's
  exit code cleaner — out of scope per the ticket; any newly-discovered gaps get logged as evidence
  in the non-fatal warning path, not fixed inline.
- Do not add a `git add docs/REGISTRY.yaml` step inside the Finalize `agent()` prompt's numbered
  step list — the file isn't in its final regenerated state until after that call returns. The
  `git add` instruction is CLAUDE.md prose only (Step 4), consistent with how the existing "stage
  agent-monitoring/" instruction is also prose-only, not code that runs `git add` automatically.
- Do not touch `run_static_precheck` (Part A) or any of its 5 existing conditions.
- Do not touch `check_monitoring_write_recorded` or its non-blocking wiring
  (`monitoringCheckOutput`, lines 1123–1151 of `implement-ticket.js`) — a structurally different
  check governed by a monitoring-specific Hard Rule with no registry equivalent.
- Do not introduce a new blocking status string (e.g. no `REGISTRY_ENTRY_MISSING`) — the new
  condition rides the existing `FINALIZE_INCOMPLETE` status, already documented generically in
  `docs/ai/ticket-lifecycle.md` line 497 ("Finalize's own migration self-check found a
  discrepancy"), which already covers this failure mode without an edit.
- Do not add a test asserting a specific numeric entry count in `docs/REGISTRY.yaml` or in any doc
  text.
- Do not modify the `Makefile`'s `docs-registry` target — it is unaffected and needs no change.

## Dependency Map

- Step 1 (new function) must land before Step 2 (wiring it into `run_finalize_selfcheck`) — Step 2
  imports the name Step 1 defines.
- Step 2 must land before Step 3's comment update makes sense (the comment describes the combined
  behavior of Steps 1+2).
- Step 3 has no code dependency on Steps 1–2 beyond needing them to exist for the comment to be
  accurate — could be written in parallel but should land after for correctness of the description.
- Step 4 (CLAUDE.md) is independent of Steps 1–3 in code terms but describes their combined effect
  — write last among the non-test steps so the prose matches the final implementation.
- Step 5 (tests) depends on Steps 1 and 2 (imports the new function and asserts on
  `run_finalize_selfcheck`'s new 4-condition shape) and on Step 4 (the `CLAUDE.md` content test).
  Write/run last.
- Step 6 is independent and can happen any time after Step 1 (needs the new function's name to
  exist for an accurate `v2_evidence` addendum, if one is added).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — regen invoked unconditionally on every ticket close, all tiers including hotfix | Step 1 (no `tier` param), Step 2 (eager tuple evaluation), Step 3 (reuses existing unconditional call site) | `test_check_registry_entry_regenerated_applies_under_hotfix_tier`, `test_run_finalize_selfcheck_all_pass` |
| AC #2 — nonzero tool exit is a non-blocking warning, never blocks ticket close | Step 1 (try/except around `generate_registry()`, status governed only by entry presence, not exit code) | `test_check_registry_entry_regenerated_nonzero_tool_exit_does_not_fail` |
| AC #3 — self-check confirms regenerated registry contains an entry for the closing ticket_id before Finalize completes | Step 1 (entry-presence check), Step 2 (blocking 4th condition in `run_finalize_selfcheck`), Step 3 (existing generic FAIL→`FINALIZE_INCOMPLETE` handling) | `test_check_registry_entry_regenerated_passes_when_entry_present`, `test_check_registry_entry_regenerated_fails_when_entry_absent`, `test_run_finalize_selfcheck_surfaces_missing_registry_entry`, `test_registry_entry_check_ordering_guard_fails_if_ticket_still_inprogress` |
| AC #4 — CLAUDE.md's "After Work" section documents the unconditional trigger and `git add docs/REGISTRY.yaml` staging | Step 4 | `test_claude_md_documents_registry_regen_trigger` |

## Anti-Drift Notes

- **Ordering is load-bearing.** `check_registry_entry_regenerated` must only ever be invoked from
  a call site that runs after the Finalize `agent()` call has moved the ticket to `tickets/done/`
  and (for standard/epic) migrated `stored_artifacts/`. `run_finalize_selfcheck` already satisfies
  this by construction (it's Part B, invoked from `finalizeCheckOutput` after the `agent()` call
  returns) — do not extract the new function into anything invoked earlier, and the ordering-guard
  test in Step 5 exists specifically to catch a future regression here.
- **The regen is a side effect of what looks like a read-only "check" function** — this is a
  deliberate, precedent-guided design (per Question 2's resolution) to avoid adding a parallel
  invocation site, but it means `check_registry_entry_regenerated`, unlike every sibling `check_*`
  function in this file, mutates a tracked file (`docs/REGISTRY.yaml`) as part of "checking." Keep
  the docstring explicit about this so a future maintainer doesn't assume it's pure.
- **Two distinct failure surfaces must not be conflated**: (a) `generate_registry()`'s own exit
  code, which can go nonzero for reasons entirely unrelated to the closing ticket (any
  frontmatter-missing doc anywhere in `docs/`) and must never by itself cause a FAIL; versus
  (b) the closing ticket's own entry being absent post-regen, which is the only thing that should
  produce FAIL. Test both paths independently (Step 5) — do not write a single test that only
  exercises the "everything fine" case and assume it covers both.
- **No new blocking status vocabulary.** The new condition's FAIL rides the existing
  `FINALIZE_INCOMPLETE` status and its existing generic handling — do not invent
  `REGISTRY_ENTRY_MISSING` or similar, and do not add a new row to
  `docs/ai/ticket-lifecycle.md`'s status table (the existing `FINALIZE_INCOMPLETE` row's generic
  wording already covers this failure mode).
- **`collect_tickets()`'s existing WARNING-vs-error split matters for fixture design in Step 5**:
  per investigation.md, `generate_registry.py` treats a ticket missing frontmatter as a stderr
  `WARNING:` only (never affects exit code), while a *doc* under `docs/` missing frontmatter is
  what actually drives the nonzero exit code. Get this distinction right when building the
  "entry absent" vs. "nonzero exit" test fixtures in Step 5 — they are not the same scenario and
  must be triggered by different fixture shapes (read `collect_tickets`/`collect_docs` in
  `generate_registry.py` to confirm exact behavior before writing the fixtures, per the plan's own
  Step 5 instruction not to guess).
- **Concurrent-session interleaving** (investigation.md Risk #5) is an accepted residual risk,
  matching the existing precedent for `clean_data_runs_early` — not something this plan attempts
  to solve.

## Deviations

- **Step 5, item 4 fixture choice.** The plan suggested two candidate fixtures for
  `test_run_finalize_selfcheck_surfaces_missing_registry_entry`: "ticket file itself missing
  required frontmatter, or ticket still in `tickets/inprogress/`." Reading `collect_tickets()`
  (per the plan's own instruction not to guess) confirmed a missing-frontmatter ticket file still
  produces a registry entry — `ticket_id` falls back to the filename stem (WARNING-only path,
  never an error, never an absent entry) — so that fixture cannot actually trigger a missing-entry
  FAIL. "Still in `tickets/inprogress/`" was reserved for the dedicated ordering-guard test
  (`test_registry_entry_check_ordering_guard_fails_if_ticket_still_inprogress`). The implemented
  test instead deletes the ticket from `tickets/done/` entirely (no ticket file present under that
  ticket_id anywhere), which does produce a genuinely absent entry and is fixture-distinct from
  the ordering-guard test.
- **Step 5, item 2 (`_scaffold_finalize_repo` update).** No change to the shared helper, and no new
  sibling helper, was needed. `_scaffold_finalize_repo`'s existing `_write_ticket(...)` call
  already writes valid ticket frontmatter (including `ticket_id`) plus `## Title`/`## Tier` body
  sections, which `collect_tickets()` parses into a full registry entry — so a real regen against
  the existing fixture already produces a matching entry with zero fixture changes. The plan
  anticipated this might be necessary; it wasn't.
- **Step 6 (parity ledger).** At Implement time the Implementer judged `INFRA-183` should stay
  unedited — it describes `generate_registry.py`'s *output shape*, untouched by this ticket — and
  made no addendum. The plan's own Step 6 explicitly left the final call to "the Parity phase if
  ambiguous." The Parity phase (parity-updater agent) subsequently ran and decided the new
  ticket-close registry-regeneration *guarantee* itself warranted its own entry — added
  `INFRA-263` to `docs/parity_ledger/infrastructure.yaml` as a companion to (not an edit of)
  `INFRA-183`, citing precedent from other dev-tooling entries in that file. Both decisions are
  correct for what each was actually evaluating (INFRA-183's own content vs. whether a new
  guarantee needed tracking) — see ticket Implementation Notes for the reconciled account.
