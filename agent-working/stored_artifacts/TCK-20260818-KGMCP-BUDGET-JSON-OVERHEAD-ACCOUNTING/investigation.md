---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING
artifact_type: investigation
tags: [ai, mcp, performance]
---

# Investigation: TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING

## Root Cause

`assemble_within_budget()`'s cost function (`_statement_included_content_cost()`) summed
hand-picked raw field text: `statement.text`, `ContextEntry.summary`, `EvidenceEntry.evidence_id`/
`path`/`evidence_hash`. `truncate_conflicts_within_budget()` summed only `ConflictClaim.value`.
Cross-referencing against `tools/knowledge_gateway_mcp.py`'s actual response-building code
(`_run_knowledge_context()`) found the real serialized dicts include several more fields never
costed: `Statement.statement_id`/`classification`/`evidence_ids`/`verification`,
`ContextEntry.kind`/`source_id`/`path`/`evidence_hash`/`authority`, `EvidenceEntry.source_id`,
and — for conflicts — `Conflict.subject`/`automatic_resolution`/`recommended_action` and
`ConflictClaim.source_id`/`authority`/`valid_from`/`valid_to`. None of this was guessed: every
field above was confirmed present in the real dict-construction code at
`tools/knowledge_gateway_mcp.py`'s response-building block (read directly, not inferred).

`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`'s own #12
section (from the prior closure ticket) had already named exactly this field list as the honest,
disclosed reason the real §21 #12 pass rate stayed at 2/7 even after a real 11-22% payload
reduction — confirming this investigation's own finding independently, from a different angle
(real measured data vs. static code reading).

## Design Decision

Chose whole-fragment `json.dumps()` measurement over further hand-picking individual fields:
extracted the exact dict-construction logic `tools/knowledge_gateway_mcp.py` uses into four new
shared functions in `tools/knowledge_gateway_packet_assembly.py`
(`statement_response_fragment()`/`context_response_fragment()`/`evidence_response_fragment()`/
`conflict_response_fragment()`), then measure `kgmcp_char_heuristic_v1(json.dumps(fragment,
sort_keys=True))` per item. This structurally closes the "which field did we forget" failure mode
(any field the real response serializes is automatically costed) and captures real per-item JSON
structural overhead (braces, keys, commas, quoting) that hand-picked field-text summing could
never see. Refactored `tools/knowledge_gateway_mcp.py`'s response builder to call these same
functions instead of inlining the dict shape a second time — a structural guarantee against future
drift, not just a convention.

## Real Corpus Re-Measurement — False Start, Then Corrected

Initial attempt to run the real live gateway (`_run_knowledge_context()`) against
`context_search`-routed queries used a bare `python3 -c "..."` invocation and found
`context_search` failing with `"index not found"` — traced to `tools/search_mcp.py::
_ensure_loaded()`'s `SentenceTransformer(...)` call raising `ModuleNotFoundError: No module named
'sentence_transformers'` (silently swallowed by a bare `except Exception: return False`). At that
point I wrongly concluded the knowledge-search stack (`requirements-knowledge.txt`) was entirely
unavailable in this sandbox and that a network block prevented installing it (`curl -v
https://huggingface.co` does genuinely hang at the TLS Certificate stage, matching a real
network-filtering pattern seen elsewhere this session) — and drafted the ticket, both docs, and
the parity ledger entry around that false conclusion.

**Correction, caught before this ticket closed:** `make knowledge-index-update` (run later, during
Finalize, since docs/ files changed) succeeded and loaded model weights without issue — using
`.venv/bin/python3`, not bare `python3`. Re-checked directly:
`.venv/bin/python3 -c "from sentence_transformers import SentenceTransformer"` imports cleanly.
The bare `python3` on `PATH` earlier in the session was a *different*, system interpreter without
the venv's packages — a self-inflicted false negative, not a real environment blocker. Re-ran the
gateway with the correct interpreter and it worked immediately (`status: OK`, real statements
returned). Every doc, ticket section, and parity ledger entry that had recorded the false "blocked"
conclusion was corrected to the real, measured result (see below) before this ticket closed — not
left standing as a plausible-sounding but wrong record.

## Real Corpus Re-Measurement — Actual Result

Cleared both live cache tables (`retrieval_provider_result_cache_rows`,
`retrieval_context_packet_cache_rows` — gitignored, untracked local dev-machine state, same
disclosed-hygiene precedent as the recalibration hotfix) and ran the frozen 7-entry corpus at
`budget_tokens=1000` via `.venv/bin/python3`, computing `_compute_budget_compliance()`'s exact
formula (`kgmcp_char_heuristic_v1(json.dumps(response, sort_keys=True))` vs. `1000 × 1.2`
threshold). Ran twice, clearing the cache again in between, confirming `cache: MISS` (genuine
cold compute, not a stale value) both times and identical token counts both runs:

Q1=1115, Q2=183, Q3=1099, Q4=1171, Q5=179, Q6=1154, Q7=1038 — all seven ≤ 1200. **Real result:
§21 #12 budget-tolerance is 7/7 PASS, up from 2/7.** Every previously-failing `context_search`-
routed entry (Q1, Q3, Q4, Q6, Q7) dropped from the post-INFRA-356 range of 2200-2450 tokens to
1038-1171 — the fix closes the gap in full on this corpus. Full table recorded in
`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`'s "Further
accounting closure" section and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-357` entry.

## Conflicts

`truncate_conflicts_within_budget()`'s own field gap was fixed the same way for consistency, even
though the real 7-entry corpus has never observed a real conflict (0/7, per #13's own disclosure)
— so this specific fix does not move any currently-measured number, but closes the same latent
gap class before it could resurface once the corpus (or a future one) does exercise conflicts.
