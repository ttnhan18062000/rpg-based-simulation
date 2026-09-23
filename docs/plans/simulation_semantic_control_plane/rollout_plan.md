---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Rollout Plan — Simulation Semantic Control Plane

Part of [the epic](README.md). Staged, evidence-gated rollout — mirrors how the Mechanism
Registry's own `system` tier was gated (feasibility investigation, then a separate value-vs-cost
investigation, before any schema landed) at the scale this is actually built at, not the scale a
full 172×93 mapping would otherwise imply.

---

## Stage A — minimal structured model, no final ontology

Add only the minimum structured data required to represent:

```
Rule ↔ Mechanism participation (typed edge, architecture.md §3)
realization classification (reused vocabulary, architecture.md §4)
evidence reference
UNKNOWN as an explicit, storable state
domain-level aggregation
```

Do not design the final schema up front. `architecture.md` §3 deliberately leaves the exact file
format undecided — Stage B (below) is where real data pressure-tests the shape before it is
locked in and validated the way `registries/mechanisms.yaml` is.

## Stage B — first operational slice: Territory / Control

**Chosen domain:** `docs/world_rules/places-culture/territory-control.md` (`TERR-01`–`TERR-0N`).
Reasons this is the right first slice, not an arbitrary pick:

- It already has the richest, most concrete real-code finding in the whole frozen Catalog —
  `owner_faction_id` read as three different concepts by three different consumers, already
  investigated and cited directly (`TownResolutionSystem`'s tax pass, `region.suppression_active`,
  and `PlaceState`'s own "Sovereignty override" field comment).
- Its own review export already has a non-binding Implementation Candidates entry
  (`TerritorialRelation`-shaped typed record) — a real head start to validate the mapping schema
  against, not a cold start.
- It touches multiple systems (`world`, `faction`) and layers (`region`, `faction`), so it
  exercises the many-to-many shape immediately rather than deferring that test to a later slice.

**Purpose of this slice**: establish the first real data shape, find schema friction, exercise the
actual implement/debug/impact workflow end-to-end, produce the first domain management view.

**Explicitly not the purpose of this slice**: proving whether the whole Control Plane deserves to
exist. Do not treat Stage B as an ROI gate the way the Mechanism Registry's own `system`-tier value
investigation was — this plane's incremental-enrichment model (Stage D) is the actual cost control,
not a single pass/fail investigation up front.

**Concretely, in Stage B:**
1. Map each `TERR-0N` Rule to its real mechanisms (a first candidate set: `regional_sovereignty`,
   `regional_trauma`, `city`/`RegionState`-adjacent mechanisms — verify against the actual registry
   at execution time, do not assume this list is still current).
2. Record typed edges (`REALIZES`/`PARTIALLY_REALIZES`/`CONSTRAINED_BY`) with the same evidentiary
   discipline the Mechanism Registry already requires — a citation, not a guess.
3. Generate the first domain management view (`architecture.md` §8's six axes) for Territory only.
4. Record every schema friction point found — this becomes the input to finalizing Stage A's
   deferred schema decisions, not a reason to redesign mid-slice.

## Stage C — drift detection begins here, scoped to what Stage B just created

**Resolves an item this epic's own review left open: drift detection needs a stage, not just a
"mandatory, someday" label.** It starts here, at Stage C, immediately after Stage B produces the
first real mappings — not deferred to a later, unscheduled point, and not built before there is
anything to check drift against.

Minimum detector, report-only, mirroring `mechanism_registry_changed_code_check.py`'s own
philosophy exactly (`mechanism_claims_as_tests_initiative.md` §4.1, "a detector that fires on
legitimate code teaches people to ignore it — report-only first"):

```
implementation cited by a mapped mechanism changed since the mapping was last reviewed
a mapped mechanism was renamed/removed/split/merged
a mapped Rule was renamed/removed
a mapped mechanism's verified.verdict changed since the mapping was last reviewed
```

The detector surfaces "mapping review required" — it does not attempt to determine new semantic
truth on its own, the same restraint the Mechanism Registry's own changed-code check already
applies.

## Stage C (continued) — ingest existing known findings, without laundering prose into fact

Reuse the Rule Catalog's own review-export "Implementation Candidates" sections where they name a
real, checkable finding (Territory's own `owner_faction_id` finding is the clearest example
already on file). **Old prose classification does not automatically become current structured
truth** — re-verify against the actual current registry/code state before recording a mapping
entry, the same discipline `mechanism_identity_and_change_taxonomy.md` §4 already applied when
re-checking earlier "split everything" claims and finding some of them unevidenced.

## Stage D — incremental expansion through real work (the actual cost model)

When a ticket touches a domain or mechanism already covered by a Rule, resolve or validate its
mapping as part of that ticket's own normal work — not as a separate mapping-completion project.
This is what keeps the cost bounded: 172×93 is never attempted as a standalone effort; the mapping
grows exactly as fast as the domains it covers actually get worked on, the same incremental model
the Mechanism Registry's own `implemented_by` coverage already uses (76 of 93 populated
organically, never backfilled in one pass).

A targeted broader sweep may run later if a specific domain needs it faster than organic coverage
would provide — that is a scoped decision made at the time, not a standing commitment made here.

## Stage E — management baseline across domains

Once more than one domain has real mapping coverage, generate the cross-domain view
(`architecture.md` §8's six axes, one row per major domain), always showing `mapped`/`unmapped`
and `verified`/`unverified` counts alongside any classification breakdown — never a percentage
computed from a pre-filtered known subset alone (the exact discipline
`TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY` already had to retrofit onto the
Mechanism Registry's own rollup after a misleading confirmation rate went unchallenged for one
review cycle).

## Stage F — Context Compiler, only after real query patterns exist

Do not build this now. Collect real query patterns first, through Stages B–E's own normal use.
When it is eventually built, it **wraps/orchestrates existing retrieval tools** — `graphify` for
structural/code queries, this plane's own registries for semantic/realization queries — it does
not replace either, and its own temporary unavailability (as `graphify-out/` regularly is,
per `docs/CLAUDE.md`'s own note that it's deliberately untracked and rebuilt locally) must never
invalidate the rest of this architecture. Building this before Stage B–E produce real usage data
risks the same fate as a second search engine nobody asked for.

## Explicit non-goals, restated from architecture.md for this plan specifically

- Do not stop normal RPG-core engineering work until the mapping is "complete" — there is no
  planned completion point; Stage D is permanent, ongoing maintenance, not a project with an end
  date.
- Do not require a formal ROI proof before Stage B starts (contrast with the Mechanism Registry's
  own `system`-tier value investigation, which *was* an appropriate gate at that smaller scale —
  at 172×93 scale, an all-or-nothing ROI question is the wrong question; the right one is "does
  Stage B find real schema friction," which Stage B itself answers by executing).
- Do not let Stage C's drift detector attempt to resolve disagreements automatically — report-only,
  same as its Mechanism Registry precedent.

## Related

- [architecture.md](architecture.md) — the model this rollout builds incrementally.
- [agent_operating_model.md](agent_operating_model.md) — the workflow Stage D's "normal ticket
  work" already assumes.
- `docs/world_rules/places-culture/territory-control.md` and
  `docs/world_rules/review-exports/places-territory-batch-11a-review.md` — Stage B's actual
  starting material.
- `tmp/semantic-control-plane-review.md` — the review this rollout plan's own Stage C directly
  answers (the "drift detection has no assigned stage" item).
