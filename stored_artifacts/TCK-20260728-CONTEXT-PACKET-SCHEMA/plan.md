---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260728-CONTEXT-PACKET-SCHEMA
artifact_type: plan
tags: [ai, registry, schema]
---

# Implementation Plan — TCK-20260728-CONTEXT-PACKET-SCHEMA

## Summary

This ticket authors exactly one new file, `docs/engine/contracts/context_packet_contract.md`,
that specifies the `ContextRequest`/`ContextPacket` field shapes verbatim from the idea doc's
Proposed Architecture §1 (lines 91-106 of
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`),
resolves Open Decision 3 by mapping packet `authority`/`freshness` directly onto
`docs/REGISTRY.yaml`'s existing `status`/`authority` frontmatter enums (never inventing a
parallel enum space), and documents two explicitly-scoped extensions the idea doc's field list
does not cover on its own: (a) a fallback authority/freshness posture for non-registry-backed
source kinds, and (b) an advisory doc-only tie-break rule for representing conflicting active
documents. The doc mirrors `task_result_update_substrate_contract.md`'s shape (Purpose → field
list → constraints → verification-path-equivalent) and `monitoring_writer_decision.md`'s
"decides and evidences, implements nothing" disclaimer convention. No `src/`/`tools/` code, no
`docs/REGISTRY.yaml` schema change, and no other Open Decision (1, 2, 4, 5, 6) is touched. This
is a pure documentation-authoring ticket with no pytest-testable behavior; verification is via
`tools/validate_frontmatter.py` plus manual content-diff/citation checks per `test_plan.md`.

## Resolved Design Decisions (binding on the implementer — do not re-litigate)

These three points were flagged as open in `investigation.md`. Each is resolved here as a
concrete authoring instruction. The implementer follows these verbatim; it does not re-decide them.

**Decision A — non-registry-backed source fallback (investigation's open question 1).**
The contract doc's `included[].authority`/`included[].freshness` field description must state,
in the field-list section itself (not buried in a footnote), that these values are only
REGISTRY-backed when `included[].kind` identifies a `docs/REGISTRY.yaml`-indexed source (i.e.
a doc under `docs/` not in `_SKIP_DOC_SUBDIRS`, or a `tickets/done/` entry). For every other
`kind` — code symbol, test file, Graphify node, `tickets/inprogress/` ticket body, or
`docs/parity_ledger/` entry — the doc must state an explicit fallback rather than imply a real
REGISTRY value always exists:
- `docs/parity_ledger/` entries carry their own differently-shaped authority proxy
  (`priority`: `P0`/`P1`/`P2` plus `status`: `verified|divergent|missing|unsupported|legacy_verified`,
  per `docs/parity_ledger/schema.json:16-23`) — the packet's `authority`/`freshness` fields must
  be populated from parity ledger's own `priority`/`status` for these sources, not from
  REGISTRY.yaml (they are not indexed there), and the doc must flag this as a **second,
  differently-shaped vocabulary**, not silently coerced into REGISTRY's 3-value/4-value enums.
- Code symbols, test files, Graphify nodes, and `tickets/inprogress/` bodies have **no**
  authority/freshness primitive anywhere in the repo today. The doc must state the documented
  fallback: `authority: unrated` (a value distinct from REGISTRY's `P0`/`P1`/`P2`, explicitly
  not one of them) and `freshness: unrated`, both flagged in the doc as "this source kind has no
  registry-backed authority signal; the packet must not imply otherwise." This is a documentation
  statement only — it does not add `unrated` to `tools/validate_frontmatter.py`'s
  `AUTHORITY_VALUES` (that enum governs doc *frontmatter*, a different namespace from a packet's
  per-source-item field value; no code changes as part of this ticket).

**Decision B — conflicting active documents (investigation's open question 2).**
The doc's Open Decision 3 resolution section states an advisory, doc-only tie-break rule, framed
explicitly as guidance for a future packet-assembly implementation, not a schema change:
when two `included[]` entries are both docs with `status: active` or `status: authoritative`
(per `tools/validate_frontmatter.py:44` `STATUS_VALUES`) and address the same subject, the
packet includes both entries rather than silently dropping one, ranks them by `authority`
(`P0 > P1 > P2`, per `tools/validate_frontmatter.py:54`) and then by `last_verified` recency as
the tie-break, and sets the lower-ranked entry's `inclusion_reason` to name it as the
superseded/lower-priority alternative (e.g. `"superseded-by:<source_id of higher-ranked entry>"`
as an illustrative, non-normative example format). This must be explicitly labeled as advisory
documentation guidance for packet-assembly logic, not a `docs/REGISTRY.yaml` field addition —
Out of Scope forbids modifying REGISTRY.yaml's schema/enums, and this rule adds no new registry
field, only a convention for populating the packet's own (already-listed) `inclusion_reason`
field.

**Decision C — doc placement (investigation's open question 3).**
Finalized target: `docs/engine/contracts/context_packet_contract.md`. This is an Engine Contract
(per the ticket's own Scope/AC1 wording and `task_result_update_substrate_contract.md`'s
doc-shape precedent), not `docs/ai/` where sibling decision docs
(`monitoring_writer_decision.md`, `code_test_index_boundaries_decision.md`) live. The
distinguishing rationale, to be stated in the new doc's own opening line: this document defines
a data-shape *contract* that a future Phase 3 ticket implements against, mirroring
`task_result_update_substrate_contract.md`'s role for the engine's Task/Result/Update substrate,
whereas the `docs/ai/*_decision.md` docs are evidentiary decision records for orchestration
process questions. Do not move or duplicate content into `docs/ai/`.

## Steps

### Step 1 — Author the contract doc skeleton and frontmatter
**Files:** `docs/engine/contracts/context_packet_contract.md` (new)
**Change:** Create the file with:
- Frontmatter: `status: active`, `layer: ai`, `authority: P1`, `audience: agent`,
  `tags: [ai, registry, schema]` (all three tags already registered per
  `tools/tag_registry.py list`, confirmed in investigation.md; `layer: ai` already registered
  per `tools/layer_registry.py list`).
- Title: `# Context-Packet Contract`.
- An opening disclaimer paragraph, mirroring `monitoring_writer_decision.md`'s convention:
  states this document **defines a schema contract for a future implementation**, that no
  `src/`/`tools/` code exists yet or is added by this ticket, and states the placement rationale
  from Decision C above (contract vs. decision-record distinction).
- Preserve verbatim the idea doc's load-bearing constraint sentence (idea doc lines 108-110):
  "The packet is a retrieval artifact, not a new source of truth. Consumers must re-read the
  cited source before making a high-impact change and reject packets whose source hashes no
  longer match."
**Do NOT touch:** Any other file. Do not create `docs/ai/context_packet_*.md`. Do not add a
`docs/parity_ledger/` entry.
**Verify:** `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md`
exits clean (AC1 check from test_plan.md).

### Step 2 — Write the ContextRequest field section (verbatim)
**Files:** `docs/engine/contracts/context_packet_contract.md`
**Change:** Add a `## 1. ContextRequest` section listing, verbatim, every field named in the
idea doc's Proposed Architecture §1 (lines 91-106): `task_ref | ticket_id | free-text intent`,
`provider`, `agent_role`, `workflow`, `phase`, `risk_tier`, `changed_paths`, `scenario`,
`token_budget`. One bullet per field with a one-line purpose description (purpose text may be
original prose — only the field *names* must match verbatim; do not rename or drop any field).
State the "→ classify and retrieve" transition line from the idea doc as the section's closing
note (this is the request's disposition, not a new field).
**Do NOT touch:** Do not add fields not in this list (e.g. no invented `conflict_group_id` or
similar convenience field — anti-drift hazard from investigation.md). If Decision A/B's
resolution needs a field not in this original list, it must go in the `ContextPacket` section's
extension subsection (Step 4), clearly marked as this ticket's own addition, never merged
silently into this verbatim `ContextRequest` list.
**Verify:** Manual content-diff check (test_plan.md "verbatim field inventory" check, AC2) —
every `ContextRequest` field name from idea doc lines 93-95 appears in this section.

### Step 3 — Write the ContextPacket field section (verbatim)
**Files:** `docs/engine/contracts/context_packet_contract.md`
**Change:** Add a `## 2. ContextPacket` section listing, verbatim, every field from the idea doc:
`packet_id`, `corpus_generation`, `retrieval_version`, `budget_requested`, `budget_returned`,
`included[]` (with its ten sub-fields: `source_id`, `kind`, `path`, `heading_or_symbol`, `hash`,
`authority`, `freshness`, `score`, `inclusion_reason`, `excerpt_budget`), `excluded_summary[]`
(sub-fields: `source_id`/`kind`/`reason`/`count` only), `expansion_policy` (and escalation
conditions). One bullet per field/sub-field with a one-line purpose description. Immediately
following the `included[].authority`/`included[].freshness` sub-field bullets, insert the
Decision A fallback text (non-registry-backed source kinds) inline as part of those two
sub-fields' own descriptions — this is describing the verbatim field's *semantics*, not adding a
new field, so it belongs in this section rather than a separate extension block.
**Do NOT touch:** Do not drop or rename any of the ten `included[]` sub-fields or the four
`excluded_summary[]` sub-fields. Do not add new top-level `ContextPacket` fields here (any true
addition goes in Step 4's clearly-marked extension subsection).
**Verify:** Manual content-diff check (test_plan.md "verbatim field inventory" check, AC2) —
every `ContextPacket` field and every `included[]`/`excluded_summary[]` sub-field from idea doc
lines 99-105 appears in this section.

### Step 4 — Write the Open Decision 3 resolution section
**Files:** `docs/engine/contracts/context_packet_contract.md`
**Change:** Add a `## 3. Open Decision 3 Resolution` section, structured per the sibling-doc
precedent (`monitoring_writer_decision.md`/`code_test_index_boundaries_decision.md`'s
blockquote-the-decision → resolution shape):
- Open with a blockquote of the exact Open Decision 3 text from the epic ticket: "Which
  authority/freshness metadata should be mandatory for a packet source, and how should
  conflicting active documents be represented?"
- State the core resolution: packet `authority` for REGISTRY-backed sources is populated
  directly from `docs/REGISTRY.yaml`'s `authority` field (`P0`/`P1`/`P2`,
  `tools/validate_frontmatter.py:54`), and `freshness` is derived from `status` (`authoritative`/
  `active`/`historical`/`archive`, `tools/validate_frontmatter.py:44`) plus `last_verified`
  recency — not a new independent numeric score. Cite these exact enum names/line numbers.
- Include Decision A's fallback rule (non-registry-backed sources) as a clearly-labeled
  **extension** subsection: "Extension — non-registry-backed source fallback (this ticket's
  addition, not in the idea doc's original field list)." State the `authority: unrated` /
  `freshness: unrated` fallback and the separate parity-ledger-proxy handling, per Decision A
  above.
- Include Decision B's conflicting-active-documents tie-break rule as a second clearly-labeled
  extension subsection: "Extension — conflicting active documents (advisory guidance, not a
  REGISTRY.yaml schema change)." State the rank-by-authority-then-recency rule and the
  `inclusion_reason` convention, per Decision B above.
- Close with a paragraph naming what does NOT change: `docs/REGISTRY.yaml`'s generator, schema,
  or enum values are untouched; no new frontmatter field is required on any existing doc; no
  `tools/validate_frontmatter.py` code change accompanies this document.
**Do NOT touch:** `tools/validate_frontmatter.py`, `tools/generate_registry.py`,
`docs/REGISTRY.yaml`, `docs/parity_ledger/schema.json`. Do not resolve or gesture toward an
answer for Open Decisions 1, 4, 5, or 6 anywhere in this section or elsewhere in the doc.
**Verify:** Manual content check (test_plan.md "Open Decision 3 resolution citation check", AC3)
— resolution section names `STATUS_VALUES`/`AUTHORITY_VALUES` by their exact enum value sets and
does not invent a parallel enum.

### Step 5 — Add the closing verification-path-equivalent section
**Files:** `docs/engine/contracts/context_packet_contract.md`
**Change:** Add a closing `## 4. Verification Path` section mirroring
`task_result_update_substrate_contract.md`'s §5 shape, substituting "enforcing code/tests" (none
exist yet) with: a citation back to
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
§"Proposed Architecture" → "1. Context-packet contract" as the field list's source of truth, a
citation to this resolution (Section 3 of this doc) as Open Decision 3's authoritative answer,
and an explicit statement that no code enforces this contract yet — a future Phase 3 ticket
implementing `ContextPacket` construction/serialization must add its own
`tests/`-path verification and, at that time, a `docs/parity_ledger/` entry if it introduces
simulation-adjacent behavior (it will not, since this is agent-orchestration tooling, per
investigation.md's Mechanics/Engine Constraints finding — state this explicitly so a future
reader doesn't assume a parity ledger entry is missing).
**Do NOT touch:** Do not add a real `docs/parity_ledger/` entry now — there is no code to check
parity against.
**Verify:** Full-doc read-through confirms AC1-AC3 line items are all present in one file.

### Step 6 — Link the new doc from the epic ticket and mark Open Decision 3 resolved
**Files:** `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`
**Change:** In the epic's `## Assumptions / Open Questions` section, replace the current
"OPEN DECISION 3: Which authority/freshness metadata..." line with a `**RESOLVED**` line in the
exact style already used for OPEN DECISION 2 (see that entry as the literal template): date
`2026-07-29`, ticket ref `TCK-20260728-CONTEXT-PACKET-SCHEMA`, a one-paragraph answer summary
(REGISTRY-backed authority/freshness mapping, non-registry fallback, conflicting-docs tie-break),
and a citation `docs/engine/contracts/context_packet_contract.md`. Also add this ticket to the
epic's Related Tickets / child-ticket tracking if a list exists there (check the epic body's
`## Related Tickets`/child-tracking section for the existing pattern used for the Decision-2
sibling ticket and mirror it).
**Do NOT touch:** Do not alter OPEN DECISION 1, 4, 5, or 6 lines in the epic. Do not change the
epic's `## Status` (`EPIC_SCOPED`) or `## Tier` (`epic`) — this child ticket does not close the
epic.
**Verify:** Diff of the epic file shows only the Open Decision 3 line (and Related Tickets entry,
if applicable) changed; git diff contains no edits to Decision 1/4/5/6 lines.

### Step 7 — Update this ticket's own body (Implementation Notes / Test Summary / Files Changed)
**Files:** `tickets/inprogress/TCK-20260728-CONTEXT-PACKET-SCHEMA.md`
**Change:** Fill in `## Implementation Notes` (summary of Decisions A/B/C and where each landed
in the new doc), `## Test Summary` (the four check results from test_plan.md — frontmatter pass,
verbatim field inventory, Open Decision 3 citation check, Out of Scope re-check — plus the
scoped pytest command's pass/fail result), and `## Files Changed` (list
`docs/engine/contracts/context_packet_contract.md` (new),
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`,
`tickets/inprogress/TCK-20260728-CONTEXT-PACKET-SCHEMA.md`). Leave `## Status` as `OPEN` — a
later Finalize step (not part of this plan) moves it to `tickets/done/` after done-checker runs.
**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria` — these sections are
already correctly authored (confirmed in investigation.md) and must not be edited to
retroactively match implementation; if implementation cannot satisfy an AC as written, that is a
blocker to raise, not a section to quietly loosen.
**Verify:** `tickets/inprogress/TCK-20260728-CONTEXT-PACKET-SCHEMA.md`'s Out of Scope section
re-read at Finalize still excludes src/tools implementation, Phase 3/4/5-6 (test_plan.md's
"Out of Scope boundary check", AC4).

### Step 8 — Run the scoped regression check
**Files:** None changed; verification only.
**Change:** Run the exact command from test_plan.md:
```bash
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v
```
Confirm all pass — this is regression coverage proving the new doc doesn't break frontmatter
validation or registry generation, not new test authorship (none is required per test_plan.md's
"New Tests Required" section, since there is no executable ContextPacket behavior to unit-test).
**Do NOT touch:** Do not run `pytest tests/` broadly. Do not write a new pytest test file — none
is warranted for a doc-only change per test_plan.md.
**Verify:** All three test files pass with no failures/errors.

## Scope Guards

- Do not modify `docs/REGISTRY.yaml`'s generator (`tools/generate_registry.py`), schema, or any
  existing enum value (`STATUS_VALUES`, `AUTHORITY_VALUES`, `AUDIENCE_VALUES`, etc. in
  `tools/validate_frontmatter.py`).
- Do not write any `src/` or `tools/` code implementing `ContextPacket`/`ContextRequest`
  construction, serialization, hashing, or validation. The contract doc's field examples are
  illustrative text only, never executable code.
- Do not touch `docs/parity_ledger/` — no entry exists for this territory and none should be
  added; this is documentation-only agent-orchestration tooling, not simulation logic (confirmed
  no parity overlap in investigation.md).
- Do not resolve, answer, or gesture toward answering Open Decisions 1, 2, 4, 5, or 6. Decision 2
  is already resolved by the sibling ticket (`TCK-20260728-CODE-TEST-INDEX-BOUNDARIES`) — do not
  re-litigate or restate it beyond the existing citation.
- Do not place the new doc anywhere other than `docs/engine/contracts/context_packet_contract.md`
  (specifically: not `docs/ai/`, despite that being the sibling decision docs' location).
- Do not implement Phase 3 (retrieval/cache), Phase 4 (observability events/dashboard), or Phase
  5-6 (shadow packets/workflow adoption) work — this ticket is Phase 2 schema-authoring only.
- Do not change the epic ticket's `## Status` or `## Tier`, and do not touch Decision 1/4/5/6
  lines in its Assumptions/Open Questions section.
- Do not edit this ticket's own `## Scope`, `## Out of Scope`, or `## Acceptance Criteria`
  sections.

## Dependency Map

- Steps 1-5 are sequential (each appends to the same new file, in doc-reading order) but each is
  independently verifiable once written (frontmatter check after Step 1; content-diff checks
  after Steps 2/3; citation check after Step 4; full read-through after Step 5).
- Step 6 (epic cross-link) depends on Steps 1-5 being complete (the citation target must exist
  and be stable before linking to it).
- Step 7 (this ticket's own body update) depends on Steps 1-6 being complete (summarizes what was
  actually done).
- Step 8 (regression pytest run) is independent of Steps 1-7's content but should run last, after
  the new file exists, to confirm registry/frontmatter tooling still handles it correctly.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — new doc exists with frontmatter passing `validate_frontmatter.py` using registered layer/tags | Step 1 | `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` |
| AC2 — doc documents ContextRequest/ContextPacket fields verbatim from idea doc §1 | Steps 2, 3 | Manual verbatim field inventory diff against idea doc lines 91-106 |
| AC3 — doc explicitly resolves Open Decision 3 citing REGISTRY.yaml's enums, not a parallel system | Step 4 | Manual citation check confirming `STATUS_VALUES`/`AUTHORITY_VALUES` named exactly |
| AC4 — ticket's Out of Scope excludes src/tools impl, Phase 3/4/5-6 | Step 7 (re-confirm, already authored per investigation.md) | Out of Scope boundary re-check at Finalize |

## Anti-Drift Notes

- **Verbatim field list discipline**: Steps 2 and 3 must not add convenience fields beyond the
  idea doc's exact list (e.g. no invented `conflict_group_id`). Any field needed to make Decision
  A/B's resolution concrete must be described as semantics of an *existing* verbatim field
  (`authority`/`freshness`/`inclusion_reason` already exist in the idea doc's list) — not as a new
  field. This was the investigation's top-flagged hazard.
- **Do not silently imply every `included[]` entry has a real REGISTRY-backed authority value.**
  Step 4 must state the non-registry-backed fallback (`unrated`) explicitly, per Decision A —
  this is the investigation's most detailed open-question finding and the most likely place for
  an implementer to under-specify.
- **Conflicting-active-documents rule is advisory prose, not a schema change.** Step 4 must label
  Decision B's tie-break rule as guidance for future packet-assembly logic, explicitly not a
  `docs/REGISTRY.yaml` field addition — Out of Scope forbids modifying REGISTRY.yaml's enums.
- **Placement is settled, not re-debatable.** Step 1 must not default to `docs/ai/` out of habit
  from the sibling `monitoring_writer_decision.md`/`code_test_index_boundaries_decision.md`
  precedent — the ticket's own Scope/AC1 name `docs/engine/contracts/context_packet_contract.md`
  explicitly.
- **Tag-registry enforcement nuance**: `_validate_doc` (the function that will validate this
  file, since it is `content_type: doc` per path-based inference) does not itself call
  `_check_tags` — tag registration is a process-discipline check, not a hard gate for this
  specific file. All three tags (`ai`, `registry`, `schema`) are registered regardless, so this is
  moot in practice, but Step 1 should not assume `validate_frontmatter.py`'s exit code alone
  proves tag registration; the tags are independently confirmed registered per investigation.md.
- **Tier is `standard`**: per investigation.md's Risks section, this ticket should still go
  through architecture review despite being doc-only — the reviewer's focus is doc-schema-shape
  correctness and whether Open Decision 3 is honestly resolved (not overclaimed), not a
  durable-state diff (there is none).
