---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260728-CONTEXT-PACKET-SCHEMA
artifact_type: test_plan
tags: [ai, registry, schema]
---

# Test Plan — TCK-20260728-CONTEXT-PACKET-SCHEMA

## Regression Surface

This ticket produces exactly one new file, `docs/engine/contracts/context_packet_contract.md`
(doc-only, `content_type: doc`), plus edits to the ticket body and the epic's Assumptions/Open
Questions section. No `src/`, `tools/`, or existing-doc *behavior* changes. The regression surface
is therefore narrow: confirm the frontmatter/registry tooling that will process the new file still
behaves correctly, and confirm no doc/tooling that already depends on `docs/REGISTRY.yaml`'s
enum shapes is disturbed.

**Unit**
- `tests/tools/test_validate_frontmatter.py` — must keep passing; specifically exercises
  `_validate_doc`'s required-field/enum checks (`status`, `layer`, `authority`, `audience`) that
  the new doc's frontmatter must satisfy, and `detect_content_type`'s path-based inference
  (`docs/engine/contracts/...` → `content_type: doc`, since `engine` is not in
  `{archive, superpowers, specs}`).
- `tests/tools/test_generate_registry.py` — must keep passing; covers `collect_docs()`'s
  frontmatter-to-entry mapping (`status`/`layer`/`authority`/`audience`/`tags`/`last_verified`)
  that will pick up the new doc on the next `make docs-registry` run, and `_SKIP_DOC_SUBDIRS`
  behavior (confirms `docs/parity_ledger/` continues to be excluded — relevant since this ticket's
  resolution of Open Decision 3 explicitly discusses that exclusion).
- `tests/tools/test_registry_query.py` — indirect regression check: confirms `related_code_areas`/
  `tags`-based filtering (used by future agents to discover this new contract doc) is unaffected by
  adding one more `type: doc` entry to the registry.
- `tests/tools/test_layer_registry.py` (if present) / `tools/layer_registry.py list` — confirms
  `layer: ai` remains a registered value the new doc can legally use.
- `tests/tools/test_tag_registry.py` (if present) / `tools/tag_registry.py list` — confirms
  `ai`, `registry`, `schema` remain registered tags (process discipline; note `_validate_doc` does
  not itself call `_check_tags`, so this is a belt-and-suspenders check, not a hard gate for this
  particular file per the investigation's Anti-Drift Hazards).

**Integration**
- None applicable — no `src/` behavior changed, no cross-subsystem call path touched.

**Arena-combat**
- Not applicable — this ticket is entirely outside combat/simulation domains.

## New Tests Required

This is a documentation-only ticket (no `src/`/`tools/` implementation of `ContextPacket`
construction/serialization is in scope, per the ticket's own Out of Scope). Per the acceptance
criteria, no new pytest unit/integration test is required, because there is no executable behavior
to unit-test. Instead, the acceptance criteria are verified by **doc-level checks**, listed below
as the equivalent of "new tests":

- **Check name**: `validate_frontmatter — context_packet_contract.md passes`
  **Category**: tooling/script check (not a pytest test; run as a scoped CLI invocation, same
  precedent as the sibling ticket's Test Summary: `python3 tools/validate_frontmatter.py
  docs/ai/code_test_index_boundaries_decision.md`)
  **What it verifies**: AC1 — the new doc's frontmatter (`status`, `layer`, `authority`,
  `audience`) passes `tools/validate_frontmatter.py` with no violations.
  **Where it runs**: `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md`

- **Check name**: `verbatim field inventory — ContextRequest/ContextPacket`
  **Category**: manual/agent content-diff check (no automated test; this is a documentation-content
  correctness check, analogous to how the sibling ticket verified its own claims against
  `graphify/extract.py` directly rather than trusting a prior investigation)
  **What it verifies**: AC2 — every field named in the idea doc's Proposed Architecture §1
  (`task_ref`, `ticket_id`, free-text intent, `provider`, `agent_role`, `workflow`, `phase`,
  `risk_tier`, `changed_paths`, `scenario`, `token_budget` for `ContextRequest`; `packet_id`,
  `corpus_generation`, `retrieval_version`, `budget_requested`, `budget_returned`, `included[]`
  sub-fields, `excluded_summary[]`, `expansion_policy` for `ContextPacket`) appears in the new
  contract doc, with no field silently dropped or renamed.
  **Where it runs**: reviewer/implementer diffs the new doc's field list against
  `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
  lines 91-106 at Verify time.

- **Check name**: `Open Decision 3 resolution citation check`
  **Category**: manual/agent content check
  **What it verifies**: AC3 — the new doc's Open Decision 3 resolution explicitly cites
  `docs/REGISTRY.yaml`'s `status`/`authority` enum values (not a new parallel enum), and does not
  silently invent new registry machinery for "conflicting active documents."
  **Where it runs**: reviewer confirms the resolution section names the exact enum values from
  `tools/validate_frontmatter.py:44,54` (`STATUS_VALUES`, `AUTHORITY_VALUES`).

- **Check name**: `Out of Scope boundary check`
  **Category**: manual/agent content check
  **What it verifies**: AC4 — the ticket's own Out of Scope section (already present, confirmed at
  investigation time) excludes `src/`/`tools/` implementation, Phase 3 retrieval/cache, Phase 4
  observability, Phase 5-6 workflow adoption. No code change should confirm this — it is a
  ticket-body check, not a test.
  **Where it runs**: `tickets/inprogress/TCK-20260728-CONTEXT-PACKET-SCHEMA.md` Out of Scope
  section (already satisfied as authored; re-confirm unchanged at Finalize).

If a future Phase 3 ticket implements `ContextPacket` construction/serialization in code, that
ticket's own test_plan.md must add real unit tests (e.g. field-presence/type validation, hash
mismatch rejection per the idea doc's "reject packets whose source hashes no longer match"
constraint) — explicitly out of scope here.

## Scoped Pytest Commands

```bash
# Frontmatter/registry tooling regression — the only src/tools/ behavior this ticket's doc
# addition can affect (registry indexing, frontmatter validation).
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v
```

Do not run `pytest tests/` — nothing outside `tests/tools/` (registry/frontmatter tooling) is
touched by this ticket.

## Anti-Drift Test Guards

- **`test_generate_registry.py`'s `_SKIP_DOC_SUBDIRS` coverage** (if present) guards against a
  future accidental change that starts indexing `docs/parity_ledger/` into `docs/REGISTRY.yaml` —
  which would silently invalidate this ticket's Open Decision 3 resolution (which explicitly relies
  on parity ledger entries NOT sharing REGISTRY.yaml's enum space).
- **`test_validate_frontmatter.py`'s enum-value tests** (`STATUS_VALUES`, `AUTHORITY_VALUES`) guard
  against a future change to those enums silently invalidating this ticket's Open Decision 3
  resolution, which cites the enums by exact value set. If either enum set changes, the new
  contract doc's resolution section becomes stale and must be re-verified — this is analogous to
  the idea doc's own "reject packets whose source hashes no longer match" principle applied to the
  contract doc itself.
- **Manual re-grep of `docs/parity_ledger/*.yaml` for "context packet"/"ContextRequest"** at Verify
  time — guards against scope creep where a future edit to this ticket accidentally starts adding a
  parity ledger entry for a doc-only change (this ticket has no `src/` implementation, so no parity
  entry should exist; if one appears, that is scope creep into implementation territory this ticket
  explicitly excludes).
- **Ticket Out of Scope re-check at Finalize** — re-read
  `tickets/inprogress/TCK-20260728-CONTEXT-PACKET-SCHEMA.md`'s Out of Scope section before closing,
  to catch any implementer drift toward writing `src/`/`tools/` code "just to illustrate" the
  schema (a common trap when documenting a data contract — the sibling
  `monitoring_writer_decision.md` avoided this by using clearly-labeled non-executable illustration
  blocks only).
