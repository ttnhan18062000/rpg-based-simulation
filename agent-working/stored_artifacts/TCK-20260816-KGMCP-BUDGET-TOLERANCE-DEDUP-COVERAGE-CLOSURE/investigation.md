---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE

## Current Behavior

### Gap 1 — `assemble_within_budget()`'s real accounting logic

`tools/knowledge_gateway_packet_assembly.py:643-670` (`assemble_within_budget()`):

```python
def assemble_within_budget(statements, budget_requested):
    ordered_indices = sorted(range(len(statements)), key=lambda i: (statements[i].priority_tier, i))
    included = []
    running_total = 0
    for i in ordered_indices:
        statement = statements[i]
        cost = kgmcp_char_heuristic_v1(statement.text)
        if running_total + cost <= budget_requested:
            included.append(statement)
            running_total += cost
        else:
            break
    return included, running_total
```

Traced precisely:
1. **What it measures**: only `Statement.text` for each candidate statement, via
   `kgmcp_char_heuristic_v1(text) = ceil(len(text.encode("utf-8")) / 4)` (`:85-91`). Nothing else —
   not `ContextEntry.summary`, not `EvidenceEntry`, not `Conflict` fields, not JSON structural
   overhead (keys, braces, `cache_key_version`, etc).
2. **What it truncates**: iterates statements sorted `(priority_tier ascending, original index)` —
   stable, deterministic — and greedily includes each statement only if
   `running_total + cost <= budget_requested`; the loop `break`s on the first statement that would
   overflow, so every statement at or after that point in sort order is dropped, not just the one
   offending statement.
3. **What it returns**: `(included_statements, running_total)`. `running_total` becomes
   `PacketAssembly.budget_returned`, which is `<= budget_requested` by construction (never a
   post-hoc clamp).
4. **Downstream in `assemble_packet()` (`:770-790`)**: `included_statements` (from the call above)
   is used to build `included_evidence_ids`, and `final_context`/`final_evidence` are then filtered
   to `context_entries`/`evidence_entries` whose `source_id`/`evidence_id` is in that set. Critically,
   `render_candidates()` (`:260-387`) sets `ContextEntry.summary = text` — **the exact same string**
   already counted as `Statement.text` for `context_search`/`graphify`-sourced items. So for those
   two providers, every statement's byte cost is effectively present again, uncounted, in
   `context[]`, and a third time (as `EvidenceEntry`, without a `summary`/`text` field but still
   contributing `path`/`evidence_hash`/`evidence_id` JSON bytes) in `evidence[]`. `conflicts[]` is
   also entirely unbudgeted, though in practice `build_conflicts()` returns `[]` against every real
   provider today (module docstring `:27-31`; confirmed live below), so it contributes zero to the
   real gap.
5. Confirmed via `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`
   §21 #12 (lines 110-136): measured against `json.dumps(response)` (the full real payload), 5 of 7
   corpus entries exceed the ±20% tolerance on `budget_tokens=1000` — every `context_search`-routed
   entry (Q1, Q3, Q4, Q6, Q7) is 2.3×-2.4× over the 1200-token threshold; only the two pure-`graphify`
   entries (Q2, Q5) pass, because `graphify`'s single-statement response shape happens to be small
   enough that duplicating it in `context[]` still fits.

### Gap 2 — live, real-corpus dedup coverage

`deduplicate_statements()` (`:425-469`), `_content_hash()` (`:249-257`), and
`_conflict_signal_index_pairs()` (`:398-422`) are real, reachable from `assemble_packet()`'s fixed
pipeline, and covered by INFRA-347's 11 unit tests (`tests/tools/test_knowledge_gateway_packet_assembly.py`).
`deduplicate_statements()` groups by `_dedup_key()`, which returns `statement.evidence_hash` when
present, else `_content_hash(statement.text)` (sha256 of stripped text) as a fallback for
directly-constructed test fixtures only.

I ran the live gateway against all 7 frozen corpus entries today (`tools/agent-monitoring/kgmcp_baseline_corpus.py`),
calling `kgr.route(query_text)` → `kgpa.call_providers_for_routing_decision()` →
`kgpa.render_candidates()` → grouping every produced `Statement.evidence_hash` by which provider
contributed it (`_provider_id_for_evidence_id()`), then separately running
`deduplicate_statements()`. Real, current routing (Level 2/Parity/`changed_paths` now all live,
per Phase 3/4) now sends **2 of 7 entries** to more than one provider, not 1 as the ticket's own
framing (based on the older Phase 3 measurement) states — Q7 (`context_search`+`graphify`, as
before) **and now also Q3** (`context_search`+`parity_ledger`, newly live since
TCK-20260816-KGMCP-P4-PARITY-ADAPTER). Real per-entry result:

| Entry | providers_selected (live today) | statements pre-dedup | cross-provider content_hash collisions |
|---|---|---|---|
| Q1_authoritative_state | context_search | 8 | 0 |
| Q2_symbol_lookup | graphify | 1 | 0 |
| Q3_requirement_completeness | context_search, parity_ledger | 8 | 0 |
| Q4_historical_rationale | context_search | 8 | 0 |
| Q5_test_impact | graphify | 1 | 0 |
| Q6_ticket_status | context_search | 8 | 0 |
| Q7_negative_knowledge | context_search, graphify | 9 | 0 |

`deduplicate_statements()`'s post-dedup statement count equals its pre-dedup count for every entry
(8→8, 1→1, 8→8, 8→8, 1→1, 8→8, 9→9) — **zero real duplicate content across providers exists in the
live 7-entry corpus today**, confirmed by direct execution, not inference from the FAIL doc.

Additional real finding while tracing Q3: `providers_selected` includes `parity_ledger`, but
`call_providers_for_routing_decision()`'s real return for it had
`results["parity_ledger"]["results"]["found"] == False` — the parity index has no matching entry
for that free-text query, so `render_candidates()` never emits a parity-sourced statement for Q3 at
all (its 8 statements are 100% `context_search`). So in the live corpus today, no entry has ever
actually produced a rendered statement from more than one provider *simultaneously with non-empty
content on both sides* except Q7 (`context_search` × `graphify`) — Q3's second provider slot exists
in routing but is empirically a no-op today.

A second, real, previously-undocumented structural nuance found while tracing this: for the
`parity_ledger` block, `render_candidates()` (`:348-386`) sets
`evidence_hash = record["canonical_fragment_hash"]` — the parity index's own precomputed hash —
**not** `_content_hash(text)` as the `context_search`/`graphify` blocks both use. `_dedup_key()`
then keys on `statement.evidence_hash` when present, so a parity-sourced statement's dedup identity
is `canonical_fragment_hash`, a different hash than `_content_hash()` would produce for the same
literal text. Byte-identical text between a parity statement and a context_search statement would
therefore **not** collapse into one dedup group, since their key strings would differ even though
their content is identical. This was never observed live today (Q3's parity call returned
`found=False`, so no parity statement exists in the corpus to test this against), so it is not a
disproven mechanism either — it is an untested, real code-path gap, distinct from and additional to
the ticket's own stated Gap 2.

## Mechanics / Engine Constraints

- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8 (Token-Counting
  Method): ratifies `kgmcp_char_heuristic_v1` as `ceil(len(text.encode("utf-8"))/4)` with a
  documented **±20% tolerance** against a true tokenizer count — this is the tolerance §21 #12 is
  measured against, and the tolerance a fix must continue to satisfy for the full payload, not just
  `statements[]`.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §15 (Token-Budgeted Assembly) and §16 (Failure and
  Fallback Semantics): §16's "budget-assembly failure" row requires "Return a smaller evidence list
  or provider references, never fabricated content" — any fix must preserve this fallback's
  semantics for the now-also-budgeted `context[]`/`evidence[]`.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §14 (Conflict Handling): conflicts are
  structural-only (no semantic/embedding heuristic) — a fix must not introduce any semantic
  comparison to `conflicts[]` truncation either; it can only be measured/truncated by the same
  extractive-size discipline.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`: governs the 8
  closed evidence-identity-kind forms and the content-hash-based identity concept
  `deduplicate_statements()`/`_content_hash()` already implements — any dedup-related work must stay
  consistent with this, never introduce a second, competing identity concept.
- Module docstring's own honesty notes (`tools/knowledge_gateway_packet_assembly.py:17-39`): "do not
  'fix' these by inventing heuristics" — governs both gaps; a fix must extend the existing real,
  measured-size discipline, never approximate it with a length-based multiplier or similar
  shortcut (the anti-pattern explicitly named at `tools/context_packet_assembler.py:287` in
  `assemble_within_budget()`'s own docstring, `:648-649`).

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`: §21 #12's
  FAIL result and per-entry table must be updated once §12 is re-measured against the fixed code,
  per this ticket's own Scope — replace the 2/7 result with whatever the real re-run produces,
  honestly, including if it is still not 7/7.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §15 (Token-Budgeted Assembly) currently describes
  budget accounting only in terms of statements/priority tiers; it must be updated to describe the
  real extended accounting scope (context/evidence/conflicts) and whatever truncation order Plan
  selects, since this changes what "token-budgeted assembly" actually means going forward.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: §8's Token-Counting
  Method section documents `kgmcp_char_heuristic_v1`'s ±20% tolerance as the standard the Phase 3
  pilot's budget-tolerance criterion is measured against — if the fix changes what payload subset is
  now bounded by that tolerance (full response vs statements-only), this section's own framing needs
  a one-line update reflecting the new real scope.
- `docs/parity_ledger/infrastructure.yaml`: a new entry is required for this ticket's real behavior
  change to `assemble_within_budget()`/`assemble_packet()`, per the ticket's own AC5 — and
  `INFRA-347`'s existing citations (`tools/knowledge_gateway_packet_assembly.py:643-670` and
  surrounding line numbers) must be corrected in place if this ticket's diff shifts any cited line
  number, per this repo's own citation-drift-correction convention (INFRA-347 itself already
  documents two prior line-shift corrections from sibling tickets — this ticket is a third).
- `docs/plans/knowledge-gateway-mcp-proposal.md` §21: if the re-measured #12 result changes the
  criterion's own status line in the proposal's own acceptance-criteria list, that line needs
  updating too (currently references "budget tolerance ... FAIL" language at multiple points, e.g.
  around line 1502/1521-1523/1581).

If Gap 2 is resolved by an additive corpus note (see Risks below, pending human review), that note's
own doc location is not yet decided here — left to Plan/human review, not assumed.

## Parity Ledger Overlap

- `INFRA-347` (`docs/parity_ledger/infrastructure.yaml:9593-9698`): the original entry documenting
  `deduplicate_statements()`/`assemble_within_budget()`/`kgmcp_char_heuristic_v1()`'s Phase 3
  hardening (content-hash dedup identity, conflict-aware dedup guard, budget-truncation visibility
  markers). `status: verified`, `priority: P1`. This ticket's Gap 1 fix directly modifies
  `assemble_within_budget()`, one of this entry's cited functions — its `v2_evidence` line numbers
  for `:643-670`-adjacent code will need correction once the fix lands (three prior corrections are
  already recorded in this same entry from sibling tickets' insertions elsewhere in the file, so a
  fourth correction following this ticket is consistent with established practice, not a
  first-of-its-kind edit).
- No other `docs/parity_ledger/infrastructure.yaml` entry (`INFRA-346`, `INFRA-348`–`INFRA-351`
  region) claims ownership of `assemble_within_budget()`'s budget-accounting scope itself — INFRA-348
  covers `evidence_dependencies`/Level 2 invalidation, a different concern that happens to share the
  same file.
- This entry is `P1`, not `P0` — no pre-existing `test_path` requirement beyond "a passing test,"
  which this ticket's own AC1/AC3 already require.

## Prior Work

- `stored_artifacts/TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT/investigation.md`: the
  ticket that hardened dedup identity (content-hash) and added the conflict-aware dedup guard and
  budget-truncation visibility markers this ticket must extend, not replace. Its own investigation
  already flags (line ~92-94) that `assemble_packet()`'s fixed step order is
  `render → dedup (step 5) → conflicts (step 7) → budget truncation` — i.e. dedup already runs before
  conflicts and before budget truncation; this ordering is unchanged by this ticket's own scope
  (Gap 1 only touches step 8's *measurement scope*, not the step order itself) and must be preserved.
- `stored_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/` (referenced via `docs/REGISTRY.yaml` and
  `INFRA-347`'s own third line-shift correction note): added the `parity_ledger` provider and its
  `render_candidates()` block — directly relevant context for Gap 2's newly-discovered
  `canonical_fragment_hash`-vs-`_content_hash()` dedup-key divergence noted above; not read in full,
  since Out of Scope explicitly excludes "re-opening or re-litigating Phase 4/5's own already-closed
  findings" — only its live behavioral effect on the corpus was traced, not its own design decisions.
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` and its
  runner `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`: supply the exact §21 #12 FAIL
  numbers cited above and the reusable 4-call-per-entry measurement methodology this ticket's own
  Scope requires reusing (not reimplementing) for the re-run.

## Risks and Open Questions

- **Gap 1 design tension is real and unresolved here, per the ticket's own instruction not to
  resolve it in Investigate.** `response["context"]`/`response["evidence"]` are what a caller
  actually reads — statements alone (bare extractive text with no source attribution beyond
  `evidence_ids`) are arguably not very useful without their supporting context/evidence entries.
  Three real candidate designs, none selected here:
  1. **Truncate context/evidence proportionally alongside statements** — extend
     `assemble_within_budget()` to measure the combined per-statement cost (statement text +
     matching context summary + matching evidence entry) as one atomic unit, and greedily include
     whole units (statement+context+evidence together) until the budget is exhausted. This keeps
     every included statement fully supported, but roughly **3× the effective per-statement cost**
     compared to today's statements-only accounting (since `context[].summary` duplicates
     `statement.text` for `context_search`/`graphify` sources), so far fewer statements would fit in
     the same `budget_tokens` than today — a real, disclosed behavior change to how much content a
     given budget yields.
  2. **Truncate context/evidence only after statements are chosen** — first select statements against
     (some fraction of) the budget as today, then fill remaining budget room with matching
     context/evidence, dropping context/evidence entries (but keeping their statements) once the
     budget is exhausted. This risks producing "orphan" statements with no supporting context/evidence
     — visible via a still-required truncation marker, but a materially different failure mode than
     today's "statement itself is dropped."
  3. **Split the budget into sub-budgets** (e.g. a fixed or caller-configurable ratio between
     statements and context/evidence) — most explicit, but introduces a new tunable the proposal
     doc has never defined, and needs its own default + tolerance definition before it could be
     measured against §21 #12's ±20%.
  Whichever order Plan selects, `conflicts[]` needs a real decision too — today always `[]` against
  real providers, so no live corpus data can validate a `conflicts[]`-truncation path end-to-end;
  any fix touching conflicts truncation would only be exercised by directly-constructed test
  fixtures, mirroring the same limitation `build_conflicts()`'s own module docstring already
  discloses for conflict detection itself.
- **Gap 1's re-measurement is not guaranteed to reach 7/7.** The ticket's own AC2 only requires an
  honestly reported new pass rate, "whatever it actually is" — Investigate does not predict the
  post-fix number; whichever design Plan selects should be evaluated against the real §21 #12
  methodology, not assumed to close all 5 current FAILs.
- **Gap 2's live finding (zero real cross-provider duplicates today) is not proof duplicates can
  never occur.** The only structural argument for a plausible future occurrence found during this
  investigation is the `canonical_fragment_hash`-vs-`_content_hash()` divergence above — but that
  requires a parity_ledger `found=True` result whose `text` is byte-identical (after `.strip()`) to
  a context_search excerpt, which no live corpus entry currently produces (Q3's only parity-selecting
  entry returns `found=False`). No entry is "close" to producing this — Q3's context_search results
  and parity_ledger's not-found status are unrelated; there is no principled, narrow, real-evidence
  reason found in this investigation to expect a corpus entry to organically develop this collision
  without a corpus change. Constructing one would require either (a) a new corpus entry whose query
  matches both a parity_ledger record and a context_search-indexed doc chunk with textually identical
  content, or (b) accepting this as a structurally distinct, real, additional finding (the
  hash-formula divergence) that is arguably its own follow-up concern rather than something this
  ticket's Gap 2 (which is scoped to "duplicate content the frozen corpus already incidentally
  surfaces") can close via corpus extension. **This is flagged as a decision point for Plan/human
  review, not resolved here**, per the ticket's own Assumptions/Open Questions section.
- **Routing has changed since the Phase 3 measurement was written.** The ticket's own framing ("only
  1 of 7 entries even queries both providers") is now stale — Q3 also selects a second provider live
  today (parity_ledger, though it returns no content). This does not change Gap 2's substantive
  finding (0 real duplicates) but should be corrected in any human-facing summary derived from this
  investigation, to avoid citing the outdated "1 of 7" framing as still-current.

## Anti-Drift Hazards

- Do not "fix" Gap 1 by multiplying `statements[]`'s measured cost by a constant factor (e.g. ×3) to
  approximate context/evidence duplication — this is exactly the `len(candidates) * constant`
  anti-pattern `assemble_within_budget()`'s own docstring explicitly names and rejects
  (`tools/context_packet_assembler.py:287`). Any fix must call `kgmcp_char_heuristic_v1()` on the
  real `ContextEntry.summary`/`EvidenceEntry` text being included, exactly as `statements[]` already
  does.
- Do not reorder `assemble_packet()`'s fixed pipeline (`render → dedup → conflicts →
  truncation → §16 fallback`) as a side effect of extending truncation's measurement scope — this
  ordering is explicitly called out as "load-bearing and must not be reordered"
  (`assemble_packet()` docstring, `:727-730`) by a prior ticket; Gap 1's fix must stay inside step 8
  (or add clearly-scoped new steps after it), not touch step 5/7's relative order.
- Do not let a Gap 1 fix silently change `PacketAssembly.budget_returned`'s existing meaning
  (currently: sum of included statement costs only) without updating every caller/test that reads
  it as such — `test_budget_returned_never_exceeds_budget_requested` and
  `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate` both currently encode
  the statements-only assumption.
- Do not add a synthetic/fabricated duplicate-content corpus entry and present it as
  "corpus-derived" — the ticket's own Scope explicitly forbids this, and Out of Scope forbids editing
  any existing frozen entry. Any corpus extension must be additive, narrow, and disclosed for human
  review, not unilaterally added and closed out.
- Do not conflate the `canonical_fragment_hash`-vs-`_content_hash()` divergence (a real, newly-found,
  distinct structural gap in parity-ledger dedup identity, never before documented) with the ticket's
  own Gap 2 scope (multi-provider dedup coverage on the frozen 7-entry corpus) — report both, but do
  not silently fold one into the other's acceptance criterion without disclosure.
- Do not "fix" the parity_ledger hash-formula divergence as an unscoped drive-by while investigating
  Gap 2 — Out of Scope excludes "any change to Level 1/Level 2 cache mechanics, routing, the Parity
  adapter" and Related Tickets marks the parity adapter ticket as already DONE; this divergence
  should be reported for Plan/human review, not silently patched here or in Implementation without
  explicit scope approval.
