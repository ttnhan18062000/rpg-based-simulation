---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY
phase: open
date: 2026-09-08
tags: [ai, mcp, governance]
---

# TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY

## Title
Monitor, then hard-delete, the archived Knowledge Gateway MCP (epic M2, steps 3-4)

## Status
BLOCKED

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` executed `TCK-20260907-KGMCP-DEPRECATION-EPIC`'s
M2 steps 1-2: it extracted the shared, load-bearing write-path-guard functions into
`tools/write_path_guard.py`, archived the remaining Knowledge Gateway MCP modules to
`tools/archive/` (`knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`,
`start_knowledge_gateway_mcp.sh`), archived their dedicated test files to `tests/archive/` (15
files, excluded from default collection via `pyproject.toml`'s `norecursedirs`), and deregistered
`.mcp.json`'s `knowledge-gateway` entry. This ticket executes the two remaining M2 steps that
could not happen in that same session:

1. **M2 step 3** — a 2-week zero-call monitoring window on the archived `tools/archive/` modules,
   confirming nothing outside this repo's own visibility still calls the archived gateway (the
   MCP registration is already gone from `.mcp.json`, so no Claude Code session can invoke it
   going forward; this window is a confirmation/blast-radius check, not a live risk-mitigation
   gate).
2. **M2 step 4** — once the window closes clean, hard-delete (not archive) the 6 files under
   `tools/archive/` and the 15 test files under `tests/archive/`, and remove the now-empty
   `norecursedirs` entry if nothing else uses `archive/` as a directory name by then (check first
   — `docs/archive`, `docs/plans/archive`, `scripts/archive` may still exist and are unrelated to
   this cleanup).

## Scope
- Confirm the 2-week zero-call window: re-run `grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ | grep -v '^tools/archive/\|^tests/archive/'` (widened from an earlier archived-path-only pattern, `tools/archive/knowledge_gateway\|tools\.archive\.knowledge_gateway`, per `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` — that narrower form only ever matched the NEW post-archival path form and would never have caught the 5 `tools/agent-monitoring/kgmcp_phase*_runner.py` scripts that hotfix found and archived, which referenced the OLD pre-archival path form, e.g. `tools/knowledge_gateway_mcp.py`. The bare `knowledge_gateway` stem, filtered to exclude self-references inside `tools/archive/`/`tests/archive/` themselves, catches both forms) across `tools/`, `src/`, `tests/`, `.claude/`, `docs/` (excluding the archived files' own self-references and this ticket's own history — plus historical doc/ticket prose citing the module by name, which is expected and not a live call site) to confirm zero new call sites appeared since `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` landed. Also confirm `agent-monitoring/` shows zero tool-call records referencing `mcp__knowledge-gateway__*` in the intervening window (the registration is already gone, so this should trivially hold, but confirm rather than assume).
- Hard-delete `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` and `tools/archive/start_knowledge_gateway_mcp.sh`.
- Hard-delete the 15 files under `tests/archive/` moved by `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (see that ticket's `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md` Step 8 for the exact 15-file list).
- Remove the `"archive"` entry from `pyproject.toml`'s `norecursedirs` if, at delete time, no other directory named `archive` still holds test files that need the exclusion (check `find tests -type d -iname archive` first — if `tests/archive/` itself is removed by this ticket and nothing else populates it, the exclusion is dead weight).
- Confirm `tools/write_path_guard.py` and its consumers (`tools/retrieval_cache.py`) are unaffected — this ticket deletes only the archived remainder, never the extracted, still-live module.
- Update `docs/parity_ledger/infrastructure.yaml`'s 21 entries this ticket's own predecessor annotated (INFRA-334, 335-339, 342-352, 354-357) to reflect the final delete — INFRA-342/343 in particular may need a `status` change (`verified` -> `missing` or similar) since their cited `v2_evidence`/`test_path` will no longer exist anywhere in the repo, archived or not, once this ticket lands. Follow this repo's Authoritative Mechanics Rule and use `tools/parity_ledger_writer.py`, never a raw `Edit`.

## Out of Scope
- Re-litigating the Option C re-ratification decision — already settled
  (`TCK-20260907-KGMCP-DEPRECATION-EPIC` M1, `keep_or_deprecate_decision.md` §4).
- Any change to `tools/write_path_guard.py` or its live consumers — this ticket only deletes the
  already-archived, already-dead remainder.
- Un-archiving anything — if the 2-week window surfaces a real, live, undiscovered consumer of the
  archived gateway, this ticket's own Definition of Done is blocked, not satisfied by deleting
  anyway; escalate instead (see Assumptions / Open Questions).
- A full `status: historical` frontmatter sweep of the wider
  `docs/engine/contracts/knowledge_gateway_mcp/` directory (10+ docs) — flagged by
  `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s own investigation as a separate, future
  follow-on, not this ticket's scope either.

## Acceptance Criteria
- [ ] The 2-week zero-call monitoring window (from `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s
      merge date) has genuinely elapsed before this ticket's Implement phase begins.
- [ ] A fresh repo-wide sweep confirms zero live call sites reference any `tools/archive/knowledge_gateway_*` module or `tools/archive/start_knowledge_gateway_mcp.sh`, outside their own archived files and historical doc/ticket text.
- [ ] `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` and `tools/archive/start_knowledge_gateway_mcp.sh` are hard-deleted.
- [ ] The 15 test files under `tests/archive/` (per the predecessor ticket's Step 8 list) are hard-deleted.
- [ ] `pyproject.toml`'s `norecursedirs` no longer carries a now-dead `"archive"` entry, unless something else still legitimately needs it.
- [ ] `tools/write_path_guard.py` and `tools/retrieval_cache.py` remain fully functional, confirmed via `pytest tests/tools/ tests/docs/ -v` passing in full.
- [ ] `docs/parity_ledger/infrastructure.yaml`'s 21 previously-annotated entries are updated to reflect the final delete, via `tools/parity_ledger_writer.py`.

## Related Tickets
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (done) — executed M2 steps 1-2; this ticket
  executes M2 steps 3-4, the direct predecessor whose archive locations (`tools/archive/`,
  `tests/archive/`) this ticket deletes.
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (`tickets/inprogress/`) — the parent epic this ticket
  completes (M2, final steps).
- `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` (done) — the original ratification, superseded by the
  epic's own M1 re-ratification.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (§1) — the
  original milestone spec, M2 steps 3-4.
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` (§4) — the
  re-ratification this ticket, and its predecessor, execute.
- `docs/parity_ledger/infrastructure.yaml` — the 21 entries
  (`stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md` Step 13 for the exact
  list and the lightweight-annotation vs. full-rewrite split) this ticket must revisit.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/` (once migrated from
  `staging_artifacts/`) — the predecessor's investigation/plan/test_plan, including the exact
  15-file test-archival list and the 6-file source-archival list this ticket deletes verbatim.

## Related Code Areas
- `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`
- `tools/archive/start_knowledge_gateway_mcp.sh`
- `tests/archive/` (15 files)
- `pyproject.toml` (`norecursedirs`)
- `docs/parity_ledger/infrastructure.yaml`

## Assumptions / Open Questions
- This ticket cannot start its Implement phase until the 2-week monitoring window has genuinely
  elapsed from `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s merge date — marked `BLOCKED`
  rather than `OPEN` for exactly this reason (a time-based precondition, not a missing-context
  block).
- If the monitoring window surfaces a real, live, undiscovered consumer of the archived gateway,
  this ticket's own Definition of Done cannot be satisfied by deleting anyway — escalate back to
  the parent epic for a scope decision (un-archive, fix the consumer, or explicitly accept the
  break) rather than silently proceeding.
- Whether `pyproject.toml`'s `"archive"` `norecursedirs` entry can be fully removed, or must stay
  for an unrelated reason, is not yet known — check at Implement time, not assumed here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
