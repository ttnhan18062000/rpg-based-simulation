---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-FAME-DERIVER-LEGEND-FACT
artifact_type: test_plan
tags: [social, strategy]
---

# Test Plan — TCK-20260905-FAME-DERIVER-LEGEND-FACT

## Regression Surface

**Unit — culture/fidelity sibling suites (must pass unmodified — this ticket must not touch
either sibling's read/write behavior):**
- `tests/unit/domains/culture/test_culture_deriver.py`
- `tests/unit/domains/culture/test_culture_exporter.py`
- `tests/unit/domains/chronicle/test_fidelity_deriver.py`
- `tests/unit/domains/chronicle/test_fidelity_exporter.py`

**Unit — Chronicle substrate (unchanged, read-only consumer):**
- `tests/unit/chronicle/test_significance.py`
- `tests/unit/chronicle/test_chronicle_compiler.py`
- Chronicle grouper tests under `tests/unit/domains/chronicle/` (if any exist beyond the fidelity
  ones above)

**Unit — Perception domain (must pass unmodified; a new `WorldSignal` kind branch, if added, must
not change existing classification behavior for the 5 already-documented kind groups):**
- `tests/unit/domains/perception/test_phase12_signal_salience_evaluator.py`
- `tests/unit/domains/perception/test_phase12_attention_focus_service.py`
- `tests/unit/domains/perception/test_phase12_perception_filter_service.py`

**Unit — Motivation domain (must pass unmodified — no new `FameState`/`LegendFact` parameter is
added to `compute_bias_multiplier()` in this ticket):**
- Existing motivation service unit tests under `tests/unit/domains/motivation/` (or wherever
  `E62C-MOTIVATION-OVERLAY`'s own suite lives, per that stored artifact)

**Unit — Coming of Age (must pass unmodified — `_CANDIDATE_ROLES` is not extended):**
- `tests/unit/strategic/test_coming_of_age_archetype_choice.py`

**Unit — Social consequence events (must pass unmodified — `LegendFact` must never touch this
path):**
- Existing tests covering `evaluate_social_consequence()` / `LegendaryArrivalEvent` (locate via
  `tests/unit/social/` — the same suite exercised by `TCK-20260904-REPUTATION-LOCALITY-SCOPE`)

**Integration — Campaign orchestration (episode-boundary wiring must not disturb existing
exporters):**
- `tests/integration/culture/test_culture_drift_acceptance.py`
- `tests/unit/domains/campaigns/test_fidelity_wiring.py`
- `tests/integration/campaigns/` (broad campaign orchestration suite)
- `tests/integration/scenarios/test_campaign_chronicle.py`
- `tests/integration/scenarios/test_campaign_runtime.py`

**Architecture guards (must pass unmodified — precedent write-path guards for sibling fields):**
- `tests/architecture/test_fidelity_write_paths.py`
- `tests/architecture/test_social_write_paths.py`
- `tests/architecture/test_clan_reputation_write_paths.py`
- `tests/architecture/test_phase18_import_boundaries.py` (watch for the same pinned-import-line
  drift the sibling ticket hit if a new exporter import shifts line numbers in
  `orchestrator.py` — re-pin deliberately if so, do not silently ignore a failure here)

## New Tests Required

Per AC (ticket's Acceptance Criteria, in order):

1. **`test_fame_deriver_attributes_two_subjects_distinctly`**
   - Category: unit
   - Verifies: `FameDeriver.derive()` on a `ChronicleHierarchy` containing a `quest_completed`
     entry for `subject_id="1"` and a `HERO` `entity_death` entry (`payload={"entity_role":
     "HERO"}`) for `subject_id="2"` produces two distinct, non-zero `FameState` entries, each
     correctly keyed to its own `subject_id`, with the third distractor entity (present in neither
     entry) absent from the result dict.
   - Where: `tests/unit/domains/fame/test_fame_deriver.py` (new module directory, mirroring
     `tests/unit/domains/culture/test_culture_deriver.py`'s own file shape/`_hierarchy()`/`_entry()`
     helpers)

2. **`test_fame_deriver_only_option_b_events_contribute`**
   - Category: unit
   - Verifies: a non-HERO `entity_death` entry and a `faction_shift`/`calamity` entry both
     contribute zero fame (Option B's own negative-space guarantee) — guards against silent
     event-type-set widening.
   - Where: `tests/unit/domains/fame/test_fame_deriver.py`

3. **`test_fame_deriver_empty_hierarchy_returns_empty_dict`** and
   **`test_fame_deriver_normalises_like_culture_deriver`** (denominator/clamp parity check against
   `CultureDeriver.NORMALISE_DENOMINATOR`)
   - Category: unit
   - Verifies: baseline empty-input behavior (mirrors `test_deriver_empty_hierarchy_returns_zero_culture`)
     and that the ticket's "verbatim" normalization mandate is actually satisfied (same denominator,
     same `min(1.0, raw/denominator)` clamp shape).
   - Where: `tests/unit/domains/fame/test_fame_deriver.py`

4. **`test_fame_exporter_populates_entity_fame`** and
   **`test_fame_exporter_preserves_untouched_entity_across_zero_event_episode`**
   - Category: unit
   - Verifies AC2: `FameExporter.export()` is called at the same episode-boundary call site as
     `CultureDriftExporter.export()` (asserted via a direct exporter-level test first, then the
     integration wiring test below), and an untouched entity's `FameCarryForward` from a prior
     episode survives unchanged into a later episode that produces zero new events for them
     (mirrors `test_exporter_overwrites_on_later_episode`'s inverse case —
     `test_culture_exporter.py` covers the "overwrites when new events exist" side; this ticket
     needs the "persists when no new events exist" side explicitly, matching the AC's literal
     wording).
   - Where: `tests/unit/domains/fame/test_fame_exporter.py` (mirrors
     `tests/unit/domains/culture/test_culture_exporter.py`)

5. **`test_fame_wiring_advance_state_calls_fame_exporter_alongside_culture_and_fidelity`**
   - Category: integration
   - Verifies AC2's call-site claim directly: calling `CampaignOrchestrator._advance_state()` once
     populates `region_cultures`, `historical_drift`, and `entity_fame` all from one call (mirroring
     `tests/unit/domains/campaigns/test_fidelity_wiring.py`'s exact pattern, extended to check all
     three fields).
   - Where: `tests/unit/domains/campaigns/test_fame_wiring.py`

6. **`test_legend_fact_constructed_only_above_threshold`** and
   **`test_legend_fact_not_constructed_below_threshold`**
   - Category: unit
   - Verifies AC3: a fame value at/above the Plan-phase-decided `fame_threshold` constant produces
     a `LegendFact`; a value strictly below it produces none (`None` or empty, per whatever
     construction API Plan decides — e.g. a `LegendFactService`/module-level function reading
     `FameImporter.get_fame(...)`).
   - Where: wherever `LegendFact` itself lives (e.g. `tests/unit/domains/fame/test_legend_fact.py`)

7. **`test_legend_fact_discoverable_via_perception_filter_service`**
   - Category: unit (calls the real `PerceptionFilterService.filter()` directly — no
     `PerceptionUpdatePhase` involvement)
   - Verifies AC4: given an `EntityState` and a `WorldSignal` constructed to represent a
     `LegendFact` (kind + salience derived from the fact/fame value per whatever conversion Plan
     decides — see investigation.md's Risks section), `PerceptionFilterService.filter()` returns
     it inside the correct typed container of the resulting `PerceptionUpdate` (either
     `perceived_opportunities` via the existing catch-all branch, or a new typed container if Plan
     adds an explicit `kind` branch) with `salience > 0.0`.
   - Where: `tests/unit/domains/perception/test_legend_fact_discoverability.py` (new file, kept
     separate from the existing `test_phase12_perception_filter_service.py` suite so a source-text
     guard can confirm `PerceptionUpdatePhase`'s own call-site count is untouched — see guard #4
     below)

8. **`test_legend_fact_distinct_from_legendary_arrival`** (source-text guard)
   - Category: architecture guard
   - Verifies AC5: `LegendFact` and `LegendaryArrivalEvent`/`LEGENDARY_ARRIVAL` remain two
     separately-named, separately-defined classes/constants — e.g. an AST or regex scan confirming
     no `class LegendFact` inherits from or references `LegendaryArrivalEvent`/`LEGENDARY_ARRIVAL`,
     and that `FameDeriver`'s own event-type frozensets never include the literal string
     `"LEGENDARY_ARRIVAL"`.
   - Where: `tests/architecture/test_fame_legend_fact_distinctness.py` (new, mirroring
     `tests/architecture/test_fidelity_write_paths.py`'s `_BELIEF_OR_KNOWLEDGE_PATTERN` source-scan
     technique)

## Scoped Pytest Commands

Primary scoped regression run for this ticket's own new/changed code, following the same
"structural backstop" convention the sibling Fidelity ticket used (bare directory, not
cherry-picked files, for any change under `src/domains/`):

```
pytest tests/unit/domains/ tests/unit/domains/culture/ tests/unit/domains/chronicle/ \
       tests/unit/domains/perception/ tests/unit/domains/campaigns/ tests/unit/domains/fame/ \
       tests/unit/domains/motivation/ tests/unit/strategic/test_coming_of_age_archetype_choice.py \
       tests/unit/social/ tests/integration/culture/ tests/integration/campaigns/ \
       tests/architecture/ -q
```

Narrower fast-loop command while iterating on `FameDeriver`/`FameExporter`/`LegendFact` alone:

```
pytest tests/unit/domains/fame/ tests/unit/domains/culture/test_culture_deriver.py \
       tests/unit/domains/chronicle/test_fidelity_deriver.py \
       tests/unit/domains/campaigns/test_fame_wiring.py \
       tests/unit/domains/perception/test_legend_fact_discoverability.py \
       tests/architecture/test_fame_legend_fact_distinctness.py -q
```

Never: `pytest tests/` (full suite) — scope stays to the domains this ticket actually touches.

## Anti-Drift Test Guards

- **`test_fame_module_no_perception_update_phase_call_site_increase`** — a source-text/AST guard
  (mirroring `test_fidelity_deriver_and_model_no_engine_or_core_state_imports`'s technique) scanning
  `src/domains/perception/phase.py` and `AuthoritativeApplyPipeline.refine()`'s own source to
  confirm `PerceptionUpdatePhase(` still has zero live pipeline call sites after this ticket lands —
  directly enforces AC4's own "without any change to `PerceptionUpdatePhase`'s own call-site count
  (still zero in the live pipeline)" clause.
- **Implemented as a second assertion inside `test_fame_module_no_perception_update_phase_call_site_increase`**
  (not a separate `test_motivation_service_compute_bias_multiplier_no_new_call_sites` function as
  originally named here) — confirming `compute_bias_multiplier(` still has zero call sites outside
  `src/domains/motivation/service.py` itself, enforcing the Out-of-Scope item against opportunistic
  wiring. Folded into the same test as the companion `PerceptionUpdatePhase` guard since both check
  the identical "stayed dormant" property; verified independently at Test phase that the assertion is
  real and passing, not just present in name.
- **`test_coming_of_age_candidate_roles_unchanged`** — a guard asserting
  `src/ai/coming_of_age.py::_CANDIDATE_ROLES` is still exactly `(SHOPKEEPER, WORKER, GUARD)` (3
  elements, no `HERO`/`ADVENTURER`), enforcing the Out-of-Scope item against silently extending it.
- **`test_entity_fame_written_only_through_fame_exporter`** — direct structural mirror of
  `tests/architecture/test_fidelity_write_paths.py::test_historical_drift_written_only_through_fidelity_exporter`:
  a repo-wide regex scan for `entity_fame[` index-assignment, allowlisting only the new
  `FameExporter`'s own module. This is the exact class of guard that caught a real,
  previously-undisclosed second write path in the idea-60 ticket
  (`CampaignOrchestrator._build_initial_state()`) — must actually be run against the real
  implementation, not just written and trusted.
- **`test_fame_module_no_belief_entry_knowledge_fact_or_legendary_arrival_references`** — combines
  the sibling Fidelity ticket's `BeliefEntry`/`KnowledgeFact` exclusion guard with a
  `LEGENDARY_ARRIVAL`/`LegendaryArrivalEvent` exclusion guard, scoped to
  `src/domains/fame/{model,deriver,exporter}.py` and wherever `LegendFact` itself is defined.
- **`test_fame_deriver_and_model_no_engine_or_core_state_imports`** — same AST-based
  no-`src.engine`/no-`src.core.state`-import guard the Culture/Fidelity Deriver+Model modules
  already carry, applied to the new `src/domains/fame/` package.
- **`test_fame_deriver_is_deterministic_byte_identical`** — calling `FameDeriver.derive()` twice
  with the same `ChronicleHierarchy` input produces byte-identical output (same technique as
  `test_fidelity_derive_is_deterministic_byte_identical`), guarding against any accidental
  non-determinism (e.g. dict iteration order, unseeded randomness) creeping into the new deriver.
