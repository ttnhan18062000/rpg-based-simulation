# Cross-Domain Management View

Generated from `registries/rule_mechanism_edges.yaml` + `registries/rule_classifications.yaml` + `registries/mechanisms.yaml` -- regenerate with `make cross-domain-management-view`. Do not hand-edit.

**The first real cross-domain view proving the Rule<->Mechanism model generalizes past Territory/Control's own idiosyncrasies (architecture.md §8, roadmap.md M4).** Each axis is reported independently, never averaged into one score. `UNKNOWN` is a legitimate, complete answer where no suitable evidence exists -- it renders explicitly rather than as a blank cell.

**Mapped / unmapped (combined)**: 14/16 real Rules mapped across both domains (2 unmapped).

**Verified / unverified (combined)**: 10/16 Rules have at least one mapped mechanism confirmed by a runtime instrument (6 unverified).

**Classification breakdown (combined)**: SUPPORTED: 0, PARTIAL: 12, CONFLICTING: 2, MISSING: 0, INERT-OFF: 0, UNKNOWN: 2.

## Territory / Control (TERR-01, TERR-02, TERR-03, TERR-05)

**Mapped / unmapped**: 4/4 real Rules mapped (0 unmapped).

**Verified / unverified**: 0/4 Rules have at least one mapped mechanism confirmed by a runtime instrument (4 unverified) -- distinct from the classification breakdown below, never collapsed into it.

**Classification breakdown**: SUPPORTED: 0, PARTIAL: 2, CONFLICTING: 2, MISSING: 0, INERT-OFF: 0, UNKNOWN: 0.

| Rule | DESIGN | REALIZATION | IMPLEMENTATION | VERIFICATION | INTEGRATION | OBSERVED OUTCOME |
|---|---|---|---|---|---|---|
| `TERR-01` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | CONFLICTING | `betrayal_siege_war` (CONSTRAINED_BY), `regional_sovereignty` (PARTIALLY_REALIZES) | 2/2 code_trace, 0/2 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `TERR-02` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | PARTIAL | `regional_sovereignty` (PARTIALLY_REALIZES) | 1/1 code_trace, 0/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `TERR-03` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | CONFLICTING | `betrayal_siege_war` (CONSTRAINED_BY), `regional_sovereignty` (PARTIALLY_REALIZES) | 2/2 code_trace, 0/2 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `TERR-05` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | PARTIAL | `city` (PARTIALLY_REALIZES) | 1/1 code_trace, 0/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |

## Combat / Conflict (CONFLICT-01, PERC-01, KNOW-01, AGENCY-01, AGENCY-02, AGENCY-04, LIFE-01, LIFE-02, BODY-07, OWN-02, CAP-01, ECOL-04)

**Mapped / unmapped**: 10/12 real Rules mapped (2 unmapped).

**Verified / unverified**: 10/12 Rules have at least one mapped mechanism confirmed by a runtime instrument (2 unverified) -- distinct from the classification breakdown below, never collapsed into it.

**Classification breakdown**: SUPPORTED: 0, PARTIAL: 10, CONFLICTING: 0, MISSING: 0, INERT-OFF: 0, UNKNOWN: 2.

| Rule | DESIGN | REALIZATION | IMPLEMENTATION | VERIFICATION | INTEGRATION | OBSERVED OUTCOME |
|---|---|---|---|---|---|---|
| `CONFLICT-01` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | UNKNOWN | none | 0/0 (n/a) | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `PERC-01` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `tactical_decision` (PARTIALLY_REALIZES) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `KNOW-01` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `tactical_decision` (PARTIALLY_REALIZES) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `AGENCY-01` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `tactical_decision` (PARTIALLY_REALIZES) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `AGENCY-02` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_engagement` (PARTIALLY_REALIZES) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `AGENCY-04` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_resolution` (PARTIALLY_REALIZES) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `LIFE-01` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_resolution` (PARTIALLY_REALIZES), `movement` (PARTIALLY_REALIZES) | 1/2 code_trace, 1/2 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `LIFE-02` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_resolution` (PARTIALLY_REALIZES), `movement` (PARTIALLY_REALIZES) | 1/2 code_trace, 1/2 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `BODY-07` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_resolution` (CONSTRAINED_BY) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `OWN-02` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_resolution` (CONSTRAINED_BY) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `CAP-01` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | PARTIAL | `combat_resolution` (PARTIALLY_REALIZES) | 0/1 code_trace, 1/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `ECOL-04` | `docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter `status: authoritative`, `last_verified: "2026-09-23"`; header "**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same day" | UNKNOWN | none | 0/0 (n/a) | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |

## Comparison

Territory is `0/4` verified (every mapped mechanism is `code_trace`-only) with a classification
breakdown of 2 `CONFLICTING`, 2 `PARTIAL`. Combat is `10/10` verified **at the Rule level** (every
mapped Rule has at least one runtime-verified mechanism among its own mapped set) with a
classification breakdown of 10 `PARTIAL`, 2 `UNKNOWN` -- but this is not uniform at the
*mechanism* level: `combat_resolution` (`scenario`), `tactical_decision` (`corpus_run`), and
`combat_engagement` (`scenario`) all carry a runtime instrument, while `movement` -- cited
alongside `combat_resolution` on both `LIFE-01` and `LIFE-02` -- is `code_trace`-only. Every one
of Combat's mapped Rules still clears the Rule-level bar only because `movement` is never a Rule's
*sole* mapped mechanism.

**The inconvenient part, stated plainly**: Combat's much higher Rule-level verified-count is not
evidence Combat is "more done" than Territory. `tactical_decision` -- the mechanism most of
Combat's mapped Rules cite -- is verified by a real corpus run, and that same run is exactly what
proved its `ATTACK`-intent branch essentially never fires in real play
(`verified.verdict: contradicted`). A high verified-count and a real problem coexist on the same
mechanism. This is the same lesson architecture.md §2 already states from the `combat_judgement`
precedent ("implemented" and "actually works" are different claims) showing up again one axis
over: "has runtime evidence" and "the evidence is good news" are also different claims, and this
view's own raw-counts discipline (never a percentage alone) is what makes that visible instead of
hidden behind a single "10/10 verified" headline.

Neither domain came out "cleaner" than the other by design -- Territory's `CONFLICTING` rows are a
real semantic violation (an overloaded field slot); Combat's `PARTIAL` rows are a real,
correctly-built-but-under-exercised mechanism. Both are real findings, differently shaped, and this
view represents each faithfully rather than collapsing them into one comparable score.
