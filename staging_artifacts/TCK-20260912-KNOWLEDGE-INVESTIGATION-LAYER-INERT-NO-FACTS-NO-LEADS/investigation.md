# Investigation — TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS

## Path decision: Gap 2 vs Gap 4

**Gap 4 (`PaidInformationTransactionSystem.enforce()`/`InformationProviderState`)**: assumed
cheap ("if cheap" per peer's own framing), found not to be. Zero production construction sites for
`InformationProviderState` (only tests). No existing role/archetype hook: `EntityRole` has
`SHOPKEEPER` (loose match to `MERCHANT`) but nothing for `GUILD_MASTER`/`ELDER`; no content
anywhere tags an entity with any of the three archetypes. Would need new world-authoring schema
work, not a call site.

**Gap 2 (`GuildAction.visit()`/`ENABLE_GUILD_QUEST_GENERATION`)**: already fully wired
(`GuildNeedScorer` → `GuildVisitPhase` → `GuildAction.visit()`), previously real-kernel-verified
by its own origin ticket (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`: "5 real quests generated in
`sandbox_world`"). `GuildNeedScorer` targets `town_hall`, present in every real corpus world (its
own code comment). Chosen.

## Real blocker found, not assumed: `"iron"` vs `"iron_vein"`

`GuildAction.visit()` checked `node.kind == "iron"`. The real content catalog
(`data/content/world/resources.yaml`) has no resource with that id — the real id is `"iron_vein"`.
Confirmed via grep: 0 of 15+ real corpus worlds have a `kind == "iron"` node; 15 have real
`iron_vein` nodes (including `frontier_living_world`, `frontier_extended`, `frontier_marches`,
`generated_frontier_3_42`, etc.). Confirmed via a real instrumented 300-tick run against
`frontier_living_world`: `leads_gained == 0` across 7 real `GuildAction.visit()` calls before the
fix, non-zero after.

**Two independent blockers, not one**: flag OFF (the ticket's own original framing) and this string
mismatch (found only by tracing real execution, not by reading the flag). Fixing either alone would
have produced zero observable change — exactly why this survived undetected since the mechanism was
first written.

## A third defect surfaced by fixing the second

Fixing the string mismatch made `GuildAction.visit()` produce real leads for the first time — which
immediately exposed `src/systems/strategic_systems/intelligence.py:406-436`'s belief-confirmation
loop throwing on every tick for every entity holding one of these leads (`LeadState.detail` format
mismatch: parseable `"x,y"` expected, free narrative text supplied). Caught by a bare
`except Exception`, logged, silently discarded — filed as
`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` rather than fixed inline (a real
design question, not an implementation detail). Checked: leads still land in
`entity.strategic.leads` regardless — only observation-based confirmation is affected.

## The propagation gap — found while shipping the flag flip

Flipped `FeatureFlagManager`'s own default for `ENABLE_GUILD_QUEST_GENERATION` to `ON`. Before
declaring this done, ran the exact test harness a real corpus profile
(`frontier_marches`) uses (`tools.calibrate_simq._run_engine` with the profile's own real
`feature_flags:` overrides) — zero `GuildAction`/`GuildNeedScorer` calls, identical to the pre-flip
state. Confirmed by reverting the flip entirely and re-running: bit-identical zero calls either way.

Root cause: `GuildNeedScorer.score()`/`GuildVisitPhase`'s own internal check both read
`state.feature_flags` directly with their own hardcoded `"OFF"` fallback — a completely separate
surface from `FeatureFlagManager`, which nothing in real production code seeds `state.feature_flags`
from. The earlier D-10 measurement only worked because it set the env var directly, populating
`state.feature_flags` through `tools/calibrate_simq.py`'s own override merge — a different path
entirely from the dict entry that was changed.

Filed `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (P0) with the
measured blast radius: exactly 1 of 28 flags currently disagrees between its manager default and
its own inner-gate fallback (the one this ticket just created); 8 more flags share the same
dual-gate shape and currently agree only by coincidence (both `OFF`); 19 flags are gated
exclusively through `FeatureFlagManager`/`run_phase()` and are unaffected.

## Also checked, ruled out as this ticket's own cause

4 hardcoded `NARRATIVE`-pillar anchors in `tests/unit/worldassembly/test_corpus_diversity.py`
initially looked broken by the flag flip (their own comments cite the flag's OFF state as the
reason for a zero anchor). Verified via revert-and-compare before touching anything: all 4 fail
identically with the flip fully reverted — pre-existing, unrelated NARRATIVE-pillar flakiness
(matches the wall-clock kernel-throttle variance already found and correctly left alone earlier
this same batch). Not this ticket's regression. Not touched.

## Disposition

Ticket stays `BLOCKED`, not `DONE`. D-10 stands as real evidence the mechanism works once actually
reached. The default flip does not reach real runs — closing this ticket `DONE` now would document
a feature as delivered while it remains inert in every real run.
