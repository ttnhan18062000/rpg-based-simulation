---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER
phase: done
date: 2026-09-29
tags: [investigation, root-cause, corpus, world]
---

# TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER

## Title
Classification pass over the 4 zero-caller / dead-constant tickets (`T01` of
`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
This ticket's own priority (`P2`) sits between the priorities of the tickets it covers —
`CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` is `P3`, `REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-
DEBUFFS` is `P2`, `PROFILE-API-PAYLOAD-DEAD-API-REFS` is `P2`, and `CALAMITY-INTENSITY-PRODUCER-
NEVER-FIRES` is `P1` (but that ticket's actual disposition is `T04`'s job, not this ticket's — see
Scope). Don't read `P2` here as implying any of those four tickets' own priority changed.

`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` groups 14 open "unreachable mechanism"
tickets under one classification axis (`DEFECT` / `CONDITION` / `UNDECLARED` / `MISLABEL`) so that
tickets which read identically on their face — "this code has zero real callers" — stop being
treated as interchangeable. The wave that motivated the epic
(`TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE`, PR #258) proved the axis matters: three
superficially similar findings resolved to two different verdicts (`DEFECT` for `calamity_intensity`,
`CONDITION` for `regional_trauma` and aging/succession).

This ticket (`T01` per `tickets/todos/unreachable-mechanism-classification/SEQUENCE.md`) is the
classification pass over the epic's "zero real callers / dead constant" corpus group — the four
tickets whose shared *shape* is "real, non-dead code or a real constant with zero live invocations
or reads anywhere in `src/`," not the four tickets whose shared *cause* is assumed to be the same
(the epic explicitly disconfirmed a shared-root-cause hypothesis during the wave and this ticket
inherits that same discipline — see Assumptions).

## Scope
For each of the following three tickets, produce exactly one verdict from the epic's four-value
axis (`DEFECT` / `CONDITION` / `UNDECLARED` / `MISLABEL`), backed by evidence per the epic's
evidence bar (a named zero-caller grep, a content fact, or tick arithmetic — reading the code alone
does not count):

1. `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` (hotfix, P3) — `CalamityService.
   CALAMITY_RANDOM_CHANCE = 0.005` has zero real usages per the ticket's own exhaustive `src/` grep;
   `should_spawn` is driven entirely by a deterministic interval check. Classify whether this is a
   `DEFECT` (orphaned during a refactor, meant to gate something), a `MISLABEL` (the constant's name
   overstates intent that was never real), or another verdict — re-verify the zero-usages grep
   directly rather than trusting the ticket's own prose as evidence.
2. `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` (hotfix, P2) —
   `RegionalSovereigntyService.process_taxation()` (`src/world/regional_sovereignty.py`) has zero
   real callers per a repo-wide grep; the ticket's own Scope item 1 asks for a *direct pipeline
   trace*, not just the grep, before concluding dead — that trace has not yet been done and is part
   of this pass's evidence requirement, not something to skip.
3. `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` (hotfix, P2) — `tools/perf/
   profile_api_payload.py` imports `SimulationConfig`/`EngineManager`, neither of which exist under
   those names in the current `src/`, and has never successfully run per the ticket's own account of
   `make profile-api`'s history. This one differs in kind from the other three: it is dead *because
   of* a rename/removal elsewhere (`V2EngineManager` superseded `EngineManager`; `SimulationConfig`
   was removed in favor of `RuntimeProfile`), not because nothing ever called it — classify it on its
   own evidence, don't assume the same verdict as the `src/world/` pair just because it's grouped
   here by shape.

For `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`: **this pass does not classify it.** It
already carries a `DEFECT` verdict from the wave (`apply_calamity_consequences()` has zero real
callers anywhere in `src/`, confirmed in that ticket's own 2026-09-20 Implementation Notes and in
`stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/`). This ticket's job for it is
**citation only** — including it in this pass's classification-doc contribution as "see T04" rather
than leaving it silently absent from a "zero-caller corpus" writeup. **Recording the verdict into
the ticket's own body and the epic's classification document is `T04`'s job, per `SEQUENCE.md`'s own
explicit note on this exact overlap** ("`T04` owns its actual disposition... `T01` covers it only as
a corpus-grouping entry, not a duplicate classification pass"). Do not re-record it here.

For each of the 3 tickets actually classified by this pass, record the verdict in two places
(per the epic's own Deliverables 1–2):
- A verdict + evidence note appended to the ticket's own body (its own Implementation Notes or a new
  dedicated subsection), so the ticket carries its answer if picked up standalone later.
- A contribution to the classification document under `docs/plans/` (create it if no sibling pass
  has yet, per the epic's Deliverable 1; if `T02`/`T03`/`T04` already created it, append this pass's
  three entries rather than creating a second doc).

## Out of Scope
- **Fixing anything.** No code change lands under this ticket for any of the three tickets it
  classifies — a `DEFECT` verdict becomes its own future fix ticket, same as the epic's own rule.
- **Touching `registries/mechanisms.yaml`.** Must stay byte-for-byte unchanged, same guard as the
  epic and the wave that preceded it.
- **Re-deriving combat volume.** Not relevant to this corpus group, but the epic's hard constraint
  applies to every child regardless.
- **Classifying `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`.** Already `DEFECT`-verdicted
  by the wave; recording that verdict into the ticket body and classification doc is `T04`'s scope,
  not this ticket's. This ticket cites it, it does not re-derive or re-record it.
- **Any of the other 10 corpus tickets** covered by `T02`/`T03`/`T04`/`T05` (never-seeded,
  dead-guard, wave-confirmed/scale-conditioned, undeclared-design groups).
- **Assuming a shared root cause** across the three tickets classified here just because they share
  the "zero real callers" shape — the epic explicitly disconfirmed that hypothesis during the wave
  and any claim of a shared cause here must be proven with its own evidence, not assumed from the
  grouping.

## Acceptance Criteria
1. Each of `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`,
   `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS`, and
   `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` carries exactly one verdict from the four-value
   axis (`DEFECT` / `CONDITION` / `UNDECLARED` / `MISLABEL`), recorded in its own ticket body. (Maps
   to epic AC 1.)
2. Every verdict cites named evidence — a grep command and its actual output, a content fact (e.g. a
   registry/config value), or tick arithmetic. A verdict supported only by re-reading the code
   without re-running or re-confirming that evidence is not accepted. (Maps to epic AC 2.)
3. `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` is cited in this pass's classification-doc
   contribution as already `DEFECT`-verdicted by the wave (with a pointer to `T04`), and is **not**
   given a second, independently-derived verdict by this ticket. (Maps to epic AC 3's discipline,
   applied to the citation rather than a re-record.)
4. `registries/mechanisms.yaml` is byte-for-byte unchanged (`git diff --stat registries/
   mechanisms.yaml` empty) at this ticket's close. (Maps to epic AC 4.)
5. No `src/` or `tools/` behavior change lands under this ticket (`git diff --stat` shows only
   ticket/doc files touched, plus the classification doc). (Maps to epic AC 5.)
6. If any of the three classified tickets resists all four verdicts, that is recorded explicitly as
   a fifth outcome with the specific reason it resists classification — not forced into the nearest
   bucket. (Maps to epic AC 7.)

## Related Tickets
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — parent epic; this is its `T01` child.
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — cited only, not classified by this
  ticket; see `T04`.
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` — classified by this ticket.
- `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` — classified by this ticket.
- `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` — classified by this ticket.
- `TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (closed, PR #258) — method precedent this pass
  reuses (Card J's bounded-reachability procedure), and the source of `CALAMITY-INTENSITY`'s
  existing `DEFECT` verdict.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` (open) — adjacent, not merged: owns
  `regional_sovereignty`'s `implemented_by` registry correction; this ticket owns the separate
  question of `RegionalSovereigntyService`'s own runtime reachability verdict. Surfaced by this
  ticket's own overlap scan (score 20.6) as related, not duplicate — same relationship the epic
  itself already documented in its Out of Scope.
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (closed) — prior, earlier-generation instance of
  the same "zero live callers on real code" shape (7 instances, PR #148/#150); informational
  precedent for how that audit disposed of similar findings, not itself part of this corpus.

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` — cited in `CALAMITY-INTENSITY-PRODUCER-NEVER-
  FIRES`'s own Related Docs as a candidate entry once root cause is confirmed; carried forward here
  since this pass's citation of that ticket references the same underlying finding.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §4 — cited in `REGIONAL-SOVEREIGNTY-
  SERVICE-ORPHAN-TAXATION-DEBUFFS`'s own Related Docs as the correction note that first surfaced this
  ticket.
- `docs/plans/world_composition_precondition_gap_finding.md` — cited in `CALAMITY-INTENSITY-
  PRODUCER-NEVER-FIRES`'s own Completion Summary as "the durable record of this finding"; relevant
  background for this pass's citation-only handling of that ticket, not something this pass edits.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/` — Card J's bounded-reachability
  method (`investigation.md`, `plan.md`, `test_plan.md`), the precedent this pass's own evidence
  discipline follows.
- None of this ticket's own yet — standard tier; `staging_artifacts/TCK-20260929-UNREACHABLE-
  CLASSIFY-ZERO-CALLER/` (`plan.md`, `investigation.md`, `test_plan.md`) created when this ticket is
  picked up for implementation, per the project's standard-tier workflow rule.
- `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER/` — this ticket's own `investigation.md`/`plan.md`/`test_plan.md`, migrated at closure.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.CALAMITY_RANDOM_CHANCE`, `should_spawn` in
  `process_world_dynamics()`) — read-only re-verification of the zero-usages grep.
- `src/world/regional_sovereignty.py::RegionalSovereigntyService` — read-only pipeline trace for the
  orphan-taxation verdict.
- `src/world/influence.py::FactionInfluenceService` — read-only, for confirming this is the distinct
  live sovereignty mechanism `RegionalSovereigntyService` is not a duplicate of.
- `tools/perf/profile_api_payload.py`, `tools/perf/turbo_run.py` (reference fix pattern, read-only),
  `src/api/engine_manager.py`, `src/config/profiles.py`, `Makefile` — read-only confirmation of the
  dead-import verdict for the profile-api ticket.
- `registries/mechanisms.yaml` — read-only reference; must not be edited (see Out of Scope).

## Assumptions / Open Questions
- **Assumed:** no shared root cause across the three tickets classified here, despite sharing the
  "zero real callers / dead constant" shape. Not yet tested for this specific trio — `CALAMITY-
  RANDOM-CHANCE` and `REGIONAL-SOVEREIGNTY-SERVICE` both live in `src/world/`, which could tempt a
  "same refactor left both orphaned" narrative, but that must be proven (e.g. matching git-blame
  eras) rather than assumed, per the epic's own disconfirmed-hypothesis discipline.
- **Open:** whether the `docs/plans/` classification document (epic Deliverable 1) is a single doc
  incrementally built by `T01`–`T04` in whatever order they run, or something `T06` assembles from
  each pass's independent notes. This ticket's Scope assumes the former (create-or-append, whichever
  applies at pickup time) since `SEQUENCE.md` allows `T01`–`T04` to run in parallel and Deliverable 2
  (per-ticket body edits) is unambiguous either way; if wrong, the doc-assembly mechanics need
  correcting, not the verdicts themselves.
- **Environment note, actually observed in this worktree (not the planning worktree the epic's own
  note describes):** `mcp__knowledge-search__search_docs` was tested directly while scoping this
  ticket (query: "unreachable mechanism zero callers dead constant calamity classification") and
  returned real ranked results (8 hits, including `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`
  and `docs/world/ecology_and_calamity_contract.md`) — it is **not** dead here, unlike the epic's own
  caveat about the `m2-idea43-temporal-note` planning worktree. `graphify query` also returned live
  results (108 nodes). Whoever picks up this ticket should re-verify at that time rather than assume
  either state carries forward, but as of this scoping pass, both tools work in this worktree.
- **Tag note:** the `corpus` tag was chosen to mirror the parent epic's own tag set for cross-
  reference consistency, but see this ticket's own `tag_relevance_flags` output for a caveat on its
  registered-note fit.

## Implementation Notes

Classified 3 of the epic's 4 zero-caller / dead-constant tickets (the fourth, `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`, is cited and classified only in `T04`). Each verdict is recorded in the covered ticket's own body (epic Deliverable 2); evidence lives there and in `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER/investigation.md`.

| Covered ticket | Verdict | Evidence in one line |
|---|---|---|
| `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` | fifth outcome `NO-MECHANISM` (AC-7) | one grep hit (the declaration); introduced `562116889` 2026-05-18, never connected; docs already say dead; nothing executable to be unreachable |
| `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` | `UNDECLARED` | zero callers re-confirmed, **but** live `TownResolutionSystem.resolve()` (`pipeline.py:339`) implements taxation and a conquered-region penalty with different cadence/trigger/numbers; contract doc names the dead one |
| `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` | `DEFECT` | executed: `ImportError: cannot import name 'EngineManager'`; `SimulationConfig` undefined; `make profile-api` runs it |

Calibration, as directed: only the registry-orphan ticket has any `registries/mechanisms.yaml` involvement (a binding correction, not a verdict), so the registry-dating method used in `T02` was not applied; the general "date the cited code against the filing date" check was (no commits to the cited files since filing, apart from the `scripts/`->`tools/` move for the profile tool). No `STALE-PREMISE` was hunted for and none was found. One covered ticket's premise was partly wrong, which is a different thing: the registry-orphan ticket's "distinct capability never wired in" is incomplete because taxation is live elsewhere.

## Test Summary

Classification only; no repo test suite authored or run. Verification was repo-wide greps (commands and output recorded in each covered ticket's body), drift checks with `git log`, and one execution of `tools/perf/profile_api_payload.py` (fails). No scratch script was needed; nothing was committed outside ticket/artifact files.

## Files Changed

No `src/`/`tests/`/`tools/`/content change; `registries/mechanisms.yaml` confirmed byte-for-byte unchanged against `origin/main`. Files touched are ticket/artifact bookkeeping only:
- this ticket: `tickets/todos/` -> `tickets/inprogress/` -> `tickets/done/`; `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER/` (`investigation.md`, `plan.md`, `test_plan.md`) migrated from `staging_artifacts/` at closure.
- the three covered tickets (`TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`, `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS`, `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS`) — each carries its verdict.
- `docs/REGISTRY.yaml` — regenerated by Finalize's self-check, not hand-edited.

## Completion Summary
All three covered tickets carry a verdict: `NO-MECHANISM` (AC-7 fifth outcome), `UNDECLARED`, `DEFECT`. The pass produced one real correction to a covered ticket's premise (taxation is not an unwired capability; a competing live implementation exists) and one runtime-executed defect confirmation. No `CONDITION` verdict, so the epic's AC-6 run-length/content split does not apply here. Deferred, not dropped: the epic's shared classification document (Deliverable 1) belongs to `T06`; the wrong taxation source in `docs/world/regional_sovereignty_runtime_contract.md` and the constant's wire-vs-delete decision are left to their owners; `T04` records `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`. No push, PR or merge.
