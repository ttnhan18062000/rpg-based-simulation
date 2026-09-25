---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW
artifact_type: plan
tags: [architecture, schema, registry, combat]
---

# Implementation Plan — TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW

## Summary

This plan writes Combat/Conflict's real Rule↔Mechanism mapping (10 of the 12 real Rule IDs get a
disposition of "mapped," 2 stay `UNKNOWN` with a written reason — never a silent 12/12), extends
the existing Territory generator in place to also render a combined two-domain management view,
writes the short honest comparison directly into that generated view, adds the citation-rule
sentence to `architecture.md` §3, closes the roadmap's M4 section and the epic's milestone table,
fixes the one cosmetic `core_rpg_design_direction.md` run-on paragraph, and reports (does not
define) which §10 terms the view actually needed — which, per direct read of the real generator
source, is none of the eight undefined ones. Every mapping decision below is made from evidence
read directly during this planning pass (file:line citations given per edge), not copied from
`investigation.md`'s own candidate list without re-confirmation — where this plan's own reading
sharpens or diverges from `investigation.md`'s flagged-not-resolved candidates, that is called out
explicitly.

### The 12-ID disposition table (AC1)

| Rule ID | Disposition | Mechanism(s) | Edge type | Classification |
|---|---|---|---|---|
| `CONFLICT-01` | **UNKNOWN — no row** | none | — | — |
| `PERC-01` | Mapped | `tactical_decision` | `PARTIALLY_REALIZES` | `PARTIAL` |
| `KNOW-01` | Mapped | `tactical_decision` | `PARTIALLY_REALIZES` | `PARTIAL` |
| `AGENCY-01` | Mapped | `tactical_decision` | `PARTIALLY_REALIZES` | `PARTIAL` |
| `AGENCY-02` | Mapped | `combat_engagement` | `PARTIALLY_REALIZES` | `PARTIAL` |
| `AGENCY-04` | Mapped | `combat_resolution` | `PARTIALLY_REALIZES` | `PARTIAL` |
| `LIFE-01` | Mapped | `combat_resolution`, `movement` | `PARTIALLY_REALIZES` (both) | `PARTIAL` |
| `LIFE-02` | Mapped | `combat_resolution`, `movement` | `PARTIALLY_REALIZES` (both) | `PARTIAL` |
| `BODY-07` | Mapped | `combat_resolution` | `CONSTRAINED_BY` | `PARTIAL` |
| `OWN-02` | Mapped | `combat_resolution` | `CONSTRAINED_BY` | `PARTIAL` |
| `CAP-01` | Mapped | `combat_resolution` | `PARTIALLY_REALIZES` | `PARTIAL` |
| `ECOL-04` | **UNKNOWN — no row** | none | — | — |

10 mapped Rule IDs, 12 edges, 10 classification rows, all `PARTIAL`. This is not a forced-clean
result and not a forced-uniform one either — see "Why every mapped Rule lands on `PARTIAL`, not a
mix" below and the written comparison (Step 12) for why this is the honest outcome, not a
manufactured one.

### Why `CONFLICT-01` and `ECOL-04` stay `UNKNOWN` (not a cross-system edge)

Read directly this session, `docs/world_rules/capability-progression/conflict-combat.md:45-54`:
`CONFLICT-01`'s own "Repository evidence" names three things — `ResourceOpportunityProvider`'s
reward scaling, an `AGENCY-01`-evidenced `blocker_penalty`, and `ECOL-04`'s own regional-
scarcity/migration feedback. Grepped `registries/mechanisms.yaml` directly this session for the
exact strings `ResourceOpportunityProvider`, `blocker_penalty`, `migration`, `ecology`, and
`scarcity`: **zero hits for every one of them.** These are class/field names from the Rule's own
prose, not registered `mechanism_id`s, and no registered mechanism's `implemented_by` cites either
class. `investigation.md` flagged `resource_harvesting` (`registries/mechanisms.yaml:2489`,
`systems: [economy]`, binds to `HarvestSystem`, `state: orphan`) and `regional_trauma`
(`registries/mechanisms.yaml:1948`, `systems: [world]`, binds to `RegionalConsequenceService`) as
subject-matter-adjacent candidates but did not resolve the question. Having now checked: **neither
is the mechanism `CONFLICT-01`'s own text actually names.** `HarvestSystem` is not
`ResourceOpportunityProvider`; `RegionalConsequenceService`'s `trauma_score` accumulation is not a
migration/scarcity feedback mechanism. Writing an edge to either would assert an identity between
the Rule's own cited evidence and an unrelated registered mechanism based on subject-matter
similarity alone — exactly the "infer identity from a similar-looking name" failure this
plan must not commit, and it would also be a category error on its own terms: `CONFLICT-01`'s
entire point is that these outcomes are resolved **without** any Combat mechanism (`"Combat is one
Conflict-resolution mechanism this repository implements, not the only legitimate shape Conflict
may take"`) — mapping it to a Combat-domain mechanism would misstate the Rule's own claim regardless
of which mechanism was picked. `ECOL-04`'s own regional-scarcity/migration mechanism is the same
unresolved-name problem and inherits the same disposition. **Decision: both stay `UNKNOWN`, no
edge or classification row for either.** This is the one place this plan diverges from writing a
row for every candidate `investigation.md` surfaced — a genuinely unresolvable citation is not the
same as an unmapped Rule with no evidence at all, and forcing a row here would be worse than
leaving it honestly `UNKNOWN`.

### Why every mapped Rule lands on `PARTIAL`, not a mix of `SUPPORTED`/`CONFLICTING`/`UNKNOWN`

This is a real, evidence-driven outcome, not a manufactured "safe middle" to avoid taking a
position (which AC7 forbids just as much as manufacturing a clean contrast):

- **`PERC-01`/`KNOW-01`/`AGENCY-01`** map to `tactical_decision`, whose own live `verified.verdict`
  is `contradicted` (`registries/mechanisms.yaml:189-247`, re-confirmed by direct read this
  session) — the perception-gated targeting the Rule requires is real, correctly-wired code
  (`src/engine/tactical.py:196-199`, `_gate.can_perceive(...)`, confirmed by direct read this
  session), but the branch it gates (`ATTACK`-intent) is a textbook STARVED case per
  `docs/plans/status_axis_model.md` §4 — 0 of 1130 real corpus calls had a non-empty `hostiles`
  list. A real, correct gate that almost never actually gates anything in real play is neither
  `SUPPORTED` (the guarantee isn't robustly demonstrated in practice) nor `CONFLICTING` (nothing
  demonstrates it doing the wrong thing) — `PARTIAL` is the honest middle **for a real reason**, not
  a hedge. A second, independent reason applies to all three: the `try/except Exception: pass`
  fail-open fallback around the same gate call (`src/engine/tactical.py:196-200`, `conflict-
  combat.md`'s own Open Question #2, explicitly unresolved and out of this ticket's scope to
  decide) means the gate's enforcement is not airtight in every code path, even when the branch
  does fire.
- **`AGENCY-02`** maps to `combat_engagement`, whose `EngagementRiskEvaluator.caution = max(0.0,
  min(1.0, 1.0 - bravery))` (`src/domains/combat_engagement/risk_evaluator.py:56`, confirmed by
  direct read this session) is a real, correct, code-level separation of estimation from
  consideration — but `combat_engagement`'s own `verified.note` (`registries/mechanisms.yaml:248-
  284`) states the "1960 → 837" positive evidence is `metropolis`-specific; in the three real
  corpus worlds this path sees 0-2 calls per 1000-2000 ticks regardless of this gate's state,
  because the path it governs is the same one `tactical_decision` above found dormant. Same
  PARTIAL reasoning: real, correct code, weakly exercised in real play.
- **`AGENCY-04`/`CAP-01`** map to `combat_resolution`. Its own value-differential evidence
  (`registries/mechanisms.yaml:169-188`) confirms `calculate_damage()` is a **deterministic,
  no-RNG** function of `combat.atk`/`combat.def_stat` — a real, wired mechanism, but one whose
  own pure damage math translates capability fairly directly into outcome. The Rule's actual claim
  ("context, environment, resources, decision quality may still produce an unfavorable outcome for
  the nominally stronger side") is only partly realized by `combat_resolution` alone; the rest of
  that claim's real support (tactical positioning/posture gating) lives in `combat_engagement`'s
  own risk gate, a separate mechanism already carrying its own dormancy caveat above — `PARTIAL`
  reflects that the claim's realization is split across mechanisms and incomplete within any one
  of them, not a hedge.
- **`LIFE-01`/`LIFE-02`** map to both `combat_resolution` (`src/engine/combat.py:147-233`, real
  `outcome_kind` values `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`/`SURVIVE`/`REJECTED`, confirmed by
  direct read this session) and `movement` (`src/engine/movement.py:216-219`,
  `"combat_escape": "EVASIVE_SUCCESS"`, confirmed by direct read this session, the seventh
  withdrawal outcome). This is the exact TERR-05 shape from M1: a real, live, differentiated
  mechanism for most of the Rule's scope, plus a **confirmed** (not unlooked-at) absence for the
  rest — `conflict-combat.md:126-130` states directly, "Confirmed MISSING, checked directly: no
  surrender, capture, or forced-displacement-as-a-combat-outcome exists." `PARTIAL`, matching M1's
  own precedent for exactly this "real edge, one confirmed-absent clause" shape.
- **`BODY-07`/`OWN-02`** map to `combat_resolution` via `CONSTRAINED_BY` (per
  `architecture.md` §3's own definition: "the Rule bounds how this mechanism may behave, without
  the mechanism being the Rule's primary realization" — exactly this boundary claim).
  `combat_resolution`'s own `outcome_kind` assignments confirm Combat's own producer-side half is
  real (it produces events; it does not itself write bodily-consequence state anywhere in
  `src/engine/combat.py`, confirmed by direct read this session). The actual consequence-*owning*
  mechanism is Life/Body's own domain, entirely outside Combat's 8 registered mechanisms and
  outside this ticket's own investigated scope (Out of Scope: no third domain). A real, confirmed
  half plus a genuinely uninvestigated other half is `PARTIAL`, not `UNKNOWN` (something real was
  found and evidenced) and not `SUPPORTED` (the consumer side has not been independently
  confirmed by this ticket, and asserting it works without checking would be exactly the kind of
  unevidenced claim this plan must not make).

**A separate, explicitly out-of-scope note**: Batch 06's own domain has two already-documented
`CONFLICTING` findings against `ResourceOpportunityProvider`/`HarvestScorer` for this same general
perception/agency Rule family (`conflict-combat.md:96-97`), which have never been formally mapped
into `rule_mechanism_edges.yaml`/`rule_classifications.yaml` (confirmed zero existing rows for any
non-`TERR-*` `rule_id` today). Per the shared-Rule-ID-across-domains model
(`architecture.md` §3, `roadmap.md` Assumptions #2), a Rule's classification is a judgment over
what is **actually mapped today**, not omniscient knowledge of prose findings elsewhere that this
ticket's own Scope forbids investigating (Out of Scope: no third domain). If/when Batch 06's own
mapping pass writes those `CONFLICTING`-worthy edges, the affected Rules' classifications may need
revisiting then — that is a future ticket's job, not something to pre-empt here by reasoning from
knowledge not yet formally mapped.

### Extend-vs-new-file decision (Assumption #1)

**Decision: extend `tools/semantic_control_plane/generate_territory_control_view.py` in place —
do not write a new module, do not rename the existing file/output/Make target.**

Justification in one paragraph: direct read of the real file
(`tools/semantic_control_plane/generate_territory_control_view.py:43-144`) confirms
`investigation.md`'s own finding — `build_territory_view`'s per-Rule loop body (`_edges_for_rule`,
`_classification_for_rule`, `_verification_cell`, the implementation-cell join) contains **zero**
Territory-specific logic; the only two Territory-specific things in the whole file are the
`_TERR_RULE_IDS` list constant and the `_DESIGN_VALUE` citation string. Generalizing this to a
second domain is therefore a strictly additive change (a second Rule-ID constant, a second
`_DESIGN_VALUE`-shaped constant, and a thin new function that calls the existing per-Rule logic
twice and combines the counts) — not a rewrite, and not a reason to introduce a second file that
would duplicate the exact same row-building code. Renaming the existing module/output/Make target
away from "territory" was considered and rejected: it would touch `test_territory_control_view.py`'s
own imports and the committed `docs/brainstorm/territory_control_management_view.md` path for no
functional gain, and this roadmap's own M4 is explicitly a **two-domain proof**, not a promise of a
fully domain-agnostic renderer for an unbounded future N — building that generality now would be
exactly the kind of ahead-of-evidence infrastructure `architecture.md` §9's non-goals already warn
against (no Context Compiler before real query patterns exist; the same discipline applies here).
Concretely: Territory's own existing CLI invocation (`python3 .../generate_territory_control_view.py`,
no flags) keeps producing byte-identical output through the exact same `render()`/`main()` code
path, untouched; a new `--combined` flag on the same `main()` and two new functions
(`build_cross_domain_view()`, `render_cross_domain()`) add Combat + the combined rendering without
touching a single line of the existing Territory-only path.

## Steps

### Step 1 — Live re-check #1: `tactical_decision`'s verdict and the paused hostility sweep (AC3)

**Files:** none changed (verification-only step, run before any registry write)

**Change:** Re-run, right now, the exact checks `investigation.md` already ran, independently,
before trusting any of this plan's own `tactical_decision`-dependent evidence text (Step 5):

```
python3 - <<'PY'
import yaml
d = yaml.safe_load(open("registries/mechanisms.yaml"))
m = next(x for x in d["mechanisms"] if x["id"] == "tactical_decision")
print(m["state"], m["verified"]["instrument"], m["verified"]["verdict"], m["verified"]["date"])
PY
ls tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md tickets/inprogress/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md tickets/done/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md 2>&1
grep -n "^## Status" tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md
```

Expected (per `investigation.md`, dated today): `state=done`, `verdict=contradicted`,
`date=2026-09-19`; the ticket file exists only under `tickets/todos/` with `## Status` = `OPEN`. If
either check disagrees with this, **stop** — do not proceed to Step 5 with stale evidence text;
re-derive the affected classification(s) and record what was actually found, not what was expected.

**Do NOT touch:** Nothing to touch — read-only step.

**Verify:** Both commands run and their output is recorded (paste it) in the ticket's own
`## Implementation Notes` alongside Step 8's second re-check (AC3 requires the *found* state
recorded, not a citation of this document).

---

### Step 2 — Write the 12 real `rule_mechanism_edges.yaml` rows for Combat

**Files:** `registries/rule_mechanism_edges.yaml`

**Change:** Append 12 rows (do not touch the existing 6 TERR rows). Each row's `mechanism_id` is
confirmed to already resolve in `registries/mechanisms.yaml` today (`combat_resolution:123`,
`tactical_decision:189`, `combat_engagement:248`, `movement:285`, all read directly this session)
and each `rule_id` is confirmed to resolve via `scan_rule_ids()` per `investigation.md`'s own
independently-re-derived table. Evidence text per row (condensed from the Summary's own reasoning
above — full reasoning lives there, not duplicated at row-length in the YAML):

1. `PERC-01` → `tactical_decision`, `PARTIALLY_REALIZES`. Evidence: perception-gated targeting —
   `PerceptionGate.can_perceive(...)` (`src/engine/tactical.py:196-199`) runs before any neighbor
   becomes target-eligible, cited by `tactical_decision`'s own registry note
   (`registries/mechanisms.yaml:234-247`) and `conflict-combat.md:91-95`; caveated by the
   `try/except Exception: pass` fail-open fallback (`tactical.py:196-200`) and by the branch's own
   STARVED dormancy (0 of 1130 real corpus calls had non-empty `hostiles`,
   `registries/mechanisms.yaml:216-217`). Date `2026-09-24`.
2. `KNOW-01` → `tactical_decision`, `PARTIALLY_REALIZES`. Same evidence as row 1 —
   `conflict-combat.md:69-70` states perception AND knowledge must both route through the same
   gate; this is the knowledge-side citation of the identical live mechanism. Date `2026-09-24`.
3. `AGENCY-01` → `tactical_decision`, `PARTIALLY_REALIZES`. Same evidence as row 1 — decision
   stages must not read hidden state directly; the same perception gate is what forecloses that
   shortcut for Combat's own targeting path. Date `2026-09-24`.
4. `AGENCY-02` → `combat_engagement`, `PARTIALLY_REALIZES`. Evidence: `EngagementRiskEvaluator`
   (`src/domains/combat_engagement/risk_evaluator.py:56`, `caution = max(0.0, min(1.0, 1.0 -
   bravery))`) keeps the capability estimate itself untouched by bravery, changing only the
   resulting `risk_score`/`CombatPosture` — a direct instance of "influence, not determination";
   caveated by `combat_engagement`'s own world-specificity note
   (`registries/mechanisms.yaml:261-269`) — the gated path this evaluator feeds only measurably
   fires in the synthetic `metropolis` reference scenario, 0-2 calls/1000-2000 ticks elsewhere.
   Date `2026-09-24`.
5. `AGENCY-04` → `combat_resolution`, `PARTIALLY_REALIZES`. Evidence:
   `calculate_damage()`'s confirmed, no-RNG, deterministic response to `combat.atk`/
   `combat.def_stat` (`registries/mechanisms.yaml:169-188`,
   `tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py`) is real
   mechanical support for capability mattering to outcome, but the Rule's full "may still lose"
   claim (context/decision-quality/resources) is only partly covered by this one mechanism's own
   deterministic formula — the rest of that claim's support lives in `combat_engagement`'s
   separate risk gate (row 4), not inside this mechanism. Date `2026-09-24`.
6. `CAP-01` → `combat_resolution`, `PARTIALLY_REALIZES`. Same evidence as row 5 —
   `conflict-combat.md:154-159` cites this as the same Inherited entry reusing both `CAP-01` and
   `AGENCY-04`; both are independently citable foreign keys per the citation rule (Step 9), same
   underlying evidence, not a copy-paste duplicate (distinct `rule_id`, same as M1's
   `TERR-01`/`TERR-03` → `betrayal_siege_war` precedent). Date `2026-09-24`.
7. `LIFE-01` → `combat_resolution`, `PARTIALLY_REALIZES`. Evidence: `src/engine/combat.py`'s real
   `outcome_kind` assignments (`:147,164-172,185-188,233`, confirmed by direct read this session) —
   `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`/`SURVIVE`/`REJECTED`, a genuine differentiated
   vocabulary satisfying "incapacitated ≠ dead." `PARTIALLY_REALIZES` because the Rule's own scope
   (per `conflict-combat.md:126-130`) also names surrender/capture/forced-displacement, which no
   mechanism covers (see the classification's own `MISSING`-sub-clause reasoning). Date
   `2026-09-24`.
8. `LIFE-01` → `movement`, `PARTIALLY_REALIZES`. Evidence: `src/engine/movement.py:216-219`,
   `"combat_escape": "EVASIVE_SUCCESS"` — the seventh, withdrawal outcome `conflict-combat.md:124-
   126` explicitly adds beyond Batch 05's own six. `PARTIALLY_REALIZES` for the same
   confirmed-missing-clause reason as row 7. Date `2026-09-24`.
9. `LIFE-02` → `combat_resolution`, `PARTIALLY_REALIZES`. Same evidence as row 7, cited
   independently for `LIFE-02`'s own foreign key (both `LIFE-01`/`LIFE-02` are cited together by
   this one Inherited entry, per the citation rule). Date `2026-09-24`.
10. `LIFE-02` → `movement`, `PARTIALLY_REALIZES`. Same evidence as row 8, independent citation.
    Date `2026-09-24`.
11. `BODY-07` → `combat_resolution`, `CONSTRAINED_BY`. Evidence: `src/engine/combat.py`'s
    `outcome_kind`/`CombatUpdate` construction (`:147-233`, confirmed by direct read this session)
    produces triggering events only — no line in `src/engine/combat.py` writes bodily-consequence
    state (life/body fields) directly; the Rule bounds this mechanism's own scope (producer-only)
    without this mechanism being the Rule's primary realization (that owner is Life/Body's own
    domain, outside Combat's 8 mechanisms and this ticket's investigated scope). Date `2026-09-24`.
12. `OWN-02` → `combat_resolution`, `CONSTRAINED_BY`. Same evidence as row 11, independent
    citation — this Inherited entry cites both `BODY-07` and `OWN-02` together
    (`conflict-combat.md:139-142`). Date `2026-09-24`.

Also add one header-comment block (mirroring M1's own convention) recording that `CONFLICT-01` and
`ECOL-04` were investigated and deliberately left `UNKNOWN` — see the Summary's own reasoning — so
a future mapper does not re-investigate the same dead end from scratch.

**Do NOT touch:** The existing 6 `TERR-*` rows (Territory's own committed mapping) — zero edits
anywhere above the new Combat block. Do not write any row for `CONFLICT-01` or `ECOL-04`. Do not
write a row citing `resource_harvesting`, `regional_trauma`, `ResourceOpportunityProvider`, or
`blocker_penalty` — none of these resolves to real, on-point evidence per the Summary's own
reasoning.

**Verify:** `python3 tools/semantic_control_plane/registry.py` — zero new violations attributable
to this step (a `rule_id` with no matching `rule_classifications.yaml` record is not an error;
confirm any reported violation, if present, is pre-existing/unrelated).

---

### Step 3 — Add the corpus-guard and evidence-quality tests (part 1)

**Files:** `tests/unit/tools/test_semantic_control_plane_schema.py`

**Change:** Add, per `test_plan.md`'s New Tests Required:
- `test_all_twelve_combat_rule_ids_resolve_against_the_live_corpus` (item 2) — asserts
  `scan_rule_ids()` resolves all 12 named IDs and that `CONFLICT-02` is absent from the set.
- `test_combat_rule_mechanism_edges_have_nonempty_evidence_and_date` (item 3) — asserts every
  Combat `rule_id` written in Step 2 has a non-empty `evidence` and a `YYYY-MM-DD` `date`.
- `test_rule_mechanism_edge_shared_rule_id_across_domains_is_not_a_duplicate` (item 1) — a
  **synthetic** fixture (not Step 2's real data): two edges sharing one `rule_id` (e.g. a made-up
  `PERC-01` row citing a made-up Perception-domain `mechanism_id` plus a second real `PERC-01` row
  citing `tactical_decision`), asserting both validate cleanly. Per `test_plan.md`'s own anti-drift
  guard, this must be a genuinely different-provenance pair, not a copy-paste same-file duplicate
  with a different `edge_type` (that is already covered by the existing
  `test_rule_mechanism_edge_same_pair_different_edge_type_is_not_a_duplicate`).

**Do NOT touch:** `test_no_function_derives_classification_from_edges` — leave unmodified.

**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py -v` — all three new
tests green against Step 2's real data (first two) and a synthetic fixture (third).

---

### Step 4 — Live re-check #2: re-confirm before writing classifications (AC3, required immediately before finalizing)

**Files:** none changed (verification-only step)

**Change:** Re-run the **identical** two checks from Step 1, one more time, right now — not a
reuse of Step 1's already-printed output. This is the ticket's own explicit AC3 requirement ("at
execution time," immediately before the final classification write) and is not satisfied by
Step 1 alone if any time has passed or any other agent could have touched `registries/
mechanisms.yaml` or `tickets/todos/` in between. If the result differs from Step 1's, stop and
report before Step 5 — do not silently write classification rows against a verdict that already
moved out from under this plan.

**Do NOT touch:** Nothing — read-only step.

**Verify:** Record both re-checks' output (Step 1's and Step 4's) side by side in the ticket's own
`## Implementation Notes`, confirming they agree, before Step 5 proceeds.

---

### Step 5 — Write the 10 real `rule_classifications.yaml` rows

**Files:** `registries/rule_classifications.yaml`

**Change:** Append 10 rows, one per mapped Rule ID (`CONFLICT-01`/`ECOL-04` get none), each
`classification: PARTIAL`, `review_date: "2026-09-24"`, evidence text summarizing the per-Rule
reasoning already spelled out in the Summary above (do not re-derive at implementation time — copy
the reasoning, cite the same file:line evidence already gathered in Step 2's edges). Written as a
**separate pass after Step 2's edges are already on disk and validator-clean** — same sequencing
discipline `validate_rule_classifications()`'s own docstring requires and M1's own plan already
established.

**Do NOT touch:** The existing 4 `TERR-*` rows. Do not write a second row for any already-present
`rule_id`. Do not derive any of these 10 values mechanically from Step 2's `edge_type` column —
each is its own human judgment call, using the edges only as cited evidence (this is exactly what
`test_no_function_derives_classification_from_edges` exists to catch if violated in code, but the
same discipline applies to how a human writes the YAML by hand too).

**Verify:** `python3 tools/semantic_control_plane/registry.py` and
`pytest tests/unit/tools/test_semantic_control_plane_schema.py::test_all_three_schemas_pass_on_real_seed_data -v`
— zero errors.

---

### Step 6 — Full existing-validator regression confirmation (AC2)

**Files:** none changed (verification-only step)

**Change:** Run the full existing regression surface named in `test_plan.md`:
`test_all_three_schemas_pass_on_real_seed_data`, `test_documented_cli_invocation_actually_runs`,
`test_no_function_derives_classification_from_edges`, `test_rule_id_scanner_finds_known_rule_ids`,
`test_rule_mechanism_edge_same_pair_different_edge_type_is_not_a_duplicate`,
`test_validator_rejects_duplicate_rule_mechanism_edge_type_triple`. AC2 requires "zero manual
overrides of a reported violation" — if any violation appears, return to Step 2 or 5 and fix the
data, never edit `registry.py`'s validation logic to accommodate it.

**Do NOT touch:** `tools/semantic_control_plane/registry.py`, `tools/semantic_control_plane/rule_catalog.py`
— zero code changes to either file anywhere in this ticket.

**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py -v` full file green;
`python3 tools/semantic_control_plane/registry.py` exits 0 printing `OK`.

---

### Step 7 — Extend `generate_territory_control_view.py` in place for Combat + the combined view

**Files:** `tools/semantic_control_plane/generate_territory_control_view.py`

**Change:** Additive only (per the extend-vs-new-file decision above):
- Add `_COMBAT_RULE_IDS = ["CONFLICT-01", "PERC-01", "KNOW-01", "AGENCY-01", "AGENCY-02",
  "AGENCY-04", "LIFE-01", "LIFE-02", "BODY-07", "OWN-02", "CAP-01", "ECOL-04"]` — all 12, including
  the 2 `UNKNOWN` ones (the existing `_classification_for_rule`/row-building logic already renders
  an absent-record Rule ID with `REALIZATION: UNKNOWN`, `IMPLEMENTATION: none`, `VERIFICATION:
  0/0 (n/a)` with zero new code — confirmed by direct read of `build_territory_view`'s existing
  per-rule loop, `:103-134`). Rendering `CONFLICT-01`/`ECOL-04` this way, rather than omitting them,
  is itself the AC1 anti-drift guard made visible in the view, not just the registry.
- Add `_COMBAT_DESIGN_VALUE`, citing `conflict-combat.md`'s own frontmatter
  (`status: authoritative`, `last_verified: "2026-09-23"`) and header (`**Status.** Batch 07
  (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day...`), mirroring
  `_DESIGN_VALUE`'s exact shape.
- Refactor the shared per-Rule-ID row-building body out of `build_territory_view` into a new
  private helper `_build_rows(rule_ids, design_value, rule_mechanism_data, classifications_data,
  registry)` returning `(rows, mapped, verified_rules, classification_counts)` — `build_territory_view`
  becomes a one-line call to this helper with `_TERR_RULE_IDS`/`_DESIGN_VALUE`, so its own
  externally-observed behavior (and therefore `test_real_territory_view_is_up_to_date`'s byte-for-
  byte guarantee) is unchanged.
- Add `build_cross_domain_view(rule_mechanism_data, classifications_data, registry)` calling
  `_build_rows` twice (once per domain) and combining: `territory` and `combat` sub-results kept
  separate (each domain's own `rows`/`mapped`/`unmapped`/`verified`/`unverified`/
  `classification_counts`), plus one combined top-level `mapped`/`unmapped`/`verified`/`unverified`
  total across both domains and one combined `classification_counts` dict merging both domains'
  breakdowns.
- Add `render_cross_domain(rule_mechanism_data, classifications_data, registry)` producing: a
  banner, the combined mapped/unmapped + verified/unverified + classification-breakdown lines
  (AC4), then **two separate H2 sections** — `## Territory / Control` (Territory's own existing
  six-axis table, reusing `render()`'s own per-domain table-rendering logic factored into a small
  `_render_domain_section(name, view)` helper) and `## Combat / Conflict` (the same table shape for
  Combat's 12 rows) — never one merged table forcing both domains' differently-shaped `DESIGN`
  citations into one row shape (this is the concrete form of AC7's "two structurally different
  domains... without distorting either into the same shape"). Then a `## Comparison` section — see
  Step 12.
- Extend `main()`'s `argparse` with a `--combined` flag; when passed, `--output` defaults to
  `docs/brainstorm/cross_domain_management_view.md` instead of the Territory-only default, and
  `main()` calls `render_cross_domain(...)` instead of `render(...)`. Territory's own invocation
  (no flag) is byte-for-byte unchanged — same default output path, same `render()` call, same
  `--check` behavior.

**Do NOT touch:** `render()`'s or `main()`'s existing Territory-only code path's observable
behavior — every existing call with no `--combined` flag must produce identical output to before
this step. Do not fold `_TERR_RULE_IDS`/`_DESIGN_VALUE` into a single ambiguous "current domain"
global; keep both domains' constants named and separate.

**Verify:** `python3 tools/semantic_control_plane/generate_territory_control_view.py --output /tmp/terr_check.md`
(no flag) still produces output byte-identical to the committed
`docs/brainstorm/territory_control_management_view.md`. `python3 tools/semantic_control_plane/generate_territory_control_view.py --combined --output /tmp/combined_check.md`
runs without error and contains both `## Territory / Control` and `## Combat / Conflict` sections.

---

### Step 8 — Wire the `cross-domain-management-view` Makefile target

**Files:** `Makefile`

**Change:** Add, alongside the existing `territory-control-view` target:
```
cross-domain-management-view: ## Regenerate docs/brainstorm/cross_domain_management_view.md (Territory + Combat, architecture.md §8's six axes, both domains)
	$(PYTHON3) tools/semantic_control_plane/generate_territory_control_view.py --combined
```

**Do NOT touch:** The existing `territory-control-view` target — add only, do not fold the two
targets into one or change what `territory-control-view` invokes.

**Verify:** `make cross-domain-management-view` runs successfully and writes
`docs/brainstorm/cross_domain_management_view.md`; `make territory-control-view` still runs and
still writes byte-identical content to the already-committed Territory file.

---

### Step 9 — Generate the real combined view file and reconfirm Territory's file is untouched

**Files:** `docs/brainstorm/cross_domain_management_view.md` (new, generated)

**Change:** Run `make cross-domain-management-view` against the now-fully-populated registries
(Steps 2 and 5). Commit the generated output as-is, never hand-edited, matching every other
generated-view precedent in `docs/brainstorm/`.

**Do NOT touch:** `docs/brainstorm/territory_control_management_view.md` — confirm with `git diff
docs/brainstorm/territory_control_management_view.md` that it shows zero changes after this step
(the Anti-Drift Hazard: "Do not let the cross-domain view's Territory rows change").

**Verify:** `python3 tools/semantic_control_plane/generate_territory_control_view.py --check`
(Territory-only, no flag) still reports `OK`. The new combined file contains all 4 Territory Rule
IDs and all 12 Combat Rule IDs (including `CONFLICT-01`/`ECOL-04` rendered `UNKNOWN`), the combined
mapped/unmapped and verified/unverified counts, and a classification breakdown.

---

### Step 10 — Add the cross-domain view tests

**Files:** `tests/unit/tools/test_cross_domain_management_view.py` (new file)

**Change:** Add, per `test_plan.md`'s New Tests Required:
- `test_cross_domain_view_renders_both_domains` (item 4) — asserts all 4 Territory IDs and all 12
  Combat IDs appear, across the six axes, in the real generated output.
- `test_cross_domain_view_shows_raw_counts_not_bare_percentage` (item 5) — asserts raw
  mapped/unmapped and verified/unverified counts are present alongside the classification
  breakdown, and that no single collapsed percentage/badge appears anywhere in the combined
  output (mirrors the existing Territory-only guard, applied to both domains together).
- `test_combat_mixed_realization_is_not_smoothed_into_a_clean_result` (item 6) — asserts Combat's
  own rows in the real generated output contain at least one non-`SUPPORTED` classification
  (`PARTIAL` in this plan's own real result) and at least one `UNKNOWN` (`CONFLICT-01`/`ECOL-04`) —
  a direct, mechanical AC7 guard against this exact mapping being quietly "cleaned up" later.

**Do NOT touch:** `tests/unit/tools/test_territory_control_view.py` — its own assertions about
Territory's four rows stay exactly as they are; this is a new file, not an edit to that one.

**Verify:** `pytest tests/unit/tools/test_cross_domain_management_view.py -v` — all three tests
green.

---

### Step 11 — Add the `architecture.md` §3 doc-coverage regression test

**Files:** `tests/unit/tools/test_semantic_control_plane_schema.py`

**Change:** Add `test_architecture_md_section_3_documents_inherited_entry_citation_rule` (item 7)
— asserts §3's text states that an Inherited/Applied Foundational entry is cited under the
original Rule ID it derives from. Write this test **before** Step 13's doc edit so it fails first
(red), then passes once Step 13 lands — the same red-then-green discipline this repo's own CI-
wiring precedent requires for every new check.

**Do NOT touch:** The existing §3-content tests
(`test_architecture_md_no_longer_says_deliberately_undecided`,
`test_architecture_md_section_3_names_chosen_schema`).

**Verify:** Test fails now (§3 does not yet contain the sentence); re-run after Step 13 to confirm
it turns green.

---

### Step 12 — Write the honest comparison directly into the generated combined view

**Files:** `tools/semantic_control_plane/generate_territory_control_view.py`

**Change:** Add a `## Comparison` section, rendered by `render_cross_domain()` (Step 7), containing
a short, hand-written prose constant (the comparative facts are stable findings from this planning
pass, not something to recompute from the registries every regeneration — matching how
`_DESIGN_VALUE`/`_COMBAT_DESIGN_VALUE` are already hand-written citation strings baked into this
same script). Content, stated honestly per AC7 (this is not draft prose to soften later):

- Territory is `0/4` verified (every mapped mechanism is `code_trace`-only) with a classification
  breakdown of 2 `CONFLICTING`, 2 `PARTIAL`. Combat is `10/10` verified **at the Rule level**
  (every mapped Rule has at least one runtime-verified mechanism among its own mapped set) with a
  classification breakdown of 10 `PARTIAL`, 2 `UNKNOWN` — but this is not uniform at the
  *mechanism* level: `combat_resolution` (`scenario`) and `tactical_decision` (`corpus_run`) and
  `combat_engagement` (`scenario`) all carry a runtime instrument, while `movement` — cited
  alongside `combat_resolution` on both `LIFE-01` and `LIFE-02` — is `code_trace`-only. Every one
  of Combat's mapped Rules still clears the Rule-level bar only because `movement` is never a
  Rule's *sole* mapped mechanism; stated as "every mapped mechanism" without that caveat would be
  false.
- **The inconvenient part, stated plainly**: Combat's much higher verified-count is not evidence
  Combat is "more done" than Territory. `tactical_decision` — the mechanism most of Combat's mapped
  Rules cite — is verified by a real corpus run and that same run is exactly what proved its
  `ATTACK`-intent branch essentially never fires in real play (`verified.verdict: contradicted`).
  A high verified-count and a real problem coexist on the same mechanism. This is the same lesson
  `architecture.md` §2 already states from the `combat_judgement` precedent ("implemented" and
  "actually works" are different claims) showing up again one axis over: "has runtime evidence"
  and "the evidence is good news" are also different claims, and this view's own raw-counts
  discipline (never a percentage alone) is what makes that visible instead of hidden behind a
  single "10/10 verified" headline.
  - Neither domain came out "cleaner" than the other by design — Territory's `CONFLICTING` rows
    are a real semantic violation (an overloaded field slot); Combat's `PARTIAL` rows are a real,
    correctly-built-but-under-exercised mechanism. Both are real findings, differently shaped, and
    this view represents each faithfully rather than collapsing them into one comparable score.

**Do NOT touch:** Any registry file in this step — this is a rendering/prose-only addition to the
generator script.

**Verify:** `make cross-domain-management-view` re-run; the committed output contains the
`## Comparison` section with the exact counts stated above.

---

### Step 13 — `architecture.md` §3: document the inherited-entry citation rule

**Files:** `docs/plans/simulation_semantic_control_plane/architecture.md`

**Change:** Add one sentence to §3 (after the existing "Where it lives" paragraph, before "Two
distinct records, not one"): *"An Inherited / Applied Foundational entry in the World Rule
Catalog — one that reuses an earlier batch's Rule ID rather than being admitted as its own new
Rule — is cited in this mapping under that original Rule ID; it never receives a new local ID of
its own, since direct reuse of an earlier Rule ID is itself the entry's citable identity."*

**Do NOT touch:** Any other section of `architecture.md`; do not also edit the World Rule Catalog's
own admission-discipline section (that rides on `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`,
not this ticket, per the ticket's own Scope item 4).

**Verify:** Step 11's test now passes.

---

### Step 14 — `roadmap.md` M4 section update (AC9)

**Files:** `docs/plans/simulation_semantic_control_plane/roadmap.md`

**Change:** Update the M4 section's status to record: Combat/Conflict mapped (10 of 12 real Rule
IDs, 2 `UNKNOWN` with a written reason), the combined cross-domain view generated, the comparison
written honestly (not manufactured clean), and — the specific AC9 wording requirement — state
plainly that **this roadmap is now complete** while the underlying **mapping itself is not
finished**: Stages D (ongoing per-ticket expansion), E (broader multi-domain view as coverage
grows), and F (Context Compiler, gated on real query patterns) all continue per `rollout_plan.md`,
unaffected by this roadmap's own bounded M0-M4 scope closing.

**Do NOT touch:** M0/M1/M2/M3's own sections — those milestones' own recorded dispositions do not
change.

**Verify:** Read back the updated M4 section; confirm it does not imply the mapping itself is done
(only that M0-M4's proof-of-generalization goal is met).

---

### Step 15 — Epic ticket's milestone table update (AC9, parent ticket)

**Files:** `tickets/inprogress/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md`

**Change:** Update the M4 row of the milestone table (currently `| M4 — Combat slice +
cross-domain view | not yet created | Gated on M1, M2, and M3's narrow triage only. |`) to point at
this ticket (`TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW`) with a **DONE** disposition
matching Step 14's own roadmap-complete-but-mapping-continues framing. This is the parent epic
ticket, a different file from this ticket's own — edit only the M4 row, nothing else in that
ticket's body (its own closure/disposition as a whole epic is a separate decision for whoever owns
that ticket, not this plan's job).

**Do NOT touch:** Any other row of that table (M0-M3's own recorded dispositions), or any other
section of the epic ticket.

**Verify:** Read back the updated row; confirm it names this ticket ID and states the roadmap-
complete-but-mapping-continues distinction, matching Step 14's own wording.

---

### Step 16 — `core_rpg_design_direction.md` §10 run-on paragraph fix (Scope item 5, first bullet)

**Files:** `docs/brainstorm/core_rpg_design_direction.md`

**Change:** At line 478 (confirmed by direct read this session), insert a blank line between
"...Rule realization axis." and "**Status note (2026-09-24).**" — two paragraphs where there is
currently one, with no other text change. This is a formatting-only fix; the vocabulary itself
(Out of Scope) is not touched.

**Do NOT touch:** Any word of the existing prose — only the paragraph break is added. Do not edit
the vocabulary list itself or add/remove any of the eight undefined terms.

**Verify:** New test from Step 17 passes.

---

### Step 17 — Add the §10 run-on-paragraph regression test

**Files:** a new small test file (e.g. `tests/unit/tools/test_core_rpg_design_direction_docs.py`,
since no existing `tests/unit/tools/` file covers this doc per `test_plan.md`'s own note that none
was found — co-located here rather than a new `tests/unit/docs/` directory, to avoid inventing a
new test directory for one assertion)

**Change:** Add `test_core_rpg_design_direction_section_10_has_no_run_on_paragraph` (test_plan.md
item 8) — asserts a blank line (`\n\n`) separates "...Rule realization axis." from "**Status note
(2026-09-24).**" in the real file.

**Do NOT touch:** Any other doc-coverage test file.

**Verify:** Fails before Step 16, passes after.

---

### Step 18 — Report the §10 terms actually needed (Scope item 5, second bullet) — report only, into this ticket's own body

**Files:** `tickets/inprogress/TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW.md`
(`## Implementation Notes` section)

**Change:** Record the finding, already confirmed by direct read of the real generator source
during investigation and re-confirmed by this plan's own Step 7 additions: **none of the eight
undefined §10 terms** (`MISSING`, `DESIGNED`, `EXPERIMENTAL`, `OFF`, `DORMANT`, `LIVE`,
`DEPRECATED`, `REPLACED`) are needed anywhere in the cross-domain view — every cell in both
`render()` and `render_cross_domain()` draws exclusively from Axis A (`state`), Axis B
(`verified.verdict`/`instrument`), and Axis D (the six-value Rule classification vocabulary). The
one place a §10 term legitimately belongs is the **prose** written comparison (Step 12), where
`STARVED` — the one term with a real existing definition — is the accurate plain-English word for
`tactical_decision`'s situation; Step 12's own comparison text does not currently use it and could,
optionally, but that is a wording choice, not a new requirement. This is a report, not a decision:
no term is defined, pruned, or edited here — that call stays with `world-rule-catalog-design`, per
the ticket's own instruction.

**Do NOT touch:** `docs/brainstorm/core_rpg_design_direction.md`'s §10 vocabulary list itself
(beyond Step 16's blank-line fix) — no term added, removed, or defined.

**Verify:** Read back the filled section; confirm it is a report (what was needed: none) and not a
definition or edit of any term.

---

### Step 19 — Full scoped regression run

**Files:** none changed (verification-only step)

**Change:** Run the combined scoped command:
```
pytest tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_territory_control_view.py \
       tests/unit/tools/test_semantic_control_plane_drift_detector.py \
       tests/unit/tools/test_cross_domain_management_view.py \
       tests/unit/tools/test_mechanism_registry.py \
       tests/unit/tools/test_core_rpg_design_direction_docs.py \
       -v
```

**Do NOT touch:** Do not run repo-wide `pytest tests/`.

**Verify:** All six files green.

---

### Step 20 — Run the drift check against the new rows (AC5)

**Files:** none changed (verification-only step)

**Change:** `make semantic-control-plane-drift-check`. Expected clean (0 cited-code findings, 0
verdict findings) — the new rows are dated `2026-09-24`, and `tactical_decision`'s `contradicted`
verdict predates that date (`2026-09-19`, confirmed Step 1/4), so `check_verdict_drift`'s own
review-time-vs-current comparison finds no drift by construction. **If this reports anything other
than clean, that is a real M2 finding to report as-is — never a date to adjust to silence it**
(the ticket's own AC5 wording).

**Do NOT touch:** `tools/semantic_control_plane/mapping_drift_check.py` — report-only tool, zero
code changes.

**Verify:** Command output recorded in the ticket's `## Test Summary`.

---

### Step 21 — Fill the ticket's closing sections and run done-checker

**Files:** `tickets/inprogress/TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW.md`
(`## Test Summary`, `## Files Changed`, `## Completion Summary`)

**Change:** Record: every test run and its result (Steps 3, 6, 10, 11, 17, 19, 20); the full list
of files changed (Steps 2, 5, 7, 8, 9, 11, 12, 13, 14, 16, 17, plus the epic ticket in Step 15 and
the ticket's own body); a completion summary stating the 12-ID disposition (10 mapped `PARTIAL`, 2
`UNKNOWN`), that the roadmap is complete but the mapping continues under Stage D, and the §10
terms-needed report (none). Then run `done-checker` for this ticket.

**Do NOT touch:** Anything beyond these three sections and the done-checker run itself.

**Verify:** `done-checker` passes; move ticket to `tickets/done/`; migrate staging artifacts to
`stored_artifacts/`.

## Scope Guards

- No third domain, and no mapping of Batch 07's other two files (`capability-progression.md`,
  `learning-adaptation.md`).
- No mapping of the remaining ~46 rule families beyond this ticket's 12 IDs — they stay `UNKNOWN`
  by design.
- No defining or pruning of `core_rpg_design_direction.md` §10's vocabulary — Step 18 is a report,
  never an edit beyond Step 16's blank-line fix.
- No edit to `docs/world_rules/` anywhere, including `conflict-combat.md` itself — frozen,
  read-only for this track.
- No fix for any defect the mapping surfaces (the fail-open perception gate, the two governing
  docs' `±50.0`/`±100.0` disagreement carried from M1, the missing surrender/capture/displacement
  outcome) — record as evidence only, never patch `src/`.
- No resolving `tactical_decision`'s `contradicted` verdict, and no resuming
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — Steps 1/4 only re-check and record
  current state.
- No CI wiring for the drift detector.
- No lineage field added to `mechanisms.yaml`.
- No row written to `mechanism_causal_edges.yaml` — this ticket's own Scope (§1-§5) never asks for
  one; a real `tactical_decision → combat_resolution` causal candidate is visible in the code but
  writing it would exceed this ticket's own explicit deliverables — leave it for a future ticket
  to pick up deliberately, not as a side effect of this one.
- No edge citing `resource_harvesting`, `regional_trauma`, or any mechanism outside Combat's own 8
  registered mechanisms — `CONFLICT-01`/`ECOL-04` stay `UNKNOWN` per the Summary's own reasoning.
- Territory's own 4 rows, 6 edges, 4 classifications, and generated view file must render
  byte-identically to `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE`'s own
  committed output before and after every step in this plan.

## Dependency Map

- Step 1 (live re-check #1) has no dependency; must run before Step 2.
- Step 2 (edges) depends on Step 1's confirmation for the `tactical_decision`-citing rows' evidence
  text; independent of Steps 7-18.
- Step 3 (schema tests part 1) depends on Step 2 for the two real-data tests; the synthetic-fixture
  test is independent of Step 2.
- Step 4 (live re-check #2) depends on Step 1 existing first (it re-runs the same checks); must run
  before Step 5.
- Step 5 (classifications) depends on Steps 2 and 4.
- Step 6 (full validator regression) depends on Steps 2, 3, 5.
- Step 7 (generator extension) depends on Steps 2 and 5 (needs real edge + classification data to
  render Combat's rows) but is otherwise independent of Steps 13-18.
- Step 8 (Makefile target) depends on Step 7.
- Step 9 (generated file) depends on Steps 7 and 8.
- Step 10 (cross-domain view tests) depends on Step 9.
- Step 11 (§3 test, written red) has no data dependency; independent of Steps 2-10.
- Step 12 (comparison prose) depends on Step 7's `render_cross_domain` existing, and on Step 9's
  real counts to state accurately.
- Step 13 (§3 doc edit) turns Step 11's test green; independent of Steps 2-10.
- Step 14 (roadmap.md) depends on Steps 2, 5, 9, 12 all being real and final (it summarizes them).
- Step 15 (epic ticket) depends on Step 14's own wording.
- Step 16 (§10 blank line) and Step 17 (its test) are mutually dependent (red-then-green) but
  independent of every other step.
- Step 18 (§10 terms report) has no code dependency; can happen any time after Step 7 confirms the
  real axes used.
- Step 19 (full regression) depends on every test-adding step (3, 10, 11, 17) and every data step
  (2, 5, 7, 9, 16).
- Step 20 (drift check) depends on Steps 2 and 5 being on disk.
- Step 21 (closing) depends on every prior step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — all 12 Rule IDs enumerated with explicit disposition, `UNKNOWN` valid | Summary's disposition table, Steps 2, 5, 7 | `test_all_twelve_combat_rule_ids_resolve_against_the_live_corpus`, `test_combat_mixed_realization_is_not_smoothed_into_a_clean_result` |
| AC2 — every edge/classification cites real evidence; validator zero manual overrides | Steps 2, 3, 5, 6 | `test_all_three_schemas_pass_on_real_seed_data`, `test_combat_rule_mechanism_edges_have_nonempty_evidence_and_date`, `test_documented_cli_invocation_actually_runs` |
| AC3 — `tactical_decision`/hostility-sweep re-checked at execution time, findings recorded | Steps 1, 4 | Recorded directly in ticket `## Implementation Notes`; no pytest assertion (matches M1's own AC7 precedent for non-mechanical findings) |
| AC4 — combined view renders both domains with raw counts + classification breakdown | Steps 7, 9, 10 | `test_cross_domain_view_renders_both_domains`, `test_cross_domain_view_shows_raw_counts_not_bare_percentage` |
| AC5 — drift check clean after new rows | Step 20 | Manual command output recorded; report-only tool, no pytest assertion beyond existing drift-detector regression tests |
| AC6 — inherited-entry citation rule documented in `architecture.md` §3 | Step 13 | `test_architecture_md_section_3_documents_inherited_entry_citation_rule` |
| AC7 — comparison honest, non-`SUPPORTED` results recorded as-is, never smoothed | Step 12 (comparison prose), Summary's own "why PARTIAL" reasoning | `test_combat_mixed_realization_is_not_smoothed_into_a_clean_result` |
| AC8 — §10 run-on fixed; terms-needed list reported, vocabulary not edited | Steps 16, 18 | `test_core_rpg_design_direction_section_10_has_no_run_on_paragraph` |
| AC9 — `roadmap.md` M4 section + epic milestone table record disposition and roadmap-complete-but-mapping-continues | Steps 14, 15 | Read-back verification (no pytest assertion; matches done-checker's doc-review) |

## Anti-Drift Notes

- **`CONFLICT-01`/`ECOL-04` are the one place this plan deliberately does not force a row.** Any
  implementer tempted to "just pick the closest mechanism" for these two must re-read the Summary's
  own reasoning first — `resource_harvesting`/`regional_trauma` are confirmed wrong-identity
  matches, not merely weak ones.
- **Do not let "all 10 mapped Rules are `PARTIAL`" read as suspicious uniformity and get
  "fixed" into a forced mix.** Each `PARTIAL` above has its own independent, real reason (STARVED
  dormancy, world-specific gating, a confirmed-missing outcome clause, an unconfirmed consumer
  side) — re-read the Summary's per-Rule reasoning before changing any of them, and do not
  manufacture a `SUPPORTED` or `CONFLICTING` result to make the spread look less uniform; AC7
  forbids manufacturing a result in *either* direction.
- **Do not classify `combat_engagement`'s dormancy-outside-`metropolis` finding as `CONFLICTING`.**
  Per the M3 triage log's own already-settled reasoning (carried forward here, not re-derived):
  `CONFLICTING` is a code-vs-Rule semantic-violation judgment; a real mechanism that is simply
  weakly exercised in real corpus play is not the same claim.
- **Territory's own rows, edges, classifications, and generated view must not change anywhere in
  this plan.** Every step touching the shared generator script (Step 7) must be verified against
  Territory's own byte-identical output before moving on, not just at the end.
- **Do not resolve the fail-open `try/except Exception: pass` gate question, the missing
  surrender/capture/displacement outcome, or `tactical_decision`'s dispatch-gate question** — all
  three are real, cited as evidence, and explicitly left as open design questions by their own
  source documents; this ticket records them, never decides them.
- **Do not add a `mechanism_causal_edges.yaml` row for `tactical_decision → combat_resolution`**
  even though it is visibly a real causal relationship in the code — it is outside this ticket's
  own Scope items, and adding it as an unplanned bonus would be scope creep past what was reviewed.

## Unresolved Questions

None. Every open item carried by `investigation.md`, the ticket's own Assumptions/Open Questions
section, and this plan's own fact-verification pass (the exact mechanism/edge-type/classification
for all 12 Rule IDs, the extend-vs-new-file call, the cross-domain view's concrete shape, and where
the written comparison and the §10 terms-needed report physically live) has been resolved as a
concrete decision above, with the evidence and reasoning that produced it spelled out in the
Summary and the relevant Step's Change text.
