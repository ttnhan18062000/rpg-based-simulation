---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION
phase: done
date: 2026-08-15
tags: [ai, mcp, process-improvement]
---

# TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION

## Title
Record the human reviewer's ratification of proposal §24 items 1 and 4, closing the last two
pending Phase 0 checklist items for the knowledge-gateway-mcp epic

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 0 checklist had 8 of 10 items marked
Done and 2 marked "Drafted / pending ratification": the cached-payload redaction/retention policy
(`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`, gated on §24 item 1)
and the token-counting method (same document §8, gated on §24 item 4). Both require an explicit
human reviewer ruling per `TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC`'s own Acceptance Criteria — no
agent may unilaterally decide them.

The user, acting as the reviewer, was presented both decisions with their concrete drafted content
(allowlist scope, redaction rules, size cap, secret-scan baseline and its explicit
non-production-complete disclosure, never-cache list for item 1; `kgmcp_char_heuristic_v1` =
`ceil(utf8_bytes/4)` with documented ±20% tolerance, chosen to avoid a new tokenizer dependency, for
item 4) on 2026-08-15 and ratified both as drafted, with no changes to the drafted content.

This ticket records that ratification in the authoritative documents — it does not re-derive or
second-guess the decision, and it does not begin any Phase 1+/Phase 2 implementation work
(explicitly out of scope: this is a paperwork-closing ticket only).

## Scope
- Update `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §11
  ("Ratification Status") to record: ratified by the user (repository owner acting as reviewer) on
  2026-08-15, as drafted, no changes. Phase 2 payload caching remains unimplemented — ratification
  authorizes future implementation to proceed against this policy, it does not itself implement
  anything.
- Update the same document's §8 ("Token-Counting Method") to add a ratification note for §24 item 4
  (approved as drafted on 2026-08-15).
- Update `docs/plans/knowledge-gateway-mcp-proposal.md` §24 "Open Decisions Requiring Explicit
  Review": mark items 1 and 4 as ratified (with date and outcome), leave items 2/3/5/6 unresolved
  exactly as before.
- Update the same document's §20 Phase 0 checklist: change the 2 "Drafted / pending ratification"
  bullets ("Ratify the cached-payload redaction and retention policy", "Define a reproducible
  token-counting method...") to "**Done (ratified 2026-08-15)**", citing this ticket.
- Re-run `docs_to_update`/frontmatter checks on both edited docs.

## Out of Scope
- Any Phase 1+ or Phase 2 implementation (routing, MCP tool exposure, actual cache payload
  read/write code, a real secret-scanning module, a real `kgmcp_char_heuristic_v1` callable).
- Re-litigating §24 items 2, 3, 5, 6 — still open, untouched by this ticket.
- Closing the `TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC` ticket itself — that is a separate step
  taken only after this ticket lands and the epic's remaining Acceptance Criteria are re-checked.

## Acceptance Criteria
- [ ] `redaction_retention_policy.md` §11 records the ratification (who, when, outcome) without
      altering the substance of §2-§10's drafted rules.
- [ ] `redaction_retention_policy.md` §8 records item 4's ratification.
- [ ] `knowledge-gateway-mcp-proposal.md` §24 items 1 and 4 marked ratified with date/outcome; items
      2/3/5/6 unchanged.
- [ ] `knowledge-gateway-mcp-proposal.md` §20's 2 previously-pending bullets now read Done, citing
      this ticket.
- [ ] No Phase 1+/Phase 2 code is added by this ticket.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent epic; this ticket clears its AC5 ratification gap)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (DONE; drafted the policy this ticket ratifies)
- TCK-20260814-KGMCP-MEASUREMENT-BASELINE (DONE; cites `kgmcp_char_heuristic_v1` as a token-count
  precedent)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20, §24

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
None — pure documentation ticket, no code changes.

## Assumptions / Open Questions
None — the ratification decision itself was made by the user directly; this ticket only records it.

## Implementation Notes
Recorded the user's 2026-08-15 ratification decision (both items approved as drafted, no content
changes) in the authoritative documents:
- `redaction_retention_policy.md` §11 rewritten from "drafted, not ratified" to "Ratified as
  drafted", naming this ticket, and explicitly preserving the still-standing requirement that the
  §4 secret-scan baseline gets a dedicated security pass before Phase 2 ships.
- Same doc §8 gained a short ratification note for §24 item 4.
- `knowledge-gateway-mcp-proposal.md` §24 items 1 and 4 marked ratified with date/ticket; items 2,
  3, 5, 6 left untouched.
- `knowledge-gateway-mcp-proposal.md` §20's 2 pending bullets changed to "Done (ratified
  2026-08-15)".
- `measurement_baseline_contract.md`'s cross-reference to the redaction policy (a stale "drafted,
  not ratified" citation) corrected for accuracy — incidental, not part of this ticket's own scope
  bullets but directly caused by the substance change above.

Two test-scoped discoveries, fixed as part of this ticket (both trivial, zero-risk, directly caused
by this ticket's own substance change or a pre-existing latent path bug surfaced while re-running
this area's tests):
1. `tests/docs/test_redaction_retention_policy_doc.py::test_policy_doc_explicitly_flags_ratification_pending`
   asserted the pre-ratification "drafted, not ratified" string — genuinely stale now, since the
   real state changed. Renamed to `test_policy_doc_explicitly_flags_ratification_status` and
   updated to assert the new "Ratified as drafted" text, this ticket ID, and the "no changes to
   §2-§10" language — the property under test (doc's ratification section matches real status) is
   unchanged, only the real status changed.
2. `tests/tools/test_kgmcp_measurement_baseline.py`'s `_INVESTIGATION_MD` path pointed at
   `staging_artifacts/TCK-20260814-KGMCP-MEASUREMENT-BASELINE/investigation.md` — a pre-existing
   latent bug from that ticket's own Finalize phase (which correctly moved staging_artifacts to
   stored_artifacts, but nothing re-ran that ticket's tests afterward to catch the now-broken
   path). Fixed the path to `stored_artifacts/...`. Unrelated to this ticket's own ratification
   substance; fixed because it was discovered while re-running this area's full test surface and is
   an obviously-correct, zero-risk path fix.

## Test Summary
`.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py
tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_knowledge_gateway_contract_schemas.py
tests/tools/test_evidence_cache_identity_contract.py tests/docs/test_prescan_mandate_instruction_draft.py -q`
→ 72 passed, 0 failed. `python3 tools/validate_frontmatter.py` passed for both edited docs and the
ticket file.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (§8, §11 ratification
  recorded)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (§20, §24 ratification recorded)
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` (stale
  cross-reference corrected)
- `tests/docs/test_redaction_retention_policy_doc.py` (test renamed/updated to match ratified
  state)
- `tests/tools/test_kgmcp_measurement_baseline.py` (stale `staging_artifacts` path fixed to
  `stored_artifacts`)
- `tickets/inprogress/TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION.md` (this file)

## Completion Summary
Recorded the user's ratification of Knowledge Gateway MCP proposal §24 items 1 (cached-payload
redaction/retention policy) and 4 (token-counting method), both approved as drafted with zero
content changes, closing the last 2 pending items of Phase 0's §20 checklist. Also fixed a stale
test assertion and a stale test fixture path discovered while verifying. No Phase 1+/Phase 2 code
was added.
