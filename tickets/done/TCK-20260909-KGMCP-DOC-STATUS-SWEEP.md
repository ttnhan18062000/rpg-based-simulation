---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260909-KGMCP-DOC-STATUS-SWEEP
phase: done
date: 2026-09-09
tags: [mcp, documentation]
---

# TCK-20260909-KGMCP-DOC-STATUS-SWEEP

## Title
Resolve the deferred `status:` sweep of `docs/engine/contracts/knowledge_gateway_mcp/`

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Both KGMCP deprecation-execution tickets explicitly deferred the same item to "a separate,
future follow-on" — and that follow-on was never actually filed. `TCK-20260908-KGMCP-DELETE-
ARCHIVED-GATEWAY`'s own Out of Scope says it verbatim:

> "A full `status: historical` frontmatter sweep of the wider
> `docs/engine/contracts/knowledge_gateway_mcp/` directory (10+ docs) — flagged by
> `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s own investigation as a separate, future
> follow-on, not this ticket's scope either."

Confirmed live against `main` (2026-09-09): **12 docs under that directory are still
`status: active`** in `docs/REGISTRY.yaml`, describing an MCP server that is archived,
deregistered from `.mcp.json`, and scheduled for hard-deletion. Only
`keep_or_deprecate_decision.md` is already `historical`. Until this is fixed, `search_docs`
and the registry keep surfacing them as live, authoritative guidance for infrastructure that
no longer exists.

This is **not** gated on `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s 2-week monitoring
window — the docs describe already-archived infrastructure regardless of when the files are
hard-deleted, so this can proceed immediately and independently.

## Scope
- Assess each of the 12 still-`active` docs individually and set the correct `status:` — this
  is a per-doc judgment call, **not** a blanket find-and-replace to `historical`. Known
  starting analysis (verify each rather than trusting this list):
  - **Clearly historical** (pure measurement/phase records for a now-dead system):
    `phase1_baseline_comparison.md`, `phase2_baseline_recomparison.md`,
    `phase3_pilot_acceptance_measurement.md`, `phase4_direct_tool_comparison.md`,
    `phase4_warm_direct_tool_comparison.md`, `phase4_workflow_recommendation.md`,
    `phase5_repeated_demand_measurement.md`, `measurement_baseline_contract.md`.
  - **Likely historical, but confirm** (describe archived internals):
    `cache_migration_plan.md`, `evidence_cache_identity_contract.md`.
  - **Judgment call**: `audit_phase0_5.md` — it is the consolidated evidence record the
    re-ratification cites, so it retains reference value even though its subject is dead.
  - **Do NOT blanket-mark historical**: `redaction_retention_policy.md` documents the policy
    behind `scan_for_secrets()`/`check_allowlist()`/`check_size_cap()` and friends, which
    **survived the archival** into the live `tools/write_path_guard.py` and are now wired into
    a live `PreToolUse` Bash hook (`TCK-20260904-BASH-SECRET-SCAN-HOOK`). Part of this doc
    describes live behavior; marking the whole file historical would wrongly retire policy that
    is still in force. Resolve by splitting the still-live policy content out, or by an
    explicit scoped note — decide during Investigate, don't assume.
- Regenerate `docs/REGISTRY.yaml` and confirm the sweep is reflected.
- Run `make knowledge-index-update` so `search_docs` stops ranking retired docs as live
  guidance (this is the actual user-visible symptom motivating the ticket).

## Out of Scope
- Deleting any of these docs — they stay as historical record; only `status:` (and, for
  `redaction_retention_policy.md`, possibly content organization) changes.
- Anything in `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s scope (the hard-delete of
  `tools/archive/`, the parity-entry finalization, the `norecursedirs` cleanup) — that ticket
  remains independently blocked on its own monitoring window.
- The `.json` schema files in the same directory — they carry no frontmatter and are not
  registry-indexed, so they are unaffected by a `status:` sweep.
- Re-litigating the Option C deprecation decision — settled.

## Acceptance Criteria
- [x] Each of the 12 `status: active` docs has been individually assessed and either changed to
      the correct status or explicitly justified as legitimately staying `active`.
- [x] `redaction_retention_policy.md`'s still-live content (the `write_path_guard.py` policy now
      backing the live Bash secret-scan hook) is not wrongly retired — resolved by a split or an
      explicit scoped note, with the decision recorded.
- [x] `docs/REGISTRY.yaml` regenerated and reflects the new statuses.
- [x] `make knowledge-index-update` run so retrieval stops surfacing retired docs as live.
- [x] `python3 tools/validate_frontmatter.py <each changed doc> --content-type doc` passes.

## Related Tickets
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` — deferred this sweep in its own Out of Scope.
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` — its investigation originally flagged the
  sweep as a future follow-on; also the ticket that moved `scan_for_secrets()` into
  `tools/write_path_guard.py`, creating the `redaction_retention_policy.md` nuance above.
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` — parent epic.
- `TCK-20260904-BASH-SECRET-SCAN-HOOK` — the live consumer of the policy that must not be
  retired.

## Related Docs
- All 13 markdown files under `docs/engine/contracts/knowledge_gateway_mcp/`.
- `docs/REGISTRY.yaml`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/engine/contracts/knowledge_gateway_mcp/`
- `tools/generate_registry.py` (registry regeneration)
- `tools/write_path_guard.py` (the surviving live module the policy doc partly describes)

## Assumptions / Open Questions
- The 12/13 split was verified live against `origin/main` on 2026-09-09 via `docs/REGISTRY.yaml`;
  re-verify at Investigate rather than trusting this count, since other sessions may land
  changes in the interim.
- Whether `audit_phase0_5.md` should stay `active` as an evidence record or become `historical`
  is a genuine judgment call, not a foregone conclusion — decide it explicitly and record the
  reasoning rather than defaulting either way.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260909-KGMCP-DOC-STATUS-SWEEP/plan.md`'s 7 steps,
no deviations:

1. Flipped line 2 `status: active` → `status: historical` (single-line edit via `sed`, then
   verified with `git diff` per file) in the 11 files named in Scope: the 8 phase/measurement
   docs, `cache_migration_plan.md`, `evidence_cache_identity_contract.md`, and `audit_phase0_5.md`.
   `git diff --stat` confirmed exactly 11 files, 1 line each, no other content touched.
2. Inserted the plan's exact draft scoped-status note into `redaction_retention_policy.md`,
   verbatim, between the intro paragraph and `## 1. Purpose`. Line 2 (`status: active`) confirmed
   unchanged; `git diff` confirmed the change is a pure 15-line insertion with zero deletions.
3. Ran `make docs-registry`; regenerated `docs/REGISTRY.yaml` (2302 entries). Spot-checked via a
   small Python script that `phase1_baseline_comparison.md`, `cache_migration_plan.md`,
   `audit_phase0_5.md` now read `status: historical`, `redaction_retention_policy.md` and
   `keep_or_deprecate_decision.md` are unaffected/already-correct. `git diff --stat` on
   `docs/REGISTRY.yaml` showed exactly 11 status-field diffs plus the `# Generated:` timestamp
   comment line — no unrelated entries drifted.
4. Ran `make knowledge-index-update` — exit 0, "Incremental update: 12 files changed/new" (the 11
   flipped docs + `redaction_retention_policy.md`'s content addition), 3496 unchanged from cache.
5. Ran `validate_frontmatter.py` over the whole `knowledge_gateway_mcp/` directory — `OK: 13
   file(s) checked — no violations`, confirming zero collateral damage to
   `keep_or_deprecate_decision.md` or the excluded `.json` schema files.
6. Ran `tests/docs/test_redaction_retention_policy_doc.py` unmodified — all 7 tests passed
   (test_plan.md's own Investigate-time note already flagged 7, not the ticket's originally-cited
   6, as the live count; no test file edits were made).
7. Ran `tests/tools/test_generate_registry.py` + `tests/tools/test_validate_frontmatter.py`
   (144 passed) and `tests/tools/test_write_path_guard.py -m "not slow"` (54 passed), confirming
   zero code drift in `tools/write_path_guard.py`, `tools/generate_registry.py`, or
   `tools/validate_frontmatter.py`.

Final `git diff --stat` confirmed the entire changeset touches only the 11 flipped docs, the one
additive doc, `docs/REGISTRY.yaml`, and `agent-monitoring/`/ticket-lifecycle files — no diff in
`docs/engine/contracts/knowledge_gateway_mcp_contract.md`, any `.json` schema file, or any file
under `tools/`/`src/`. No deviations from `plan.md` were required.

## Test Summary
- `pytest tests/docs/test_redaction_retention_policy_doc.py -v` — 7 passed (unmodified test file).
- `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -v` —
  144 passed.
- `pytest tests/tools/test_write_path_guard.py -v -m "not slow"` — 54 passed.
- `python3 tools/validate_frontmatter.py docs/engine/contracts/knowledge_gateway_mcp/
  --content-type doc` — `OK: 13 file(s) checked — no violations`.
- `make knowledge-index-update` — exit 0, 12 files re-embedded as expected.
- `make docs-registry` — exit 0, regenerated cleanly, spot-checked statuses correct.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md` — `status:` → historical
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — additive scoped-status note inserted; `status:` unchanged (`active`)
- `docs/REGISTRY.yaml` — regenerated via `make docs-registry`
- `tickets/inprogress/TCK-20260909-KGMCP-DOC-STATUS-SWEEP.md` — this ticket (Scope-phase move from `tickets/todos/`, and this Implement-phase update)
- `staging_artifacts/TCK-20260909-KGMCP-DOC-STATUS-SWEEP/investigation.md` — created during this run's Investigate phase
- `staging_artifacts/TCK-20260909-KGMCP-DOC-STATUS-SWEEP/plan.md` — created during this run's Plan phase
- `staging_artifacts/TCK-20260909-KGMCP-DOC-STATUS-SWEEP/test_plan.md` — created during this run's Investigate/Plan phase
- `agent-monitoring/data/2026-W37/tools.jsonl` — auto-updated by the monitoring hook on tool calls

## Completion Summary
Swept `docs/engine/contracts/knowledge_gateway_mcp/`'s stale `status: active` frontmatter: 11 docs
(8 phase/measurement records, the cache-migration and evidence-cache-identity design contracts,
and the consolidated `audit_phase0_5.md`) were flipped to `status: historical` since they describe
a now-archived gateway with no live consumer. `redaction_retention_policy.md` was deliberately left
`status: active` (its §2-§7 + partial §9 content backs the live `tools/write_path_guard.py` module
and the live `PreToolUse:Bash` secret-scan hook) and instead received an additive scoped-status note
distinguishing its still-live sections from its historical ones — a physical file split was
evaluated and rejected per investigation.md's precedent/regression-risk reasoning.
`docs/REGISTRY.yaml` was regenerated and the knowledge-search index rebuilt so retrieval stops
surfacing the retired docs as live guidance. All scoped tests (7 + 144 + 54) pass, with
`tests/docs/test_redaction_retention_policy_doc.py` confirmed unmodified.
