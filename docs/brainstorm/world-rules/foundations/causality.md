---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Causality

**Purpose/scope.** How causes and consequences are allowed to relate to each other across the
world, and how that relation is distinguished from mere correlation, coincidence, or a fabricated
narrative link. This family operationalises `simulation-rule-taxonomy-evaluation-direction.md`'s
anti-correlation principle and outcome-neutrality principle as world-semantic Rules, not only as
evaluation-side scoring rules — a domain author needs these to be true of the *world*, independent
of whether SimQ happens to be checking for them on any given run.

**Status.** Foundational Batch 01, first draft.

---

## CAUSE-01 — A consequence requires a real causal path

> A durable state change should trace to a real producer: an event, decision, rule application, or
> prior state — not to nothing, and not to a narrative label alone.

**Disposition: ACCEPT.** This is the world-semantic root the other Causality rules refine; it is
deliberately broad and is expected to be sharpened by CAUSE-02 through CAUSE-05, not by itself.

**Repository evidence: ACCEPT, PARTIAL.** Architecturally encouraged, not runtime-enforced: the
typed-`Update`/`Patch` pipeline gives every commit a real producing call site (so a change can
always be traced in code), but nothing at runtime asserts that the *semantic* reason attached to
that call is itself a real precondition rather than an arbitrary label — that gap is exactly why
CAUSE-04 exists as its own separate rule below rather than being folded into this one.

**Scenarios:** [FND-S01](../scenarios/foundational-batch-01.md#fnd-s01), [FND-S10](../scenarios/foundational-batch-01.md#fnd-s10), [FND-S18](../scenarios/foundational-batch-01.md#fnd-s18), [FND-S19](../scenarios/foundational-batch-01.md#fnd-s19) (adversarial expansion — a false belief is a real cause of a real action; a held-but-inert belief is legitimately not a cause of anything).

---

## CAUSE-02 — Causal chains may cross domains without breaking

> A cause in one domain may produce a consequence in another, and that consequence may itself
> become a cause further downstream. The chain does not need to stay inside one domain to be valid.

**Disposition: ACCEPT unchanged.** The worked probe chain (`drought → resource scarcity →
migration → abandoned settlement → ecological takeover`) is kept as given — it is a good probe
precisely because it is only partially real yet in this repository.

**Repository evidence, per link:**
- `drought → resource scarcity`: SUPPORTED — world-evolution drought/climate pressure is a real
  input to resource-node depletion.
- `resource scarcity → migration`: SUPPORTED — scarcity signals feed migration-decision weighting
  in the strategic-cognition layer.
- `migration → abandoned settlement`: MISSING — no settlement-occupancy-loss consequence exists
  yet (matches the Places-domain gap already recorded in `core_rpg_design_direction.md`'s target
  map and in `identity.md`'s ID-03 open item on camp→settlement→ruin).
- `abandoned settlement → ecological takeover`: MISSING, for the same reason — there is nothing
  upstream of it to react to yet.

**Scenarios:** [FND-S10](../scenarios/foundational-batch-01.md#fnd-s10) (traces this exact chain
and is explicitly scored as *partially covered*, stopping where repository support stops).

---

## CAUSE-03 — Correlation is not causal connectivity

> Two events or states being statistically associated, temporally adjacent, or narratively
> convenient to link does not make one the cause of the other. A causal claim requires a declared
> link, a producer-side consequence, a consumer-side reaction, and a traceable causal or
> provenance relation.

**Disposition: ACCEPT strongly, unchanged.** This is the Causality-family restatement, at the
world-semantic level, of the anti-correlation principle already adopted in
`simulation-rule-taxonomy-evaluation-direction.md` — it is deliberately the same standard, not a
parallel or looser one, so that a world author and an evaluator are held to identical proof
requirements for "this caused that."

**Repository evidence: SUPPORTED as a standard**, precisely because nothing in the repository is
allowed to claim causal connectivity through correlation alone — the same four-part test
(declared link / producer consequence / consumer reaction / causal-or-provenance relation) is what
this batch has applied throughout, e.g. in distinguishing the SUPPORTED `injury → impaired
capability` link (all four parts present) from the MISSING `impaired capability → economic loss`
link (no producer-side consequence exists to even evaluate).

**Scenarios:** [FND-S11](../scenarios/foundational-batch-01.md#fnd-s11) (the required
correlated-but-not-causal counter-scenario).

---

## CAUSE-04 — Preconditions and capability gates must be real, not narrative

> If a rule or narrative claims an actor could or could not do something because of a
> precondition, that precondition must be checked against real state, not asserted for flavor.

**Disposition: ACCEPT, PARTIAL evidence — and this is the rule this batch expects to be hardest
to satisfy going forward, not easiest.**

**Repository evidence: PARTIAL, matching a gap `simulation-rule-taxonomy-evaluation-direction.md`
already identified independently.** There is no general-purpose capability/precondition detector
in the codebase — individual systems each check their own specific preconditions locally (e.g.
combat checks HP/readiness directly), but there is no shared mechanism that would catch a
narrative or content-authored claim asserting a precondition that was never actually checked
against state. This is a real, named gap, not a design decision to leave something incomplete —
carried forward below.

**Scenarios:** [FND-S01](../scenarios/foundational-batch-01.md#fnd-s01).

---

## CAUSE-05 — Causal history must remain traceable, within a declared reach

> A causal chain should be reconstructable after the fact, within whatever reach (tick, entity,
> region, campaign, etc.) the system declares it supports. A system is not required to remember
> everything forever, but what it claims to remember must be real and must not silently degrade
> into fabrication.

**Disposition: ACCEPT, PARTIAL evidence.** The reach qualifier is doing real work here — it is
what keeps this rule from silently becoming "everything must be remembered forever."

**Repository evidence: PARTIAL.** Chronicle/causal-memory mechanisms genuinely exist and genuinely
work, but their declared reach is Campaign-mode only — outside Campaign mode, the same causal
chains occur but are not retained at the same fidelity. That's a legitimate declared-reach
boundary, not a violation of this rule, provided the boundary itself stays honestly declared
rather than quietly assumed to hold everywhere.

**Scenarios:** [FND-S04](../scenarios/foundational-batch-01.md#fnd-s04).

---

## CAUSE-06 — Compression and summarization must not fabricate causal links

> When history, memory, or chronicles compress detail over time, the compression may drop detail
> but must not invent a causal relation that wasn't there, and must not silently upgrade a
> correlation into a stated cause. Separately, a fact's *significance* — how prominent it is in
> the world's living memory — may legitimately diminish over time even while the fact itself
> remains fully retained and unfabricated. Fading significance is not erasure, not fabrication,
> and not a violation of ID-05/OWN-06; it is a distinct, legitimate kind of change this rule must
> not be read as forbidding.

**Disposition: ACCEPT, partial-MOVE, refined 2026-09-21 per adversarial scenario expansion
(`tmp/world-catalog-expand-scenario-and-review-layer-ext-ai.md`).** The no-fabrication constraint
stays in this family, at this level of generality, because it is a direct restatement of CAUSE-03
applied specifically to the compression case. The detailed design of *how* compression tiers
should work (what gets dropped first, how far back full fidelity is kept, etc.) is explicitly
deferred to a future History/Provenance foundational family — this batch is not the place to
design that mechanism, only to assert the constraint it must obey whenever it is designed. The
added sentence is a light refinement, not a new idea: FND-S21 (a dead entity's historical
relevance should be able to legitimately fade) showed that ID-05 ("destruction doesn't erase
history") and OWN-06 ("historical reference doesn't imply present ownership") could otherwise be
over-read by a future domain author as requiring every recorded fact to stay at constant
significance forever. Stating the distinction here — fading weight vs. erasure/fabrication —
closes that over-broad reading without designing the fading mechanism itself, which still belongs
to the deferred History/Provenance family.

**Repository evidence:** not separately evaluated this batch for compression-tier design — no
such mechanism exists yet to check against, recorded as MISSING by absence rather than by failure.
For the added sentence specifically: checked directly, no importance-decay mechanism exists
anywhere in `src/domains/chronicle/` or `src/domains/fame/legend.py` either — every recorded fact
stays at constant significance once created, within whatever reach CAUSE-05 already declares.
This is MISSING in the same sense (no mechanism yet), not a violation of the refined rule, which
only asserts that such a mechanism *would be* legitimate if built.

**Scenarios:** [FND-S20](../scenarios/foundational-batch-01.md#fnd-s20),
[FND-S21](../scenarios/foundational-batch-01.md#fnd-s21) (the fading-significance counter that
prompted this refinement).

---

## CAUSE-07 — World outcomes carry no inherent polarity

> Collapse, stability, victory, extinction, and every other world-level outcome are not, by
> themselves, good or bad results. Only the causal validity of the process that produced the
> outcome has standing to be evaluated.

**Disposition: ACCEPT strongly, unchanged.** This is the Causality-family restatement of the
outcome-neutrality principle already adopted in `simulation-rule-taxonomy-evaluation-direction.md`
— included here explicitly as a *world*-semantic rule (what causal validity means for the world
itself) rather than only as a SimQ scoring rule (what evidence a grader collects), matching the
evaluation/governance boundary this session already drew: this rule does not redefine SimQ, it
gives SimQ's existing stance a citable home in the world's own semantics.

**Repository evidence:** not independently re-checked this batch — this is a restatement of a
principle already verified in the evaluation-direction document's own review; re-verifying it here
would duplicate that work rather than add new evidence.

**Scenarios:** [FND-S12](../scenarios/foundational-batch-01.md#fnd-s12) (a world-state collapse
scenario, scored on causal validity of the chain that produced it, not on collapse itself).

---

## Cross-domain links recorded here

- CAUSE-02 → Ecology/population, World evolution, Places/settlements (the drought chain)
- CAUSE-04 → Agency/motivation/decision, Capability/progression (precondition-gated actions)
- CAUSE-05, CAUSE-06 → History/significance (a future foundational family, not yet started)
- CAUSE-07 → Evaluation (SimQ) — explicitly a shared-standard link, not a redefinition either way

## Open questions carried forward

1. CAUSE-04's gap (no general capability/precondition detector) is the most load-bearing MISSING
   finding in this whole batch — it affects every future domain that gates an action on a
   precondition. Flagged for the design-order's own reassessment method
   (`simulation-rule-world-law-design-preparation.md` §4.5) rather than solved here.
2. CAUSE-06 defers real design work to a future History/Provenance foundational family; this batch
   only asserts the constraint that family must satisfy, and that family does not yet exist in the
   world-rule design order as a numbered item — noted so it isn't silently forgotten.
3. CAUSE-06's fading-significance sentence (added 2026-09-21) states that fading is legitimate
   but does not design how it would work — mechanism design (what fades first, at what rate, does
   it differ by domain) stays with the same deferred History/Provenance family as the rest of
   CAUSE-06, not resolved here.
