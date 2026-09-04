---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-04
tags: [ai, agent-monitoring, data-quality]
---

# Standalone Items — Horizon 0 &amp; Horizon 2

**Tracking ticket**: not yet created (planning stage — detail plan and milestones only).
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, Bucket A inventory rows marked
`epic: standalone` — each carries independent value and independent rollback, so grouping them
into a bigger epic would only add coordination overhead with no shared component to justify it
(§71's separation criteria). Grouped into one doc here purely for planning-doc convenience — they
remain four independent units of work, not one epic.
**Roadmap**: `roadmap.md` — one Horizon-0 item, three Horizon-2 items.

## 1. Remove/archive knowledge-gateway (Horizon 0 — start now)

**Priority**: P0 — Measured Inefficiency motivation, Level A evidence (2 real MCP calls ever vs.
2,138 calls to the direct tool it wraps).

**Problem**: `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` (3,036
lines across 5 modules) is registered as a live MCP server in `.mcp.json` but is, by real usage
data, dead infrastructure.

**Milestones**:
1. **Extract `scan_for_secrets()`** out of `knowledge_gateway_redaction.py` into a location
   independent of the gateway module — this is the cross-epic dependency
   `governance_capability_policy_epic.md`'s M4 needs (see `roadmap.md`). Do this step first,
   regardless of which of the two dependents lands first.
2. **Archive, don't hard-delete**, the remaining gateway modules — move to an archive location,
   remove the `.mcp.json` registration.
3. **Monitor for 2 weeks**: confirm zero `mcp__knowledge-gateway__*` calls appear in
   `agent-monitoring/tools.jsonl` post-archival.
4. **Delete** only after the monitoring window confirms no renewed calls.

**Acceptance signal**: `scan_for_secrets()` is importable from its new location and used by
`governance_capability_policy_epic.md`'s M4; the gateway module is archived, deregistered, and
(after the monitoring window) deleted; zero regressions in any tool that legitimately depended on
the gateway (none currently known, per the usage data — this step exists to catch an
undiscovered consumer, not an expected one).

## 2. Extend cost_proxy_score to implement-epic.js / create-tickets.js (Horizon 2 — ready, schedule later)

**Priority**: P2 — Preventive Hardening motivation, Level B evidence.

**Problem**: only `implement-ticket.js` emits `cost_proxy_score`/`tool_call_count` into
`agent-monitoring/`; `implement-epic.js` and `create-tickets.js` report `null` for both fields
(`docs/agent-monitoring/schema.md`).

**Milestone**: wire the existing `tools/agent-monitoring/cost_proxy.py` computation into the two
workflows' event-recording call sites — the same computation, two more call sites, no new logic.

**Acceptance signal**: all three workflows show non-null `cost_proxy_score` in `runs.jsonl` after
their next real run.

## 3. working_log.csv parser and cleanup (Horizon 2 — ready, schedule later)

**Priority**: P2 — Known Structural Risk motivation, Level A evidence (real, confirmed data-
quality problems: unescaped commas in free-text `summary` fields corrupt column alignment for a
visible subset of the file's 3,300 rows).

**Problem**: `tickets/working_log.csv` cannot currently support any automated rework-rate or
reopened-ticket signal — grep-level analysis over it is unreliable, confirmed this session.

**Milestone**: write a proper CSV parser (handling the existing malformed rows) or migrate the
file to a stricter quoted-field format going forward — either resolves the same underlying
problem; which one is an implementation-time choice, not fixed here.

**Explicit constraint, added during planning discussion**: this mirrors the same principle applied
to `tools.jsonl` in `telemetry_retention_epic.md` — parsing repair must not become historical
reinterpretation. Existing rows are parsed as faithfully as possible; ambiguous/unparseable rows
are marked explicitly, never silently "corrected" or reinterpreted. Only future writes get the
stricter schema. If a fully normalized, query-friendly view is genuinely needed, it should be a
derived representation alongside the original (e.g. a separate normalized file), not an in-place
rewrite of historical rows.

**Acceptance signal**: a round-trip parse of the full file recovers every row without ambiguity;
this unblocks (but does not itself perform) any future rework-rate analysis referenced elsewhere
in the frozen proposal.

## 4. Provider-portability conformance test (Horizon 2 — ready, schedule later)

**Priority**: P2 — Preventive Hardening motivation, Level D evidence (the ADR itself names this
test as "proposed-pending-implementation-evidence" — a documented, not yet built, gap).

**Problem**: `docs/architecture/agent_orchestration_contract.md`'s Provider-Adapter Boundary ADR
requires `.claude/` and `.codex/` to stay "thin" translations of the shared
`agent-orchestration/` contract — but no test currently verifies that constraint holds; it's
enforced only at the field-name level (`tools/retrieval_event_parity_check.py` bans
provider-specific field names in the shared schema).

**Milestone**: write a test diffing `.claude/agents/*.md` phase/status/gate definitions and
`.codex/config.toml`'s translated equivalents against the canonical `agent-orchestration/`
contract — the ADR's own spec for what this test should check.

**Acceptance signal**: the test exists, passes against current `.claude/`/`.codex/` state, and
fails against a deliberately introduced adapter/contract mismatch (a real before/after check, not
just a passing test with no proof it can catch the thing it's meant to catch).

## References

- `roadmap.md` — placement of each item across Horizon 0/2, and the shared dependency note for
  item 1.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — Change Inventory rows for all four items.
- `docs/architecture/agent_orchestration_contract.md` — source ADR for item 4.
