---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-KGMCP-DEPRECATION-EPIC
phase: open
date: 2026-09-07
tags: [mcp, governance]
---

# TCK-20260907-KGMCP-DEPRECATION-EPIC

## Title
Re-ratify and execute Knowledge Gateway MCP (KGMCP) deprecation

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
`TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` ratified **Option A — keep as-is, no further
investment** on 2026-08-24 (`docs/engine/contracts/knowledge_gateway_mcp/
keep_or_deprecate_decision.md`), on the strength of Phase 4's 7/7 warm-path latency/token
losses and Phase 5's weak repeated-demand signal. That decision blocks
`standalone_items.md` §1's proposed removal (`roadmap.md` item 6 is currently marked
"BLOCKED, conflicts with TCK-20260824-KGMCP-KEEP-OR-DEPRECATE's ratified 'no changes
authorized'"). A month of real usage data since that ratification, plus fresh external
research, is new evidence Option A's own reviewer never had:

- Real corpus usage since 2026-08-24: **1 real content-retrieval call
  (`mcp__knowledge_gateway__knowledge_context`) in the project's entire recorded history**
  (2026-08-17, predating the ratification), against 2,259 real calls to the direct
  `search_docs` tool it sits alongside — a wider gap than the numbers Option A was
  ratified against, not a narrowing one.
- The gateway's tool-allowlist grant (`done-checker`, `test-scoper`) turned out to be an
  accident of `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`'s historical-usage-derived
  scoping, not a deliberate design choice — there is no considered rationale anywhere for
  keeping it available even to those two roles.
- External research (coding-assistant products — Cursor, Windsurf, Sourcegraph Cody,
  Aider, Devin/Cognition's own removal of an embeddings-based retrieval layer in favor of
  direct grep-style search — and real AI-first development practice — Anthropic's own
  internal Claude Code usage study, Sourcegraph/Amp, the Zup internal-agent case study,
  harness-engineering literature, spec-driven frameworks) found no example of a
  production or AI-first-development system building a live routing/caching context
  gateway in front of direct retrieval tools; the consistent, repeated pattern is direct
  tools plus routing guidance expressed as prompts/instructions (which this project
  already has, in CLAUDE.md's Proactive Tool Use table).
- The measured 1.31x-3.76x latency / 1.04x-2.93x token overhead (Phase 4, cold-cache) is
  the cost of routing + provider calls + packet assembly/redaction/provenance-wrapping —
  not of caching. Removing only the caching layer would not remove this overhead; the
  wrapping step itself is the source, confirmed by the fact the warm-cache re-comparison
  (`phase4_warm_direct_tool_comparison.md`) still lost on all 7/7 entries even with
  caching's benefit fully realized.

This epic scopes bringing that evidence back to the repository owner for re-ratification,
and — contingent entirely on that outcome — executing removal per `standalone_items.md`
§1's already-scoped 4-milestone plan. **Do not start this epic's work until the current
agent-working-implementer session's active work finishes** (explicit sequencing from the
repository owner, not a technical dependency).

## Scope
- **M1 — Re-ratification brief.** Produce a concise, evidence-grounded brief presenting
  the fresh evidence above (usage-gap widening, accidental allowlist, external research
  findings, the caching-vs-wrapping-overhead distinction) as a re-opening of
  `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE`'s decision, and take it to the repository owner
  for explicit re-ratification. This does not re-derive or re-run any KGMCP measurement
  corpus — it cites the existing Phase 3/4/5 evidence trail plus the new usage-count and
  external-research evidence gathered since. Record the outcome (re-affirm Option A, or
  move to Option C — deprecate) the same way the original decision ticket did: present,
  then record a human ratification, never an agent-chosen outcome.
- **M2 — If re-ratified toward deprecation, execute `standalone_items.md` §1's plan**
  (contingent, not committed until M1 resolves):
  1. Extract `scan_for_secrets()` from `knowledge_gateway_redaction.py` into a location
     independent of the gateway module (the cross-epic dependency
     `governance_capability_policy_epic.md`'s M4 needs regardless of KGMCP's own fate).
  2. Archive, don't hard-delete, the remaining gateway modules
     (`tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`,
     `tools/start_knowledge_gateway_mcp.sh`); remove the `.mcp.json` registration.
  3. Monitor for 2 weeks: confirm zero `mcp__knowledge-gateway__*` calls appear in
     `agent-monitoring/data/*/tools.jsonl` post-archival.
  4. Delete only after the monitoring window confirms no renewed calls.
- **M3 — If re-ratified to keep Option A (or a new Option B), close this epic** recording
  that outcome and update `roadmap.md` item 6 / `standalone_items.md` §1 accordingly — no
  code change in that branch.

Child tickets for M1 (and M2's 4 steps, if reached) are deliberately not created yet —
M2's real scope depends entirely on M1's outcome, matching this repo's own
"don't force premature child tickets before a gating decision resolves" precedent
(`TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s EPIC_SCOPED handling of its own
Bucket-B/C items).

## Out of Scope
- Choosing keep/deprecate unilaterally — same boundary `TCK-20260824-KGMCP-KEEP-OR-
  DEPRECATE` itself drew; this epic re-opens the question, it does not answer it.
- Any code change to `tools/knowledge_gateway_*.py` or `.mcp.json` before M1's
  re-ratification actually lands on Option C.
- Re-running any KGMCP measurement corpus or warm/cold comparison — M1 cites existing
  evidence plus the fresh usage-count/external-research evidence already gathered this
  session, it does not re-derive prior results.
- `governance_capability_policy_epic.md`'s M4 (Bash secret-exposure advisory hook) itself
  — M2 step 1 only extracts the shared dependency that ticket needs; wiring it into the
  hook is that epic's own scope, not this one's.

## Acceptance Criteria
- [ ] M1: a re-ratification brief is presented to the repository owner citing the fresh
      evidence (usage-gap, accidental allowlist, external research, caching-vs-wrapping
      distinction) without re-deriving prior measurements, and an explicit ratification
      (re-affirm Option A, or move to Option C) is recorded.
- [ ] M2 (contingent on M1 -> Option C): `scan_for_secrets()` is extracted and importable
      independent of the gateway; gateway modules are archived and deregistered from
      `.mcp.json`; a 2-week zero-call monitoring window is confirmed; the gateway is
      deleted.
- [ ] M3 (contingent on M1 -> keep): `roadmap.md` item 6 and `standalone_items.md` §1
      updated to reflect the re-affirmed decision; no code touched.

## Related Tickets
- `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` (done) — the decision this epic re-opens.
- `TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC`, `TCK-20260816-KGMCP-P4-DIRECT-TOOL-
  COMPARISON`, `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`, `TCK-20260816-KGMCP-P5-
  REPEATED-DEMAND-MEASUREMENT` — the underlying evidence trail, cited not re-derived.
- `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` — source of the accidental
  `done-checker`/`test-scoper` KGMCP allowlist grant cited in M1's evidence.
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` — precedent for epic-tier tickets not
  forcing premature child tickets before a gating decision resolves.

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` — the
  decision record being re-opened.
- `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md`,
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md` —
  the warm/cold comparison evidence.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (item 6),
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (§1) —
  the already-scoped removal plan this epic's M2 would execute.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  (M4) — the cross-epic dependency on `scan_for_secrets()`'s extraction.

## Related Stored Artifacts
None yet — epic tier, no direct implementation until M1/M2 child tickets are scoped.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
  `tools/knowledge_gateway_redaction.py`, `tools/start_knowledge_gateway_mcp.sh`
- `.mcp.json`
- `.claude/agents/done-checker.md`, `.claude/agents/test-scoper.md` (the current, accidental
  allowlist grant, resolved by whichever way M1/M2/M3 land)

## Assumptions / Open Questions
- Explicit sequencing constraint from the repository owner: do not begin M1 until the
  current agent-working-implementer session's active work finishes. Not a technical
  blocker — a deliberate scheduling choice to avoid concurrent-session contention.
- M1's brief should be genuinely concise (the repository owner explicitly prefers direct,
  evidence-led asks over long documents) — a short brief plus pointers to the existing
  evidence trail, not a new multi-section decision doc duplicating
  `keep_or_deprecate_decision.md`'s own shape.
- If M1 re-affirms Option A again, this epic still has value: it converts an assumption
  ("nothing's changed") into a dated, evidence-backed re-confirmation, and gives the
  accidental tool-allowlist question (M3) a real resolution either way.

## Implementation Notes
(filled in once M1 begins)

## Test Summary
(filled in once M2, if reached, has real changes to test)

## Files Changed
(filled in per-milestone)

## Completion Summary
(filled in at close)
