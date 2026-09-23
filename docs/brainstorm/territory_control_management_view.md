# Territory Control Management View

Generated from `registries/rule_mechanism_edges.yaml` + `registries/rule_classifications.yaml` + `registries/mechanisms.yaml` -- regenerate with `make territory-control-view`. Do not hand-edit.

**Territory/Control Rules (TERR-01, TERR-02, TERR-03, TERR-05) rendered across architecture.md §8's six management-view axes.** Each axis is reported independently, never averaged into one score. `UNKNOWN` is a legitimate, complete answer where no suitable evidence exists -- it renders explicitly rather than as a blank cell.

**Mapped / unmapped**: 4/4 real TERR Rules mapped (0 unmapped). TERR-04 is excluded -- it is a stale citation, not a real Rule ID (see the ticket's own Findings).

**Verified / unverified**: 0/4 Rules have at least one mapped mechanism confirmed by a runtime instrument (4 unverified) -- distinct from the classification breakdown below, never collapsed into it.

**Classification breakdown**: SUPPORTED: 0, PARTIAL: 2, CONFLICTING: 2, MISSING: 0, INERT-OFF: 0, UNKNOWN: 0.

| Rule | DESIGN | REALIZATION | IMPLEMENTATION | VERIFICATION | INTEGRATION | OBSERVED OUTCOME |
|---|---|---|---|---|---|---|
| `TERR-01` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | CONFLICTING | `betrayal_siege_war` (CONSTRAINED_BY), `regional_sovereignty` (PARTIALLY_REALIZES) | 2/2 code_trace, 0/2 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `TERR-02` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | PARTIAL | `regional_sovereignty` (PARTIALLY_REALIZES) | 1/1 code_trace, 0/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `TERR-03` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | CONFLICTING | `betrayal_siege_war` (CONSTRAINED_BY), `regional_sovereignty` (PARTIALLY_REALIZES) | 2/2 code_trace, 0/2 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
| `TERR-05` | `docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; header "**Status.** Batch 11A (Places/Settlements/Territory), first draft" | PARTIAL | `city` (PARTIALLY_REALIZES) | 1/1 code_trace, 0/1 runtime | UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped mechanisms; see the schema-friction note in that file's own header | UNKNOWN -- no runtime evidence currently exists |
