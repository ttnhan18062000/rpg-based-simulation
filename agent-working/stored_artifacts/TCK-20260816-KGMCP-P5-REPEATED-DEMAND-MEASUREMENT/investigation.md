---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT

## Current Behavior

This ticket does not touch any executable gateway/cache code path. It measures a property of
this repository's own real historical usage. The relevant "current behavior" is therefore: what
real data sources exist that could evidence "agents ask semantically repeated project questions,"
and what the Knowledge Gateway MCP currently does with equivalent-but-differently-worded queries.

- `tools/knowledge_gateway_cache.py::compute_lookup_identity()` / `compute_context_packet_lookup_
  identity()` build cache identity from provider-native IDs only (ticket ID, parity ID, symbol
  name, doc registry ID) plus normalized intent/filters/budget/routing-policy version — confirmed
  by direct read. There is no canonicalization or alias table; two different-but-equivalent
  phrasings of the same question currently produce different lookup identities and therefore
  different cache rows. This is exactly the gap Phase 5's three proposal bullets exist to close.
- `tools/agent-monitoring/kgmcp_baseline_corpus.py::CORPUS` — 7 entries, one per §8 routing-shape
  row, explicitly built unique-per-entry (module docstring: "5 of the 7 entries also carry one of
  the 5 `use_case` IDs... the other 2 carry `use_case=None`"; no duplicate/near-duplicate query is
  present by construction). Confirmed unusable for this measurement, exactly as this ticket's own
  Scope states — there is no wording variance to detect within a 7-entry, deliberately-distinct
  corpus.
- Three real candidate data sources were read directly (`tickets/working_log.csv`,
  `agent-monitoring/retro/`, `agent-monitoring/events.jsonl`) and assessed below.

### Candidate source 1 — `agent-monitoring/retro/*.md` (REJECTED as unusable)

Read `agent-monitoring/retro/RETRO-2026-W33.md` (most recent weekly retro) in full. Its content is
exclusively pre-aggregated statistics: run counts by tag/tier/agent, gate-failure counts, DONE
rates. It contains **no per-question or per-investigation free text** — only counts. There is
nothing in any retro file to compare for semantic equivalence between two individual questions.
This source is structurally incapable of supporting this measurement and is rejected outright, not
merely deprioritized.

### Candidate source 2 — `tickets/working_log.csv` (USABLE, used as a secondary/corroborating source)

1,413 data rows (1,414 lines including header), columns
`timestamp,ticket_id,title,status,summary,artifacts_path`, spanning 2026-03-21 through
2026-08-16 — real, append-only history of completed ticket work, one row per closed ticket. `title`
and `summary` are real, human/agent-authored free text describing what was investigated/built. This
is a real, non-synthetic, non-corpus signal: if two unrelated tickets' own title+summary reference
the same specific code entity while asking the same kind of question, that is evidence of
repeated-question demand.

### Candidate source 3 — `agent-monitoring/events.jsonl` (USABLE, used as the PRIMARY source)

6,573 lines. Filtering to `phase == "Investigate"` (the standard workflow phase name emitted by the
`investigator` agent) yields 622 events; deduplicating to one summary per `run_id` (a ticket keeps
only its first recorded Investigate event) yields **521 distinct tickets with a real Investigate-
phase summary**. This is the more direct signal for "what question did an agent go investigate,"
since it is the investigator agent's own real, contemporaneous finding-summary for that ticket's
actual question — closer to "the question asked" than a post-hoc completed-work title. Chosen as
primary; `working_log.csv` used as a secondary, larger-sample corroboration (it also covers tickets
from before `agent-monitoring/` existed).

## Mechanics / Engine Constraints

This is an agent-infrastructure/tooling ticket (`layer: ai` — this repo's own convention, per
`registries/layer_registry.jsonl`'s `ai` entry note: "this repo's layer:ai means the agent system,
not gameplay cognition"). No `docs/mechanics/` Mechanics Bible chapter governs this work — no
domain simulation logic (combat, economy, strategy, world) is touched. The governing documents are:

- `docs/plans/knowledge-gateway-mcp-proposal.md` §11.2 ("Lookup Identity and Equivalent
  Questions") — the conservative, multi-signal equivalence method (normalize → extract stable
  identifiers → classify intent → compare identity+intent agreement) this ticket's own measurement
  method is required to mirror, and explicitly rules out raw-string-only and embedding-only
  equivalence.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18.1 ("Repeated Knowledge Demand") — states the
  measurement should use "safe deterministic intent, provider-native entity IDs, normalized
  filters, and the keyed query hash" for demand grouping, framed there for Phase 6 but explicitly
  is the direct methodological precedent this ticket applies to Phase 5 (per the epic ticket's own
  framing).
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 5 — the three bullets this measurement
  gates ("Add canonical entity IDs and aliases," "Reuse results across compatible phrasings," "Add
  conservative semantic candidate matching with deterministic validation").
- `tmp/mcp-followup-instruction.md` §7 ("Measure Repeated Knowledge Demand") — the direct
  precedent this ticket's whole premise applies (there, to Phase 6; here, for the first time, to
  Phase 5).

## Real Measurement Method

Implemented in `staging_artifacts/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT/
investigate_measurement_script.py` (committed here for traceability; not wired into any recurring
runner — this is Investigate-phase preliminary measurement, per this ticket's own instruction, and
Implement decides separately whether to formalize it into a committed `tools/agent-monitoring/
kgmcp_phase5_*.py` runner mirroring Phase 1-4's pattern).

1. **Normalize**: lowercase, collapse whitespace.
2. **Extract stable identifiers** per summary, four kinds:
   - Subsystem-topic tags via `tools/registry_query.py::candidate_tags_from_text()` — the real,
     existing seed-vocabulary substring matcher against `registries/tag_registry.jsonl`, already
     used by `create-tickets.js`'s Investigate phase and this same investigator agent's own "Finding
     Prior Work" step. Reused unmodified, not reimplemented.
   - CamelCase-shaped code-symbol tokens (regex requiring an actual lowercase *letter*, not just a
     digit, between two capitals, min length 6 — see Anti-Drift/Risks below for why this was
     tightened after a first pass produced false positives).
   - Repo-relative file paths (`src/…`, `docs/…`, `tools/…`, `tests/…`).
   - Referenced ticket IDs (`TCK-YYYYMMDD-…`) and parity-ledger entry IDs (`INFRA-206`,
     `STRAT-227`, etc.).
3. **Classify intent** into 6 buckets (`mechanism_explanation`, `root_cause_debugging`,
   `completeness_verification`, `feasibility_evaluation`, `location_lookup`, `other`) via a
   keyword-rule classifier. This bucket set is informed by, but does not reuse code from, the 7 real
   `ROUTING_SHAPES` already used throughout Phase 0-4 (`tools/knowledge_gateway_router.py::
   ROUTING_TABLE`, `kgmcp_baseline_corpus.ROUTING_SHAPES`) — no free-text-to-shape classifier exists
   anywhere in this repository to reuse directly (confirmed by grep of `knowledge_gateway_router.py`
   and `kgmcp_baseline_corpus.py`), so this ticket's classifier is new, disclosed as such, and
   collapses the routing-shape vocabulary into 6 coarser investigation-intent buckets appropriate
   for terse finding-summaries rather than user-facing queries.
4. **Compare identity+intent agreement**: two *different* tickets' summaries count as a
   **conservative repeated-demand pair** only if (a) same intent bucket AND (b) they share at least
   one specific extracted identifier (CamelCase symbol, file path, ticket ID, or parity-entry ID).
   Shared subsystem-topic **tag alone**, with no specific identifier overlap, is explicitly **not**
   counted — reported separately as a weaker signal — because tags like `mcp`/`cognition` are
   shared by dozens of otherwise-unrelated tickets (confirmed: `RETRO-2026-W33.md` shows 32 runs
   tagged `mcp` in one week alone) and would produce an unusably noisy, non-conservative result if
   used as the sole matching signal. This mirrors §11.2 step 4's own "reuse only when intent and
   resolved entities agree" rule.

This is explicitly **not** raw-string similarity alone (no string-distance metric is used at all)
and **not** embedding similarity alone (no embedding model was used — `python3
tools/knowledge_search.py query ...` confirmed unavailable, "Warning: sentence-transformers not
installed"; this is disclosed as a real tooling limitation, not silently worked around). The method
is multi-signal: registry-backed tag extraction + regex entity extraction + keyword intent
classification + conjunctive comparison, genuinely mirroring §11.2's shape.

## Real Results

### Primary source — `agent-monitoring/events.jsonl`, Investigate-phase summaries (521 tickets)

Intent bucket distribution: `mechanism_explanation` 198, `other` 174, `completeness_verification`
82, `root_cause_debugging` 49, `location_lookup` 10, `feasibility_evaluation` 8.

- **17 conservative repeated-demand pairs** found (same intent + shared specific identifier,
  different tickets) — 15 sharing a real code symbol or file path (the strongest signal), 2 sharing
  only a referenced ticket/parity-entry ID.
- **427 pairs** shared an intent bucket and a subsystem-topic tag but **no** specific identifier —
  correctly **not counted**.
- **30 of 521 distinct tickets (5.8%)** appear in at least one conservative repeated-demand pair.
- Pairwise density: 17 pairs out of C(521,2) = 135,460 possible pairs = **0.0126%** of all possible
  ticket-pairs.

Full pair-level data: `staging_artifacts/.../investigate_events_jsonl_measurement_output.json`.

### Secondary/corroborating source — `tickets/working_log.csv` title+summary (1,411 tickets with text)

Intent bucket distribution: `completeness_verification` 517, `other` 455, `root_cause_debugging`
246, `mechanism_explanation` 166, `feasibility_evaluation` 15, `location_lookup` 12.

- **372 conservative repeated-demand pairs** (282 sharing a real code symbol/file path).
- **10,347 tag-only pairs** correctly not counted.
- **261 of 1,411 distinct tickets (18.5%)** appear in at least one pair.
- Pairwise density: 372 / C(1411,2) = 994,755 possible pairs = **0.0374%**.

Full pair-level data: `staging_artifacts/.../investigate_working_log_measurement_output.json`.

### Honest qualitative reading of the matched pairs (not just the count)

Reading a sample of the matched pairs directly (both files' `pairs`/`pairs_sample` fields, and the
15-pair console sample retained in this investigation) shows the *large majority* are **not** "the
same question asked twice with different wording" — the literal scenario Phase 5's three bullets
exist to catch. Instead they are natural **incremental, sequential investigation of an evolving
codebase**: a later ticket, often weeks or months after an earlier one, independently touches the
same symbol/file/parity-entry while asking a *different* specific question about it (e.g.
`TCK-20260619-E21B-REGEN-SERVICE` found `ResourceNodeUpdate` had no `charges_set`; ~7 weeks later
`TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION` re-examined the same class and found
`ResourceNodeUpdate` "already exists" — a genuinely different question, not a repeat). A minority of
pairs are closer to genuine same-question recurrence (e.g. two same-day `E-phase` sibling tickets
both citing INFRA parity entries in a shared checklist, or `TCK-20260805-COMMUNITY-SKILL-SWAP-
DISCLOSED`/`-UNDISCLOSED` both independently running the identical `WebSearch` sub-question). This
qualitative pattern held in both data sources.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: needs a new entry (next available ID `INFRA-355`,
  confirmed by `grep -o "INFRA-[0-9]*" ... | sort -n | tail`, current max `INFRA-354`) certifying
  this ticket's measurement methodology as sound, mirroring `INFRA-344`/`INFRA-353`'s precedent —
  the entry certifies the measurement tool/method is real, correct, and applied consistently; it
  does not itself certify that Phase 5 is warranted.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 5's three bullets need an honest
  annotation recording this ticket's real finding (marginal, low-density, mostly-not-literal-repeat
  demand; economics of even a genuine hit remain unproven per Phase 3/4) rather than being marked
  Done or silently left unannotated — mirroring the Phase 5 epic's own AC4.
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md`: does not yet
  exist; needs creation (mirroring the existing `phase3_pilot_acceptance_measurement.md`/
  `phase4_direct_tool_comparison.md` pattern in the same directory) to hold the full real
  count/rate/method detail this investigation summarizes, as the durable record for this ticket's
  measurement — confirmed via `grep -rl` that only the proposal doc, the parity ledger, and
  `docs/REGISTRY.yaml` (auto-regenerated) currently reference the Phase 3/4 equivalents, so no other
  doc needs a cross-reference update.

## Parity Ledger Overlap

- No existing `docs/parity_ledger/*.yaml` entry currently describes repeated-demand measurement for
  Phase 5 specifically. `INFRA-344` (Phase 2 baseline recomparison) and `INFRA-353` (Phase 4
  workflow-recommendation evaluation) are the direct format precedents for the new entry this ticket
  requires (see Docs Requiring Update). Neither is P0; this ticket's own new entry should be `P1` or
  `P2` (methodology-certification entries in this series have used `P1`/`verified`), not `P0` — no
  P0 entry is implicated, so no `test_path` regression obligation beyond this ticket's own new
  test(s) (see test_plan.md).
- `docs/parity_ledger/infrastructure.yaml` INFRA-206/207/208/212/213/215/220/275 and others appear
  incidentally in the measured summaries (as `parity` identifier matches) but are unrelated
  subsystems' entries, not overlapping this ticket's own scope.

## Prior Work

- `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION` (DONE) — direct methodological
  precedent: an honest "evaluate before building" ticket whose real, negative finding was itself
  the complete, valid deliverable, with no code/workflow/skill file touched. This ticket follows the
  identical shape.
- `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON` (DONE) — supplies the real 7/7 negative gateway-
  vs-direct-tool comparison this ticket's recommendation weighs (see Risks/Recommendation below).
- `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` (DONE) — supplies the real budget-tolerance
  FAIL (2/7 pass) and the real "token count does not improve" finding this ticket's recommendation
  also weighs.
- `TCK-20260705-TAG-REGISTRY-QUERY` / `TCK-20260720-TAG-TOUCHPOINT-CLEANUP` — origin of
  `tools/registry_query.py::candidate_tags_from_text()`, reused unmodified by this ticket's
  measurement script for identifier extraction.

## Cross-Reference: Repeated Demand vs. Proven Per-Hit Economics

Even taking the higher, secondary-source reading (18.5% of tickets, 0.037% of all possible pairs)
at face value as *some* real, non-zero repeated-question demand, the decisive question this ticket's
own Scope requires answering is whether **resolving** that demand via broader cache-hit matching
would be net-positive, given Phase 3/4's own real, already-measured per-hit economics:

- **Phase 3** (`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`):
  criterion #12 (budget respected within tolerance) is a real **FAIL, 2/7** — `context_search`-
  routed queries' full response payload runs 2.3×–2.4× over the ±20% tolerance, because
  `assemble_within_budget()` only bounds `statements[]`, not `context[]`/`evidence[]`/`conflicts[]`.
  Criterion #18's token half is also a real **FAIL** — a genuine Level-2-warm cache **hit**'s own
  median full-payload token count (2865) is *larger* than both the cold baseline (2846) and the
  freshly-measured Level-1-warm baseline (2615). Only the latency half of #18 improves.
- **Phase 4** (`docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`): a
  fresh, live, paired run found the gateway **slower (1.31×–3.76×) and heavier in tokens
  (1.04×–2.93×) than direct tool use for all 7 of 7 corpus entries**, with hand-written quality
  judgments favoring direct tools 6 of 7 times and 0 of 7 favoring the gateway.

Both of these are measurements of the gateway's behavior **on a query that already reaches the
existing, provider-native-ID cache identity** — i.e. exactly the case Phase 5 would *not* need to
change. Phase 5's three bullets do not touch `assemble_within_budget()`, the redaction/cache-write
token overhead, or per-call routing cost — they only broaden **which additional queries** map onto
that same identity. Since the per-hit economics of the cases Phase 5 would newly route into a cache
hit are, if anything, *identical in kind* to the cases already measured (same cache/packet
machinery, same token-accounting gap), there is no evidence a broadened-match hit would behave any
better than the already-measured hits — it would very plausibly reproduce the same FAIL/negative
outcome, just triggered more often.

## Risks and Open Questions

- **The equivalence-detection method's own false-positive risk is real and was caught mid-
  measurement, not merely theoretical.** A first-pass CamelCase regex matched bare ALL-CAPS acronyms
  (`INFRA`, `STRAT`, `TOWN`) and digit-joined pseudo-CamelCase tokens (`E2E`) as if they were
  specific code symbols, inflating the working-log pair count from 748 to a corrected 372 once the
  regex was tightened to require an actual lowercase letter (not merely a digit) between two
  capitals and a minimum 6-character length. This is disclosed rather than silently fixed-and-hidden
  because it demonstrates the method needed a real correction pass to stay conservative, and a
  residual risk remains that a small number of the 17/372 counted pairs are still coincidental token
  overlap rather than genuine topical recurrence (spot-checked a sample above; not exhaustively
  hand-verified for every pair).
- **No embedding-similarity tooling was available** (`sentence-transformers` not installed in this
  environment). Per this ticket's own instruction this is an acceptable, disclosed limitation, not a
  blocker — the method does not depend on embeddings, matching §11.2's own point that embedding
  similarity alone would be insufficient regardless.
- **This measurement approximates "agents asking the same project question" via ticket-level
  investigation-summary recurrence, not literal gateway call logs** — the Knowledge Gateway itself
  does not yet log individual free-text queries (raw prompts are deliberately not persisted, per
  proposal §10.3/§18.1), so no more direct signal exists anywhere in this repository. This is the
  best real available proxy, not a perfect one, and is disclosed as such.
- **Open question this Investigate phase does not resolve**: whether the ~5.8%–18.5% ticket-
  involvement rate found here would, in practice, translate into materially more real gateway
  cache-hit traffic if Phase 5 were built — that depends on future agent behavior (would agents
  actually call the gateway for these recurring topics at all, given Phase 4's own finding that
  direct tool use is currently preferred 6 of 7 times), which cannot be measured from historical
  data alone. Flagged, not assumed either way.

## Anti-Drift Hazards

- Do not round the 5.8%/18.5% ticket-involvement figures up into a stronger "demand is proven"
  claim than the data supports, or down into "no demand exists" — both would misstate a real,
  small, mixed-quality positive signal.
- Do not let a future Plan/Implement phase quietly reuse the 748-pair (pre-regex-fix) number instead
  of the corrected 372 — the corrected script and its output are what's committed here.
- Do not treat this ticket's own new `INFRA-355` parity entry (once written by Parity phase) as
  certifying that Phase 5 is warranted — per the `INFRA-344`/`INFRA-353` precedent, it certifies only
  that the measurement method itself is sound.
- Do not scope-creep into building any part of Phase 5's canonical-entity-ID or semantic-matching
  machinery in this ticket — this ticket is measurement-and-recommendation only, per its own Out of
  Scope.
