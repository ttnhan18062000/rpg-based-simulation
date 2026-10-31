---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-30
tags: [ai, governance, delivery, planning]
---

# Handover: AI-first SDLC evolution work, from agent-working-designer-u24 to ubuntu's agent-working-designer

**From** `agent-working-designer-u24` (host u24desktop), which wrote both documents. **To** `agent-working-designer` on host ubuntu. **Date** 2026-10-30.
**Why:** an owner instruction, #715 6525124859 (given in the ubuntu lead-planner terminal): "transfer that new major epic to this host, register this host an agent-working-designer, give it the documetn and the context". The owner also chose "Push as-is" for the public repo (#715 6525164303).
**After this handover** the u24 seat stops all work on this epic and keeps no parallel copy. The gitignored originals stay in the u24 main checkout's `tmp/` unless the owner says otherwise.

This file holds only the context that the two documents don't.

## 1. What you are receiving

| File | What it is | Status |
|---|---|---|
| `AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md` | Read-only discovery and audit of the SDLC machinery, at `815eef38d` (2026-10-26). About 20.7k words, 9 Mermaid diagrams. It carries a 12-item errata block (2026-10-26) written during the plan's revalidation; read the errata first. | Final, superseded where the errata say so |
| `AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md` | Architecture alternatives, target architecture, phased roadmap, at `1f749c1aa` (2026-10-26). About 16k words, 61 sections, 6 diagrams. | **Proposal only. Nothing is implemented, no ticket exists.** |

*(Note 2026-10-31: true when written. Since then the plan has its Round 2 revision and the audit a small generalisation, so neither is byte-identical now.)* Both bodies are byte-identical to the `tmp/` originals: audit sha256 `5ad89dca…ffdd11`, plan sha256 `5a920f14…99bb`. The only addition is the frontmatter header, in its own commit. Their internal references to `tmp/...` paths are left as written; the files now live here.

**Not committed:** the two owner instruction specs the documents cite, `tmp/ai-first-audit-instruction.md` (audit) and `tmp/ai-first-audit-instruction-2.md` (plan). They exist only in the u24 main checkout and are gitignored. They define the section structure, the evidence and decision labels and the self-critique requirement (plan §61). If you need them, ask the owner (through your lead) to have u24 commit or send them.

## 2. Decided, and ruled out

**Owner-decided (in force; the documents build on these):**
- Audit scope (2026-10-26, audit header): the repo plus local Claude config plus runtime state; SDLC machinery only; repo and host names kept, secrets redacted.
- Standing operating constraints, collected with dates in plan §13: AI-first up to the human points (push, PR, merge, workflow opt-in); guardrail, not a sandbox; **no new orchestration engine**; no blocking gates on monitoring data; one PR per batch; owner-only merge, push to main, remote delete and worktree/data delete; never `bypassPermissions`; token efficiency over speed.
- Since the documents (2026-10-28): owner asks from u24 seats go through lead-planner-u24, which logs the answer on #715 first and relays the comment id (#715 6459766303). The role cards now say a lead seat citing that comment id can carry an approval (#715 6459850177 item 4, landed as #772). This is relevant to OD-2 and OD-3: it is a process workaround for the shared identity, not the identity fix the plan recommends.

**Recommended but NOT decided:** Alternative D, the "evidence-gated hand path" (plan §4, §20), and phases 0 to 6 (§39).

**Ruled out by the author** (plan §60 has the full reasons): A alone (harden and keep everything); B (lean rebuild); C2/C3 (LangGraph, Temporal: they break the no-new-engine constraint and there's no demonstrated need); restoring the 12-phase pipeline as default (0 completions in 3 weeks; one failed run cost 925k tokens); the sandbox as the primary control; a database-backed state store; a full OTel collector now; ephemeral workers replacing seats (kept only as experiment E2c). These were the author's judgments, not owner decisions; the owner can reopen any of them.

## 3. Owner conversation about OD-1..OD-9

**None of OD-1..OD-9 is decided.** This was checked on #715 at the handover and in the u24 seat's own records.
- After the audit (2026-10-26) the u24 seat put five questions to the owner in chat: (1) retire or rehabilitate the formal pipeline, (2) a separate agent GitHub identity, (3) the CLAUDE.md "push/PR need the user" prose against a config that allows them, (4) draft an epic from the recommendations, (5) publish the report as a private artifact page. None was answered. The plan folded (1) to (3) into OD-1, OD-2, OD-3 and OD-5. (4) is effectively this transfer. (5) was overtaken by the owner's "Push as-is" choice.
- After the plan (2026-10-26) the owner gave no answer on any OD.
- The transfer instruction (#715 6525124859) and the push answer (#715 6525164303) both say explicitly that they decide none of the ODs.
- Plan §43 lists the decision checkpoints, and §51 to §53 split decisions into "can be made now", "need more evidence" and "reserved for the owner".

## 4. Stale evidence: re-check before relying on it

- **Revision.** The plan reads `1f749c1aa` and the audit `815eef38d`. At this handover `origin/main` was `ba7aa11bd`, 38 commits past the plan. The SDLC-relevant ones: #754 (the graphify pin shim, role cards fold scattered files, the card budget falls from 460 to 456), #759 (RPG-OWNS-RPG-MEASURE), #763 (the graphify rebuild-command doc fix), #772 (lead-relayed approval wording in the role cards). The plan's "460-token card budget" (§13) is now 456.
- **Workload numbers (W42-W43).** Closure counts, the "100% hand-closed" headline, the closure-reliability baseline (84 tickets, 51 PRs, E1) and coordination-overhead figures all come from W42-W43 monitoring data. W44 data has accumulated since (the week runs to 2026-11-01). When the documents were written the W42/W43 per-batch shards had not been folded by close-week, and at this handover the session hook still reported them unfolded. Re-run the counts before quoting them.
- **Live GitHub facts** (ruleset, required checks, admin bypass on every merge, the single admin login) were read from the API on 2026-10-26. They're the plan's highest-confidence facts, but they're live settings: re-read them before Phase 1.
- **Claude Code behaviour** (auto mode honouring `ask` rules; the classifier allowing pushes to the default branch; settings and hooks hot-reloading) was taken from the docs at v2.1.31x on a host running 2.1.310 [plan Src R13]. It was not tested live; the audit's E-3 (does auto mode honour `ask`?) was answered from the docs only.
- **Research access** was limited from u24 (arxiv.org and openai.com blocked). Several references were read through mirrors or summaries (plan §7). Ubuntu may be able to read the originals.

## 5. The ubuntu-workload gap

The u24 seat could not inspect host ubuntu. Everything about ubuntu came from committed repo evidence only (audit header; plan §7 "Medium confidence: the workload of the ubuntu host (not inspected)"; §55 open question 5 "What did the ubuntu host's sessions do in W42-W43?"; §59 assumption "The ubuntu host behaves like u24", Medium confidence, which the seat-workload conclusions depend on).
From ubuntu you can close this gap directly: its local `~/.claude` config and settings, its guard and permission setup, its handover notes and `.git/session-roles` runtime state, and its sessions' share of W42-W44 closures. If ubuntu differs materially (for example, the formal pipeline is used there, or permissions differ), the hand-path dominance and seat-model conclusions need revisiting before OD-1 and OD-5.

## 6. Half-finished and not executed

- **Experiments (plan §45).** Only **E1** (closure reliability, read-only) ran. Not run: E1-replay (close-check precision, Phase 2), E2a/E2b/E2c (thin chain vs hand path, independent reviewer, ephemeral vs seat: opt-in, token cost, Phase 6), E3 (context retrieval baseline: read-only, possible now), E4 (recovery, opt-in), E5 re-run (traceability, Phase 3; the baseline is audit §28), **E6** (identity boundaries: owner present, on a scratch PR, Phase 1), E7 "after" (simplification, Phase 4), E8 (instruction/skill ablation, opt-in). Everything that writes state or costs tokens needs owner opt-in.
- **Registry change for your seat.** The instruction reverses the 2026-10-18 "no designer on host ubuntu" note: in `registries/session_roles.yaml` the ubuntu `agent-working-designer` row is `seat_status: unstaffed, interim_holder: agent-working-planner`. #715 6525124859 says the flip goes through the agent-working domain as a normal change. It is **not** done on this branch.
- **Diagram checking.** All 15 Mermaid diagrams parsed at the time, with mermaid 11.4.1 plus jsdom in a session scratchpad (`check.mjs`) that's no longer guaranteed to exist. If you edit the diagrams, set up your own parser.
- **No epic or tickets exist.** This branch is an S2 backup with no PR; per the instruction it folds into the epic's first PR. Its commits carry an `agent-working:` prefix instead of a TCK id for that reason.
- **Public repo.** The documents describe control weaknesses: one shared admin identity, admin-bypass merges, and auto mode allowing pushes to the default branch. The owner chose to push them as-is (#715 6525164303). Keep that in mind when deciding what new findings to commit, and ask the owner through your lead if a finding goes further.

## 7. Suggested first steps (non-binding)

1. Read the audit errata, then plan §1 to §7, §43 and §51 to §55.
2. Close the ubuntu gap (§5 above) and refresh the stale numbers (§4) before taking the ODs to the owner.
3. Put OD-1..OD-9 to the owner through your lead, as the plan's §6 table. OD-2 (machine user) and OD-1 (official execution model) unblock most of the roadmap.
