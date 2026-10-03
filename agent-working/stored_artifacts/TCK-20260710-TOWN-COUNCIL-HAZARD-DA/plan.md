---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-TOWN-COUNCIL-HAZARD-DA
artifact_type: plan
tags: [world, faction, simulation-quality]
---

# Implementation Plan — TCK-20260710-TOWN-COUNCIL-HAZARD-DA

## DA Ruling

**Ruling: (a) — INTENTIONAL.** `town_council`'s unmitigated `NATURAL_TERRAIN` hazard exposure at
`bandit_road` (2 `merchant_caravan_frontier_guard` entities, both `urban_political` and
`generated_frontier_3_42`) is ratified as designed "conflict-pressure" behavior. No content or
mechanism change is made; the decision is recorded as a new entry in
`docs/guidelines/intentional_divergences.md`.

### Rationale

`docs/mechanics/05_world_evolution.md` §3 "Regional Sovereignty" → "Hazard Impacts" is the
authoritative tie-breaker the ticket instructs the planner to use, and it resolves cleanly in favor
of (a):

1. **The doc's own criterion for endurance is native habitat, and `town_council`'s guards fail it
   by design, not by accident.** Every worked example of a faction *declaring* endurance
   (`wild_beast_pack`/`goblin_warband` enduring "their own forest habitats," `undead_remnants`
   enduring "the corruption of their own battlefield") is a faction native to the hazard it is
   exempt from. `town_council`'s `merchant_caravan_frontier_guard` entities are the thematic
   opposite: they are dispatched to `bandit_road` *because* it is bandit-contested, not because
   they live there. `bandit_company` (native) already correctly holds the immunity; `town_council`
   was never a candidate for the same reasoning.
2. **The doc's explicit worked counter-example endorses exactly this shape of exposure as
   designed, not tolerated.** A hero party and a hostile wolf pack both take full, equal
   `TOXIC_GAS` drain fighting inside a hazard neither declares endurance for — "because neither
   faction lists `TOXIC_GAS` in its `hazard_immunities`." This is presented as the mechanism
   working correctly, not as a gap. A guard escort taking slow attrition on a contested road over
   a long campaign is structurally the same case: a non-native party absorbing a hazard it isn't
   adapted to, as a cost of the mission it was assigned.
3. **The mechanism's own design discipline forbids inferring endurance from anything other than
   an explicit per-faction declaration.** `TCK-20260701-HAZARD-NATIVE-IMMUNITY`'s investigation
   record shows a first-pass design was rejected specifically for inferring endurance from a
   coarse property (`entity.identity.faction == Faction.MONSTER_HORDE and region.kind ==
   "WILDERNESS"`). Ruling (b) here would grant `town_council` a `NATURAL_TERRAIN` immunity for a
   reason that reduces to "the last remaining unmitigated faction in an otherwise-reconciled
   region" — a corpus-consistency argument, not a nativity argument. That is exactly the kind of
   inferred/blanket reasoning the mechanism's design history warns against; "everyone else here is
   already immune" is not evidence of native habitat.
4. **No functional harm is occurring under the exposure.** `test_population_stability` passes
   cleanly for both worlds at the documented 300-tick floor with the exposure present and
   unmodified (confirmed by direct run during investigation). There is no regression pressure
   forcing (b).

The corpus-consistency argument for (b) (`town_council` is now the *only* unmitigated faction at
`bandit_road`) is real but is a pattern-matching argument, not a mechanics argument — the doc gives
no support for "immunity should track how many other factions in the region already have one."
Both prior investigations' non-committal framing is treated as exactly what it was: a deferral
under uncertainty, not a lean toward (b) — this ticket exists specifically to convert that
deferral into a decision using the mechanics doc as the tie-breaker, which is what step above does.

This ruling does **not** mechanically extend to `merchant_league`. `merchant_league`'s existing
`bandit_road` immunity was granted under a separate, already-closed ticket
(`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`) for reasons not re-litigated here; this ticket
does not have visibility into whether that grant was itself a nativity call or a different
rationale, and the Out of Scope section explicitly forbids touching it. This is noted as a
candidate observation for a future scoping pass, not resolved here.

## Steps

### Step 1 — Add Divergence Summary Table row
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** In `## 1. Divergence Summary Table`, add one new row immediately after the existing
`| **World / Ecology** | Resource Ecology Kind-Emission Catalog Alignment | **Bug Fix** | RATIFIED |`
row (the last row in the table):

```
| **World / Environment** | Non-Native Faction Hazard Exposure (`town_council`/`bandit_road`) | **Intentional Gameplay Change** | RATIFIED |
```
**Do NOT touch:** Any other row in the table, including the existing `World / Environment` row for
`Hazard-Kind Faction Endurance` (§2.20) — that row documents the mechanism itself and must remain
unmodified. Do not renumber or reorder existing rows.
**Verify:** Manual review — table has exactly one new row, table markdown still renders (pipe
alignment), no existing row's text changed.

### Step 2 — Add Detailed Record §2.30
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** Immediately after the existing `### 2.29 Hazard-Zone Resource-Free Regions
(TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT)` entry and before the `---` /
`## 3. Unsupported / Retired Behavior` section, insert:

```markdown
### 2.30 Non-Native Faction Hazard Exposure — `town_council` at `bandit_road` (TCK-20260710-TOWN-COUNCIL-HAZARD-DA)
- **Subsystem**: World / Environment — Content Disposition
- **Situation**: `town_council`'s 2 `merchant_caravan_frontier_guard` entities are stationed at
  `bandit_road` (`hazard_level: 2.0`, `hazard_kind: "NATURAL_TERRAIN"`) in both `urban_political`
  and `generated_frontier_3_42`. `town_council` declares no `hazard_immunities`
  (`data/content/social/factions.yaml`), so these entities take full, unmitigated hazard drain via
  `EnvironmentService.calculate_hazard_drain`, unlike `bandit_road`'s native `bandit_company`
  (`hazard_immunities: ["NATURAL_TERRAIN"]`) and the region's other populating faction,
  `merchant_league` (also `["NATURAL_TERRAIN"]`, granted by
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`). Two independent investigations
  (`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` Risk #2,
  `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` Root cause 2) found this
  identical case and both declined to rule on it, deferring it as "may be intentional
  conflict-pressure flavor" without recording a decision. A blast-radius check (this ticket)
  confirmed `town_council` is populated in exactly one hazardous region across both worlds —
  `bandit_road` — and nowhere else corpus-wide within the two named worlds
  (`trading_company_hub.yaml`'s `hometown`/`trading_hometown` region spawns only
  `merchant_league`, never `town_council`, in either world's actual resolved spec).
- **Decision**: This exposure is **ratified as intentional**, decided by DA ruling under
  `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` (2026-07-10). `town_council`'s guards are not native to
  `bandit_road` — they are dispatched there specifically because it is a bandit-contested
  wilderness road, i.e. the thematic opposite of "native habitat," which
  `docs/mechanics/05_world_evolution.md` §3 establishes as the criterion for declared endurance.
  The mechanics doc's own worked example (a hero party and a hostile wolf pack both taking full,
  equal `TOXIC_GAS` drain inside a hazard neither declares endurance for) establishes that
  non-native factions taking unmitigated drain in a hazard they are not adapted to is designed
  behavior, not an oversight — `town_council`'s guard escort taking slow attrition on a contested
  road over a long campaign is the same shape of case. No content or code change is made;
  `data/content/social/factions.yaml` and `docs/parity_ledger/world_dynamics.yaml` (`WORLD-029`,
  `WORLD-060`) are left unchanged by this ruling.
- **Rationale**: **Intentional Gameplay Change**. Endurance under this mechanism is strictly a
  faction-declared, native-habitat property (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`'s design,
  reaffirmed by this ruling) — `town_council` was never native to `bandit_road`, so extending it
  an immunity here would require inferring endurance from something other than declared nativity
  (e.g. "is the last remaining unmitigated faction in the region"), which is the same
  blanket/inferred-immunity anti-pattern that mechanism's own rejected first-pass design
  (`entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`) was
  rejected for.
- **Verification**: `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[urban_political]`,
  `::test_population_stability[generated_frontier_3_42]` (both pass at the existing 300-tick floor
  with this exposure present and unmodified, confirmed 2026-07-10);
  `::test_hazard_kind_matches_populating_faction_immunity[urban_political]`,
  `::test_hazard_kind_matches_populating_faction_immunity[generated_frontier_3_42]`
  (region-level immunity match already satisfied by `bandit_company`/`merchant_league`, unaffected
  by this ruling).
- **Status**: ACTIVE
```

Use `§2.29`'s Situation/Decision/Rationale/Verification/Status format (not the Old
Behavior/New Behavior format used by mechanism-change entries like `§2.20`) since this is a
design-acknowledgment ruling with no behavior change, matching `§2.29`'s own precedent.
**Do NOT touch:** `§2.20` (`Hazard-Kind Faction Endurance`) or `§2.29` — both are prior, unrelated
(or mechanism-defining) entries and must not be edited, merged, or renumbered.
**Verify:** Manual review — new `### 2.30` section present, correctly placed after `2.29` and
before `## 3.`, all four cited test names match `test_plan.md`'s Regression Surface exactly.

### Step 3 — Record blast-radius result and coordination notes in the ticket
**Files:** `tickets/inprogress/TCK-20260710-TOWN-COUNCIL-HAZARD-DA.md`
**Change:** Fill in the `## Implementation Notes` section (currently empty) with three items:
1. **Blast-radius check result** (satisfies AC "blast-radius check ... recorded in Implementation
   Notes," applies regardless of ruling): state the investigation's finding verbatim in substance —
   `town_council` is populated in exactly one hazardous region across both worlds (`bandit_road`,
   2 `frontier_guard` entities each); `trading_company_hub.yaml`'s `hometown`/`trading_hometown`
   region spawns only `merchant_league` in both worlds' actual resolved specs, never
   `town_council` — the candidate case named in the ticket's Scope did not materialize.
2. **Sibling ticket coordination** (satisfies the `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`
   reconciliation AC): re-check `tickets/inprogress/` and `tickets/todos/` at implementation time
   for that ticket's live location (investigation found it still in
   `tickets/todos/simq-roadmap-phase1-process-hardening/`, not started, with no temporary test
   exception yet present in `tests/unit/worldassembly/test_corpus_diversity.py`). If still
   unstarted: record "No reconciliation action taken — sibling ticket
   `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` had not yet added its temporary
   `town_council`/`bandit_road` test exception at this ticket's implementation time; this ruling
   (a) is now available for that ticket to cite when it lands, per its own stated design." If it
   has since started/landed with the temporary exception present: read that exception's comment in
   `test_corpus_diversity.py` and record instead that the comment should be updated (by that
   ticket or a fast-follow) to cite this ticket's landed ruling (a) rather than "not yet its own
   ticket" — do not edit `test_corpus_diversity.py` under this ticket regardless (see Scope
   Guards).
3. **`merchant_league` generalization note** (satisfies Out of Scope's "if the ruling's rationale
   mechanically also applies to `merchant_league`, note that explicitly"): record that this
   ruling's nativity-based rationale does not retroactively question `merchant_league`'s existing
   immunity — that grant was made under a separate, already-closed ticket for reasons not
   re-examined here — and flag it only as a candidate observation for a future scoping pass, not
   an action item.
**Do NOT touch:** Any other section of the ticket file (`Scope`, `Out of Scope`, `Acceptance
Criteria`, etc.) in this step — those are edited only by the Finalize phase's normal ticket-closure
process, not by this content step.
**Verify:** Manual review — `Implementation Notes` section is non-empty and contains all three
items; no other ticket section altered.

### Step 4 — Close out `docs/plans/audit_fix_plan.md` P2-Q
**Files:** `docs/plans/audit_fix_plan.md`
**Change:** Two edits in this file:
1. At the P2-Q narrative entry (currently lines ~474-489, header
   `### P2-Q: Non-native factions stationed in a hazardous region with no immunity — recurring open
   design question, never formally resolved`), append a closing line after the existing **Fix:**
   paragraph: `**Resolved (2026-07-10):** Ruled (a) intentional by
   \`TCK-20260710-TOWN-COUNCIL-HAZARD-DA\` — see \`docs/guidelines/intentional_divergences.md\`
   §2.30. \`town_council\`'s bandit_road exposure is ratified as designed non-native
   conflict-pressure flavor; no content or code change made.`
2. At the ledger table row (line 742):
   `| P2-Q | D06/D20 (new) | **P2** | Docs/DA | OPEN (added 2026-07-09) — XS — one DA ruling on
   \`town_council\`/\`bandit_road\` hazard exposure, resolves 2 recurrences at once |`
   change the status cell to:
   `**RESOLVED (2026-07-10)** — ruled (a) intentional, see \`intentional_divergences.md\` §2.30 —
   \`TCK-20260710-TOWN-COUNCIL-HAZARD-DA\``
**Do NOT touch:** The stale sibling-ticket path reference at line ~804
(`tickets/inprogress/TCK-20260710-HAZARD-KIND-CORPUS-WIDE.md`, actually still in
`tickets/todos/simq-roadmap-phase1-process-hardening/`) — this is a pre-existing doc inaccuracy
discovered during investigation but explicitly not part of this ticket's AC; leave it as-is. Do
not touch any other P2-* or P3-* row.
**Verify:** Manual review — P2-Q entry and its table row both show resolved status citing this
ticket and the divergence entry; no other row changed; line ~804 unchanged.

### Step 5 — Close out `docs/plans/simq_development_roadmap.md` Phase 1.2
**Files:** `docs/plans/simq_development_roadmap.md`
**Change:** In the `### 1.2 — town_council/bandit_road DA ruling (P2-Q)` section (currently lines
~208-217), append a new line after the existing `**Ticket filed (2026-07-10):**` line:
`**Ruling landed (2026-07-10):** ruled **(a) intentional** — see
\`docs/guidelines/intentional_divergences.md\` §2.30 and
\`docs/plans/audit_fix_plan.md\` P2-Q. No \`factions.yaml\`/parity-ledger change made.`
**Do NOT touch:** The `### 1.1` section, the "Correction (2026-07-10, after ticketing)" callout
above both subsections (it documents ordering history and remains accurate as written — do not
edit it to claim 1.1 has landed, since it hasn't), or the "**Acceptance signal (both items)**"
line.
**Verify:** Manual review — 1.2 section shows the ruling landed with correct citation; 1.1 section
and the correction callout unchanged.

### Step 6 — Regression verification pass
**Files:** none changed (verification only); ticket `Test Summary` / `Files Changed` sections
(`tickets/inprogress/TCK-20260710-TOWN-COUNCIL-HAZARD-DA.md`) updated with results
**Change:** Run the scoped commands from `test_plan.md`:
```bash
pytest tests/unit/worldassembly/test_corpus_diversity.py -k "population_stability or hazard_kind" -v
pytest tests/unit/world/test_regional_consequences.py -v
pytest tests/unit/worldbuilding/test_world_compiler.py -k urban_political_resolved_bandit_road -v
```
Confirm: same pass/fail profile as the investigation's baseline run (31 passed / 1 pre-existing
unrelated failure in the first command; all green in the other two). Additionally diff-check
(`git diff`) that `data/content/social/factions.yaml` and
`docs/parity_ledger/world_dynamics.yaml` show **zero changes** (required by AC2 under ruling (a)).
Record the command output summary and the zero-diff confirmation in the ticket's `Test Summary`
section; list the 5 changed files
(`docs/guidelines/intentional_divergences.md`, `tickets/inprogress/TCK-20260710-TOWN-COUNCIL-HAZARD-DA.md`,
`docs/plans/audit_fix_plan.md`, `docs/plans/simq_development_roadmap.md`, plus this
`staging_artifacts/.../plan.md`) in `Files Changed`.
**Do NOT touch:** Do not run the full suite (`pytest tests/`). Do not attempt to fix the
pre-existing `test_generated_frontier_3_42_extended_population_stability` failure — it is
unrelated (tick-budget-throttle non-determinism, already tracked/resolved under P2-P) and must not
regress further, but this ticket does not own fixing it.
**Verify:** Test output matches baseline; `git diff -- data/content/social/factions.yaml
docs/parity_ledger/world_dynamics.yaml` is empty.

## Scope Guards

- Do not add or modify `hazard_immunities` on `town_council` in
  `data/content/social/factions.yaml` — ruling (a) requires this file be **unchanged**.
- Do not modify `docs/parity_ledger/world_dynamics.yaml` (`WORLD-029`, `WORLD-060` or any other
  entry) — ruling (a) requires this file be **unchanged**.
- Do not touch `merchant_league`'s existing `hazard_immunities: ["NATURAL_TERRAIN"]` entry in
  `data/content/social/factions.yaml` — its `bandit_road` case is already resolved by a separate,
  closed ticket; only note the generalization question, do not act on it.
- Do not modify `src/world/environment.py::EnvironmentService.calculate_hazard_drain` — working as
  documented, out of scope under both rulings.
- Do not modify `src/worldassembly/resolver.py`'s `"PHYSICAL"` `hazard_kind` default — unrelated,
  out of scope.
- Do not modify `tests/unit/worldassembly/test_corpus_diversity.py` — this ticket does not own
  that file; any temporary exception there belongs to `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` to
  add or remove, not this ticket (Step 3 only reads it for the coordination note).
- Do not recompile or touch `data/worlds/urban_political/` or
  `data/worlds/generated_frontier_3_42/` compiled artifacts — no source content changes under
  ruling (a), so no recompile is needed or permitted.
- Do not touch race-level `hazard_immunities` (`RaceDefinition` extension point) — explicitly out
  of scope per `TCK-20260701-HAZARD-NATIVE-IMMUNITY`.
- Do not edit `bandit_company`'s existing immunity or `bandit_road_trade_pressure.yaml`'s
  `hazard_kind` declaration — both already correct, not in question.
- Do not fix the stale `docs/plans/audit_fix_plan.md` line ~804 sibling-ticket path reference — a
  pre-existing, unrelated doc inaccuracy flagged during investigation but outside this ticket's AC.
- Do not renumber or edit any existing entry in `docs/guidelines/intentional_divergences.md`
  (§2.1–§2.29 or the summary table's existing rows) beyond the two additive insertions in Steps 1–2.

## Dependency Map

- Step 1 and Step 2 both edit `docs/guidelines/intentional_divergences.md` — do Step 1 (table row)
  before Step 2 (detailed record) to keep the table's row list and the detail sections in sync as
  a single reviewable diff, but neither strictly blocks the other.
- Step 3 (ticket Implementation Notes) is independent of Steps 1–2 and 4–5; it can be done at any
  point but is most naturally done alongside or after Steps 1–2 since it cites the same §2.30
  entry number.
- Step 4 and Step 5 both cite the §2.30 entry created in Step 2 — do Step 2 before Steps 4 and 5
  so the citation (`§2.30`) is accurate at the time it's written.
- Step 6 (regression verification) should run last, after Steps 1–5, so the zero-diff check on
  `factions.yaml`/`world_dynamics.yaml` reflects the final state of the working tree and the ticket
  Test Summary/Files Changed sections can be filled in accurately.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Exactly one DA ruling is made and recorded (not merely investigated), applicable to both worlds | Ruling stated in this plan's "DA Ruling" section; recorded in Steps 1–2 | Manual review of §2.30 entry + summary table row |
| If ruled intentional: table row + Detailed Record with rationale class + verification citation; `factions.yaml`/`world_dynamics.yaml` unchanged | Steps 1, 2, 6 | Manual review (Steps 1–2); `git diff` empty check (Step 6) |
| If ruled a genuine gap: `factions.yaml` gains `hazard_immunities`; worlds recompiled; parity ledger updated; regression tests pass | N/A — not applicable under ruling (a); satisfied vacuously since no content/parity change is made (see row above) | N/A |
| Blast-radius check against `trading_company_hub.yaml` (and any other corpus pairing) performed and result recorded in Implementation Notes | Step 3 (item 1) | Manual review of ticket's `Implementation Notes` section |
| `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s temporary test exception (if present) reconciled — removed or comment updated to cite this ticket | Step 3 (item 2) | Manual review of ticket's `Implementation Notes` section; live check of sibling ticket's location and `test_corpus_diversity.py` content at implementation time |
| `docs/plans/audit_fix_plan.md` P2-Q and `docs/plans/simq_development_roadmap.md` Phase 1.2 updated to reflect closure, citing this ticket | Steps 4, 5 | Manual review of both files' updated sections |

## Anti-Drift Notes

- **This is a documentation/content-decision ticket, not a mechanism ticket.** No file under `src/`
  is touched by any step. If any step appears to require a `src/` change, stop — that means the
  ruling or scope has been misunderstood, not that a step was missed.
- **The two files ruling (a) explicitly forbids touching are the highest-risk drift point**:
  `data/content/social/factions.yaml` and `docs/parity_ledger/world_dynamics.yaml`. Step 6's
  `git diff` check exists specifically to catch an accidental edit to either (e.g. from an
  editor auto-save, a stray find/replace across `data/content/`, or a copy-paste of ruling-(b)
  language from the ticket text into the wrong file).
  Do not add a `hazard_immunities` entry "just in case" alongside the divergence record.
- **`merchant_league` is already resolved — do not re-open it.** Its immunity was granted by
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`, a separate closed ticket. This ticket's
  rationale is about `town_council` specifically; Step 3 records the generalization question as an
  observation only, never as an action.
- **`TCK-20260710-HAZARD-KIND-CORPUS-WIDE` may have changed state between investigation and
  implementation** — investigation confirmed it was still unstarted (`tickets/todos/`), but Step 3
  explicitly requires a fresh check at implementation time rather than trusting the investigation's
  snapshot, per the ticket's own Assumptions section.
- **Entry numbering in `intentional_divergences.md` is not strictly sequential in file order**
  (e.g. §2.19 appears before §2.18) — insert §2.30 by *position* (immediately after §2.29, before
  `## 3.`), not by searching for where numerical order "should" put it.
- **The Divergence Summary Table is already known to be incomplete relative to the Detailed
  Records** (several entries §2.24–§2.29 have no matching table row) — this is a pre-existing
  inconsistency in the doc, not something to fix under this ticket. Add exactly one new row for
  §2.30 per the AC; do not attempt to backfill the table's other missing rows.
