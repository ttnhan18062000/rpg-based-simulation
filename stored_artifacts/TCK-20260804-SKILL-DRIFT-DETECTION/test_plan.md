---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-DRIFT-DETECTION
artifact_type: test_plan
phase: open
date: 2026-08-04
tags: [ai, workflows, skills]
---

# Test Plan — TCK-20260804-SKILL-DRIFT-DETECTION

## Regression Surface

**Unit — `tools/gate_checks/` siblings (must keep passing unchanged; the new doc-drift function is
additive to `workflow_meta_conformance.py`, not a rewrite — must not disturb any existing function
signature or behavior in that file):**
- `tests/tools/test_workflow_meta_conformance.py` — all 15 existing tests (`extract_meta_phases`
  x4, `resolve_workflow_source_path` x2, `collect_run_event_statuses` x2,
  `check_workflow_meta_conformance` x5, the `xfail(strict=True)` Security-Review real-fixture
  guard, and the `vocabulary.py`-reuse architecture guard). The `xfail(strict=True)` test must
  remain `xfail` — this ticket does not resolve that gap (see investigation.md Risk #1); if
  implementation work incidentally makes it pass, that is a signal to re-examine the wiring
  design, not to quietly remove the marker.
- `tests/tools/test_done_checker_static.py` — exercises `check_monitoring_write_recorded`,
  `check_tag_drift`, `run_finalize_selfcheck`, `_jsonl_rows_for_run_id` (imported by
  `workflow_meta_conformance.py`; must not be touched by this ticket).
- `tests/tools/test_done_checker_audit.py`
- `tests/tools/test_validate_agent_monitoring.py` — includes
  `test_canonical_vocabulary_single_sourced`, the existing guard against forking a second copy of
  `WORKFLOW_PHASES`/`infer_workflow`.

**Integration — `tests/agent_orchestration_claude_adapter/`:**
- `tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py` — both tests
  (`test_phase_order_conformance_byte_identical_to_live_meta_phases`,
  `test_live_phase_order_has_the_expected_12_phases`) import `extract_meta_phases` directly and
  assert the live 12-phase `implement-ticket.js` order. Must keep passing unchanged — a second,
  independent consumer of `extract_meta_phases()` that this ticket must not break by changing that
  function's signature or return shape.

**No `src/`, `tests/unit/`, `tests/integration/` (simulation), or `tests/arena-combat/` surface is
implicated** — this ticket touches only `.claude/workflows/*.js` (documentation-only edits to
`SKILL.md` files, not the `.js` files themselves), `.claude/skills/*/SKILL.md`, and
`tools/gate_checks/workflow_meta_conformance.py`.

## New Tests Required

All new tests live in `tests/tools/test_workflow_meta_conformance.py` (extending the existing
file, not a new one — mirrors that file's own established fixture helpers
`_write_workflow_js(tmp_path, workflow_name, titles)` / the pattern for a parallel
`_write_skill_md(tmp_path, workflow_name, body_text)` helper), per the ticket's instruction to
reuse `extract_meta_phases()` rather than reimplement it, and per that file's own
coverage-honesty requirement (every check function needs ≥1 fixture proving it catches a real
violation, not just a happy-path run).

1. **`test_skill_doc_covers_all_declared_phases_happy_path`**
   - Category: unit
   - Verifies: for a synthetic `meta.phases` list (`["Alpha", "Beta"]`) and a synthetic SKILL.md
     body text containing both `**Alpha**` and `**Beta**` (mirroring the real bold-wrapped format
     confirmed in investigation.md), the new function reports full coverage / zero missing titles.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

2. **`test_skill_doc_flags_missing_phase_title`** (coverage-honesty required fixture — catches a
   real violation)
   - Category: unit
   - Verifies: a synthetic SKILL.md body missing one declared title entirely (e.g. `meta.phases =
     ["Alpha", "Beta", "Gamma"]`, body text mentions only `**Alpha**` and `**Beta**`) is reported
     as missing `"Gamma"`, with non-empty evidence identifying which title and which file.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

3. **`test_skill_doc_tolerates_bold_and_plain_wrapping`**
   - Category: unit (real-evidence-based, not assumed)
   - Verifies: a title present as plain, unwrapped text (no `**`) still counts as covered —
     directly encodes investigation.md's finding that markdown bold-wrapping never actually
     obstructs a substring match (both forms found in the real files: e.g.
     `create-tickets/SKILL.md`'s `**Investigate**` heading vs. its later plain-text
     "the Investigate phase derives them" mention).
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

4. **`test_skill_doc_substring_collision_between_sibling_titles_is_a_known_limitation`**
   (anti-drift / documents the found risk rather than silently hiding it)
   - Category: unit (regression/limitation guard)
   - Verifies: reproduces the exact `Review`/`Security-Review` (or `Verify`/`Architecture-Verify`)
     shape found in investigation.md — a synthetic `meta.phases = ["Review", "Security-Review"]`
     with a body text containing only `**Security-Review**` (the standalone `**Review**` heading
     deleted, simulating the exact future-edit risk flagged) — and asserts whatever behavior Plan
     decided on for this case (either: the check correctly flags `Review` as missing because the
     match logic guards against the collision, in which case this test proves the guard works; or,
     if Plan explicitly accepted the blind spot per investigation.md Risk #2, this test is instead
     an explicit `xfail`/documented-limitation test, not silently omitted). Whichever design Plan
     picks, this test must exist and must not be silently dropped — the collision is a confirmed,
     evidenced finding, not a hypothetical.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

5. **`test_check_covers_real_implement_ticket_skill_md`** (AC #6 — real-file, not synthetic)
   - Category: unit (real-evidence, matches `test_parses_meta_phases_from_implement_ticket_js`'s
     "read the real file, not a fixture copy" convention)
   - Verifies: running the new check against the real, live
     `.claude/workflows/implement-ticket.js` + `.claude/skills/implement-ticket/SKILL.md` pair
     produces zero missing-title findings — directly proves the new check does not false-positive
     against the file this session's `TCK-20260804-SKILL-JS-PHASE-SYNC` already fixed. Directly
     satisfies ticket AC #6 for the `implement-ticket` half.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

6. **`test_check_covers_real_create_tickets_skill_md`** (AC #6 — real-file, not synthetic)
   - Category: unit (real-evidence)
   - Verifies: same as #5, for the real `.claude/workflows/create-tickets.js` +
     `.claude/skills/create-tickets/SKILL.md` pair — zero missing-title findings. Directly
     satisfies ticket AC #6 for the `create-tickets` half (fixed today by
     `TCK-20260804-CREATE-TICKETS-SKILL-SYNC`).
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

7. **`test_check_covers_real_implement_epic_skill_md`**
   - Category: unit (real-evidence)
   - Verifies: `.claude/workflows/implement-epic.js` + `.claude/skills/implement-epic/SKILL.md`
     pair — zero missing-title findings against `implement-epic.js`'s own 3 phases
     (`Discover, Implement, Report`), confirmed present in investigation.md. Per investigation.md
     Risk #3, this test asserts coverage of `implement-epic.js`'s *own* `meta.phases` only — it
     must NOT assert anything about `implement-ticket.js`'s 12 phase titles appearing in
     `implement-epic/SKILL.md` (they legitimately don't; that file delegates by reference).
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

8. **`test_new_function_reuses_extract_meta_phases_not_a_reimplementation`** (architecture guard)
   - Category: architecture guard
   - Verifies: mirrors the existing
     `test_reuses_vocabulary_infer_workflow_not_a_reimplementation` pattern — asserts (via source
     inspection or a monkeypatch/call-count spy on `extract_meta_phases`) that the new function
     calls the existing `extract_meta_phases()` rather than reimplementing its own
     `phases: [` / `title:` regex parsing.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

9. **`test_finalize_wiring_output_never_changes_terminal_status`** (JS-side behavior verified from
   the Python side, mirroring `check_monitoring_write_recorded`'s established precedent — no
   `*.test.js` harness exists in this repo)
   - Category: architecture guard
   - Verifies two things about the new `implement-ticket.js` call site specifically:
     (a) **static**: `grep`/source-inspect `implement-ticket.js` to confirm the new
     `check_workflow_meta_conformance` call site is placed strictly after the existing
     `pushEvent('Finalize', ..., 'ok', ...)` / `await writeMonitoring('DONE')` lines (same
     positioning as `check_monitoring_write_recorded`/`check_tag_drift`, `implement-ticket.js:1492-1493`)
     and that no code path reassigns the `status` field returned to the caller based on this
     check's result; (b) **behavioral**: feed the aggregate function a fixture guaranteed to
     contain at least one `"FAIL"` entry (e.g. the real `Security-Review`-absent shape) and assert
     the JSON emitted for the `MARKER:`-prefixed CLI contract is well-formed and contains that
     `FAIL`, proving a FAIL result is representable and parseable by the JS-side
     `indexOf` + `try/catch JSON.parse` convention without needing the JS runtime itself.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

## Scoped Pytest Commands

```bash
# New/extended module's own tests
pytest tests/tools/test_workflow_meta_conformance.py -v

# Full regression surface: this file's siblings + the second independent consumer of
# extract_meta_phases() (the Claude-adapter phase-order conformance tests)
pytest tests/tools/test_workflow_meta_conformance.py \
       tests/tools/test_done_checker_static.py \
       tests/tools/test_done_checker_audit.py \
       tests/tools/test_validate_agent_monitoring.py \
       tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py -v
```

Never `pytest tests/` — scope stays inside `tests/tools/` plus the one confirmed
`extract_meta_phases()` consumer outside it (`tests/agent_orchestration_claude_adapter/`); this
ticket touches nothing under `src/`, so no `tests/unit/`, `tests/integration/`, or
`tests/arena-combat/` domain is implicated.

## Anti-Drift Test Guards

- **Test #4 is the primary anti-drift guard for the match-semantics design decision itself** — it
  exists specifically so the `Review`/`Security-Review` (and `Verify`/`Architecture-Verify`)
  substring-collision finding from investigation.md cannot be silently forgotten. Whatever design
  Plan picks, deleting this test (rather than updating its assertion to match the chosen design)
  should be treated as a scope regression.
- **Tests #5, #6, #7 are the ones that directly gate ticket AC #6** ("Both new checks pass against
  the current, just-fixed state of `implement-ticket/SKILL.md` and `create-tickets/SKILL.md`") —
  they must run against the real, live files (not fixture copies), matching
  `test_parses_meta_phases_from_implement_ticket_js`'s own established "read the real file"
  convention, so a future re-drift of either SKILL.md fails these tests immediately rather than
  only being caught by a human noticing again.
- **Test #8 is a structural anti-drift guard**, not behavioral — mirrors
  `test_reuses_vocabulary_infer_workflow_not_a_reimplementation`'s intent for the new function:
  catches a future edit that "helpfully" inlines a second copy of the `phases: [` / `title:` regex
  instead of calling `extract_meta_phases()`.
- **Test #9 is the guard that the Finalize wiring never becomes a hard gate** — directly verifies
  the ticket's own AC #4 constraint ("non-blocking/advisory") and Out-of-Scope bullet ("no
  track record yet... never a new hard gate"). A future edit that starts branching `status` on
  this check's result should fail this test immediately.
- **The existing `xfail(strict=True)` Security-Review test in the regression surface must remain
  `xfail`** — if implementation work for this ticket incidentally causes it to start passing (e.g.
  because Plan's Risk #1 resolution touches shared logic), that is a signal requiring an explicit
  Plan/investigation update, not a silent `xfail` removal. Treat an unexpected pass (`XPASS` under
  `strict=True`, which itself fails the run) as a stop-and-report event, not a bug to route around
  during Test/Verify.
- Do not let any new test assert a clean, zero-missing-title result against
  `implement-epic/SKILL.md` for `implement-ticket.js`'s 12 phase titles — per investigation.md
  Risk #3, that file legitimately does not (and per the 1:1-pairing design should not need to)
  mention them; asserting otherwise would either force scope creep into duplicating the
  translation table there or falsely validate a design nobody chose.
