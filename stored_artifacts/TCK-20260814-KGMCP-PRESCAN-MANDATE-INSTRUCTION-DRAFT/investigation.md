---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT
artifact_type: investigation
tags: [ai, claude-md, process-improvement]
---

# Investigation — TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT

## Current Behavior

### The mandate this ticket drafts a relaxation of (currently live, unmodified)
The blanket "search_docs + graphify before grep" mandate is currently duplicated across **five**
distinct instruction surfaces, all still present and unmodified as of this investigation:

1. `CLAUDE.md` Hard Rules bullet, line 24: *"Do not run grep, find, raw file reads, or spawn
   Explore agents for investigation before first calling `search_docs` (MCP) and `graphify query`
   for the topic."*
2. `CLAUDE.md` `## Context Scan (Mandatory)` section, lines 29-40: numbered 4-step order
   (`search_docs` → `graphify query` → `knowledge_search.py` fallback → check
   tickets/docs/stored_artifacts), with "Raw grep and direct file reads are follow-up steps only —
   they narrow down what the semantic tools already surfaced. Never start with grep."
3. `CLAUDE.md` `## Proactive Tool Use` table, "Any investigation" row, lines 320-321 (also the
   adjacent "User asks project-specific mechanics..." row): same Step-1/Step-2/Step-3 ordering,
   explicit "never skip it."
4. `.claude/agents/investigator.md`, lines 12-16: agent-specific callout added by
   `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` — confirmed present verbatim by direct grep
   during this investigation (see Anti-Drift Hazards; this ticket's Out of Scope forbids touching
   it).
5. `.claude/skills/implement-ticket/SKILL.md`, Step 0 ("Context search", added earlier) and the
   phase-scoped sentence appended to Step 2 ("Investigate") by
   `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (confirmed present verbatim): *"Search-before-grep
   is phase-scoped, not satisfied by Step 0... Step 0's one-time upfront call does not substitute
   for this phase-scoped call."* This is the specific hand-orchestration entry point the hardening
   ticket built and named this ticket must not regress (per this ticket's Scope and Related Tickets).

This ticket's own Related Docs section names only surface (1)/(2)/(3) (`CLAUDE.md`'s Context Scan
and Proactive Tool Use). Surface (5) is not named in this ticket's Related Docs or Related Code
Areas at all, even though it is the exact mechanism whose compliance is currently the pending
signal (see below) and is explicitly the thing `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`
built. Flagged as a gap for Plan — see Risks and Open Questions.

### Status of `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (real, verified)
Confirmed **DONE**, `tickets/done/TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP.md`, all 3
Acceptance Criteria checked `[x]`. The ticket's own AC3 reads verbatim: *"`TCK-20260810-CONTEXT-
TOOLING-EFFECTIVENESS-TRACKING` (sibling epic child) can measure whether this fix holds in the next
retro window — this ticket does not itself need to prove long-term compliance, only that the
callout is real and reachable."* This confirms the premise in this ticket's own Request Summary:
the hardening ticket explicitly deferred long-term compliance proof to the tracking ticket's
correlation section, and did not itself claim full proof. The fix landed as an addition to
`.claude/skills/implement-ticket/SKILL.md` step 2's text block (not `.claude/workflows/
implement-ticket.js`, contrary to the ticket's own original Related Code Areas guess — Investigate
found the real dispatch mechanism was whole-pipeline hand-orchestration of the Skill's numbered
steps, not JS-file routing), backed by two new regression tests in
`tests/tools/test_skill_investigate_search_before_grep.py` (both pass).

### Status of `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (real, verified)
Confirmed **DONE**, `tickets/done/TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING.md`, all 6
Acceptance Criteria checked `[x]`. It landed a real `### Read-Count Correlation (Search-Before-Grep
Compliance)` subsection inside `generate_retro.py`'s `## Tool Safety Audit` section, computed from
real `(run_id, seq)` per-pair data (`compute_tool_safety_metrics`'s `per_pair_compliance`), with a
real first data point recorded in its own Implementation Notes (`--all` corpus run: compliant-group
median 12.0 Read-calls (n=138) vs. non-compliant-group median 9.0 (n=79)).

### Whether the compliance-correlation signal is retro-confirmed as holding — **it is not, yet**
This is the load-bearing finding for this ticket's branch choice. Both landing tickets are DONE,
but "landed" and "held through a retro window" are different claims, and the ticket's own Scope
distinguishes them. Verified directly by reading the freshly generated
`agent-monitoring/retro/RETRO-LAST14D.md` (regenerated 2026-08-15T02:24, same day as this epic's
5 children closed 2026-08-14 — this file was generated specifically as
`TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC`'s own post-close Verification Note check, per
its `## Notes` section):

- Corpus-wide `Search-Before-Grep Compliance (Investigate Phase)` this window: 63.7% (58/91).
- The report's own `## Notes` section states explicitly (quoted, not paraphrased): *"this number
  does not yet demonstrate `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s specific fix... the
  most recent `agent=claude` Investigate-phase event in the entire corpus is from
  2026-08-10T07:12:00Z, before the fix landed (committed 2026-08-14T18:47Z...). No hand-orchestrated
  Investigate-phase run has occurred since the fix shipped, so there is no real data yet confirming
  compliance improved for the specific gap this ticket closed — only that the callout is present and
  reachable... This is a genuine, honest gap, not a fabricated pass."*
- The report's own conclusion: *"2 of 3 retro-based signals plus the separate status-drift check
  show real, positive, non-fabricated movement. The 3rd (search-before-grep compliance) cannot be
  confirmed or denied yet... Recommend flagging the epic as substantially verified with one signal
  pending natural recurrence."*

This matches the "3/4 real signals moved, 1/4 pending" framing exactly: parity ledger write-safety
co-occurrence (moved), skill-adoption zero-invocation flagging (moved), status-drift (moved/fully
satisfied) = 3 confirmed; search-before-grep compliance for this specific fix = the 1 pending
signal, honestly flagged, not fabricated.

**Conclusion for this ticket's branch choice (per Scope):** the hardening fix has **landed** but has
**not yet held through a retro window** (no real data exists either way — the specific failure mode
it targets has not recurred since the fix shipped). Per this ticket's Scope, this selects the
second branch: *"if the hardening fix has not yet landed or not yet held: draft the relaxation
anyway (Phase 0 is contract-drafting, not activation) but explicitly record in this ticket that
activation must wait for the hardening ticket's retro-confirmed fix, and do not treat this ticket
as unblocking activation on its own."*

## Mechanics / Engine Constraints
None. This ticket produces no `src/` runtime behavior and does not touch any Mechanics Bible chapter
or engine contract — it is a process/agent-instruction artifact, the same category
`docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 0 places sibling artifacts
(`evidence_cache_identity_contract.md`, `redaction_retention_policy.md`) in when noting "No
`docs/parity_ledger/` entry accompanies this document — this subsystem is agent-orchestration/
retrieval tooling."

## Docs Requiring Update
- `docs/ai/claude_md_prescan_mandate_relaxation_draft.md`: this is the ticket's actual deliverable —
  the drafted, not-yet-activated replacement instruction text itself. Path finalized by Plan (this
  investigation predates Plan's path choice; updated post-Implement to record the real path that
  was actually written).

No existing live doc requires a content update by this ticket. `CLAUDE.md`, `.claude/agents/
investigator.md`, and `.claude/skills/implement-ticket/SKILL.md` are explicitly Out of Scope (not
modified). This is a deliberate judgment call, not a lazy default: the ticket's entire purpose is to
produce a new, inert artifact — no live instruction surface changes as part of this ticket.

## Parity Ledger Overlap
None. Confirmed by direct precedent: sibling KGMCP Phase-0 artifacts in the same epic
(`evidence_cache_identity_contract.md` §6, `knowledge_gateway_mcp_contract.md` §5,
`redaction_retention_policy.md`'s closing note) all explicitly classify this subsystem
(agent-orchestration/retrieval tooling, process/instruction artifacts) as not requiring a
`docs/parity_ledger/` entry. No P0 entry is implicated.

## Prior Work

### Draft-only / not-activated artifact precedent (Investigation item 3)
Two precedent locations exist in this repo for "drafted, not yet applied" artifacts, and they serve
genuinely different purposes — Plan should pick based on which this ticket's deliverable more
closely resembles:

- **`docs/engine/contracts/knowledge_gateway_mcp/`** — houses `redaction_retention_policy.md` (this
  exact epic's sibling ticket, `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`) and
  `measurement_baseline_contract.md`. Both use "drafted, not ratified" / ratification-gate language
  in a **§-numbered contract/policy** shape (SQLite limits, redaction regex rules, token-counting
  formulas) — i.e., artifacts that define *system behavior a future implementation ticket will wire
  in*, reviewed against a formal Ratification Status section (`redaction_retention_policy.md` §11).
  This location is for KGMCP subsystem contracts specifically, alongside the schema/contract
  documents `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` and `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`
  produced.
- **`docs/ai/`** — houses three `codex_posttool_adapter_*` documents
  (`codex_posttool_adapter_real_command_proposal.md`, `codex_posttool_adapter_activation_fragment.md`,
  `codex_posttool_adapter_exact_config_diff_for_review.md`), each opening with the identical
  boilerplate: *"This document is **for human review only**. Nothing in this repository parses it
  as [TOML/etc.], ... no code in this repository implements or executes what it describes."* These
  are **agent-orchestration/config-instruction drafts** — proposed hook registrations and command
  strings that would change how an agent process is invoked — explicitly not activated, with a
  named list of unmet activation prerequisites (`activation_fragment.md`'s nine-item checklist
  against `agent-orchestration/hook-surface-policy.yaml`).

**This ticket's deliverable is an agent-instruction *prose* change** (CLAUDE.md Context Scan/
Proactive Tool Use replacement wording), not a system-behavior contract and not a hook/command
config. It is categorically closer to the `docs/ai/codex_posttool_adapter_*` shape (an instruction/
policy-text proposal awaiting human review before it changes what agents are told to do) than to
the `docs/engine/contracts/knowledge_gateway_mcp/` shape (a system-behavior spec for code that will
later implement it). Recommendation for Plan: prefer `docs/ai/` (e.g.
`docs/ai/claude_md_prescan_mandate_relaxation_draft.md`), reusing the exact "for human review only /
nothing in this repository parses or executes this" opening boilerplate, over
`docs/engine/contracts/knowledge_gateway_mcp/`. Neither location has an existing structural test
covering the `docs/ai/codex_posttool_adapter_*` docs (grep confirmed: zero test files reference any
of the three by name) — `tests/docs/test_redaction_retention_policy_doc.py` (see Test Plan) is the
only existing "test a not-activated doc's structure" precedent in the repo, and is reusable as a
pattern even though it targets a doc in the other location.

### Related tooling/process precedent
- `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` (DONE) — added the investigator.md callout,
  predecessor fix this ticket must not regress.
- `TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES` and `TCK-20260704-SKILL-TRIGGER-COVERAGE` (both DONE,
  found via `docs/REGISTRY.yaml` tag/title match on `claude-md`) — prior precedent for how CLAUDE.md
  instruction-surface edits are scoped and tested in this repo, useful context for Plan even though
  this ticket does not itself edit CLAUDE.md.
- `TCK-20260731-GATE-BYPASS-HARDENING` (found via registry) — prior instruction-hardening-against-
  drift precedent in `.claude/skills/implement-ticket`/`implement-epic`, relevant anti-drift
  reference for how this repo phrases non-optional instruction language.

## Risks and Open Questions
- **Gap, not yet resolved:** the ticket's own Related Docs/Related Code Areas name only `CLAUDE.md`
  as the surface the draft must be checked against for non-regression, but a full non-regression
  check must also cover `.claude/skills/implement-ticket/SKILL.md`'s Step 0 and Step 2 callout — the
  literal mechanism `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` built, whose compliance is the
  pending signal this very ticket's Scope is conditioned on. A draft that only checks non-regression
  against `CLAUDE.md`'s two named sections while silently contradicting `SKILL.md`'s phase-scoped
  callout would defeat the entire sequencing purpose of this ticket. Flagging for Plan to decide
  explicitly — not assumed here.
- **Open, per this ticket's own Assumptions/Open Questions section:** whether the drafted language
  should be scoped narrower than proposal §2.1's full ambient-utility text (e.g., an explicit carve-
  out preserving the hand-orchestration entry point SKILL.md now hardens) or left general with an
  activation precondition attached. Investigate's finding (fix landed, not yet retro-confirmed)
  supports drafting the general §2.1 language but attaching an explicit, unambiguous activation
  precondition — consistent with the Scope's second branch instruction — rather than hand-crafting a
  narrower carve-out not asked for by the proposal text itself. This is a judgment call for Plan, not
  decided here.
- **The gateway itself does not exist yet.** §2.1's ambient-utility text describes "the gateway" as
  an available tool alongside `rg`/Graphify/Context Search, but per `docs/plans/knowledge-gateway-
  mcp-proposal.md` §20, only Phase 0 (contract/schema/policy work) is complete for this epic — no
  `knowledge_context`/`knowledge_status` MCP tool exists in `tools/` yet (Phase 1+ is unimplemented).
  The drafted instruction text must not imply the gateway is callable today. §2.1's own text already
  handles this correctly ("Until that amendment is approved and generated, current repository
  instructions remain in force; merely implementing the MCP does not silently override them") — the
  draft should preserve that framing, not soften it into implying present availability.
- No open question here blocks Investigate's own conclusions; the branch-selection finding above is
  based on real, current data (RETRO-LAST14D.md, regenerated same-day), not an assumption.

## Anti-Drift Hazards
- **Do not edit `CLAUDE.md`, `.claude/agents/investigator.md`, or `.claude/skills/implement-ticket/
  SKILL.md`** as part of this ticket — explicitly Out of Scope. The draft artifact must be written
  to a new file only.
- **Do not let the draft silently imply activation.** Every precedent doc in both candidate
  locations opens with unambiguous "for human review only" / "not ratified" / "does not itself
  decide or imply approval" language stated in the doc's own first paragraph, not buried later. The
  draft here must do the same, and should state the specific activation precondition found by this
  investigation (hardening fix landed but not yet retro-confirmed) rather than a generic "pending
  review" placeholder.
- **Do not treat this ticket as closing or resolving the hardening ticket's pending signal.** The
  pending signal can only move when a real hand-orchestrated Investigate-phase run recurs naturally
  and gets picked up by a future retro window — this ticket cannot manufacture that data, and must
  not claim to.
- **Do not silently narrow or broaden §2.1's substance without flagging it.** If Plan decides to
  scope the draft narrower than §2.1's full text (per the open Assumptions/Open Questions item
  above), that deviation from the proposal's literal §20 Phase 0 bullet must be recorded explicitly,
  not left implicit.
- **Do not duplicate a second correlation/compliance metric.** The real compliance data already
  exists in `agent-monitoring/retro/RETRO-LAST14D.md` / `generate_retro.py`'s `read_count_correlation`
  and `search_before_grep` sections — this ticket only needs to *cite* that data, never recompute or
  fork a parallel version of it.
