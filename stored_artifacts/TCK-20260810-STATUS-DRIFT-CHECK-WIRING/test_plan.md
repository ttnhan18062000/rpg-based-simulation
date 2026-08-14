---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-STATUS-DRIFT-CHECK-WIRING
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement, data-quality]
---

# Test Plan — TCK-20260810-STATUS-DRIFT-CHECK-WIRING

## Regression Surface

**Unit:**
- `tests/tools/test_status_drift_check.py` (16 tests) — must stay green through both the body-text
  data repair and whichever wiring option is chosen. Includes
  `test_uses_real_dashboard_extraction_function` (anti-drift guard: checker must keep importing the
  real `parse_body_section`, never a reimplemented regex) and `test_check_is_read_only` (the checker
  itself must never mutate `tickets/done/*.md` or `agent-monitoring/runs.jsonl` — the data repair in
  this ticket happens via direct edits, not via the checker).
- `tests/tools/test_ticket_field_values.py` (8 tests) — regression surface if option (a) is chosen,
  since the new condition sits alongside `ticket_field_values_valid` in the same
  `run_static_precheck` checks tuple; must confirm this ticket's change does not alter
  `check_ticket_field_values`'s own behavior.
- `tests/tools/test_done_checker_static.py` — regression surface if option (a) is chosen (new
  condition added to `run_static_precheck`'s checks tuple, changing its expected length/shape from
  7 to 8 entries — mirrors how `TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM` updated
  `test_run_static_precheck_all_pass_eligible`'s assertion from 5 to 6 conditions).
- `tests/tools/test_generate_registry.py` — regression surface only if `parse_body_section` itself
  is touched (it should not be — Out of Scope explicitly excludes rebuilding extraction logic).

**Integration:**
- `tests/tools/test_agent_ops_dashboard_ingest.py` — confirms `workflow_status` extraction
  (`ingest.py:137`) is unaffected; relevant because the 7 real drift fixes change what
  `workflow_status` resolves to for those 7 ticket files (from `OPEN`/`INPROGRESS` to `DONE`).
- `tests/tools/test_agent_ops_dashboard_api.py`, `test_agent_ops_dashboard_frontend_api_surface.py`
  — confirms the dashboard's `statuses` facet and ticket-list endpoint still behave correctly after
  the 7 files' body text changes (no schema change, just data value changes — should be a no-op
  regression check, not expected to need updates).

**Arena-combat:** None — this ticket touches no simulation/combat code.

## New Tests Required

Per Acceptance Criteria:

1. **Test name:** `test_[3-or-7]_real_drift_instances_fixed` (or one parametrized test per file)
   **Category:** unit (data-repair regression)
   **What it verifies:** each repaired ticket file (`TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md`,
   `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`, `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md`,
   plus whichever of the 4 newly-confirmed instances Plan decides to include —
   `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION.md`,
   `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS.md`,
   `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION.md`,
   `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`) now has `## Status` body text resolving
   to exactly `DONE` via `parse_body_section`.
   **Where it should live:** either a new small script/test in `tests/tools/` asserting
   `check_ticket_status_drift(Path("tickets/done"))` returns the single `PASS` aggregate with these
   filenames absent from any FAIL evidence, or (cheaper, matches this module's own read-only
   philosophy) a live-corpus assertion inline in the Verify phase, not necessarily a new pytest test
   — the existing `test_status_drift_check.py` suite already tests the check function against
   synthetic fixtures, so a full live-corpus PASS re-run (see Scoped Pytest Commands) may be
   sufficient without inventing a new brittle "read these 7 specific files" test. Recommend Plan
   decide between a lightweight new test vs. relying on the live-run command below — do not invent a
   hardcoded-filename-list test that would go stale the moment corpus composition changes again
   (mirrors this checker's own value/pattern-based exemption design philosophy, not the anti-pattern
   it deliberately avoids).

2. **Test name:** `test_2_false_positives_untouched`
   **Category:** unit / architecture guard (anti-drift)
   **What it verifies:** `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md` and
   `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md`'s `## Status` body text is byte-identical before
   and after this ticket's changes (a `git diff` check, not necessarily a pytest test — Verify phase
   should confirm via `git diff --stat tickets/done/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md
   tickets/done/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md` showing no changes).
   **Where it should live:** Verify-phase diff check (per AC #3's own wording: "verified by a diff
   check in Verify"), not necessarily a new pytest test.

3. **Test name:** depends on wiring option chosen by Plan:
   - **If option (a) (blocking gate):** a new test in `tests/tools/test_done_checker_static.py`
     mirroring `test_run_static_precheck_blocks_on_bad_priority`/
     `test_run_static_precheck_passes_valid_priority` (the `ticket_field_values_valid` precedent) —
     e.g. `test_run_static_precheck_blocks_on_non_canonical_status` /
     `test_run_static_precheck_passes_canonical_status`, proving the new condition actually catches a
     synthetic non-`DONE` `## Status` on the ticket currently being closed (a genuine-catch proof,
     per `TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM`'s own precedent of stashing the fix and
     confirming the test fails pre-fix). Plus an update to
     `test_run_static_precheck_all_pass_eligible` for the new condition count (7 → 8 checks in
     `run_static_precheck`'s tuple).
     **Category:** unit / architecture guard.
     **Where it should live:** `tests/tools/test_done_checker_static.py`.
   - **If option (b) (recurring report):** a test confirming the new Makefile
     target/`generate_retro.py` call site actually invokes `check_status_drift()` and surfaces its
     result (e.g. a subprocess test asserting `make <target-name>` runs `status_drift_check.py` and
     exits non-zero on a synthetic drift fixture, or a `generate_retro.py` unit test asserting the
     drift section appears in its report output).
     **Category:** integration.
     **Where it should live:** `tests/tools/test_generate_retro.py` (if that module exists — verify
     during Plan) or a new `Makefile`-invocation test alongside existing gate-check Makefile tests.

4. **Test name:** `test_forward_only_exemption_decision_documented` — **only if** Plan decides a
   date-exemption mechanism is needed (per this investigation's Risk #5, current evidence says it is
   not needed for a per-ticket-only gate, and not urgently needed for a corpus-wide gate given 0
   pre-cutoff FAILs today). If Plan adds an exemption:
   **Category:** unit.
   **What it verifies:** a synthetic pre-2026-07-04 ticket with non-canonical `## Status` is exempted
   (mirrors `tag_taxonomy.md`'s forward-only precedent for tag/registry checks); a
   post-2026-07-04 ticket with the same defect is NOT exempted.
   **Where it should live:** `tests/tools/test_status_drift_check.py`.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_status_drift_check.py -v
python3 -m pytest tests/tools/test_ticket_field_values.py tests/tools/test_done_checker_static.py -v
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```

Live-corpus confirmation (not pytest, but required evidence for Verify — matches this module's own
`__main__` CLI contract):
```
python3 tools/gate_checks/status_drift_check.py
```
Expect the `MARKER:` JSON payload's ticket-FAIL entries to be reduced from 9 (2 of which are known
false positives) to exactly 2 (the false positives), assuming Plan fixes all 7 confirmed real
instances; or reduced from 9 to 6 if Plan holds strictly to the originally-cited 3.

Never: `pytest tests/` (repo-wide) — none of the above scope touches `src/` simulation code, so a
broader run is unnecessary and against CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **`test_2_false_positives_untouched`** (New Tests #2) is itself the primary anti-drift guard for
  this ticket's most explicit hazard — an agent "fixing" the false positives to quiet the checker
  instead of leaving genuinely accurate completion prose alone.
- **`test_uses_real_dashboard_extraction_function`** (existing, `test_status_drift_check.py`) must
  keep passing unmodified — proves no one reverts to a bespoke regex while wiring this in.
- **`test_check_is_read_only`** (existing) must keep passing unmodified — the checker itself must
  remain read-only; the 7 body-text repairs must be direct file edits by the implementer, never a
  checker-triggered auto-fix (no such auto-fix mechanism should be introduced — Out of Scope
  explicitly limits this ticket to detection/decision, not auto-remediation).
- If option (a) is chosen: a test proving the new blocking condition validates **only the ticket
  currently at Verify/Finalize**, not a full `tickets/done/` corpus scan — this is the specific
  design-mismatch hazard flagged in this investigation's Anti-Drift Hazards (accidentally wiring in
  `check_ticket_status_drift(done_dir)`'s corpus-wide scan as a per-close blocking gate would make
  every future unrelated ticket close fail-closed the instant any drift appears anywhere in the
  corpus — a materially different, more fragile design than the `ticket_field_values.py` precedent
  it's meant to mirror). A regression test asserting the new check function's signature/behavior
  takes a single `ticket_path`, not a `done_dir`, would catch this directly.
- A regression test (or Verify-phase manual check) confirming `docs/parity_ledger/infrastructure.yaml`'s
  INFRA-277 entry no longer says "Ships unwired" once wiring lands, and no longer cites a stale
  "confirmed clean: `[]`" live-corpus result — catches a parity-ledger staleness regression of the
  exact kind CLAUDE.md's Authoritative Mechanics Rule and this repo's own dogfooded practice (see
  `docs/parity_ledger/infrastructure.yaml`'s own past self-correcting parity-gap entries) are meant
  to prevent.
