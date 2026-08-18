---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing]
---

# Knowledge Gateway MCP — Phase 4 Workflow Integration Recommendation

Source ticket: `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`.

## Headline: This document creates no mandatory phase, gate, or ticket step

This is an evaluation-only document. No `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`,
or `.claude/agents/*.md` file changed in the ticket that produced it, and nothing in this
document should be read as instructing any of those files to change. Every recommendation below
is advisory, per `tmp/mcp-followup-instruction.md` §1 ("the gateway must be treated as a general
repository utility, not as a workflow phase or mandatory ticket step... should not mechanically
require it in specific phases").

## Candidate 1 — Scope and Investigate phases (`search_docs` + `graphify query`)

**Call sites:** `.claude/workflows/implement-ticket.js:131-134` (Scope), `:497-500` (Investigate,
mirrored in `.claude/agents/investigator.md:12-13`), `.claude/workflows/simq-audit.js:448-451`,
`.claude/skills/create-tickets/SKILL.md:49-59`.

**Evidence:** Phase 1 cold-call measurements
(`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`) show gateway calls
at 1469.7–5325.8 ms and 2649–7633 tokens per entry, against a re-derived Phase 0 baseline of
1870.64 ms / 2527.14 tokens for the existing `search_docs` + `graphify` pair. The real, mixed
result: 4 of 7 corpus entries measure slower (1.35x–2.85x), while the 3 fastest entries (Q3, Q4,
Q6 — all single-provider `context_search`-routed) measure *faster* than baseline (0.79x–0.90x);
Q6 specifically is the fastest gateway call in the whole corpus, not a "1.3x slower" data point.
Token count, by contrast, is heavier for all 7 entries without exception (1.05x–3.0x) — the
overhead is universal for tokens but not for latency. These four call sites issue
a one-shot query keyed on a per-ticket title/summary, which is textually unique per ticket, so a
genuinely warm Level 2 cache hit — the only measured configuration
(`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`) where the
gateway beats the baseline on latency (median 1438.21 ms vs. 2521.78 ms cold / 1543.32 ms
Level-1-warm) — is structurally rare at these call sites, since Level 2 only pays off on a
semantically-identical repeat of the same query. The realistic case here is the cold case.

**Recommend against.** Do not add a gateway call at these four sites. This does not reopen this
repo's existing `search_docs`/`graphify query` Hard Rule ordering, which predates the gateway and
is out of scope to re-litigate here.

## Candidate 2 — Document-Update / doc-updater phase

**Call site:** `.claude/workflows/implement-ticket.js:774-838` (Phase 5a), `.claude/agents/doc-updater.md`.
No `search_docs`, `graphify`, or gateway call exists here today.

**Evidence:** `knowledge_status_response.schema.json` has no per-document, per-path field
anywhere in its schema (`gateway_version`, `reported_schema_version`, `providers`,
`cache_entry_counts`, `cache_hit_rate`/`cache_miss_rate`/`cache_stale_rejection_rate`,
`latency_summary_ms`, `provider_fallback_rate`, `recent_invalidation_reasons`, `branch_scope`,
`cache_rebuildable` — gateway-wide/aggregate only). It cannot answer "is
`docs/mechanics/03_economic_laws.md` stale relative to the current diff," which is exactly what
`tools/gate_checks/doc_staleness_check.py` already does deterministically today
(`implement-ticket.js:840-902`). `knowledge_context` with `changed_paths` could trigger
`revalidate_cache_row()` / `revalidate_context_packet_row()` (confirmed live via Phase 3's
AC6/#7/#8 PASS results), but that only revalidates an already-cached packet — it performs no
fresh discovery for a first-time-touched doc, which is doc-updater's actual situation (target
paths are already injected from `investigation.md`, never discovered by doc-updater itself). No
measured corpus entry in Phases 0–3 tests this call pattern at all — all 7 entries are
natural-language investigation-style queries.

**Insufficient evidence to recommend for.** The gateway's actual capability does not map to the
retro's diagnosed problem (`agent-monitoring/retro/RETRO-2026-W33.md`'s Notes section names
doc-staleness handling as this period's one recurring gap). That retro's own suggested fix — a
prompt-content change to `doc-updater.md`'s base instructions — is not a knowledge-tool call and
does not compete with or require this recommendation either way.

## Candidate 3 — Architecture Review (`docs/REGISTRY.yaml` filter)

**Call site:** `.claude/agents/architecture-reviewer.md:9-11` ("Registry Lookup") — a flat-file
filter on `type: doc`, `status: active|authoritative`, `layer: <plan_layer>`, no LLM/MCP round
trip.

**Evidence:** `agent-monitoring/retro/RETRO-2026-W33.md` shows Architecture-Verify has the
highest phase-average cost-proxy-score (85.5) and most raw failures (35/127), but its own Notes
section (based on direct inspection) states these rejections are "almost all substantive
catches... not noise" — the cost driver is review depth, not a slow context-discovery step. No
gateway measurement in Phases 1–3 shows any configuration beating a flat-file registry filter on
latency (the registry filter has zero network/subprocess round-trip cost by construction).

**Recommend against.** No evidenced context-gathering bottleneck exists at this phase for a
gateway call to solve.

## Candidate 4 — Dormant shadow-packet hook (`SHADOW_CONTEXT_PACKET_ENABLED`)

**Call site:** `.claude/workflows/implement-ticket.js:528-588` — off by default, fail-open,
`timeout 10s`, writes to `agent-monitoring/events.jsonl` on a disjoint negative `seq` range,
currently passes an empty candidate set (no real retrieval pipeline wired in;
`tools/hybrid_retrieval.py` wiring explicitly deferred).

**Evidence:** This is the one place in the repo already structurally shaped exactly as
`tmp/mcp-followup-instruction.md` §1 asks integrations to be: opportunistic, non-mandatory,
fail-open, off by default. But wiring it to make real `knowledge_context` calls today would hit
the same Investigate-phase usage pattern analyzed in Candidate 1 — a per-ticket-unique query,
realistically landing in the cold case, which measures heavier in tokens for all 7 corpus entries
(1.05x-3.0x) and slower in latency for 4 of 7 (1.35x-2.85x) — the 3 fastest gateway calls in the
corpus (Q3, Q4, Q6) do beat the baseline on latency alone, but token overhead remains universal.
Separately, Phase 3's own measurement
(`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`) discloses
two still-open gaps even in the best-case warm scenario: budget enforcement (§21 #12) FAILs for
5/7 entries because `assemble_within_budget()` only accounts `statements[]`, not
`context[]`/`evidence[]`/`conflicts[]`, so the full payload a caller actually pays for is
structurally unbounded; and even a genuine Level 2 hit's median token count (2865) is not smaller
than either baseline (Phase 1 cold: 2846; Level-1-warm: 2615) — a real FAIL on AC4/§18's token
half.

**Recommend against enabling it today. Flag as the correct landing spot for a future ticket**,
specifically conditioned on a later ticket first closing both of Phase 3's disclosed gaps above
(§12 budget enforcement covering the full payload; §18's token-count regression on a genuine
Level 2 hit). Until both close, wiring real calls into this hook reproduces the same regression
already measured at Candidate 1, not an improvement.

## Evidence honesty note

The Level 1 cache-size cap (`MAX_PAYLOAD_BYTES`) was 8192 bytes during Phase 2, producing 0/7
genuine hits (every real response payload, 10.6–30.5 KB, was rejected as `oversized_payload`).
`TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` later raised the cap to 65536 and
confirmed 7/7 hits at the new cap, and Phase 3 ran after that hotfix. Both numbers are real and
are reported in their true chronological context above (Candidate 1/4 analysis uses Phase 3's
post-hotfix numbers where warm-cache economics are discussed) — the pre-hotfix 0/7 result is not
allowed to be silently erased by the later fix, since a workflow integration shipped against the
Phase-2-era state would genuinely have seen 0/7 hits.

## Open question not settled by this document

Whether a future, purpose-built cache-warming strategy (pre-populating Level 2 for top-N repeated
query shapes, per `tmp/mcp-followup-instruction.md` §7) could change the Investigate-phase
economics above is genuinely unmeasured — `RETRO-2026-W33.md`'s Retrieval Quality section reports
"No cache-level data this period," and §7's study has not been done. This document does not
assume an answer either way.
