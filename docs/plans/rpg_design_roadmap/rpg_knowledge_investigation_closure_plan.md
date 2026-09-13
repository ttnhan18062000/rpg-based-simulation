---
status: active
layer: strategy
authority: P1
audience: agent
tags: [cognition, self-model, content, architecture]
---

# Plan — Knowledge & Investigation Closure

**Status, scoped 2026-09-13.** This plan **sequences three already-open tickets** covering the
knowledge / information-seeking layer, adds one newly-found defect, and records the design decision
each needs. It does not replace or supersede any existing ticket — see §6 for why that warning is
at the top of this document.

**Relationship to Epic 4.2.** `docs/plans/long_term_development_roadmap.md` Epic 4.2 (*Active
Information-Seeking / Belief Economy*) describes this feature as unbuilt. That is inaccurate and
the epic should not be picked up as written. Most of its declared scope exists in code with real
tests (`tests/unit/cognition/test_information_seeking.py`, ~1200 lines, covering paid transactions,
lead kinds, and provider reliability). What remains is not construction — it is **connection, and a
disposition decision about whether to connect it at all**. Epic 4.2's *acceptance signal* remains
the right target and is reused verbatim in §4.

---

## 1 · What the feature is supposed to be

In gameplay terms, stripped of implementation:

> A hero needs moon-resin and has no idea where to find it. She knows she doesn't know. So she
> walks into town, finds the guild master, and pays for the answer. He tells her — but he heard it
> second-hand two seasons ago. She travels three days to the ridge he named and finds the vein
> worked out. Now she knows two things: where the resin isn't, and that the guild master's word is
> worth less than she paid for it. Next time she asks the blacksmith instead.

Four beats: **recognising a gap**, **paying someone for an answer**, **acting on what you were
told**, and **learning you were told wrong**. Each is a separate mechanism, and they are in
noticeably different states of completion.

---

## 2 · What actually exists today

Verified against `origin/main` on 2026-09-13 by reading call sites and flag defaults.

| Beat | State | Evidence |
|---|---|---|
| Recognise a gap | **Live** | `UnknownFact`; `ASK_INFORMATION` route family scored and selected (`src/domains/adventure/generator.py:116`) |
| Ask, via the Adventure domain | **Trace lies; charge dormant — §3.1** | `action_intent.py:145-151`: records `execution_result="SUCCESS"` for a no-op; the `cost_gold` deduction never fires (never populated upstream) |
| Ask, via the Information domain | **Built, flag-gated OFF** | `action_intent.py:153+` closes the loop correctly, but `ENABLE_INFORMATION_INTENT_EXECUTION` is `FeatureMode.OFF` (`feature_flags.py:42`) and no corpus profile turns it on |
| Providers answer queries | **Inert, two distinct ways — §3.2** | `InformationProviderState` never constructed; and `Guide`/`Blacksmith`/`Guild` provider classes have zero production callers |
| Assimilate an answer | **Built, never reached** | `InformationAssimilationService.assimilate()` measured firing **zero times** in a real 500-tick run |
| Learn a lead was wrong | **Built, unfed** | `LeadService.evaluate_lead_outcome()` exists; `entity.strategic.leads` measured empty for every entity at every tick |

**The honest summary is that the layer produces nothing in a real run.** Facts are never written;
leads are never created. Every mechanism above the "ask" layer is real, tested, and unreachable.
This is the same "built but not observable" shape the dormant-mechanism arc has been unpicking, at
the scale of a whole subsystem rather than a single mechanism.

---

## 3 · The defects, in dependency order

### 3.1 · Adventure-originated ASK_INFORMATION records a lying trace; the gold charge is dormant, not active — NEW

**Corrected 2026-09-13, after this section's original claim proved wrong under implementation.**
The original text here said the handler "deducts `cost_gold`... the entity pays for information
and receives none... a live gold sink that reads as commerce in economy aggregates" and reported
that to the user as an active defect. **That was wrong.** `intent.payload.get("cost_gold", 0)`
reads a key that is never populated anywhere in the real call chain:
`ObjectiveIntentResolver.resolve()` has exactly one real call site (`src/engine/tactical.py:348`),
which passes `payload={"position": target_pos} if target_pos else {}` — never `cost_gold` — and
`ObjectiveState` (`src/core/strategic.py:303-310`) has no field to carry a cost even if one were
wanted. The deduction is a **dormant shape**, not a currently-active charge: `gold_deduct` always
evaluates to `0` in production today, so `InventoryUpdate(gold_delta=-0)` was a real no-op update,
not a real economic sink. This was concluded from the handler's own code shape without checking
whether anything upstream ever populates the key it reads — see §6 for why that error is recorded
there too.

**What is real and live is the trace.** `src/engine/intent/action_intent.py:145-151` (pre-fix)
emitted an `IntentTrace` with `execution_result="SUCCESS"` unconditionally, before either branch of
the handler ran — so every real Adventure-originated `ASK_INFORMATION` intent (confirmed real,
scored, and selected traffic — see the table row above) recorded a trace asserting success for a
branch that queried nothing, consulted no provider, and assimilated no fact. That is the actual
live defect this section describes: an instrumentation record lying about what happened, not an
active economic exploit.

This was a **deliberate deferral** — the handler's own comment required the branch stay
"byte-identical to pre-fix code" — taken while closing the Information-domain branch beside it.
Defensible then; it is the class of deferral this repo repeatedly loses track of.

**Not covered by any existing ticket.** The open inert-layer ticket enumerates six gaps (two
fact-write paths, four lead-creation paths); this is none of them — it is the intent handler's own
lying trace and dormant charge shape. **This is the one new ticket this plan adds.**

It is also the only item here that could proceed without a disposition decision first: fixing a
lying trace, and removing a dormant charge that would otherwise silently activate if a future
caller ever populates `cost_gold`, are both correct regardless of whether the wider layer ever gets
connected.

**Closed**: `TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING` — trace now
records an honest result for the no-op branch; the dormant gold-deduction shape was removed
outright.

### 3.2 · The provider side is inert in two distinct ways

Owned by `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (open, standard).

That ticket's analysis is more thorough than anything this plan would add, and should be read as
the authority: it enumerates **four lead-creation sites, each unreachable for a different reason**
— dead code (`GuildIntelSystem.update()`), flag-gated off (`GuildAction.visit()`), update-only and
structurally unable to seed from empty (the belief-confirmation loop), and a structurally
unreachable type (`PaidInformationTransactionSystem.enforce()` requiring an
`InformationProviderState` that nothing constructs). Collapsing those into one "it's gated"
explanation would destroy the useful part.

**One addition for that ticket, found while scoping this plan:** `src/world/providers/information.py`
defines `GuideInformationProvider`, `BlacksmithInformationProvider`, and
`GuildInformationProvider`, each producing `KnowledgeFact`s and `suggested_leads`. **None has any
production caller** — the only non-test references are `src/worldbuilding/compiler.py` importing
the *types* to shape authored seed data. This is a **different type** from the
`InformationProviderState` in that ticket's gap #4, and a fifth distinct instance of the same
shape. Worth appending there rather than filing separately.

**The disposition decision this ticket already asks for is the real fork**, and it is mine to
answer rather than the implementer's:

- **(a) Connect the provider path.** Makes reliability, `knowledge_age`, and lead quality real,
  which is what gives "being told wrong" something to bite on. Substantial work across several of
  the six gaps.
- **(b) Document as intentional and build nothing.** Cheapest and honest, but Epic 4.2's
  acceptance signal becomes unreachable by design, and the layer's considerable existing test
  coverage permanently describes behaviour that never occurs.

**Recommendation: (a), but scoped to one path rather than all six.** The declared-intent test this
arc has used throughout supports building: provider reliability is declared as a gameplay concept
in the dataclass, the seed schema, and Epic 4.2's scope. But six gaps is not one ticket, and
fixing all four lead sites would be inventing scope. The narrow version is to connect the single
path that already has the most machinery behind it and verify one real lead reaches one real
entity in a real run — then decide whether the remaining gaps are worth anything.

**This decision blocks 3.3 and 3.4 and should be made before either starts.**

### 3.3 · Capability estimates never receive enemy or region data

Owned by `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (open). Independently
verified during this scoping; that ticket's findings match mine exactly — same fields, same three
call sites, same conclusion, including the stronger result that `travel_regions` has **zero
production construction sites**, so the travel-safety branch at `capability_estimate.py:152-171`
has never executed outside tests. **Nothing to add; no new ticket.**

Consequence worth stating in gameplay terms: every entity assesses every enemy identically, from a
hardcoded `_ENEMY_DANGER` constant, regardless of what it has learned. The belief-driven branch is
dead.

This is the payoff item — until it lands, knowledge can be acquired but cannot change behaviour,
which is what makes the rest of the layer worth having. **It is therefore downstream of 3.2's
decision**: if the disposition is (b), this ticket has no facts to read and should be re-scoped or
closed alongside it.

### 3.4 · Campaign-mode actor-ID mismatch

Owned by `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open). Its
analysis was re-verified, not merely trusted, and it stands.

Its own central warning is why it sequences **last**: the obvious fix compiles, passes a naive
test, and silently delivers seeded facts to the wrong entity. Campaign mode spawns via
`WorldEntitySpawner`, which never sets `properties["population_id"]`, so `WorldCompiler`'s
`target_population_id → actor_id` resolution is meaningless against the campaign roster. Its
worked example — `actor_id=9`, intended for a frontier guard, resolving to a goblin raider — is
real.

Last is deliberate: with the items above resolved there is an observable knowledge path to verify
against, so "the right entity learned it" becomes checkable rather than asserted.

---

## 4 · Acceptance signal

Inherited verbatim from Epic 4.2, and honest only if disposition (a) is chosen:

> In a 600-tick run, at least one HERO entity transitions through:
> `information_need_identified → information_seeking_project → information_transaction →
> lead_received → route_scored_with_lead → belief_contradiction (if lead was stale) →
> information_seeking_retry`.

Two additions, both from lessons already paid for in this arc:

1. **Reachability, not just passing.** Observed in a real run of an existing corpus world, not in a
   fixture built to produce it. A test that constructs the preconditions proves the code works; it
   does not prove the feature happens.
2. **Correct delivery, not just non-empty delivery.** Per 3.4, any assertion about facts arriving
   must assert *which entity* received them. "The field is populated" is precisely the false
   positive that ticket exists to prevent.

Under disposition (b), this signal is formally unreachable and should be struck from Epic 4.2
rather than left standing as an aspiration.

---

## 5 · Tickets governed by this plan

| # | Ticket | State | Gate |
|---|---|---|---|
| 1 | `TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING` | **done** | none |
| 2 | `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` | open | §3.2 disposition decision |
| 3 | `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` | open | blocked on #2 |
| 4 | `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` | open | blocked on #2 |

Exactly one new ticket. Three existing tickets are sequenced and gated, **not** superseded,
reworded, or closed.

**Not in this initiative:**
`TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION` (independent disposition
question) and `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`
(cooperation, separately tracked).

---

## 6 · Correction: this plan's first draft made a false claim from a stale worktree

The first draft of this document asserted in this section that two ticket IDs "exist nowhere in the
repository" and proposed refiling them under new IDs. **That was wrong.** Both
`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` and
`TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` are real, committed, and open on
`main` (PR #174, commit `24920f912`). The peer implementer caught it before anything was filed.

**Root cause, worth recording because it generalises:** the existence check was a repo-wide grep run
from a git worktree whose branch predated PR #174 by ~20 commits. The grep was correct about its
own working tree and wrong about the repository. *Any "does X exist" check run from a worktree is
only valid for that worktree's branch* — for ticket existence, provenance, or "has this already
been filed" questions, the check must be `git ls-tree origin/main` or equivalent, after a fetch.

Two consequences beyond the near-miss:

1. **Acting on that claim would have destroyed evidence.** The two existing tickets are better
   researched than the replacements proposed for them — the inert-layer ticket enumerates four
   lead-creation gaps with four *distinct* root causes, which a rewrite would have collapsed. The
   proposed correction was worse than what it corrected.
2. **A second claim from the same stale read was also wrong.** The first draft's §2 recorded the
   Information-domain ask→answer loop as "live, loop closed." It is built and correct but gated
   `ENABLE_INFORMATION_INTENT_EXECUTION = FeatureMode.OFF`, which no corpus profile overrides. The
   corrected table above says so.

This is the same failure this arc keeps finding, applied to process rather than code: **a
confident claim about what exists, unverified against the authoritative source.** It belongs in
the record next to the mechanisms that were documented as running while inert.

**Second instance, same author, same document, 2026-09-13.** §3.1's original text claimed the
Adventure-originated `ASK_INFORMATION` handler "deducts `cost_gold`... the entity pays for
information and receives none... a live gold sink that reads as commerce in economy aggregates,"
and that claim was reported to the user as an active defect. It was wrong: the deduction never
fires in production, because nothing upstream of the handler ever populates the `cost_gold` key it
reads (`ObjectiveIntentResolver`'s one real call site passes only `position`;
`ObjectiveState` has no cost field at all). The implementer traced the actual call path before
building anything and found this; §3.1 above is corrected to state it.

**This is not the same root cause as the worktree error above, but it is the same *class* of
error**: a confident claim about a mechanism's current, active behavior, drawn from reading the
mechanism's own code, without checking whether the path that would actually exercise it is ever
populated at runtime. Existence-of-code-shape was read as evidence of behavior. That is precisely
the reachability-versus-existence distinction this whole document argues for elsewhere (§2's
table, the "built but not observable" framing) — committed here, by the same author, in the
document making that argument. Recorded with the error visible rather than tidied away, for the
same reason §6 above is: a findings document is more useful when its own failures are legible than
when they're quietly corrected out of the record.

---

## 7 · Related

- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md` — the parent pattern; this
  is another instance of its "built but not observable" finding.
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — why a mechanism that
  cannot execute in a real run has not delivered its feature, regardless of test coverage. §6 here
  is a process-level instance of the same.
- `docs/plans/deferred_tuning_decisions_register.md` — §3.1's deferral belongs to the class this
  register exists to prevent losing.
- `docs/plans/long_term_development_roadmap.md` Epic 4.2 — scope section inaccurate; acceptance
  signal retained, conditional on §3.2's disposition.
- `docs/simulation/belief_and_detour_contract.md` — carries framing the inert-layer ticket may need
  to amend further once disposition is reached.
- `docs/mechanics/04_strategic_cognition.md` — authoritative Leads/Knowledge definitions.
