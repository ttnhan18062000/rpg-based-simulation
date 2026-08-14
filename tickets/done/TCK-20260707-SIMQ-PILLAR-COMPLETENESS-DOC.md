---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC
phase: done
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, documentation, world]
---

# TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC

## Title
Document the pillar-completeness research conclusion: no new top-level SimQ pillar is justified

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2 performed pillar-completeness
research (per user request: "consideration of new pillars if warranted") and reached a conclusion
that is not yet recorded anywhere durable: **no new top-level pillar is justified.** Four candidate
dimensions were checked and each is already owned by a dedicated system outside SimQ:

- **Determinism/replay-fidelity** — owned by `tests/certification/`, `tests/integration/kernel/`
  (including a dedicated `test_long_run_determinism.py`), `tests/integration/observability/
  test_phase28_observability_determinism.py`, `tests/unit/kernel/test_replay_determinism.py`
  (investigation.md §2.2)
- **Performance/tick-time budget** — owned by `tests/perf/` (14+ files) plus per-phase budget tests,
  tied to `docs/engine/performance_contract.md`'s hardware classes; SimQ's own overhead is separately
  budgeted in `tests/simulation_quality/test_performance.py` (investigation.md §2.3)
- **Save/checkpoint integrity** — owned by `tests/integration/kernel/
  test_checkpoint_reproducibility.py` and `tests/unit/engine/test_scenario_checkpointer.py`
  (investigation.md §2.4)
- **Content/catalog health** — owned by `src/content/validator.py`'s `CAT-REL-001` through
  `CAT-REL-011` rules (investigation.md §2.5)

The contract's own §1 ("What this module is NOT") already scopes SimQ away from determinism and
performance explicitly; a SimQ pillar covering either would duplicate existing test domains and
violate that scope boundary.

One genuine, narrow gap **was** found (investigation.md §2.6): `building_sabotage` (pipeline phase
15, `src/engine/sabotage.py::BuildingSabotageSystem.resolve()`) is a live, non-dead mechanic —
mutates `building_updates` (hp_delta, functional_set) on `SABOTAGE`/`ENTITY_ACT` intents — exercised
by real corpus content (`urban_political`'s resolved world spec and
`data/content/world_modules/trading_company_hub.yaml`), but emits no
`ObservabilityEventEnvelope`/`SimulationEvent` and is invisible to all 10 pillars'
event-type/tag lists, including WORLD's. Per the contract's own §7.1 vs §7.2 extensibility
distinction, this is a **new scoring rule under the existing WORLD pillar**, not grounds for an 11th
top-level pillar — `FACTION` is a plausible secondary owner (given `urban_political`'s
faction-conflict framing) but WORLD is the cleaner primary per the §7.3 conflict-detection rule (no
existing pillar currently claims building-state events). This finding is tracked separately as
`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`, which cites this ticket's output as its evidence
source.

## Scope
1. Read `docs/simulation_quality/quality_scoring_contract.md` §7 (Extensibility Protocol, lines
   1008-1067: §7.1 Adding a New Pillar, §7.2 Adding a Scoring Rule to an Existing Pillar, §7.3
   Conflict Detection Rules, §7.4 Configuring Quality Profiles) to confirm the natural home for this
   conclusion. Per that read (already performed during epic scoping): §7 is the extensibility
   protocol itself — a completed pillar-completeness audit is a direct, citable precedent for how
   that protocol was applied, so add a new **§7.5 "Pillar Completeness Audit (2026-07)"** subsection
   to `quality_scoring_contract.md` rather than creating a new standalone doc. This keeps the
   authoritative extensibility section self-documenting with its own precedent case, avoiding a
   second doc that could drift out of sync with §7's rules over time.
2. In the new §7.5 subsection, document:
   - The 4 candidate dimensions checked and exactly which existing system owns each (cite the file
     lists above / investigation.md §2.2-2.5 directly, verified against current repo state — do not
     just copy the investigation's text without re-confirming the cited files still exist).
   - The `building_sabotage` finding and why it is a WORLD-pillar rule addition, not a new pillar
     (cite investigation.md §2.6 and the contract's own §7.1/§7.2/§7.3 rules being applied).
   - The overall conclusion: no new top-level pillar is justified at this time.
3. Cross-reference `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` from the new §7.5 subsection as the
   ticket implementing the one identified follow-up.
4. Run `make knowledge-index-update` since this modifies a file under `docs/`.

## Out of Scope
- Implementing the `building_sabotage` event emission or WORLD-pillar scoring rule itself — that is
  `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`'s scope; this ticket is documentation-only.
- Re-running the pillar-completeness research itself — investigation.md §2 already performed it;
  this ticket transcribes and durably records the conclusion, re-verifying only that cited file
  paths still exist (not re-deriving the analysis from scratch).
- Any change to `quality_scoring_contract.md` outside the new §7.5 subsection.
- Creating a second, separate doc under `docs/simulation_quality/` — Scope item 1 already decided
  against this in favor of extending §7 in place.

## Acceptance Criteria
- [ ] `docs/simulation_quality/quality_scoring_contract.md` has a new §7.5 subsection documenting
      the pillar-completeness conclusion
- [ ] All 4 candidate dimensions and their owning systems are cited with currently-valid file paths
      (re-verified, not just copied from investigation.md)
- [ ] The `building_sabotage` finding is documented with a cross-reference to
      `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`
- [ ] `make knowledge-index-update` run successfully after the doc change
- [ ] `python3 tools/validate_frontmatter.py docs/simulation_quality/quality_scoring_contract.md
      --content-type doc` passes (frontmatter unaffected by a body-only addition, but re-verify)

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (parent epic)
- TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL — depends on this ticket's output for citation; must
  land after this one

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2 (full pillar-completeness
  research: method §2.1, 4 redundant candidates §2.2-2.5, the `building_sabotage` finding §2.6,
  overall conclusion §2.7)
- `docs/simulation_quality/quality_scoring_contract.md` §1 ("What this module is NOT" scope table),
  §7 (Extensibility Protocol — target location for this ticket's new §7.5)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` (see Related Docs)

## Related Code Areas
None — documentation-only ticket. (`src/engine/sabotage.py` is cited but not modified here; its
modification is `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`'s scope.)

## Assumptions / Open Questions
- Assumes the 4 "owning system" file lists from investigation.md §2.2-2.5 still accurately reflect
  the repo at implementation time — Scope item 2 requires re-confirming these paths exist, not
  trusting the investigation's snapshot blindly (self-evident intent, hence hotfix tier; if
  re-verification finds a cited file has moved/been deleted, correct the citation rather than
  treating it as a scope-invalidating surprise).

## Implementation Notes
Added `### 7.5 Pillar Completeness Audit (2026-07)` to
`docs/simulation_quality/quality_scoring_contract.md`, directly after `### 7.4 Configuring Quality
Profiles` and before the `## 8. Data Flow & Persistence` separator (so it lands inside the
Extensibility Protocol section as its own precedent case, per the ticket's Scope item 1 decision).

Before writing, discovered that `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md`
(the ticket's own cited evidence source) does not exist on disk — `staging_artifacts/` currently
contains only `TCK-20260702-SIMQ-UPLIFT2-INFORMATION/`. This is the exact same citation-rot pattern
already root-caused and documented by `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING`
(gitignored pre-ticket staging file, epic-tier ticket never ran a Finalize/migrate step, lost from
the working tree). Rather than block on this, used the full transcription of investigation.md §2
already embedded verbatim in this ticket's own Request Summary (lines 30-64, written during epic
scoping when the investigation doc still existed) as the content source, and independently
re-verified every cited file path against current repo state per Scope item 2 and the Assumptions
section's instruction to correct rather than block on drift:

- Determinism/replay-fidelity, performance, and checkpoint-integrity citations verified unchanged
  (`tests/certification/`, `tests/integration/kernel/test_long_run_determinism.py`,
  `tests/integration/observability/test_phase28_observability_determinism.py`,
  `tests/unit/kernel/test_replay_determinism.py`, `tests/perf/` (38 files, up from "14+" cited —
  updated the count), `docs/engine/performance_contract.md`, `tests/simulation_quality/test_performance.py`,
  `tests/integration/kernel/test_checkpoint_reproducibility.py`,
  `tests/unit/engine/test_scenario_checkpointer.py` — all exist).
- **Corrected one citation**: the ticket's "CAT-REL-001 through CAT-REL-011" was checked against
  `src/content/validator.py` directly (`grep -n "CAT-REL-[0-9]" `) — the actual rule ID range is
  non-contiguous: `CAT-REL-001`–`CAT-REL-004`, then `CAT-REL-011`–`CAT-REL-019`, plus a `CAT-REL-099`
  fallback. There is no `CAT-REL-005` through `CAT-REL-010`. The new §7.5 cites the corrected,
  verified range instead of copying the stale "through CAT-REL-011" phrasing.
- `building_sabotage` finding verified against `src/engine/sabotage.py::BuildingSabotageSystem.resolve()`
  directly (SABOTAGE/ENTITY_ACT(action=SABOTAGE) intents, mutates `building_updates.hp_delta`/
  `functional_set`, no observability emission in the file) and cross-checked pipeline phase 15
  against `docs/engine/authoritative_pipeline.md:35` (`building_sabotage` row, confirmed).
  `data/content/world_modules/trading_company_hub.yaml` and
  `data/worlds/urban_political/resolved/world.resolved.yaml` both confirmed to exist.
- WORLD pillar's event-type/tag list (§5 WORLD DYNAMICS, lines 866-921) re-read directly to confirm
  no existing tag covers building damage/functional-state changes, supporting the §7.3
  no-dual-ownership reasoning cited in the new subsection.

No deviation from the ticket's Scope beyond the one corrected citation (CAT-REL range), which the
ticket's own Assumptions section explicitly anticipated and pre-authorized ("if re-verification
finds a cited file has moved/been deleted, correct the citation rather than treating it as a
scope-invalidating surprise" — extended here to a corrected rule-ID range, same principle).

## Test Summary
Documentation-only change; no code paths affected. Verified: (1)
`python3 tools/validate_frontmatter.py docs/simulation_quality/quality_scoring_contract.md
--content-type doc` → `OK: 1 file(s) checked — no violations`; (2) `grep -n "^## 7\|^### 7\."` on
the file confirms `### 7.5 Pillar Completeness Audit (2026-07)` is correctly nested under `## 7.
Extensibility Protocol`, after `### 7.4`; (3) every file path cited in the new §7.5 subsection was
independently re-verified to exist via direct `ls`/`grep` checks (see Implementation Notes); (4)
`make knowledge-index-update` ran successfully (`Incremental update complete: 5485 chunks total (4
files re-embedded, 1953 from cache, 0 deleted)`).

## Files Changed
- `docs/simulation_quality/quality_scoring_contract.md` — added `### 7.5 Pillar Completeness Audit
  (2026-07)` subsection

## Completion Summary
Added `### 7.5 Pillar Completeness Audit (2026-07)` to `docs/simulation_quality/quality_scoring_contract.md`,
recording the pillar-completeness research conclusion: no new top-level SimQ pillar is justified. All
4 candidate dimensions (determinism/replay-fidelity, performance/tick-time budget, save/checkpoint
integrity, content/catalog health) were re-verified against current repo state and confirmed each is
already owned by a dedicated system outside SimQ (one citation corrected: `CAT-REL` rule ID range is
non-contiguous, `001`-`004` + `011`-`019` + `099` fallback, not "through CAT-REL-011"). The one genuine
gap found — `building_sabotage` (pipeline phase 15) mutating `building_updates` with no observability
emission — was documented as a new WORLD-pillar scoring rule (not an 11th pillar), cross-referenced to
`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` as its implementing ticket. `make knowledge-index-update`
ran successfully; `validate_frontmatter.py` passed; all cited file paths independently re-verified.
Documentation-only change, no code paths affected. done-checker returned READY_TO_CLOSE on first pass.
