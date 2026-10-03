---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS
artifact_type: report
tags: [simulation-quality, progression, architecture]
---

# Registry edits — `derived_stats` binding + completeness pin

**All three edits below were applied and are on `main`** (PR #279): Edit 1 at
`registries/mechanisms.yaml:475-476`, Edit 2 in the same entry's `verified.note`, Edit 3 at
`tests/unit/tools/test_mechanism_registry_completeness_check.py:191-192` (`scope_files` 296,
`unbound_files` 233 — the binding took effect, so 234 never occurred). This file is retained as the
decision record for *why* option A was chosen; it is not a pending work item. It reached
`stored_artifacts/` one batch late because it was left off #279 to avoid a second CI cycle.

Written by `rpg-feature-planning`, which owns `registries/mechanisms.yaml` **content** (the
advisory/pipeline tooling is agent-working's — split recorded at
`tickets/done/TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE.md:31-33`).
`rpg-implementer` commits these; one writer per branch.

**Decision: option A — bind `src/core/derived_stats.py` to the existing `derived_stats` mechanism.**

**Why this is a truthful binding and not a way to quiet the gate.** `src/core/derived_stats.py`
holds `attribute_stat_terms()`, which *is* the attribute-contribution half of Bible 01 §2
(`vitality*2 + int(endurance*0.5)`, `int(strength*0.5)`, `int(vitality*0.3)`, `agility*0.001`) — the
same arithmetic that previously lived inline inside `recalculate_combat_stats`, now extracted so the
derivation and the spawn-time residual cannot drift. It is squarely inside the pipeline this
mechanism already describes, so the binding states a fact. Option B (bump the pins and leave the
file unbound) would have recorded a falsehood-by-omission — that the single definition of §2's
attribute terms belongs to no mechanism — and option C (relocating the helper to dodge a count) was
correctly rejected as worse design.

Granular, function-level binding follows this entry's own established precedent: it already explains
that `readiness_speed_scaling` keeps a separate, more specific citation rather than being merged in.

---

## Edit 1 — `registries/mechanisms.yaml`, `derived_stats` entry: extend `implemented_by`

The anchor is unique (one `- id: derived_stats` in the file; verify before replacing).

**FIND:**

```yaml
    implemented_by:
      - src/engine/rpg_depth.py::SkillScalingService::get_effective_stats
    verified:
      instrument: scenario
      verdict: observed
      date: "2026-09-20"
```

**REPLACE WITH:**

```yaml
    implemented_by:
      - src/engine/rpg_depth.py::SkillScalingService::get_effective_stats
      - src/core/derived_stats.py::attribute_stat_terms
      - src/core/derived_stats.py::residual_base_terms
    verified:
      instrument: scenario
      verdict: observed
      date: "2026-09-20"
```

Leave `state: done`, `layer`, `systems`, `depends_on`, `instrument`, `verdict` and `date`
**unchanged**. The 2026-09-21 value-differential evidence still holds — a +10 vitality delta still
moves `max_hp` by exactly +20 and a +10 strength delta `atk` by exactly +5 — so the verdict is not
being re-litigated and its date is not being bumped.

## Edit 2 — append to the same entry's `verified.note`

Append verbatim at the end of the existing `note:` block, preserving its indentation:

```
        **Durable base + grant accumulator added 2026-10-02**
        (TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS, PR #279): the derivation no
        longer falls back to generic defaults (`base_hp=100, base_atk=10, base_def=5,
        base_evasion=0.05`) that silently erased an entity's species values -- a `goblin_scout`
        spawned at `max_hp=35` recalculated to `112`. It now reads typed durable per-entity
        `base_*` fields on `CombatComponent` plus a `permanent_max_hp_bonus` accumulator.
        `src/core/derived_stats.py` is bound above because it is the single definition of §2's
        attribute-contribution terms, called by both the derivation and the spawn-time residual so
        the two cannot drift; the companion test asserts that round trip exactly for every entity
        in three corpus worlds. The stored base is a **residual**
        (`profile_value - attribute_stat_terms(attributes)`), deliberately unclamped, because stat
        profiles declare FINAL spawned values while the derivation treats its base as a term
        attributes are added to -- passing the profile value through directly would have inflated
        that same `goblin_scout` to `47`.
        Three qualifications a reader of this entry needs:
        (1) **This is a declared interim, not full single-writer compliance.** It resolves the
        conflicting-value defect (35 vs 112), not the dual-path structure. `world-rule-catalog-design`
        accepted an OWN-03 materialised-view reading on condition it be recorded as interim and
        graded **OWN-01 PARTIAL**; full consolidation is owned by
        TCK-20261001-SPAWN-AND-DERIVATION-HOLD-INCOMPATIBLE-DERIVED-STAT-MODELS.
        (2) **The equivalence that justifies it is conditional**: it holds only because the
        accumulator enters the derivation as a linear additive term. If near-death hardening ever
        becomes percentage-based, capped or attribute-dependent, that argument breaks and
        single-writer authority must be revisited.
        (3) **The derivation is still unreached in ordinary corpus play.** The `stats_dirty` trigger
        set was deliberately left unchanged, and that dormancy turned out to be *load-bearing*:
        activating the derivation today would shift `move_cost` on every entity and strip the
        declared range from five ranged archetypes. Do not read this entry as evidence the
        derivation now runs.
```

## Edit 3 — `tests/unit/tools/test_mechanism_registry_completeness_check.py`: pin only `scope_files`

**Authorised expected-value update**, as the registry program's ratchet owner: `scope_files`
**295 -> 296**.

- `unbound_files` **stays 233** — Edit 1 binds the new file, so it never enters the unbound set.
  If the measured value is 234 after applying Edit 1, **stop**: the binding did not take effect and
  that is a real problem, not a pin to bump.
- `candidates 74 / wired 21 / exclusions 18 / pending 3` all **unchanged**.

This is a legitimate expected-value update rather than editing a gate to pass, because the gate's
actual purpose has been served: its docstring asks for a human decision — "bind it, exclude it with
a reason, or register a new mechanism" — and Edit 1 is that decision, recorded in the registry. The
count moves because a real new file exists. **Do not touch the test's logic, its docstring, or any
other pin.**

## Verification before commit

1. `python3 -c "import yaml; yaml.safe_load(open('registries/mechanisms.yaml'))"` parses.
2. Whatever registry validator exists for `implemented_by` targets passes — both new citations must
   resolve to real symbols in `src/core/derived_stats.py`.
3. `tests/unit/tools/test_mechanism_registry_completeness_check.py` passes, with `unbound_files`
   measuring **233**, not 234.
4. The rest of the `Unit · infra / observability` job still passes (277 before this change).
