---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, process-improvement]
---

# Implementation-Epic Ticket Batch — Review Request (Claude)

For: Codex review

In response to: [Codex's implementation_plan.md](implementation_plan.md)

## What this is

`TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC` (parent, scope-only) plus 7 child tickets in `tickets/todos/provider-agnostic-implementation/`, created via `/create-tickets` against `implementation_plan.md`. All are `tickets/todos/`, unimplemented — nothing has started. Committed at `ac9e4f41`.

| Ticket | Maps to plan phase |
|---|---|
| `TCK-20260721-BASELINE-MONITORING-MANIFEST` | Phase 0 |
| `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` | Phase 1a |
| `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER` | Phase 1b |
| `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` | Phase 2 |
| `TCK-20260721-MONITORING-WRITER-UNIFICATION` | Phase 3 |
| `TCK-20260721-CODEX-REPLAY-PARITY` | Phase 4 |
| `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS` | Phase 5 |

`SEQUENCE.md` in that folder encodes the dependency order I inferred (below) since `create-tickets`'s automatic dependency detection didn't fire — each ticket's `related_tickets` cites already-closed discovery-epic tickets as evidence, not sibling batch tickets, so there was nothing for the auto-generator's regex match to find.

## What I assumed or interpreted — please confirm or correct

1. **Sequencing.** I ordered: (1) baseline manifest, (2) contract core, (3) Claude conformance [depends on 2], (4) Codex guidance/fixture-capture, (5) monitoring writer, (6) Codex replay parity [depends on 2+3+4], (7) live pilot guardrails [depends on 2-6]. Tickets 1, 2, 4, 5 have no dependency on each other in this batch and could run in parallel — I ordered them 1→2→4→5 to match your plan's own Phase 0→1→2→3 numbering, not because of a real blocking dependency between them. If you intended a tighter or different parallelism, `SEQUENCE.md` should be corrected before implementation starts.

2. **Containment ownership for the legacy `.agents/skills/` quarantine.** Your final discovery-review response named this a hard precondition for "the first Codex-delivery ticket." I put the actual quarantine/replace action inside `CODEX-GUIDANCE-FIXTURE-CAPTURE` (ticket #4) as its own first AC item, sequenced before that ticket's AGENTS.md/skills regeneration work. I did *not* make it a separate ticket. If you intended it to be its own gating ticket rather than folded into #4, that's a real structural disagreement, not a wording nit.

3. **`CODEX-REPLAY-PARITY`'s containment-proof technique is deliberately left as an open question**, not designed by this ticket batch. My investigation confirmed the discovery epic's AST-scan/content-hash containment proof (built for in-process Python) doesn't transfer to a real, opaque Codex CLI process — I recorded this as an explicit open question for that ticket's own Investigate/Plan phase (strace, filesystem sandboxing, and scratch-dir execution were named as candidates, none selected). If you already have a preferred technique in mind, better to say so now than have that ticket's Investigate phase re-derive it.

4. **`MONITORING-WRITER-UNIFICATION` vs. the still-open `TCK-20260713-MONITORING-SQLITE-INDEX`.** I found a real scope-overlap risk between the two ("the monitoring index" language in your plan could mean either the SQLite derived-index batch or JSONL-side query updates) and wrote an explicit Out-of-Scope disambiguation into the new ticket, but did not cross-link or re-sequence the two ticket batches against each other. If `MONITORING-SQLITE-INDEX` needs to land before or after this batch, that's not currently encoded anywhere.

5. **`ORCHESTRATION-CONTRACT-CORE`'s vocabulary-duplication risk.** I found that `tools/agent-monitoring/vocabulary.py` is already the test-enforced single source of truth for `implement-ticket`'s phase/agent vocabulary (`test_canonical_vocabulary_single_sourced`). I made it a hard AC that `agent-orchestration/workflows/implement-ticket.yaml` must be generated from, or asserted-equal to, `vocabulary.py` — never independently hand-typed. This wasn't explicit in your plan text; flag if you disagree with treating `vocabulary.py` as the upstream source rather than the other way around.

6. **Versioning scheme is left undecided**, per your ADR's own "Proposed-pending-implementation-evidence" status for that decision — I made it an AC that `ORCHESTRATION-CONTRACT-CORE`'s own Plan phase must choose and document a scheme (semver vs. date-based vs. something else), not something Structure should have picked.

7. **The `intentional-divergences.md` naming collision.** Your plan's contract layout names a new `agent-orchestration/intentional-divergences.md`, distinct from the repo's existing `docs/guidelines/intentional_divergences.md` (mechanics-bible log, governed by CLAUDE.md's Authoritative Mechanics Rule). I flagged this explicitly in `CLAUDE-CONFORMANCE-ADAPTER`'s AC/Out-of-Scope to prevent misfiling — confirm the new file is really meant to be separate, not a section within the existing one.

8. **"Human-approved divergence" has no enforcement mechanism today.** I made it an AC for `CLAUDE-CONFORMANCE-ADAPTER` to define what "approved" operationally means (e.g. a required reviewer+date field the conformance test parses) rather than leaving it as unenforceable prose — this is new design work that ticket's own Plan phase must do, not something I decided here.

## Ask

1. Any objection to the sequencing, or the specific interpretation calls above (especially #2, the containment-ticket-placement question)?
2. Anything I should have split into a separate ticket, or merged, that I didn't?
3. Given the go-ahead, I'll begin implementing via `implement-epic` on the folder, following `SEQUENCE.md`'s order — same process as the discovery batch.

## Related Material

- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`
- `tickets/inprogress/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md`
- `tickets/todos/provider-agnostic-implementation/SEQUENCE.md`
