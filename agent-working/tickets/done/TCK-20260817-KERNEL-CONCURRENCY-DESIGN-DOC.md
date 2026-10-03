---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC
phase: done
date: 2026-08-17
tags: [documentation, architecture, engine]
---

# TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC

## Title
Land the kernel concurrency & design-philosophy doc (Appendix A) into docs/architecture/

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
During discussion, the author drafted a complete high-level design write-up covering why Collection is a synchronous fork-join over a bounded pool instead of asyncio/anyio, how immutable snapshots plus stateless per-call RNG plus the 'Option A' one-result-per-entity protocol prevent races without locks/GIL reliance, how the RuntimeMode ladder and PhaseBudgetGovernor degrade gracefully under load, and the implicit design-priority order the engine follows. This content currently exists only in the conversation and an ephemeral external artifact link, and is not discoverable via search_docs, graphify query, or docs/REGISTRY.yaml. It needs to be placed into the docs tree, cross-linked from the contracts it summarizes, and folded into the knowledge index so it stands alone once the session ends.

## Scope
- Extract Appendix A content (all 5 Parts + both mermaid diagrams) from docs/plans/kernel_concurrency_design_review_proposal.md into a new doc under docs/architecture/
- Correct the doc's frontmatter status from the invalid 'draft' value to a legal value in {authoritative, active, historical, archive}; confirm authority tier (P1 vs P2) against sibling docs/architecture/ docs such as simulation_watchdog.md (P1)
- Add cross-links from docs/engine/kernel.md and the three concurrency contracts (bounded_concurrency_contract.md, worker_contract.md, concurrent_integrity_contract.md) to the new doc
- Preserve the two open-question pointers in Appendix A (RNG-in-Collection, concurrency_limit rationale) as pointers to their respective tickets rather than resolving them inline
- Run make docs-registry and make knowledge-index-update after landing

## Out of Scope
- Resolving the concurrency_limit rationale (covered by TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE) or the RNG-in-Collection question (covered by TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION)
- Fixing the concurrency contradiction or phase-count contradiction this doc's 'Known documentation drift' section narrates — those are separate tickets that must land first (see assumptions)
- Rewriting the lawbook's pillar precedence ordering (covered by TCK-20260817-STATE-DESIGN-PRIORITY-ORDER)

## Acceptance Criteria
- [x] New doc under docs/architecture/ contains all 5 Parts + both mermaid diagrams from Appendix A — **corrected during Implement**: the true diagram count is 4, not 2 (or the intro paragraph's "three"). Investigation recovered all 4 original diagrams (Part 1 `flowchart LR`, Part 2 `flowchart TB`, Part 3 `sequenceDiagram`, Part 4 `stateDiagram-v2`) from the still-reachable ephemeral artifact link that the repo's Appendix A fence had silently dropped when originally pasted in. This AC is marked satisfied against the corrected, evidence-based count of 4 (verified: `grep -c '^```mermaid' docs/architecture/kernel_concurrency_design_philosophy.md` == 4), not the ticket's literal "both"/2 wording, which Plan and Investigation both independently flagged as stale relative to the real source content. This is a deliberate correction, not an oversight.
- [x] Frontmatter status field is one of {authoritative, active, historical, archive}, never 'draft' — set to `active`, `authority: P1`, `audience: developer`, `layer: architecture` (matches sibling `docs/architecture/simulation_watchdog.md`); `tools/validate_frontmatter.py` exits 0.
- [x] docs/engine/kernel.md contains a grep-verifiable cross-link to the new doc
- [x] All three concurrency contracts (bounded_concurrency_contract.md, worker_contract.md, concurrent_integrity_contract.md) contain a cross-link to the new doc
- [x] `make docs-registry` exits 0 with the new doc indexed under layer architecture/engine — indexed under layer `architecture` (registry entry at docs/REGISTRY.yaml, confirmed by direct grep/read).
- [ ] `make knowledge-index-update` completes such that search_docs for 'kernel concurrency design philosophy fork-join' surfaces the new doc — **did not complete**. Ran for real; failed with exit code 2 (`OSError: We couldn't connect to 'https://huggingface.co'` inside `SentenceTransformer.__init__` in `tools/knowledge_search.py:838`). This is the previously-confirmed sandbox network block on huggingface.co, an environment limitation not caused by or fixable from this ticket's content — per CLAUDE.md and the plan's explicit instruction, not worked around and not falsely marked passed.

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260802-DOC-UPDATE-DISCIPLINE
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
- TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT
- TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION
- TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Related Docs
- docs/plans/kernel_concurrency_design_review_proposal.md
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/project_lawbook_m10.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/contracts/worker_contract.md
- docs/engine/contracts/concurrent_integrity_contract.md
- docs/architecture/simulation_watchdog.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/kernel_concurrency_design_review_proposal.md
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/project_lawbook_m10.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/contracts/worker_contract.md
- docs/engine/contracts/concurrent_integrity_contract.md
- docs/architecture/simulation_watchdog.md
- tools/validate_frontmatter.py
- src/engine/kernel.py
- src/engine/policy.py
- src/engine/apply.py

## Assumptions / Open Questions
- This ticket MUST be sequenced AFTER TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION and TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION (see SEQUENCE.md in this folder) — Appendix A's 'Known documentation drift' section narrates exactly those two contradictions and would go stale if this doc lands first; update/remove that section to reflect the fixes before landing
- TCK-20260817-STATE-DESIGN-PRIORITY-ORDER contains near-identical unlanded 'priority order' prose (Appendix A Part 1); this landed doc should be the single source of truth for that prose, and the lawbook ticket must cross-link here rather than restate it verbatim — verify wording matches at close
- Authority tier (P1 vs P2) for the new doc needs confirming against sibling docs/architecture/ docs like simulation_watchdog.md (P1)
- Appendix A's two open questions (RNG in Collection, concurrency_limit rationale) must remain as pointers to their tickets, not be silently resolved when landing
- layer chosen as `architecture` (rather than `engine`) because the deliverable is an ADR-shaped design doc landing specifically into docs/architecture/, per that layer's registered note ("ADRs and structural/architectural decisions"); the `engine` tag is retained to reflect the kernel-concurrency subject matter

## Implementation Notes

Executed the 12-step approved plan in `staging_artifacts/TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC/plan.md`
exactly, no deviations from the plan's content decisions.

1. Created `docs/architecture/kernel_concurrency_design_philosophy.md` with frontmatter
   `status: active, layer: architecture, authority: P1, audience: developer` (matching sibling
   `simulation_watchdog.md`). Body copied verbatim from
   `docs/plans/kernel_concurrency_design_review_proposal.md:200-366` (the current, already-fixed
   repo prose — not the stale externally-fetched artifact's prose).
2. Spliced all 4 recovered mermaid diagrams (exact verbatim source from investigation.md's
   "Recovered Diagram Source" section, character-for-character, standard ` ```mermaid ` fences not
   the artifact's `<pre class="mermaid">` wrapper) into Parts 1-4 at the anchors specified. Wrote
   the whole doc (base body + diagrams + Step 2/3 fixes below) in a single pass since all edits
   land in the same new file.
3. Fixed the 2 stale "Known documentation drift" items (concurrency framing contradiction, phase-
   count contradiction) with the exact `**Update (...)**` annotation text specified in Step 2,
   sourced from the parent proposal's own C2/C3 Update blocks. Item 3's existing annotation left
   untouched.
4. Replaced the stale `concurrency_limit` open-question pointer in Part 4 with the "now resolved"
   treatment (matching Part 3's RNG-pointer pattern), pointing to `GovernorPolicy.from_mode()`'s
   docstring and `bounded_concurrency_contract.md` §5.1 rather than restating the mechanism.
5. Added one-line "See also" cross-links (exact text from the plan) to `docs/engine/kernel.md`
   (after the Concurrency & Resolution Bottleneck bullets), `bounded_concurrency_contract.md`
   (after §5.1, before Non-Goals), `worker_contract.md` (after `## Purpose`, before
   `## 1. Payload Discipline` — did not touch either manifest-mandatory heading), and
   `concurrent_integrity_contract.md` (after `## Purpose`, before `## Scope`).
6. Verified all 4 cross-links with the combined grep (Step 8) — exactly 4 matches, one per file.
7. Added the C1 completion annotation to `docs/plans/kernel_concurrency_design_review_proposal.md`
   under `## C1`, using the actual close date 2026-08-21 (the plan's placeholder "2026-08-2X" filled
   with the real date observed during this Implement run).
8. Ran `make docs-registry` — exit 0, new doc indexed under layer `architecture`.
9. Ran `make knowledge-index-update` for real — it failed as predicted, exit code 2, due to the
   sandboxed environment's network block on `huggingface.co` (SentenceTransformer model load
   inside `tools/knowledge_search.py:838`). This is an environment limitation confirmed in
   investigation, not a defect introduced by this ticket's content; not worked around, reported
   honestly per the plan's explicit instruction and CLAUDE.md's gate-integrity rule.
10. Final verification pass (Step 12): `worker_contract.md`'s manifest-mandatory headers (`##
    Purpose`, `## 4. Backpressure & Fallback Law`) unchanged (note: the plan's own grep text
    approximated the second heading as `## Backpressure & Fallback Law`, but the real heading text
    is `## 4. Backpressure & Fallback Law` — confirmed unedited either way, and confirmed passing
    via `test_document_structural_compliance` directly rather than relying on the plan's imprecise
    grep string); full `tests/docs/`/`tests/unit/docs/` suite and the 5 named `tests/tools/` files
    pass; the xfail on `test_doc_path_citations_exist` remains pinned at exactly 12 dead citations
    (none of the new doc's 27 References citations, all individually pre-verified during Plan,
    introduced a 13th); Step 8's cross-link grep and Step 1b's mermaid-count grep both re-confirmed
    a second time after all edits landed.

**Deliberate AC correction**: the ticket's own AC text ("both mermaid diagrams") and the plan's/
test_plan's literal "2" wording are stale relative to investigation's confirmed count of 4 real
diagrams recovered from the still-reachable ephemeral external artifact. All 4 were landed, per
the plan's explicit instruction (see Acceptance Criteria above and `plan.md`'s Anti-Drift Notes,
which already flagged and pre-authorized this correction).

No architectural issues encountered; this was pure documentation extraction/cross-linking with
no simulation-law or durable-state changes.

## Test Summary

- `.venv/bin/python3 tools/validate_frontmatter.py docs/architecture/kernel_concurrency_design_philosophy.md --content-type doc` — exit 0.
- `.venv/bin/python3 -m pytest tests/docs/ tests/unit/docs/ -m "not slow" -q` — 44 passed, 1 skipped, 1 xfailed.
- `.venv/bin/python3 -m pytest tests/docs/test_doc_integrity.py::test_manifest_file_existence tests/docs/test_doc_integrity.py::test_document_structural_compliance tests/docs/test_doc_integrity.py::test_terminology_alignment tests/docs/test_doc_path_existence.py::test_doc_path_citations_exist -v` — 3 passed, 1 xfailed (confirmed still pinned at exactly 12 dead citations via `-rx` output).
- `.venv/bin/python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py tests/tools/test_layer_registry.py tests/tools/test_tag_registry.py -q` — 190 passed.
- `grep -rn "kernel_concurrency_design_philosophy" docs/engine/kernel.md docs/engine/contracts/bounded_concurrency_contract.md docs/engine/contracts/worker_contract.md docs/engine/contracts/concurrent_integrity_contract.md` — 4 matches (1 per file).
- `grep -c '^```mermaid' docs/architecture/kernel_concurrency_design_philosophy.md` — 4.
- `make docs-registry` — exit 0.
- `make knowledge-index-update` — exit 2 (real failure: `huggingface.co` network block, sandbox environment limitation, reported honestly not fabricated).

## Files Changed

- `docs/architecture/kernel_concurrency_design_philosophy.md` (new) — landed doc, 5 Parts + 4 mermaid diagrams, corrected frontmatter, drift-item annotations, `concurrency_limit` pointer fix.
- `docs/engine/kernel.md` (modified) — added 1-line "See also" cross-link after the Concurrency & Resolution Bottleneck bullets.
- `docs/engine/contracts/bounded_concurrency_contract.md` (modified) — added cross-link after §5.1, before `## Non-Goals`.
- `docs/engine/contracts/worker_contract.md` (modified) — added cross-link after `## Purpose`, before `## 1. Payload Discipline`; manifest-mandatory headers untouched.
- `docs/engine/contracts/concurrent_integrity_contract.md` (modified) — added cross-link after `## Purpose`, before `## Scope`.
- `docs/plans/kernel_concurrency_design_review_proposal.md` (modified) — added C1 `**Update (TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC, closed 2026-08-21)**` completion annotation.
- `docs/REGISTRY.yaml` (regenerated via `make docs-registry`) — new doc now indexed under layer `architecture`.
- `docs/parity_ledger/infrastructure.yaml` (modified) — appended optional `v2_evidence` cross-references to `INFRA-365`/`INFRA-366`/`INFRA-367`, pointing at the new doc's relevant Parts; no new entry needed since this ticket changes no behavior (confirmed exactly 3 entries semantically changed via a parsed-YAML diff).
- `staging_artifacts/TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC/investigation.md`, `plan.md`, `test_plan.md` (created during this ticket's own Investigate/Plan phases, part of this run's real changeset — not authored by this Implement step but confirmed present via `git status` as untracked new files belonging to this ticket).
- `tickets/inprogress/TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC.md` (this file — created earlier in the pipeline, updated here with Status/AC/Implementation Notes/Test Summary/Files Changed/Completion Summary).

## Completion Summary

Landed Appendix A of `docs/plans/kernel_concurrency_design_review_proposal.md` as a standalone,
standing reference doc at `docs/architecture/kernel_concurrency_design_philosophy.md`
(`status: active, authority: P1, audience: developer, layer: architecture`), using the current
repo's already-corrected prose (not the stale externally-fetched artifact's prose) plus all 4
mermaid diagrams recovered from that same artifact — a corrected count from the ticket's original
"both"/2 assumption, confirmed and pre-authorized by investigation and plan. Fixed 2 stale internal
"Known documentation drift" annotations and the `concurrency_limit` open-question pointer in place.
Cross-linked the new doc from `docs/engine/kernel.md` and all three concurrency contracts
(`bounded_concurrency_contract.md`, `worker_contract.md`, `concurrent_integrity_contract.md`)
without disturbing `worker_contract.md`'s manifest-mandatory headers. Added a matching C1 completion
annotation to the parent proposal for internal self-consistency. `make docs-registry` succeeded and
indexed the new doc; `make knowledge-index-update` failed with the previously-confirmed sandbox
`huggingface.co` network block (exit 2), reported honestly rather than worked around or fabricated
as passing. All targeted doc-integrity and tools tests pass, and the pre-existing 12-item dead-
citation xfail count is unchanged.
