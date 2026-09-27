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
`docs/plans/systemic_world/roadmap.md` (the capability/dependency map) — this document is the
separate, concrete milestone plan the roadmap's §8 and the fourth external review round both ask
for, so the roadmap itself stays a map rather than a milestone transcript. Produced from the actual
feasibility-gate run, composition probe, observer-evidence sketch, and bounded authority audit in
the roadmap's §7/§3.1 (2026-09-27) — every claim below cites that evidence rather than repeating it.

**This is a conditional plan, not a committed backlog.** One milestone (M1) exists only because this
round's investigation surfaced a real, load-bearing defect.

**World correctness and product legibility are separate tracks with separate gates (fifth external
review round correction)**: fixing M1's defect and verifying a composed world-side sequence (M4a)
is worthwhile regardless of what the observer check (M2) finds — a weak or negative M2 result does
not pause M4a. Only the *optional* observer/projection follow-on on the composed sequence (M4b)
depends on M2's own findings. Do not read this plan as one linear M1→M2→M4 chain.

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

## 2. Milestones — dependency order, domain ownership, parallel paths (revised, fifth review round)

```text
M1 (world-substrate/authority) ──> Gate A ──> M4a (world-side composed sequence)
                                                  │
                                                  └──> Gate B (needs M4a + a real
                                                       evidence-production signal,
                                                       NOT gated on M2's own result) ──> M4b
                                                       (optional observer/projection
                                                       follow-on on the composed sequence)

M2 (lineage + observation/delivery) ── independent of M1/M4a/M4b; feeds Gate B only

M3a (combat + world-dynamics)     ── independently schedulable
M3b (faction)                     ── independently schedulable   } all three parallel to
M3c (social)                      ── independently schedulable   } M1, M2, M4a, M4b
```

| Milestone | Domain owner | Depends on | Parallel with |
|---|---|---|---|
| M1 — Fix the `entity.lifecycle.active` dual-writer race | World substrate / engine-core (§3.1 area) | Nothing new | M2, M3a, M3b, M3c |
| M2 — Single-hop observer/evidence check (state→evidence→encounter→inference) | Lineage (social/history) + Observation/delivery | Nothing new (uses today's `verified: observed` mechanisms) | M1, M3a, M3b, M3c, M4a |
| M3a — Resolve entity-death `alive_set` boundary | Combat + World dynamics | Nothing new | M1, M2, M3b, M3c |
| M3b — Resolve faction-diplomacy `diplomatic_relations_set` boundary | Faction | Nothing new | M1, M2, M3a, M3c |
| M3c — Resolve public-reputation `reputation_set` boundary | Social | Nothing new | M1, M2, M3a, M3b |
| M4a — Composed multi-hop world-side sequence | Lineage | M1 only (Gate A) — **not gated on M2** | M2, M3a, M3b, M3c |
| M4b — Optional observer/projection follow-on on the composed sequence | Lineage + Observation/delivery | M4a + a real evidence-production signal (Gate B) | — |

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

### M2 — Single-hop observer/evidence check: state, evidence, encounter, and inference kept separate (revised, fifth review round)

**Entry evidence**: roadmap §7.2 — a design-check sketch already exists (observer position, one
early legitimate clue, one reasonable-but-unprovable hypothesis, two named negative checks). The
underlying mechanisms are `verified: observed` today; this milestone does not wait on M1, and its
result does not gate M4a (only the optional M4b follow-on — see §4 below).

**Deliverable, as four explicit, separately-answerable sub-checks — not one bundled test**:

1. **State** (already established, not re-done here): the tick-0 inheritance produces a real state
   change — the heir's inventory gains the deceased's item. No new work; cited from §7.1.
2. **Evidence/encounter** (scriptable — a real test, not a human exercise): does the specified
   observer's own viewpoint/query mechanics actually let them *access* that changed state at all —
   correct timing (after the transfer, before it's overwritten by something else), correct viewpoint
   scoping (the observer's own position/permissions actually reach this data), and non-leakage of
   the *other*, hidden fields (`cognition.motivation.named_intention`, `strategic.blockers` — §7.2's
   named leak-risk fields must not appear in whatever the observer's query surfaces). This is a
   scripted, deterministic test.
3. **Provenance signal** (already confirmed missing, not re-done here): no producer records "this
   item passed through inheritance" as its own distinguishable fact — cited from §7.2's negative
   check 1. Distinct from #2: #2 asks whether the *existing* state change can be seen at all; this
   asks whether a *dedicated* inheritance-provenance fact exists to make the clue less ambiguous.
4. **Inference** (requires a real blinded-human exercise — **a scripted test cannot substitute for
   this step**): given only what #2 confirms is actually encounterable, can an observer who does not
   already know the answer form a reasonable, clue-supported hypothesis? This needs an actual human
   reviewer standing in for the player, blinded to the ground truth, not a script asserting what a
   "reasonable" hypothesis would be.

**Finite exit evidence**: #1 and #3 already answered (cited, no new work). #2 answered from a real
scripted test — pass/fail on timing, viewpoint access, and non-leakage, each individually. #4
answered from a real blinded-human exercise, **or left explicitly `pending` if no such exercise is
run** — `PLAYER-EXPERIENCED` is never marked resolved on script output alone (roadmap §5's own
evidence-level distinction).

**Relevant Rules/mechanisms/scenarios**: `succession`/`aging_death`; the epistemic principle (roadmap
§2); `KnowledgeModelService`'s existing hidden-world-truth-not-injected invariant as the negative
constraint for sub-check #2.

**Failure/blocked branch**: if #2's scripted test finds a real leak or a viewpoint-access failure,
that is a defect to document and escalate (same discipline as M1/M3a-c), not a reason to skip #4. If
#4 is never run, report `PLAYER-EXPERIENCED: pending` plainly — this is not a failure of the
milestone, just an honest evidence-level statement, and it does **not** pause M4a (§4 below).

### M3a/M3b/M3c — Resolve the 3 `UNKNOWN_WITH_REASON` audit boundaries (independently schedulable, revised fifth review round)

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

**Entry evidence**: M1 complete and its exit evidence verified. **Not gated on M2 in any form** —
world-side correctness and product legibility are separate concerns with separate exit evidence
(fifth review round correction); a weak or `pending` M2 result never pauses this milestone.

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

### M4b — Optional observer/projection follow-on on the composed sequence (gated on M4a + a real evidence-production signal)

**Entry evidence**: M4a complete, **and** a real inheritance-provenance signal exists (M2's
sub-check #3, or a follow-up item if M2 found it insufficient) — **not gated on M2's inference
sub-check #4 passing**; a `pending` inference result does not block attempting this milestone, since
this milestone exists to make legibility better, not to wait for it to already be proven.

**Deliverable**: begin — but do not complete within this wave — the groundwork for a closed-loop
proof (a later decision/opportunity producing a durable, player-observable outcome, per roadmap
§5's evidence ladder's final rung), building on the now-composed two-hop sequence.

**Finite exit evidence**: explicitly out of this wave's completion scope (§1) — this milestone
produces groundwork/scoping only, not a finished closed-loop proof.

**Failure/blocked branch**: if no evidence-production signal exists by the time M4a completes, this
milestone stays unscheduled — report it as a real, named prerequisite gap, not silently skipped.

---

## 4. Decision gates (revised, fifth review round — world-side and player-side kept separate)

**Gate A (before M4a)** — world-side only: M1's exit evidence is real (natural-aging succession
fires correctly through ordinary per-tick aging). **M2's result is not part of Gate A in any form.**

- **If M1 passes**: M4a proceeds — still only a single additional hop, not a full multi-generation
  arc, and still a world-side claim only.
- **If M1 fails or surfaces a second defect**: return to the roadmap's §3.1 audit process — this may
  indicate the dual-writer-race pattern is broader than the two instances found so far, which would
  be new information for the roadmap itself, not just this plan.

**Gate B (before M4b)** — the optional follow-on only: M4a complete, **and** a real
inheritance-provenance signal exists (M2 sub-check #3). M2's inference sub-check #4 (the blinded-
human exercise) is **not** part of Gate B either — a `pending` inference result does not block
attempting M4b, since M4b's own purpose is improving legibility, not confirming it first.

- **If Gate B's provenance condition isn't met**: M4b stays unscheduled, reported as a named
  prerequisite gap (M4b's own failure/blocked branch, §3) — this does not affect M4a, M3a/b/c, or M1
  in any way; they proceed and complete independently of Gate B.

---

## 5. World-side and player-side acceptance criteria (kept separate, per the roadmap's §5 evaluation criterion)

**World-side (M1, M3a/b/c, M4a exit evidence)**: the underlying outcome has a coherent,
Rule-conforming causal trace, and the state transition is committed through the authoritative
pipeline with a declared precedence rule — never a stale-assumption commit. This is checked by real
`Kernel.tick_once()` runs and scenario tests, not by code inspection alone. **This track's
milestones (M1, M4a) complete on their own evidence, independent of the player-side track below.**

**Player-side (M2's four sub-checks, and M4b)**: given only the legitimate clues a specified
observer position can encounter, can a reasonable (possibly wrong) hypothesis be formed, and would a
later clue be able to revise it? Sub-checks #1-#3 (state, evidence/encounter, provenance) are
scriptable; sub-check #4 (inference) requires a real blinded-human exercise and stays `pending` if
unrun. **A world-side pass does not imply a player-side pass, and a pending/weak player-side result
does not block or pause the world-side track** — M1/M4a succeeding only re-enables composition; it
says nothing about whether that composition is legible to an observer, which stays M2/M4b's own
separate, non-blocking question.

---

## 6. Bounded evidence and regression strategy

Reuses existing infrastructure only — no new registry, no new governance system:
- **Scenario/corpus tests**: the existing `tests/simulation_quality/` and
  `tests/integration/campaigns/` conventions, extended with the natural-aging regression test (M1)
  and the four observer/evidence sub-check tests (M2, sub-checks #1-#3 scripted; #4 a real human
  exercise if run) — new test files, not a new test framework.
- **Mechanism registry**: `succession`/`aging_death`'s existing entries get a dated addendum note
  once M1 lands (matching this registry's own established convention of appending dated notes
  rather than rewriting history) — done through whatever ticket implements M1, not this document.
- **Semantic Control Plane**: no new mapping required for M1/M2/M3a-c (none of the touched fields
  are currently SCP-mapped); if M4a/M4b's eventual work touches a mapped Rule, record it through the
  SCP's normal evidence process (roadmap §9's tooling), not a new parallel process.
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
- **M2's result** updates roadmap §7.3's gate-question table (Q2's status) — each of the four
  sub-checks recorded individually, with sub-check #4 recorded as `pending` if unrun rather than
  silently omitted.
- **M3a/M3b/M3c's reclassifications** update roadmap §3.1's audit table directly, each converting
  its own `UNKNOWN_WITH_REASON` to its real outcome (including `BLOCKED_WITH_REASON` where that is
  the honest result) — independently, as each completes.
- **M4a's result** updates roadmap §5's evidence table (lineage row) and §7's gate questions 1/3 as
  soon as it completes, regardless of M4b/M2's status. **M4b's result, if scheduled**, may re-open
  the closed-loop-proof question as its own, later, separately-scoped item — this plan does not
  commit to scoping that follow-on work now.
- **No mapping claim from this wave is asserted as `SUPPORTED` in the Semantic Control Plane** unless
  it goes through the SCP's own established validation process (roadmap §9) — this plan's own
  findings are Catalog-level/mechanism-registry-level evidence, not a substitute for that process.

This plan stays `PROPOSED / FOR REVIEW` until the owner explicitly approves it; nothing in it
authorizes starting M1, M2, M3a-c, M4a, or M4b without that approval.
