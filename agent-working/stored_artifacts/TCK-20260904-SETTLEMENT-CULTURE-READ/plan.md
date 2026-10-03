---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-SETTLEMENT-CULTURE-READ
artifact_type: plan
tags: [content, documentation]
---

# Implementation Plan — TCK-20260904-SETTLEMENT-CULTURE-READ

## Summary

Adopt the investigation's recommended design as-is: a new pure `SettlementPersonalityService.describe(culture)`
function that wraps the already-certified `CulturalBiasApplicator.compute_culture_delta` over a
canonical tag set (no new formulas, no threshold changes — WORLD-CULT-002/003 stay untouched), a new
read-only `CampaignOrchestrator.describe_settlement_personality(region_id)` method that composes
`CultureDriftImporter.get_culture` + the new service (does not touch `_build_initial_state()` /
`_advance_state()`), and a new `GET /api/v1/campaigns/{campaign_id}/regions/{region_id}/personality`
REST endpoint in `src/api/routes/campaigns.py` mirroring the existing `/history` endpoint's exact
shape (module-level `_CAMPAIGN_REGISTRY` read, Pydantic presenter, 404-on-unknown-campaign). The
consumer is scoped to **Region granularity** (`RegionState.id`/`RegionState.name`, confirmed at
`src/core/state.py:259-263`) — not `PlaceState`, which has no name/display field
(`src/core/state.py:335-360`, only `place_id`/`region_id`) and is explicitly not touched. The plan
also covers three non-code deliverables the ticket's AC requires: two doc corrections (atlas idea-61
card, `culture_drift_contract.md`), filing a new ticket for the `CampaignOrchestrator` Region/Place-
carry gap, and one new parity ledger entry for the new consumer's behavior claim.

## Steps

### Step 1 — New pure `SettlementPersonalityService`
**Files:** `src/domains/culture/settlement_personality.py` (new)
**Change:** Add a new module, structurally mirroring `src/domains/culture/applicator.py`
(read at `src/domains/culture/applicator.py:1-93`) and `src/domains/culture/model.py`
(read at `src/domains/culture/model.py:24-67` — `CultureState` is a frozen dataclass with exactly
four float axes: `fatalism`, `hero_veneration`, `resource_scarcity_memory`,
`faction_conflict_exposure`, each defaulting `0.0`).

Define:
```python
CANONICAL_TAGS: Tuple[str, ...] = (
    "caution", "recovery", "flee", "pride", "combat",
    "aggressive", "loyalty", "party", "survival",
)
# The full union of tags CulturalBiasApplicator's axis rules key off of
# (src/domains/culture/applicator.py:31-36) — reusing this set (not inventing a new
# one) keeps the new service's output traceable 1:1 to already-verified axis→tag rules.

_AXIS_TRAIT_NAMES: Dict[str, str] = {
    "fatalism": "fatalistic",
    "hero_veneration": "hero_venerating",
    "resource_scarcity_memory": "scarcity_scarred",
    "faction_conflict_exposure": "conflict_hardened",
}

@dataclass(frozen=True, slots=True)
class SettlementPersonalityDescriptor:
    traits: Tuple[str, ...] = ()
    tag_deltas: Dict[str, float] = field(default_factory=dict)

    @property
    def is_neutral(self) -> bool:
        return not self.traits

class SettlementPersonalityService:
    @staticmethod
    def describe(culture: Optional["CultureState"]) -> SettlementPersonalityDescriptor:
        if culture is None:
            return SettlementPersonalityDescriptor()
        traits = tuple(
            trait_name
            for axis_name, trait_name in _AXIS_TRAIT_NAMES.items()
            if getattr(culture, axis_name) > CULTURE_ACTIVATION_THRESHOLD
        )
        tag_deltas = {
            tag: CulturalBiasApplicator.compute_culture_delta(culture, [tag])
            for tag in CANONICAL_TAGS
        }
        return SettlementPersonalityDescriptor(traits=traits, tag_deltas=tag_deltas)
```
Import `CULTURE_ACTIVATION_THRESHOLD` and `CulturalBiasApplicator` from
`src.domains.culture.applicator` — do not redefine the threshold constant (currently `0.3`,
`src/domains/culture/applicator.py:29`) locally; a divergent copy would silently create two
"personality activates" definitions per the test plan's own Anti-Drift Test Guard. `describe()` is
pure, stateless, and never imports `AuthoritativeState`/`EntityState` (matches `CultureState`'s own
module-doc constraint at `src/domains/culture/model.py:8`).

Neutral/zero behavior falls out of reuse, not new logic: `compute_culture_delta` already returns
`0.0` when every axis is `<= CULTURE_ACTIVATION_THRESHOLD` (`src/domains/culture/applicator.py:92`),
so `culture=None` and an all-default `CultureState()` both produce `traits=()` and all-`0.0`
`tag_deltas` — satisfying test-plan items 1 and 2 without a special-cased branch for the zero-axes
case.

**Do NOT touch:** `src/domains/culture/applicator.py`, `src/domains/culture/deriver.py`,
`src/domains/culture/exporter.py`, `src/domains/motivation/service.py` — this step only adds a new
caller, no existing culture-substrate file changes.
**Verify:** `tests/unit/domains/culture/test_settlement_personality.py` (new) — test-plan items 1–5:
`test_describe_with_none_culture_returns_neutral_descriptor`,
`test_describe_with_zero_axes_culture_returns_neutral_descriptor`,
`test_describe_with_high_fatalism_axis_produces_fatalistic_signal`, one test per remaining axis
(`hero_veneration`, `resource_scarcity_memory`, `faction_conflict_exposure`), `test_describe_delta_bounded`.
Run: `pytest tests/unit/domains/culture/ -v`.

---

### Step 2 — `CampaignOrchestrator.describe_settlement_personality(region_id)` read method
**Files:** `src/domains/campaigns/orchestrator.py`
**Change:** `CampaignOrchestrator.__init__` (read at `src/domains/campaigns/orchestrator.py:134-144`)
constructs `self._state = CampaignState(campaign_id=manifest.id, episode_index=0)`; the existing
`state` property (`orchestrator.py:146-149`) already exposes it read-only
(`"""Current mutable CampaignState. Read-only property; do not replace."""`). Add a new method
directly below the `state` property:
```python
def describe_settlement_personality(self, region_id: str) -> SettlementPersonalityDescriptor:
    """Pure read: settlement-personality signal for a region from carried-forward culture.

    Composes CultureDriftImporter.get_culture() + SettlementPersonalityService.describe().
    Does not read or mutate episode_index, persistent_entities, or narrative_ledger, and
    never calls _build_initial_state()/_advance_state() — this is a query over
    already-populated CampaignState.region_cultures, not an episode-boundary hook.
    """
    culture = CultureDriftImporter.get_culture(self._state, region_id)
    return SettlementPersonalityService.describe(culture)
```
Add the two new imports (`from src.domains.culture.exporter import CultureDriftImporter`,
`from src.domains.culture.settlement_personality import SettlementPersonalityService,
SettlementPersonalityDescriptor`) alongside the existing `src.domains.campaigns.*` imports at the
top of the file (`orchestrator.py:28-51`).

`CultureDriftImporter.get_culture(campaign_state, region_id)` (read at
`src/domains/culture/exporter.py:64-79`) already returns `Optional[CultureState]` and "does not
raise — unknown regions return None" (its own docstring, line 74) — so when `region_id` has no
entry in `self._state.region_cultures` (the default state for every one of the 21 corpus worlds per
investigation.md's Risks section), `describe_settlement_personality` returns
`SettlementPersonalityDescriptor()` (the neutral descriptor object, `traits=()`), not a bare Python
`None`. **This is a deliberate resolution of test-plan item 7's ambiguous "returns None/neutral"
wording** — the method always returns a `SettlementPersonalityDescriptor` object and never returns
`None`, so downstream callers (including the REST endpoint in Step 3) never need a null-check branch.
Rename test-plan item 7 to `test_campaign_orchestrator_describe_settlement_personality_with_unknown_region_returns_neutral_descriptor`
when writing it, and assert `result.is_neutral is True` / `result.traits == ()`, not `result is None`.

**Other writers to `CampaignState`/`orchestrator._state` (enumerate, since this step reads a field
other code mutates):** `CampaignOrchestrator._advance_state()` (`orchestrator.py:226-230`, confirmed
by investigation.md) is the only writer to `region_cultures` (via `CultureDriftExporter.export()`,
`src/domains/culture/exporter.py:30-61`), and it runs once per completed episode, synchronously,
inside `run_episode()`. `describe_settlement_personality()` never calls `run_episode()`,
`_advance_state()`, or `_build_initial_state()` itself — it only reads `self._state` at whatever
point the caller invokes it, the same pattern the existing `state` property already uses. There is no
concurrent-write hazard: `CampaignOrchestrator` is not used across threads/async tasks in this
codebase (single-threaded per-campaign orchestration, confirmed by `run_episode()`'s synchronous
`svc.start()` call at `orchestrator.py:176`), so a call to `describe_settlement_personality()`
between two `run_episode()` calls simply observes whatever `region_cultures` state existed at call
time — an ordinary read-after-write, not a race.
**Do NOT touch:** `_build_initial_state()`, `_advance_state()`, `run_episode()`, `CarryForwardRules`,
or any other orchestrator method — this step adds one new method only.
**Verify:** `tests/unit/domains/campaigns/test_settlement_personality_read.py` (new) — test-plan
items 6–7 (renamed per above). Must assert `episode_index`, `persistent_entities`, and
`narrative_ledger` are unchanged before/after calling the new method (test-plan's own
"`_build_initial_state()`/`_advance_state()` untouched guard"). Seed `region_cultures` directly the
way `test_culture_exporter.py` does (construct a `CultureCarryForward` and assign into
`orchestrator.state.region_cultures[region_id] = ...` — note `state` is read-only as a *property
reassignment* but the underlying dict is still mutable in place, matching how `_advance_state()`
itself populates it at `exporter.py:56-61`). Run: `pytest tests/unit/domains/campaigns/ -v`.

---

### Step 3 — REST endpoint + presenter
**Files:** `src/api/routes/campaigns.py`, `src/api/presenters/campaigns.py`
**Change:** In `src/api/presenters/campaigns.py`, add a new presenter alongside
`NarrativeLedgerEntryPresenter`/`CampaignHistoryResponse` (read at
`src/api/presenters/campaigns.py:18-58`):
```python
class SettlementPersonalityResponse(BaseModel):
    """Shaped read model for GET /api/v1/campaigns/{id}/regions/{region_id}/personality."""

    campaign_id: str
    region_id: str
    traits: List[str]
    tag_deltas: Dict[str, float]
    is_neutral: bool

    @classmethod
    def from_domain(
        cls, descriptor: Any, campaign_id: str, region_id: str
    ) -> "SettlementPersonalityResponse":
        return cls(
            campaign_id=campaign_id,
            region_id=region_id,
            traits=list(descriptor.traits),
            tag_deltas=dict(descriptor.tag_deltas),
            is_neutral=descriptor.is_neutral,
        )
```
Uses attribute access on `descriptor` (typed `Any` in the signature), not a domain import — same
one-way-dependency discipline `NarrativeLedgerEntryPresenter.from_domain` already follows
(`src/api/presenters/campaigns.py:33-40`, its own comment: "preserving the one-way dependency
direction (presenter → domain is fine, domain → presenter is forbidden)").

In `src/api/routes/campaigns.py`, add a new route directly below `get_campaign_history`
(`src/api/routes/campaigns.py:66-133`), following its exact structure — same `_CAMPAIGN_REGISTRY`
lookup, same 404-on-unknown-campaign / 500-on-unexpected-error shape:
```python
@router.get(
    "/{campaign_id}/regions/{region_id}/personality",
    response_model=SettlementPersonalityResponse,
    summary="Get settlement personality signal for a region",
    description=(
        "Return a Culture-Drift-derived personality signal for a region within the "
        "specified campaign, or a neutral descriptor if no culture data has been "
        "derived for that region yet."
    ),
    responses={
        404: {"description": "Campaign not found"},
        500: {"description": "Internal error"},
    },
)
async def get_settlement_personality(
    campaign_id: str, region_id: str
) -> SettlementPersonalityResponse:
    state = _CAMPAIGN_REGISTRY.get(campaign_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign '{campaign_id}' not found.",
        )
    try:
        culture = CultureDriftImporter.get_culture(state, region_id)
        descriptor = SettlementPersonalityService.describe(culture)
        return SettlementPersonalityResponse.from_domain(descriptor, campaign_id, region_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve settlement personality: {exc}",
        ) from exc
```
Add imports: `from src.domains.culture.exporter import CultureDriftImporter`,
`from src.domains.culture.settlement_personality import SettlementPersonalityService`, and extend
the existing `from src.api.presenters.campaigns import (...)` line to include
`SettlementPersonalityResponse`.

**Note the deliberate non-composition with Step 2**: this route reads `CampaignState` directly from
`_CAMPAIGN_REGISTRY` (a `Dict[str, CampaignState]`, `src/api/routes/campaigns.py:37`), not through a
`CampaignOrchestrator` instance — the registry never stores orchestrators, only their `CampaignState`
(confirmed: `register_campaign(campaign_id, state)`'s signature takes `state: CampaignState`,
`src/api/routes/campaigns.py:40-50`). This exactly matches the existing `/history` endpoint's own
pattern (`state.narrative_ledger` read directly, no orchestrator call, `campaigns.py:117`). Both
Step 2's orchestrator method and this route independently call the same two pure functions
(`CultureDriftImporter.get_culture` + `SettlementPersonalityService.describe`) against different
`CampaignState` sources — this is not duplicated logic, it is the same two pure calls composed twice
against two different, legitimate holders of `CampaignState` (in-process orchestrator vs.
API-registered state), matching how `state` (a `CampaignState`) and `_CAMPAIGN_REGISTRY` values are
already two independent access paths to the same object shape today.

**Other writers to `_CAMPAIGN_REGISTRY` (enumerate, since this route reads it):** only
`register_campaign()` (`campaigns.py:40-50`) writes to it, and `unregister_campaign()`
(`campaigns.py:53-55`) removes from it; `_clear_registry()` (`campaigns.py:58-60`) is test-only. Per
investigation.md, **`register_campaign()` has zero production call sites today** — confirmed by
investigation, not re-verified here since Step 4 below explicitly disposes of this finding rather
than silently inheriting it. This new route is therefore reachable in tests (via direct
`register_campaign()` calls, matching `tests/api/test_campaign_history_api.py`'s own pattern, read
at `tests/api/test_campaign_history_api.py:1-80`) and via the FastAPI router (already mounted at
`src/api/server.py:137`, confirmed registered), but — exactly like the existing `/history`
endpoint — not reachable from a real running `CampaignOrchestrator` today, because nothing calls
`register_campaign()` after constructing one. See Step 4 for the explicit disposition of this gap.

**Do NOT touch:** `get_campaign_history`, `register_campaign`, `unregister_campaign`,
`_clear_registry`, `NarrativeLedgerEntryPresenter`, `CampaignHistoryResponse` — additive only.
**Verify:** extend `tests/api/test_campaign_history_api.py` (read at
`tests/api/test_campaign_history_api.py:1-80` for the exact pattern: direct `await
get_campaign_history(...)` call, no HTTP client, `register_campaign()`/`_clear_registry()` fixture)
with the new endpoint's tests — test-plan items 8–9:
`test_settlement_personality_endpoint_returns_shaped_presenter_not_raw_domain_object`,
`test_settlement_personality_endpoint_404_for_unregistered_campaign`,
`test_settlement_personality_endpoint_empty_for_unknown_region`. Run: `pytest tests/api/ -k campaign -v`.

---

### Step 4 — Dispose of the `register_campaign()` reachability gap explicitly (disclosure, not a fix)
**Files:** `tickets/inprogress/TCK-20260904-SETTLEMENT-CULTURE-READ.md` (this ticket's own body —
`## Assumptions / Open Questions` and `## Completion Summary` sections)
**Change:** Per the ticket brief's resolution requirement and investigation.md's own recommendation
("Recommend the latter (defer, name explicitly)"): **do not** wire a real `register_campaign()` call
site into `CampaignOrchestrator` as part of this ticket. That would mean deciding *where*
production code should call it (API-triggered campaign creation? CLI? — genuinely unclear and
out of this ticket's investigated scope) — a scope expansion the ticket's Out of Scope section does
not authorize. Instead, when filling in the ticket's `## Completion Summary` at close, explicitly
state: "The new `/regions/{region_id}/personality` endpoint is correct and tested but inherits the
same 'router-registered but not reachable from a real running campaign' status the existing
`/history` endpoint already has, because `register_campaign()` (`src/api/routes/campaigns.py:40-50`)
has zero production call sites — a pre-existing gap this ticket does not fix." This satisfies the
Anti-Drift Hazard in test_plan.md ("Do not let a green done-checker pass stand in for confirming the
consumer is genuinely exercised outside tests").
**Do NOT touch:** `CampaignOrchestrator.__init__`/`run_episode()` to add a `register_campaign()` call
— that is the scope expansion this step exists to explicitly decline.
**Verify:** no test — this is a documentation/disclosure step. Confirm at Finalize that the
Completion Summary sentence above (or equivalent) is present before the ticket moves to
`tickets/done/`.

---

### Step 5 — Correct the atlas idea-61 card
**Files:** `docs/brainstorm/rpg_feature_atlas.html`
**Change:** Confirmed current text at `docs/brainstorm/rpg_feature_atlas.html:2680-2691` (verify
against live file content before editing, per investigation.md's own Anti-Drift Hazard — the file
may have moved between investigation and implementation; re-grep for
`id="idea-61"` — actually the card has no literal `id="idea-61"` attribute, it is matched by its
`"title": "61. Settlements Develop Personalities..."` string at line 2681 and the nearby anchor
`#idea-61` referenced from the sequencing table at line 822 — locate by that title string, not by
an HTML id). Replace the single badge object at lines 2683-2686:
```json
{
  "cls": "gated",
  "text": "Blocked — the mechanism it needs (Culture Drift) is real and live, but has zero callers anywhere; not buildable until that's wired"
}
```
with a corrected badge reflecting this ticket's own shipped state, e.g.:
```json
{
  "cls": "shipped",
  "text": "Shipped (read-side) — CultureDeriver/write-side was already live; this ticket added the read-side consumer (SettlementPersonalityService + CampaignOrchestrator.describe_settlement_personality + REST endpoint), scoped to Region granularity, non-Campaign-mode-episode-machinery only"
}
```
(match whatever `cls` values the rest of the atlas file's badge vocabulary already uses for a
shipped/done card — grep other cards' `"cls":` values before picking one, do not invent a new CSS
class name unsupported by the page's stylesheet). Append (do not delete) a new `<strong>...</strong>`
correction sentence to the end of the existing `"desc"` field (line 2689), following the file's own
established pattern of appending dated correction notes rather than rewriting prior text (see the
precedent at lines 2677 and 2137) — state plainly: `CultureDeriver`/write-side confirmed live;
`CulturalBiasApplicator` read-side was zero-call-site until this ticket; `MotivationBiasService`
(the class `CulturalBiasApplicator` was built to extend) remains entirely dead code in production,
independent of this ticket (per investigation.md's broader finding, not just `CulturalBiasApplicator`
itself); the real remaining gap is `CampaignOrchestrator`-Region/Place-carry reachability, tracked by
the new ticket filed in Step 6.
**Do NOT touch:** any other idea card in this file, the sequencing table's idea-61 cross-references
(line 822 — unaffected by this change), or idea 48/23's own cards.
**Verify:** no automated test (doc file); confirm the exact replaced text no longer matches the stale
string at Finalize (`grep -c "zero callers anywhere" docs/brainstorm/rpg_feature_atlas.html` should
no longer match this specific occurrence — note the string also appears at line 2137 for an unrelated
card (`WOUND_THRESHOLD_RATIO`); only the idea-61 occurrence must change).

---

### Step 6 — File the new Campaign-mode Region/Place-carry ticket
**Files:** `tickets/todos/TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY.md` (new — exact filename TBD by
whichever short-scope slug the ticket-creation step picks; must start `TCK-20260904-` per today's
date and follow the uppercase-hyphen `TCK-YYYYMMDD-SHORT-SCOPE.md` convention)
**Change:** Create a new ticket following the exact Required Sections template in
project `CLAUDE.md` ("Ticket Format"). Populate:
- `## Title`: `CampaignOrchestrator._build_initial_state() never carries Region/Place into per-episode AuthoritativeState`
- `## Tier`: standard (real code change to `_build_initial_state()`, not a hotfix-sized diff)
- `## Type`: bug / repair
- `## Priority`: P2 (confirmed no corpus world exercises Campaign mode today per
  investigation.md's Risks section — real but not urgent)
- `## Request Summary`: cite `src/domains/campaigns/orchestrator.py:575-655` (per investigation.md)
  — `_build_initial_state()` constructs `AuthoritativeState(tick=0, seed=episode_seed)` with no
  `regions=` argument and never calls `WorldCompiler.compile()`, so `state.regions` is empty for
  every Campaign-mode episode; contrast with every non-Campaign entrypoint
  (`src/cli/entry.py:223-228`, `src/api/engine_manager.py:136`, `src/lab/orchestrator.py:198`,
  `src/worldbuilding/cli.py:282`), all of which do call `WorldCompiler.compile()`. Also cite the
  corroborating `TownResolutionSystem.resolve()` early-exit
  (`src/engine/town_resolution.py:38-43`) as independent evidence of the blocker's severity.
- `## Scope`: fix `_build_initial_state()` to call `WorldCompiler.compile()` (or an equivalent) and
  thread `regions=`/`places=` into the constructed `AuthoritativeState`, for both the episode-0 and
  survivor-reconstruction branches.
- `## Out of Scope`: explicitly exclude the second, distinct plumbing gap this ticket's own
  investigation flagged — even after Region/Place carry is fixed, `region_cultures` still would not
  automatically reach in-episode `AuthoritativeState`/`EntityState` (no field currently threads it
  through); name that as a further, even-later dependency, not something the new ticket must also
  solve.
- `## Related Tickets`: this ticket (`TCK-20260904-SETTLEMENT-CULTURE-READ`) and
  `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`.
- `layer:` frontmatter — `world` (registered, `python3 tools/layer_registry.py list` confirms; matches
  this ticket's own layer and the subject matter: "World generation, worldbuilding, region/biome
  content").
- `tags:` frontmatter — verify against `python3 tools/tag_registry.py list` before finalizing; no
  tag matching "campaign"/"region"/"carry" is registered today (confirmed by this plan's own registry
  check), so use already-registered tags that fit (e.g. `world`) rather than inventing new ones
  mid-ticket-filing; register a new tag only if truly nothing existing fits, per the Hard Rule.
**Do NOT touch:** do not begin implementing the fix itself — this step only files the ticket. Do not
put it in `tickets/inprogress/` — it belongs in `tickets/todos/` per the workflow (a new, unstarted
unit of work).
**Verify:** `python3 tools/validate_frontmatter.py tickets/todos/TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY.md`
(or the project's equivalent frontmatter validator) passes; the new ticket ID is referenced by ID in
this ticket's own `## Related Tickets` section (already scaffolded as a placeholder line in the
ticket body — replace `(new, to be filed by this ticket) Campaign-mode Region/Place-carry gap...`
with the real ID once filed).

---

### Step 7 — Doc corrections: `culture_drift_contract.md` and `rpg_m4_beyond_city_epic.md`
**Files:** `docs/world/culture_drift_contract.md`, `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`
**Change:** In `culture_drift_contract.md`, per investigation.md: (a) correct the "Purpose" section's
present-tense claim that culture state "produces measurable differences in entity motivation scoring"
to note this is true in tests today and, as of this ticket, also true via the new read-side consumer
described below — not (yet) via any per-tick entity-decision path (`MotivationBiasService` remains
uncalled in production); (b) add a new row to the "Integration Points" table for the new consumer:
`SettlementPersonalityService.describe()` (pure) +
`CampaignOrchestrator.describe_settlement_personality()` (orchestrator-layer read) +
`GET /api/v1/campaigns/{id}/regions/{id}/personality` (REST), noting the contract currently stops at
`CultureDriftImporter` with no listed caller — this closes that gap. In
`rpg_m4_beyond_city_epic.md`, update item 3 (idea 61) to record the read-side consumer has shipped,
referencing this ticket's ID and the Step 6 ticket's ID, mirroring how item 1's 2026-09-04 status
update was recorded for the Camp/Nest classification ticket (per investigation.md's Docs Requiring
Update section).
**Do NOT touch:** `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`,
`docs/mechanics/05_world_evolution.md`, `rpg_m5_memory_reputation_epic.md`,
`rpg_m6_political_identity_epic.md` — investigation.md explicitly confirms none of these require
changes for this ticket (formulas unaffected; broader doc-language corrections are the hardening
plan's own separate scope, per this ticket's Out of Scope).
**Verify:** no automated test; confirm via read-back that both docs' new text accurately names the
three concrete new symbols from Steps 1–3 (not placeholder/aspirational language). Run
`make knowledge-index-update` at Finalize since `docs/` files changed (per project CLAUDE.md's After
Work rule).

---

### Step 8 — New parity ledger entry
**Files:** `docs/parity_ledger/world_dynamics.yaml`
**Change:** This ticket introduces one new, distinct behavior claim ("a settlement-personality
descriptor derives named traits and bounded per-tag deltas from a region's `CultureState`, reusing
`CulturalBiasApplicator`'s existing axis/threshold/clamp rules unchanged") that is not covered by
the three existing culture entries (`WORLD-CULT-001` — round-trip, `WORLD-CULT-002` — deriver axis
rules, `WORLD-CULT-003` — applicator delta rules; all confirmed `status: verified` at
`docs/parity_ledger/world_dynamics.yaml:1243-1255` and unaffected by this ticket per investigation.md
— no edit to those three entries). Per project CLAUDE.md's Parity rule and investigation.md's own
flag ("If Plan's final design introduces a genuinely new, distinct behavior claim... a new parity
entry should be added"), add a new entry `WORLD-CULT-004` immediately after `WORLD-CULT-003`
(`docs/parity_ledger/world_dynamics.yaml:1255`), matching the existing entries' exact schema shape:
```yaml
- id: WORLD-CULT-004
  text: 'A region with at least one culture axis above CULTURE_ACTIVATION_THRESHOLD (0.3)
    produces a SettlementPersonalityDescriptor with a non-empty traits tuple and non-zero
    tag_deltas for that axis'"'"'s canonical tag group; a region with no CultureState data
    (the default for all 21 registered corpus worlds) produces the neutral empty descriptor.'
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: src/domains/culture/settlement_personality.py; reuses
    CulturalBiasApplicator.compute_culture_delta unchanged, adds no new axis/threshold/clamp
    rules — a new caller, not new derivation logic
  proof_type: parity
  test_path: tests/unit/domains/culture/test_settlement_personality.py::test_describe_with_high_fatalism_axis_produces_fatalistic_signal
```
Use `tools/parity_ledger_writer.py` (the sanctioned, schema-validating tool) to make this edit, not a
raw `Edit`/ad-hoc script against the full YAML file — a hand-written full-file rewrite of a large
generated YAML risks corruption; the sanctioned writer tool is safe for this kind of targeted append.
Priority `P2` (not P0/P1): this is a new consumer of already-`P1`-verified formulas, not a Mechanics
Bible chapter itself, and the ticket's own AC does not require P0/P1 treatment.
**Do NOT touch:** `WORLD-CULT-001`/`002`/`003` entries' `status`/`v2_evidence` fields — investigation.md
confirms this ticket does not change their underlying formulas.
**Verify:** whatever schema-validation the parity ledger tooling runs (e.g.
`python3 tools/validate_parity_ledger.py docs/parity_ledger/world_dynamics.yaml` or equivalent —
confirm exact tool name before running) passes; the new entry's `test_path` test (Step 1's test file)
passes.

## Scope Guards

- Do not extend `CampaignOrchestrator._build_initial_state()` to carry compiled regions/places into
  per-episode `AuthoritativeState` — tracked by the new ticket filed in Step 6, not built here.
- Do not add any code path threading `region_cultures`/`CultureState` into `AuthoritativeState` or
  `EntityState` fields — confirmed by investigation.md as a second, distinct plumbing gap beyond
  Region/Place carry; out of scope for both this ticket and the Step 6 ticket.
- Do not wire `CulturalBiasApplicator`/`MotivationBiasService`/the new `SettlementPersonalityService`
  into `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) — rejected as the primary
  consumer by investigation.md because (a) that scorer only ever sees
  `AuthoritativeState`/`EntityState`, which has no channel to `CampaignState.region_cultures` at all
  (would be dead code in practice), and (b) an unconditional new additive term risks silently
  invalidating `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`
  (`src/systems/strategic_systems/intelligence.py`, guarded by
  `tests/architecture/test_adventure_route_score_max_unchanged.py`, STRAT-186, shared by
  `RegionStabilizationGoalScorer`/`SocialContractGoalScorer`). No step in this plan touches
  `src/domains/adventure/scoring.py` or `src/systems/strategic_systems/intelligence.py`.
- Do not add a `name`/display-identity field to `PlaceState` (`src/core/state.py:335-...`) — the
  Region-granularity design (Steps 1-3, keyed on `RegionState.id`/`.name`) avoids needing this; the
  gap is named, not solved, per the ticket's Scope bullet 4.
- Do not wire a real `register_campaign()` call site into `CampaignOrchestrator` — Step 4 explicitly
  disclose-not-fixes this pre-existing gap.
- Do not edit `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`,
  `docs/mechanics/05_world_evolution.md`, `rpg_m5_memory_reputation_epic.md`, or
  `rpg_m6_political_identity_epic.md` — confirmed not required by investigation.md.
- Do not modify `WORLD-CULT-001`/`002`/`003` parity entries — only append `WORLD-CULT-004`.

## Dependency Map

- Step 1 has no dependencies — pure module, can be built and tested standalone first.
- Step 2 depends on Step 1 (imports `SettlementPersonalityService`/`SettlementPersonalityDescriptor`).
- Step 3 depends on Step 1 (imports the same service) but not on Step 2 (calls the service directly,
  not through the orchestrator method) — Steps 2 and 3 can be built in either order or in parallel
  once Step 1 lands.
- Step 4 depends on Step 3 existing (it discloses that endpoint's reachability status).
- Step 5 (atlas) is independent of Steps 1-4 — can be done any time, but references the concrete
  symbol names Steps 1-3 introduce, so sequence it after Step 3 to avoid citing names that later
  change during implementation.
- Step 6 (new ticket) is independent of all code steps — can be filed at any point, but Related
  Tickets cross-references should be finalized after Step 5 corrects the atlas card, since both
  reference the same gap.
- Step 7 depends on Steps 1-3 (references their concrete symbol names) and Step 6 (references its
  ticket ID).
- Step 8 depends on Step 1 (the new test_path it cites must exist and pass).

Suggested implementation order: 1 → 2 → 3 → 4 → 8 → 5 → 6 → 7 (doc/ticket-filing steps last, once all
concrete symbol names and IDs exist to cite accurately).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `investigation.md` records a definite answer to whether any real corpus world runs multi-episode Campaign mode today | Already satisfied by investigation.md (Risks and Open Questions section: "Answered ... No.") — no plan step needed | N/A (doc content, not code) |
| A read-side consumer exists that reads `region_cultures` (or the `CultureState` it derives from) and produces a settlement/Place-level personality signal, scoped explicitly to non-Campaign-mode consumption | Steps 1, 2, 3 | `tests/unit/domains/culture/test_settlement_personality.py`, `tests/unit/domains/campaigns/test_settlement_personality_read.py`, extended `tests/api/test_campaign_history_api.py` |
| A new ticket is filed for the `CampaignOrchestrator` Region/Place-carry gap and referenced by ID in this ticket's Related Tickets / Out of Scope | Step 6 | `validate_frontmatter.py` on the new ticket file; manual cross-reference check |
| `docs/brainstorm/rpg_feature_atlas.html`'s idea 61 card badge/text is corrected to distinguish `CultureDeriver` (live) from `CulturalBiasApplicator` (zero production call sites) and to name the real Campaign-mode-reachability gap | Step 5 | Manual read-back; stale-string grep check |
| New tests cover the read-side consumer's behavior given populated vs. empty/absent `region_cultures` data | Steps 1, 2, 3 (test-plan items 1-2, 6-7, 9 specifically cover empty/absent; items 3-4, 6, 8 cover populated) | Same test files as row 2 |

Note: the ticket's stated AC list (`## Acceptance Criteria` in the ticket body) does not use the
field names "traits"/"tag_deltas"/"SettlementPersonalityDescriptor" — those are this plan's own
concrete naming choices for satisfying the AC's generic "produces a settlement/Place-level
personality signal" language. Confirmed no contradiction: the AC's wording is intentionally generic
("a settlement/Place-level personality signal") precisely because investigation.md flagged exact
naming as a Plan-phase decision, not a ticket-locked field name — Region-granularity substitutes for
"Place-level" per the ticket's own Scope bullet 4 requiring this substitution to be named explicitly
(done in this plan's Summary and Scope Guards).

## Anti-Drift Notes

- **`register_campaign()` reachability**: Step 4 exists specifically so a green `done-checker` pass
  does not get mistaken for "the new endpoint is exercised by real gameplay." Carry this sentence
  into the ticket's own Completion Summary verbatim or near-verbatim, per test_plan.md's own
  Anti-Drift Hazard.
- **Empty-`region_cultures`-is-the-default**: per investigation.md's confirmed answer (no corpus
  world runs Campaign mode), every new test suite in Steps 1-3 must weight the empty/`None`/unknown-
  region case at least as heavily as the populated case — it is the realistic default, not an edge
  case. Steps 1-3's Verify sections above already name the specific tests covering this; do not skip
  them under time pressure.
- **Threshold-constant duplication**: Step 1 explicitly imports `CULTURE_ACTIVATION_THRESHOLD` from
  `src.domains.culture.applicator` rather than redefining `0.3` locally — if the implementer finds
  themselves typing a new float literal `0.3` anywhere in `settlement_personality.py`, that is a sign
  the import was dropped; fix by importing, not by re-deriving the value.
- **`AdventureRouteScorer`/`_ADVENTURE_ROUTE_SCORE_MAX` guard**: no step in this plan touches
  `src/domains/adventure/scoring.py` or `src/systems/strategic_systems/intelligence.py`. If a later
  reviewer or a future ticket reconsiders wiring culture into route scoring, re-read investigation.md's
  "Alternative considered and not recommended" section first — the STRAT-186 shared-normalization risk
  is real and specific, not a generic caution.
- **Atlas edit precision**: the stale string "zero callers anywhere" appears twice in
  `rpg_feature_atlas.html` (idea 61 at line ~2685, and an unrelated `WOUND_THRESHOLD_RATIO` card at
  line ~2137) — Step 5 must only change the idea-61 occurrence; a naive global find/replace would
  corrupt the unrelated card.
- **Do not let Step 6's new ticket balloon in scope while filing it** — it should describe the
  Region/Place-carry fix only (per its own Out of Scope bullet, drafted in Step 6 above), not attempt
  to also solve the second `region_cultures`-into-`AuthoritativeState` plumbing gap investigation.md
  separately flagged.
