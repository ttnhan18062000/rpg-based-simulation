---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE
artifact_type: plan
tags: [architecture, schema, registry, combat]
---

# Plan — TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE

Built directly on `investigation.md`'s re-verified evidence and the ticket's own
"## Scoping Decisions (2026-09-24, post-Investigate)" section (D1/D2/D3), which resolved every
open question Investigate raised. No further scoping ambiguity remains — this plan is a
disposition-by-disposition execution spec, not a re-investigation.

## Acceptance-criteria map

| AC | How this plan satisfies it |
|---|---|
| 1 | Triage log covers every finding in every named source, scoped per D3 (Territory: 3 of 10 items in `places-territory-batch-11a-review.md`) and the ticket's own batch-07 scope guard (Combat: items 1, 2, 7, 12 of 12) |
| 2 | Every log row cites today's re-verification (registry read, code path opened, tool run) from `investigation.md` — never restates prose as fact |
| 3 | One Territory registry edit (TERR-01 evidence text amendment), validated by `registry.py` with zero manual overrides |
| 4 | Combat findings (C1.1/C1.2/C1.3, cross-cited from C3 items 1/2/7) dispositioned `PROMOTE-AT-M4` with verified evidence; zero Combat rows written to either registry — checked by manual grep at Verify |
| 5 | Re-run `make semantic-control-plane-drift-check` after the TERR-01 edit; must stay 0/0 |
| 6 | Non-promote findings exist (T1/T2 not-a-control-plane-fact, T3/C2-items-2-4 UNKNOWN, T4/T5-item-1/T5-item-8 already-covered, C1.4/C3-item-12 not-a-control-plane-fact) — this is not an all-promote outcome, no justification-of-cleanliness needed |
| 7 | `roadmap.md` M3 section gets a dated note that the narrow bar is met, with explicit "no complete state" language preserved |
| 8 | Epic ticket's M3 row updated from "not yet created" to a disposition |

## Step 1 — Write `docs/plans/simulation_semantic_control_plane/finding_triage_log.md`

New file. One entry per in-scope finding, grouped by domain then by source. Each entry: source
citation (file + section/line), what was re-verified today and how (pulled from
`investigation.md`, not restated prose), disposition, one-line reason. Per "define information
once," this file does **not** restate finding prose or duplicate registry evidence text — it
records the triage decision and points at the evidence, matching the ticket's own instruction.

**Territory (3 findings, per D3):**

| Finding | Disposition | Reason (cites re-verification) |
|---|---|---|
| T1/T2 — `TerritorialRelation` typed-record proposal (territory-control.md Implementation Candidates; batch-11a-review.md identical, byte-confirmed duplicate) | **Not a control-plane fact** | Forward-looking design proposal, explicitly `DEFERRED`; zero `TerritorialRelation` hits anywhere in `src/`/`registries/` (grepped). One log entry, two citations — not two rows. |
| T3 — "does Territory need its own relation model" (territory-control.md Open Questions #1) | **UNKNOWN** | Genuinely undecided design question; no registry-checkable claim to verify against. |
| T4 / batch-11a-review item 8 — "does `owner_faction_id`'s assignment trace to a real causal basis" (territory-control.md Open Questions #2; same fact as batch-11a-review item 8, TERR-02) | **Already covered — TERR-02 `PARTIAL`** | `rule_classifications.yaml` TERR-02 row (read today, dated 2026-09-24) already answers this with real evidence (`FactionInfluenceService.process_influence_shift()`) plus two confirmed gaps. No new row. |
| batch-11a-review item 1 (TERR-01/TERR-03 conflation + contested-claim divergence) | **Already covered — TERR-01/TERR-03 `CONFLICTING`** | Word-for-word match to the existing rows, re-read today. No new row. |
| batch-11a-review item 2 (no residence/cultural-association field) | **Promote — amend TERR-01 evidence text** | Confirmed today: `src/core/state.py` `PlaceState`/`RegionState` carry no such field, and TERR-01's current evidence text never itemizes this sub-fact separately (only the overloaded-slot claim). See Step 2. Aggregate `CONFLICTING` verdict is unaffected. |

Note in the log, explicitly: batch-11a-review's Repository Findings items 3–7, 9, 10 were
checked and are Places/Settlements-scoped (per-item Rule IDs: PLACE-02, PT-S02/PT-S05,
SETT-03/SETT-01, SETT-02, `settlements.md`, SETT-02/PT-S13, SETT-01) — out of scope, not silently
dropped.

**Combat (per the ticket's own scope: `conflict-combat.md`'s 4 Repository Findings + 4 Open
Questions, and batch-07-review items 1, 2, 7, 12):**

| Finding | Disposition | Reason |
|---|---|---|
| C1.1 / C3 item 1 — perception-gated targeting (SUPPORTED in source prose) | **PROMOTE-AT-M4** | Confirmed today against `src/engine/tactical.py:181,199` — matches prose exactly, current. M3 records the evidence; M3 does **not** assert `SUPPORTED` or any classification — that is M4's call per the ticket's own asymmetry rule. |
| C1.2 / C3 item 2 — `combat_engagement` / `ENABLE_COMBAT_ENGAGEMENT` | **PROMOTE-AT-M4, corrected evidence — call out explicitly per D1** | Per D1: the source docs' "INERT/OFF, default OFF" is stale — `feature_flags.py:32` is `FeatureMode.ON` since 2026-09-14 (`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`, #190, `1e075b807`), wired live into `pipeline.py`'s tick loop, with observed runtime effect in `mechanisms.yaml` (posture gate 1960→837). Log entry must state the flag is ON and record this as the ticket's own AC2 catch-in-action, not a footnote. **Not** dispositioned `CONFLICTING` — see D1's reasoning (that vocabulary describes code-vs-Rule, not doc-vs-reality). Fail-open `try/except Exception: pass` sub-claim (a separate, still-true robustness gap) recorded alongside, unchanged. |
| C1.3 / C3 item 7 — no surrender/capture/forced-displacement outcome | **PROMOTE-AT-M4** | Confirmed today: `combat.py` `outcome_kind` / `movement.py` `FLED` vocabulary has no such value. Current. |
| C1.4 — no non-combat Conflict superclass | **Not a control-plane fact** | Source doc itself frames this as a stated Scope Boundary, not a gap. Confirmed unchanged today. |
| C2 items 2–4 — fail-open-should-fail-closed?, surrender/capture as real outcomes?, dedicated Conflict-resolution mechanism? | **UNKNOWN** (all three) | Genuinely open design questions this ticket's own Out of Scope forbids deciding. Code unchanged, confirmed today. |
| C2 item 1 — "should `ENABLE_COMBAT_ENGAGEMENT` be turned on" | **Resolved by event, not UNKNOWN** | Already happened, 2026-09-14, independent of this ticket. Log entry cross-references the C1.2/C3-item-2 evidence rather than treating this as still-open. |
| C3 item 12 — `src/world/displacement.py` naming near-collision | **Not a control-plane fact** | Confirmed today: `DisplacementService` is calamity-driven (idea 65), structurally unrelated to combat-defeat outcomes. Naming collision only, per the source's own framing. |

Note in the log, explicitly: batch-07-review items 3, 8, 9 were checked (not merely accepted from
the ticket's own incomplete first-read guess) and resolved to out-of-scope/Progression
(BreakthroughService, fame-to-followers PROG-07, non-HERO significance CP-S15 respectively) —
same treatment as items 4/5/6/10/11, which the ticket did name.

## Step 2 — Amend `registries/rule_classifications.yaml`'s TERR-01 evidence text

Edit only. No new row (the schema is one row per Rule ID; TERR-01 already has one). Append a
third clause to the existing `evidence` block naming the confirmed-absent residence/cultural-
association sub-fact (mirroring TERR-05's own pattern of naming a confirmed-MISSING half inside a
non-MISSING aggregate verdict). `classification` stays `CONFLICTING` — D3 confirms the aggregate
verdict does not move. `review_date` stays `"2026-09-24"` (already today's date from M1's own
pass — re-verified today, not re-dated to fabricate freshness it doesn't need since it already
reflects today).

After the edit: `python3 tools/semantic_control_plane/registry.py` must report `OK` with zero
manual overrides (AC3).

## Step 3 — Update `docs/plans/simulation_semantic_control_plane/roadmap.md` M3 section

Add a dated note under the existing M3 section (do not replace the "no complete state" framing —
AC7 requires it stay explicit): record that the narrow Territory+Combat triage bar is met
2026-09-24 by this ticket, with a one-line pointer to `finding_triage_log.md` and the count
(3 Territory findings triaged, 7 Combat findings triaged across the two Combat sources). State
plainly that M3 itself remains a permanent stream with no complete state — only its bar for M4 is
met.

## Step 4 — Update the epic ticket's M3 row

`tickets/inprogress/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md`'s milestone table, M3 row:
change `Ticket` from "not yet created" to this ticket's ID, `Disposition` to a short DONE note
(narrow bar met, pointer to the triage log), matching M1/M2's own row format. Do not touch M4's
row (still "not yet created" — this ticket does not create M4).

## Step 5 — Verification

1. `pytest tests/unit/tools/test_semantic_control_plane_schema.py tests/unit/tools/test_semantic_control_plane_drift_detector.py tests/unit/tools/test_territory_control_view.py -v`
2. `python3 tools/semantic_control_plane/registry.py` (AC3)
3. `make semantic-control-plane-drift-check` — must stay 0/0 after the TERR-01 edit (AC5); if not,
   report it as a real M2 finding, do not adjust the date to silence it
4. Manual grep guard (test_plan.md's own anti-drift note, AC4): confirm zero `CONFLICT-*`
   rule_id rows in `registries/{rule_mechanism_edges,rule_classifications}.yaml`

## Out of scope, reaffirmed (nothing in this plan crosses these)

- No edit to `docs/world_rules/capability-progression/conflict-combat.md` (D2) — the
  `ENABLE_COMBAT_ENGAGEMENT` staleness is recorded in the triage log only; the peer session is
  separately handing the doc-staleness report to `world-rule-catalog-design`, not this ticket.
- No Combat registry rows written (M4's deliverable).
- No repair of any gap a finding names (fail-open fallback, missing outcome kinds, etc.).
- No action on `tactical_decision`'s `contradicted` verdict or the paused
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`.
- No feature-flag flip (moot regardless — the flip already happened independently).
