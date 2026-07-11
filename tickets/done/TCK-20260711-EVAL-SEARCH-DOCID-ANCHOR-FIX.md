---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX
phase: open
date: 2026-07-11
tags: [bug, data-quality, root-cause]
---

# TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX

## Title
Fix `make eval-search` always reporting Recall@5/MRR@10 = 0.00 regardless of actual retrieval quality

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`make eval-search` (`tools/eval_search.py`) reports `Recall@5: 0.00 | Recall@10: 0.00 | MRR@10: 0.00` on every one of the 40 curated queries, including trivial exact-term lookups like "WorldRepository". This is not a real search-quality regression — live `search_docs` queries in this same session returned clearly relevant top hits. The eval harness's comparison logic is broken: `tools/eval/queries.json`'s `expected_doc_ids` are all bare document-level identities (`{section}/{stem}`, e.g. `architecture/world_repository_layout`), but `knowledge_search.py`'s `knowledge_docs.doc_id` SQL column is actually populated from the chunk-level `id` field (`f"{doc_id}#{heading_slug}-{seq}"` or `f"{doc_id}#body-000"`), which always carries a `#anchor` suffix for docs/ files. A bare string can never equal an anchored string, so every comparison fails by construction — the eval has been silently reporting FAIL for the wrong reason since chunk-level `id`/`doc_id` diverged (introduced by heading-level chunking, after `TCK-20260612-LOCAL-CTX-EVAL` shipped assuming the two were identical).

## Scope
- `tools/eval_search.py`: strip the `#anchor` suffix from each retrieved chunk id before comparing against `expected_doc_ids` in `_hit()`/`_reciprocal_rank()` call sites, restoring the document-level comparison the eval was designed around.
- `tests/tools/test_eval_search.py`: add regression coverage reproducing the exact failure mode (anchored result vs. bare expected id) to lock in the fix.
- Re-run `make eval-search` to confirm it now produces a real, non-zero signal.

## Out of Scope
- Changing the `knowledge_docs.doc_id` SQL column itself, or the MCP/HTTP search response `doc_id` field — those are correctly anchored today and used elsewhere (e.g. `search_docs` results cite exact sections); rewriting them would ripple into `search_mcp.py`/`search_server.py` consumers that rely on chunk-level precision.
- Retuning hybrid-search weights based on the now-real Recall@5 number — that's a separate follow-up if the corrected score is below the 0.80 threshold.
- Auditing/expanding `tools/eval/queries.json` beyond what's needed to verify the fix.

## Acceptance Criteria
- [x] `_strip_anchor()` (or equivalent) added to `tools/eval_search.py` and applied before every `expected_doc_ids` comparison
- [x] New regression test reproduces the bug (anchored chunk id vs. bare expected id → must count as a hit) and would fail against the pre-fix code
- [x] Existing 21 tests in `tests/tools/test_eval_search.py` still pass unchanged
- [x] `make eval-search` run against the live index no longer reports a blanket 0.00 — produces a real Recall@5/MRR@10 signal

## Related Tickets
- TCK-20260612-LOCAL-CTX-EVAL (original eval harness — designed against bare doc_id, predates the anchor divergence)
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (introduced 8-field query output, `doc_id` semantics unchanged at that point)
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS (heading-level chunking — introduced the `id` vs `doc_id` split that this bug stems from)

## Related Docs
- docs/guidelines/agent_working_environment.md (search environment reference; no content change needed — behavior restored to originally documented design, not altered)

## Related Stored Artifacts
- stored_artifacts/TCK-20260612-LOCAL-CTX-EVAL/investigation.md (original design: "Column 0 (doc_id) is the document identity... This is what expected_doc_ids in queries.json should match against")

## Related Code Areas
- `tools/eval_search.py`
- `tests/tools/test_eval_search.py`

## Assumptions / Open Questions
- Assumed the correct fix is on the eval side (strip anchor at comparison time), not the indexer side, per the Out of Scope reasoning above — chunk-level `doc_id` is intentional and load-bearing elsewhere.
- Real Recall@5 after the fix may land below the 0.80 threshold (it was never actually measured correctly before); if so, that's a legitimate follow-up ticket, not something to chase inside this hotfix.

## Implementation Notes
- Added `_strip_anchor(doc_id: str) -> str` to `tools/eval_search.py`: `doc_id.split("#", 1)[0]`.
- In `evaluate()`, compare `[_strip_anchor(d) for d in results]` against `expected` for `_hit()`/`_reciprocal_rank()`; raw `results` (with anchors) retained unchanged for the `top1`/`results` report fields so per-query debugging still shows exactly which chunk matched.
- No change to `knowledge_search.py`, `search_mcp.py`, or `search_server.py` — their anchored `doc_id` output is correct and unaffected.

## Test Summary
- Added `TestStripAnchor` (3 cases: anchored id, bare id passthrough, multiple `#` in text) and a new `TestEvaluateExitCode` case reproducing the exact real-world bug (`_run_query` returns `"target/doc#body-000"`, expected is `"target/doc"` → must hit).
- Full `tests/tools/test_eval_search.py` suite: 27/27 pass (21 original + 6 new).
- `make eval-search` re-run against the live index post-fix: **Recall@5 0.53 | Recall@10 0.65 | MRR@10 0.33** (was 0.00/0.00/0.00 pre-fix) — a real, non-zero, believable signal for the first time. Still below the 0.80 threshold (`make eval-search` exits 1), which is a legitimate search-quality finding, not a harness defect — flagged as an explicit follow-up, not chased in this hotfix (see Out of Scope).

## Files Changed
- `tools/eval_search.py`
- `tests/tools/test_eval_search.py`

## Completion Summary
Root-caused `make eval-search`'s blanket 0.00 Recall@5/MRR@10 to a bare-vs-anchored `doc_id` string mismatch between `tools/eval/queries.json`'s fixture (designed pre-chunking) and `knowledge_search.py`'s chunk-level `doc_id` column (populated post-chunking). Fixed by stripping the `#anchor` suffix at comparison time in `eval_search.py` only, preserving anchored `doc_id` everywhere it's actually used for chunk-level citation (MCP/HTTP search responses). Post-fix, `make eval-search` produces a real signal for the first time: Recall@5 0.53 | Recall@10 0.65 | MRR@10 0.33 — below the 0.80 gate, meaning the search feature likely does have room to improve (hybrid weight tuning, chunking granularity), but that is a genuine follow-up ticket, not part of this hotfix.
