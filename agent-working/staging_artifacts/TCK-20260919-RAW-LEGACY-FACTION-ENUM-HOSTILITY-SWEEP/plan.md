---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP
artifact_type: plan
tags: [combat, faction, root-cause]
---

# Plan — raw legacy-`Faction`-enum hostility sweep

Read `investigation.md` first for the verified inventory and the Group A/B/C ranking. This plan does not
restate them.

## Step 0 — the shared helper, and the dependency on item 1

Every fix below needs the same catalog test. **There must be exactly one**, or this ticket reproduces at
larger scale the defect it exists to close.

`LegalityServiceV2._is_engagement_hostile` (`src/engine/legality.py:516-544`) is the reference
implementation and is currently a **private static on a service class** — eight callers across
`src/engine/`, `src/systems/`, `src/domains/` and `src/ai/` cannot all reasonably reach a private member
of `LegalityServiceV2`.

**Lift it to a shared home: `src/content_semantics/faction.py`**, which already owns
`get_faction_semantics_service` and `get_faction_id_str`. Keep `_is_engagement_hostile` as a thin
delegating wrapper so `legality.py`'s existing behaviour and tests are untouched.

**Sequencing:** work-order item 1
(`TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND`) runs first and already needs
this same helper for `scorers.py:108`. **Whichever lands first creates it; the second consumes it.** If
item 1 has already landed, confirm where it put the helper and use that — do not create a second one.
Record in Implementation Notes which ticket established it.

**The signature must take the real context, not a hardcoded one.** Build `RelationContext` with the
caller's actual distance and `combat_engaged` state. The 34-97% disagreement figures were measured under
a permissive `distance=1.0` context and are floors; a helper that hardcodes it would bake that in.

## Steps 1-3 — one group per staged commit, measured between

This ticket's own Request Summary says **"triage and prioritize, do not fix all at once."** It is also
project policy that follow-ups ship in the same batch rather than being parked. The resolution: **one
ticket, one branch, three ordered commits, each measured before the next** — nothing is parked, and no
group's effect is attributed to another's.

### Step 1 — Group A, the durable-state sites

**1a. `combat.py:507`** — replace `attacker.identity.faction == other_ent.identity.faction` with the
negation of the shared helper. Watch the direction: the current code *skips* on same-bucket; the fix
must skip when the catalog says **not hostile**. Getting this inverted turns splash into friendly fire
on everything, so T1 in the test plan asserts both directions.

**1b. `intake.py:30`** — `danger` concern only for a catalog-hostile neighbour.

**1c. `intake.py:44`** — `trauma_dead_ally` only for a catalog-**ally**. Note this site is the inverse
direction (same-bucket, not hostility), so it needs an "allied" test, not `not hostile` —
**`NEUTRAL` is neither**, and conflating them would make every dead neutral an ally. Decide and record
which predicate you use.

**1d. Decide and record: does `trauma_dead_ally`'s record need changing too?** The id literal
`f"trauma_dead_ally_{neighbor.id}"` encodes the claim "ally" in a durable identifier, which the Durable
State Rule forbids. Fixing the predicate stops *new* wrong records; it does not address meaning living in
an id. **State a disposition either way** — fix it here, or file a follow-up — but do not leave it
unremarked. Changing the id literal will move canonical hashes; see "Fixtures".

### Step 2 — Group B

**`legality.py:451`, `has_hostile_at`** — adopt the shape from `:265-269` in the same file: prefer
`is_hostile_compat`, fall back to the raw enum **only** when clean identity data is unavailable. That
fallback is deliberate and must be preserved, not removed.

### Step 3 — Group C, in one pass

`cognition.py:44` and `:117`, `cooperation/providers.py:50`, `intelligence.py:149` and `:439`.

**Before fixing C3/C4, confirm whether their outputs are durable** (cooperation contracts; leads). The
investigation ranked them on reading, not measurement. **If either writes durable state, stop and
promote it to Group A** with its own measurement — do not quietly fix it as a transient.

`cognition.py:44` is the folded-in `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM`. Its
recorded "0.5% real impact" was measured for a different consumer. **Re-measure; do not inherit it.**
`CombatEngageScorer` calls `filter_saliency` on the line directly above its own hostility test, so this
site shapes the candidate set item 1's fix acts on.

## Measurement, per group — the honest instrument

For each group, before and after, on `crowded_frontier` and `frontier_living_world`, seed 42, 2000
ticks, real `Kernel.tick_once()`, **`LocalSequentialExecutor()` explicitly**:

1. How often the site's predicate is evaluated at all (the frequency nobody has measured).
2. Of those, how many flip answer, **split by direction** — over-detection corrected vs under-detection
   corrected. These have opposite gameplay meanings and a single "N changed" number hides that.
3. The group's own durable consequence: Group A1 → splash victims, deaths; A2 → `danger` and
   `trauma_dead_ally` concern counts per 1000 ticks; B → flanking-bonus applications; C → re-measured
   saliency impact.

**Measure Group A1 after item 1 has landed**, or the baseline comes from a world where decision-driven
combat barely happens (measured: 2 and 3 decision-path attacks per 2000 ticks).

**Expect under-detection to dominate the corpus effect.** All three monster factions share
`MONSTER_HORDE`, so the headline behavioural change is likely that monster-vs-monster conflict becomes
possible at all. If the measurement shows otherwise, that is a finding, not an error — report it.

## Prohibitions

- Do **not** touch `scorers.py:108`. Item 1's, and it must land with item 1's dispatch fix.
- Do **not** "fix" `legality.py:269` — a deliberate clean-data fallback — or `:524`, a docstring.
- Do **not** create a second hostility helper. One definition, see Step 0.
- Do **not** remove `:451`'s fallback-when-unclean structure; adopt it.
- Do **not** silently regenerate a moved recorded-hash fixture.
- Do **not** touch the benign sites the ticket already recorded as checked (`environment.py:83`,
  `certification/harness.py`, `semantic_entity_index.py:163`, `campaigns/orchestrator.py:612`,
  `state_presenter.py`, `identity_resolver.py:119`). Re-litigating them wastes the original sweep's work.

## Fixtures and determinism

`strategic.concerns` is in canonical state (`src/core/state.py:964`), so **Group A2 will move canonical
hashes and the determinism fingerprint**. This is expected and is the point. Identify every moved
fixture and explain it as "these concerns are no longer generated / are now generated"; if a movement
cannot be explained that way, stop. Changing the `trauma_dead_ally` id literal (step 1d) moves them
again — if you do it, do it in the same commit as 1c so the two movements are not conflated.

## Docs and parity

- `docs/mechanics/02_combat_laws.md` — splash/friendly-fire targeting now catalog-driven.
- `docs/mechanics/04_strategic_cognition.md` — concern intake, saliency and morale inputs.
- `docs/parity_ledger/combat_movement.yaml` and `strategic_cognition.yaml` — update `status` and
  `v2_evidence` on the affected entries; add entries where none exist. `P0` entries need a passing
  `test_path`.
- `docs/guidelines/intentional_divergences.md` — **expected to be needed here**, unlike item 1. These
  are real gameplay changes (monster-vs-monster combat becoming possible) that depart from legacy
  behaviour, with rationale class `Bug Fix` or `Unified`. Decide per group and record the verification
  path.
- Close `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` as folded into this ticket; do
  not leave it open in `tickets/todos/`.
