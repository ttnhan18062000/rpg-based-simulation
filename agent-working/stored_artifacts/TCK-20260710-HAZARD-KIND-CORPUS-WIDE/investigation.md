---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-HAZARD-KIND-CORPUS-WIDE
artifact_type: investigation
tags: [simulation-quality, world, corpus, calibration]
---

# Investigation — TCK-20260710-HAZARD-KIND-CORPUS-WIDE

## Current Behavior

- `tests/unit/worldassembly/test_corpus_diversity.py:413-447` —
  `test_hazard_kind_matches_populating_faction_immunity` is parametrized over
  `HAZARD_KIND_MATCH_WORLDS` (line 41): `["dungeon_crawl", "urban_political",
  "generated_frontier_3_42"]` — a 3-world allowlist, not the full corpus. No `town_council`/
  `bandit_road` exception exists anywhere in the file today (confirmed by full read — no
  `xfail`, no skip, no named carve-out).
- The test's matching logic (line 438-447) is **region-level "any populating faction," not
  per-faction "every populating faction."** It builds `populating_factions_by_region` as the
  **union** of every faction with an entity spawned in that region, then asserts
  `matched = any(hazard_kind in immunities.get(f, set()) for f in populating_factions)`. If
  *any one* faction in that union is immune to the region's `hazard_kind`, the assertion
  passes — even if other co-located factions are not individually immune.
- `test_hazard_kind_completeness` (lines 390-406) is a separate, presence-only sibling test
  (parametrized over `HAZARD_KIND_COMPLETENESS_WORLDS`, the 8 `ANCHORED_WORLD_BANDS` worlds
  plus `dungeon_crawl`/`sandbox_world`/`generated_frontier_3_42`/`urban_political`) — it only
  checks `hazard_level > 0` regions declare a truthy `hazard_kind`, never checks matching. Out
  of scope for this ticket (ticket Out of Scope, confirmed unmodified by design).
- `src/worldassembly/resolver.py:798` — `hazard_kind=getattr(reg, "hazard_kind", "PHYSICAL")`.
  Confirmed unchanged; `"PHYSICAL"` remains the resolver default that no faction is ever
  immune to by design (`docs/mechanics/05_world_evolution.md` §3 line 93).
- `src/world/environment.py::EnvironmentService.calculate_hazard_drain` (lines 16-41) —
  confirmed unchanged. This is the actual runtime mechanism, and it is **per-entity, not
  per-region**: `get_faction_id_str(entity)` resolves the individual entity's own faction,
  and only *that* faction's `hazard_immunities` is checked against `region.hazard_kind`
  (line 31). This is stricter than the test's region-level "any" check — an entity whose own
  faction is not immune takes full drain regardless of what other factions share the region.
  This is the exact mismatch behind the whole defect class (§ Current Behavior above and Risks
  below).
- `data/content/social/factions.yaml` — `hazard_immunities` grep confirms 8 factions declare
  immunities: `goblin_warband`, `wild_beast_pack` (implied via other block), `merchant_league`,
  `bandit_company`, `forest_wardens`, `orc_clan`, `undead_remnants` (`UNDEAD_CORRUPTION`),
  `arcane_circle` (`ARCANE_CORRUPTION`), `swamp_tribe`, `dragon_cult`. `town_council` has **no**
  `hazard_immunities` entry (confirmed by grep — no match near its block).

### Corpus World Count and ID Confirmation (investigation step 1)

- `data/worlds/*` (excluding `world_index.json`) = **17 directories**, confirmed by direct
  listing: `crowded_frontier, dungeon_crawl, frontier_extended, frontier_living_world,
  frontier_marches, generated_frontier_3_42, hero_guild_routing, highland_traverse,
  resource_dense_basin, sandbox_world, simq_routing_test, swamp_border_world,
  unit_faction_tension, unit_information_source, unit_selfmodel_pilot, urban_political,
  wilderness_survival`.
- `tests/simulation_quality/fixtures/grade_anchors.json`'s world-id set (stripped of
  `_seed{N}_{ticks}t`) = the **exact same 17 world_ids**, confirmed by script extraction.
- **No divergence.** The ticket's Assumptions-section premise ("17 worlds, both sources
  identical") holds unchanged; no re-verification action needed.

## Corpus-Wide Dry-Run Results

Ran the corpus-wide check as an investigation dry-run, using the test module's own
`_faction_hazard_immunities()` helper and the exact matching expression from
`test_hazard_kind_matches_populating_faction_immunity` (imported the live module and
re-executed its logic against all 17 worlds' resolved specs — not a hand-derived
reimplementation; cross-checked twice, once standalone and once via `import
test_corpus_diversity as m` using its actual `WORLDS_ROOT`/`_faction_hazard_immunities`).

**Result: 0 mismatches across all 17 worlds, 45 hazardous-populated-region checks, including
every `bandit_road` occurrence.**

| World | Hazardous populated regions checked | Mismatches |
|---|---|---|
| crowded_frontier | bandit_road, goblin_camp, orc_stronghold | 0 |
| dungeon_crawl | goblin_camp, old_mine, haunted_battlefield, bandit_road | 0 |
| frontier_extended | bandit_road, goblin_camp, old_mine, orc_stronghold, haunted_battlefield, wolf_den, sacred_grove | 0 |
| frontier_living_world | bandit_road, goblin_camp, old_mine, haunted_battlefield, wolf_den | 0 |
| frontier_marches | bandit_road, goblin_camp, old_mine, orc_stronghold, swamp_border_territory, haunted_battlefield, wolf_den | 0 |
| generated_frontier_3_42 | bandit_road, goblin_camp, moon_cave, old_mine, orc_stronghold | 0 |
| hero_guild_routing | goblin_camp, haunted_battlefield | 0 |
| highland_traverse | wolf_den | 0 |
| resource_dense_basin | old_mine, orc_stronghold | 0 |
| sandbox_world | wolf_den | 0 |
| simq_routing_test | goblin_camp, old_mine | 0 |
| swamp_border_world | swamp_border_territory, wolf_den | 0 |
| unit_faction_tension | wolf_den | 0 |
| unit_information_source | (no hazardous populated regions) | n/a |
| unit_selfmodel_pilot | (no hazardous populated regions) | n/a |
| urban_political | bandit_road, trading_hometown | 0 |
| wilderness_survival | haunted_battlefield, wolf_den | 0 |

**The known `town_council`/`bandit_road` case specifically** (present in `crowded_frontier`,
`frontier_extended`, `frontier_living_world`, `frontier_marches`, `generated_frontier_3_42`,
`urban_political` — 6 of the 17 worlds): `bandit_road` has `hazard_kind: "NATURAL_TERRAIN"` and
is populated by `bandit_company`, `merchant_league`, and `town_council`. `bandit_company` and
`merchant_league` both declare `hazard_immunities: ["NATURAL_TERRAIN"]`; `town_council` does
not. Under the test's **region-level "any populating faction"** semantics, `matched = any(...)`
evaluates `True` because `bandit_company`/`merchant_league` satisfy it — **regardless of
`town_council`'s non-immune status.** The assertion passes at every one of the 6 occurrences.

**No other mismatch exists anywhere in the corpus.** All 45 hazardous-populated-region checks
pass under the test's current matching logic, with zero exceptions required.

## P2-Q Status Update

The ticket's own Assumptions section (line 145-149) states P2-Q was "confirmed not yet its own
ticket" and reasons: *"if P2-Q lands before this ticket implements, prefer letting the test pass
unaided (no exception needed) over adding a now-redundant carve-out."* Since this investigation
began, **P2-Q has landed**: `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` (done 2026-07-11) recorded
**ruling (a) — intentional** in `docs/guidelines/intentional_divergences.md` §2.30. Verified via
direct read of both the done ticket and §2.30: `town_council`'s unmitigated exposure at
`bandit_road` in `urban_political` and `generated_frontier_3_42` (per-entity, real, ongoing —
confirmed by `calculate_hazard_drain`'s per-entity resolution above) is ratified as **permanent
designed "conflict-pressure flavor,"** not a bug to be fixed. `data/content/social/factions.yaml`
and `docs/parity_ledger/world_dynamics.yaml` are confirmed byte-for-byte unchanged by that ruling
(git diff --stat verified empty in the done ticket's own Test Summary).

**Correction to the orchestrator's framing:** the task brief for this investigation assumed
ruling (a) necessarily means "the corpus-wide test WILL still need the town_council/bandit_road
exception." **The dry-run evidence above shows this is not the case.** The reason is a layer the
ticket's own Assumptions section did not anticipate: the test's matching semantics are
**region-level "any,"** not per-faction "every" — a design choice already flagged as out of scope
to redesign by this ticket itself (Out of Scope, "Redesigning `test_hazard_kind_completeness`'s
broader presence-only coverage semantics... citing investigation.md Risk 5" — the same
region-vs-per-faction gap applies to `test_hazard_kind_matches_populating_faction_immunity`, not
just its presence-only sibling). Because `bandit_company` and `merchant_league` are already
immune at every `bandit_road` occurrence (the latter's immunity was granted earlier, by the
already-done `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`), the region-level "any" check was
**already passing before P2-Q ever ruled**, and continues to pass now. `town_council`'s
individual non-immunity is real (confirmed by the mechanism itself, `calculate_hazard_drain`) but
invisible to this specific test's coarser region-level check — which is a known, out-of-scope
limitation, not something this ticket introduces or must fix.

This also explains the landed ticket's own Implementation Notes point 2 (`TCK-20260710-
TOWN-COUNCIL-HAZARD-DA`, line 209-222): it independently concluded "Phase 1.1 is now clear to
land directly against the corpus-wide completeness test without ever needing to add that
temporary exception" — though its stated reasoning there was that this ticket had "not yet
added" the exception at that ticket's implementation time (a timing observation, not a semantics
one). The dry-run in this investigation confirms the **outcome** that ticket predicted
(no exception needed) is correct, but for a structural reason (the test's "any" semantics) that
holds independent of timing or of which DA ruling landed.

**Net implication for the Plan phase:** AC #3 ("(a) excluded via a narrow, named, commented
exception citing the P2-Q tracking reference, or (b) resolved because P2-Q landed first and the
mechanism now matches") is satisfied by **outcome (b)** — the mechanism (the test's own matching
logic) now passes unaided, corpus-wide, with **no code-level exception required**. However, the
precise reason is not "P2-Q's ruling changed the mechanism" (ruling (a) made zero content
changes) — it is "the test's pre-existing region-level match semantics were never actually
falsified by this case." The Plan should:
1. Parametrize `test_hazard_kind_matches_populating_faction_immunity` over all 17
   `data/worlds/*` world_ids (replacing `HAZARD_KIND_MATCH_WORLDS`), reusing
   `_load_resolved_spec`/`_faction_hazard_immunities`/`pytest.skip` exactly as scoped.
2. Add **no runtime exception/xfail** for `town_council`/`bandit_road` — the dry run shows it
   is unnecessary — but **do** add an explanatory code comment near the test (or near wherever
   `bandit_road`'s expected-pass shape would otherwise look surprising to a future reader) citing
   `docs/guidelines/intentional_divergences.md` §2.30 and `TCK-20260710-TOWN-COUNCIL-HAZARD-DA`
   as the record of why `town_council`'s non-immune presence at `bandit_road` is known and
   ratified, and noting that the test's region-level "any" semantics (not a content fix) is why
   this case does not need a carve-out. This keeps the Completion Summary's citation stale-proof
   without violating the ticket's Out-of-Scope bar against a "broad or wildcard exception
   mechanism" (line 57) or a matching-semantics redesign — it is documentation only, not logic.
3. Remove `HAZARD_KIND_MATCH_WORLDS` per Scope (line 62-63) since it is now fully superseded.

## Mechanics / Engine Constraints

- `docs/mechanics/05_world_evolution.md` §3 "Hazard Impacts" / "Native Endurance to a Region's
  Hazard Kind" (lines 55-107) is the authoritative law: every region carries a `hazard_kind`
  (default `"PHYSICAL"`, line 93); `FactionDefinition.hazard_immunities` is the faction-declared
  set of `hazard_kind` values its members endure without harm; the exemption is **unconditional
  and per-entity**, resolved against the entity's own faction, "independent of hostility to any
  other faction present" (also stated verbatim in `calculate_hazard_drain`'s docstring). This
  per-entity design is why the test's region-level "any" check is a structurally weaker
  approximation of the real mechanism — a fact this ticket's Out-of-Scope bar (redesign of
  matching semantics) explicitly declines to close.
- This ticket makes **zero changes** to `src/worldassembly/resolver.py` or
  `src/world/environment.py::calculate_hazard_drain` (confirmed unchanged, read-only per ticket
  Out of Scope) — the dry run above used the current, unmodified mechanism.

## Parity Ledger Overlap

- **WORLD-029** (`docs/parity_ledger/world_dynamics.yaml` line 285-300, status `verified`,
  priority `P0`) — "Calamity aura and regional hazards apply local debuffs/drain." `v2_evidence`
  cites `calculate_hazard_drain`'s per-entity faction-immunity exemption; no `test_path` field
  present in this entry (only `legacy_evidence`/`v2_evidence` prose). Confirmed unaffected — this
  ticket is test-only and finds no genuine new content defect requiring a `v2_evidence` update.
- **WORLD-060** (line 320-335, status `verified`, priority `P0`) — "Regional hazards drain
  HP/Readiness based on intensity." Same mechanism, same conclusion: unaffected, no update
  required. Both entries already reference `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`'s
  fix; neither yet references `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` or this ticket, but per the
  landed ticket's own AC #2 that update was explicitly **not required** under ruling (a) (zero
  content change), and this ticket is test-only per its own Scope — no P0 `test_path` gap to
  flag.
- No other parity ledger subsystem file overlaps this ticket's scope (test-file-only change to
  an existing, already-covered mechanism).

## Prior Work

- `TCK-20260701-HAZARD-NATIVE-IMMUNITY` — origin of the `hazard_kind`/`hazard_immunities`
  mechanism; its investigation explicitly rejected a blanket/inferred-immunity design
  (`entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`) in favor
  of the current faction-declared, native-habitat model — directly relevant precedent for why
  the Plan should not invent a broad exception mechanism here either.
- `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` — first corpus-wide `hazard_kind` authoring pass (7
  modules, 6 factions).
- `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` — extended
  `HAZARD_KIND_COMPLETENESS_WORLDS`/`POPULATION_STABILITY_WORLDS` to cover previously-uncovered
  worlds (2nd-order coverage-gap fix, same pattern as this ticket but for the presence-only
  sibling test).
- `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` — 2nd recurrence; added `dungeon_crawl`/
  `urban_political` to `HAZARD_KIND_MATCH_WORLDS`; granted `merchant_league` its
  `NATURAL_TERRAIN` immunity (the fix that makes today's dry run pass for `bandit_road`); first
  surfaced the `town_council`/`bandit_road` question (Risk #2).
- `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` — 3rd recurrence; added
  `generated_frontier_3_42`; re-surfaced the same `town_council`/`bandit_road` question (Root
  cause 2).
- `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` (done 2026-07-11, landed **after** this ticket was
  scoped) — made the P2-Q ruling; see P2-Q Status Update above for full detail.
- `docs/plans/audit_fix_plan.md` — P2-O status: `OPEN (added 2026-07-09)`, this ticket's own
  source entry, line 743. P2-Q status: `RESOLVED (2026-07-10)`, line 745, confirming the landed
  ruling.
- `tickets/todos/simq-roadmap-phase1-process-hardening/SEQUENCE.md` — the sibling sequencing doc
  ordering P2-Q (`TCK-20260710-TOWN-COUNCIL-HAZARD-DA`) before P2-O (this ticket),
  reasoning "running 1.1's corpus-wide test before this DA ruling lands hits the
  `town_council`/`bandit_road` case as a live failure." **This reasoning does not match the dry-
  run evidence** — the region-level "any" semantics mean it was never actually a live failure,
  with or without P2-Q, once `merchant_league`'s immunity landed (already true before P2-Q).
  Flagged as a documentation staleness item, not a blocker (see Risks below).

## Risks and Open Questions

1. **SEQUENCE.md's ordering rationale is empirically incorrect and should be corrected when this
   ticket closes.** It claims running the corpus-wide test before P2-Q lands would hit a live
   failure; the dry run shows it would not have (region-level "any" already covered
   `bandit_road` via `bandit_company`/`merchant_league`, independent of P2-Q or of ordering).
   This does not block implementation, but the Plan/Completion Summary should note the
   correction so a future reader of `SEQUENCE.md` is not misled about why 1.1 passed cleanly.
   Not this ticket's file to edit unless the planner scopes it in explicitly — flagging per the
   Uncertainty Rule rather than assuming license to touch a doc outside Related Docs.
2. **The region-level "any" vs. per-entity mismatch is a real, structural test-coverage gap** —
   it is *possible* (not observed in this corpus, but structurally possible) for a future world
   to add a hazardous region populated only by non-immune factions alongside one immune faction,
   and the current test would still pass while some entities silently take unmitigated drain.
   This is exactly Risk 5's territory from the referenced prior investigation and is explicitly
   out of scope for this ticket to redesign — flagging so the Plan does not attempt to "fix" it
   as a drive-by, and so a future ticket has a paper trail if this gap ever produces a 4th/5th
   recurrence that this test's own logic fails to catch.
3. **No genuine new (4th+) recurrence was found.** AC #7's contingency (document a new
   recurrence if found) does not apply — the dry run is clean. This should be stated explicitly
   and not silently omitted, since the ticket's Out of Scope explicitly anticipated this
   possibility.
4. `docs/plans/audit_fix_plan.md` P2-O (line 743) still reads `OPEN` — the Plan/Completion phase
   should close this out citing the corpus-wide test landing, consistent with how P2-Q's own
   closure was recorded (line 745 pattern).

## Anti-Drift Hazards

- Do not redesign `test_hazard_kind_matches_populating_faction_immunity`'s matching logic from
  region-level "any" to per-faction "every" under this ticket — that is a semantics change
  explicitly out of scope (ticket Out of Scope, Risk 5 precedent) even though the dry run above
  surfaces it as a real latent gap. A redesign would also newly fail on `bandit_road`'s
  `town_council` case for the first time, which would then require the very exception mechanism
  this investigation shows is currently unnecessary — do not let that tempt an in-ticket
  redesign-plus-exception bundle.
- Do not touch `src/worldassembly/resolver.py` or `src/world/environment.py` — confirmed
  read-only reference throughout this investigation; the `"PHYSICAL"` default and
  `calculate_hazard_drain` are both working as documented.
- Do not fold any of the 4 previously-`HAZARD_KIND_MATCH_WORLDS`-absent-but-now-covered worlds
  into `ANCHORED_WORLD_BANDS`, `EXPECTED_DISTINCT_POPULATED_FACTIONS`, or the entity-count-band
  tests — unrelated concerns, explicitly out of scope.
- Do not modify `test_hazard_kind_completeness` or its `HAZARD_KIND_COMPLETENESS_WORLDS` list —
  a different test/list, unmodified-behavior AC.
- Do not add a broad/wildcard exception mechanism even though this investigation found the
  narrow one is not needed — if a future implementer misreads this and adds one preemptively
  "just in case," that violates the ticket's explicit Scope guardrail (line 57).
- Do not edit `docs/guidelines/intentional_divergences.md` §2.30 itself — that document is owned
  by `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` and is Out of Scope here; only *cite* it in a code
  comment.
