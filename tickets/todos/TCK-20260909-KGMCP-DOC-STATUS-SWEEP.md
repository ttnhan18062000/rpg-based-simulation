---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260909-KGMCP-DOC-STATUS-SWEEP
phase: open
date: 2026-09-09
tags: [mcp, documentation]
---

# TCK-20260909-KGMCP-DOC-STATUS-SWEEP

## Title
Resolve the deferred `status:` sweep of `docs/engine/contracts/knowledge_gateway_mcp/`

## Status
OPEN

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
- [ ] Each of the 12 `status: active` docs has been individually assessed and either changed to
      the correct status or explicitly justified as legitimately staying `active`.
- [ ] `redaction_retention_policy.md`'s still-live content (the `write_path_guard.py` policy now
      backing the live Bash secret-scan hook) is not wrongly retired — resolved by a split or an
      explicit scoped note, with the decision recorded.
- [ ] `docs/REGISTRY.yaml` regenerated and reflects the new statuses.
- [ ] `make knowledge-index-update` run so retrieval stops surfacing retired docs as live.
- [ ] `python3 tools/validate_frontmatter.py <each changed doc> --content-type doc` passes.

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
(filled in during implementation)

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
