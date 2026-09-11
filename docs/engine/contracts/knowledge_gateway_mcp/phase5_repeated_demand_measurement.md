---
status: historical
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing]
---

# Knowledge Gateway MCP — Phase 5 Repeated-Demand Measurement Results

Source ticket: `TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`. This measures the real, honest
count/rate of repeated or semantically-equivalent project questions across this repository's own
historical Investigate-phase summaries and completed-ticket log text — the specific problem
proposal §20 Phase 5's three bullets (canonical entity IDs/aliases, reuse across compatible
phrasings, conservative semantic candidate matching) exist to solve. This is **not** a gateway
call-site measurement: no `tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, or any other gateway/cache/router source file was read,
called, or modified by this ticket's own runner.

## Data source and method

**Primary source**: `agent-monitoring/events.jsonl`, `phase == "Investigate"` events, deduplicated
to the first event per ticket `run_id` — 521 distinct tickets with a real Investigate-phase summary,
frozen as a point-in-time snapshot (`tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.
json`) as of this ticket's own Implement step, **explicitly excluding this ticket's own run_id**
(`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`) to avoid the confirmed-live self-contamination
hazard where this ticket's own mandatory Investigate-phase monitoring write would otherwise land in
the exact dataset it measures (the raw, unfiltered live file yields 522 records; the correct,
self-contamination-safe count is 521).

**Secondary/corroborating source**: `tickets/working_log.csv`'s own `title`+`summary` columns —
1,411 tickets with non-empty text, frozen the same way
(`tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json`).

Both sources are real, non-synthetic, non-corpus production data — not the frozen 7-entry
`kgmcp_baseline_corpus.CORPUS` (deliberately built unique-per-entry, structurally incapable of
demonstrating repeated demand), and not `agent-monitoring/retro/*.md` (pre-aggregated counts only,
no per-question free text to compare).

The equivalence-detection method mirrors proposal §11.2's conservative, multi-signal approach —
never raw-string-only, never embedding-only (no embedding-similarity tooling was available in this
environment; disclosed, not silently worked around):

1. **Normalize**: collapse whitespace.
2. **Extract stable identifiers**, four kinds: subsystem-topic tags (via
   `tools/registry_query.py::candidate_tags_from_text()`, imported unmodified); CamelCase
   code-symbol tokens (regex requiring an actual lowercase letter between two capitals, minimum
   6-character length); repo-relative file paths (`src/…`, `docs/…`, `tools/…`, `tests/…`);
   referenced ticket IDs and parity-ledger entry IDs.
3. **Classify intent** into 6 buckets (`mechanism_explanation`, `root_cause_debugging`,
   `completeness_verification`, `feasibility_evaluation`, `location_lookup`, `other`) via keyword
   rules.
4. **Compare**: two different tickets/rows count as a conservative repeated-demand pair only if (a)
   same intent bucket (excluding `other`, too weak) AND (b) at least one overlapping *specific*
   identifier (CamelCase symbol, file path, ticket ID, or parity-entry ID) — subsystem-topic **tag
   alone** is explicitly not counted, and reported separately as a weaker signal.

**Disclosed correction mid-measurement**: a first-pass CamelCase regex without the lowercase-letter
and minimum-length requirements matched bare ALL-CAPS acronyms (`INFRA`, `STRAT`, `TOWN`) and
digit-joined pseudo-CamelCase tokens (`E2E`) as specific code symbols, inflating the secondary-source
pair count from 748 to a corrected 372 once tightened. The corrected regex and its 372/17 output are
what this ticket commits — the pre-fix 748 number is never reused anywhere.

## Real numbers

| Source | Total tickets | Conservative repeated-demand pairs | Strong (symbol/path) pairs | Tickets involved | Pairwise density |
|---|---|---|---|---|---|
| Primary (`events.jsonl`) | 521 | **17** | 15 (2 ticket/parity-ID-only) | 30 / 521 (**5.8%**) | 0.0126% |
| Secondary (`working_log.csv`) | 1,411 | **372** | 282 | 261 / 1,411 (**18.5%**) | 0.0374% |

Tag-only pairs (same intent, shared subsystem-topic tag, **no** specific identifier overlap) are
explicitly **not counted** toward the conservative totals above: 427 for the primary source, 10,347
for the secondary source.

## Qualitative reading

Reading a sample of the matched pairs directly shows the large majority are **not** "the same
question asked twice with different wording" — the literal scenario Phase 5's three bullets exist to
catch. Instead they are natural, incremental, sequential investigation of an evolving codebase: a
later ticket, often weeks or months after an earlier one, independently touches the same
symbol/file/parity-entry while asking a genuinely *different* specific question about it. Example:
`TCK-20260619-E21B-REGEN-SERVICE` found `ResourceNodeUpdate` had no `charges_set`; roughly seven
weeks later `TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION` re-examined the same class and found
`ResourceNodeUpdate` "already exists" — a different finding about the same symbol, not a repeat. A
minority of pairs are closer to genuine same-question recurrence — for example
`TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`/`TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED`, two
same-day sibling tickets both independently running an identical `WebSearch` sub-question. This
qualitative pattern held in both data sources.

## Cross-reference to Phase 3/4 economics

Even taking the higher, secondary-source reading (18.5% of tickets, 0.0374% of all possible pairs)
at face value as *some* real, non-zero repeated-question demand, the decisive question is whether
**resolving** that demand via broader cache-hit matching would be net-positive, given Phase 3/4's own
real, already-measured per-hit economics:

- **Phase 3** (`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`):
  a real **FAIL, 2/7** on budget-tolerance (`context_search`-routed queries' full response payload
  runs 2.3x-2.4x over the ±20% tolerance). The token half of criterion #18 is also a real **FAIL** —
  a genuine Level-2-warm cache **hit**'s own median full-payload token count (2865) is *larger* than
  both the cold baseline (2846) and the Level-1-warm baseline (2615).
- **Phase 4** (`docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`): a
  fresh, live, paired run found the gateway slower (1.31x-3.76x) and heavier in tokens
  (1.04x-2.93x) than direct tool use for all 7 of 7 corpus entries, with hand-written quality
  judgments favoring direct tools 6 of 7 times and 0 of 7 favoring the gateway.

Both of these measure the gateway's behavior on a query that already reaches the existing,
provider-native-ID cache identity — exactly the case Phase 5 would *not* need to change. Phase 5's
three bullets do not touch `assemble_within_budget()`, the redaction/cache-write token overhead, or
per-call routing cost — they only broaden **which additional queries** map onto that same identity.
A broadened-match Phase 5 hit would reach the *same* cache/packet machinery already measured
unfavorable, so there is no evidence a broadened hit performs any differently — it would very
plausibly reproduce the same FAIL/negative outcome more often, not resolve it.

## Recommendation

Proceed with Phase 5's remaining two bullets (canonical entity IDs/aliases; conservative semantic
candidate matching) only after Phase 3's own disclosed gaps (budget-tolerance FAIL; token-count
regression on a genuine cache hit) close — not now, not never.

## Closing note

This document's own real finding does NOT itself declare Phase 5 built, does not modify any gateway
source file, and does not authorize or block any future child ticket — it records a real,
reproducible measurement and the reasoning drawn from it, nothing more.

## Cross-references

- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` — the committed runner
  that produced this measurement, reading only the frozen Step 1 snapshot fixtures.
- `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json` — full committed
  numbers (primary: full 17-pair list; secondary: a 20-pair sample of the full 372).
- `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` /
  `kgmcp_phase5_working_log_snapshot.json` — the frozen input snapshots.
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`,
  `phase4_direct_tool_comparison.md` — the real per-hit economics findings this recommendation
  weighs.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §11.2, §20 Phase 5.
