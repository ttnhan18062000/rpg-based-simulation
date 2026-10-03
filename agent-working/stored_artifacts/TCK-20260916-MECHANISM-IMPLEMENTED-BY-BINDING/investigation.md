---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING

## Trigger

Building `tools/mechanism_registry_completeness_check.py` (for
`TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`) as a regex-search-over-prose tool surfaced 47
"unmapped" false positives on first run. Root cause: the original 75 mechanisms have ZERO
source-path citations in `mechanisms.yaml` — their evidence
(`stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md`) cites atlas card
IDs and wiring-map node names only ("atlas `entity-cognition#13`; wiring-map MOT-->CAPT-->DEC"),
never a real file. A prose-text checker could only ever see the 11 mechanisms cited inline by
`TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS`.

A hand-authored path-to-mechanism-id lookup table inside the checker tool was considered and
rejected per peer review: it would be a second place the code<->mechanism relationship lives,
unverifiable in exactly the way the atlas citations turned out to be, and violates the user's own
standing principle (a piece of information is defined in one document only). The binding belongs
in the registry itself, as a field.

## What was built

1. `implemented_by: [<repo-relative path>, ...]` — optional field on the mechanism schema.
2. `mechanism_registry.py::validate()` invariant 7: every present `implemented_by` path must exist
   on disk. A deleted implementing module fails validation immediately.
3. `tools/mechanism_registry_completeness_check.py` rewritten to read `implemented_by`
   structurally (never regex-search prose). Reports three honest, non-overlapping buckets: bound
   (confirmed via a real path), excluded (confirmed infrastructure, reasoned), unbound (not yet
   checkable — explicitly NOT asserted to be a gap, since most almost certainly belong to one of
   the 69 mechanisms with no `implemented_by` yet).

## Population — dispatched sub-investigation, then independently verified

A background investigation classified the checker's first 47 "unmapped" targets (9 domain
directories whose name didn't directly match a mechanism id, 38 systems-subpackage files) against
the 86-mechanism registry. Its findings were NOT trusted blindly — the most consequential and
surprising ones were independently re-verified before acting:

- **`causal_spatial_memory` state-drift** (verified directly): registered `orphan`, but
  `MemoryUpdatePhase.apply()` is called live from `engine/pipeline.py:154-157` via
  `run_phase("memory_update", ..., "ENABLE_MEMORY_UPDATE")` — a real caller exists, gated OFF by
  default. `orphan` (zero callers) was factually wrong; corrected to `gated`, with a `verified`
  block recording the correction and its evidence.
- **Two new orphan mechanisms** (verified directly via `grep -rn "<ClassName>" src/`, confirming
  zero real callers outside the defining file): `group_coordination`
  (`social_systems/group_service.py::GroupService`) and `quest_reward_distribution`
  (`social_systems/reward_distribution.py::FairShareProtocol`).
- **One new partial mechanism** (verified directly): `commitment_pressure_consequences`, covering
  `src/domains/commitment/{pressure,impact,reputation,abandonment}.py`. NOT the real implementation
  of the already-registered `commitment_betrayal` (that is `Betrayal(FactionDirective)` in
  `engine/faction_decision.py` and `BetrayalRecord` in `core/models/social.py` — a real
  namespace-adjacent trap, confirmed by checking both locations directly). Mixed disposition within
  one domain: `pressure.py`/`impact.py` have zero real callers (orphan-within); `reputation.py`
  (called from `engine/quests.py:227`) and `abandonment.py` (called from
  `observability/event_extractor.py`, default-ON) are live — same "partial" shape already
  established for `belief_institution`.
- **Six existing-mechanism bindings added** after direct verification of each claimed caller:
  `adventure_routing` (`domains/adventure/service.py`), `cultural_drift`
  (`domains/culture/deriver.py`), `demographic_cohort_cycle` (`domains/demographics/cohort.py`),
  `diplomacy` (`domains/faction/diplomatic_state_machine.py`), `temporal_pressure`
  (`domains/time/service.py`), plus `causal_spatial_memory` above.
- **Not populated**: the sub-investigation's remaining ~30 candidate systems-file bindings (mostly
  high-confidence matches to already-registered mechanisms, e.g. `chests`→
  `inventory_trade_conservation`, `guilds`→`guilds`, `party`→`party_formation`) and the two
  domain-level findings flagged as genuinely ambiguous (`domains/information`: split between
  `belief_institution` and `information_trust_deception`; `domains/world_emergence`: split between
  `opportunity_rumor_seeds` and `quest_generation_sourcing`, multiple files each) — left for organic
  backfill rather than rushed in under this ticket's own scope, per peer review ("don't populate
  all 86 now... it grows organically").

## Outcome

20 of 89 mechanisms now carry a real `implemented_by` binding. The completeness checker reports
this honestly as its own visible, shrinking gap rather than a hidden one, and never conflates
"not yet bound" with "missing" — the exact overclaiming failure this whole epic exists to catch,
just in the opposite direction from the one `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS`
caught.
