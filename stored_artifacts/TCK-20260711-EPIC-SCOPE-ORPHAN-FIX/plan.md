---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260711-EPIC-SCOPE-ORPHAN-FIX
artifact_type: plan
tags: [epic, scope, orphan, workflow]
---

# Implementation Plan — TCK-20260711-EPIC-SCOPE-ORPHAN-FIX

## Summary

The Scope phase's ticketId-provided branch of `.claude/workflows/implement-ticket.js`
unconditionally copies a `tickets/todos/**` original to `tickets/inprogress/{id}.md` before the
orchestrator knows the ticket's tier (Step 1c, current line 61). For epic-tier tickets, which
return immediately after Scope (lines 340-348) and never reach Finalize's cleanup `rm`
(lines 1039-1049), this leaves a permanent duplicate on disk. The fix moves the file-location +
tier-read + cp/rm decision out of agent-prompt text and into a deterministic, unit-testable Python
module invoked by the orchestrator via `bash()` **before** the existing `captureTs()` call — never
between it and `agent()`, which would break `test_step0_ts_orchestrator.py`'s exact literal-adjacency
assertion. A second, independent Python module provides a standalone (not pipeline-wired) repo-wide
sweep that flags the actual orphan signature — an epic-tier ticket present in both
`tickets/inprogress/` and `tickets/todos/**` simultaneously — while explicitly not flagging either
of the two legitimate dual-presence shapes already confirmed live in this repo (non-epic tickets
mid-workflow, and epic tickets resting in `tickets/inprogress/` with no todos original). Both new
Python modules live in `tools/agent-monitoring/` (decision and reasoning below), reusing
`epic_staleness_check.py`'s existing `_section_body()` Tier-parsing helper rather than
reimplementing it a third time.

## Resolved Open Questions

**1. Orchestrator-side `bash()` vs. narrower in-prompt resequencing — DECISION: orchestrator-side `bash()`.**
The ticket's Scope bullet 2 explicitly asks to relocate the cp/rm decision "out of the
ticket-scoper prompt's LLM-interpreted text and into deterministic orchestrator-side bash()." The
investigation's own re-verification (Prior Work, Risk #1) confirms the "ordering deadlock" that
would block this only applies to the create-new-ticket branch (out of scope, untouched); for the
ticketId-provided branch, `## Tier` is a static fact already on disk, locatable by the same
mechanical search Step 1a/1b/1c already performs — nothing here requires agent judgment. This also
matches the direct precedent this ticket's own Scope bullet cites
(`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` / `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`).
The narrower in-prompt-resequencing alternative was rejected: it would satisfy "move not copy"
behaviorally but leave the decision LLM-interpreted, failing the ticket's explicit architectural
ask.

**2. New module placement: `tools/gate_checks/` vs. `tools/agent-monitoring/` — DECISION: `tools/agent-monitoring/`, for both new modules.**
Reasoning:
- Neither new module is ticket_id/run_id-gated the way every existing `gate_checks/` module is
  called (`run_static_precheck(ticket_id, tier, ts)`, `run_finalize_selfcheck(ticket_id, tier)`,
  `check_workflow_meta_conformance(run_id, ...)`). The orphan-detection sweep specifically has no
  run_id/ticket_id input at all — it is a pure repo-wide sweep, structurally identical in shape to
  `epic_staleness_check.py` (also a parameterless, advisory, repo-wide sweep over
  `tickets/inprogress/*.md` filtered by `## Tier`), not to any `gate_checks/` module.
- The ticket's own wording ("mirroring `done_checker_static.py`'s `check_ticket_location`'s
  `(status, evidence)` tuple shape") is a shape reference, not a file-location mandate — the
  investigation confirms this distinction explicitly (Risk #4).
- Practically, `tools/agent-monitoring/epic_staleness_check.py` already has the exact `## Tier`
  section-parsing helper (`_section_body(text, "Tier")`, lines ~86-97) both new modules need.
  Reusing it in place (same directory, flat import, no `sys.path` gymnastics beyond what
  `test_epic_staleness_check.py` already does) avoids inventing a new cross-package import path.
  Existing precedent (`workflow_meta_conformance.py`, a `gate_checks/` module) already imports
  *from* `tools/agent-monitoring/` (its `vocabulary` module) via `sys.path` insertion — there is no
  precedent, and no need to invent one, for the reverse direction.
- Both new modules therefore follow `epic_staleness_check.py`'s own test-import convention exactly:
  `sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"))`
  then a flat `from <module> import <fn>` (no dotted package path — `agent-monitoring` has a
  hyphen and cannot be a valid Python package segment).

This supersedes test_plan.md's tentative placement guess (`tools/gate_checks/epic_scope_orphan_check.py`,
explicitly marked "pending the placement decision" there) — the test file *names* in test_plan.md
are unchanged, only the import path and the module's directory differ from that guess.

## Steps

### Step 1 — Build `resolve_and_relocate_ticket()` as a standalone, testable Python module
**Files:** `tools/agent-monitoring/scope_ticket_relocate.py` (new)

**Change:** Add a module with:
```python
def resolve_and_relocate_ticket(
    ticket_id: str,
    inprogress_dir: Path = Path("tickets/inprogress"),
    todos_dir: Path = Path("tickets/todos"),
    done_dir: Path = Path("tickets/done"),
) -> dict:
    ...
```
Logic, mirroring the current agent-prompt Step 1a/1b/1c search order exactly:
1. If `inprogress_dir/{ticket_id}.md` exists: return
   `{"ticket_path": <that path>, "tier": <parsed via _section_body>, "todos_source_path": "", "action": "already_in_inprogress"}`.
2. Else if `done_dir/{ticket_id}.md` exists: same shape, `"action": "already_in_done"`.
3. Else glob `todos_dir.rglob(f"{ticket_id}.md")`. If no match: return
   `{"ticket_path": "", "tier": "", "todos_source_path": "", "action": "not_found"}`.
4. Else (found under todos): read the file, parse tier via
   `_section_body(text, "Tier").strip().lower()` (import this exact helper from
   `epic_staleness_check.py` — do not reimplement the regex/section-scan a third time; default to
   `"standard"` if the parsed value is empty, matching the current agent-prompt Step 2's stated
   default). Copy the file to `inprogress_dir/{ticket_id}.md` (`inprogress_dir` created if
   missing). If tier == `"epic"`: also delete the todos original (`unlink()`) — this is the move.
   If tier != `"epic"`: leave the todos original in place (copy-only — preserves existing
   Finalize-reconciliation behavior for hotfix/standard). Return
   `{"ticket_path": str(inprogress_dir/{ticket_id}.md), "tier": tier, "todos_source_path": str(<original todos path>), "action": "moved_from_todos" | "copied_from_todos"}`.

Add a `MARKER:`-prefixed CLI entrypoint identical in shape to `workflow_meta_conformance.py`'s:
`if __name__ == "__main__": print("MARKER:" + json.dumps(resolve_and_relocate_ticket(sys.argv[1])))`.

**Do NOT touch:** `.claude/workflows/implement-ticket.js` in this step — this step is pure Python,
independently testable with a `tmp_path` fixture before any JS wiring exists.

**Verify:**
- `test_epic_tier_move_deletes_todos_original` (test_plan.md item 2) — synthetic `tickets/todos/{folder}/TCK-*.md`
  fixture with `## Tier` = `epic`; assert exactly one on-disk copy after the call, in
  `inprogress_dir`, todos original gone.
- `test_standard_hotfix_tier_still_copy_only` (test_plan.md item 3) — same fixture shape,
  `## Tier` = `standard`/`hotfix`; assert todos original still present.
Both live in new file `tests/tools/test_scope_orphan_fix.py`, importing
`resolve_and_relocate_ticket` via the `sys.path.insert(..., "tools/agent-monitoring")` +
flat-import convention (mirrors `test_epic_staleness_check.py`).

### Step 2 — Wire the new module into `implement-ticket.js`'s orchestrator, before `captureTs()`
**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Add a new helper `const resolveScopeTicketLocation = async (id) => { ... }` (place it
alongside the other orchestrator helpers, near `captureTs`/`writeSidecar`, ~line 189 — the file's
established style already defines helpers used earlier in execution order at this location, e.g.
`captureTs` itself is defined at line 189 but called at line 52). The helper runs:
`await bash('python3 tools/agent-monitoring/scope_ticket_relocate.py "${id}" 2>/dev/null')`,
finds the line starting with `MARKER:`, and `JSON.parse`s the remainder (same parse convention as
every other `MARKER:`-prefixed script call in this file).

Then, at the exact current site of line 52, insert **one new line immediately before it**:
```js
const scopeOrphanInfo = ticketId ? await resolveScopeTicketLocation(ticketId) : null

const scopeTs = await captureTs()
const ticketInfo = await agent(
```
The critical placement constraint: `scopeOrphanInfo`'s capture must be its own statement **before**
`const scopeTs = await captureTs()` — never inserted between `captureTs()` and `agent(`. This
leaves the literal string `"const scopeTs = await captureTs()\nconst ticketInfo = await agent("`
byte-for-byte intact and adjacent, which is exactly what
`tests/tools/test_step0_ts_orchestrator.py:31`'s `_IMPLEMENT_TICKET_ADJACENCY[0]` asserts.

**Do NOT touch:**
- Anything between `const ticketInfo = await agent(` and `{ label: 'scope',` (the object-literal
  call-options argument a few lines below the prompt string) — `test_current_run_sidecar_orchestrator.py::test_scope_phase_call_site_has_no_preceding_sidecar_write`
  asserts no `writeSidecar(` call in that exact span. This step's insertion point (before
  `captureTs()`) is naturally outside that span; do not move it later "for tidiness."
- The request-mode (`ticketId` falsy) branch (lines 88-132) — `scopeOrphanInfo` is `null` for that
  branch and nothing about it changes.
- `TICKET_SCHEMA` (lines 31-50) — no field additions/removals needed; `tier`, `ticket_path`
  (implicit via `ticket_path` prose), and `todos_source_path` already exist in the schema.

**Verify:**
- New test `test_step1c_orphan_bash_precedes_capturets` (test_plan.md item 1) in
  `tests/tools/test_scope_orphan_fix.py` — asserts the new `resolveScopeTicketLocation(...)` call
  site appears in the source text strictly before `const scopeTs = await captureTs()`, and that the
  exact adjacency substring `"const scopeTs = await captureTs()\nconst ticketInfo = await agent("`
  is still present unbroken.
- Unmodified pass of `tests/tools/test_step0_ts_orchestrator.py::test_ts_capture_bash_precedes_each_covered_agent_call`
  and `tests/tools/test_current_run_sidecar_orchestrator.py::test_scope_phase_call_site_has_no_preceding_sidecar_write` /
  `test_writeMonitoring_call_has_no_preceding_sidecar_write`.

### Step 3 — Rewrite the ticketId-branch prompt text to state pre-computed facts, not derive them
**Files:** `.claude/workflows/implement-ticket.js` (same prompt string, current lines ~55-87)

**Change:** Replace the current Step 1 (a/b/c file-location + unconditional copy) and Step 2
(read-file + extract `## Tier`) prose with text that states the orchestrator-resolved values as
already-known facts, using `scopeOrphanInfo` (from Step 2) interpolated directly into the template
literal:
```
The ticket file has already been located (and relocated from tickets/todos/ if it originated
there) by the orchestrator:
  ticket_path = "${scopeOrphanInfo.ticketPath}"
  tier = "${scopeOrphanInfo.tier}"
  todos_source_path = "${scopeOrphanInfo.todosSourcePath}"
Read the file at ticket_path directly — do not re-locate, re-copy, or move it; that has already
been done.
```
Update the branch's Return contract line to use these stated values verbatim
(`tier=(the tier value stated above)`, `todos_source_path=(the todos_source_path value stated
above)`) instead of the current "value from ticket or 'standard'" / "the tickets/todos/... path if
found in step 1c" framing, which implied the agent still had to derive them.

**Do NOT touch:** Steps 3/3a/3b (tag→skill mapping table, tags echo, mistag-warning check) —
these remain genuinely agent-interpreted and unaffected; do not consolidate them into
orchestrator-side logic as part of this ticket (that is explicitly out of scope, called out in
`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`'s own Out of Scope section).

**Verify:** `test_ticket_scoper_prompt_no_longer_unconditionally_copies` (test_plan.md item 4) —
confirms the literal unconditional instruction `Copy it to tickets/inprogress/${ticketId}.md so it
enters the standard workflow location` no longer appears in the ticketId-branch prompt text, and
that `tier`/`todos_source_path` are now stated as pre-computed facts (interpolated values) rather
than "extract"/"if found" derivation language.

### Step 4 — Build the standalone orphan-detection sweep
**Files:** `tools/agent-monitoring/epic_scope_orphan_check.py` (new)

**Change:** Add:
```python
def check_single_epic_orphan(
    ticket_id: str,
    inprogress_path: Path,
    todos_dir: Path = Path("tickets/todos"),
) -> tuple[str, str]:
```
`(status, evidence)` shape mirroring `check_ticket_location` — `"FAIL"` if a
`tickets/todos/**/{ticket_id}.md` original exists while `inprogress_path` holds an epic-tier copy
of the same `ticket_id`; `"PASS"` otherwise, with evidence naming both paths on FAIL.

```python
def scan_epic_scope_orphans(
    inprogress_dir: Path = Path("tickets/inprogress"),
    todos_dir: Path = Path("tickets/todos"),
) -> list[dict]:
```
Aggregate function (mirrors `workflow_meta_conformance.py`'s one-function/list-of-dicts shape):
scans `inprogress_dir/*.md`, filters to `## Tier` == `epic` (reuse `_section_body` from
`epic_staleness_check.py`, do not reimplement), and for each, calls `check_single_epic_orphan`.
Returns one `{"ticket_id": ..., "status": "FAIL"/"PASS", "evidence": ...}` dict per epic-tier file
found in `inprogress_dir` — non-epic tickets in `inprogress_dir` are not included in the result at
all (they are never candidates, per the orphan signature being epic-tier-specific).

`MARKER:`-prefixed CLI entrypoint, no `run_id` argument (this is a parameterless repo-wide sweep,
unlike `workflow_meta_conformance.py`'s `run_id`-scoped one):
`if __name__ == "__main__": print("MARKER:" + json.dumps(scan_epic_scope_orphans()))`.

Not wired into any workflow phase or `done_checker_static.py` aggregate — matches the ticket's own
scope (a standalone check) and the `workflow_meta_conformance.py` precedent (ships checker + tests
only, ready for a future ticket to wire in).

**Do NOT touch:** `done_checker_static.py`'s `check_ticket_location`, `check_ticket_finalized`, or
`run_finalize_selfcheck` — no signature change, no new call site added inside any of them.

**Verify:**
- `test_new_orphan_check_flags_dual_presence` (test_plan.md item 5)
- `test_new_orphan_check_passes_when_todos_original_absent` (item 6)
- `test_new_orphan_check_does_not_flag_legitimate_epic_resting_in_inprogress` (item 7)
- `test_new_orphan_check_ignores_non_epic_dual_presence` (item 8)
- `test_check_ticket_location_and_finalized_signatures_unchanged` (item 10)
All live in new file `tests/tools/test_epic_scope_orphan_check.py`, using the same
`sys.path.insert(..., "tools/agent-monitoring")` + flat-import convention as Step 1's tests.

### Step 5 — Verify AC #4 against the live repo
**Files:** `tests/tools/test_epic_scope_orphan_check.py` (same file as Step 4)

**Change:** Add `test_live_repo_orphan_check_returns_zero_findings` (test_plan.md item 9) — calls
`scan_epic_scope_orphans()` with default (real) directory args, no fixture, asserts zero
`"FAIL"` entries. Run it manually once after Steps 1-4 land to confirm the live repo (which the
investigation already confirmed has zero live orphans as of this session) still reports zero after
the fix — this is the literal AC #4 check, distinct from the synthetic-fixture tests in Step 4.

**Do NOT touch:** Do not delete or alter any live ticket file to "make the test pass" — if this
test fails, that means a real orphan exists and must be investigated as a separate finding, not
silently special-cased in the check's logic.

**Verify:** `test_live_repo_orphan_check_returns_zero_findings` passes.

### Step 6 — Full scoped regression pass and ticket bookkeeping
**Files:** none (verification only), plus ticket file `tickets/inprogress/TCK-20260711-EPIC-SCOPE-ORPHAN-FIX.md`
(Implementation Notes / Test Summary / Files Changed sections)

**Change:** Run the post-implementation scoped pytest command from test_plan.md:
```
pytest tests/tools/test_step0_ts_orchestrator.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_done_checker_static.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_epic_staleness_check.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_scope_orphan_fix.py tests/tools/test_epic_scope_orphan_check.py -v
```
All must pass. Fill in the ticket's Implementation Notes (what changed), Test Summary (which tests
were added/run), and Files Changed sections.

**Do NOT touch:** Do not run the unscoped `pytest tests/` — CLAUDE.md's Testing Rule explicitly
forbids it.

**Verify:** All listed test files green; zero regressions in the pre-existing files in that list.

## Scope Guards

- Do not touch the create-new-ticket (request-mode) branch of `implement-ticket.js`, lines 88-132.
- Do not change `TICKET_SCHEMA`'s required fields or types.
- Do not insert any statement between `const ticketInfo = await agent(` and `{ label: 'scope',`.
- Do not modify `check_ticket_location`, `check_ticket_finalized`, or `run_finalize_selfcheck`'s
  signatures or return shapes in `tools/gate_checks/done_checker_static.py`.
- Do not remove, weaken, or duplicate Finalize's `rm "${ticketInfo.todos_source_path}"` step
  (lines 1039-1049) — it remains the sole cleanup path for hotfix/standard tiers; this ticket's
  epic-tier move logic is additive/parallel, not a replacement.
- Do not touch Steps 3/3a/3b of the ticketId-branch prompt (tag→skill mapping, tags echo, mistag
  warning).
- Do not fold `epic_staleness_check.py::discover_candidate_epics()`'s double-discovery dedupe fix
  into this ticket — that is `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK`'s scope, a distinct file
  with its own test file.
- Do not wire the new `epic_scope_orphan_check.py` sweep into any workflow phase or into
  `done_checker_static.py`'s aggregates — it ships standalone, per the `workflow_meta_conformance.py`
  precedent this ticket explicitly mirrors.
- Do not run unscoped `pytest tests/`.

## Dependency Map

- Step 1 (relocate module) — independent, no dependencies.
- Step 2 (JS wiring) — depends on Step 1 (calls the module built there).
- Step 3 (prompt text rewrite) — depends on Step 2 (`scopeOrphanInfo` variable must exist first).
- Step 4 (orphan sweep module) — independent of Steps 1-3 (separate module, separate concern); may
  be built in parallel with Steps 1-3 if convenient, but is sequenced after here for narrative
  clarity.
- Step 5 (live-repo AC #4 check) — depends on Step 4 (needs the sweep built) and logically follows
  Steps 1-3 (verifies the state "post-fix," even though zero live orphans exist today regardless).
- Step 6 (regression pass + bookkeeping) — depends on all of Steps 1-5 being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — exactly one on-disk copy after epic Scope, never both simultaneously | Steps 1, 2, 3 | `test_epic_tier_move_deletes_todos_original`, `test_step1c_orphan_bash_precedes_capturets`, `test_ticket_scoper_prompt_no_longer_unconditionally_copies` |
| AC2 — hotfix/standard tier unaffected, existing coverage passes | Step 1 (copy-only branch), Step 6 (regression pass) | `test_standard_hotfix_tier_still_copy_only`; unmodified `test_step0_ts_orchestrator.py`, `test_current_run_sidecar_orchestrator.py`, `test_done_checker_static.py`, `test_epic_staleness_check.py` |
| AC3 — new static check flags dual presence, not mere epic-resting-in-inprogress | Step 4 | `test_new_orphan_check_flags_dual_presence`, `test_new_orphan_check_passes_when_todos_original_absent`, `test_new_orphan_check_does_not_flag_legitimate_epic_resting_in_inprogress`, `test_new_orphan_check_ignores_non_epic_dual_presence` |
| AC4 — running the new check against the live repo post-fix returns zero orphans | Step 5 | `test_live_repo_orphan_check_returns_zero_findings` |

## Anti-Drift Notes

- **Highest risk in this ticket:** placing the new `bash()` call in the wrong spot relative to
  `captureTs()`. It must go before `const scopeTs = await captureTs()`, never between it and
  `const ticketInfo = await agent(`. Getting this wrong silently breaks
  `test_step0_ts_orchestrator.py::test_ts_capture_bash_precedes_each_covered_agent_call`, a
  pre-existing, unrelated-looking passing test. Step 2's Verify section and Step 6's regression
  pass both re-check this.
- The distinction between "epic ticket legitimately resting in `tickets/inprogress/`" (normal,
  documented at `docs/ai/ticket-lifecycle.md:440`) and "epic ticket with a surviving todos
  original" (the actual orphan bug) must never collapse into a single "is it in inprogress/" check
  — Step 4's `check_single_epic_orphan` must always cross-reference `tickets/todos/**`, never flag
  on inprogress-presence alone.
- Two live tickets (`TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`, and this ticket itself) currently
  sit in legitimate standard-tier dual presence (todos original + inprogress copy, pending
  Finalize). The new sweep must not flag either — `test_new_orphan_check_ignores_non_epic_dual_presence`
  is the direct tripwire; do not let tier-blind logic creep into `scan_epic_scope_orphans`.
- Reuse `epic_staleness_check.py`'s `_section_body()` for `## Tier` parsing in both new modules —
  do not write a third independent regex for this; that already happened once
  (agent-prompt Step 2's own ad hoc extraction) and this ticket is explicitly replacing that
  instance, not adding a fourth parser.
- Sweep logic must be verified with a synthetic fixture (Step 4), not just the live-repo check
  (Step 5) — the live repo currently has zero orphans, so a live-only test would pass trivially
  even with badly broken detection logic.

## Deviations

- **Step 3's illustrative pseudocode used camelCase field names** (`scopeOrphanInfo.ticketPath`,
  `.todosSourcePath`) for the interpolated facts. The implementation uses snake_case
  (`scopeOrphanInfo.ticket_path`, `.tier`, `.todos_source_path`) instead — this matches
  `resolve_and_relocate_ticket()`'s actual Python dict keys 1:1 (no translation layer needed) and
  is consistent with this same file's existing convention for JSON-derived fields
  (`ticketInfo.ticket_path`, `ticketInfo.todos_source_path`, `ticketInfo.tier` are already
  snake_case throughout `implement-ticket.js`). Purely a naming choice; no behavioral difference.
- **Step numbering in the rewritten ticketId-branch prompt jumps from "Step 1" to "Step 3"** (no
  "Step 2"). The old "Step 2" (read-file-and-extract-tier) is fully eliminated now that tier is a
  stated fact, and the scope guard forbids renumbering "Step 3/3a/3b" (tag→skill mapping,
  unaffected) — so the gap is the correct outcome of honoring both constraints simultaneously
  rather than an oversight.
- **Added three extra tests beyond test_plan.md's enumerated list**, all in
  `tests/tools/test_scope_orphan_fix.py`: `test_already_in_inprogress_is_not_touched`,
  `test_already_in_done_is_not_touched`, `test_not_found_returns_empty_fields`. These cover
  `resolve_and_relocate_ticket()`'s other two discovery branches (Step 1a/1b hits, and the
  no-match case) directly at the unit level — not called out as separate test_plan.md items, but
  needed for full branch coverage of the module built in Step 1 and do not contradict or replace
  any planned test.
