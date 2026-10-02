---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP
artifact_type: test_plan
tags: [combat, faction, root-cause]
---

# Test plan — raw legacy-`Faction`-enum hostility sweep

## Proof Plan

- **Level:** mixed. Unit for each predicate's two directions; mechanic-scenario for the durable
  consequences; integration for determinism.
- **Proof kind:** behavioural per site, plus a per-group before/after measurement split by error
  direction.
- **Oracle source:** the content catalog itself, reached through
  `get_faction_semantics_service().is_hostile_compat(...)`, with
  `LegalityServiceV2._is_engagement_hostile`'s own construction (`src/engine/legality.py:516-544`) as the
  reference. `docs/mechanics/02_combat_laws.md` for splash/friendly-fire;
  `docs/mechanics/04_strategic_cognition.md` for concern intake and morale.
  **The oracle is not "different from the raw enum"** — that would pass by changing anything. It is "the
  catalog's answer for this pair in this context".
- **Expected effect:** under-detection corrections dominate — monster-vs-monster conflict becomes
  possible, since `bandit_company`, `goblin_warband` and `orc_clan` share `MONSTER_HORDE`. Over-detection
  corrections reduce friendly fire and spurious `danger` concerns.
- **Selected commands:** see "Scoped commands".

## The fixture every site needs

A world with **two factions in the same legacy bucket that the catalog calls hostile** (two of
`bandit_company` / `goblin_warband` / `orc_clan`) **and** two in different buckets that the catalog calls
friendly. Without both, every test below can pass for the wrong reason. Build it once, minimal — the
entities the assertions read plus ~10-15 for realism, not a corpus world.

**Also include a `NEUTRAL` entity.** `NEUTRAL` is neither hostile nor allied, and step 1c's predicate
choice (`not hostile` vs `allied`) is exactly where a neutral gets misclassified.

## Per-site tests — each needs BOTH directions

The single most important rule here: **every site gets an under-detection test and an over-detection
test.** A one-directional test passes on a predicate that is still half wrong, and this ticket is
precisely about a predicate that was wrong in both directions at once.

**T1 — `combat.py:507` splash (Group A1).**
- T1a *under*: same-bucket catalog-hostile victim in radius **is** damaged. Fails today.
- T1b *over*: different-bucket catalog-friendly victim in radius is **not** damaged. Fails today.
- T1c *inversion guard*: the attacker's own catalog-allies are never splashed. Catches the
  skip-condition being inverted, which would turn splash into friendly fire on everything — the most
  damaging plausible implementation error.

**T2 — `intake.py:30` danger concern (A2).** Different-bucket catalog-friendly neighbour within 3 tiles
produces **no** `danger` concern; same-bucket catalog-hostile neighbour **does**. Assert on
`strategic.concerns` content, not on a log line.

**T3 — `intake.py:44` `trauma_dead_ally` (A2).** Dead same-bucket catalog-**non**-ally produces **no**
trauma concern; dead catalog-ally **does**. **Plus a neutral case**: a dead `NEUTRAL` neighbour — assert
whatever step 1c decided, and make the test name state the decision, so the choice is visible rather than
implied.

**T4 — `legality.py:451` flanking (B).** Flanking bonus applies against a same-bucket catalog-hostile
flanker and not against a different-bucket catalog-friendly one. **T4b**: with clean identity data
unavailable, the raw-enum fallback still engages — guards the `:265-269` structure the plan says to
preserve rather than remove.

**T5 — Group C sites.** One pair of assertions each for `cognition.py:44`, `cognition.py:117`,
`cooperation/providers.py:50`, `intelligence.py:149`, `intelligence.py:439`.

**T6 — exactly one helper.** Assert the shared catalog predicate is one object, imported by every fixed
site — e.g. identity-compare the function across modules, as the boss-kinds drift-pin ticket did for its
constants. This is the test that stops the sweep from recreating the divergence it closes. Do **not**
assert over source text.

**T7 — the deliberate non-sites stay untouched.** `legality.py:269` keeps its clean-data fallback;
`scorers.py:108` is unchanged by this ticket (item 1 owns it). A test or an explicit review note is fine;
the point is that "fixed everything that matched the grep" is the wrong outcome.

**T8 — determinism.** Two identical seeded runs produce identical canonical hashes, then the full
canonical/replay/fingerprint/hash/checkpoint sweep.

## Scoped commands

```
pytest tests/unit/combat/ tests/unit/engine/ tests/unit/strategic/ -q
pytest tests/unit/observability/ tests/unit/core/ -q
pytest tests/mechanic_scenarios/ -q
pytest tests/integration/ -q -m "not slow"
```
Then the determinism sweep as the repo runs it. Re-run specifically:
`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`'s own tests (same predicate, already
converted — they are the regression guard for the helper), and anything asserting
`is_hostile_compat`, `_is_engagement_hostile` or `get_engaged_hostiles_at_pos`.

## Fixtures — expect movement, and expect it twice

`strategic.concerns` is in canonical state (`src/core/state.py:964`), so **Group A2 moves canonical
hashes and the determinism fingerprint by design.** Explain each movement as "these concerns are no
longer generated / are now generated". If a movement cannot be explained that way, **stop** — that is a
finding.

If step 1d changes the `trauma_dead_ally` id literal, hashes move a second time. Do it in the same commit
as T3's fix so the two movements are not conflated, or the explanation for each becomes guesswork.

## Coverage against the required classes

| class | covered by |
|---|---|
| normal flow | T1a, T2, T3, T4 |
| edge cases | the `NEUTRAL` case in T3; T4b's unclean-identity fallback |
| failure modes | T1c inversion guard; T6 helper uniqueness |
| regression-prone paths | T7 non-sites; the re-run of the original arc's tests |
| architecture — read-only logic did not mutate live state | `filter_saliency` and the scorers stay pure |
| architecture — authoritative apply path used | T1-T3 run through `Kernel.tick_once()`, not direct mutation |
| architecture — typed records round-trip | T8 canonical hash; `ConcernState` serialisation |

## Known gaps, stated rather than left implicit

- **No site has a measured corpus firing frequency.** The 34-97% figure is a disagreement rate over
  flagged pairs, **not** a frequency. The per-group before/after measurement in `plan.md` exists to
  supply what is missing; until it runs, no impact claim should be made for any site.
- **Group A1's baseline must be taken after item 1 lands.** Decision-driven combat currently fires 2-3
  times per 2000 ticks, so a splash baseline taken now measures a world where the path barely runs.
- **C1's inherited "0.5% real impact" is not this ticket's number** — it was measured for a different
  consumer. Re-measure.
- **C3 and C4's durability is unconfirmed.** If either writes durable state they belong in Group A with
  their own measurement; the plan says confirm, not assume.
- `quest_dense_frontier` is unsuitable as a measurement world for anything combat-driven (0 combat-engage
  wins in 410 competitions). Use `crowded_frontier` and `frontier_living_world`.
