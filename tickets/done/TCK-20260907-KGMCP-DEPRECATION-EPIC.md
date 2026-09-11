---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-KGMCP-DEPRECATION-EPIC
phase: done
date: 2026-09-07
tags: [mcp, governance]
---

# TCK-20260907-KGMCP-DEPRECATION-EPIC

## Title
Re-ratify and execute Knowledge Gateway MCP (KGMCP) deprecation

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
`TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` ratified **Option A — keep as-is, no further
investment** on 2026-08-24 (`docs/engine/contracts/knowledge_gateway_mcp/
keep_or_deprecate_decision.md`), on the strength of Phase 4's 7/7 warm-path latency/token
losses and Phase 5's weak repeated-demand signal. That decision blocks
`standalone_items.md` §1's proposed removal (`roadmap.md` item 6 is currently marked
"BLOCKED, conflicts with TCK-20260824-KGMCP-KEEP-OR-DEPRECATE's ratified 'no changes
authorized'"). A month of real usage data since that ratification, plus fresh external
research, is new evidence Option A's own reviewer never had:

- Real corpus usage since 2026-08-24: **1 real content-retrieval call
  (`mcp__knowledge_gateway__knowledge_context`) in the project's entire recorded history**
  (2026-08-17, predating the ratification), against 2,259 real calls to the direct
  `search_docs` tool it sits alongside — a wider gap than the numbers Option A was
  ratified against, not a narrowing one.
- The gateway's tool-allowlist grant (`done-checker`, `test-scoper`) turned out to be an
  accident of `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`'s historical-usage-derived
  scoping, not a deliberate design choice — there is no considered rationale anywhere for
  keeping it available even to those two roles.
- External research (coding-assistant products — Cursor, Windsurf, Sourcegraph Cody,
  Aider, Devin/Cognition's own removal of an embeddings-based retrieval layer in favor of
  direct grep-style search — and real AI-first development practice — Anthropic's own
  internal Claude Code usage study, Sourcegraph/Amp, the Zup internal-agent case study,
  harness-engineering literature, spec-driven frameworks) found no example of a
  production or AI-first-development system building a live routing/caching context
  gateway in front of direct retrieval tools; the consistent, repeated pattern is direct
  tools plus routing guidance expressed as prompts/instructions (which this project
  already has, in CLAUDE.md's Proactive Tool Use table).
- The measured 1.31x-3.76x latency / 1.04x-2.93x token overhead (Phase 4, cold-cache) is
  the cost of routing + provider calls + packet assembly/redaction/provenance-wrapping —
  not of caching. Removing only the caching layer would not remove this overhead; the
  wrapping step itself is the source, confirmed by the fact the warm-cache re-comparison
  (`phase4_warm_direct_tool_comparison.md`) still lost on all 7/7 entries even with
  caching's benefit fully realized.

This epic scopes bringing that evidence back to the repository owner for re-ratification,
and — contingent entirely on that outcome — executing removal per `standalone_items.md`
§1's already-scoped 4-milestone plan. **Do not start this epic's work until the current
agent-working-implementer session's active work finishes** (explicit sequencing from the
repository owner, not a technical dependency).

## Scope
- **M1 — Re-ratification brief.** Produce a concise, evidence-grounded brief presenting
  the fresh evidence above (usage-gap widening, accidental allowlist, external research
  findings, the caching-vs-wrapping-overhead distinction) as a re-opening of
  `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE`'s decision, and take it to the repository owner
  for explicit re-ratification. This does not re-derive or re-run any KGMCP measurement
  corpus — it cites the existing Phase 3/4/5 evidence trail plus the new usage-count and
  external-research evidence gathered since. Record the outcome (re-affirm Option A, or
  move to Option C — deprecate) the same way the original decision ticket did: present,
  then record a human ratification, never an agent-chosen outcome.
- **M2 — If re-ratified toward deprecation, execute `standalone_items.md` §1's plan**
  (contingent, not committed until M1 resolves):
  1. Extract `scan_for_secrets()` from `knowledge_gateway_redaction.py` into a location
     independent of the gateway module (the cross-epic dependency
     `governance_capability_policy_epic.md`'s M4 needs regardless of KGMCP's own fate).
  2. Archive, don't hard-delete, the remaining gateway modules
     (`tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`,
     `tools/start_knowledge_gateway_mcp.sh`); remove the `.mcp.json` registration.
  3. Monitor for 2 weeks: confirm zero `mcp__knowledge-gateway__*` calls appear in
     `agent-monitoring/data/*/tools.jsonl` post-archival.
  4. Delete only after the monitoring window confirms no renewed calls.
- **M3 — If re-ratified to keep Option A (or a new Option B), close this epic** recording
  that outcome and update `roadmap.md` item 6 / `standalone_items.md` §1 accordingly — no
  code change in that branch.

Child tickets for M1 (and M2's 4 steps, if reached) are deliberately not created yet —
M2's real scope depends entirely on M1's outcome, matching this repo's own
"don't force premature child tickets before a gating decision resolves" precedent
(`TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`'s EPIC_SCOPED handling of its own
Bucket-B/C items).

## Out of Scope
- Choosing keep/deprecate unilaterally — same boundary `TCK-20260824-KGMCP-KEEP-OR-
  DEPRECATE` itself drew; this epic re-opens the question, it does not answer it.
- Any code change to `tools/knowledge_gateway_*.py` or `.mcp.json` before M1's
  re-ratification actually lands on Option C.
- Re-running any KGMCP measurement corpus or warm/cold comparison — M1 cites existing
  evidence plus the fresh usage-count/external-research evidence already gathered this
  session, it does not re-derive prior results.
- `governance_capability_policy_epic.md`'s M4 (Bash secret-exposure advisory hook) itself
  — M2 step 1 only extracts the shared dependency that ticket needs; wiring it into the
  hook is that epic's own scope, not this one's.

## Acceptance Criteria
- [x] M1: a re-ratification brief is presented to the repository owner citing the fresh
      evidence (usage-gap, accidental allowlist, external research, caching-vs-wrapping
      distinction) without re-deriving prior measurements, and an explicit ratification
      (re-affirm Option A, or move to Option C) is recorded. **DONE 2026-09-07: re-ratified
      to Option C — deprecate.** See `keep_or_deprecate_decision.md` §4.
- [x] M2 steps 1-2 (contingent on M1 -> Option C, now satisfied): `scan_for_secrets()` (and the
      full ~19-symbol transitive closure `evaluate_write_candidate()` needed) is extracted and
      importable from `tools/write_path_guard.py`, independent of the gateway; gateway modules
      are archived to `tools/archive/` and deregistered from `.mcp.json`. **DONE 2026-09-07** via
      `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`.
- [x] M2 steps 3-4: a 2-week zero-call monitoring window is confirmed; the gateway is
      hard-deleted. **DONE 2026-09-10** via `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` — the
      time-based monitoring window itself was formally superseded by a dated, evidence-backed
      Early Closure Decision (repository owner confirmation) rather than fully elapsing; the
      zero-call-site re-verification the window existed to provide was still performed, fresh,
      before the delete.
- [x] **N/A** — M3 (contingent on M1 -> keep) was the branch for re-affirming Option A; M1
      instead re-ratified to **Option C — deprecate** (`keep_or_deprecate_decision.md` §4), so
      M3's own condition never triggers. Marked N/A explicitly, not left as an open box, so this
      doesn't read as unfinished work: `roadmap.md` item 6 and `standalone_items.md` §1 were
      updated anyway (to reflect deprecation, not the "keep" scenario M3 describes), as a natural
      consequence of M2's own execution — see M2's Implementation Notes above and
      `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s own doc updates.

## Related Tickets
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (`tickets/done/`, closed 2026-09-07) — executed
  this epic's M2 steps 1-2 (extract shared redaction symbols, archive the gateway modules).
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (`tickets/done/`) — executed M2 steps 3-4 (2-week
  zero-call monitoring window, then hard-delete) on 2026-09-10, via a documented Early Closure
  Decision superseding the time-based window rather than fully elapsing it.
- `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` (done) — the decision this epic re-opens.
- `TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC`, `TCK-20260816-KGMCP-P4-DIRECT-TOOL-
  COMPARISON`, `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`, `TCK-20260816-KGMCP-P5-
  REPEATED-DEMAND-MEASUREMENT` — the underlying evidence trail, cited not re-derived.
- `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` — source of the accidental
  `done-checker`/`test-scoper` KGMCP allowlist grant cited in M1's evidence.
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` — precedent for epic-tier tickets not
  forcing premature child tickets before a gating decision resolves.

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` — the
  decision record being re-opened.
- `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md`,
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md` —
  the warm/cold comparison evidence.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (item 6),
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (§1) —
  the already-scoped removal plan this epic's M2 would execute.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  (M4) — the cross-epic dependency on `scan_for_secrets()`'s extraction.

## Related Stored Artifacts
None yet — epic tier, no direct implementation until M1/M2 child tickets are scoped.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
  `tools/knowledge_gateway_redaction.py`, `tools/start_knowledge_gateway_mcp.sh`
- `.mcp.json`
- `.claude/agents/done-checker.md`, `.claude/agents/test-scoper.md` (the current, accidental
  allowlist grant, resolved by whichever way M1/M2/M3 land)

## Assumptions / Open Questions
- Explicit sequencing constraint from the repository owner: do not begin M1 until the
  current agent-working-implementer session's active work finishes. Not a technical
  blocker — a deliberate scheduling choice to avoid concurrent-session contention.
- M1's brief should be genuinely concise (the repository owner explicitly prefers direct,
  evidence-led asks over long documents) — a short brief plus pointers to the existing
  evidence trail, not a new multi-section decision doc duplicating
  `keep_or_deprecate_decision.md`'s own shape.
- If M1 re-affirms Option A again, this epic still has value: it converts an assumption
  ("nothing's changed") into a dated, evidence-backed re-confirmation, and gives the
  accidental tool-allowlist question (M3) a real resolution either way.

## Implementation Notes

**M1 (2026-09-07) — DONE.** Independently re-verified the two hardest evidence claims against
real repo state before drafting the brief: (a) exactly 1 real `knowledge_gateway__knowledge_context`
content-retrieval call exists in the entire monitoring history (2026-08-17, predating the original
ratification), against 3,375 real `search_docs` calls (re-counted live via
`agent-monitoring/data/*/tools.jsonl`; this had grown from the epic's own 2,259 figure even within
the same session, matching this project's recurring "numbers move, re-derive live" pattern); (b)
the `done-checker` allowlist grant traces to `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`'s
historical-usage-derived scoping pass, confirmed by reading that ticket directly (note: `test-scoper`
carries `knowledge_status` only, not `knowledge_context` — a minor precision correction on the
epic's own framing, not a substantive one). The external-research and caching-vs-wrapping-overhead
points were cited from `agent-working-design`'s prior work, not re-derived. Presented the concise
brief directly to the repository owner and recorded their explicit choice via `AskUserQuestion` —
**Option C, deprecate** — never an agent-chosen outcome.

Recorded the re-ratification in `docs/engine/contracts/knowledge_gateway_mcp/
keep_or_deprecate_decision.md` (new §4, additive, the original §3 Option-A ratification left
intact as historical record) plus matching additive "Status update (2026-09-07)" pointer
paragraphs in `audit_phase0_5.md` §5 and `knowledge-gateway-mcp-proposal.md` §25, following the
exact pattern `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE`'s own Implementation Notes documented for its
own (now-superseded) ratification. Updated `roadmap.md` item 6's inventory row/prose (BLOCKED →
UNBLOCKED, H0/blocked → H0/start-now) and the eval-pilot exit gate's item-6 condition note, plus
`standalone_items.md` §1's header and a new status-update paragraph — all additive, no prior
analysis text removed, per this repo's established amend-don't-rewrite convention for prior
decision docs.

**M2 (2026-09-07) — steps 1-2 DONE** via `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`: the real
transitive-closure complication flagged below turned out to be even larger than initially found —
`evaluate_write_candidate()` needed ~19 symbols moved (the whole allowlist/redact/secret-scan/
size-cap/never-cache-categories block), not just the 3 named functions, into a new
`tools/write_path_guard.py`. `tools/retrieval_cache.py`'s real import dependency on
`knowledge_gateway_redaction.py` (`open_connection_with_limits()`, `evaluate_write_candidate()`,
beyond just `scan_for_secrets()`) was resolved by repointing its 3 call sites at the new module
before archival. 5 gateway modules + 15 dedicated test files archived; `.mcp.json` deregistered;
the accidental `done-checker`/`test-scoper` allowlist grant removed; 21 parity-ledger entries
updated. Steps 3-4 (2-week monitoring window, delete) filed as a separate follow-on ticket
(`TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`).

**M2 (2026-09-10) — steps 3-4 DONE** via `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`: rather than
waiting out the remaining ~12 days of the scheduled 2-week window, the repository owner explicitly
confirmed proceeding now, recorded as a dated, evidence-backed Early Closure Decision (same
attribution shape as this epic's own M1 re-ratification — the owner's confirmation is the
operative fact, the verification evidence is supporting material under it). A fresh
zero-call-site sweep was still run before the delete (not skipped because of the confirmation),
confirming zero live call sites remained. Hard-deleted all 26 archived files (11 under
`tools/archive/`, 15 under `tests/archive/`, including 5 orphaned phase-comparison runner scripts
`TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` had separately found and archived in the
interim); updated all 21 `docs/parity_ledger/infrastructure.yaml` entries via
`tools/parity_ledger_writer.py` (3 rounds of architecture review caught 2 real disposition errors
before landing, plus a post-merge peer-review finding — `INFRA-343` — fixed in a follow-up
commit); removed the now-dead `"archive"` `pyproject.toml` `norecursedirs` entry. This completes
all 4 of M2's steps — the epic's own execution phase is now fully done.

**M3 — N/A.** M1 re-ratified to Option C (deprecate), not a re-affirmed Option A, so M3's own
"if re-affirmed to keep" condition never triggers — see the Acceptance Criteria checkbox above for
the explicit disposition and reasoning. `roadmap.md` item 6 and `standalone_items.md` §1 were
still updated (by M2's own execution, reflecting deprecation rather than the keep scenario M3
describes) — closing that documentation loop was M2's natural consequence, not a separate M3
deliverable.

## Test Summary
No direct test coverage for this epic ticket itself (epic tier, no direct implementation). Each
milestone's own child ticket carried its own test coverage: `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`
(M2 steps 1-2) and `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (M2 steps 3-4) both ran and passed
their own full scoped regression suites, documented in their own Test Summary sections.

## Files Changed
No direct file changes by this epic ticket itself — all substantive changes landed via its child
tickets: `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` and `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`
(both `tickets/done/`), plus the M1 re-ratification's own doc updates
(`keep_or_deprecate_decision.md` §4, `audit_phase0_5.md` §5, `knowledge-gateway-mcp-proposal.md`
§25, `roadmap.md`, `standalone_items.md`).

## Completion Summary
Re-ratified the Knowledge Gateway MCP keep-or-deprecate decision from Option A (keep) to Option C
(deprecate/remove), on fresh evidence the repository owner explicitly reviewed and decided on
(never an agent-chosen outcome), then executed the full 4-step removal: extract the shared,
gateway-independent write-path-guard logic (`tools/write_path_guard.py`), archive the remaining
gateway modules and tests, run a monitoring window (formally superseded by an explicit, dated,
evidence-backed owner confirmation rather than fully elapsed), then hard-delete everything
archived. All 3 milestones resolved: M1 DONE, M2 DONE (all 4 steps, across 2 child tickets), M3
N/A (moot once M1 landed on deprecate rather than keep). No code in `src/` was touched at any
point — this epic and both its child tickets were pure tooling/governance/doc work.
(filled in at close)
