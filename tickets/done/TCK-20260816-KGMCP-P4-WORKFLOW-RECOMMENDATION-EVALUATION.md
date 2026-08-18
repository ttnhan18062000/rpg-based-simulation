---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION
phase: done
date: 2026-08-16
tags: [ai, mcp, testing]
---

# TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION

## Title
Evaluate (do not mandate) optional workflow recommendations or opportunistic gateway calls

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §20 Phase 4's third bullet is "Evaluate optional workflow recommendations or opportunistic
calls without creating a mandatory phase, gate, or ticket step." `tmp/mcp-followup-instruction.md`
§1 is explicit: the gateway "must be treated as a general repository utility, not as a workflow
phase or mandatory ticket step... Workflow integrations may recommend or opportunistically use the
gateway, but should not mechanically require it in specific phases." This ticket is an
investigation/evaluation ticket — its deliverable is a real, evidence-based recommendation, not a
code change that adds a new mandatory gate.

## Scope
- Survey this repo's existing `.claude/workflows/*.js` and `.claude/skills/*/SKILL.md` for real
  points where an agent currently does (or plausibly should) reach for project knowledge — e.g.
  Investigate phases, doc-staleness checks, Architecture Review — and assess whether the
  now-live Knowledge Gateway MCP (`knowledge_context`/`knowledge_status`) would genuinely reduce
  token cost or investigation time at any of those points, relative to the tools already used there
  (`search_docs`, `graphify query`, raw grep/read).
- Use this epic's own retro data (`agent-monitoring/retro/`) and the Phase 1-3 baseline/recomparison
  measurement docs as real evidence, not speculation — e.g. does the gateway's own measured latency
  profile (`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`,
  `phase3_pilot_acceptance_measurement.md`) suggest it would be faster or slower than the tools an
  agent currently reaches for at a given point?
- Produce a real recommendation document (new file under `docs/engine/contracts/knowledge_gateway_mcp/`
  or `docs/architecture/`, per this ticket's own Investigate-phase decision on the right location) —
  for each candidate integration point found, state plainly: recommend it, recommend against it, or
  state the evidence is insufficient to recommend either way. A "no clear opportunity found, keep the
  gateway purely pull-based" conclusion is an acceptable, honest real result — this ticket must not
  manufacture a recommendation to appear more successful than the real evidence supports.
- If a genuinely strong, evidence-backed case emerges for a specific opportunistic integration (e.g.
  a skill's own doc-updater step optionally querying `knowledge_status` for a specific known
  question type), this ticket documents the recommendation for a human reviewer to act on in a
  separate, later ticket — it does NOT implement that integration itself.

## Out of Scope
- Any code change to `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md`
  — this ticket produces a recommendation document only, per its own explicit "evaluate, don't
  mandate" framing.
- Adding the gateway as a required step anywhere, under any framing (e.g. "soft-required," "strongly
  recommended in the prompt template") — per `tmp/mcp-followup-instruction.md` §1's explicit
  prohibition, this ticket must not create ANY mechanism that functions as a mandatory gate even if
  not labeled one.
- Re-litigating this repo's own existing `search_docs`/`graphify query` Hard Rule ordering in
  CLAUDE.md — that predates the gateway and is out of this ticket's scope to second-guess.

## Acceptance Criteria
- [x] A real survey of existing workflows/skills for candidate gateway-integration points is
      performed and documented, citing real file paths, not a generic list.
- [x] Each candidate point gets a real, evidence-cited recommendation (for / against / insufficient
      evidence) — no candidate is left unaddressed, and no recommendation is asserted without citing
      real retro/measurement data.
- [x] The recommendation document explicitly states it does not create any mandatory
      phase/gate/ticket step, and no code change in this ticket's own diff adds one.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added, certifying this
      ticket's evaluation methodology as sound (not certifying that any particular workflow
      integration itself is correct, since none is implemented) — mirroring
      `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s own `INFRA-344` tool-certifies-not-conclusion-
      certifies precedent. Added in the Parity phase as `INFRA-353`.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC (parent)
- TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT (DONE; the real latency/token measurement data
  this ticket's evaluation cites as evidence)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4
- `tmp/mcp-followup-instruction.md` §1
- `agent-monitoring/retro/RETRO-2026-W33.md` (real per-phase cost-proxy and search-before-grep
  compliance data — candidate evidence source)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md` (survey targets, read-only)

## Assumptions / Open Questions
- Whether any genuinely strong integration case will be found at all is explicitly not assumed — a
  negative/no-opportunity-found result is a real, acceptable outcome for this ticket.

## Implementation Notes
Implemented Steps 1 and 3 of the approved `plan.md` exactly as written, using the corrected
multipliers (4 of 7 corpus entries slower at 1.35x-2.85x, 3 of 7 faster at 0.79x-0.90x; token
overhead universal at 1.05x-3.0x for all 7 entries; Phase 3 budget-tolerance FAILs at
2.22x-2.39x). Steps 2 (`INFRA-353` parity entry) and 4 (marking the proposal's Phase 4 "Evaluate"
bullet Done) were deliberately NOT done in this pass — per the orchestrating instruction, those
are the separate Parity phase's and Document-Update phase's jobs respectively, per this session's
established phase-split convention. This is a real, intentional deviation from plan.md's own step
ownership (plan.md assigns all 4 steps to Implement); the deviation is orchestration-level phase
routing, not a scope or content change to what Steps 1 and 3 themselves produce.

- **Step 1:** Wrote `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`
  verbatim per plan.md's required document structure — Headline (no mandatory
  phase/gate/step created) + 4 `## Candidate N` sections (Scope/Investigate `search_docs`+`graphify`
  sequence — Recommend against; Document-Update/doc-updater — Insufficient evidence to recommend
  for, on a genuine `knowledge_status_response.schema.json` capability mismatch; Architecture
  Review's `docs/REGISTRY.yaml` filter — Recommend against; the dormant
  `SHADOW_CONTEXT_PACKET_ENABLED` hook — Recommend against enabling today, flagged as a future
  candidate) + an Evidence honesty note (pre-hotfix 0/7 vs. post-hotfix 7/7 Level 1 cache numbers,
  both preserved in chronological context) + an Open question section (cache-warming study, §7,
  not yet done). Every numeric claim was transcribed verbatim from plan.md's own already-corrected
  text — no re-derivation.
- **Step 3:** Wrote `tests/docs/test_phase4_workflow_recommendation_doc.py`, mirroring
  `tests/docs/test_redaction_retention_policy_doc.py`'s pattern (module docstring, `_REPO_ROOT`/doc
  path constants, one `_read_doc()` helper, static substring/regex assertions only). Implemented
  the 4 tests test_plan.md specifies, plus one additional test
  (`test_document_update_candidate_uses_insufficient_evidence_not_recommend_against`) enforcing the
  plan's own Anti-Drift Notes instruction not to flatten Candidate 2's "insufficient evidence"
  verdict into "recommend against" for consistency — this is a stricter check than test_plan.md
  strictly required, added because the plan explicitly calls this distinction out as a drift risk
  worth guarding mechanically, not just by review.
  - Test 1 asserts the doc exists and contains all 7 required section headings plus the
    allow-listed "creates no mandatory phase, gate, or ticket step" phrase.
  - Test 2 splits the doc on `## Candidate ` and asserts each of the 4 isolated sections contains
    one of the 3 literal verdict markers.
  - Test 3 (citation integrity) extracts paragraphs containing a numeric latency/ms/token/x claim
    and asserts each such paragraph cites (by substring) one of the 4 real evidence paths
    (`phase1_baseline_comparison.md`, `phase2_baseline_recomparison.md`,
    `phase3_pilot_acceptance_measurement.md`, `agent-monitoring/retro/RETRO-2026-W33.md`), then
    asserts every path actually cited in the document resolves on disk via `Path.exists()`. Note:
    `phase2_baseline_recomparison.md` is not cited by file path anywhere in the doc body (plan.md's
    own required text only references "Phase 2" in prose, not by path, in the Evidence honesty
    note) — this is consistent with plan.md's literal text, not an omission introduced during
    implementation, and the test does not require all 4 paths to appear, only that any path that
    is cited is real.
  - Test 4 (anti-mandate deny-list) confirms none of `must call`, `is required to call`, `shall
    invoke`, or `mandatory ... gateway` appear describing the gateway itself, after stripping the
    one allow-listed negation phrase.

Verified no `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md` file
was touched: `git status --porcelain -- .claude/workflows .claude/skills .claude/agents` returned
empty output.

## Test Summary
`pytest tests/docs/test_phase4_workflow_recommendation_doc.py -v` — 5 passed (4 required by
test_plan.md + 1 additional Candidate-2-specific guard), 0 failed.

`pytest tests/docs/ -v` — 29 passed, 2 failed, 1 skipped. The 2 failures
(`test_v1_symbols_not_in_primary_sections`, `test_no_broken_src_links_in_doc`, both in
`tests/docs/test_design_patterns_currency.py`) are pre-existing and unrelated to this ticket: they
assert facts about `docs/guidelines/design_patterns.md` (a `GoalScorer` V1-symbol placement issue
and a stale `src/domains/adventure/phase.py` citation) that this ticket's diff does not touch —
confirmed by `git status` showing `docs/guidelines/design_patterns.md` absent from this session's
changed-file list entirely. No collision with the new test file's names or fixtures.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md` (new) — the
  recommendation document, Step 1.
- `tests/docs/test_phase4_workflow_recommendation_doc.py` (new) — doc-structure/citation-integrity
  tests, Step 3.

Not changed by this pass (explicitly deferred to later phases per orchestrating instruction):
`docs/parity_ledger/infrastructure.yaml` (`INFRA-353` — Parity phase),
`docs/plans/knowledge-gateway-mcp-proposal.md` (Done annotation — Document-Update phase).

### Document-Update phase
- `docs/plans/knowledge-gateway-mcp-proposal.md` — appended the `**Done**
  (`TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`)` annotation to §20 Phase 4's
  "Evaluate optional workflow recommendations or opportunistic calls without creating a mandatory
  phase, gate, or ticket step." bullet, word-for-word per plan.md's Step 4 drafted text (including
  the corrected multipliers: 4 of 7 entries measured slower at 1.35x-2.85x, the other 3 faster;
  universal token overhead 1.05x-3.0x), matching the sibling Parity Ledger Adapter / Changed-Path
  Context bullets' existing `**Done** (TICKET-ID) — ...` pattern. No other bullet or section in the
  file was touched. investigation.md's "Docs Requiring Update" reasoning (that this file was
  correctly omitted from that section, since it only tracked behavior-change doc updates, and this
  is a tracking-status annotation covered instead by plan.md's own Step 4) was confirmed accurate —
  no restructuring needed. `docs/parity_ledger/infrastructure.yaml` (`INFRA-353`) remains
  out of scope for this phase, per the Parity phase's exclusive ownership.

## Completion Summary

Delivered a real, evidence-based evaluation of four candidate points where the live Knowledge
Gateway MCP could opportunistically integrate into this repo's existing workflows and skills —
not a shipped capability. The honest, real result is a **negative/against** outcome for the
majority of candidates: **recommend against** integration at 3 of 4 points (Scope/Investigate's
`search_docs`+`graphify` sequence, per universal 1.05x-3.0x token overhead and 4-of-7-corpus-entries
latency overhead at 1.35x-2.85x measured in Phase 1; Architecture Review's `docs/REGISTRY.yaml`
flat-file filter, which has zero network/subprocess round-trip cost by construction and no
evidenced bottleneck for the gateway to solve), **insufficient evidence** at 1 (Document-Update/
doc-updater — a genuine capability mismatch, since `knowledge_status_response.schema.json` has no
per-document/per-path field the doc-staleness problem actually needs), and the dormant
`SHADOW_CONTEXT_PACKET_ENABLED` hook flagged only as a **future-candidate landing spot**,
conditioned explicitly on Phase 3's own disclosed budget-enforcement (§21 #12) and token-count
(AC4/§18) gaps closing first. No candidate was manufactured into a "for" recommendation to make
this ticket look more successful than the real evidence supports — a genuinely-warm Level 2 cache
hit is the only measured configuration where the gateway beats baseline latency, and it is
structurally rare at every surveyed call site (each issues a per-ticket-unique query). This is the
correct, disciplined outcome for an "evaluate, don't mandate" ticket: the real value delivered is
the honest "don't build this now" finding plus a methodology sound enough to trust that finding —
not a shipped integration.

Architecture Review caught a real defect during its first pass — an overstated latency claim in
the draft document — and required a correction before approval; the corrected numbers were
independently re-verified exact on the second Architecture Review pass. This is disclosed here,
not smoothed over: the review process worked as intended and the final document reflects the
corrected, re-verified numbers.

No `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md` file was
touched by this ticket at any phase — confirmed empty via `git status --porcelain -- .claude/workflows
.claude/skills .claude/agents`, satisfying AC3 and the ticket's Out of Scope guard against any
mechanism that functions as a mandatory gate even if unlabeled.

**Parity phase complete:** added `INFRA-353` to `docs/parity_ledger/infrastructure.yaml`
(`status: verified`, `priority: P2`, `proof_type: regression`) via the schema-validating
`write_entry()`, followed by a separate, visible `python3 tools/parity_index.py build`. The entry
mirrors `INFRA-344`'s "methodology-not-conclusion" precedent exactly: it certifies that real call
sites were surveyed with real citations, real measured numbers were used without cherry-picking,
no candidate was left unaddressed, and every citation was independently verified accurate across
2 Architecture-Review passes — it explicitly does NOT certify that any evaluated workflow
integration is correct or beneficial, since none was implemented. `v2_evidence` cites the real
recommendation doc; `test_path` cites the real, passing
`tests/docs/test_phase4_workflow_recommendation_doc.py` (6/6 passing, including the citation-
resolution test added during the Test phase). Confirmed `INFRA-352` was the prior last id before
writing `INFRA-353` (`grep -n "^- id: INFRA-3" docs/parity_ledger/infrastructure.yaml` showed
350/351/352 as the trailing ids). Citation-drift check: this ticket touched no `tools/` code
(confirmed — its own diff is limited to `docs/engine/contracts/knowledge_gateway_mcp/
phase4_workflow_recommendation.md` and `tests/docs/test_phase4_workflow_recommendation_doc.py`;
unrelated uncommitted `tools/knowledge_gateway_packet_assembly.py`/`tools/knowledge_gateway_router.py`
changes in the working tree belong to sibling Phase-3/4 tickets, not this one), so no drift is
possible on any prior code-citing parity entry from this ticket's own changes.

All 4 acceptance criteria are now met. This ticket's own diff never adds a mandatory phase, gate,
or ticket step, and the `INFRA-353` entry's `support_boundary` is worded to prevent any future
reader from mistaking "methodology certified sound" for "integration certified correct."
