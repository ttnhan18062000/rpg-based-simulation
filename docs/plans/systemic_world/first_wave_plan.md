---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-27"
---

# Systemic World First-Wave Milestone Plan — PROPOSED / FOR REVIEW

**Status: `PROPOSED / FOR REVIEW`. Not owner-approved.** Companion document to
`docs/plans/systemic_world/roadmap.md` (the capability/dependency map) — this document is the
separate, concrete milestone plan the roadmap's §8 asks for, so the roadmap itself stays a map
rather than a milestone transcript. Produced from the actual
feasibility-gate run, composition probe, observer-evidence sketch, and bounded authority audit in
the roadmap's §7/§3.1 (2026-09-27) — every claim below cites that evidence rather than repeating it.

**This is a plan for owner review, not a started wave.** No milestone below begins until the
owner has reviewed this scope. M1's implementation ticket is drafted
(`tickets/todos/TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE.md`); no other milestone ticket
exists yet.

**World correctness and product legibility are separate tracks with separate gates.** Fixing M1's
defect and verifying a composed world-side sequence (M4a) is worthwhile whatever M2 finds; a weak,
negative, blocked, or pending M2 result never pauses M4a. An optional observer/projection follow-on
on the composed sequence is a future-scoping note (§3, end), not a milestone of this wave. Do not
read this plan as one linear M1→M2→M4 chain.

---

## 1. Outcome and scope

**What this wave aims to establish**:
- **World side**: natural aging leads to an authoritative OLD_AGE death and succession, and a
  bounded two-hop lineage sequence works through ordinary ticks (M1, M4a).
- **Player side**: a chosen, owner-scoped design for the minimum evidence-production and in-world
  carrier path that would let a situated observer encounter a single inheritance (M2). Today no
  such path exists (roadmap §7.2), so this wave designs it; it does not build or prove it.
- **Foundation**: explicit outcomes for the three remaining named authority boundaries (M3a/b/c).

**What this wave does NOT aim to establish**:
- Any player-facing or `PLAYER-EXPERIENCED` proof. No clue is encounterable today, so there is
  nothing for an observer exercise to evaluate within this wave.
- Anything beyond M4a's single bounded two-hop run. One composed run proves that run only. It does
  not show natural frequency, population-wide emergence, or a multi-generation arc.
- A durable changed-life-trajectory proof (roadmap §5's closed-loop distinction). That needs a later
  decision or opportunity and a durable outcome; this wave produces no player-facing proof at all.
- A recognition-domain proof (roadmap Path 1 — depends on §3.4's propagation gap, out of this
  wave's scope entirely).
- Full-Catalog Rule mapping, a second registry, or a universal ontology (explicitly out of scope
  here).
- Any renderer, final gameplay lens, or art-pipeline decision (interface/contract level only — §6
  below).

**Domain ownership stays distinct across this wave** — lineage, world-substrate/authority, and
observation/delivery are three separate owners below, not one team or one deployment sequence.

---

## 2. Milestones — dependency order, domain ownership, parallel paths

**This wave has 6 milestones, all with finite exit evidence: M1, M2, M3a, M3b, M3c, M4a.** A
further follow-on beyond the composed sequence (previously drafted as "M4b") has no finite
deliverable this wave can commit to, so it is a "Future follow-on" note at the end of §3, not a
milestone.

```text
M1 (world-substrate/authority) ──> Gate A ──> M4a (world-side composed sequence)

M2 (lineage + perception/observation) ── independent of M1/M4a; a design milestone
                                          (evidence path), never gates M4a

M3a (combat + world-dynamics)     ── independently schedulable
M3b (faction)                     ── independently schedulable   } all three parallel to
M3c (social)                      ── independently schedulable   } M1, M2, M4a
```

| Milestone | Domain owner | Depends on | Parallel with |
|---|---|---|---|
| M1 — Fix the `entity.lifecycle.active` dual-writer race (ticket drafted) | World substrate / engine-core (§3.1 area) | Nothing new | M2, M3a, M3b, M3c |
| M2 — Choose the minimum evidence-production + carrier path for a single inheritance | Lineage + Perception/observation | Nothing new | M1, M3a, M3b, M3c, M4a |
| M3a — Resolve entity-death `alive_set` boundary | Combat + World dynamics | Nothing new | M1, M2, M3b, M3c |
| M3b — Resolve faction-diplomacy `diplomatic_relations_set` boundary | Faction | Nothing new | M1, M2, M3a, M3c |
| M3c — Resolve public-reputation `reputation_set` boundary | Social | Nothing new | M1, M2, M3a, M3b |
| M4a — Composed multi-hop world-side sequence | Lineage | M1 only (Gate A) — **not gated on M2** | M2, M3a, M3b, M3c |

---

## 3. Milestone detail

### M1 — Fix or explicitly re-scope the `entity.lifecycle.active` dual-writer race

**Entry evidence**: roadmap §7.1 describes a real, reproducible defect.
`ApplyPath._compute_entity_changes` (`src/engine/apply.py:106-109`) commits `active=False` one tick
ahead of `LifecycleSystem.resolve_lifecycle`'s own OLD_AGE check
(`src/systems/lifecycle_systems/lifecycle.py:193-194`). This happens for any death that arrives
through ordinary per-tick aging, as opposed to the artificially staged case both existing repo tests
use. It was verified at runtime twice, not just traced:
- a 5-tick probe, printing per-tick state;
- a regression scenario (seed 42), which failed 3/3 against current code. It is kept on the
  unmerged local branch `natural-aging-old-age-dispatch-fix-unreviewed`, not on this branch.

**Ticket**: `tickets/todos/TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE.md` (drafted, not
started). It carries the full reproduction, the acceptance criteria, and two open questions to
settle before merge:
- whether `initial_active=False` spawns currently rely on the passive branch to activate them;
- a sibling starvation/sleep-debt silent-death gap, which is a separate ticket.

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

### M2 — Choose the minimum evidence-production and carrier path for a single inheritance

**Entry evidence**: roadmap §7.2 records a read-only code inspection (2026-09-27) of the single
tick-0 inheritance. It answers the four observer-side checks as follows:

| Check | Result | Evidence level |
|---|---|---|
| 1. World state: the heir's inventory gains the item | `PASS` | Scenario runtime (`test_heir_inventory_transfer_corpus.py`, 1 passed) |
| 2. Encounter: a situated observer can receive a signal about it | `BLOCKED_WITH_REASON` — no in-world carrier delivers another entity's inventory/equipment to an observer (`PerceivedEntity` has no item fields; `PerceptionUpdatePhase` is not wired into production) | Reachable production path (inspection) |
| 3. Provenance: any clue identifies *inheritance* specifically | `ABSENT` — the transfer carries no origin marker | Reachable production path (inspection) |
| 4. Inference: a blinded human can reason from the clues | `BLOCKED` — no encounterable clue exists to reason from. This is not `PENDING`: there is nothing a human exercise could evaluate yet | — |

Non-leakage of `cognition.motivation.named_intention` / `strategic.blockers` is vacuously true for
in-world channels today and untestable until a carrier exists.

**Deliverable (finite, design only)**: a short design note choosing the minimum path that would
make a single inheritance legitimately encounterable. It names the owning domain and viewpoint
scope and drafts the implementation ticket. Two domain-appropriate candidates are known:
- **A. Viewpoint-scoped visible equipment in perception.** Coarse equipped slots only; never
  inventory contents or cognition. Owner: the perception domain. It first requires wiring
  `PerceptionUpdatePhase` into production. On its own it yields only the ambiguous clue "now
  carries X".
- **B. A witness-scoped local inheritance event.** Perceivable only by co-located or bonded
  entities, keeping direct participation, uninvolved witnessing, and hearsay distinct (roadmap
  §3.4). Owner: the lifecycle/lineage domain. It makes an inheritance-origin clue possible.

The note may choose A, B, both, or another path it justifies by domain meaning, authority, and
viewpoint scope. A dedicated provenance record is not mandated, and a global history feed is out.

**Finite exit evidence**: the design note and its drafted ticket exist and have been reviewed. The
player-facing status is recorded explicitly:
- `BLOCKED` while no clue is encounterable;
- then `PENDING` until a blinded-human exercise runs after the chosen path is built;
- never `PLAYER-EXPERIENCED` on script output.

**Failure/blocked branch**: if neither candidate is acceptable to its domain owner, record M2 as
`BLOCKED_WITH_REASON` with the objection. That affects no other milestone.

**Not in this wave**: building the chosen path, the scripted encounter/non-leakage test that becomes
possible once it exists, and the human exercise.

### M3a/M3b/M3c — Resolve the 3 `UNKNOWN_WITH_REASON` audit boundaries (independently schedulable)

**Each of the three is its own milestone, run in any order, by its own domain owner** — not one
atomic M3. Each may resolve to `CONFIRMED_FINE_WITHIN_SCOPE`, `DEFECT_CONFIRMED`, **or
`BLOCKED_WITH_REASON`** if a representative scenario genuinely cannot be executed (e.g., the harness
cannot stage the same-tick collision deterministically, or the relevant systems aren't independently
triggerable in a test). **Never force a fine/defect verdict where the honest answer is "couldn't
test it."**

**M3a — Entity death**: `alive_set` written from `combat.py` (5 sites) and `world_dynamics.py`
(hazard damage). Entry evidence: precedence comments exist (`groups.py:99`, `clan_lifecycle.py:19`)
suggesting deliberate ordering, unverified by scenario. Deliverable: one same-tick hazard-kill +
combat-kill collision scenario. Owner: Combat + World dynamics.

**M3b — Faction diplomacy**: `diplomatic_relations_set` from the autonomous state machine and the
auto-alliance handler, same tick, same pipeline phase. Entry evidence: ordering looks intentional
(`pipeline.py:255-283`), unverified by scenario. Deliverable: one same-pair-same-tick collision
scenario. Owner: Faction.

**M3c — Public reputation**: `SocialComponent.reputation` (`reputation_set`) from `social_memory.py`
and `orchestrator.py`. Entry evidence: two real writer call sites, phase ordering unchecked.
Deliverable: one same-tick-same-entity collision scenario. Owner: Social. (Separate from — and does
not touch — the roadmap's own open *semantic* question of what `public_reputation` means, Owner
Decision List item 3; this is a mechanical dual-writer check only.)

**Finite exit evidence, each**: one scenario result with an explicit classification (including
`BLOCKED_WITH_REASON` where applicable) and citation, recorded back into the roadmap's §3.1 audit
table as its own dated addendum — not a new document, and not bundled with the other two.

**Failure/blocked branch, each**: a `DEFECT_CONFIRMED` result is documented and escalated via a real
ticket, same discipline as M1 — not fixed inside this milestone's own scope unless trivially the
same shape as M1's fix. A `BLOCKED_WITH_REASON` result is reported as exactly that — a named
harness/scenario limitation, not silently reclassified to force a verdict.

### M4a — Composed multi-hop world-side sequence (gated on M1 only)

**Entry evidence**: M1 complete and its exit evidence verified. **Not gated on M2 in any form.**
World-side correctness and product legibility are separate concerns with separate exit evidence, so
a weak, blocked, or pending M2 result never pauses this milestone.

**Deliverable**: repeat the composition probe (roadmap §7.1's second attempt) using ordinary
per-tick aging now that the race is fixed; confirm the heir's own eventual death correctly cascades
succession a second time.

**Finite exit evidence**: a real two-hop composed run (grandparent → parent → grandchild, both hops
through ordinary aging) with identity and chronology preserved across both hops — answers gate
questions 1 (fuller form) and 3 for real, not narrated. This is a **world-side** claim only — it
says nothing about whether the sequence is legible to any observer.

**Relevant Rules/mechanisms/scenarios**: `succession`/`aging_death`, post-M1.

**Failure/blocked branch**: if M1's fix does not actually enable natural two-hop composition (e.g.,
a second, different defect surfaces), report the new blocker with the same precision as §7.1 and
return to Gate A (§4) rather than silently extending this milestone's scope.

### Future follow-ons (not milestones of this wave)

Two named items are left for later waves because this wave cannot commit to a finite exit for
them:

- **Build and test the evidence path M2 chooses**, then run the scripted encounter/non-leakage check
  and a blinded-human inference exercise on it. This is where a single inheritance could first become
  `PENDING`, and later, with real human evidence, player-experienced.
- **Closed-loop-proof groundwork on M4a's composed sequence** (previously drafted as "M4b"). Its
  precondition is a legitimate, encounterable evidence path **sufficient for the specific claim
  being made**. Any domain-appropriate path M2 chooses can satisfy it; a dedicated
  inheritance-provenance record is one option, not a requirement. A pending or negative human
  inference result does not block scoping this item: its purpose is to improve legibility, not to
  wait for legibility to be proven first.

---

## 4. Decision gate

**Gate A (before M4a)** — the only gate within this wave's own milestones, world-side only: M1's
exit evidence is real (natural-aging succession fires correctly through ordinary per-tick aging).
**M2's result is not part of Gate A in any form.**

- **If M1 passes**: M4a proceeds — still only a single additional hop, not a full multi-generation
  arc, and still a world-side claim only.
- **If M1 fails or surfaces a second defect**: return to the roadmap's §3.1 audit process — this may
  indicate the dual-writer-race pattern is broader than the two instances found so far, which would
  be new information for the roadmap itself, not just this plan.

M2 and M3a/M3b/M3c have no gate; each proceeds and completes independently on its own entry
evidence (§3). The future follow-ons' preconditions live with those notes (§3), not here, because
this wave does not commit to them.

---

## 5. World-side and player-side acceptance criteria (kept separate, per the roadmap's §5 evaluation criterion)

**World-side (M1, M3a/b/c, M4a exit evidence)**: the underlying outcome has a coherent,
Rule-conforming causal trace, and the state transition is committed through the authoritative
pipeline with a declared precedence rule — never a stale-assumption commit. This is checked by real
`Kernel.tick_once()` runs and scenario tests, not by code inspection alone. **This track's
milestones (M1, M4a) complete on their own evidence, independent of the player-side track below.**

**Player-side (M2, and later the future follow-ons)**: the eventual question is whether, given only
the legitimate clues a specified observer position can encounter, a reasonable (possibly wrong)
hypothesis can be formed and later revised. Status levels are kept separate:
- **Technical checks** (state, encounter, provenance, non-leakage) are scriptable. They are already
  answered for today's code: `PASS`, `BLOCKED_WITH_REASON`, `ABSENT`, and vacuous, respectively.
- **Human inference** needs a real blinded-human exercise. It is `BLOCKED` while no clue is
  encounterable, `PENDING` once one exists but before the exercise runs, and never established by
  script output.

This wave's player-side exit is M2's design note only.

**A world-side pass does not imply a player-side pass, and no player-side result pauses the
world-side track.** M1/M4a succeeding re-enables composition but says nothing about legibility.

---

## 6. Bounded evidence and regression strategy

Reuses existing infrastructure only — no new registry, no new governance system:
- **Scenario/corpus tests**: the existing `tests/simulation_quality/` and
  `tests/integration/campaigns/` conventions, extended with the natural-aging regression test (M1),
  the composed two-hop scenario (M4a), and one collision scenario per M3 boundary. These are new test
  files, not a new test framework. M2 adds no tests in this wave: there is nothing encounterable to
  test yet.
- **Mechanism registry**: `succession`/`aging_death`'s existing entries get a dated addendum note
  once M1 lands (matching this registry's own established convention of appending dated notes
  rather than rewriting history) — done through whatever ticket implements M1, not this document.
- **Semantic Control Plane**: no new mapping required for M1/M2/M3a-c/M4a (none of the touched
  fields are currently SCP-mapped); if the future follow-on's eventual work touches a mapped Rule,
  record it through the SCP's normal evidence process (roadmap §9's tooling), not a new parallel
  process.
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
  (`SocialComponent.reputation` is M3c, a *mechanical* dual-writer check only — this
  wave does not decide or depend on what `public_reputation` is supposed to mean semantically).
  Stays visible, not blocking.
- **Which candidate trajectory runs first**: not an Owner Decision List item; it is resolved
  (roadmap §7.4, §10). Lineage is the working default.

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
- **M2's result** (the chosen evidence path and its owning domain) updates roadmap §7.2/§7.3. Q2
  stays `BLOCKED` until the path is built; the human-inference level is recorded separately and never
  inferred from scripts.
- **M3a/M3b/M3c's reclassifications** update roadmap §3.1's audit table directly, each converting
  its own `UNKNOWN_WITH_REASON` to its real outcome (including `BLOCKED_WITH_REASON` where that is
  the honest result) — independently, as each completes.
- **M4a's result** updates roadmap §5's evidence table (lineage row) and §7's gate questions 1/3 as
  soon as it completes, regardless of M2's status. **If the future follow-on note is later scoped
  and completed**, its result may re-open the closed-loop-proof question as its own, later,
  separately-scoped item — this plan does not commit to scoping that follow-on work now.
- **No mapping claim from this wave is asserted as `SUPPORTED` in the Semantic Control Plane** unless
  it goes through the SCP's own established validation process (roadmap §9) — this plan's own
  findings are Catalog-level/mechanism-registry-level evidence, not a substitute for that process.

This plan stays `PROPOSED / FOR REVIEW` until the owner explicitly approves it; nothing in it
authorizes starting M1, M2, M3a-c, or M4a without that approval.
