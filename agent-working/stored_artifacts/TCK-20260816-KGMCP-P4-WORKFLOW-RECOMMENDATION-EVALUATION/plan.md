---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION

## Summary

This ticket ships no code. Its entire deliverable is a new document,
`docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`, that honestly
reports investigation.md's real findings: at every one of the four surveyed candidate
integration points, the live Knowledge Gateway MCP would make things worse or has no evidenced
case, against the tools/mechanisms already in use there. Three points get a plain "recommend
against" (Scope/Investigate `search_docs`+`graphify` sequence; Architecture Review's
`docs/REGISTRY.yaml` filter), one gets "insufficient evidence" (Document-Update/doc-updater,
on a genuine capability mismatch), and one — the dormant `SHADOW_CONTEXT_PACKET_ENABLED` hook —
gets "recommend against enabling today, flag as future candidate," conditioned explicitly on
Phase 3's own two disclosed, still-open gaps (budget enforcement, token-count regression) being
fixed first. The plan also adds one parity ledger entry (`INFRA-353`) that certifies the
evaluation methodology only, and a new static doc-structure test file mirroring
`tests/docs/test_redaction_retention_policy_doc.py`. No `.claude/workflows/*.js`,
`.claude/skills/*/SKILL.md`, or `.claude/agents/*.md` file is touched by any step below.

## Steps

### Step 1 — Write the recommendation document

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md` (new)

**Change:** Create the document with the exact structure below. This is the ticket's real
deliverable; every numeric claim must be transcribed verbatim from the cited source, not
re-derived or rounded differently than investigation.md already computed it (investigation.md
itself re-derived the Phase 0 baseline numbers from Phase 1's restated 50%-thresholds at
`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` — confirmed to exist,
read in full at plan-verification time, headline table shows all three §4 thresholds FAIL 0/7).

Required document structure (heading text must match exactly — the new test in Step 3 asserts
these strings as literal substrings):

```markdown
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
```

**Do NOT touch:** Any file under `.claude/workflows/`, `.claude/skills/`, `.claude/agents/`. Do
not add a "recommended" or "should" instruction anywhere that a future skill-prompt author could
read as a soft mandate.

**Verify:** `test_phase4_workflow_recommendation_doc_exists_and_has_required_sections`,
`test_every_candidate_point_has_an_explicit_recommendation_verdict`,
`test_recommendation_doc_cites_real_evidence_paths_not_fabricated`,
`test_recommendation_doc_never_states_a_mandatory_requirement` (all from test_plan.md, Step 3
below).

### Step 2 — Add the `INFRA-353` parity ledger entry

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after `INFRA-352` (confirmed at
`docs/parity_ledger/infrastructure.yaml:10138` as the current last Phase-4-sibling entry; next
free ID is `INFRA-353`, verified by `grep -n "^- id: INFRA-35" docs/parity_ledger/infrastructure.yaml`
returning only 350/351/352). Schema (`docs/parity_ledger/schema.json`) requires
`[id, text, status, priority]`; because `status: verified` is used, the conditional block also
requires `v2_evidence` and `test_path` (both non-null strings) — confirmed by reading
`schema.json`'s `allOf` block directly.

Entry content, mirroring `INFRA-344`'s "certifies methodology, not conclusion" phrasing pattern
(`docs/parity_ledger/infrastructure.yaml:9339-9353`, read in full — the exact sentence is "This
entry certifies the measurement tool itself as real, correct, and tested -- it does NOT claim the
measured cache/gateway performance succeeded"):

```yaml
- id: INFRA-353
  text: 'Knowledge Gateway MCP Phase 4 workflow-integration recommendation evaluation --
    TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION. Surveys every real
    "reach for project knowledge" call site in .claude/workflows/*.js and
    .claude/agents/*.md (Scope and Investigate phases'' search_docs+graphify sequence,
    Document-Update/doc-updater''s absence of any knowledge-tool call, Architecture Review''s
    docs/REGISTRY.yaml filter, and the dormant SHADOW_CONTEXT_PACKET_ENABLED hook) and evaluates
    each against the real, committed Phase 1-3 latency/token measurements
    (docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md,
    phase2_baseline_recomparison.md, phase3_pilot_acceptance_measurement.md) and
    agent-monitoring/retro/RETRO-2026-W33.md. This entry certifies that this evaluation''s
    methodology was sound -- real call sites were surveyed with real citations, real measured
    numbers were used without cherry-picking the most favorable phase, and no candidate point was
    left unaddressed -- it does NOT certify that any particular workflow integration is correct or
    beneficial, since no integration was implemented (Out of Scope explicitly forbids any diff to
    .claude/workflows/*.js, .claude/skills/*/SKILL.md, or .claude/agents/*.md). The evaluation''s
    own honest, real output: recommend against integration at 3 of 4 candidate points (evidenced
    universal 1.05x-3.0x token overhead per Phase 1, plus latency overhead for 4 of 7 corpus
    entries at 1.35x-2.85x -- the other 3 entries measured faster on latency alone), insufficient
    evidence at 1 (Document-Update, a genuine capability mismatch against knowledge_status_response.schema.json),
    and the 5th point (the dormant shadow-packet hook) flagged as a future-only candidate,
    conditioned on Phase 3''s own disclosed budget-enforcement (Sec.21 #12) and token-count (AC4/Sec.18)
    gaps closing first. See docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md
    for the full per-candidate breakdown.'
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md
  test_path: tests/docs/test_phase4_workflow_recommendation_doc.py
  proof_type: regression
  divergence_note: null
  support_boundary: 'This entry certifies the evaluation methodology was sound (real call sites
    surveyed, real measurements cited, no candidate silently omitted). It does not certify that
    any evaluated workflow integration would work, since none was implemented in this ticket.'
```

**Do NOT touch:** `INFRA-339`, `INFRA-344`, `INFRA-350`, `INFRA-351`, `INFRA-352`, or any other
existing entry's text/status/evidence fields. Do not renumber or reorder existing entries.

**Verify:** `test_infra_353_parity_entry_is_schema_valid_and_certifies_methodology_not_conclusion`
(test_plan.md item 5).

### Step 3 — Add the doc-structure/citation-integrity test file

**Files:** `tests/docs/test_phase4_workflow_recommendation_doc.py` (new)

**Change:** Mirror `tests/docs/test_redaction_retention_policy_doc.py`'s pattern exactly (read in
full: module docstring explains doc-structure-only scope, `_REPO_ROOT`/doc-path constants at
top, one `_read_doc()` helper, each test a plain substring/regex assertion — no runtime behavior
asserted). Implement the four tests test_plan.md specifies:

1. `test_phase4_workflow_recommendation_doc_exists_and_has_required_sections` — asserts the file
   exists and contains, as literal substrings, every `##`/`###` heading from Step 1's document
   structure above (headline section, all four `## Candidate N` headings, evidence-honesty and
   open-question sections).
2. `test_every_candidate_point_has_an_explicit_recommendation_verdict` — asserts each of the four
   `## Candidate N` sections contains one of the exact verdict markers used in Step 1's document:
   `**Recommend against.**`, `**Insufficient evidence to recommend for.**`, or `**Recommend
   against enabling it today. Flag as the correct landing spot for a future ticket**. Split the
   document on `## Candidate ` to isolate each section before asserting, so a verdict marker
   appearing in the wrong section is caught.
3. `test_recommendation_doc_cites_real_evidence_paths_not_fabricated` — regex-extract every
   numeric latency/token claim's adjacent backtick-quoted path in the same paragraph, assert each
   resolves to one of the four real paths (`phase1_baseline_comparison.md`,
   `phase2_baseline_recomparison.md`, `phase3_pilot_acceptance_measurement.md`,
   `agent-monitoring/retro/RETRO-2026-W33.md` — all four confirmed present on disk at plan-write
   time via `ls` and `test -f`), and assert `Path(...).exists()` for each cited path.
4. `test_recommendation_doc_never_states_a_mandatory_requirement` — deny-list regex over the doc
   text for `must call`, `is required to call`, `shall invoke`, `mandatory ... gateway` (case
   insensitive) describing the gateway itself, allow-listing the literal phrase "creates no
   mandatory phase, gate, or ticket step" as a permitted negation.

**Do NOT touch:** `tests/docs/test_redaction_retention_policy_doc.py`,
`tests/docs/test_doc_integrity.py`, `tests/docs/test_contributor_guardrails.py`,
`tests/docs/test_design_patterns_currency.py`,
`tests/docs/test_prescan_mandate_instruction_draft.py` — new file only, no edits to existing
sibling test files.

**Verify:** `pytest tests/docs/test_phase4_workflow_recommendation_doc.py -v` (all tests pass);
`pytest tests/docs/ -v` (confirms no naming/fixture collision with the sibling suite).

### Step 4 — Mark the proposal's Phase 4 "Evaluate" bullet Done

**Files:** `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:** The §20 Phase 4 bullet list (read at `docs/plans/knowledge-gateway-mcp-proposal.md:1417-1418`,
text: "Evaluate optional workflow recommendations or opportunistic calls without creating a
mandatory phase, gate, or ticket step.") is the tracking checklist this ticket closes out. Its two
sibling bullets in the same list — Parity Ledger Adapter (`:1392-1402`) and Changed-Path Context
(`:1403-1416`) — both already carry an inline `**Done** (TICKET-ID) — ...` annotation appended
when their respective tickets closed, established as the file's own real pattern (confirmed by
direct read of both, not inferred from bullet-list conventions elsewhere). investigation.md's own
"Docs Requiring Update" section did not list this file, since it only considered *behavior-change*
doc updates and this is a tracking-status update — but the sibling-bullet pattern applies equally
here, and the annotation itself is not a claim of code behavior, so it does not conflict with "no
behavior changes."

Append, in the same style as the sibling bullets:

```
- Evaluate optional workflow recommendations or opportunistic calls without creating a mandatory
  phase, gate, or ticket step. **Done** (`TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`) —
  real, evidence-based evaluation performed across every candidate integration point in
  `.claude/workflows/*.js` and `.claude/agents/*.md`. Result: recommend against integration at 3 of
  4 candidate points (Scope/Investigate `search_docs`+`graphify` sequence; Architecture Review's
  `docs/REGISTRY.yaml` filter), measured universally 1.05x-3.0x heavier in tokens and slower in
  latency for 4 of 7 corpus entries (1.35x-2.85x; the other 3 entries measured faster on latency
  alone) than the existing baseline; insufficient evidence at 1 (Document-Update/doc-updater — capability mismatch,
  not a measured regression); the dormant `SHADOW_CONTEXT_PACKET_ENABLED` hook flagged as a future-
  only candidate conditioned on Phase 3's own disclosed budget-enforcement and token-count gaps
  closing first. No code, workflow, or skill file changed by this ticket. See
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md` for the full
  breakdown.
```

This bullet is a genuine "evaluate" task, not a "build X" task (contrast with the Parity Adapter
and Changed-Path Context bullets above it, which required real shipped code to mark Done) — a
real, honest evaluation that concludes "no case for integration" fully satisfies an "evaluate"
bullet's own definition of done, the same way the Changed-Path Context bullet's own "evaluated and
explicitly declined" sub-clause (routing-integration point (b), `:1410-1416`) was marked Done
without implementing that declined sub-piece. Marking this Done does not certify any workflow
integration is correct — only that the evaluation was genuinely performed, mirroring `INFRA-353`'s
own methodology-not-conclusion framing from Step 2.

**Do NOT touch:** Any other bullet in §20, or any other section of the proposal doc. Do not alter
the Parity Adapter or Changed-Path Context bullets' existing text.

**Verify:** No dedicated test — this is a tracking-doc annotation, not new claimed behavior.
Architecture-Verify should confirm by direct read that the appended text does not overstate the
evaluation's conclusion (e.g. does not claim any integration was validated).

## Scope Guards

- No diff to any file under `.claude/workflows/`, `.claude/skills/`, or `.claude/agents/` — ticket
  Out of Scope, restated in investigation.md's Anti-Drift Hazards.
- No wording anywhere in the new document that functions as a soft-mandatory gate (e.g. "should
  call," "workflows are encouraged to invoke") even if not labeled a mandate —
  `tmp/mcp-followup-instruction.md` §1's explicit prohibition.
- Do not re-litigate the existing `search_docs`/`graphify query` Hard Rule ordering in root
  `CLAUDE.md` — predates the gateway, explicitly out of scope.
- Do not cherry-pick only Phase 3's favorable latency number while omitting Phase 3's own
  token-count and budget-enforcement FAILs, or omit the pre-hotfix Phase 2 0/7 result in favor of
  the post-hotfix number — both must appear, in true chronological/scope context.
- The `INFRA-353` entry's `support_boundary` and `text` must not be edited into a conclusion-
  certifying statement (e.g. "the gateway was found unsuitable for these workflows" implies a
  code-level finding was validated) — it certifies methodology only, per AC4 and INFRA-344's
  precedent.

## Dependency Map

- Step 1 (document) has no dependency — write first, since Steps 2 and 3 both cite/reference it.
- Step 2 (parity entry) references the document's path (`v2_evidence`) — should follow Step 1 so
  the path is confirmed to exist, but is otherwise independent content.
- Step 3 (tests) depends on Step 1's exact heading/verdict-marker text existing, since the tests
  assert literal substrings — must be written or finalized after Step 1's document text is final,
  and should be run only after both Step 1 and Step 2 land (test 5 covers Step 2's entry).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: real survey of candidate points, citing real file paths | Step 1 (Candidate 1-4 sections cite real `implement-ticket.js`/`simq-audit.js`/`create-tickets/SKILL.md`/`architecture-reviewer.md` line numbers) | `test_phase4_workflow_recommendation_doc_exists_and_has_required_sections` |
| AC2: each candidate gets an evidence-cited for/against/insufficient-evidence verdict, none left unaddressed | Step 1 (all four Candidates get an explicit verdict) | `test_every_candidate_point_has_an_explicit_recommendation_verdict`, `test_recommendation_doc_cites_real_evidence_paths_not_fabricated` |
| AC3: doc states no mandatory phase/gate/step created; no code diff adds one | Step 1 (Headline section), Scope Guards (no `.claude/` diff in any step) | `test_recommendation_doc_never_states_a_mandatory_requirement` |
| AC4: schema-valid `INFRA-353` parity entry certifying methodology not conclusion | Step 2 | `test_infra_353_parity_entry_is_schema_valid_and_certifies_methodology_not_conclusion` |

## Anti-Drift Notes

- Investigation's Anti-Drift Hazards (restated here for the implementer): do not let the document
  read as a mandate; do not cite only the most favorable per-phase number; do not implement any of
  the evaluated integrations.
- The Document-Update/doc-updater candidate is "insufficient evidence," not "recommend against" —
  keep this distinction; it reflects a genuine capability mismatch (no per-path field in
  `knowledge_status_response.schema.json`), not a measured performance regression like the other
  three candidates. Do not flatten it into "recommend against" during implementation for
  consistency — the underlying evidence differs in kind.
- The shadow-packet hook (Candidate 4) is the one candidate with a real "future landing spot"
  qualifier. Do not upgrade this to an unconditional "recommend for later" — it is conditioned
  explicitly on Phase 3's two disclosed gaps (§12 budget enforcement, §18 token-count regression)
  closing first; state that condition, not just the conclusion.
- Test 3 (citation-existence check) is deliberately shallow — it confirms cited files exist, not
  that transcribed numbers are accurate. Architecture-Verify must independently spot-check at
  least one FAIL-carrying numeric claim against its source doc by direct read, per test_plan.md's
  own Anti-Drift Test Guards — this is a review-phase obligation, not something Step 3's test
  itself can enforce.
