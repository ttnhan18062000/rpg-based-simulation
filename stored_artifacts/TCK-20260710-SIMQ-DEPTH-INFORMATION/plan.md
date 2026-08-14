---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-INFORMATION
artifact_type: plan
tags: [simulation-quality, information, world, corpus, calibration]
---

# Implementation Plan — TCK-20260710-SIMQ-DEPTH-INFORMATION

## Closure-Mechanism Decision

**Decision: close as "already-satisfied by prior work" directly (investigation's recommended
option), not folded into Phase 5's Coverage Decision Gate. This mirrors the FACTION sibling
ticket's (`TCK-20260710-SIMQ-DEPTH-FACTION`) closure mechanism exactly, without modification.**

Rationale, grounded in the roadmap doc's actual text (`docs/plans/simq_development_roadmap.md`):

- **Phase 3's own text already names this exact outcome as valid**, without needing Phase 5 at all:
  "Per the correction note above, 'zero new worlds, coverage already adequate, documented and
  closed' is also a valid acceptance outcome for either ticket — this phase does not require
  finding new candidate worlds if honest investigation finds none remain" (line 331-333). This
  ticket's finding — 9/17 covered, 8/17 each with a documented, live-verified reason to stay
  INFORMATION-inert — is precisely that outcome for the second of the phase's "either" tickets.
- **Phase 5 is explicitly a later, corpus-wide, multi-phase gate — not a per-ticket closure
  mechanism.** Its own text (line 400-408): "Once Phases 2–4 have landed... this roadmap's job is
  done and a new, short decision doc... should answer: given the *actual* observed
  cost-per-world-per-pillar from the three waves, is continuing toward full 17-world coverage
  worth it." Phase 4 (`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) has not landed as of this
  ticket. Firing Phase 5 early on the strength of one pillar's one-ticket finding would conflate a
  ticket-scoped "is there any remaining work here" question with a roadmap-scoped "is continuing to
  full coverage worth the cost" question — different questions, different evidence bars. This is
  the identical reasoning the FACTION sibling's plan already applied; it is not FACTION-specific.
- Folding this ticket into Phase 5 would also incorrectly imply the 8 non-candidate worlds are "not
  yet covered but could be," pending a corpus-wide cost/benefit call. That is not what the
  investigation found: those 8 worlds are inert by design (2 structurally incapable — no
  population-bearing settlement module; 2 Stress tier-purity; 1 Regression/baseline fixture; 3 Unit
  single-mechanic isolation). There is no future world of "continuing INFORMATION coverage into
  them" for Phase 5 to weigh — doing so would break either a structural constraint or an isolation
  contract regardless of what Phase 5 eventually decides for the roadmap as a whole. This is a
  closed ticket-level finding, not an open roadmap-level trade-off.
- The roadmap's Phase 3 section already carries a `Closure (2026-07-10, TCK-20260710-SIMQ-DEPTH-
  FACTION done)` blockquote (lines 343-355) that explicitly states "The INFORMATION half... is
  tracked separately and is not affected by this closure." This plan adds a sibling blockquote for
  the INFORMATION half using the same closure shape, not a rewrite of the FACTION one.

Therefore this plan documents the finding as a durable, discoverable closure (in
`eval_matrix_results.md` and `corpus_tier_taxonomy.md`, not just in `staging_artifacts/`), adds the
INFORMATION-half closure blockquote to the roadmap's Phase 3 section (alongside, not replacing, the
existing FACTION-half blockquote), fixes a minor parity-ledger naming gap, and closes the ticket. No
content authoring, no recalibration, no engine change.

## INFRA-256/INFRA-257 Naming-Gap Decision

**Decision: fix it, as a small additive clause — do not leave it.**

The investigation found `INFRA-256`/`INFRA-257`'s prose `text` bodies name `urban_political` + the 6
`CORPUS-E2E-CONTENT-EXPANSION` worlds + `frontier_marches` (8 worlds) by name, but never name the
9th covered world, `unit_information_source`, even though it clearly satisfies both entries'
`support_boundary` (confirmed live: `grep -n "unit_information_source" docs/parity_ledger
/infrastructure.yaml` returns zero hits anywhere in the file). Reasons to fix rather than defer:

- It is a **genuine accuracy gap in a P1, `status: verified` entry** — CLAUDE.md's Traceability
  priority (priority 3, above "Tests and verification" and "Local convenience") weighs toward
  closing documented gaps found while already touching the adjacent territory, not deferring them
  to a future session that would have to rediscover the same gap. An unnamed evidence world
  silently relies on "satisfies `support_boundary`" being re-derived by a future reader rather than
  stated outright.
- The fix is **low-risk and mechanically identical to an already-established pattern in these same
  two entries**: both `INFRA-256` and `INFRA-257` already carry an additive clause for
  `frontier_marches` (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS adds a third scale data point...`)
  that appends new evidence without rewording prior text. Adding one more short, additive sentence
  naming `unit_information_source` (citing `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`) is
  the same shape of edit, at the same low risk.
- It does **not** require a `status` or `v2_evidence` change — both entries are already `verified`
  and their `v2_evidence` cites the code paths, not an exhaustive world list; only the narrative
  `text` field gains one sentence each.
- This is explicitly **not** "changing behavior" (which CLAUDE.md's Authoritative Mechanics Rule
  would require a parity-ledger status change for) — it is closing a documentation-completeness gap
  in an already-`verified` entry, the same category of edit the FACTION sibling's plan considered
  and declined only because no equivalent gap existed for FACTION's `FAC-012` entry. Here the gap
  does exist and is confirmed live, so the FACTION precedent's "leave it alone" outcome does not
  transfer — the two tickets found different facts.

## Summary

This ticket makes **zero code, content, or test changes**. Investigation definitively resolved
UQ-1: of the 17-world corpus, 9 worlds already carry calibrated `information_source_profiles` +
`pending_information_responses` content with `ENABLE_BELIEF_ASSIMILATION: "ON"` (independently
confirmed via two agreeing live signals — compile-time content grep and runtime flag grep, both
landing on the same 9-world set), and the remaining 8 each have a documented, live-verified reason
to stay INFORMATION-inert: 2 structurally incapable (no population-bearing settlement module), 2
Stress tier-purity, 1 Regression/baseline fixture, 3 Unit single-mechanic isolation worlds. The
roadmap's Phase 3 INFORMATION-half goal is already satisfied by four prior, already-closed tickets
(`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`, `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`,
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`, `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`,
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`). This plan's job is to record that finding
durably in the two docs future investigators will actually consult (`eval_matrix_results.md`,
`corpus_tier_taxonomy.md`), add the INFORMATION-half closure blockquote to the roadmap's Phase 3
section (coordinating with the existing FACTION-half blockquote already there, not duplicating or
overwriting it), fix the minor `INFRA-256`/`INFRA-257` naming gap, fill in the ticket's own
Completion Summary, and run a confirmatory verification pass proving no code/content/test drift
occurred during this documentation-only closure. This mirrors the FACTION sibling's plan shape
step-for-step, adapted for INFORMATION's specific world set, tier reasons, and the one additional
parity-ledger fix step FACTION's plan did not need.

## Steps

### Step 1 — Record the 17-world INFORMATION coverage table and UQ-1 resolution in `eval_matrix_results.md`
**Files:** `docs/simulation_quality/eval_matrix_results.md`
**Change:** Append a new top-level section at the end of the file (after the current final line,
~line 2023, immediately following the existing "FACTION Coverage Closure — Phase 3" section added by
the sibling ticket — this becomes the second closure section in the file, not a merge into the
first):

```
## INFORMATION Coverage Closure — Phase 3 (TCK-20260710-SIMQ-DEPTH-INFORMATION)

[17-row coverage table, copied verbatim from investigation.md's "Corpus-Wide INFORMATION Coverage
Re-Verification" table — World / Tier / INFORMATION content? / Live evidence / Reason if not
covered]

**Verdict: 9/17 worlds covered, 8/17 deliberately INFORMATION-inert (2 structurally incapable —
dungeon_crawl, wilderness_survival; 2 Stress tier-purity — crowded_frontier, resource_dense_basin;
1 Regression/baseline fixture — simq_routing_test; 3 Unit single-mechanic isolation —
hero_guild_routing, unit_faction_tension, unit_selfmodel_pilot). No genuinely uncovered,
tier-appropriate INFORMATION candidate remains in the corpus.** This closes the roadmap's Phase 3
INFORMATION-half goal (`docs/plans/simq_development_roadmap.md`) as already-satisfied by prior work
— see that doc's Phase 3 section for the closure record. No content authoring, recalibration, or
grade-anchor changes were made under this ticket; ground truth was re-verified by two independent
live signals against `data/worlds/*/world.yaml` and `config/simulation_quality/profiles/*.yaml`
(not inferred from docs) on 2026-07-12, both landing on the same 9-world set.
```

Reuse the exact table content from `investigation.md`'s coverage table (rows 1-17) verbatim, so this
becomes the durable, discoverable copy of that evidence rather than leaving it only in
`staging_artifacts/` (ticket-scoped, archived to `stored_artifacts/` on close, less discoverable to
a future investigator scanning `eval_matrix_results.md` directly).
**Do NOT touch:** any existing grade table or section in this file, including the "FACTION Coverage
Closure — Phase 3" section immediately above the new one — this is a pure append after it, no edits
to prior content.
**Verify:** Manual read-back — the new section renders correctly after the FACTION section, the
table matches `investigation.md`'s table row-for-row, and `grep -c "^|"` count on the new table
section equals 18 (1 header + 17 world rows). No automated test covers `docs/` content accuracy
(confirmed in `test_plan.md`); this is a documentation-correctness check, not a pytest target.

### Step 2 — Add closure note to `corpus_tier_taxonomy.md`
**Files:** `docs/simulation_quality/corpus_tier_taxonomy.md`
**Change:** Insert one new paragraph immediately after the existing "FACTION coverage closure
(2026-07-10, `TCK-20260710-SIMQ-DEPTH-FACTION`)" paragraph (currently lines 146-153) and before the
`---` divider (currently line 155) — i.e. append a sibling paragraph in the same slot, not replace
the FACTION one. Content:

```
**INFORMATION coverage closure (2026-07-12, `TCK-20260710-SIMQ-DEPTH-INFORMATION`):** the roadmap's
Phase 3 INFORMATION-half re-verified this table's tier assignments against live
`data/worlds/*/world.yaml` content and `config/simulation_quality/profiles/*.yaml` flags (two
independent, agreeing signals) and found them accurate (no staleness) — 9/17 corpus worlds carry
`information_source_profiles`/`pending_information_responses` content with
`ENABLE_BELIEF_ASSIMILATION: "ON"`; the 8 that do not (`dungeon_crawl`, `wilderness_survival`,
`crowded_frontier`, `resource_dense_basin`, `simq_routing_test`, `hero_guild_routing`,
`unit_faction_tension`, `unit_selfmodel_pilot`, all already listed in the table above) are each
INFORMATION-inert by a documented, pre-existing reason (2 structural — no population-bearing
settlement module; 2 Stress tier-purity; 1 Regression/baseline fixture; 3 Unit single-mechanic
isolation), not by omission. No tier reassignment resulted. See `eval_matrix_results.md`'s
"INFORMATION Coverage Closure — Phase 3" section for the full re-verification table.
```

**Do NOT touch:** the "Current tier mapping" table itself (lines 97-139) — no tier assignment
changes; the "Named scale-diversity gaps" section below the divider — those gaps are about
stress-tier scale diversity, not INFORMATION content, and are unaffected by this finding; the
existing FACTION closure paragraph (lines 146-153) — leave verbatim, append after it.
**Verify:** Manual read-back — paragraph renders in the correct location directly after the FACTION
closure paragraph, does not alter any existing table row, tier assignment, or the FACTION paragraph
itself.

### Step 3 — Add INFORMATION-half closure blockquote to `simq_development_roadmap.md`'s Phase 3 section
**Files:** `docs/plans/simq_development_roadmap.md`
**Change:** Add a new dated closure blockquote immediately after the existing FACTION closure
blockquote (currently lines 343-355) and before the `---` divider (currently line 357) — i.e.
append a second blockquote in the same slot, in the same style, not edit the FACTION one:

```
> **Closure (2026-07-12, `TCK-20260710-SIMQ-DEPTH-INFORMATION` done) — INFORMATION half closed as
> already-satisfied.** Investigation re-verified all 17 corpus worlds against live
> `data/worlds/*/world.yaml` content and `config/simulation_quality/profiles/*.yaml` flags (two
> independent, agreeing signals) and confirmed 9/17 already carry calibrated
> `information_source_profiles`/`pending_information_responses` with `ENABLE_BELIEF_ASSIMILATION:
> "ON"`, with the remaining 8 each having a documented, live-verified reason to stay
> INFORMATION-inert (2 structurally incapable, 2 Stress tier-purity, 1 Regression/baseline fixture,
> 3 Unit single-mechanic isolation — not an oversight — see `docs/simulation_quality
> /eval_matrix_results.md`'s "INFORMATION Coverage Closure — Phase 3" section). Zero content
> authoring, recalibration, or engine work was needed or performed. This is the "zero new worlds,
> coverage already adequate, documented and closed" outcome this section's Acceptance Signal
> explicitly names as valid. This closure was decided at the ticket level, not deferred to Phase 5,
> for the same reasoning the FACTION-half closure above already establishes (Phase 5 is a later,
> corpus-wide gate that fires once Phases 2-4 have all landed and asks a different question). **Both
> halves of Phase 3 (FACTION and INFORMATION) are now closed** — this phase requires no further
> tickets.
```

**Do NOT touch:** Phase 2, Phase 4, or Phase 5 sections' own text; the existing FACTION closure
blockquote (lines 343-355) — leave verbatim, append after it, do not merge the two into one
blockquote (they have different dates, different ticket IDs, and different per-world reasoning and
should stay independently attributable). Do not fire/pre-decide Phase 5.
**Verify:** Manual read-back — new blockquote renders correctly directly after the FACTION
blockquote, does not alter the FACTION blockquote's text, and the "both halves... closed" sentence
is added only in the new (INFORMATION) blockquote, not retrofitted into the FACTION one.

### Step 4 — Fix the `INFRA-256`/`INFRA-257` naming gap in `docs/parity_ledger/infrastructure.yaml`
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Per the "INFRA-256/INFRA-257 Naming-Gap Decision" above, append one additive sentence
to each entry's `text` field naming `unit_information_source`, matching the existing additive style
already used for `frontier_marches` in both entries (append-only, do not reword any existing
sentence):

For `INFRA-256` (currently the `text:` block ending at line 3124, just before `status: verified` at
line 3125), append after the existing `frontier_marches` paragraph:

```
    TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO adds a fourth data point at unit-tier scale:
    data/worlds/unit_information_source/world.yaml (16 entities/1 region, a deliberate
    single-mechanic INFORMATION-isolation world) seeds 2 information_source_profiles/
    pending_information_responses entries (town_notice_board, hometown_danger) targeting pop_0,
    with ENABLE_BELIEF_ASSIMILATION=ON in config/simulation_quality/profiles
    /unit_information_source.yaml. INFORMATION pillar grade measured B, confirming the mechanism
    holds at the smallest tested scale as well as the largest (frontier_marches).
```

For `INFRA-257` (currently the `text:` block ending at line 3194, just before `status: verified` at
line 3195), append after the existing `dungeon_crawl and wilderness_survival remain documented
INFORMATION skips` sentence:

```
    TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO seeded the same 2-entry pattern in
    unit_information_source (see INFRA-256), the 9th and final world with this content as of
    2026-07-12 (TCK-20260710-SIMQ-DEPTH-INFORMATION re-verification) — belief_assimilated/
    belief_updated calibration_hits confirmed > 0 for that world as well.
```

Do not change `status`, `priority`, `v2_evidence`, `proof_type`, `test_path`, or `divergence_note`
on either entry — both stay `verified`/`P1` with unchanged evidence-path citations; only the
narrative `text` field gains one additive sentence each, consistent with this fix being a
documentation-completeness correction, not a behavior or status change.
**Do NOT touch:** `INFRA-258`, `INFRA-259`, `INFRA-260`, or any other entry in this file — only
`INFRA-256`/`INFRA-257`'s `text` fields are touched, and only by append.
**Verify:** `grep -n "unit_information_source" docs/parity_ledger/infrastructure.yaml` returns 2
hits (one in each entry's new sentence), where it previously returned 0; `python3 -c "import yaml;
yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` (or the project's existing parity
ledger schema-validation tooling, if one exists — check `docs/parity_ledger/schema.json` /
`tools/` for a validator script before assuming none exists) parses without error after the edit.

### Step 5 — Verify no `docs/plans/audit_fix_plan.md` entry requires closure
**Files:** none (read-only verification step)
**Change:** Confirm via search that `audit_fix_plan.md` has no open entry referencing INFORMATION
coverage or this ticket's scope. Already checked during planning: `grep -n -i "information"
docs/plans/audit_fix_plan.md` returns 3 hits — line 661 (a standing structural-gap note about
COGNITION/ECONOMY/FACTION/INFORMATION/SOCIAL all being C due to 27 engine emission gaps — an
already-tracked, unrelated finding, not this ticket's content-authoring scope), line 713 (a table
row citing INFORMATION's C→B move — historical record of already-completed work, not an open item),
and line 793 (`TCK-20260701-SIMQ-EMIT-INFORMATION2`, an already-closed prior ticket reference). None
is an open entry in this ticket's scope. Record this confirmation in the ticket's Implementation
Notes (Step 6) rather than editing `audit_fix_plan.md`, since there is nothing there to close.
**Do NOT touch:** `docs/plans/audit_fix_plan.md` — no entry in that file needs a status change.
**Verify:** `grep -n -i "information" docs/plans/audit_fix_plan.md` output matches the three hits
above; no other output.

### Step 6 — Fill in the ticket's Completion Summary and related sections
**Files:** `tickets/inprogress/TCK-20260710-SIMQ-DEPTH-INFORMATION.md`
**Change:** Fill in:
- `## Status` → `DONE`
- `## Implementation Notes` — record the closure-mechanism decision (close as already-satisfied,
  not folded into Phase 5) with the rationale from this plan's "Closure-Mechanism Decision" section,
  the "INFRA-256/INFRA-257 Naming-Gap Decision" (fixed, not deferred) with its rationale, and the
  Step 5 `audit_fix_plan.md` check result.
- `## Test Summary` — record that no code/content changes were made; cite the confirmatory
  regression sweep from Step 7 (test commands + pass result) as proof of zero drift, per
  `test_plan.md`'s "Scoped Pytest Commands".
- `## Files Changed` — list exactly the 4 doc files touched: `docs/simulation_quality
  /eval_matrix_results.md`, `docs/simulation_quality/corpus_tier_taxonomy.md`,
  `docs/plans/simq_development_roadmap.md`, `docs/parity_ledger/infrastructure.yaml`.
- `## Completion Summary` — full finding: UQ-1 resolved definitively (0 legitimate candidates among
  the 8 remaining worlds), roadmap Phase 3 INFORMATION-half closed as already-satisfied by prior
  work (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`, `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`,
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`, `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`,
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`), zero code/content/test changes beyond the
  minor `INFRA-256`/`INFRA-257` naming-gap fix, closure recorded durably in `eval_matrix_results.md`
  and `corpus_tier_taxonomy.md`, and note that both halves of Phase 3 (FACTION and INFORMATION) are
  now closed per the roadmap doc.
**Do NOT touch:** the ticket's `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, or
`## Assumptions / Open Questions` sections — those are the historical record of what was originally
asked and found; do not rewrite them to retroactively match the closure outcome.
**Verify:** Ticket file renders with all sections filled; `## Status` reads `DONE`.

### Step 7 — Verification pass: confirm zero code/content/test drift
**Files:** none (verification only)
**Change:** Run a scope-boundary check and a confirmatory regression sweep:
1. `git diff --stat` (or equivalent staged diff) should show changes touching only: the 4 doc files
   from Steps 1-4, the ticket file (Step 6), and `staging_artifacts/TCK-20260710-SIMQ-DEPTH-
   INFORMATION/` artifacts (this `plan.md` itself, plus the already-existing `investigation.md`/
   `test_plan.md`). Explicitly confirm **zero** changes under `src/`, `data/worlds/`, `tests/`,
   `tests/simulation_quality/fixtures/grade_anchors.json`, or any `docs/parity_ledger/*.yaml` entry
   other than `INFRA-256`/`INFRA-257`'s `text` fields.
2. Run the confirmatory regression commands from `test_plan.md`'s "Scoped Pytest Commands" section
   (`test_world_compiler.py`, `test_assembly.py`, `test_corpus_diversity.py`,
   `test_phase5_information_belief_scenarios.py`, `test_grade_regression.py`) and confirm all pass
   — this proves the documentation-only closure (plus the minor parity-ledger text edit) did not
   accidentally destabilize anything.
3. Re-run the two live grep sweeps from `investigation.md`'s Coverage Re-Verification section
   (`grep -c "information_source_profiles\|pending_information_responses" data/worlds/*/world.yaml`
   and `grep -rn "ENABLE_BELIEF_ASSIMILATION" config/simulation_quality/profiles/*.yaml`) to confirm
   the two independent signals still agree on exactly the same 9-world set after this ticket's
   doc-only edits land — catches any accidental content edit disguised as a "doc-only" change.
**Do NOT touch:** anything — this step only runs checks and reports results, no edits.
**Verify:** `git diff --stat` output matches the expected file list above; all pytest commands from
`test_plan.md` exit 0 (or any failure is confirmed pre-existing/unrelated per the FACTION sibling's
own Step 6 precedent — report honestly, do not silently round up to a clean pass); the two grep
sweeps still return exactly the same 9-world set as `investigation.md`.

## Scope Guards

Explicit list of things this plan must **not** touch, per the ticket's Out of Scope section and the
investigation's Anti-Drift Hazards:

- Do NOT author `information_source_profiles`/`pending_information_responses` into any of the 8
  non-candidate worlds (`dungeon_crawl`, `wilderness_survival`, `crowded_frontier`,
  `resource_dense_basin`, `simq_routing_test`, `hero_guild_routing`, `unit_faction_tension`,
  `unit_selfmodel_pilot`) — each has a documented structural blocker, tier-purity default, or
  isolation contract that content authoring would break or falsely claim to satisfy.
- Do NOT touch `tests/simulation_quality/fixtures/grade_anchors.json` or `FAST_ANCHOR_KEYS` in
  `tests/simulation_quality/test_grade_regression.py` — no recalibration occurred, no new anchor
  entries are warranted.
- Do NOT touch any `data/worlds/*/world.yaml` or `data/worlds/*/resolved/world.resolved.yaml` file
  — no world content changes.
- Do NOT touch any `config/simulation_quality/profiles/*.yaml` file — no `ENABLE_BELIEF_ASSIMILATION`
  flag changes.
- Do NOT touch `grade_anchors.json`.
- Do NOT touch any `src/` file — Pattern-6 plumbing (`src/worldbuilding/schema.py`,
  `src/worldassembly/schema.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/resolver.py`,
  `src/domains/information/*.py`, `src/cognition/self_model_phase.py`, `src/engine/pipeline.py`,
  `src/observability/event_extractor.py`) is confirmed correct and unmodified; this is a
  documentation-only closure plus one minor parity-ledger text fix.
- Do NOT touch `INFRA-258`, `INFRA-259`, or `INFRA-260` in `docs/parity_ledger/infrastructure.yaml`
  — only `INFRA-256`/`INFRA-257`'s `text` fields are touched, by append only; do not change `status`,
  `priority`, `v2_evidence`, `proof_type`, `test_path`, or `divergence_note` on any entry.
- Do NOT touch Branch B (`self_model.knowledge.unknowns`/`SelfModelUpdatePhase`/
  `ENABLE_SELF_MODEL_COGNITION`) or the paid-information marketplace path
  (`InformationNeedDetector`/`state.information_providers`/`PaidInformationTransactionSystem`) — both
  explicitly out of scope per the ticket, and no evidence surfaced during investigation that either
  needs touching for this closure.
- Do NOT touch any existing table row, grade value, or anchor entry in `eval_matrix_results.md`, the
  "Current tier mapping" table in `corpus_tier_taxonomy.md`, or the existing FACTION closure
  paragraph/blockquote in either `corpus_tier_taxonomy.md` or `simq_development_roadmap.md` — Steps
  1-3 are pure, coordinated additions alongside the FACTION sibling's existing closure content, not
  edits to it.
- Do NOT touch the Phase 2, Phase 4, or Phase 5 sections of `simq_development_roadmap.md`, and do
  NOT fire/pre-decide Phase 5's Coverage Decision Gate — see "Closure-Mechanism Decision" above.
- Do NOT touch the sibling ticket `TCK-20260710-SIMQ-DEPTH-FACTION`, its ticket file, or its own
  `stored_artifacts/` — that ticket is already done and closed; this ticket only reads its plan.md
  as a format precedent.
- Do NOT add any new test — `test_plan.md` confirms none are required for this closure path.
- Do NOT touch `docs/plans/audit_fix_plan.md` — Step 5 confirms no open, in-scope entry exists there.

## Dependency Map

- Steps 1, 2, 3, 4, and 5 are independent of each other (different files, no shared state) and may
  be done in any order.
- Step 2 and Step 3 each logically follow the existing FACTION-half content in their respective
  files (append immediately after it), but do not depend on Step 1 or Step 4 being done first — all
  four content-writing steps can be sequenced arbitrarily.
- Step 6 (ticket Completion Summary) depends on Steps 1-5 being complete, since it must accurately
  cite what was changed (including the exact 4-file list from Step 4's addition) and confirm the
  `audit_fix_plan.md` check result.
- Step 7 (verification pass) depends on Steps 1-6 being complete, since it verifies the full diff
  produced by this plan and re-runs regression tests against the final state.

## Acceptance Criteria Map

The ticket's original 9 acceptance criteria mostly presuppose that content authoring occurs
(candidate worlds selected, `information_source_profiles`/`pending_information_responses` seeded,
recalibration run, corpus-wide `make evaluate` sweep). UQ-1 resolved that zero legitimate candidates
exist, so those criteria are **satisfied vacuously by prior work already done under other tickets**,
not by any action taken under this ticket.

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Investigate phase produces a re-verified candidate list, stale-premise gap reconciled (incl. possibility of zero) | Already done in `investigation.md`; durably recorded in `eval_matrix_results.md` by Step 1 | Step 1 manual read-back |
| IF candidates exist: each world has seeded `information_source_profiles`/`pending_information_responses` | N/A — vacuous, zero candidates found (by design, not gap) | — |
| IF candidates exist: each world compiles 0 warnings, >=60% alive floor | N/A — vacuous | — |
| IF candidates exist: each world's INFORMATION grade moves off C, grade-anchor entries added | N/A — vacuous | — |
| `make evaluate` full corpus sweep exits 0 with 0 regressions | Not required for a no-content-change closure per `test_plan.md`; Step 7's scoped regression sweep substitutes as the confirmatory check | Step 7 |
| `INFRA-256`/`INFRA-257` extended with `v2_evidence` for newly selected worlds (or justified as N/A) | No new worlds selected, so no `v2_evidence` extension; instead the pre-existing naming gap (unit_information_source) is closed | Step 4 |
| `eval_matrix_results.md`/`corpus_tier_taxonomy.md` updated with new worlds' grade tables/tier notes | Satisfied via closure notes instead of new-world tables (no new world) | Steps 1, 2 |
| Newly-discovered engine bug filed as its own ticket | N/A — no engine bug found | — |
| IF zero candidates: ticket closed/re-scoped with finding documented, not silently abandoned | Satisfied — Steps 1, 2, 3, 6 durably document the finding and close the ticket | Steps 1, 2, 3, 6 |

**This plan's own acceptance criteria (the real closure bar for this ticket):**

| This plan's AC | Implemented by step(s) | Verified by |
|---|---|---|
| 17-world coverage table + UQ-1 resolution durably recorded in `eval_matrix_results.md` | Step 1 | Step 1 manual verify |
| Closure note added to `corpus_tier_taxonomy.md`, coordinated with (not overwriting) the FACTION note, tier table unchanged | Step 2 | Step 2 manual verify |
| Roadmap Phase 3 section records INFORMATION-half closure alongside the existing FACTION-half blockquote, notes both halves closed | Step 3 | Step 3 manual verify |
| `INFRA-256`/`INFRA-257` naming gap fixed via additive clause, no status/evidence-path change | Step 4 | Step 4 grep + YAML-parse check |
| `audit_fix_plan.md` confirmed to have no open, in-scope entry | Step 5 | Step 5 grep check |
| Ticket's Completion Summary/Status/Test Summary/Files Changed fully filled in | Step 6 | Step 6 manual verify |
| Zero code/content/test drift beyond the 4 planned doc edits; regression sweep green; 9-world signal-agreement re-confirmed | Step 7 | Step 7 `git diff --stat` + pytest commands + grep re-sweep |

## Anti-Drift Notes

- **The strongest temptation to guard against is "completing" this ticket by forcing content into
  one of the 8 non-candidate worlds to satisfy the letter of the original 9 ACs**, especially
  `hero_guild_routing` or `unit_faction_tension`, both of which compose `frontier_village_core` (a
  population-bearing settlement module) and could technically host INFORMATION content. The
  investigation explicitly found this would be wrong — doing so would break each world's
  single-variable isolation contract. Do not do this under any interpretation of "finishing the
  ticket."
- **Do not read a settlement module's presence, or a `module_type: settlement` label, as sufficient
  evidence of an INFORMATION candidate.** `crowded_frontier`, `resource_dense_basin`,
  `hero_guild_routing`, and `unit_faction_tension` all compose a population-bearing settlement module
  yet are correctly INFORMATION-inert by design. `wilderness_survival`'s `survivor_camp_shelter`
  carries the `module_type: settlement` label but has zero `population_recipes` — the correct test
  is presence of `population_recipes` in the composed modules, not the `module_type` string or
  label.
- **Do not conflate `state.information_providers`/`InformationNeedDetector`/
  `PaidInformationTransactionSystem` with `state.information_source_profiles`/
  `InformationBeliefPhase`.** Two separate registries feeding two separate, independently-gated
  systems. Do not credit the paid-information marketplace path as INFORMATION coverage for any
  world — it remains orphaned corpus-wide and is unaffected by this closure.
- **Re-verify against live `data/worlds/*/world.yaml` and `config/simulation_quality/profiles/*.yaml`
  at implementation time, not just against this plan's or the investigation's tables**, per the
  investigation's own hazard: "corpus content can change between ticket pickup and implementation."
  If the live count has changed (e.g. a new world was added, or an existing world's content was
  removed), pause and flag rather than proceeding on stale numbers. Two independent signals
  (compile-time content, runtime flag) should still agree — if they diverge, that itself is a signal
  worth investigating before continuing this ticket's closure.
- **Do not fire or pre-decide Phase 5's Coverage Decision Gate** as part of this ticket — per the
  Closure-Mechanism Decision above, Phase 5 fires later, once Phases 2-4 have all landed, and asks a
  different (roadmap-wide cost/benefit) question than this ticket answers. Do not create or populate
  anything under `tickets/todos/simq-roadmap-phase5-coverage-gate/` as part of closing this ticket.
- **Do not merge Step 3's new blockquote into the existing FACTION-half blockquote** — keep them as
  two independently-dated, independently-attributable blockquotes in the same Phase 3 section, per
  the roadmap doc's existing convention of stacking dated correction/closure blockquotes rather than
  editing prior ones in place.
- **The `INFRA-256`/`INFRA-257` naming-gap fix (Step 4) is the one place this ticket diverges from
  the FACTION sibling's plan shape** (which found no equivalent gap in `FAC-012` and left it
  untouched). Do not over-extend this precedent into rewriting other parts of `INFRA-256`/`INFRA-257`
  beyond the two additive sentences specified — the fix is narrowly scoped to naming the one missing
  world.
