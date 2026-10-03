---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT
artifact_type: plan
tags: [simulation-quality, calibration, corpus, agency, cognition, adventure]
---

# Implementation Plan — TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT

## Summary

This is a **recalibrate-and-disclose** ticket, not a code-fix ticket. Investigate confirmed the
AGENCY drift's true root cause is broader than §2.41 discloses (the deleted
`AdventureDecisionPhase.apply()` was the sole writer of both `last_defer_reason` *and*
`last_routing_family`, and only the former is documented). This plan's own direct reads (below)
go one step further than investigation.md's Risk #1 and establish that restoring
`last_routing_family` is **not** a narrow, low-risk observability side-effect fix: it requires a
new field on the shared `StrategicUpdate` durable-update schema (`src/core/updates.py`, no such
field exists today), a `StrategicUpdate.merge()` change, and a second edit at the outer
entity-update merge site (`intelligence.py:917-927`) that today only assigns `.strategic`, never
`.property_updates` — because `RouteFamily -> ProjectKind` is a many-to-one mapping
(`src/domains/adventure/mapper.py:31-47`), the specific family cannot be reconstructed after the
fact from the committed `ProjectState.kind` at that outer site; it only exists inside
`evaluate_strategic_intent()`'s own `ADVENTURE_ROUTE` branch. That is real, reviewable,
schema-touching work for its own ticket, not proportionate scope for this P1
recalibration-and-doc-correction ticket in a subsystem already under active 7-ticket churn. This
plan therefore: (1) recalibrates `grade_anchors.json` for all 6 confirmed-drifted run_keys (the 4
named `_500t` items plus the seed123 pair, which Investigate's Finding 2 proved is the *identical*
full-zero signature, not a milder one), preceded by a mandatory fresh Implement-time
re-verification per the parent ticket's Decision 1 precedent; (2) converts the two stale `_1000t`
SLOW-tier COGNITION guards to the corrected tolerance-guard shape, informed by a fresh
idle+induced-load repro rather than the idle-only 6-trial sample Investigate collected; (3)
broadens §2.41, corrects the stale `eval_matrix_results.md` AGENCY design note, and adds the
INFRA-237 re-verification addendum it already asks for; (4) files two follow-up tickets — one for
the `last_routing_family` code-fix (deliberately out of this ticket's scope, per the schema-change
finding above) and one for `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift — rather
than silently absorbing or dropping either.

## Design Decisions

### Decision 1 — Recalibrate-only for AGENCY; the `last_routing_family` code-fix is its own follow-up ticket

**Evidence gathered this session (Plan phase), beyond what investigation.md's Risk #1 checked:**

- `src/core/updates.py:474-517` (`StrategicUpdate` dataclass, full field list read directly): no
  `property_updates`-equivalent field exists on `StrategicUpdate` today. It carries typed
  lists/optional-ids for blockers/leads/directives/projects/concerns/etc., nothing that could
  carry an arbitrary `{"last_routing_family": ...}` key.
- `src/core/updates.py:613-645` (`EntityUpdate` dataclass): `strategic: Optional[StrategicUpdate]`
  and `property_updates: Dict[str, Any]` are **sibling fields**, not nested — `property_updates`
  is never populated from `.strategic`'s contents anywhere.
- `src/systems/strategic_systems/intelligence.py:917-927` (the only call site that turns a
  `StrategicUpdate` returned by `evaluate_strategic_intent()` into part of the tick's
  `EntityUpdate`, confirmed by `grep -rn "evaluate_strategic_intent(" src/`): it merges
  `strat_up` into `ent_upd.strategic` only (`replace(ent_upd, strategic=merged_strat)`,
  line 927) — it never touches `ent_upd.property_updates`. This is the only plausible site
  outside `evaluate_strategic_intent()` itself to write `last_routing_family`, and it does not
  have the family value available (see next point).
- `src/domains/adventure/mapper.py:31-47` (`RouteToProjectMapper._MAP`, read directly): 15
  `RouteFamily` values map onto ProjectKinds with real collisions — e.g. `RECOVER` and
  `OWN_SURVIVAL` both -> `ProjectKind.RECOVERY`; `TAKE_EASY_QUEST` and `QUEST_OPPORTUNITY` both
  -> `ProjectKind.QUEST`; `BUY_UPGRADE` and `SELL_LOOT_FOR_GOLD` both -> `ProjectKind.PREPARATION`.
  The committed `ProjectState.kind` the outer merge site (`intelligence.py:917-927`) has access to
  cannot be reversed into the original `RouteFamily` — the family value only exists inside
  `evaluate_strategic_intent()`'s own `ADVENTURE_ROUTE` branch as
  `best_candidate.metadata.get("route_family")` (`intelligence.py:1489`,
  `src/ai/goals/adventure_scorer.py:217`'s `GoalScore.metadata={"route_family": family, ...}`).

**Conclusion:** a real `last_routing_family` restoration requires (a) a new field on
`StrategicUpdate`, (b) a `StrategicUpdate.merge()` update to propagate it, and (c) threading it
through *two* call sites in `intelligence.py` (the `ADVENTURE_ROUTE` branch where the family is
known, and the outer refine-loop merge site where `ent_upd.property_updates` is actually settable)
— a schema-level, cross-cutting change to a durable, shared update type consumed by every
strategic-cognition write path, not a one-line restore. Combined with: this ticket's own Out of
Scope naming `src/systems/strategic_systems/intelligence.py` as off-limits unless a real code gap
is confirmed *and* Investigate's Anti-Drift Hazards explicitly warning against treating a
`last_routing_family` port as "a reflexive fix" given the area's active-churn history (7-ticket
cluster, investigation.md Risk #4) — this plan's decision is: **recalibrate `grade_anchors.json`
to the confirmed current AGENCY=0/0.0/C values for all 6 run_keys, broaden §2.41's disclosure to
cover `last_routing_family` honestly, and file the code-fix as a separate, explicitly-scoped
follow-up ticket** (Step 9a) rather than attempt it inside this ticket.

The `last_defer_reason` half of §2.41 is unaffected by this decision — it stays exactly as already
`Bounded`/deliberately-not-ported, per the existing rationale (sub-floor discard at
`intelligence.py:1409`, still accurate — confirmed by this session's own read of that line, "if
g_score.utility < 20.0: continue" gates it before any `StrategicUpdate`-returning site).

### Decision 2 — seed123 pair folds into the same recalibration pass as the 4 named items

Investigate's Finding 2 confirmed (2 independent trials, bit-identical) that
`simq_routing_test_seed123_500t` and `hero_guild_routing_seed123_500t` show the **identical**
`0 events/0.0/C` signature on both COGNITION and AGENCY — not a milder, distinct-magnitude drift
as the ticket's own Request Summary states (that text reflects a pre-`TCK-20260811-DELETE-
ADVENTURE-DECISION-PHASE` snapshot, timestamped before the causing commit landed). This plan
therefore treats all 6 run_keys as one recalibration pass, same evidence standard, same commit
(ticket Scope item 2's own "if confirmed same cause" clause is now satisfied). This also means the
ticket's own Scope item 1 sub-question ("determine why it manifests as a full 0/C band-crossing on
these 4 items but only a partial score-tolerance drift on the seed123 variants") is **moot** — no
differential manifestation exists; both are the same mechanism at the same magnitude.

### Decision 3 — `_1000t` guard shape: default to the corrected tolerance-guard (2b) shape, confirmed by a fresh induced-load trial, not assumed bit-identical

The `_500t` sibling (`test_simq_routing_test_seed42_500t_cognition_grade_stability`,
`tests/unit/worldassembly/test_corpus_diversity.py:524-629`, read directly) was *reverted* from a
proposed strict bit-identical (2a) shape back to a tolerance-guard (2b) shape after an
Implement-time induced-load rerun surfaced a rare residual (1/3 trials,
`event_count=2, grade=B, loop_detected=True`). Investigate's `_1000t` repro (investigation.md
Finding 3) sampled 6/6 clean trials but **only under idle conditions** — no induced-load trial was
run. Given the established precedent that idle-only sampling missed the `_500t` sibling's own
residual, this plan defaults the `_1000t` guards to the same tolerance-guard (2b) shape as the
corrected `_500t` sibling (idle trial asserted bit-identical `event_count=0, grade=C`; one
induced-load trial tolerated at `event_count <= 2, grade in {"C","B"}`), to be confirmed — not
reflexively assumed — by Implement running the `_500t` sibling's own `_busy_loop` mechanism once
against each `_1000t` scenario before finalizing the guard body. If Implement's induced-load trial
comes back clean (matching all 6 of Investigate's idle trials), the guard still uses the 2b shape
(safer default, matches sibling precedent) — this plan does not require re-deriving evidence for a
stricter 2a conversion, since the reviewer-visible cost of staying at 2b when 2a would also work is
low, while the cost of prematurely locking 2a without a load trial (as the `_500t` sibling's own
history shows) is a guaranteed future flake ticket.

## Steps

### Step 1 — Mandatory fresh Implement-time re-verification (precondition for Steps 2-4)

**Files:** none (verification-only step; produces the confirmed numbers Steps 2-4 depend on)
**Change:** Before writing any `grade_anchors.json` value, run 2 independent trials each via
`tools/calibrate_simq.py --ticks 500 --seed {42,123,456} --name {simq_routing_test,
hero_guild_routing}` for all 6 run_keys, confirming AGENCY is `0 events/0.0/C` on all 6, and
COGNITION is `0 events/0.0/C` on the 2 seed123 run_keys specifically. This mirrors the parent
ticket's own Decision 1 precedent (`stored_artifacts/TCK-20260811-.../plan.md`) and
investigation.md's Risk #4 ("do not copy this investigation's own snapshot values verbatim without
a final re-check immediately before commit") — this area is under active churn from a 7-sibling-
ticket commit cluster and Investigate's own snapshot is already hours old by Implement time.
**Do NOT touch:** No file edits in this step — pure verification. Do not skip this step and copy
investigation.md's Finding 1/2 tables directly into `grade_anchors.json`.
**Verify:** Fresh trial output matches investigation.md's Finding 1/2 tables (0/0.0/C for AGENCY on
all 6 run_keys; 0/0.0/C for COGNITION on the 2 seed123 run_keys). If any value differs from
Investigate's snapshot, stop and re-open the Unresolved Questions below rather than proceeding to
Steps 2-4 with stale numbers.

### Step 2 — Recalibrate `grade_anchors.json` AGENCY for the 4 named `_500t` run_keys

**Files:** tests/simulation_quality/fixtures/grade_anchors.json
**Change:** Using Step 1's freshly-confirmed values, update the `AGENCY` sub-object for exactly
these 4 top-level keys (current values confirmed by direct read this session,
`tests/simulation_quality/fixtures/grade_anchors.json`):
- `simq_routing_test_seed42_500t.AGENCY`: `{"grade": "A", "score": 0.918}` -> `{"grade": "C",
  "score": 0.0}`
- `simq_routing_test_seed456_500t.AGENCY`: `{"grade": "A", "score": 0.6415478615071283}` ->
  `{"grade": "C", "score": 0.0}`
- `hero_guild_routing_seed42_500t.AGENCY`: `{"grade": "A", "score": 0.9777327935222672}` ->
  `{"grade": "C", "score": 0.0}`
- `hero_guild_routing_seed456_500t.AGENCY`: `{"grade": "A", "score": 0.6726907630522089}` ->
  `{"grade": "C", "score": 0.0}`

Only the `AGENCY` sub-object of each entry changes — no other pillar, no other top-level key.
**Other writers of this shared resource (`grade_anchors.json`):** this is a hand-edited fixture,
not code-written at runtime; the only other "writers" are other tickets' point-edits (most
recently the parent ticket's COGNITION edits on `simq_routing_test_seed42_500t` /
`hero_guild_routing_seed42_500t` for the *other* 2 named items it touched, already merged before
this ticket started — confirmed those are different top-level keys/pillars than this step's
edits, no collision). `test_grade_anchor_file_exists_and_valid`
(`tests/simulation_quality/test_grade_regression.py`) is the structural guard that runs after
every edit; it does not itself write the file.
**Do NOT touch:** `COGNITION`, `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`, `SOCIAL`,
`INFORMATION`, `WORLD`, `NARRATIVE` sub-objects on any of these 4 keys.
`hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift (confirmed present, per
investigation.md Finding 1) is explicitly deferred to Step 9b's follow-up ticket, not folded in
here.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k
"simq_routing_test_seed42_500t or simq_routing_test_seed456_500t or hero_guild_routing_seed42_500t
or hero_guild_routing_seed456_500t"` passes on AGENCY (other pillars on
`hero_guild_routing_seed456_500t` will still fail — expected, tracked by Step 9b, not this
ticket's own AC4 gate for the named 4 items' AGENCY).

### Step 3 — Recalibrate `grade_anchors.json` COGNITION+AGENCY for the seed123 pair

**Files:** tests/simulation_quality/fixtures/grade_anchors.json
**Change:** Per Decision 2, update both `COGNITION` and `AGENCY` sub-objects for these 2 keys
(current values confirmed by direct read this session):
- `simq_routing_test_seed123_500t.COGNITION`: `{"grade": "A", "score": 0.5295315682281059}` ->
  `{"grade": "C", "score": 0.0}`
- `simq_routing_test_seed123_500t.AGENCY`: `{"grade": "A", "score": 0.6415478615071283}` ->
  `{"grade": "C", "score": 0.0}`
- `hero_guild_routing_seed123_500t.COGNITION`: `{"grade": "A", "score": 0.5295315682281059}` ->
  `{"grade": "C", "score": 0.0}`
- `hero_guild_routing_seed123_500t.AGENCY`: `{"grade": "A", "score": 0.6415478615071283}` ->
  `{"grade": "C", "score": 0.0}`
**Other writers of this shared resource:** same as Step 2 — hand-edited fixture, no runtime
writer, no other ticket currently touching these 2 keys' COGNITION/AGENCY fields (confirmed:
parent ticket's own named 4 items did not include the seed123 pair).
**Do NOT touch:** any other pillar on these 2 keys, including the `PROGRESSION` sub-object (its
`watchdog_variance` ceiling annotation, not the anchor value itself, is Step 4's concern, and the
PROGRESSION *anchor value* in `grade_anchors.json` is not touched by this ticket at all).
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k
"simq_routing_test_seed123_500t or hero_guild_routing_seed123_500t"` passes on COGNITION and
AGENCY.

### Step 4 — Annotate the stale `score_ceilings.json` entry (do not delete)

**Files:** tests/simulation_quality/fixtures/score_ceilings.json
**Change:** The existing `simq_routing_test_seed123_500t` / `PROGRESSION` / `watchdog_variance`
entry (confirmed present, line 28-34 as read this session) has a `reason` field asserting COGNITION
was "stable at 0.5295/52 events across both re-runs" — now false per Step 1/3's fresh
re-verification. Prepend an annotation to the `reason` string (matching the parent ticket's own
precedent for its now-superseded `simq_routing_test_seed42_500t`/COGNITION entry, line 22-25 of
the same file, which prepends `"SUPERSEDED (<ticket>, <date>): ..."` rather than deleting the
original text): `"SUPERSEDED-IN-PART (TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT,
2026-08-13): the 'COGNITION stable at 0.5295/52 events' aside below is no longer true — fresh
re-verification found COGNITION collapsed to 0 events/0.0/C for this run_key (see
grade_anchors.json's own recalibrated COGNITION value and docs/guidelines/
intentional_divergences.md §2.41). This entry's own PROGRESSION/watchdog_variance classification is
unaffected and remains accurate. Original reason preserved below for audit history: "` followed by
the existing `reason` text unchanged.
**Other writers of this shared resource:** hand-edited fixture; `TCK-20260810-SIMQ-FAST-TIER-
DRIFT-AND-RELIABILITY-GAP` originally wrote this entry (done, not touched further); no other
in-flight ticket edits this specific entry.
**Do NOT touch:** the entry's `ceiling_kind`, `evidence`, or `since_ticket` fields, or any other
entry in the file.
**Verify:** `python3 -c "import json; json.load(open('tests/simulation_quality/fixtures/score_ceilings.json'))"`
parses cleanly; `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k
simq_routing_test_seed123_500t` still passes on PROGRESSION (ceiling logic unaffected by a `reason`
string edit).

### Step 5 — Broaden `docs/guidelines/intentional_divergences.md` §2.41 to disclose the `last_routing_family` loss

**Files:** docs/guidelines/intentional_divergences.md (section starting line 998, read in full this
session)
**Change:** §2.41's "Old Behavior"/"New Behavior" text currently describes only the
`last_defer_reason` loss (confirmed by direct read, lines 998-1027). Add a new paragraph (do not
delete the existing DEFER_WITH_REASON-specific text, which remains accurate) disclosing that the
SAME deleted `AdventureDecisionPhase.apply()` was also the sole writer of `last_routing_family`
(pre-deletion `phase.py:178-179`, readable via `git show 1825f914^:src/domains/adventure/
phase.py`), written unconditionally on every **winning** route — a case the existing "Rationale:
Bounded" paragraph's sub-floor-discard argument (`intelligence.py:1409`) does **not** cover, since
a winning candidate reaches a real commit site (`RouteToProjectMapper.map_to_states()`,
`intelligence.py:1478-1495`). State plainly that `route_selected`, `action_executed`, and
`route_family_first_use` (3 of AGENCY's 4 adventure-routing event types, sourced from
`event_shapers.py:750-773` and `event_extractor.py:594-618`) are therefore also silently dead for
every routing-capable world, not just the DEFER_WITH_REASON-driven `defer_with_reason` event. Add a
new rationale note explaining this half is **not** being ported as part of this ticket
(recalibrate-only decision, Decision 1 above) and cite the follow-up ticket filed in Step 9a once
its ID is known. Update the section's own "Status" line if the divergence log's convention
requires noting the broadened scope (keep `ACTIVE`).
**Do NOT touch:** any other numbered section (§2.40, §2.42, etc.) or the Divergence Summary Table's
existing row for this entry (row text "Adventure-Route Defer-Reason Observability Gap" — leave the
table row as-is; it is a summary label, not required to enumerate both halves).
**Verify:** manual review only (doc-correctness, no automated gate); optionally cross-checked by
the (nice-to-have, not required per test_plan.md) doc-correctness guard in Step 7.

### Step 6 — Add the INFRA-237 re-verification addendum `support_boundary` explicitly requests

**Files:** docs/parity_ledger/infrastructure.yaml (INFRA-237 entry, lines 2937-2994 as read this
session)
**Change:** The `support_boundary` field's existing "Addendum (TCK-20260811-DELETE-ADVENTURE-
DECISION-PHASE)" (lines 2979-2994) explicitly asks: "a follow-up ticket should re-run the AGENCY
calibration sweep referenced above against current HEAD before this support_boundary's grading
claims are relied upon again." Append a second addendum block: "Addendum (TCK-20260813-SIMQ-
ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT): re-verification performed. AGENCY is now `0 events/
0.0/C` for all 6 measured routing-capable run_keys (`simq_routing_test`/`hero_guild_routing`,
seeds 42/123/456, 500t) — confirmed root cause is the `last_routing_family` property-write loss
(§2.41, broadened), not a scorer-logic defect. `AgencyScorer` itself is unaffected (INFRA-237's own
`v2_evidence`/`test_path` remain correct — this is an emission-side gap, not a scoring-logic
parity divergence). The `dungeon_crawl`/`urban_political`/`sandbox_world` archetype-blocked-C claim
is unaffected (different mechanism, `ENABLE_ADVENTURE_ROUTING=OFF`, not re-verified by this ticket
— see eval_matrix_results.md AGENCY Cross-World Design Note). `grade_anchors.json` recalibrated
accordingly." Do not modify `status`, `priority`, `v2_evidence`, or `test_path` fields — this is an
emission/observability gap, not a scorer-logic parity divergence (confirmed by investigation.md's
own Parity Ledger Overlap analysis: `test_agency_scorer.py` bypasses the broken wiring entirely and
stays green either way).
**Do NOT touch:** any other `id:` entry in the file, or INFRA-237's `text`/`status`/`priority`/
`legacy_evidence`/`v2_evidence`/`proof_type`/`test_path`/`divergence_note` fields.
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses cleanly; manual review confirms the addendum accurately reflects Steps 1-3's fresh values.

### Step 7 — Correct the stale `eval_matrix_results.md` AGENCY Cross-World Design Note + add dated NOTE blocks

**Files:** docs/simulation_quality/eval_matrix_results.md
**Change:** Two edits:
(a) The "AGENCY — Cross-World Design Note" section's "Root cause" paragraph (lines 584-599, read
in full this session) states "All three AGENCY key events... are emitted only from
`AdventureDecisionPhase` (`src/domains/adventure/phase.py`)" and that `simq_routing_test`'s AGENCY
"activates... as designed" — both now factually false (`phase.py` is deleted;
`simq_routing_test`'s AGENCY no longer activates for the routing-derived events at all, per Steps
1-3's confirmed 0/0.0/C). Rewrite this paragraph (not just append a note) to state the current
mechanism: `route_selected`/`action_executed`/`route_family_first_use` were emitted from
`AdventureDecisionPhase` historically, that phase was deleted by `TCK-20260811-DELETE-ADVENTURE-
DECISION-PHASE`, and no replacement site writes the underlying `last_routing_family` property
today (§2.41, broadened) — so both `simq_routing_test` and `hero_guild_routing` now grade
AGENCY=C for a *different* reason than the archetype-gating (`ENABLE_ADVENTURE_ROUTING=OFF`)
mechanism that still correctly explains `dungeon_crawl`/`urban_political`/`sandbox_world`'s C
grade (per investigation.md Risk #5 — that claim is unaffected, not re-verified here, and remains
accurate). Do not alter the "Anti-drift" paragraph (lines 607-610) — its guidance (recalibrate
if any other world turns the flag ON) remains valid.
(b) Add a dated NOTE block (matching the existing 2026-08-13 COGNITION NOTE pattern already present
per the parent ticket, confirmed present around line 454-459 of this file) to both the
`simq_routing_test` and `hero_guild_routing` sections recording this ticket's AGENCY findings and
linking to the recalibrated anchors and §2.41.
**Do NOT touch:** the AC6 stasis-dynamic content, the "Second exception class" / "Second
routing-capable archetype" subsections (lines 612-632), or any other world's section.
**Verify:** manual review only (doc-correctness, no automated gate).

### Step 8 — Convert the two `_1000t` COGNITION guard tests to the corrected tolerance-guard shape

**Files:** tests/unit/worldassembly/test_corpus_diversity.py
(`test_simq_routing_test_seed42_1000t_cognition_grade_stability` at line 633,
`test_hero_guild_routing_seed42_1000t_cognition_grade_stability` at line 717, both confirmed by
direct read this session — the ticket's own cited `~600`/`~684` are stale)
**Change:** Per Decision 3, convert both tests from the current 3-trial mean-tolerance shape
(`n_trials=3`, `_within_band` + `_within_score_tolerance` against the stale anchors
`{"grade": "A", "score": 1.7961, "abs_floor": 0.2768}` and `{"grade": "S", "score": 2.0641,
"abs_floor": 0.5536}` respectively) to the SAME idle+induced-load tolerance-guard shape as the
corrected `_500t` sibling (`test_simq_routing_test_seed42_500t_cognition_grade_stability`, lines
524-629, read in full this session — reuse its `_busy_loop`/`multiprocessing` induced-load
mechanism verbatim, adjusted for `ticks=1000`): one idle trial asserted bit-identical
`event_count == 0 and grade == "C"`, one induced-load trial (2x core oversubscription) tolerated at
`event_count <= 2, grade in {"C", "B"}`. Update each docstring to drop the stale "F6/
decision_divergence_detected-class... genuinely unstable" framing (confirmed inaccurate — investigation.md's
6/6 idle-trial repro found deterministic 0/C, no load-variance signature observed, matching the
`_500t` sibling's own now-corrected framing) and cite this ticket + the `3d992dd0`/§2.40 root
cause, matching the `_500t` sibling's own corrected docstring pattern exactly.
**Other writers of this shared resource:** `test_corpus_diversity.py` is edited by whichever
ticket owns the specific guard being touched — confirmed by reading the file's own section
comments (lines 491-523) that this is a single-owner-per-test convention (each guard's docstring
names its owning ticket); no other in-flight ticket touches these 2 specific tests. The file-level
`nodeid_count < 32` guard (`make simq-corpus-diversity-slow-isolated`) is a downstream consumer,
not a writer — must stay >= its current count (no test deletion, only body edits).
**Do NOT touch:** any other test in this file, including the corrected `_500t` sibling itself
(read-only reference for this step) or the other 12 anchors in the
`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` section (lines 492-498).
**Verify:** `pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability" --resource-budget large --tb=short -q -m slow` and the
`hero_guild_routing` equivalent, both run in isolation (not combined `-k`), then
`make simq-corpus-diversity-slow-isolated` as the final full-sweep gate.

### Step 9 — File two follow-up tickets

**Files:** new ticket files under `tickets/inprogress/` (or `tickets/todos/`, per this session's
established disclosure pattern of filing real follow-up tickets rather than leaving findings
untracked)
**Change:**
(a) **`last_routing_family` code-fix follow-up** — scope: restore `last_routing_family` emission by
adding a property-updates-carrying field to `StrategicUpdate` (`src/core/updates.py`), threading it
from the `ADVENTURE_ROUTE` win branch (`intelligence.py:1478-1495`, where `family` is known) through
`StrategicUpdate.merge()` and the outer refine-loop call site (`intelligence.py:917-927`) into
`EntityUpdate.property_updates`. Cite this plan's Decision 1 evidence (the schema-change/
many-to-one-mapping findings) as the reason it's a separate ticket. Explicitly NOT in scope for
that follow-up either: `last_defer_reason` (stays `Bounded` per §2.41, sub-floor discard argument
still valid) or any change to `evaluate_project_switch()`'s own lock/margin decision logic
(STRAT-185/186/187).
(b) **`hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION drift follow-up** — scope: investigate
why this one run_key's ECONOMY (was B, now drifted) and PROGRESSION (event count/negative-count
changed) moved beyond band/tolerance in the same fresh committed report Investigate read
(investigation.md Finding 1), confirmed present but not investigated (out of this ticket's own
named Scope, which names only AGENCY + seed123 COGNITION/AGENCY).
**Do NOT touch:** do not expand this ticket's own `grade_anchors.json` edits (Steps 2-3) to cover
`hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION fields — that stays exclusively in
follow-up (b)'s scope.
**Verify:** both follow-up tickets exist under `tickets/` with valid frontmatter (`layer`, `tags`
from the registries) before this ticket moves to `tickets/done/`.

## Scope Guards

- No edits to `src/domains/adventure/`, `src/ai/goals/adventure_scorer.py`,
  `src/systems/strategic_systems/intelligence.py`, `src/core/updates.py`, or any other production
  strategic-cognition code — Decision 1 makes this a recalibrate-and-disclose ticket, not a
  code-fix ticket. The code fix is Step 9a's follow-up ticket.
- No change to `evaluate_project_switch()`'s own lock/margin/retention logic (STRAT-185/186/187) —
  not touched by this ticket under any circumstance, including inside the Step 9a follow-up's own
  future scope (explicitly excluded there too).
- No porting of `last_defer_reason` — stays `Bounded`/deliberately-not-ported exactly as §2.41
  already states; Step 5 only broadens the *disclosure* text, not the code behavior.
- No addition to `SCORE_TOLERANCE_OVERRIDES` (`tests/simulation_quality/test_grade_regression.py:90-96`)
  — confirmed none of the 6 named run_keys/pillars appear there; a `grade_anchors.json` point-edit
  is the correct shape.
- No extension of the `watchdog_variance` ceiling mechanism to any of the 6 `(run_key, {AGENCY,
  COGNITION})` pairs touched by Steps 2-3 — this is a deterministic, directly-bisected step-change
  (0/0/0 event counts across every sampled trial), not F6 jitter.
- No edits to `hero_guild_routing_seed456_500t`'s ECONOMY or PROGRESSION fields in
  `grade_anchors.json` — deferred entirely to Step 9b's follow-up ticket.
- No edits to any other `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` entry beyond the 6 named run_keys and
  2 named `_1000t` guard tests.
- No modification to `tests/simulation_quality/test_agency_scorer.py` or
  `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` — both must stay
  green unmodified (they bypass the broken emission wiring entirely and are not a regression
  signal for this ticket, per investigation.md's Anti-Drift Hazards).
- Do not run `tests/unit/worldassembly/test_corpus_diversity.py -m slow` as a raw sequential sweep
  during Implement — isolated single-nodeid invocations only, per the
  `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` precedent; use
  `make simq-corpus-diversity-slow-isolated` for the final full-sweep gate.
- Never `pytest tests/` repo-wide (CLAUDE.md Testing Rule).
- Do not delete the `score_ceilings.json` entry in Step 4 — annotate only, preserving audit
  history, matching the parent ticket's own precedent.

## Dependency Map

- Step 1 (fresh re-verification) **must precede** Steps 2, 3, and 4 — their exact values depend on
  Step 1's confirmed numbers, not Investigate's now-hours-old snapshot.
- Steps 2 and 3 are independent of each other (disjoint `grade_anchors.json` keys/pillars) but both
  depend on Step 1.
- Step 4 depends on Step 1/3's confirmed COGNITION value for `simq_routing_test_seed123_500t`
  (the annotation text asserts the new value).
- Steps 5, 6, 7 (doc corrections) are independent of Steps 1-4's exact numeric outcome in mechanism
  (the root-cause finding doesn't change), but should be finalized after Step 1 so any cited
  numbers in the NOTE blocks/addenda are accurate, not stale.
- Step 8 is fully independent of Steps 1-7 — its own fresh idle+induced-load repro is a separate
  verification track.
- Step 9 (follow-up tickets) is independent but should be filed after Decision 1/Step 5-6 are
  finalized, so the follow-up ticket text cites the correct current-state evidence.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause of the AGENCY drift confirmed (or ruled out) as §2.41's `defer_with_reason` gap, via direct evidence | Investigate's Finding 1 (already complete) + Step 5 (durable doc recording) | Manual review of §2.41's broadened text against `event_shapers.py:750-783`/`event_extractor.py:594-630` citations |
| `grade_anchors.json` AGENCY (and COGNITION/AGENCY for seed123 variants) recalibrated to confirmed live values | Steps 1, 2, 3 | `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "<6 run_keys>"` |
| `_1000t` guard tests re-verified fresh and updated to match confirmed current behavior | Step 8 | `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability` and `::test_hero_guild_routing_seed42_1000t_cognition_grade_stability`, isolated |
| `pytest test_grade_regression.py -m "not slow" -q` shows 0 unexplained failures for the 6 named run_keys | Steps 1, 2, 3 | Same scoped `-k` command above, plus full `-m "not slow"` sweep for cross-contamination check |
| `pytest test_corpus_diversity.py -m slow -v` shows the 2 named `_1000t` guards passing | Step 8 | `make simq-corpus-diversity-slow-isolated` (final gate) |

## Anti-Drift Notes

- **This is a recalibrate-and-disclose ticket, not a bug-fix ticket** — the underlying
  adventure-routing decision logic (`AdventureGoalScorer.score()`) still runs correctly every tick;
  only its observability side-effect is gone. Do not let AGENCY's 0/C reading be mistaken for "the
  scorer is broken" during Implement — `tests/simulation_quality/test_agency_scorer.py` staying
  green throughout is expected and correct, not a sign the fix is incomplete.
- **The seed123 pair is not a smaller/different problem** — do not treat it as optional or a
  stretch goal; Decision 2 folds it into the same required recalibration pass as the 4 named items.
- **Do not attempt the `last_routing_family` code fix inside this ticket even if it looks
  tempting/small once you're looking at `intelligence.py:1478-1495` directly** — Decision 1's
  evidence (schema change to `StrategicUpdate`, two call sites, many-to-one `RouteFamily ->
  ProjectKind` mapping) is real and was independently re-derived this session, not just carried
  over from investigation.md's more tentative Risk #1 framing. File Step 9a instead.
- **`_1000t` guard conversion must include an induced-load trial before finalizing shape** — the
  `_500t` sibling's own history (2a proposed, then reverted to 2b after a load-trial found a
  residual) is direct evidence that idle-only sampling under-covers this test family. Do not skip
  the `_busy_loop` mechanism just because Investigate's 6 idle trials were clean.
- **Citation correction**: investigation.md's Finding 1 cites
  `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`'s "Guard 1" as the
  test pinning the `last_defer_reason` absence/presence contract. Direct read this session
  (Plan phase) found `test_defer_property_name_constant_matches_phase_and_extractor` actually lives
  in `tests/unit/observability/test_event_extractor_agency2.py::TestAntiDriftGuards` (matching
  §2.41's own "Verification" field, which cites the correct path) —
  `test_delete_adventure_decision_phase_guards.py` contains a *different* set of guards
  (`test_pipeline_module_has_no_adventure_decision_phase_reference`,
  `test_relocated_eligibility_helpers_are_byte_identical_to_pre_relocation_source`,
  `test_strat_236_v2_evidence_does_not_reference_adventure_decision_phase`,
  `test_adventure_contract_engine_phase_does_not_reference_adventure_decision_phase`), none of
  which pin the `last_defer_reason` contract. Implement should run/cite
  `tests/unit/observability/test_event_extractor_agency2.py` for this guard, not
  `test_delete_adventure_decision_phase_guards.py`, when confirming it stays green.
- **`grade_anchors.json`'s `{"grade","score"}`-only shape must be preserved** — confirmed by direct
  read this session (`python3 -c "import json; ..."` dump of all 6 run_keys' existing pillar
  objects) that no `event_count` or other field lives in this fixture; do not add one.

## Unresolved Questions

None blocking Implement start — Decision 1/2/3 above resolve every open question investigation.md
raised (Risk #1 code-gap-vs-anchor decision, Risk #2 seed123 scope-fold, Risk #3
hero_guild_routing_seed456_500t disposition, the `_1000t` shape question from test_plan.md's New
Test items 1/2). If Step 1's fresh re-verification (Implement time) produces any value that
diverges from Investigate's snapshot tables, Implement must stop and flag it back to this plan
before writing `grade_anchors.json`, rather than silently adjusting the target values.

## Deviations

- **Step 1's fresh re-verification matched investigation.md's snapshot exactly** — no divergence
  found on any of the 6 run_keys (AGENCY 0/0.0/C on all 6, COGNITION 0/0.0/C on the seed123 pair,
  all bit-identical across 2 independent trials each). Steps 2-4 proceeded as planned with no
  re-opened questions.
- **New discovery beyond this plan's named scope, folded into Step 9b's follow-up ticket rather
  than fixed here or left undisclosed**: Step 2's before/after verification (`git stash` A-B
  comparison of `test_grade_within_anchor_band`) surfaced that `simq_routing_test_seed456_500t`
  also carries an unannotated PROGRESSION score-tolerance drift (anchor `-0.6927374301675978` vs.
  fresh actual `-0.15483870967741936`, no `score_ceilings.json` ceiling covers it). This was
  invisible to Investigate's own sampling because `test_grade_within_anchor_band`'s assertion order
  checks `band_failures` before `score_failures` — this run_key's own pre-fix AGENCY band-crossing
  failure was short-circuiting the test before its PROGRESSION score-tolerance failure could ever
  surface. This plan's Step 2/Scope Guards only named `hero_guild_routing_seed456_500t`'s
  ECONOMY/PROGRESSION drift as deferred to Step 9b; Implement broadened Step 9b's follow-up ticket
  (`TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`) to cover this second, newly-found drift too,
  rather than fixing it here (would have violated the Scope Guard against expanding
  `grade_anchors.json` edits beyond the 6 named run_keys) or leaving it undisclosed (would violate
  CLAUDE.md's "no material gap left unstated" rule). No `grade_anchors.json`/`score_ceilings.json`
  edit was made for `simq_routing_test_seed456_500t`'s PROGRESSION field — deferred entirely to that
  follow-up ticket, consistent with how `hero_guild_routing_seed456_500t`'s own ECONOMY/PROGRESSION
  drift was already being handled.
- **Full `FAST_ANCHOR_KEYS` sweep (`-m "not slow"`, all 89 keys) confirmed identical
  32-failed/39-passed count before and after this ticket's edits** (via `git stash`/`git stash pop`
  A-B comparison) — the plan's own Anti-Drift Test Guards section called for this full-sweep
  cross-contamination check; it found zero new failures, only a change in which pillar explains
  each of the 6 named run_keys' pre-existing failure.
- No other deviation from the plan's 9 steps — all edits match the plan's specified scope, file
  paths, and Do-Not-Touch lists exactly.
