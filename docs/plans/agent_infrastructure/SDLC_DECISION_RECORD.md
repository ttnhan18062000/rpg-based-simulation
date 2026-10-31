---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-31
tags: [ai, governance, delivery, planning]
---

# AI-First SDLC: Decision Record

What the owner has decided about `AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md` (section 6), and what they have not. The plan's "Recommended" column is a recommendation, not a decision. A row reads **decided** only when it matches what an owner comment says, in that comment's words; where the plan and a comment differ, the comment wins. Plan and summary read at `1ccaba303`.

Sources (all on issue #715, the approvals log):

- **A** = comment 6529263880, owner answer given in the lead-planner terminal on 2026-10-31, recorded by lead-planner.
- **B** = comment 6529808776, owner answers given in the agent-working-designer terminal on 2026-10-30T17:55Z, recorded by lead-planner.

## Decided

| ID | Decision | Date | Source | Exact scope |
|---|---|---|---|---|
| OD-1 | The hand/batch path is the official model | 2026-10-31 | A | Yes. Does not retire the pipeline (that is OD-5). |
| OD-2 | A machine user for agents | 2026-10-31 | A | Yes ("machine user for agents; owner credentials off both hosts, old tokens revoked"), with OD-10. No credential change is authorised yet. |
| OD-10 | Where owner credentials live | 2026-10-31 | A | Yes, with OD-2 (same wording). No credential change is authorised yet. |
| OD-3 | Merge model | 2026-10-31 | A | **M1**: keep owner-only merge via the `update` rule, **subject to E6b confirming it**. No ruleset change is authorised yet. |
| OD-14 | Security rollback | 2026-10-31 | A | Yes: "safe rollback, agents never regain the owner token". |
| OD-15 | Freeze baselines before retirement | 2026-10-31 | A | Yes: "freeze baselines as tags". A tag push is a separate owner ask. |

Decided, but not an OD:

| Item | Date | Source | Exact scope |
|---|---|---|---|
| E6b | 2026-10-31 | A | Yes: a throwaway public repo test of GitHub behaviours; no production settings touched. |
| Audit document | 2026-10-30 | B | "Generalise, delete branch later": the docs PR generalises the credential details in the audit before it lands on main; the branch `agent-working-designer-u24-sdlc-plan-handover` is deleted after the docs PR, on the owner's own command. |
| E6b identity | 2026-10-30 | B | "Create the machine user now": the owner creates the account themself, added only to a throwaway repo, with a token that cannot reach this repo; it stays out of this repo until the Phase 1 ask. |

**No credential or ruleset change on this repository is authorised** by A or B. Execution comes later by ticket, each with its own ask.

## Undecided

All of these read undecided as of 2026-10-31 (A and B both say so). Nothing below is decided by being listed in the plan, the summary or a ticket.

| ID | Decision (plan section 6 title) |
|---|---|
| OD-4 | What has to be machine-proven before a close |
| OD-5 | Retire `implement-ticket.js`, `implement-epic.js` and the skill imitation |
| OD-6 | Codex/provider-neutral track |
| OD-7 | Owner review load (follows OD-3) |
| OD-8 | A token/cost budget |
| OD-9 | Coordination target |
| OD-11 | Evidence lifecycle |
| OD-12 | Claim consistency |
| OD-13 | Required CI shape |
| OD-16 | Evaluation investment and execution |
| OD-17 | Evaluation framework |
| OD-18 | Scope of model comparisons |
| OD-19 | Advanced optimization |
| OD-20 | Promotion of an experimental result |
| OD-21 | Practical threshold and budget per stage |

## Where the plan's wording differs from the comments

- OD-2 and OD-10: the plan's table says the owner's credentials "leave agent-reachable storage"; comment A says "off both hosts". This record uses the comment's words.
- OD-14: the plan recommends "Suspend" publishing; comment A says "safe rollback, agents never regain the owner token". This record uses the comment's words.
