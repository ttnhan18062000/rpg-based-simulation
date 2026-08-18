---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT

## Central Finding (read this first)

`changed_paths` is **already** a real, live, fully-wired, fully-tested caller-facing field. It is
not new work to build. Tracing the real code (not the ticket's framing) shows:

- `tools/knowledge_gateway_mcp.py:153` — `_run_knowledge_context()`'s real signature already has
  `changed_paths: Optional[list[str]] = None`.
- `tools/knowledge_gateway_mcp.py:167-168` — already threaded into the request dict
  (`if changed_paths is not None: request["changed_paths"] = changed_paths`).
- `tools/knowledge_gateway_mcp.py:491` — the registered `@server.tool() knowledge_context()` MCP
  wrapper already exposes `changed_paths: list[str] = None` and passes it straight through
  (`:511`).
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` — already
  declares `"changed_paths": {"type": "array", "items": {"type": "string"}}`, and
  `additionalProperties: false` already allow-lists it.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §9.1 — the conceptual input JSON example already
  shows `"changed_paths": ["src/observability/streams.py"]`.
- Integration point **(a)** (cache-validity revalidation) is already fully wired, both levels:
  - Level 1: `perform_cache_lookup()` (`tools/knowledge_gateway_cache.py:290-313`) reads
    `request.get("changed_paths", [])` at `:308` and passes it into `revalidate_cache_row()`
    (`:214-229`), which calls `working_tree_overlap_forces_revalidation()` (`:206-211`).
  - Level 2: `perform_context_packet_cache_lookup()` (`:496-529`) reads
    `request.get("changed_paths", [])` at `:524` and passes it into
    `revalidate_context_packet_row()` (`:249-283`), which also calls
    `working_tree_overlap_forces_revalidation()` (`:267-268`).
  - `working_tree_overlap_forces_revalidation()` itself (`:206-211`) never queries git — its own
    docstring is explicit: "`changed_paths` is read once by the caller from the validated request
    dict (DD11) and passed through unchanged — this function never re-queries git." So the "is a
    caller-supplied value redundant with an internal git-diff mechanism" branch of the ticket's own
    central question is answered: **no internal git-diff mechanism exists at all.**
    `changed_paths` is the gateway's *only* representation of "what changed" — confirmed
    independently by `tests/tools/fixtures/kgmcp_phase3_pilot_acceptance_measurement_results.json:38`:
    "changed_paths is the gateway's only representation of 'uncommitted changes' (no separate
    git-diff-based mechanism exists)."
- Real, already-passing, already-committed tests already prove this is genuine behavior, not
  accept-and-ignore:
  - `tests/tools/test_knowledge_gateway_mcp.py:820-834` —
    `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh` calls
    `_run_knowledge_context()` twice, once with `changed_paths=["docs/foo.md"]`, and asserts the
    second call is a real `MISS` (forced refresh) instead of a stale `HIT` — a genuine end-to-end
    behavior-change assertion at the exact public boundary this ticket's AC3 cares about.
  - `tests/tools/test_knowledge_gateway_cache.py:212` (`test_working_tree_fingerprint_uses_
    changed_paths_intersection_not_full_tree_hash`), `:515` (`test_revalidate_context_packet_row_
    rejects_on_changed_paths_intersection`), `:697-718` (spy proving `changed_paths` is passed
    through unmodified) — unit-level coverage of the same mechanism.
  - `tests/tools/test_knowledge_gateway_contract_schemas.py:179-180` and
    `tests/tools/test_evidence_cache_identity_contract.py:306-317` — schema/doc-parity coverage.

This work was built incidentally by the two prior tickets that needed a real `changed_paths` input
to implement evidence_cache_identity_contract.md §5 rule 3 (working-tree fingerprinting via
changed-paths intersection, never a full-tree hash):
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` (Level 1) and the Phase 3 Level 2 tickets
(`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` /
`TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION`). They added the field directly to the
schema/signature at that time because their own cache-validity logic structurally required it —
before this ticket existed to formally introduce it as a caller option.

## Real Gap: Routing Integration (b) Is a Genuine Conflict, Not Yet Resolved

Sibling ticket `TCK-20260816-KGMCP-P4-PARITY-ADAPTER` (DONE) explicitly deferred routing-path
integration to *this* ticket. Its own parity ledger entry, `docs/parity_ledger/infrastructure.yaml`
`INFRA-351`, `support_boundary` field, states verbatim: "`impact()`/`health()` and `changed_paths`
threading are explicitly out of this entry's scope
(`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`'s job)."

However, that same ticket also added a **committed anti-drift guard test** that locks the current
non-wiring in place:
`tests/tools/test_knowledge_gateway_router.py:486-489`
(`test_changed_path_impact_call_is_not_wired_by_this_ticket`) does AST inspection of
`_run_parity_provider()`'s real source body and asserts `"impact" not in called_attrs` and
`"changed_path" not in kwarg_names`.

`tools/parity_index.py:599` confirms `impact(changed_path=None, test_path=None, symbol=None,
db_path=None)` exists and remains genuinely unused anywhere in the repo — `_run_parity_provider()`
(`tools/knowledge_gateway_router.py:292-312`) calls only `entry()` (`:550`).

This is a real, load-bearing conflict, not a hypothetical one:
- Wiring `changed_paths` into routing (option b) — i.e. making `_run_parity_provider()` prefer
  `impact(changed_path=...)` over `entry()` when a `changed_paths` value is present and the query is
  parity/verification-shaped — necessarily means editing `_run_parity_provider()`'s real source
  body in `tools/knowledge_gateway_router.py`.
- This ticket's own **Out of Scope** section explicitly prohibits exactly that: "Any change to the
  Parity adapter itself (`TCK-20260816-KGMCP-P4-PARITY-ADAPTER`'s job) — this ticket may call into
  it once it exists, but does not build it."
- Doing so would also directly break the just-cited anti-drift guard test, requiring a deliberate,
  explicit rename/rewrite of a test another ticket wrote specifically to lock in the current
  boundary — not a silent side effect, but still a real scope collision between two sibling
  tickets' own stated boundaries.

Per the ticket's own explicit "Assumptions / Open Questions" instruction ("do not assume") and
CLAUDE.md's Clarification Rule ("conflict with existing system"), **this investigation does not
resolve this conflict** — it is flagged below as a blocking open question for Plan/human decision,
not silently built or silently skipped.

## Current Behavior

- `_run_knowledge_context()` (`tools/knowledge_gateway_mcp.py:149-172`): builds a request dict from
  only non-`None` supplied args (including `changed_paths`), validates against
  `REQUEST_VALIDATOR` (the frozen `knowledge_context_request.schema.json`), then routes
  (`_kgr.route(query)`), checks Level 2 cache (`perform_context_packet_cache_lookup`), then Level 1
  cache (`perform_cache_lookup`), then falls through to `assemble_packet()` on a genuine miss.
- `working_tree_overlap_forces_revalidation(evidence_paths_json, changed_paths)`
  (`tools/knowledge_gateway_cache.py:206-211`): pure set-intersection, `bool(evidence_paths &
  set(changed_paths))`. No git subprocess call. Stateless, deterministic.
- `revalidate_cache_row()` / `revalidate_context_packet_row()` both consult
  `working_tree_overlap_forces_revalidation()` first (§5 rule 3), before any
  provider-generation/fingerprint comparison (§5 rule 1/§4).
- `_run_parity_provider(query_text: str)` (`tools/knowledge_gateway_router.py:292-312`): calls only
  `tools.parity_index.entry(entry_id, db_path=...)`; takes no `changed_path`/`changed_paths`
  parameter today.

## Mechanics / Engine Constraints

This ticket is pure infrastructure/tooling (Knowledge Gateway MCP), not simulation mechanics — no
`docs/mechanics/` chapter applies. The governing constraints are the Knowledge Gateway MCP's own
engine contracts:
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5 rule 3 —
  "Working-tree fingerprinting uses changed-paths intersection, not whole-tree hashing" — already
  the authoritative, already-implemented law governing integration point (a). This document
  explicitly says it "references that field by name and does not redefine it" (the schema is the
  definition point), so no edit is needed there for (a).
- `docs/plans/knowledge-gateway-mcp-proposal.md` §9.1 — "Caller options express information needs,
  not routing internals... may accept a budget, optional changed paths, desired evidence detail,
  and history relevance." Already satisfied by the existing field; also states the public contract
  "must not expose provider weights, cache-level selection, semantic thresholds, provider forcing,
  or ranking-policy switches" — directly relevant to why routing-integration (b), if ever built,
  must stay need-oriented (e.g. "prefer parity evidence when paths changed") and never expose a raw
  provider-forcing switch.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: add a new entry (next id `INFRA-352`) recording this
  ticket's own finding — that `changed_paths` integration point (a) was already real, tested, and
  live before this ticket started, and that integration point (b) is a real, disclosed, deliberately
  unresolved conflict between this ticket's Out-of-Scope clause and sibling ticket `INFRA-351`'s
  `support_boundary` deferral — required by this ticket's AC4 regardless of whether new code lands.

No other doc requires a content change: the request schema, the proposal's §9.1 conceptual input,
and `evidence_cache_identity_contract.md` §5 already correctly and completely describe the
already-live behavior (verified above by direct read, not assumed).

## Parity Ledger Overlap

- `INFRA-341` (P2) — status `verified`, P1. Introduced `working_tree_overlap` column /
  `working_tree_overlap_forces_revalidation()` groundwork.
- `INFRA-343` (P2) — status `verified`, P1. `revalidate_cache_row()` end-to-end, cites
  `working_tree_overlap_forces_revalidation()` directly.
- `INFRA-348` (P3) — status `verified`, P1. `revalidate_context_packet_row()` reusing §5 primitives
  for Level 2, `test_revalidate_context_packet_row_rejects_on_changed_paths_intersection` cited as
  `test_path`-adjacent evidence.
- `INFRA-349` (P3) — status `verified`, P1. Level 2 read/write wiring into
  `_run_knowledge_context()`; cites `test_level2_hit_rejected_on_changed_paths_intersection_
  triggers_real_refresh` directly as one of its AC-mapped tests.
- `INFRA-351` (P4, sibling PARITY-ADAPTER, just closed DONE) — status `verified`, P1.
  `support_boundary` field explicitly names this ticket and explicitly defers `changed_paths`
  routing-threading to it, while `test_changed_path_impact_call_is_not_wired_by_this_ticket`
  (committed by that same ticket) locks the non-wiring in place. This is the entry this ticket must
  reconcile with (flagged above as an open question, not silently resolved).

None of these are flagged P0 in the ledger (all P1) — no P0 `test_path` gate applies here, but P1
entries still carry real regression weight, and `INFRA-341/343/348/349`'s cited `test_path`s all
still exist and were spot-checked to exist during this investigation (not just assumed from the
ledger text).

## Prior Work

- `stored_artifacts/TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING/` (if present) and
  `stored_artifacts/TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION/` — likely contain the
  original design rationale for adding `changed_paths` to the request schema; not required reading
  to act on this ticket since the resulting code/tests/docs were read directly and are more
  authoritative than a prior investigation's plan-stage reasoning.
- `stored_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/` — read via its parity ledger entry
  (`INFRA-351`) and its committed test file; directly relevant to the open routing-conflict question
  above.

## Risks and Open Questions

1. **Blocking open question (routing integration, option b):** Should this ticket build
   `changed_paths` → `impact(changed_path=...)` routing preference at all? Building it requires
   editing `_run_parity_provider()`'s real body, which:
   - conflicts with this ticket's own Out-of-Scope clause ("Any change to the Parity adapter
     itself... this ticket does not build it"), and
   - would break the committed anti-drift test
     `tests/tools/test_knowledge_gateway_router.py::test_changed_path_impact_call_is_not_wired_by_this_ticket`,
     requiring an explicit, deliberate rewrite of another ticket's guard test.
   This investigation does **not** assume an answer. Recommend Plan phase either (i) scope this
   ticket down to formalizing/documenting integration point (a) only — already real and already
   tested — plus the AC4 parity-ledger entry, and explicitly declining (b)/(c) with reasoning
   (matching the ticket's own explicit permission to scope down), or (ii) if a human/planner
   decides (b) is actually wanted now, treat that as an explicit scope amendment to both this
   ticket's Out-of-Scope section and to `INFRA-351`'s locked-in test, not a default.
2. **AC "genuinely changes behavior" risk if new code is written for its own sake:** because (a) is
   already fully live and tested, there is a real risk of Implement writing *redundant* code (e.g.
   a second, parallel `changed_paths` plumbing path) purely to make the ticket "feel implemented."
   Per CLAUDE.md's hard rule against gate-gaming, Implement should resist this — the honest,
   substantive remaining work is documentation (parity ledger entry) plus the open-question
   resolution above, not manufactured code.
3. **`impact()` staying unused is itself intentional** per the sibling ticket's own committed test —
   any future ticket that does wire it must explicitly update/replace that test, not work around it.

## Anti-Drift Hazards

- Do not add a second, parallel `changed_paths`-reading code path in `_run_knowledge_context()` or
  the cache module "to prove AC1/AC3" — the real, already-tested path
  (`request["changed_paths"]` → `perform_cache_lookup`/`perform_context_packet_cache_lookup` →
  `revalidate_cache_row`/`revalidate_context_packet_row` →
  `working_tree_overlap_forces_revalidation`) already satisfies both.
- Do not silently edit `_run_parity_provider()` to wire in `impact(changed_path=...)` without
  first getting an explicit decision on the open question above — doing so both violates this
  ticket's own Out-of-Scope text and breaks a named, committed anti-drift test from a sibling
  ticket.
- Do not treat `INFRA-351`'s `support_boundary` deferral text as a mandate that overrides this
  ticket's own Scope/Out-of-Scope sections — two sibling tickets' texts genuinely disagree here;
  this ticket's own frontmatter/body is the authoritative scope document for its own Implement
  phase.
- Do not "fix" `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5
  or the request schema — both are correct and current already; editing them without a real
  behavior change would be documentation drift in the wrong direction.
