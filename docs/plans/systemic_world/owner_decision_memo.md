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
| 1 | Accept the proposed first wave: **bounded reachability-first** (`first_wave_plan.md`)? | Epic priority | **ACCEPTED by the owner, 2026-09-28.** This approves the scope for ticket planning only. It does not approve implementation results or any player-experience proof. It is supported in principle by external review; the reasons are in roadmap §11 items 1, 3 and 5. It contains: Epic J over exactly three named mechanisms (J1 `calamity_intensity`, J2 `regional_trauma`, each linking its existing open ticket; J3 `aging_death`/`succession`); Epic B0, a situated-observation feasibility check (runtime perception check, plus one combat death in an ordinary run, with trace existence and situated encounterability reported separately); and Epic C1, the entity-death authority boundary. The natural-aging defect is ready for planning but scheduled only by a trigger (plan §3). The diplomacy and reputation checks sit outside the wave, with owners and revisit triggers. | **Accept:** the ticket planner starts on J, B0 and C1. Better behaviour in ordinary runs is tested as a hypothesis, not promised. **Alternative (a), A + B + C:** sound foundations, but nothing tests real-run behaviour. A's defect only fires at about 20M ticks, and B is design only. **Alternative (c), A + C:** no player-side progress at all. | Before the ticket planner starts |
| 2 | Is inheritance/succession an outcome a situated player is **meant** to be able to understand? | Product scope | **Yes, at a coarse level**: who now holds a household's possessions or role. Inherited grudges and dying wishes stay private unless they later produce observable behaviour. | **Yes:** Epic B uses inheritance as its probe event. **No, keep it private:** also valid, because hidden foundations are allowed. Epic B picks a different probe event whose understanding *is* intended, and Epic A is unaffected. | Before Epic B starts |
| 3 | Are individual subjective relations and institutional judgments distinct world concepts, with different authority, evidence and update rules? | World semantics (carried forward) | **Distinct**, per `SOC-01` and `INST-03`, as cited in the roadmap. That is inherited evidence, not rechecked this pass. | **Distinct:** separate epics and authorities for personal and institutional standing. **One concept at two scales:** a shared model, with the risk of conflating trust and legitimacy. | Before any institutional-judgment or recognition epic is scoped. Not first wave. |
| 4 | What is `public_reputation` meant to be in the world: publicly knowable fact, declared-scope claim, derived projection, or technical fallback? | World semantics (carried forward) | **None yet.** Define its meaning and provenance first. Its current use as a global fallback for strangers is not evidence that it is public knowledge. | Determines whether any future surface may show it, and whether it can feed opportunities. Epic C's reputation check is mechanical only and does not need this answer. | Before any epic reads or surfaces reputation. Not first wave. |
| 5 | How do world time, run duration, and scenario starting conditions relate for long-horizon claims? | World semantics and product scope | **None yet; needs owner intent.** Three separate questions (roadmap §11 item 2): **(i) world-time semantics**: what a tick and a lifespan mean in the world; **(ii) feasible run duration**: how long a run we will pay for; **(iii) scenario initial conditions**: whether starting a scenario with aged or historied subjects is a legitimate way to show long-horizon effects. The current corpus does not naturally reach generational succession. Other domains need their own evidence before the same claim is made about them. | **(i):** changing world-time semantics, e.g. compressing lifespans, makes lineage observable but shifts pacing in every domain. **(ii):** longer runs keep the semantics, at a performance cost. **(iii):** accepting declared initial conditions allows long-horizon proofs now, labelled as "from a chosen starting state" rather than "emergent from zero". These can be combined. | Before lineage is claimed as *naturally emergent*. **Does not block** the bounded reachability investigation. It sets the delivery priority of the natural-aging defect, not whether the defect gets fixed. |
| 6 | What evidence counts for player understanding? | Product scope / evaluation | **Two tiers** (roadmap §11 item 4). **Formative:** a blinded proxy reviewer (given only the encounterable clues, not told the answer) gives design feedback, labelled as proxy evidence. **`PLAYER-EXPERIENCED`:** claimable only from an appropriately blinded player-observation exercise. Needs: who can serve as blinded proxies, and when a real player exercise is warranted. | **Proxy only:** fast design feedback, but never a `PLAYER-EXPERIENCED` claim. **Plan a player exercise:** the claim becomes earnable, at a recruitment cost. **Defer both:** player-side claims stay `PENDING`. | Before any epic reports player-understanding evidence. **Does not block** the bounded reachability investigation. |

**Not owner decisions, and so not listed:**
- which trajectory to probe first (resolved: lineage is the working default, roadmap §7.4);
- institutional standing's domain home (default: the institutions domain; escalate only if a real
  cross-domain conflict appears);
- keeping or discarding the unmerged prototype branch (a routine engineering matter);
- roadmap promotion (a governance step after review).
