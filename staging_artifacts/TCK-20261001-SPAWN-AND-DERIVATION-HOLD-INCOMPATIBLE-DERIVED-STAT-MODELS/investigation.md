---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS
artifact_type: investigation
tags: [simulation-quality, progression, combat, architecture]
---

# Investigation — per-field authority for the derived combat-stat set

## 1. What this investigation changed about the ticket

The ticket was filed as "eight fields, per-field authority unknown, decide each one." That framing
was wrong in a specific and useful way: **seven of the eight fields were already decided — by the
Mechanics Bible or by `TCK-20260921`'s own shipped code — and nobody had looked.** Only `atk_range`
was genuinely open, and it was open as a *design* question, not a parity question.

The ticket's own drift table is accurate as a measurement and misleading as an agenda. It presents
`move_cost`, `atk_range` and `def_stat` as three instances of one problem ("spawn and the derivation
disagree"). They are three different problems with three different owners:

- `move_cost` — the **derivation** is right and **spawn** is the divergence.
- `def_stat` — **neither** is wrong; the drift row describes a clamp that does not exist in the code.
- `atk_range` — the **derivation** is genuinely incomplete, and no declared formula exists to appeal
  to.

So the real work is much narrower than the ticket implies, and the one thing that needed a human
decision has now had one.

## 2. The ordering that settles it (not a new policy)

`world-rule-catalog-design`, which owns `docs/world_rules/`, was asked whether a catalog Rule picks
content-vs-derivation authority. **It does not, and it should not** — and a parallel per-field policy
must not be invented here. The ordering already exists one layer down:

1. **The Mechanics Bible formula**, where one exists (CLAUDE.md "Precedence").
2. **The content declaration** — `docs/mechanics/01_entity_anatomy.md:51` states a stat profile
   declares the **FINAL spawned stat**.
3. **The derivation.**

Two catalog Rules constrain every field regardless of which way it resolves:

- **PROG-01** (`docs/world_rules/capability-progression/capability-progression.md:36`) — capability
  acquisition and loss occur only through declared causal mechanisms.
- **CAUSE-01** (`docs/world_rules/foundations/causality.md:23`) — a consequence requires a real
  causal path.

Together: **a `stats_dirty` trigger firing is not a cause.** Activation must not change any entity's
value unless that change is itself a declared mechanism (a Bible formula, a parity entry, or a
declared divergence). This is the constraint AC2/AC3 exist to discharge, and it is the reason the
exit condition in AC5 is not merely bookkeeping.

A third Rule decides `atk_range`'s shape: **CAP-05**
(`docs/world_rules/foundations/capability.md:104`) names subject state, learned ability, equipment
**and body/form** as legitimate independent factors. An equipment-only model of range is therefore a
*narrowing* a domain would have to declare, not a default it may assume.

`data/content/entities/stat_profiles.yaml` is **content data, not the Rule Catalog**. A profile value
is not a catalog declaration, so "the profile is wrong" is never a catalog fix. The catalog supplies
the constraints above and nothing more. (Framing correction from the rule owner; worth keeping,
because it is easy to argue a content question as though it were a Rules question.)

## 3. Per-field authority decision — AC1, discharged

Every row below was verified directly against the cited file at `origin/main` (`78ea7c465` +
`758eae4ff`), not relayed.

| field | authority | basis | status |
|---|---|---|---|
| `max_hp` | content (profile), reconciled by residual base | Bible `01_entity_anatomy.md:36,49-53`; `PROG-127` | **settled by #279** |
| `atk` | content (profile), reconciled by residual base | Bible `01:41,49-53`; `PROG-127` | **settled by #279** |
| `evasion` | content (profile), reconciled by residual base | Bible `01:43,49-53`; `PROG-127` | **settled by #279** |
| `def_stat` | content (profile), reconciled by **unclamped** residual | Bible `01:42,51-53`; `src/core/derived_stats.py:28-33` | **settled by #279** — see §4 |
| `move_cost` | **derivation** (spawn's default is the divergence) | Bible `01:47` | **settled by the Bible** — see §5 |
| `readiness_speed` | **derivation** | Bible `02_combat_laws.md:139-140`; `attribute_progression_contract.md:141` | **settled by the Bible** — see §6 |
| `tactical_role` | **derivation** | Bible `01:61` | **settled by the Bible** |
| `atk_range` | **content (profile) is the archetype factor; weapon is an independent factor** | user decision 2026-10-02; CAP-05 | **decided — see §7** |

## 4. `def_stat` — the drift row is hypothetical; strike it

The ticket's table says: "`worker` spawns `def 0` at `vitality 5`, so the residual is `-1`; under a
clamp-at-zero it becomes `0 → 1` (8 and 11 entities)."

**There is no clamp.** `src/core/derived_stats.py:23-40`'s `residual_base_terms()` docstring is
explicit, and names this exact entity:

> It is deliberately unclamped: a profile stat below its own attribute contribution (e.g. a
> `worker` with def 0 and vitality 5) yields a negative term, and clamping it would break the
> exact round trip that is the point of storing it.

Bible `01:51-53` agrees — each base is the residual `spawned stat - attribute contribution` **"(it
may be negative)"**. No Rule or Bible text puts a floor on final `def`. `def 0` is a legitimate
final value, and the `worker` round-trips exactly under the shipped code.

**Disposition: settled by `TCK-20260921`, no work in this ticket.** The row should be struck from
the ticket's open set. It is a correct description of a counterfactual, which read as a defect.

A standing consequence worth recording: **any future proposal to clamp a residual base at zero
would itself violate the round trip** that `PROG-127` asserts and that OWN-01's PARTIAL grade rests
on. That is the kind of change that looks like hardening and is actually a regression.

## 5. `move_cost` — spawn is the divergence, and the instrument is the parity ledger

Bible `01_entity_anatomy.md:47` declares:

```
Move_Cost = max(5.0, 10.0 + (total_weight / 5.0) - (agility * 0.1))
```

Spawn never sets `move_cost`; it leaves `CombatComponent`'s default `10.0` (`src/core/state.py:407`).
So the measured `10.0 → 9.5` shift on every entity (2/2, 49/49, 38/38) is the derivation **moving
code into Bible parity**, not away from it.

This inverts the instrument. `docs/guidelines/intentional_divergences.md` records V2 *departures*
from the Bible or legacy; a change that restores conformance does not belong there. The correct
instruments are:

- **Parity ledger** — an entry (or a `PROG-127` extension) marking the spawn path divergent today
  and verified after.
- **Ticket and PR text** — the `10.0 → 9.5` shift on every entity stated explicitly as a visible
  gameplay change. It is small per entity and universal in scope, which is exactly the combination
  that gets waved through.
- **SimQ** — caveat any comparison spanning the change. Note the grade anchors are already red on
  `main` (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`), so SimQ cannot be cited as
  evidence either way here.

A `DEV-` entry is required **only if the decision were to keep `10.0` against the Bible.** That, not
the fix, would be the divergence. This corrects an assumption carried into the investigation — the
instinct was to file a divergence for any visible value change, which would have recorded conformance
as departure.

## 6. `readiness_speed` — settled, and the formula is not where you would look

The rule owner had not checked this field and said to apply the same ordering. Applying it: a Bible
formula **does** exist, but in chapter 02, not chapter 01 — `docs/mechanics/02_combat_laws.md:139-140`
and `docs/mechanics/attribute_progression_contract.md:141`:

```
readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)
```

So the derivation is authoritative, same as `move_cost` and `tactical_role`. `01_entity_anatomy.md`
§2's own formula block does **not** carry it, which is why both the ticket and the rule owner treated
it as undeclared. The measured "no drift in these worlds" is consistent with this but is not the
reason — the Bible is.

**Note for the Bible edit (AC1/AC5):** chapter 01 §2's formula block is incomplete as a statement of
the derived set. It carries `Max_HP`, `Max_Stamina`, `Attack`, `Defense`, `Evasion`, `Move_Cost` — and
omits `readiness_speed`, `atk_range` and `tactical_role`, while line 57-58 names three of those as
fields spawn and derivation must agree on. A reader of §2 cannot see the full set the recalculation
returns. Consolidating the set into §2 (`readiness_speed` by cross-reference to ch.02, `atk_range`
newly, `tactical_role` by cross-reference to §2's own subsection) is part of this ticket's AC1 record,
not scope creep: AC1 asks for a recorded decision per field, and the record is unreadable if §2 omits
three of the eight.

## 7. `atk_range` — the one real decision, and it was the user's

**No Bible formula exists.** Verified: `01_entity_anatomy.md` mentions "attack range" only at line 58,
as one of the fields spawn and derivation must agree on — there is no formula anywhere in §2. So
"main-hand weapon property, else `1`" is a **code-only model** with no declared standing.

Content declares otherwise. Five profiles in `data/content/entities/stat_profiles.yaml` declare
non-melee `attack_range`: `goblin_archer_base` (3), `apprentice_mage_base` (3), `ranger_base` (3),
`spirit_guardian_base` (2), `dragon_champion_base` (3). The measurement caught two `scout` entities
drifting `3 → 1`; **the catalog says the blast radius is the whole declared ranged roster.**

Two readings were put to the user, because they produce opposite implementations and opposite content
outcomes:

1. **Profile declares range; weapon modifies it.** CAP-05 supports it (body/form is a legitimate
   independent factor alongside equipment), and it is factually better fitted to the content —
   `apprentice_mage_base` (3) and `spirit_guardian_base` (2) do not plausibly derive range from a
   weapon.
2. **Range emerges only from equipment**, and the five declarations are stale. Permitted by the
   Rules, but only with a **declared migration** so no entity silently loses range (PROG-01) — e.g.
   equipping those archetypes with range-granting items. That changes content and gameplay.

**Decision (user, 2026-10-02): reading 1.** The profile's `attack_range` is the archetype factor, the
weapon property is an independent factor, and **the combination rule is written into Bible 01 §2**
next to `Move_Cost`. No entity loses declared range.

The combination rule itself is left to the plan rather than fixed here, because it is an
implementation shape (`max(profile, weapon)` vs "weapon overrides when present") with a real
behavioural difference for an archer holding a melee weapon. Both satisfy the decision; the plan must
pick one, state it, and the Bible text must say which.

## 8. What remains, and the hazard that outlives it

Discharged by this investigation: **AC1** (the table in §3), and the substance of **AC5** — Bible
`01:57-58` already states the exit condition ("must not be activated before spawn and derivation agree
on `Move_Cost`, attack range, readiness speed and tactical role"), so AC5 is a matter of making that
text agree with §3 rather than writing a new condition.

Remaining, for the plan:

- **AC2** — generalise `TCK-20260921`'s round-trip test from four fields to every
  content-authoritative field. Per §3 that set is `max_hp`, `atk`, `evasion`, `def_stat` and now
  `atk_range`. It is **not** all eight: asserting a round trip on a derivation-authoritative field
  would assert the wrong invariant.
- **AC3** — a declared entry only where a value intentionally changes **against** a declared source.
  Per §5 `move_cost` is a parity-ledger item, not a divergence. On current analysis **no `DEV-` entry
  is required by this ticket** — a conclusion the plan should re-test rather than inherit.
- **AC4** — the ranged-archetype case, now concrete: a `ranger_base`/`goblin_archer_base` entity, and
  specifically **a ranged archetype with no main-hand weapon**, which is the case that breaks today.
- **AC6** — the tripwire. See below.

**The hazard does not end when this ticket lands.** AC6 asks for a test that fails loudly if
`stats_dirty` becomes reachable while the authority decisions are open. Those decisions are now
closed, so the naive reading is that AC6 is moot. It is not: the decisions are closed *on paper*, and
the drift they describe is still live in code until AC2/AC4 ship. The tripwire's condition should be
"the derivation is reachable **and** the content-authoritative fields do not round-trip", not "AC1 is
open" — otherwise it disarms itself the moment this file is committed, which is the point at which it
is most needed.

## 9. Sources verified directly (not relayed)

- `docs/mechanics/01_entity_anatomy.md:36,41-43,47,49-58,61` — formula block, residual/FINAL language,
  exit condition, tactical-role derivation
- `docs/mechanics/02_combat_laws.md:133,139-140` and `docs/mechanics/attribute_progression_contract.md:141`
  — `readiness_speed` formula
- `src/core/derived_stats.py:23-40` — `residual_base_terms`, unclamped, `worker` case named
- `docs/parity_ledger/progression.yaml:1642-1660` — `PROG-127`, `status: verified`
- `docs/world_rules/capability-progression/capability-progression.md:36` — PROG-01
- `docs/world_rules/foundations/causality.md:23` — CAUSE-01
- `docs/world_rules/foundations/capability.md:104` — CAP-05
- `data/content/entities/stat_profiles.yaml` — **re-measured, not inherited from the ticket**: of 23
  profiles, exactly **5** declare a non-melee `attack_range`, and the values match the ticket
  exactly — `goblin_archer_base` 3, `apprentice_mage_base` 3, `ranger_base` 3, `spirit_guardian_base`
  2, `dragon_champion_base` 3. So **22% of the declared roster** loses its range under the current
  derivation, not a handful of outliers.
