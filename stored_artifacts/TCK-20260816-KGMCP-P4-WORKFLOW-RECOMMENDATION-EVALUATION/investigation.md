---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION

## Current Behavior

### Every real "reach for project knowledge" call site in this repo already exists, and none of them call the gateway

A repo-wide grep (after the mandated `search_docs`/`graphify query` calls below) of
`.claude/workflows/*.js` and `.claude/agents/*.md` for `search_docs`, `graphify`, `knowledge_context`,
and `knowledge_status` finds exactly four real call sites, all pre-dating the gateway and all wired to
`mcp__knowledge-search__search_docs` + `graphify query` directly — never the gateway:

1. **Scope phase, `implement-ticket.js:131-134`** — `create-tickets.js`-driven ticket structuring calls
   `search_docs(query=request, top_k=5)` then `graphify query "<request>"` before any file read.
2. **Investigate phase, `implement-ticket.js:497-500`** (mirrored verbatim in
   `.claude/agents/investigator.md:12-13`, the agent this ticket itself runs under) — same two-call
   sequence, keyed on `<ticket title> <request summary>`, explicitly required "before any file reads or
   grep."
3. **Scope phase, `simq-audit.js:448-451`** — identical two-call pattern for SimQ-audit-derived tickets.
4. **Create-Tickets skill's own Investigate phase, `.claude/skills/create-tickets/SKILL.md:49-59`**
   (backing `concern-investigator.md`) — same ordering, `search_docs` then `graphify query "<concern
   title>"`, explicitly marked "Required order — do not skip steps."
5. **`investigate-simulation-result.js:24-25`** — `search_docs` only (no graphify — this workflow's
   Analyze phase asks a narrower "which Mechanics Bible chapters are relevant" question that has no
   code-structure component).

No skill or workflow anywhere in `.claude/skills/*/SKILL.md` or `.claude/workflows/*.js` references
`knowledge_context` or `knowledge_status` — expected, since Phase 4 is the first phase to make the
gateway a real, live tool; this confirms the survey scope (zero existing integration to audit for
correctness, only candidate points to evaluate for a *future* integration).

### One phase has genuinely NO knowledge-tool call today: Document-Update / `doc-updater`

`implement-ticket.js:774-838` (Phase 5a, `Document-Update`) and `.claude/agents/doc-updater.md` contain
no `search_docs`, `graphify`, or gateway call at all. The orchestrator injects this investigation
artifact's own docs-to-update bullets (`path`, `reason`) directly into the doc-updater
prompt (`implement-ticket.js:819`); `doc-updater.md` Step 0 states this is "never something you derive
yourself." The agent's actual work is: read each already-named target doc in full plus 2-3 sibling docs
in the same folder (`doc-updater.md:56-57`), apply a per-family rule, and edit. There is no discovery
step here — the target paths are already known by the time doc-updater runs. Immediately after,
`tools/gate_checks/doc_staleness_check.py` (a deterministic, non-LLM diff between changed files and the
declared `docs_to_update` list, `implement-ticket.js:840-902`) re-verifies coverage.

### Architecture Review uses a cheaper, already-deterministic index — not search_docs/graphify

`.claude/agents/architecture-reviewer.md:9-11` ("Registry Lookup") filters `docs/REGISTRY.yaml` by
`type: doc`, `status: active|authoritative`, `layer: <plan_layer>` — a flat-file lookup with no LLM
round trip, no embedding search, no MCP call. This is already the cheapest-possible mechanism for "find
the architecture docs relevant to this plan's layer," predating both `search_docs` and the gateway.

### The Investigate phase already has a dormant, advisory-only "opportunistic gateway call" hook

`implement-ticket.js:528-588` — a `SHADOW_CONTEXT_PACKET_ENABLED=1`-gated, fail-open, `timeout 10s`
call to `wrap_context_packet_assembly()`, placed immediately after the Investigate phase's `pushEvent`.
It is off by default, writes to `agent-monitoring/events.jsonl` on a strictly negative/disjoint `seq`
range so it can never collide with a real phase event, and currently passes an **empty candidate set**
because "no real retrieval pipeline wired in (`tools/hybrid_retrieval.py` wiring is explicitly deferred
to a follow-up ticket)" (comment at `implement-ticket.js:558-559`). This is direct, pre-existing
precedent inside this exact codebase for "recommend or opportunistically use \[a knowledge tool\]
without creating a mandatory phase, gate, or ticket step" (`tmp/mcp-followup-instruction.md` §1's own
language) — the mechanism this ticket is evaluating whether to recommend already has a parked landing
spot, unused.

## Mechanics / Engine Constraints

Not applicable in the Mechanics Bible sense — this ticket evaluates agent-infrastructure workflow
integration, not simulation mechanics. The governing constraints instead come from
`tmp/mcp-followup-instruction.md` §1 ("general repository utility, not a workflow phase or mandatory
ticket step... may recommend or opportunistically use... should not mechanically require") and
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4's third bullet (same framing). Both are
satisfied by this ticket producing a recommendation document only, per its own Scope/Out of Scope.

## Real Measured Evidence Used for Each Candidate Point

All latency/token numbers below are real, committed measurements — never estimated — from
`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`,
`phase2_baseline_recomparison.md`, and `phase3_pilot_acceptance_measurement.md`, cross-checked against
`agent-monitoring/retro/RETRO-2026-W33.md`.

**Baseline (Phase 0, direct `search_docs` + `graphify` calls, the tools already used at every real call
site above):** average combined wall time 1870.64 ms, average combined token estimate 2527.14 tokens
(both re-derived from Phase 1's own restated thresholds: `935.32 ms = 50% × baseline`,
`1263.57 tokens = 50% × baseline`).

**Gateway cold call (Phase 1, no cache):** 1469.7–5325.8 ms per entry (`context_search`-routed) and
2627.6–2650.2 ms (`graphify`-routed) — the real, mixed result against the 1870.64 ms baseline: 4 of 7
corpus entries measure slower (1.35x–2.85x, e.g. Q1 at 5325.8 ms = 2.85x), while the 3 fastest entries
(Q3, Q4, Q6 — all single-provider `context_search`-routed) measure **faster** than baseline
(0.79x–0.90x); Q6 at 1469.7 ms is the single fastest gateway call in the whole corpus, not a "1.3x
slower" data point. Token count: 2649–7633 tokens per entry — **every entry is 1.05x–3.0x larger than
the baseline average token estimate, without exception.** Token overhead is universal; latency
overhead is not.

**Gateway warm call, Level 1 cache (Phase 2):** 0/7 genuine cache hits. `MAX_PAYLOAD_BYTES = 8192`
rejected every one of the 7 real response payloads (10.6–30.5 KB) as `oversized_payload` — Level 1
caching was structurally inert for every real query in the corpus under the gateway's own default
request shape. (A later hotfix, `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`, raised the cap
to 65536 bytes and confirmed 7/7 hits at the new cap — but that fix landed *after* Phase 2's own
recomparison, which is the number available to this evaluation as the state most workflow integrations
would have shipped against.)

**Gateway warm call, Level 2 cache (Phase 3, post-hotfix cap):** 7/7 genuine hits, dual-signal-verified.
Median end-to-end latency **1438.21 ms — genuinely faster than both the Phase 1 cold baseline (2521.78
ms) and this same run's own freshly-measured Level-1-warm baseline (1543.32 ms)**. But median
full-payload token count (2865 tokens) is **not** smaller than either baseline (Phase 1 cold: 2846;
Level-1-warm: 2615) — real FAIL on the token half of Phase 3's own AC4/§18 criterion. Separately, budget
enforcement (§21 #12) **FAILs for 5/7 entries** (`context_search`-routed queries run 2.22x–2.39x over the
declared budget's ±20% tolerance) because `assemble_within_budget()`'s accounting covers `statements[]`
only, not `context[]`/`evidence[]`/`conflicts[]` — the full payload a caller actually pays token cost for
is structurally unbounded by the requested budget for the majority of query shapes.

### What this means for each specific candidate point

**Scope and Investigate phases (both mandate `search_docs` then `graphify query` today; Investigate is
this very ticket's own agent, `investigator.md:12-13`).** These are one-shot, per-ticket queries — each
ticket's title/summary is textually distinct from every other ticket's, so a genuinely warm Level 2 hit
(the only measured configuration where the gateway beats the existing baseline on latency) is
structurally rare in this exact usage pattern: Level 2 caching only pays off on a semantically-identical
repeat of the *same* query, which an Investigate-phase query (keyed on a unique ticket title) essentially
never is. The realistic case for these two phases is therefore the **cold** case, which real, measured
data shows is heavier in tokens for all 7 corpus entries (1.05x–3.0x, no exception) and slower in
latency for 4 of 7 (1.35x–2.85x) than the two calls already in use — the 3 fastest gateway calls in the
corpus do beat the baseline on latency alone, but not on tokens. Token overhead in particular is not a
marginal or ambiguous gap — it holds for all 7 corpus entries, at every phase of the epic's own
measurement (Phase 1 cold numbers, cited above, are unchanged through Phase 2 and Phase 3's own cited
comparisons). **Recommend against** replacing or supplementing the Scope/Investigate `search_docs` +
`graphify` sequence with a gateway call, on real, measured evidence, not speculation. (Re-litigating the
Hard Rule itself is explicitly Out of Scope for this ticket; this recommendation only addresses whether
the *gateway* should additionally be reached for at that same point — it should not.)

**Document-Update / `doc-updater` (no knowledge-tool call today; retro's own "What to change?" note
names doc-staleness handling as this week's one recurring, avoidable gap).** This looked, at first
read, like the most promising candidate — `tmp/mcp-followup-instruction.md`'s own example even names
"a skill's own doc-updater step optionally querying `knowledge_status` for a specific known question
type." Checking `knowledge_status_response.schema.json` against that example finds a **capability
mismatch**: `knowledge_status` reports gateway-wide provider availability, cache hit/miss/stale-rejection
*rates*, aggregate latency, and `branch_scope`/`cache_rebuildable` flags — it has no per-document,
per-path field anywhere in its schema. It cannot answer "is `docs/mechanics/03_economic_laws.md` stale
relative to the current diff" for a specific doc; that is exactly the deterministic, already-working job
`tools/gate_checks/doc_staleness_check.py` does today (`implement-ticket.js:840-902`), and doc-updater's
own target list is already injected from `investigation.md`, not discovered. `knowledge_context` could
in principle be called with `changed_paths` set to the current diff to trigger the gateway's own
evidence-revalidation machinery (`revalidate_cache_row()` / `revalidate_context_packet_row()`,
confirmed live and tested via Phase 3's AC6/#7/#8 PASS results), but that only revalidates an **already-
cached** packet for that doc — it does not perform fresh staleness discovery for a doc with no existing
cache entry, which is the doc-updater's actual situation on every first-time-touched doc. There is no
real measured data anywhere in Phases 0-3 for this specific call pattern (doc-freshness-check-by-path)
at all — the 7-entry corpus is entirely natural-language investigation-style queries. **Insufficient
evidence to recommend for** (the capability doesn't map to the retro's own diagnosed problem) **— and
the retro's own suggested fix (bake the "Docs Considered But Not Required" restructuring instruction
directly into `doc-updater.md`'s base prompt) is a prompt-content fix, not a knowledge-tool call, so it
does not compete with or require this evaluation's recommendation either way.**

**Architecture Review (`docs/REGISTRY.yaml` filter, no LLM/MCP round trip at all).** Real retro data:
Architecture-Verify has the highest phase-average cost-proxy-score (85.5) and the most raw failures
(35/127 calls), but the retro's own Notes section, based on direct inspection of this week's own Phase 3
work, states these rejections were "almost all substantive catches... not noise." The cost driver here is
review depth (reading plans/diffs against Mechanics Bible chapters and engine contracts), not a slow or
inadequate context-discovery step — the registry filter itself is already the cheapest possible
mechanism, cheaper than any gateway call by construction (no network/subprocess round trip). **Recommend
against** — no real evidence of a context-gathering bottleneck this phase has, and no measured gateway
number beats a flat-file registry filter on latency.

**The existing dormant shadow-packet hook at Investigate phase
(`SHADOW_CONTEXT_PACKET_ENABLED`, `implement-ticket.js:528-588`).** This is the one place in the repo
already structurally shaped as "opportunistic, non-mandatory, fail-open, off by default" — exactly the
posture `tmp/mcp-followup-instruction.md` §1 asks integrations to have. It currently has an empty
candidate set and no real retrieval pipeline wired in. Given the real Phase 1-3 cold/warm numbers above,
wiring it to make a real `knowledge_context` call today would reproduce the same cold-call latency/token
regression documented above on every Investigate-phase run where the flag is enabled — there is no
reason to expect this specific call site would land in the warm case any more than the general
Investigate-phase case already analyzed. **Recommend against enabling it today**, but note it explicitly
as the correct landing spot for a *future* ticket to reconsider, specifically once/if a future phase
closes Phase 3's own two disclosed real gaps (§12 budget enforcement not bounding the full payload;
§18's token-count regression even on a genuine Level 2 hit) — until then, wiring real calls into this
hook would not clear the bar this evaluation's own real evidence sets.

## Docs Requiring Update

This ticket is itself the "doc" being produced (the recommendation document) — see Output below for
its exact required location and content. No other `docs/` path requires an update to reflect a behavior
change, because **no behavior changes** (Out of Scope explicitly forbids any code/skill/workflow diff).
One doc is a candidate to *create*, not modify:

- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`: new file — the real
  recommendation document this ticket's Scope requires, per the same
  `docs/engine/contracts/knowledge_gateway_mcp/` location used by every prior Phase 1-3 measurement
  document (`phase1_baseline_comparison.md`, `phase2_baseline_recomparison.md`,
  `phase3_pilot_acceptance_measurement.md`) — chosen over `docs/architecture/` because this document's
  content is entirely about the gateway's own measured behavior at specific call sites, matching its
  sibling docs' scope and audience exactly, not a general system-design ADR.

## Parity Ledger Overlap

- `INFRA-344` (`docs/parity_ledger/infrastructure.yaml:9339`) — Phase 2's own "tool certifies
  methodology, not conclusion" precedent this ticket's own Acceptance Criteria explicitly mirrors.
- `INFRA-339`, `INFRA-350` — the Phase 1 and Phase 3 analogues of the same precedent (Phase 1 baseline
  comparison, Phase 3 pilot acceptance measurement), cited for the same reason.
- `INFRA-351`, `INFRA-352` — the two DONE Phase 4 sibling entries (Parity Adapter, Changed-Path Context)
  this ticket's own entry will sit alongside; next available ID in the file is `INFRA-353`.
- No P0 entries are touched by this ticket — this is an evaluation-only ticket with no runtime behavior
  change, so no `test_path`-requiring P0 entry applies to any *conclusion* here. The new entry this
  ticket requires (per its own AC4) certifies methodology, and per the schema (`schema.json`)
  `status: verified` still requires both `v2_evidence` and `test_path` regardless of priority — see
  Test Plan for the concrete `test_path` this ticket's own new doc-structure test provides.

## Prior Work

- `stored_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/` and
  `stored_artifacts/TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT/` — the two DONE Phase 4 sibling tickets;
  both are provider/adapter-capability work, not workflow-integration evaluation, so no direct content
  overlap, but their INFRA-351/352 entries establish this ticket's sibling-ID numbering and the
  "support_boundary" field convention used when a ticket deliberately declines to wire something (used
  by INFRA-351 to record "changed_paths threading declined, by design, not oversight" — directly
  analogous to this ticket's own "declined for real, measured reasons" framing).
- `tests/docs/test_redaction_retention_policy_doc.py` — the direct structural precedent for how a
  documentation-only Knowledge Gateway MCP ticket gets a real, passing `test_path`: static
  section-heading/required-phrase assertions against the doc file, no runtime behavior. This ticket's
  own Test Plan follows the identical pattern.
- `agent-monitoring/retro/RETRO-2026-W33.md` — read in full; its Notes section is the only place in the
  repo that already independently diagnoses a real, recurring gap (doc-staleness handling) in a phase
  this ticket also considered as a candidate integration point, and its own suggested fix (a
  `doc-updater.md` prompt change) does not involve a knowledge-tool call, which is itself informative:
  the humans/prior tickets closest to this exact problem did not reach for the gateway as the fix either.

## Risks and Open Questions

- **Open, not blocking:** the Phase 2 Level 1 cache-size-cap number cited above (8192 bytes, 0/7 hits)
  was superseded by a later hotfix (65536 bytes, 7/7 hits) before Phase 3 ran. This investigation cites
  both numbers accurately, in their real chronological/scope context, and does not let the later fix
  retroactively soften the Phase 2-era finding — a workflow integration shipped against the
  pre-hotfix state would have seen 0/7 hits; one shipped today would not. Both are real and both are
  reported; the final recommendation document (Output) must preserve this distinction rather than
  citing only the more favorable Phase 3 number.
- **Genuinely open, flagged rather than assumed:** whether a future, purpose-built cache-warming
  strategy (e.g., a nightly job that pre-populates Level 2 for the top-N most-repeated real query
  shapes, if `mcp-followup-instruction.md` §7's "measure repeated knowledge demand" study is ever done)
  could change the Investigate-phase economics analyzed above. No such measurement exists yet in this
  repo (`RETRO-2026-W33.md`'s own Retrieval Quality section reports "No cache-level data this period" —
  §7 of the followup instruction has not yet been acted on). This investigation does not assume an
  answer either way; it is out of scope for this ticket to commission that study, and the recommendation
  document must state this as a named open question, not a settled negative.

## Anti-Drift Hazards

- **Do not let this ticket's own recommendation document read as a mandate.** Every "recommend against"
  or "insufficient evidence" conclusion above must stay phrased as advisory, per the ticket's own Scope
  and Out of Scope — no wording like "workflows should require," "must call," or a prompt-template
  change proposal that would function as a soft-mandatory gate even if unlabeled as one
  (`tmp/mcp-followup-instruction.md` §1's explicit prohibition, restated in this ticket's own Out of
  Scope).
- **Do not cite only the most favorable per-phase number.** Phase 1's cold numbers, Phase 2's 0/7 Level-1
  numbers, and Phase 3's mixed 7/7-hit-but-token-FAIL numbers are all real and all relevant to different
  candidate points; cherry-picking Phase 3's latency-improvement number alone (ignoring its own
  token-count and budget-enforcement FAILs, and ignoring that it depends on a warm-cache condition rare
  at the analyzed call sites) would misrepresent the evidence this ticket exists to honestly weigh.
- **Do not implement any of the evaluated integrations.** This ticket's Out of Scope explicitly forbids
  any diff to `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md` — the
  recommendation document is the entire deliverable.
