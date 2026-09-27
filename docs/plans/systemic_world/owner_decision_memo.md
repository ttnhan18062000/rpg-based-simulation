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
| 1 | Accept the first-wave epic set: A (life/death continuity), B (situated evidence design), C (authority-boundary program) | Epic priority | **Accept A + B + C** (`first_wave_plan.md` §4) | **Accept:** the ticket planner starts on all three; none gates world-side work on B. **Drop B:** world correctness still lands, but no progress toward any player-inference proof, and later history/recognition epics lack an observer contract. **Replace B with individual history propagation:** a larger, cognition-heavy first step that still needs an observer contract. | Before the ticket planner starts |
| 2 | Is inheritance/succession an outcome a situated player is **meant** to be able to understand? | Product scope | **Yes, at a coarse level**: who now holds a household's possessions or role. Inherited grudges and dying wishes stay private unless they later produce observable behaviour. | **Yes:** Epic B uses inheritance as its probe event. **No, keep it private:** also valid, because hidden foundations are allowed. Epic B picks a different probe event whose understanding *is* intended, and Epic A is unaffected. | Before Epic B starts |
| 3 | Are individual subjective relations and institutional judgments distinct world concepts, with different authority, evidence and update rules? | World semantics (carried forward) | **Distinct**, per `SOC-01` and `INST-03`, as cited in the roadmap. That is inherited evidence, not rechecked this pass. | **Distinct:** separate epics and authorities for personal and institutional standing. **One concept at two scales:** a shared model, with the risk of conflating trust and legitimacy. | Before any institutional-judgment or recognition epic is scoped. Not first wave. |
| 4 | What is `public_reputation` meant to be in the world: publicly knowable fact, declared-scope claim, derived projection, or technical fallback? | World semantics (carried forward) | **None yet.** Define its meaning and provenance first. Its current use as a global fallback for strangers is not evidence that it is public knowledge. | Determines whether any future surface may show it, and whether it can feed opportunities. Epic C's reputation check is mechanical only and does not need this answer. | Before any epic reads or surfaces reputation. Not first wave. |

**Not owner decisions, and so not listed:**
- which trajectory to probe first (resolved: lineage is the working default, roadmap §7.4);
- institutional standing's domain home (default: the institutions domain; escalate only if a real
  cross-domain conflict appears);
- keeping or discarding the unmerged prototype branch (a routine engineering matter);
- roadmap promotion (a governance step after review).
