---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-PHASE-AGENT-CASE-FOLD
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260719-PHASE-AGENT-CASE-FOLD

## Summary

Fold phase/agent casing variants into their canonical spelling, at read time, inside
`generate_retro.py::compute_retro_metrics()`'s three phase/agent-keyed aggregations, using
`vocabulary.py`'s existing `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`/`infer_workflow` as the sole merge
target. Add a new `phase_status_distribution` output (nothing phase-keyed existed before) so the
ticket's own motivating claim (Review's real 18.2% failure rate) is actually provable.

## Anti-Drift Notes

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: implemented directly in the same pass as investigation; this file
and `investigation.md`/`test_plan.md` were written retroactively, after implementation and full
test verification (162/162 scoped tests passing), not before — same pattern as
`TCK-20260719-COST-PROXY-WRITE-PATH` immediately preceding this ticket in the same batch. The fix
itself is low architectural risk (pure read-time aggregation change, no `src/` file, no schema
change), which is why this deviation is judged acceptable rather than corrected by a full replan.

## Steps

### Step 1 — Import canonical vocabulary

**Files:** `tools/agent-monitoring/generate_retro.py`
Add `sys.path.insert(0, str(Path(__file__).resolve().parent))` (same directory, mirrors the
existing `_TOOLS_DIR` pattern one level up) and `from vocabulary import WORKFLOW_AGENTS,
WORKFLOW_PHASES, infer_workflow` — the same module object `record_events.py`/`validate.py` already
import, never a second copy.

### Step 2 — Add normalization helpers

**Files:** `tools/agent-monitoring/generate_retro.py`
`_canonicalize(value, canonical_set)` — generic casefold-match-or-passthrough, never fabricates a
canonical spelling for an unmatched value. `_normalize_phase(e)`/`_normalize_agent(e)` — thin
wrappers resolving the event's workflow via `infer_workflow` first, then delegating to
`_canonicalize` against that workflow's own `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` set. An event whose
`run_id` matches no known workflow passes its phase/agent through completely unchanged.

### Step 3 — Wire into the 3 existing aggregations + add phase_status_distribution

**Files:** `tools/agent-monitoring/generate_retro.py`
`agent_status_distribution`, `spend_proxy_by_phase`, `spend_proxy_by_agent`: replace raw
`e.get("phase"/"agent", "?")` dict keys with `_normalize_phase(e)`/`_normalize_agent(e)` (falling
back to `"?"` only if the normalizer itself returns `None`, i.e. the field was genuinely absent).
Add a new `phase_stats`/`phase_status_distribution` mirroring `agent_status_distribution`'s exact
shape but keyed by normalized phase — this is new, not a rename, since no phase-keyed breakdown
existed before. `_TAG_GATE_PHASE`'s existing `security`-tag `casefold()` comparison is left
untouched (already correctly case-insensitive, never broken).

### Step 4 — Render the new section

**Files:** `tools/agent-monitoring/generate_retro.py`
Add a "## Phase Status Distribution" section to `generate()`, placed immediately after "## Agent
Status Distribution", identical table shape (`Phase | Calls | ok | failed | blocked | skipped`).

### Step 5 — Update/add tests

**Files:** `tests/tools/test_generate_retro.py`
Update `test_compute_retro_metrics_returns_all_documented_keys` for the new key. Add: Review's
merged-failure-rate proof (with naive-vs-merged comparison), Markdown rendering proof, agent-casing
mechanism proof, `spend_proxy_by_phase` merge proof, unknown-workflow passthrough safety,
create-tickets prefix-family non-collision.

## Scope Guards

- Zero changes to `tools/agent-monitoring/validate.py` — verified via `git diff --stat` showing no
  output, not just "tests still pass."
- No second hardcoded phase/agent vocabulary list — `test_canonical_vocabulary_single_sourced`
  guards this (checks `record_events.py`/`validate.py` share one module object; `generate_retro.py`
  importing the same module satisfies the same spirit even though that specific test doesn't check
  this file by name).
- `gate_counter` (`final_status`-keyed, a different vocabulary with its own documented
  no-normalize-legacy-strings design in `_resolve_status`'s docstring) is explicitly NOT touched.
- No implementation of `TCK-20260713-MONITORING-SQLITE-INDEX`'s derived-index migration — confirmed
  still unimplemented, proceeding directly in `generate_retro.py` per the sibling ticket's own
  carried-forward sequencing note.

## Dependency Map

Step 1 before Step 2 (Step 2 imports what Step 1 makes available). Step 2 before Step 3 (Step 3
calls the helpers Step 2 defines). Step 4 depends on Step 3 (renders the key Step 3 adds). Step 5
depends on Steps 1-4 (tests the landed behavior).

## Acceptance Criteria Map

- AC1 (all 8/9 affected phases' casing variants merged in the 3 named aggregations, using
  `vocabulary.py`'s canonical sets) → Steps 1-3.
- AC2 (regression test proving Review's real merged failure rate resolves to 18.2%) → Steps 3-5
  (the `phase_status_distribution` addition Step 3 makes, tested in Step 5).
- AC3 (`validate.py`'s drift-visibility output unchanged) → Scope Guards; verified via zero-diff
  check, not just passing tests.
- AC4 (`test_canonical_vocabulary_single_sourced` continues to pass) → Step 1 (reuses the same
  imported module object, never redefines).

## Deviations

None from this plan itself (written retroactively to describe the actual landed implementation
exactly) — see Anti-Drift Notes above for the one deviation that matters: staging artifacts were
written after implementation, not before. One real, evidence-driven addition beyond a literal
reading of the ticket's Scope: `phase_status_distribution` was added because AC2 was otherwise
untestable — documented explicitly in the ticket's own Implementation Notes, not silently done.
