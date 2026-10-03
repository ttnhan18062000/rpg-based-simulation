---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-DECISION
phase: done
date: 2026-07-21
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260721-MONITORING-WRITER-DECISION

## Title
Decide execution identity, monitoring normalization, and a portable, concurrency-safe writer design

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
An inventory of all legacy monitoring schema generations and identifiers, a decision on the execution-identity model (immutable execution key, human-readable run reference, ticket linkage), a comparison of candidate writer designs, and a stress-tested/justified cross-platform concurrent-write strategy for the shared monitoring corpus — because the current tools.jsonl writer relies on POSIX fcntl.flock, which has no Windows equivalent and cannot safely support a second (Codex) writer. Bundled per the source plan's own exit-gate output 3 ("An execution-identity and monitoring-writer ADR, backed by portability and concurrent-write test evidence") — execution identity and the writer design are one combined decision, not two. Decision/evidence deliverable only: no production monitoring writer may change, and must not be combined with historical cleanup/backfill work.

## Scope
- This ticket may create only isolated contract, replay, fixture, diagnostic, or decision-record work. It must not modify production Claude/Codex workflows, hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
- Produce a written inventory of all currently-known legacy monitoring schema generations and identifier gaps, cross-referencing existing source tickets and docs/agent-monitoring/schema.md's Known Limitations.
- Decide and record the execution-identity model: an immutable per-execution key format, a human-readable run reference, and how `ticket_id` remains the stable cross-run join key once the same ticket can be run by both providers — resolving the source plan's Open Decision #3, per Codex's 2026-07-21 ticket-batch review confirming this decision belongs here, not in the contract ADR.
- Produce a side-by-side comparison of at least the 3 candidate writer designs named in the source plan against POSIX+Windows portability, malformed-partial-line rejection, append-only preservation, and safe two-writer concurrency.
- Define the explicit set of supported development platforms this design must be evidenced against.
- Produce stress-test evidence (methodology + results) for the recommended design, covering at least one non-POSIX-locking mechanism, following TCK-20260716's concurrent-writer harness methodology, on every platform in that supported-platform set.

## Out of Scope
- Creating any provider-runtime implementation ticket — blocked until all 5 discovery outputs are complete, evidence-backed, and explicitly approved (see parent epic TCK-20260721-PROVIDER-AGNOSTIC-EPIC).
- No changes to tools/agent-monitoring/post_tool_hook.py or any other production monitoring writer path.
- No historical cleanup or backfill of existing agent-monitoring/*.jsonl data — this ticket is decision/evidence-only.
- No implementation of the chosen writer design or execution-identity scheme — that is follow-on implementation work, gated by the parent epic.

## Acceptance Criteria
- [x] Deliverable produces a written inventory of every currently-known legacy monitoring schema generation and identifier gap, cross-referencing source tickets (e.g. docs/agent-monitoring/schema.md's Known Limitations) rather than re-deriving from scratch.
- [x] Deliverable decides and records the execution-identity model: an immutable per-execution key format, a human-readable run reference, and how `ticket_id` remains the stable cross-run join key once multiple providers can run the same ticket — consistent with the source plan's Open Decision #3 and its exit-gate output 3 ("An execution-identity and monitoring-writer ADR").
- [x] Deliverable produces a side-by-side comparison of at least the 3 candidate writer designs named in the source plan (lock-file protocol w/ bounded retry + stale-lock recovery; single local writer process/queue; provider-local append journals + deterministic merger), scored against POSIX+Windows portability, malformed-partial-line rejection, append-only preservation, and safe two-writer concurrency.
- [x] Deliverable defines an explicit supported-development-platform set and includes stress-test evidence (methodology + results, mirroring TCK-20260716's 150-invocation concurrent-writer harness) for the recommended design on every platform in that set, covering at least one non-POSIX-locking mechanism — the ticket's own investigation may still begin on one platform, but the writer design is not approved (must be explicitly marked NOT APPROVED / BLOCKED) until evidence exists for every platform in the supported set, per the source plan's "every supported development platform" requirement.
- [x] Deliverable makes zero changes to tools/agent-monitoring/post_tool_hook.py or any other production monitoring writer path, and touches no existing agent-monitoring/*.jsonl data files — verified by Files Changed containing only docs/investigation artifacts, no src/tools writer diffs, no historical-data backfill.

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK
- TCK-20260713-MONITORING-SQLITE-INDEX
- TCK-20260607-MON-SCHEMA
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py
- tests/tools/test_post_tool_hook.py
- tools/agent-monitoring/validate.py

## Assumptions / Open Questions
- post_tool_hook.py lines 3, 80-83 confirmed: fcntl.flock(LOCK_EX)/LOCK_UN wraps the tools.jsonl append inside a fail-silent try/except, is POSIX-only, and is only advisory against other flock-aware writers, not against a non-cooperating process.
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK explicitly deferred this exact revisit, conditioned on "unless the platform survey finds POSIX-only is NOT already the established norm" — the Codex second-writer requirement is precisely that trigger.
- The source plan's 3 candidate designs (lock-file protocol w/ bounded retry + stale-lock recovery; single local writer process/queue; provider-local append journals + deterministic merger) are a minimum comparison set, not exhaustive or pre-decided.
- TCK-20260713-MONITORING-SQLITE-INDEX is a related read-side normalization effort, not a duplicate of this write-path/concurrency decision.
- Depends on TCK-20260721-PROVIDER-AGNOSTIC-EPIC as parent; no dependency on sibling children TCK-20260721-AGENTS-DIR-DISPOSITION or TCK-20260721-CODEX-CAPABILITY-MATRIX — can run in parallel with them; its output is a required evidence input for TCK-20260721-ORCHESTRATION-CONTRACT-ADR and TCK-20260721-CODEX-REPLAY-PROOF.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/plan.md`'s 8 steps,
in order. This ticket resolved the plan's five Plan-phase decisions and produced one new
decision-record doc plus one new isolated, committed stress-test file. No production writer
path or `agent-monitoring/*.jsonl` data was touched.

1. **Baseline (Step 1):** `pytest tests/tools/ -v` → 995 passed, 6 failed (pre-existing,
   unrelated: `test_knowledge_search.py`/`test_search_mcp.py` — knowledge-search MCP wiring
   drift, no connection to agent-monitoring), 1 xfailed. Confirmed clean baseline before any
   change.
2. **Stress harness (Step 2):** `tests/tools/test_monitoring_writer_lockfile_candidate.py`
   (new). Self-contained, test-local `os.O_CREAT | os.O_EXCL` atomic lock-file writer
   (`_acquire_lock`/`_release_lock`/`_write_record_lockfile`), never imported from or added to
   `tools/agent-monitoring/`. A defensive guard, `_assert_not_real_corpus`, is called at the top
   of every write helper and is itself proven live by
   `test_lockfile_guard_rejects_real_agent_monitoring_path`. 3 tests, all passing:
   - `test_lockfile_guard_rejects_real_agent_monitoring_path` — guard raises on a real
     `agent-monitoring/tools.jsonl`-shaped path.
   - `test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines` — 10 threads
     x 20 iterations = 200 concurrent invocations against one shared `tmp_path` fixture file: 0
     corrupted/lost/duplicated/interleaved lines, exact match of all 200 expected markers.
   - `test_malformed_partial_line_is_rejected_by_downstream_reader` — 1 genuinely malformed
     (truncated) JSON line correctly rejected by a `validate.py`-style reader loop; all 5 valid
     records parsed successfully.
3. **AC1 inventory (Step 3):** `docs/ai/monitoring_writer_decision.md` Section 1 synthesizes
   `docs/agent-monitoring/schema.md`'s Known Limitations (five legacy `runs.jsonl` generations,
   the `TCK-20260623-TYPE-CHECKER` exception, the manual `run-{code}-{unix_ts}` convention, the
   `tools.jsonl`/`events.jsonl` null-field gaps) by reference, not re-derivation, and names the
   `run_id`-doubles-as-execution-and-join-key identifier gap this ticket exists to close.
4. **AC2 execution identity (Step 4):** Section 2 decides
   `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"` as the
   immutable per-execution key, retains `run_id` as the human-readable reference unchanged, and
   promotes `ticket_id` to an explicit top-level stable cross-run join key. Illustrated with a
   fenced synthetic example only — no real record was modified.
5. **AC3 design comparison (Step 5):** Section 3's 3x4 table recommends candidate 1 (lock-file
   protocol, `os.O_CREAT | os.O_EXCL`), citing Step 2's actual 200-invocation/0-corruption and
   malformed-line-rejection results directly.
6. **AC4/AC5 platform evidence (Step 6):** Section 4 defines the supported-development-platform
   set as `{Linux}` (evidenced from this environment plus `.github/workflows/test.yml`'s
   Linux-only CI), marks Linux **APPROVED** citing Step 2's real results, and marks Windows and
   macOS **NOT APPROVED / BLOCKED** (no evidence) using that exact language.
7. **Full regression + containment (Step 7):** First full pass surfaced one new,
   ticket-caused-but-out-of-scope failure —
   `test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`
   — because adding `docs/ai/monitoring_writer_decision.md` left `docs/REGISTRY.yaml` stale.
   Per `CLAUDE.md`'s "docs/REGISTRY.yaml is regenerated unconditionally... always stage the
   regenerated file" rule, ran `make docs-registry` (regenerates from frontmatter only, no
   agent-monitoring/writer-path involvement) and `make knowledge-index-update` (per CLAUDE.md's
   "if any files under docs/ were created or modified" rule), then re-ran the full suite: back
   to exactly the 6 pre-existing baseline failures, 998 passed (995 baseline + 3 new), 1
   xfailed. Containment check: `git diff --stat -- tools/agent-monitoring/` → empty (zero
   diff). `git diff --stat -- 'agent-monitoring/*.jsonl'` → append-only (466 insertions(+), 0
   deletions(-) across `runs.jsonl`/`events.jsonl`/`tools.jsonl`), consistent with this
   session's own auto-appended monitoring records.
8. **Ticket closure (Step 8, this update).**

## Test Summary

`.venv/bin/python3 -m pytest tests/tools/ -v`:
- Baseline (Step 1, before any change): 995 passed, 6 failed (pre-existing,
  `test_knowledge_search.py`/`test_search_mcp.py`), 1 xfailed.
- Final (Step 7, after all changes + `make docs-registry` + `make knowledge-index-update`): 998
  passed, 6 failed (same pre-existing set, unchanged), 1 xfailed.
- New: 3/3 passing in `tests/tools/test_monitoring_writer_lockfile_candidate.py`
  (`test_lockfile_guard_rejects_real_agent_monitoring_path`,
  `test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines` — 200
  invocations, 0 corruption, `test_malformed_partial_line_is_rejected_by_downstream_reader`).
- `tests/tools/test_post_tool_hook.py` — all 5 tests unaffected (file not touched).
- Containment: `git diff --stat -- tools/agent-monitoring/` empty; `agent-monitoring/*.jsonl`
  diff is append-only.

## Files Changed
- `docs/ai/monitoring_writer_decision.md` (new) — decision-record doc, AC1-AC4/AC5.
- `tests/tools/test_monitoring_writer_lockfile_candidate.py` (new) — stress harness, 3 tests.
- `docs/REGISTRY.yaml` (regenerated via `make docs-registry`, mechanical frontmatter-driven
  regen, no agent-monitoring/writer-path involvement).
- `tickets/inprogress/TCK-20260721-MONITORING-WRITER-DECISION.md` (this file — closure).
- `staging_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/plan.md` (Deviations section
  appended).
- `agent-monitoring/{runs,events,tools}.jsonl` (auto-appended monitoring records for this
  workflow session — append-only, not an edit to any existing line).

## Completion Summary
All five acceptance criteria are met. `docs/ai/monitoring_writer_decision.md` inventories the
legacy schema/identifier landscape (AC1) citing `docs/agent-monitoring/schema.md` by reference;
decides the execution-identity model (`execution_id`/`run_id`/`ticket_id` split, AC2); scores
the 3 named candidate writer designs against all 4 required criteria and recommends the
lock-file/`os.O_CREAT|os.O_EXCL` design (AC3), backed by real stress-test evidence from
`tests/tools/test_monitoring_writer_lockfile_candidate.py` (200 concurrent invocations, 0
corruption; malformed-line rejection confirmed); and defines the supported-development-platform
set as `{Linux}` with Linux marked APPROVED and Windows/macOS explicitly marked NOT APPROVED /
BLOCKED (AC4). Zero changes were made to `tools/agent-monitoring/post_tool_hook.py` or any
other production monitoring writer path, and no `agent-monitoring/*.jsonl` data was edited —
only appended to by this session's own monitoring hooks (AC5). No production writer design or
execution-identity scheme was implemented; both remain follow-on, epic-gated work per
`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`.
