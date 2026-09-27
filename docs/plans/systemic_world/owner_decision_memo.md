---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-27"
---

# Systemic World — Owner Decision Memo — PROPOSED / FOR REVIEW

This memo holds only choices that evidence and normal planner judgment cannot settle. Engineering
questions, such as which code path owns a fact or how a merge is resolved, belong to the ticket
planner and the implementers (`ticket_planner_handoff.md`).

Frontmatter `status: active` means "live working document", not approval.

| # | Decision | Kind | Recommended default | Consequence of each choice | Needed by |
|---|---|---|---|---|---|
| 1 | Which first-wave epic set? | Epic priority | **Revised 2026-09-28 — the planner now leans to "reachability-first".** `first_wave_plan.md` describes option (a) and will be revised if (b) is chosen. Reasons are in roadmap §11, items 1, 3 and 5. | **(a) A + B + C, as planned.** Sound foundations, but nothing visible changes. A's defect only fires at about 20M ticks, and B is design only. **(b) Reachability-first.** A program making mechanisms the registry calls "done" actually fire in ordinary runs (portfolio Epic J), plus verifying whether situated perception is live, plus C. This changes real runs sooner but delays the lineage story. **(c) (a) without B.** World correctness still lands, but nothing progresses toward a player proof. | Before the ticket planner starts |
| 2 | Is inheritance/succession an outcome a situated player is **meant** to be able to understand? | Product scope | **Yes, at a coarse level**: who now holds a household's possessions or role. Inherited grudges and dying wishes stay private unless they later produce observable behaviour. | **Yes:** Epic B uses inheritance as its probe event. **No, keep it private:** also valid, because hidden foundations are allowed. Epic B picks a different probe event whose understanding *is* intended, and Epic A is unaffected. | Before Epic B starts |
| 3 | Are individual subjective relations and institutional judgments distinct world concepts, with different authority, evidence and update rules? | World semantics (carried forward) | **Distinct**, per `SOC-01` and `INST-03`, as cited in the roadmap. That is inherited evidence, not rechecked this pass. | **Distinct:** separate epics and authorities for personal and institutional standing. **One concept at two scales:** a shared model, with the risk of conflating trust and legitimacy. | Before any institutional-judgment or recognition epic is scoped. Not first wave. |
| 4 | What is `public_reputation` meant to be in the world: publicly knowable fact, declared-scope claim, derived projection, or technical fallback? | World semantics (carried forward) | **None yet.** Define its meaning and provenance first. Its current use as a global fallback for strangers is not evidence that it is public knowledge. | Determines whether any future surface may show it, and whether it can feed opportunities. Epic C's reputation check is mechanical only and does not need this answer. | Before any epic reads or surfaces reputation. Not first wave. |
| 5 | How should world time scale relate to feasible run length? | Product scope / world semantics | **None yet; needs owner intent.** A lifespan is about 20M ticks, while affordable runs are thousands of ticks. So generational history, the core of the "persistent world" claim, never happens naturally in any run we can make. See roadmap §11 item 2. | **Compress lifespans or world time:** lineage becomes observable, but pacing across every domain shifts. **Invest in far longer runs:** real time scale is kept, at a performance cost. **Accept that generational effects are rare:** choose probes that play out over days or weeks of world time instead. | Before lineage is used as a *natural* (unstaged) proof. Epic A's correctness fix does not need it. |
| 6 | Where will player-inference evidence come from? | Product scope / evaluation | **None yet.** `PLAYER-EXPERIENCED` requires a blinded human, and the owner knows the answers. See roadmap §11 item 4. | **Recruit blinded observers:** the claim can then actually be earned. **Accept a declared proxy** (for example, a reviewer given only the clues who is not told the answer): cheaper and weaker, and it must be labelled as a proxy. **Defer:** player-side claims then stay `PENDING` indefinitely. | Before any epic claims a player-inference result. Not first wave. |

**Not owner decisions, and so not listed:**
- which trajectory to probe first (resolved: lineage is the working default, roadmap §7.4);
- institutional standing's domain home (default: the institutions domain; escalate only if a real
  cross-domain conflict appears);
- keeping or discarding the unmerged prototype branch (a routine engineering matter);
- roadmap promotion (a governance step after review).
