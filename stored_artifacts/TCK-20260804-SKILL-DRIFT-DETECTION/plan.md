---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-SKILL-DRIFT-DETECTION
artifact_type: plan
tags: [ai, workflows, skills]
---

# Implementation Plan — TCK-20260804-SKILL-DRIFT-DETECTION

## Summary

Add a new doc-drift verifier, `check_skill_doc_covers_meta_phases()`, to
`tools/gate_checks/workflow_meta_conformance.py` (reusing `extract_meta_phases()`, never
reimplementing it) that asserts every `meta.phases[i].title` from a workflow's `.js` file has a
*dedicated* mention in its corresponding `SKILL.md` — collision-safe against the confirmed
`Review`/`Security-Review` and `Verify`/`Architecture-Verify` substring-masking risk via a small
helper, `_title_has_dedicated_mention()`, that strips superstring sibling titles from a scratch
copy of the text before matching. This check ships as pytest-only (AC #3) — no pipeline wiring.
Separately, wire the existing, already-tested `check_workflow_meta_conformance()` into
`implement-ticket.js`'s Finalize tail as a third advisory-only check (matching
`check_monitoring_write_recorded`/`check_tag_drift`'s placement and non-blocking contract),
via a new generic aggregation function, `summarize_conformance_results()`, that folds the
existing `List[dict]` return shape into the `tuple[str, str]` shape the Finalize-tail call-site
pattern expects. The `Security-Review` false-positive-noise problem is resolved by filtering that
one phase out of the results *inline at the `implement-ticket.js` call site* — never inside
`workflow_meta_conformance.py` itself — preserving TCK-20260710's no-per-workflow-allowlist Scope
Guard on that module. `.claude/skills/implement-ticket/SKILL.md` and
`docs/ai/ticket-lifecycle.md`'s Finalize sections are both updated to document the new wiring;
the ticket-lifecycle.md edit also names the two pre-existing checks
(`check_monitoring_write_recorded`, `check_tag_drift`) that section never named before, since the
ticket's own Docs Requiring Update note already scopes this section in and the edit is a small,
same-paragraph accuracy fix bundled with the required update — not separate new work.

**Decisions resolved by this plan (see Anti-Drift Notes for full reasoning):**
1. Substring-collision blind spot: **closed**, not accepted — `_title_has_dedicated_mention()`
   strips sibling superstring titles before matching, so `Review` is correctly flagged FAIL if
   `Security-Review` is the only surviving mention.
2. List→tuple aggregation: new `summarize_conformance_results(results: List[dict]) ->
   tuple[str, str]` function, generic fold, no phase-specific logic.
3. Security-Review noise: **filtered at the `implement-ticket.js` call site** (inline in the
   embedded `python3 -c` block), not inside `workflow_meta_conformance.py`.
4. `implement-epic/SKILL.md` coverage: **no special-casing** — checked uniformly via the same
   1:1 `workflow_name -> SKILL.md` convention as the other two skills; it already covers its own
   3 phases per investigation.md.

## Steps

### Step 1 — Add `check_skill_doc_covers_meta_phases()` and its helpers to `workflow_meta_conformance.py`

**Files:** `tools/gate_checks/workflow_meta_conformance.py`

**Change:** Add, after the existing `resolve_workflow_source_path()` function (after L93) and
before `collect_run_event_statuses()`:

1. A new module constant: `DEFAULT_SKILLS_DIR = Path(".claude/skills")` (alongside the existing
   `DEFAULT_WORKFLOWS_DIR`/`DEFAULT_EVENTS_PATH` constants at L44-45).
2. `resolve_skill_md_path(workflow_name: Optional[str], skills_dir: Path = DEFAULT_SKILLS_DIR) ->
   Optional[Path]`: pure convention `skills_dir / workflow_name / "SKILL.md"`, `None` if
   `workflow_name is None` or the file doesn't exist — same shape as
   `resolve_workflow_source_path()`, confirmed valid 1:1 convention for all 3 in-scope workflows
   (`implement-ticket`, `create-tickets`, `implement-epic`) per investigation.md.
3. `_title_has_dedicated_mention(title: str, all_titles: List[str], text: str) -> bool`: private
   helper implementing the collision guard. For every *other* title in `all_titles` that contains
   `title` as a substring (e.g. `"Security-Review"` contains `"Review"`), strip all occurrences of
   that other title from a scratch copy of `text` via `str.replace`, then return whether `title`
   still appears in what's left. This directly implements investigation.md's suggested mechanism
   ("removing all OTHER title occurrences... still leaves at least one instance of the target
   title"), scoped to only the titles that are actual substring supersets (no need to strip
   non-colliding titles). Docstring must state explicitly why a plain substring check or
   `\btitle\b` regex is insufficient (both already disproven in investigation.md — `-` is a
   regex word-boundary character, so `\bReview\b` still matches inside `Security-Review`).
4. `check_skill_doc_covers_meta_phases(workflow_name: str, workflows_dir: Path =
   DEFAULT_WORKFLOWS_DIR, skills_dir: Path = DEFAULT_SKILLS_DIR) -> List[dict]`: the new aggregate
   entry point, mirroring `check_workflow_meta_conformance()`'s own shape (list of
   `{"phase", "status", "evidence"}` dicts, `NA`-labeled single-entry list for unresolvable
   workflow source or missing `SKILL.md`, never raises). Body: resolve the workflow `.js` path via
   the *existing* `resolve_workflow_source_path()`; resolve the `SKILL.md` path via the new
   `resolve_skill_md_path()`; call the *existing* `extract_meta_phases()` (do not reimplement
   parsing); read the `SKILL.md` text; for each declared title, call
   `_title_has_dedicated_mention(title, declared_phases, text)` — `"PASS"` if `True`, `"FAIL"`
   with evidence naming the title and both file paths if `False`.

**Do NOT touch:** `extract_meta_phases()`, `resolve_workflow_source_path()`,
`collect_run_event_statuses()`, `check_workflow_meta_conformance()`'s existing FAIL/PASS logic, or
the `if __name__ == "__main__"` block (the new doc-drift check is pytest-only per AC #3 — no CLI
entry point needed for it).

**Verify:** New tests added in Step 2; run
`pytest tests/tools/test_workflow_meta_conformance.py -v` once both steps land.

### Step 2 — Add test coverage for the new doc-drift function

**Files:** `tests/tools/test_workflow_meta_conformance.py`

**Change:** Add a new section (mirroring the file's existing `# --- ... ---` section-comment
convention), after the existing architecture-guard test (after L242), with 8 tests. Add a
`_write_skill_md(tmp_path, workflow_name, body_text)` fixture helper alongside the existing
`_write_workflow_js`/`_write_events_jsonl` helpers (writes `tmp_path / workflow_name /
"SKILL.md"`, creating the parent dir).

1. `test_skill_doc_covers_all_declared_phases_happy_path` — synthetic `["Alpha", "Beta"]` +
   body containing `**Alpha**` and `**Beta**` → all `"PASS"`.
2. `test_skill_doc_flags_missing_phase_title` — `["Alpha", "Beta", "Gamma"]` + body mentioning
   only `**Alpha**`/`**Beta**` → `"Gamma"` reported `"FAIL"` with non-empty evidence naming the
   title and the file.
3. `test_skill_doc_tolerates_bold_and_plain_wrapping` — title present as plain unwrapped text
   (no `**`) still counts as `"PASS"` — encodes investigation.md's confirmed finding.
4. `test_skill_doc_flags_missing_title_masked_by_sibling_superstring_title` (the collision test —
   **implements the "guard closes the gap" design chosen above, not the `xfail`/accepted-blind-
   spot alternative test_plan.md left open**): `meta.phases = ["Review", "Security-Review"]`, body
   text containing only `**Security-Review**` (the standalone `**Review**` heading deleted,
   reproducing the exact future-edit risk investigation.md flagged). Assert `"Review"` is reported
   `"FAIL"` and `"Security-Review"` is reported `"PASS"` — proves `_title_has_dedicated_mention()`
   is not fooled by the substring collision. This is a real, non-`xfail` assertion because Step 1
   deliberately closes this blind spot rather than accepting it.
5. `test_check_covers_real_implement_ticket_skill_md` — real
   `.claude/workflows/implement-ticket.js` + real `.claude/skills/implement-ticket/SKILL.md` →
   zero `"FAIL"` findings across all 12 real phase titles, including the real `Review`/
   `Security-Review` and `Verify`/`Architecture-Verify` pairs (this is the real-file proof that
   the collision guard does not false-flag the two titles that legitimately both have their own
   headings today). Satisfies AC #6 (implement-ticket half).
6. `test_check_covers_real_create_tickets_skill_md` — real `create-tickets.js` +
   `create-tickets/SKILL.md` → zero `"FAIL"` findings. Satisfies AC #6 (create-tickets half).
7. `test_check_covers_real_implement_epic_skill_md` — real `implement-epic.js` +
   `implement-epic/SKILL.md` → zero `"FAIL"` findings against `implement-epic.js`'s own 3 phases
   only (`Discover, Implement, Report`). Must NOT assert anything about `implement-ticket.js`'s 12
   titles appearing in `implement-epic/SKILL.md` — per investigation.md Risk #3 and Decision 4
   above, the 1:1 pairing is intentional; that file legitimately delegates by reference.
8. `test_new_function_reuses_extract_meta_phases_not_a_reimplementation` — architecture guard,
   mirrors `test_reuses_vocabulary_infer_workflow_not_a_reimplementation`'s pattern: source-inspect
   `workflow_meta_conformance.py` and assert `check_skill_doc_covers_meta_phases`'s own source (or
   the module source generally) does not contain a second `phases:\s*\[` / `title:\s*'` regex
   literal outside `extract_meta_phases()` itself — i.e. no forked re-parsing.

**Do NOT touch:** Any of the existing 15 tests in this file, including the
`@pytest.mark.xfail(strict=True)` `test_does_not_flag_security_review_absent_when_ticket_untagged_security`
test — it must remain `xfail` (it guards a different, still-unresolved gap in
`check_workflow_meta_conformance()` itself, not the new doc-drift function).

**Verify:** `pytest tests/tools/test_workflow_meta_conformance.py -v` — all new tests pass, all 15
pre-existing tests still pass unchanged, `xfail` count unchanged (still exactly 1).

### Step 3 — Add `summarize_conformance_results()` aggregation function

**Files:** `tools/gate_checks/workflow_meta_conformance.py`

**Change:** Add, after `check_workflow_meta_conformance()` (after L161) and before the
`if __name__ == "__main__"` block:

```
def summarize_conformance_results(results: List[dict]) -> tuple[str, str]:
```

A generic fold from this module's own `List[dict]` shape into the `tuple[str, str]` shape
`check_monitoring_write_recorded`/`check_tag_drift` already return at the Finalize-tail call site
(`implement-ticket.js:1502-1548`). Logic:
- If `results` is a single-entry `NA`-labeled list (the `check_workflow_meta_conformance`
  unresolvable-workflow/unknown-run_id convention), return `("NA", <that entry's evidence>)`.
- Else, collect entries with `status == "FAIL"`. If none, return `("PASS", "<N> declared phase(s)
  checked, 0 FAIL")`. If any, return `("FAIL", "; ".join(f"{phase}: {evidence}" for each failing
  entry))`.

Docstring must state explicitly (mirroring `check_tag_drift`'s own docstring convention) that this
function carries **no per-phase allowlist or suppression logic** — any phase-specific filtering
(e.g. excluding `Security-Review`) is the caller's responsibility, applied to `results` *before*
calling this function, so this module stays free of the per-workflow conditional-phase
special-casing `TCK-20260710`'s Scope Guards forbid. This docstring note is load-bearing — it is
what Step 4's design leans on to justify putting the filter in `implement-ticket.js` instead of
here.

**Do NOT touch:** `check_workflow_meta_conformance()` itself — this is a pure wrapper around its
existing output, not a change to its FAIL/PASS logic. Do not add a `Security-Review` (or any
other) string literal anywhere in this function or file.

**Verify:** New test in Step 5 (`test_finalize_wiring_output_never_changes_terminal_status`'s
behavioral half) exercises this function directly with a fixture `List[dict]` containing a `FAIL`
entry.

### Step 4 — Wire the Finalize-tail advisory check into `implement-ticket.js`

**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Insert a new block immediately after the existing `check_tag_drift` block
(`implement-ticket.js:1525-1548`) and before the terminal `return { status: 'DONE', ... }`
(currently starting L1550). Follow the exact structural pattern of the `check_tag_drift` block
(comment header explaining placement/non-blocking contract, `bash()` call with an embedded
`python3 -c "..."` script, `MARKER:`-prefixed JSON output, `indexOf` + `try/catch JSON.parse`,
conditional `pushEvent`/`log` on a bad-status result only):

```js
// Advisory-only workflow-meta-conformance check (TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK,
// wired in by TCK-20260804-SKILL-DRIFT-DETECTION) — mirrors check_monitoring_write_recorded's
// placement: runs after status is already 'DONE', never gates ticket close. Security-Review is
// filtered out of the FAIL set at THIS call site (not inside workflow_meta_conformance.py itself,
// per TCK-20260710's no-per-workflow-allowlist Scope Guard on that module) because it is a
// conditionally-skipped phase that emits zero events (not even 'skipped') for every
// non-security-tagged ticket — see docs/agent-monitoring/schema.md and
// test_workflow_meta_conformance.py's xfail(strict=True) guard for the underlying gap this
// filter works around.
const phaseMetaCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.workflow_meta_conformance import check_workflow_meta_conformance, summarize_conformance_results
results = check_workflow_meta_conformance(sys.argv[1])
results = [r for r in results if r.get('phase') != 'Security-Review']
status, evidence = summarize_conformance_results(results)
print('PHASE_META_CHECK_JSON:' + json.dumps({'status': status, 'evidence': evidence}))
" "${tid}"`
)
let phaseMetaCheck = null
const phaseMetaMarkerIndex = phaseMetaCheckOutput.indexOf('PHASE_META_CHECK_JSON:')
if (phaseMetaMarkerIndex !== -1) {
  try {
    phaseMetaCheck = JSON.parse(phaseMetaCheckOutput.slice(phaseMetaMarkerIndex + 'PHASE_META_CHECK_JSON:'.length).trim())
  } catch (e) { phaseMetaCheck = null }
}
if (phaseMetaCheck !== null && phaseMetaCheck.status === 'FAIL') {
  pushEvent('Finalize', 'finalizer', 'failed', ('phase_meta_conformance: ' + phaseMetaCheck.evidence).slice(0, 200))
  log(`WARNING: possible phase-meta drift for ${tid} — ${phaseMetaCheck.evidence}`)
}
```

Note the filter (`results = [r for r in results if r.get('phase') != 'Security-Review']`) lives
inside the embedded `python3 -c` string — i.e. in `implement-ticket.js`, the call site — not in
`workflow_meta_conformance.py`. `NA` and `PASS` statuses are silently non-warning, matching
`check_monitoring_write_recorded`'s precedent (only a bad/failing result logs).

**Do NOT touch:** The `check_monitoring_write_recorded` block (L1502-1523), the `check_tag_drift`
block (L1525-1548), or the terminal `return` object's `status: 'DONE'` literal — this new block
must never reassign `status`.

**Verify:** Step 5's `test_finalize_wiring_output_never_changes_terminal_status` (static half) —
grep/source-inspect `implement-ticket.js` to confirm placement and immutability of `status`.

### Step 5 — Add the Finalize-wiring test

**Files:** `tests/tools/test_workflow_meta_conformance.py`

**Change:** Add `test_finalize_wiring_output_never_changes_terminal_status` (depends on Steps 3
and 4 both being complete — needs `summarize_conformance_results` importable and the real
`implement-ticket.js` text to inspect). Two assertions:
- **Static**: read `.claude/workflows/implement-ticket.js` as text; assert the new
  `PHASE_META_CHECK_JSON:` call-site marker string appears in the file, and that its index is
  greater than both the `pushEvent('Finalize', 'finalizer', 'ok'` line's index and the
  `await writeMonitoring('DONE')` line's index (same ordering proof as
  `check_monitoring_write_recorded`'s placement). Also assert the literal `status: 'DONE'` in the
  terminal `return` block is not conditioned on `phaseMetaCheck` (e.g. assert no
  `phaseMetaCheck.status` token appears inside the `return {` object literal — a simple
  string-slice check between the `return {` marker and its closing `}` is sufficient, no JS
  parser needed).
- **Behavioral**: call `summarize_conformance_results()` directly with a fixture `List[dict]`
  guaranteed to contain one `"FAIL"` entry (e.g. `[{"phase": "Investigate", "status": "FAIL",
  "evidence": "declared but zero events"}]`); assert the returned `(status, evidence)` is
  `("FAIL", ...)`; assert `json.dumps({"status": status, "evidence": evidence})` round-trips
  through `json.loads` cleanly and the parsed dict's `"status"` is `"FAIL"` — proving the
  `MARKER:`-prefixed JSON CLI contract can represent a FAIL result without needing the JS runtime.

**Do NOT touch:** Any existing test in this file.

**Verify:** `pytest tests/tools/test_workflow_meta_conformance.py -v` — full file green (9 new
[8 from Step 2 + 1 from this step] + 15 pre-existing = 24 tests total, 1 xfail, 23 passing).

### Step 6 — Document both new checks in `implement-ticket/SKILL.md`'s Finalize step

**Files:** `.claude/skills/implement-ticket/SKILL.md`

**Change:** Edit the Finalize step's item `(b)` (currently L68: *"(b) run the two advisory-only
Finalize-tail checks, `check_monitoring_write_recorded` and `check_tag_drift`
(`implement-ticket.js:1502-1548`) — both are logged warnings only and can never block ticket
close."*) to name all three checks and their line range (update the end-line number to match
wherever Step 4's new block actually lands), e.g.:

> (b) run the three advisory-only Finalize-tail checks, `check_monitoring_write_recorded`,
> `check_tag_drift`, and `check_workflow_meta_conformance` (aggregated via
> `summarize_conformance_results`, with `Security-Review` filtered out at this call site —
> `implement-ticket.js:1502-<new end line>`) — all three are logged warnings only and can never
> block ticket close.

Also add one new sentence to the same step's description (or a new short bullet immediately
after) documenting the new pytest-only doc-drift check, since it is a distinct mechanism (runs via
the test suite, not via this workflow), e.g.:

> Separately, `check_skill_doc_covers_meta_phases()`
> (`tools/gate_checks/workflow_meta_conformance.py`) verifies every hand-orchestration `SKILL.md`
> mentions all of its own workflow's declared `meta.phases` titles — this runs as a pytest test
> (`tests/tools/test_workflow_meta_conformance.py`), not as part of this workflow's own Finalize
> sequence.

**Do NOT touch:** Any other numbered step (1-13) or the `## Notes` section of this file — this
ticket's SKILL.md edit is scoped to the Finalize step's existing `(b)` sub-bullet plus one
additive sentence/bullet.

**Verify:** Manual read-through; no automated test asserts SKILL.md prose content beyond what
Step 2's real-file tests (`test_check_covers_real_implement_ticket_skill_md`) already check (which
happens to also re-verify this edit doesn't remove any of the 12 phase-title mentions).

### Step 7 — Update `docs/ai/ticket-lifecycle.md`'s Finalize section

**Files:** `docs/ai/ticket-lifecycle.md`

**Change:** In the `### Finalize` section (current numbered list, L500-533, ending at item 8 —
the knowledge-index refresh added by `TCK-20260802-DOC-UPDATE-DISCIPLINE`), add a new item 9:

> 9. **Advisory-only Finalize-tail checks** (`implement-ticket.js:1502-<new end line>`, added
>    incrementally by `TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`,
>    `TCK-20260720-TAG-RELEVANCE-VERIFY`, and `TCK-20260804-SKILL-DRIFT-DETECTION`): three checks
>    run immediately after step 7's monitoring write — `check_monitoring_write_recorded` (confirms
>    the write in step 7 actually landed), `check_tag_drift` (flags a possible mismatch between the
>    ticket's declared `tags:` and its `Files Changed`/`Related Code Areas` content; uses
>    `CLEAN`/`FLAGGED`, never `PASS`/`FAIL`, so it can never be misread as a DoD condition), and
>    `check_workflow_meta_conformance` (flags a workflow phase declared in `meta.phases` that fired
>    zero events during this run; `Security-Review` is filtered out at the call site since it
>    legitimately emits zero events on non-`security`-tagged tickets). All three are logged
>    `WARNING`s only and never change the terminal `status` away from `DONE`.

This is a same-paragraph accuracy fix bundled with the ticket's own required update (investigation.md's
"Docs Requiring Update" already scopes this section in for the new wiring) — naming the two
pre-existing checks here for the first time is a small, directly-adjacent correction, not new
scope: this section is being edited regardless, and leaving it naming only the new third check
while staying silent on the two checks sitting right next to it in the same code block would itself
be a fresh doc-vs-code gap of exactly the kind this ticket exists to prevent.

**Do NOT touch:** Steps 1-8 of the existing numbered list, the `## Epic Batch Workflow` section
immediately below (L538+), or any other section of this file.

**Verify:** Manual read-through; if this file is modified, the ticket's own After-Work rule
requires `make knowledge-index-update` to run during Finalize of this ticket (already automatic
per the existing `implement-ticket.js:1482-1490` block — no separate action needed here).

## Scope Guards

- Do not edit `.claude/workflows/implement-ticket.js`, `create-tickets.js`, or
  `implement-epic.js`'s `meta.phases` arrays — confirmed accurate for all three in
  investigation.md; nothing to fix.
- Do not add a `"Security-Review"` (or any other phase name) string literal anywhere inside
  `tools/gate_checks/workflow_meta_conformance.py` — the filter belongs exclusively in
  `implement-ticket.js`'s embedded `python3 -c` call site (Step 4).
- Do not modify `check_workflow_meta_conformance()`'s existing FAIL/PASS/NA logic, its function
  signature, or its `if __name__ == "__main__"` CLI block.
- Do not modify `extract_meta_phases()`, `resolve_workflow_source_path()`, or
  `collect_run_event_statuses()`.
- Do not promote either new check to a hard-blocking gate; do not let the new Finalize-tail block
  reassign `status` away from `'DONE'` under any result.
- Do not remove or weaken the existing `@pytest.mark.xfail(strict=True)` marker on
  `test_does_not_flag_security_review_absent_when_ticket_untagged_security` — it guards a
  different, still-open gap in `check_workflow_meta_conformance()` itself.
- Do not touch `implement-epic.js`'s Discover/Report event-emission bug (hardcoded
  `phase: 'Implement'`) — confirmed pre-existing, out of scope, already flagged in
  investigation.md as a candidate future ticket.
- Do not wire `check_skill_doc_covers_meta_phases()` into any workflow's Finalize phase — it is
  pytest-only per AC #3 and the ticket's own Scope guidance.
- Do not touch `tests/tools/test_done_checker_static.py`, `test_done_checker_audit.py`,
  `test_validate_agent_monitoring.py`, or
  `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` — regression surface
  only, must keep passing unchanged.
- Do not edit `docs/ai/ticket-lifecycle.md` outside the `### Finalize` section's new item 9.

## Dependency Map

- Step 1 — independent (new functions, additive).
- Step 2 — depends on Step 1 (tests exercise the new function).
- Step 3 — independent of Steps 1-2 (wraps the pre-existing `check_workflow_meta_conformance`);
  ordered after Step 2 only to keep the file diff localized and readable.
- Step 4 — depends on Step 3 (imports `summarize_conformance_results`).
- Step 5 — depends on Steps 3 and 4 (needs both the aggregation function and the real JS wiring to
  inspect).
- Step 6 — depends on Step 4 (needs the final line range of the new JS block).
- Step 7 — depends on Step 4 (same reason as Step 6); independent of Step 6.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `meta.phases` confirmed current for all 3 in-scope workflows (or staleness flagged) | N/A — already satisfied by investigation.md (no drift found); no plan step needed | `test_parses_meta_phases_from_implement_ticket_js`/`_create_tickets_js`/`_implement_epic_js` (pre-existing, unchanged) |
| New `check_skill_doc_covers_meta_phases()`-equivalent function exists, with tests, reusing `extract_meta_phases()` | Steps 1, 2 | Tests 1-8 (Step 2), esp. #8 (reuse guard) |
| New check is runnable as a pytest test, no pipeline wiring dependency | Steps 1, 2 | `pytest tests/tools/test_workflow_meta_conformance.py -v` |
| `check_workflow_meta_conformance()` wired into `implement-ticket.js`'s Finalize phase, non-blocking/advisory | Steps 3, 4 | Step 5's `test_finalize_wiring_output_never_changes_terminal_status` |
| `implement-ticket/SKILL.md` documents both new checks in its Finalize step | Step 6 | Manual read-through; indirectly re-verified by Step 2 test #5 |
| Both new checks pass against current `implement-ticket/SKILL.md` and `create-tickets/SKILL.md` | Step 2 | Tests #5, #6 (and bonus #7 for implement-epic) |

## Anti-Drift Notes

- **Collision guard is real, not decorative.** `_title_has_dedicated_mention()` (Step 1) must
  actually strip sibling superstring titles before matching — a lazy implementation that just
  does `title in text` defeats the entire point of Step 1 and would make test #4 (Step 2) fail
  honestly, which is the intended tripwire. Do not weaken test #4 to make a naive implementation
  pass.
- **The Security-Review filter must stay in `implement-ticket.js`, never migrate into
  `workflow_meta_conformance.py`.** This is the single most re-derivable-wrong decision in this
  plan — it would be natural but incorrect to "clean up" by moving the filter into
  `summarize_conformance_results()` or `check_workflow_meta_conformance()` for convenience. Doing
  so reopens the exact per-workflow-allowlist anti-pattern `TCK-20260710`'s Scope Guards
  deliberately closed off. If a future ticket needs a second conditional-phase exclusion, it
  belongs at whatever new call site needs it, not inside the shared module.
- **`summarize_conformance_results()` is a pure, phase-agnostic fold.** It must work correctly for
  any `List[dict]` in this module's `{"phase", "status", "evidence"}` shape — including the `NA`
  single-entry convention — without knowing anything about `Security-Review` or any other specific
  phase name.
- **Both new Finalize-tail checks (existing two + the new third) remain advisory-only.** No code
  path introduced by this ticket may set the terminal `return` object's `status` to anything other
  than `'DONE'` based on `phaseMetaCheck`'s result — this mirrors the Hard Rule that a monitoring
  write failure (and, by the same precedent, this new check) must never fail the workflow.
- **The `xfail(strict=True)` test for `check_workflow_meta_conformance()`'s own Security-Review gap
  stays untouched.** This ticket resolves the Finalize-wiring *noise* problem (by filtering at the
  call site) but does not resolve the underlying "zero events of any status is ambiguous between
  legitimately-conditional and silently-skipped" architecture question the `xfail` documents — that
  remains open, tracked by that test, for a future ticket (the never-created
  `TCK-yyyymmdd-CONDITIONAL-PHASE-CALLSITE-DETECTION` investigation.md references).
- **`implement-epic.js`'s Discover/Report event-emission bug is out of scope** and must not be
  touched even though it means `check_workflow_meta_conformance` would always-FAIL if ever pointed
  at a real `implement-epic` run — irrelevant here since this ticket's Finalize wiring target is
  `implement-ticket.js` only.
- **`docs/ai/ticket-lifecycle.md`'s new item 9 naming the two pre-existing checks is an in-scope,
  same-section accuracy fix, not scope creep** — justified above in Step 7; if this judgment is
  later disputed, the minimal fallback is to only add the new third-check language and leave the
  two pre-existing checks unnamed, but that would immediately leave the edited paragraph
  internally inconsistent (naming one check by function name and describing the other two only
  by pronoun).

## Deviations

- **Step 1 also updated `workflow_meta_conformance.py`'s module docstring**, not called out in the
  plan's Step 1 change list (which named only the 4 additions: `DEFAULT_SKILLS_DIR`,
  `resolve_skill_md_path()`, `_title_has_dedicated_mention()`, `check_skill_doc_covers_meta_phases()`).
  The module's top-of-file docstring previously stated "This ticket ships the verifier and its
  tests only — it is not wired into any workflow's Finalize phase," which became false the moment
  Step 4 landed. Left unfixed, this ticket — whose entire purpose is closing exactly this class of
  doc-vs-code drift — would have shipped a new, self-inflicted instance of it inside its own
  target module. Updated the docstring to state the wiring is now live and to describe the new
  `check_skill_doc_covers_meta_phases()` function. Did not touch any of the plan's explicit "Do NOT
  touch" targets (`extract_meta_phases()`, `resolve_workflow_source_path()`,
  `collect_run_event_statuses()`, `check_workflow_meta_conformance()`'s FAIL/PASS logic, or the
  `if __name__ == "__main__"` block) — this was a docstring-only, non-functional change.
- **Step 4's actual line range is `implement-ticket.js:1502-1581`**, not the plan's placeholder
  `1502-1548` (which was the pre-existing two-check block's own range, reused as a stand-in before
  the new block's real size was known). This is expected placeholder resolution, not a design
  deviation — Steps 6 and 7 already anticipated needing "wherever Step 4's new block actually
  lands" and were written using the resolved `1502-1581` range.
