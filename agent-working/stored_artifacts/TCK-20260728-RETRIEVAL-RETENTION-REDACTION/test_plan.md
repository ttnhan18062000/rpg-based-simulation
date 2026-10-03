---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-RETENTION-REDACTION
artifact_type: test_plan
tags: [ai, observability, agent-monitoring]
---

# Test Plan — TCK-20260728-RETRIEVAL-RETENTION-REDACTION

This ticket is **decision-only**: its sole deliverable is a doc (expected
`docs/observability/retrieval_retention_redaction_policy.md`, per the Plan phase's location
decision — see investigation.md Risk 3). No `src/`, `tools/`, or `tests/` file is created or
modified as part of landing it. The ticket's own Acceptance Criteria include "Doc declares itself
decision-only: no changes land in `retention.py`, `core/retention.py`, or any
`tools/agent-monitoring/*.py` writer" — so the regression surface below exists to prove exactly
that: nothing changed.

## Regression Surface

Existing tests that must keep passing, unchanged, because this ticket touches none of their
subject code:

**Unit**
- `tests/unit/observability/test_retention_manager.py` — 3 tests
  (`test_retention_policy_classification`, `test_retention_manager_generate_plan`,
  `test_retention_manager_execute_cleanup`) covering `RetentionPolicy.classify_run()` and
  `RetentionManager.generate_cleanup_plan()`/`execute_cleanup()`. Guards
  `src/observability/reporting/retention.py`.
- `tests/unit/core/test_retention.py` — 3 tests (`test_bounded_list_overflow_evict_oldest`,
  `test_bounded_list_reject`, `test_truncate_newest`) covering `BoundedBuffer`/`OverflowPolicy`.
  Guards `src/core/retention.py`.

**Integration**
- None identified as directly coupled to `retention.py`/`core/retention.py` beyond the unit level;
  no integration test imports either module (confirmed no hits searching for
  `RetentionPolicy|RetentionManager|BoundedBuffer` outside the two unit test files above and their
  source modules).

**Arena-combat**
- Not applicable — this ticket has no combat/simulation surface.

## New Tests Required

**None.** Per the ticket's own Acceptance Criteria, this is a documentation-only decision record —
consistent with the sibling decisions in this same batch
(`docs/ai/default_packet_scenarios_decision.md`, `docs/ai/code_test_index_boundaries_decision.md`,
`docs/engine/contracts/context_packet_contract.md`), none of which added a test, since none of them
implement executable code. `docs/engine/contracts/context_packet_contract.md` §4 states explicitly
that "a future Phase 3 ticket that implements `ContextPacket` construction/serialization must add
its own `tests/`-path verification" — the same posture applies here: any test for actual
retention-duration *enforcement* or content-redaction *enforcement* belongs to the future Phase 3
ticket that implements the embedding/query-result/context-packet caches and retrieval-event writer,
not to this decision.

If the Plan phase decides a lightweight guard is nonetheless worth adding now (optional, not
required by the AC), the only candidate that would not overreach decision-doc scope is:

- **Test name:** `test_retrieval_retention_redaction_policy_doc_exists_and_has_frontmatter`
- **Category:** architecture guard / doc-hygiene (mirrors this repo's existing pattern of a thin
  doc-presence + frontmatter-validity check, not a content-semantics check)
- **What it verifies:** that the decision doc lands at its final chosen path, has valid frontmatter
  per `tools/validate_frontmatter.py` (status/layer/authority/audience all in their registries), and
  is discoverable by `docs/REGISTRY.yaml` after regeneration — the same low-bar check
  `done-checker`'s `frontmatter_valid` condition already performs generically for every ticket's
  staging artifacts, so this would be redundant with the Verify-phase gate rather than a new,
  independently-necessary test. **Recommendation: skip** — rely on the existing `done-checker`
  gate instead of adding a bespoke pytest for something the workflow already checks.
- **Where it would live:** N/A (recommended not to add).

## Scoped Pytest Commands

Regression-only, scoped to the two directly-affected modules (never `pytest tests/`):

```bash
pytest tests/unit/observability/test_retention_manager.py tests/unit/core/test_retention.py -v
```

No other scoped command is needed since no new test is being added and no other module is touched.

## Anti-Drift Test Guards

- **Re-running the regression surface above and diffing pass/fail counts against the pre-ticket
  baseline is itself the primary anti-drift guard** — if either `test_retention_manager.py` or
  `test_retention.py` fails after this ticket lands, that is direct proof the "decision-only, no
  code changes" acceptance criterion was violated, since nothing in this ticket's actual scope
  could plausibly change their outcome otherwise.
- **`git diff --stat` (or equivalent) restricted to `src/observability/reporting/retention.py`,
  `src/core/retention.py`, and `tools/agent-monitoring/*.py` should show zero changes** at Verify
  time — this is the direct, literal check for the ticket's own "no changes land in retention.py,
  core/retention.py, or any tools/agent-monitoring/*.py writer" acceptance criterion, and is a
  stronger guard than any pytest assertion could provide for a doc-only change.
- **The epic ticket's Open Decision 4 line must be updated to `RESOLVED`, and Decisions 1, 2, 3, 5,
  6 must be left exactly as they currently read** (1-3 already `RESOLVED` by sibling tickets, 5-6
  still open) — a diff of `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`
  that touches any Open Decision line other than 4 is a scope-creep signal, not a valid outcome of
  this ticket.
- **No `docs/parity_ledger/*.yaml` file should be touched** — investigation confirmed no P0/P1
  entry overlaps this scope; any parity-ledger diff accompanying this ticket's commit would itself
  be evidence of scope drift into simulation-mechanics territory this ticket does not touch.
- **No tag/layer registry addition should be needed** — this doc's frontmatter can reuse the
  ticket's own already-registered tags (`ai`, `observability`, `agent-monitoring`) and `layer: ai`;
  a diff to `docs/guidelines/tag_registry.jsonl` or `docs/guidelines/layer_registry.jsonl`
  accompanying this ticket would be an unexpected and unnecessary registry mutation for a
  decision-only doc that fits entirely within existing vocabulary.
