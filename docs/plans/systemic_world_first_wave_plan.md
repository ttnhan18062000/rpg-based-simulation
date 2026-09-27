---
status: proposed
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-27"
---

# Systemic World First-Wave Milestone Plan — PROPOSED / FOR REVIEW

**Status: `PROPOSED / FOR REVIEW`. Not owner-approved.** Companion document to
`docs/plans/systemic_world_roadmap.md` (the capability/dependency map) — this document is the
separate, concrete milestone plan the roadmap's §8 and the fourth external review round both ask
for, so the roadmap itself stays a map rather than a milestone transcript. Produced from the actual
feasibility-gate run, composition probe, observer-evidence sketch, and bounded authority audit in
the roadmap's §7/§3.1 (2026-09-27) — every claim below cites that evidence rather than repeating it.

**This is a conditional plan, not a committed backlog.** One milestone (M1) exists only because this
round's investigation surfaced a real, load-bearing defect; the plan branches explicitly at the
decision gate after M1+M2 rather than assuming M3/M4 are automatically justified.

---

## 1. Outcome and scope

**What this wave aims to establish**: that the lineage single-hop death→heir transition
(`succession`/`aging_death`, `state: done`, `verified: observed`) can be presented to a situated
observer with a legitimate evidence trail, and that at least one class of the regional-sovereignty
defect pattern (dual-writer races on durable fields with no declared precedence rule) is checked
and, where found, precisely diagnosed — bounded to a named set of boundaries, not the whole engine.

**What this wave does NOT aim to establish, this round**:
- A composed, multi-generation lineage sequence (§7.1 of the roadmap: this is `BLOCKED` on a
  confirmed defect, not attempted here — see M1 and the decision gate).
- A durable changed-life-trajectory proof (roadmap §5's closed-loop distinction — requires a later
  decision/opportunity and durable outcome; this wave produces at most a reaction-level proof).
- A recognition-domain proof (roadmap Path 1 — depends on §3.4's propagation gap, out of this
  wave's scope entirely).
- Full-Catalog Rule mapping, a second registry, or a universal ontology (explicitly out of scope
  per both external review rounds).
- Any renderer, final gameplay lens, or art-pipeline decision (interface/contract level only — §6
  below).

**Domain ownership stays distinct across this wave** — lineage, world-substrate/authority, and
observation/delivery are three separate owners below, not one team or one deployment sequence.

---

## 2. Milestones — dependency order, domain ownership, parallel paths

```text
M1 (world-substrate/authority) ──┐
                                   ├──> Decision gate ──> M4 (conditional: composed-sequence work)
M2 (lineage + observation/delivery) ─┘

M3 (world-substrate/authority) ── fully parallel to M1/M2, independent exit evidence
```

| Milestone | Domain owner | Depends on | Parallel with |
|---|---|---|---|
| M1 — Fix the `entity.lifecycle.active` dual-writer race | World substrate / engine-core (§3.1 area) | Nothing new | M2, M3 |
| M2 — Single-hop observer test | Lineage (social/history) + Observation/delivery | Nothing new (uses today's `verified: observed` mechanisms) | M1, M3 |
| M3 — Resolve the 3 `UNKNOWN_WITH_REASON` audit boundaries | World substrate / respective domain owners (faction, combat, social) | Nothing new | M1, M2 |
| M4 — Composed multi-hop sequence + closed-loop proof groundwork | Lineage + Observation/delivery | M1 (hard dependency) | — (starts only after the decision gate) |

---

## 3. Milestone detail

### M1 — Fix or explicitly re-scope the `entity.lifecycle.active` dual-writer race

**Entry evidence**: roadmap §7.1 — a real, reproducible defect: `ApplyPath._compute_entity_changes`
(`src/engine/apply.py:94-99`) commits `active=False` one tick ahead of
`LifecycleSystem.resolve_lifecycle`'s own OLD_AGE check (`src/systems/lifecycle_systems/
lifecycle.py:193-194`), for any death arriving through ordinary per-tick aging rather than the
artificially-staged case both existing repo tests use. Verified empirically (5-tick run, printed
per-tick state), not merely traced.

**Deliverable**: a declared precedence rule between the two writers of `entity.lifecycle.active` —
consistent with the roadmap's own §3.1 semantic obligation ("every persistent fact has a canonical
authority... a world effect must not commit from stale assumptions without a declared resolution
rule"). This does not have to mean one physical writer; it can mean `ApplyPath`'s passive branch
defers to `resolve_lifecycle`'s own dispatch when both would fire in the same tick, or an equivalent
explicit ordering — a real engineering ticket's own job to design, not decided here.

**Finite exit evidence**: the 5-tick natural-aging probe (or an equivalent regression test) shows
`death_reason="OLD_AGE"` set and succession/heirloom/dying-wish dispatch firing on the tick where
`age_ticks` first reaches `max_age_ticks`, through ordinary per-tick aging — no manual mid-run state
staging. Existing tests (`test_heir_inventory_transfer_corpus.py`,
`test_lineage_dispatch_deterministic_kernel_tick.py`, `test_aging_death_value_differential.py`)
continue to pass unmodified.

**Relevant Rules/mechanisms/scenarios**: `aging_death`, `succession` (`registries/mechanisms.yaml`);
no Catalog Rule change — this is an implementation-correctness fix, not a semantic one.

**Failure/blocked branch**: if the fix requires touching `ApplyPath`'s passive-decay branch in a way
that risks other entities' `active` semantics (combat death, hazard death), scope the fix narrowly
to the OLD_AGE case first and flag the broader `ApplyPath` review as a separate, later item — do not
let this milestone grow into a general `ApplyPath` audit.

### M2 — Single-hop observer test

**Entry evidence**: roadmap §7.2 — a design-check sketch already exists (observer position, one
early legitimate clue, one reasonable-but-unprovable hypothesis, two named negative checks). The
underlying mechanisms are `verified: observed` today; this milestone does not wait on M1.

**Deliverable**: turn the design sketch into a real, minimal observer-side check — not full UI or
renderer work. Concretely: a small scenario/corpus-tier test (or equivalent) that stages the tick-0
inheritance scenario, exposes the heir's changed inventory as a legitimate in-world signal from a
specified viewpoint, and records whether an independent observer (human reviewer or a scripted
check standing in for one) can state a reasonable, clue-supported hypothesis without being told the
answer.

**Finite exit evidence**: gate question 2 (roadmap §5/§7) answered from this real check — either a
documented "yes, an observer can form a reasonable hypothesis from the available clue" with the
specific clue cited, or `BLOCKED`/`PARTIAL` with a named reason (e.g., the clue is too weak to
distinguish heir from looter, per §7.2's own caveat).

**Relevant Rules/mechanisms/scenarios**: `succession`/`aging_death`; the epistemic principle (roadmap
§2); `KnowledgeModelService`'s existing hidden-world-truth-not-injected invariant as the negative
constraint to check against (do not leak `cognition.motivation.named_intention` or
`strategic.blockers` verbatim — roadmap §7.2's named leak-risk fields).

**Failure/blocked branch**: if the only available clue (changed inventory) turns out to be too weak
to support any reasonable hypothesis distinct from "random item change," report this as a genuine
evidence-production gap for lineage — not a reason to abandon the milestone, but a reason to name a
follow-up item (a dedicated inheritance-provenance signal) before claiming Q2 `passed`.

### M3 — Resolve the 3 `UNKNOWN_WITH_REASON` audit boundaries

**Entry evidence**: roadmap §3.1's bounded audit already named these three and their reason for
being unresolved:
1. Entity death: `alive_set` written from `combat.py` and `world_dynamics.py` — precedence comments
   exist, no scenario test verifies them.
2. Faction diplomacy: `diplomatic_relations_set` from the autonomous state machine and the
   auto-alliance handler, same tick — ordering looks intentional, unverified by scenario.
3. Public reputation: `SocialComponent.reputation` (`reputation_set`) from two files — no phase-
   ordering or same-tick-collision check run.

**Deliverable**: one representative integration scenario per boundary, each exercising the
same-tick-collision case the audit named. Reclassify each from `UNKNOWN_WITH_REASON` to either
`CONFIRMED_FINE_WITHIN_SCOPE` (with the passing scenario as evidence) or `DEFECT_CONFIRMED` (with a
root cause, matching M1's own diagnostic depth) — do not leave any of the three at `UNKNOWN` without
having actually tried the scenario.

**Finite exit evidence**: three scenario results, each with an explicit classification and citation,
recorded back into the roadmap's §3.1 audit table (or a dated addendum to it) — not a new document.

**Relevant Rules/mechanisms/scenarios**: none new; reuses each domain's own existing pipeline-phase
tests as a template.

**Failure/blocked branch**: if any boundary turns out `DEFECT_CONFIRMED`, treat it exactly as M1 was
treated here — document and escalate via a real ticket, do not fix it inside this milestone's own
scope unless it is trivially the same shape as M1's fix.

### M4 — Composed multi-hop sequence + closed-loop proof groundwork (conditional, post-gate)

**Entry evidence**: M1 must be complete and its exit evidence verified. This milestone does not
start otherwise — it is explicitly gated, not merely sequenced for convenience.

**Deliverable**: repeat the composition probe (roadmap §7.1's second attempt) using ordinary
per-tick aging now that the race is fixed; confirm the heir's own eventual death correctly cascades
succession a second time. If that succeeds, begin — but do not complete within this wave — the
groundwork for a closed-loop proof (a later decision/opportunity producing a durable, player-
observable outcome, per roadmap §5's evidence ladder's final rung).

**Finite exit evidence**: a real two-hop composed run (grandparent → parent → grandchild, both hops
through ordinary aging) with identity and chronology preserved across both hops — answers gate
questions 1 (fuller form) and 3 for real, not narrated.

**Relevant Rules/mechanisms/scenarios**: `succession`/`aging_death`, post-M1.

**Failure/blocked branch**: if M1's fix does not actually enable natural two-hop composition (e.g.,
a second, different defect surfaces), report the new blocker with the same precision as §7.1 and
return to the decision gate rather than silently extending this milestone's scope.

---

## 4. Decision gate (after M1 + M2, before M4)

Do not start M4 until:
- M1's exit evidence is real (natural-aging succession fires correctly), **and**
- M2's exit evidence is real (an observer can, or explicitly cannot, form a reasonable hypothesis
  from today's single-hop evidence).

**If both pass**: M4 proceeds as scoped above — still only a single additional hop, not a full
multi-generation arc, and still not a closed-loop proof.

**If M1 passes but M2 finds the available clue too weak (§7.2's own named risk)**: pause M4;
the priority shifts to designing a real evidence-production signal for inheritance before
attempting composition at all, since a composed sequence with no legible clue at either hop is not
worth building.

**If M1 fails or surfaces a second defect**: return to the roadmap's §3.1 audit process — this may
indicate the dual-writer-race pattern is broader than the two instances found so far, which would
be new information for the roadmap itself, not just this plan.

---

## 5. World-side and player-side acceptance criteria (kept separate, per the roadmap's §5 evaluation criterion)

**World-side (M1, M2, M3, M4 exit evidence above)**: the underlying outcome has a coherent,
Rule-conforming causal trace, and the state transition is committed through the authoritative
pipeline with a declared precedence rule — never a stale-assumption commit. This is checked by real
`Kernel.tick_once()` runs and scenario tests, not by code inspection alone.

**Player-side (M2's own exit evidence, and any future M4 follow-on)**: given only the legitimate
clues a specified observer position can encounter, can a reasonable (possibly wrong) hypothesis be
formed, and would a later clue be able to revise it? This is checked by the observer test itself,
not inferred from the world-side check passing. **A world-side pass does not imply a player-side
pass** — M1 succeeding only re-enables composition; it says nothing about whether that composition
would be legible to an observer, which stays M2/M4's own separate question.

---

## 6. Bounded evidence and regression strategy

Reuses existing infrastructure only — no new registry, no new governance system:
- **Scenario/corpus tests**: the existing `tests/simulation_quality/` and
  `tests/integration/campaigns/` conventions, extended with the natural-aging regression test (M1)
  and the observer-check scenario (M2) — new test files, not a new test framework.
- **Mechanism registry**: `succession`/`aging_death`'s existing entries get a dated addendum note
  once M1 lands (matching this registry's own established convention of appending dated notes
  rather than rewriting history) — done through whatever ticket implements M1, not this document.
- **Semantic Control Plane**: no new mapping required for M1-M3 (none of the touched fields are
  currently SCP-mapped); if M4's eventual work touches a mapped Rule, record it through the SCP's
  normal evidence process (roadmap §11's tooling), not a new parallel process.
- **No "full Catalog complete" gate anywhere in this plan.**

---

## 7. Presentation integration — interface/contract level only

This wave produces, at most, a **data contract** for what a future gameplay lens could read (e.g.,
"an inheritance event, once evidence-produced, exposes X shape to a viewpoint-scoped query") — it
does not select a renderer, a final gameplay lens, or an art pipeline. Per the roadmap's own §0
table, `render_and_art_program_roadmap.md`/`hud_delivery_roadmap.md`/`live_map_scaling_roadmap.md`
own the "how it renders" question entirely; this plan only ever answers "what could legitimately be
exposed," consistent with roadmap §2's epistemic principle.

---

## 8. Open decisions and when they become blocking

None of the roadmap's Owner Decision List items block this wave:

- **Individual-vs-institutional standing** (Owner Decision List item 1): not used by any milestone
  here — lineage's inheritance/succession mechanisms don't touch institutional standing. Stays
  visible for whoever scopes the recognition-domain work later (roadmap Path 1), not blocking here.
- **Institutional standing's domain ownership** (item 2): same — not touched by this wave.
- **`public_reputation`'s intended meaning** (item 3): not touched by this wave's mechanisms
  (`SocialComponent.reputation` is M3's boundary #3, a *mechanical* dual-writer check only — this
  wave does not decide or depend on what `public_reputation` is supposed to mean semantically).
  Stays visible, not blocking.
- **Which candidate trajectory runs first** (item 4): already resolved as a recommended default for
  this wave specifically — lineage, per the roadmap's own gate results (§7).

**Genuinely new item this wave surfaces**: whether the `entity.lifecycle.active` fix (M1) should be
scoped narrowly (OLD_AGE case only) or broadened into a general `ApplyPath` dual-writer review is an
**engineering decision, not an owner decision** — recommended default is narrow scope first (per
M1's own failure/blocked branch above), escalated only if the narrow fix turns out to be impossible
without touching the broader branch.

---

## 9. Feeding results back to the roadmap and the Semantic Control Plane

- **M1's result** (fixed, or re-scoped with a named reason) updates roadmap §7.1/§3.1's audit table
  via a dated addendum — the roadmap is the capability map of record; this plan does not become a
  second source of truth for that finding once it resolves.
- **M2's result** updates roadmap §7.3's gate-question table (Q2's status) the same way.
- **M3's three reclassifications** update roadmap §3.1's audit table directly, converting each
  `UNKNOWN_WITH_REASON` to its real outcome.
- **M4's result, if the decision gate is passed**, updates roadmap §5's evidence table (lineage row)
  and may re-open the closed-loop-proof question as its own, later, separately-scoped item — this
  plan does not commit to scoping that follow-on work now.
- **No mapping claim from this wave is asserted as `SUPPORTED` in the Semantic Control Plane** unless
  it goes through the SCP's own established validation process (roadmap §11) — this plan's own
  findings are Catalog-level/mechanism-registry-level evidence, not a substitute for that process.

This plan stays `PROPOSED / FOR REVIEW` until the owner explicitly approves it; nothing in it
authorizes starting M1-M4 without that approval.
