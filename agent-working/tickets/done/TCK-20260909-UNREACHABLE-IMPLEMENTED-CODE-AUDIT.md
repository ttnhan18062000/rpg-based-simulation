---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT
phase: done
date: 2026-09-09
tags: [architecture, audit]
---

# TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT

## Title
Audit src/ for implemented, tested, but never-called code — grew from 7-8 known instances to 362 real candidates (~8% of src/); reframed as mechanism-vs-surface, not zero-anywhere-vs-test-only; the biggest finding is that this codebase accumulates SUPERSEDED implementations alongside their live replacements, not just unwired features

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Over a single session of follow-up work (PR #148 / PR #150 batches), **seven separate instances**
of real, frequently unit-tested production code with **zero live callers** were found — every one
of them incidentally, while investigating something else:

| Mechanism | Location | How it surfaced |
|---|---|---|
| `BeliefCycleSystem.decay_stale_beliefs()` | `src/systems/strategic_systems/belief.py:42` | Diagnosing `combat_risk` belief staleness |
| `BiologicalSystem.update()` | `src/systems/biological_system.py` | Dirty-set consumer investigation |
| `spawn_calamity()` | `src/world/calamity.py` | `state.maturity` consumer survey |
| `CatalogScenarioStateBuilder` chain | `src/scenarios/catalog_state_builder.py` | Campaign zero-entity investigation |
| `invalidate_read_model` | `src/engine/apply_plan.py:20` | Dirty-set consumer investigation |
| Camp raid-reuse discard stub | `src/world/camp.py` | Camp content-authoring follow-up |
| `effective_certainty()` | `src/cognition/knowledge_model.py:137` | Parity-ledger check on STRAT-239 |
| `EntitySpawnContext.spawn_region` → `properties["spawn_region"]` write | `src/entities/archetype_factory.py:24,66-67` | Investigating `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s spawn-position approach |

**Eighth instance (2026-09-11), found while designing the fix for
`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`:** `EntitySpawnContext` carries a
`spawn_region: Optional[str] = None` field; when non-`None`, `ArchetypeEntityFactory.build_entity()`
writes it into the built entity's `properties["spawn_region"]`. But the only real caller,
`WorldEntitySpawner.spawn_from_context()` (`entity_spawner.py:57`), hardcodes
`spawn_region=None` on every construction — so the write path never fires in practice — and a
repo-wide grep for any reader of `properties["spawn_region"]` / `properties.get("spawn_region")`
found zero consumers. Genuinely dead on both ends (never written with a real value, and nothing
reads it even if it were). Checked specifically because it looked like it might be the intended
hook for that ticket's own per-entity spatial-placement fix — it is not: it stores a region-name
*string tag* on entity metadata, not spatial coordinates, so it wouldn't have served that purpose
even if wired. That ticket is adding a new, separate `spawn_position` field rather than reusing
this one — recorded here rather than silently fixed, per this audit ticket's own Out of Scope
("Fixing, wiring, or deleting any of the found code... each disposition is its own ticket").

The problem is not any individual entry — most have now been filed for disposition individually.
The problem is the **pattern and the detection gap**: this codebase has a systematic divergence
between "implemented and tested" and "actually reachable at runtime," and nothing surfaces it.
Discovery has been entirely accidental, at a rate of roughly one per investigation.

Two aggravating findings show existing quality mechanisms actively certify the gap rather than
catch it:

1. **A unit test asserted the defect as intended behavior.** `tests/unit/domains/campaigns/
   test_campaign_orchestrator.py` asserted `state.entities == {}` as an intentional invariant —
   codifying the Campaign-mode zero-entity bug as expected. It passed continuously and helped the
   bug survive a full ticket dedicated to Campaign-mode correctness.
2. **A P1 parity-ledger entry is marked `verified` for a mechanism that has never executed.**
   `STRAT-239` (`docs/parity_ledger/strategic_cognition.yaml:2873`) describes lead-staleness
   demotion (APPROXIMATE→VAGUE→EXHAUSTED). Its `v2_evidence` cites
   `belief.py:47 — stale_threshold: int = 50 (default)` — which verifies that *a default parameter
   exists*, not that the behavior occurs. The method has zero callers.

So both the test suite and the parity ledger have certified unreachable behavior as working.

## Scope
- Enumerate implemented-but-unreferenced code across `src/`: modules, classes, and functions with
  no live call site outside their own definition and their own tests.
- Account for legitimate false positives explicitly rather than filtering them silently — entry
  points, dynamic dispatch, registry/plugin lookup by string name, framework-invoked hooks,
  re-exported public API. The output must distinguish "genuinely unreachable" from "reachable by a
  mechanism static analysis cannot see," with the reasoning recorded per entry.
- Triage each genuine finding into exactly one of: **wire** (real intent, never connected),
  **delete** (abandoned), or **document** (deliberately dormant, with the rationale recorded).
- Produce the result as a durable artifact under `docs/audits/`, not only as ticket-body text, so
  it can be re-run and diffed later.
- File follow-up tickets for the individual dispositions rather than executing them here.

## Out of Scope
- Fixing, wiring, or deleting any of the found code. This ticket produces the list and the triage;
  each disposition is its own ticket.
- Building a CI check for unreferenced code. That was considered and deliberately deferred: the
  false-positive rate is unknown until this audit produces real numbers. Revisit with that data.
- The seven already-known instances' own dispositions — each already has, or will have, its own
  ticket (`BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`, `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`,
  `SPAWN-CALAMITY-DEAD-CODE-DISPOSITION`, `CAMP-RAID-ORIGIN-SPAWN-FIX` (done),
  `CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (done), and the `effective_certainty()` disposition).
  Include them in the audit's inventory for completeness, but do not re-litigate them.
- A full parity-ledger re-verification. See Assumptions below — it is a real adjacent question,
  but it is its own ticket if the audit's findings justify one.

## Acceptance Criteria
- [x] A complete inventory of implemented-but-unreferenced code in `src/` exists as a durable
      artifact under `docs/audits/`, with each entry triaged wire / delete / document and the
      reasoning recorded. — `docs/audits/unreachable_code_inventory.md` (narrative, deep cluster
      writeups) + `docs/audits/unreachable_code_inventory.{json,csv}` (full structured 428-row
      data). Per peer review: triage is by cluster/root-cause where a cluster was individually
      verified (4 deep writeups), not per-instance across all 362 real candidates — individually
      triaging 362 instances was confirmed not tractable, and not what "watch for shared roots"
      meant.
- [x] False positives are enumerated with the mechanism that makes each reachable, not silently
      excluded — a reader must be able to check the exclusion reasoning. — 66 excluded (42 FastAPI
      route/websocket decorators, 24 Pydantic validators), each with its own excluding decorator
      recorded in the structured data, not just a count.
- [x] The seven known instances all appear in the inventory, cross-referenced to their own
      disposition tickets. — Re-discovered by the tool directly: `spawn_calamity` (zero-anywhere)
      and `effective_certainty` (test-only, only visible after fixing the test-only methodology
      bug — see Implementation Notes). `BiologicalSystem.update()` is NOT re-discoverable by this
      tool (confirmed: generic method name collision, documented as the tool's own known
      limitation) — its own disposition ticket already had it from prior investigation.
- [x] Follow-up tickets are filed for any newly-found genuine instances; none are fixed here. — 3
      new tickets filed for the deep-verified clusters (see Related Tickets); no code changed by
      this audit itself.
- [x] The audit records its own method and its limitations plainly, including what class of
      unreachable code it cannot detect, so a future re-run knows what it is and isn't covering. —
      `docs/audits/unreachable_code_inventory.md`'s own Limitations section, and
      `tools/audit_unreachable_code.py`'s own docstring (both methodology bugs found and fixed,
      the generic-name-collision limitation, the tools/-grouped-with-tests/ simplification).

## Related Tickets
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (done) — the instance that also exposed STRAT-239.
- `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` — sharpened with a confirmed live
  equivalent (`apply.py`'s own passive hunger/sleep-debt decay), same superseded-not-missing shape.
- `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION` — its own central open question resolved:
  `CalamityService.process_world_dynamics()` already spawns a calamity entity via `spawn_monster()`,
  confirming `spawn_calamity()` is a superseded duplicate, not a missing mechanic.
- `TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION` — flagged (not confirmed)
  that a superseded-duplicate check belongs alongside its own existing abandoned/unfinished framing.
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (done) — wired the catalog spawn chain, the
  largest instance, and the one that had left Campaign mode running with zero entities.
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done)
- `TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY` (done) — same family one level up: a
  pipeline that runs but delivers almost nothing to its consumer.
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (new — Cluster C1, the
  single largest finding of this audit)
- `TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION` (new — Cluster C2)
- `TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD` (new — Cluster C4, hotfix)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` — the same failure shape
  (two competing mechanisms for the same job) already confirmed real at smaller scale before this
  audit found it recurring at subsystem scale.

## Related Docs
- `docs/audits/` — where the output belongs; see existing D-numbered dimension audits for shape.
- `docs/parity_ledger/schema.json` — for the STRAT-239-class question in Assumptions.
- `docs/guidelines/design_patterns.md`

## Related Stored Artifacts
`docs/audits/unreachable_code_inventory.md` — the durable audit artifact itself (not a
`stored_artifacts/` staging file; this ticket's own Scope specifies `docs/audits/` as the real,
re-runnable output location).

## Related Code Areas
All of `src/`. The 4 deep-verified clusters' own locations are in the audit doc; the tool itself
is `tools/audit_unreachable_code.py`.

## Assumptions / Open Questions
- ~~The false-positive rate for static reachability analysis in this codebase is unknown. If it
  turns out high enough that the inventory is untrustworthy, say so and stop...~~ **Resolved**: the
  false-positive rate is low and mechanistically explained (66/428 = ~15%, all decorator-driven and
  automatically classified) — the audit did NOT need to stop on a credible-negative-result basis.
  The real surprise was scale (362 real candidates, not the 7-8 originally known), not
  untrustworthiness.
- **Adjacent, deliberately not scoped here:** STRAT-239's own parity-ledger question — not expanded
  into during this pass, as originally planned.
- ~~Whether any of the seven represent one shared root cause...~~ **Resolved, and the single most
  important finding of this audit**: yes, and the pattern is much broader than the original seven.
  This codebase repeatedly accumulates a **superseded** implementation alongside its live
  replacement (confirmed for `spawn_calamity()` vs. `CalamityService.process_world_dynamics()`,
  `BiologicalSystem.update()` vs. `apply.py`'s own passive decay, and the entire
  `src/domains/optimization/` package vs. `ResourceGovernor`/`GovernorPolicy`) — not just
  "a subsystem built ahead of its integration." This reframes the correct default disposition for a
  cluster of dead-but-tested code from "wire it in" to "determine whether a live equivalent exists
  first" — naively wiring a superseded implementation back in would create the exact dual-mechanism
  problem `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` already confirmed real
  at smaller scale.

## Implementation Notes
Two real methodology bugs were found and fixed while building the audit tool — both by checking the
tool's own output against known ground truth (the original 7-8 instances), not by trusting a first
draft. Full detail in `tools/audit_unreachable_code.py`'s own docstring:
1. An early version only checked "referenced outside its own file" — missed that a private helper
   called by a sibling function in the same file is alive, not dead
   (`src/ai/coming_of_age.py::_personality_weight`, caught this way). Fixed: count occurrences
   anywhere minus the definition line(s) themselves, same-file included.
2. An early version counted any occurrence in `src/`/`tests/`/`tools/` as "used" — but this
   ticket's own definition ("no live call site outside their own definition **and their own
   tests**") means test-only usage should still count as unreachable. This silently hid
   `effective_certainty()` — one of the original known instances, tested but never called from
   production — until fixed. This bug mattered more than the first: it would have shipped a
   smaller, falsely-reassuring number with full confidence.

Scale discovery and reframe, in order:
1. Initial raw scan: 428 candidates, 66 auto-excluded (FastAPI/Pydantic decorators), 362 real —
   ~40x the original 7-8. Reported this to peer review before writing the final doc or filing
   anything, since the scope had grown far beyond what the ticket's own origin anticipated.
2. Peer review's direction: organize by **mechanism vs. surface**, not the zero-anywhere/test-only
   axis (test-only is the *more* interesting category, not the lesser one — it's exactly the shape
   of `decay_stale_leads()`/`effective_certainty()`). Deliverable: committed re-runnable tool +
   structured data + deep writeups for clusters only + tickets per cluster, not per instance.
3. Verified the `src/domains/optimization/` cluster directly (a real import grep, not inferred):
   8 of 9 modules have zero production imports; `admission_control.py`'s own comments reference
   `cache_strategy.py` (one of the 8) as if describing live behavior.
4. Peer review's reframe, verified directly before acting on it: `GracefulDegradationManager`
   (`degradation.py`) and `ResourceGovernor` (`src/engine/governor.py`, confirmed live during
   Batch A) do the same job — pressure-ratio-based degradation — with different specific
   thresholds. This is a **superseded duplicate**, not a missing feature. Directly confirmed the
   same shape for `spawn_calamity()` (superseded by `CalamityService.process_world_dynamics()`'s
   own inline `spawn_monster()` call) and `BiologicalSystem.update()` (superseded by `apply.py`'s
   own live passive hunger/sleep-debt decay) — carried this finding into both of those tickets'
   own Assumptions/Open Questions, correcting their framing from "wire vs. delete" toward
   "confirmed superseded, leaning delete."
5. Filed 3 tickets on the corrected basis: C1 (optimization package) explicitly framed as a
   per-module superseded-or-missing *determination*, not "wire these in" — the ticket's own title
   and Request Summary lead with the governor/degradation pair as the worked example proving
   superseded is a live possibility, per peer review's explicit instruction not to pre-judge the
   other 6 modules just because 2 confirmed match the pattern. C2 (ObservabilityConfig) filed as a
   genuine investigate-first (mechanism-vs-surface undetermined — the underlying flags aren't read
   anywhere else either, so it's a real, undetermined 3-way branch, not a foregone conclusion). C4
   (unregister pair) filed as a small, fully-verified hotfix. C3 (CatalogRepository/V2EntityBuilder
   accessor/builder methods) deliberately NOT filed as its own ticket, per peer review — surface,
   not mechanism, and filing it at the same weight as C1 would dilute the real signal.

## Test Summary
`tools/audit_unreachable_code.py` run directly, output verified against known ground truth
(re-discovers `spawn_calamity()` and, after the test-only fix, `effective_certainty()`; correctly
does NOT re-discover `BiologicalSystem.update()`, confirmed as the tool's own documented generic-
name-collision limitation rather than a bug). `src/domains/optimization/`'s 8-of-9-dead claim and
the `admission_control.py` comment-not-import distinction independently re-verified via direct
`grep -rn "from src.domains.optimization"` and direct file reads, not trusted from the tool's own
output alone. No automated test suite applies — no production code was changed by this audit.

## Files Changed
- `tools/audit_unreachable_code.py` — new, committed, re-runnable audit tool
- `docs/audits/unreachable_code_inventory.md` — new audit doc (methodology, false-positive
  categories, 4 deep cluster writeups, limitations)
- `docs/audits/unreachable_code_inventory.json`, `.csv` — new structured inventory (428 rows)
- `tickets/todos/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION.md` — new
- `tickets/todos/TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION.md` — new
- `tickets/todos/TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD.md` — new
- `tickets/todos/TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION.md` — sharpened with a
  confirmed live equivalent
- `tickets/todos/TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION.md` — central open question
  resolved, stale file path corrected
- `tickets/todos/TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION.md` —
  flagged (not confirmed) for the same superseded-duplicate check

## Completion Summary
Grew from a 7-8-instance seed list to 362 real candidates (~8.4% of all definitions in `src/`) via
an AST-based, whole-corpus-tokenization methodology built specifically to avoid this repo's own
prior dead-code audit's confirmed 100% false-positive-rate failure (`D11_dead_code.md`'s grep-based
directory-level import counting). Found and fixed two real bugs in the audit's own tooling along
the way, both caught by checking output against known ground truth rather than trusting the tool —
the second (test-only usage silently counted as "reachable") mattered most, since it would have
hidden a known instance and shipped a smaller, falsely-reassuring number with full confidence.

The scale discovery (~40x the original count) was reported to peer review before writing the final
document or filing anything, since it changed the shape of what this audit could honestly deliver.
The resulting reframe — organize by mechanism-vs-surface, not by raw reachability status; deep
writeups for individually-verified clusters only, not per-instance triage of 362 items; a
committed, re-runnable tool as the durable asset, not a one-time snapshot — produced this audit's
own most valuable output: not "40x more dead code than we thought," but **this codebase repeatedly
accumulates superseded implementations alongside their live replacements**, confirmed directly for
3 separate clusters (`spawn_calamity`, `BiologicalSystem.update()`, and the entire
`src/domains/optimization/` package against `ResourceGovernor`/`GovernorPolicy`). This reframes the
correct default response to "dead but tested code" in this codebase from "wire it in" toward "check
for a live equivalent first" — filed accordingly, with the largest ticket (C1) explicitly scoped as
a per-module determination rather than a pre-judged fix, to avoid the same dual-mechanism-
preemption failure this arc already confirmed real at smaller scale
(`TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION`).

3 new tickets filed (C1 standard/P1, C2 standard/P2, C4 hotfix/P3); C3 deliberately left
unfiled, per peer review, to avoid diluting the signal with a low-priority surface-level finding.
The 3 original open disposition tickets were updated with this audit's own confirmed evidence
rather than left to independently rediscover it. 75 of 79 identified file-clusters and 99
singletons remain in the structured data, real by the same methodology but not individually
verified beyond it — available for a future pass via the same committed, re-runnable tool.
