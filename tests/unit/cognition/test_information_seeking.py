"""
tests/unit/cognition/test_information_seeking.py

TCK-20260619-E42A-INFO-NEED — Unit tests for InformationNeedDetector.

Verifies:
  - High-priority UnknownFact (>0.5) with no seeking_project_id generates an
    INFORMATION_SEEKING project via StrategicUpdate.
  - Below-threshold or already-linked unknowns are ignored.
  - Highest-priority candidate wins when multiple unknowns compete.
  - ProjectKind.INFORMATION_SEEKING is importable and used correctly.
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.self_model import (
    KnowledgeModelComponent,
    SelfModelBundle,
    UnknownFact,
)
from src.core.strategic import ProjectKind
from src.engine.domain.cognition_extras import InformationNeedDetector


# ─── helpers ──────────────────────────────────────────────────────────────────

def _entity(unknowns: dict | None = None):
    """Build a minimal EntityState with the given unknowns dict."""
    b = V2EntityBuilder(1)
    km = KnowledgeModelComponent(unknowns=unknowns or {})
    bundle = SelfModelBundle(knowledge=km)
    b.replace_self_model(bundle)
    return b.build()


def _unknown(subject: str, priority: float, seeking_project_id: str | None = None) -> UnknownFact:
    return UnknownFact(
        subject=subject,
        reason="never_queried",
        recorded_tick=0,
        priority=priority,
        seeking_project_id=seeking_project_id,
    )


# ─── normal flow ──────────────────────────────────────────────────────────────

class TestInformationNeedDetectorNormalFlow:
    def test_unknown_fact_generates_seeking_project(self):
        """Acceptance criterion: high-priority unknown generates INFORMATION_SEEKING project."""
        entity = _entity({"moon_resin.source": _unknown("moon_resin.source", priority=0.6)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=10)

        assert result is not None
        assert len(result.projects_add_or_update) == 1
        proj = result.projects_add_or_update[0]
        assert proj.kind == ProjectKind.INFORMATION_SEEKING
        assert "moon_resin.source" in proj.id

    def test_low_priority_unknown_does_not_generate_project(self):
        """priority=0.3 is below threshold — no project created."""
        entity = _entity({"iron_ore.source": _unknown("iron_ore.source", priority=0.3)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=10)
        assert result is None

    def test_already_linked_unknown_does_not_generate_duplicate(self):
        """UnknownFact already has a seeking_project_id — must be skipped."""
        entity = _entity({
            "moon_resin.source": _unknown(
                "moon_resin.source", priority=0.8, seeking_project_id="existing_proj_42"
            )
        })
        result = InformationNeedDetector.detect_and_generate(entity, tick=10)
        assert result is None


# ─── edge cases ───────────────────────────────────────────────────────────────

class TestInformationNeedDetectorEdgeCases:
    def test_no_unknowns_returns_none(self):
        """Empty unknowns dict — nothing to seek."""
        entity = _entity({})
        result = InformationNeedDetector.detect_and_generate(entity, tick=1)
        assert result is None

    def test_highest_priority_unknown_chosen_when_multiple(self):
        """With two candidates the highest-priority one wins."""
        entity = _entity({
            "subject_low": _unknown("subject_low", priority=0.6),
            "subject_high": _unknown("subject_high", priority=0.9),
        })
        result = InformationNeedDetector.detect_and_generate(entity, tick=5)
        assert result is not None
        proj = result.projects_add_or_update[0]
        assert "subject_high" in proj.id

    def test_exactly_at_threshold_does_not_trigger(self):
        """priority == 0.5 is not strictly greater than threshold — no project."""
        entity = _entity({"exact.threshold": _unknown("exact.threshold", priority=0.5)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=1)
        assert result is None

    def test_project_kind_is_information_seeking(self):
        """Returned project must use the INFORMATION_SEEKING project kind."""
        entity = _entity({"some.subject": _unknown("some.subject", priority=0.7)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=1)
        assert result is not None
        assert result.projects_add_or_update[0].kind == ProjectKind.INFORMATION_SEEKING

    def test_objective_kind_is_ask_information(self):
        """Project must carry an ASK_INFORMATION objective targeting the unknown subject."""
        from src.core.strategic import ObjectiveKind
        entity = _entity({"quest.location": _unknown("quest.location", priority=0.75)})
        result = InformationNeedDetector.detect_and_generate(entity, tick=20)
        assert result is not None
        proj = result.projects_add_or_update[0]
        assert len(proj.objectives) == 1
        obj = proj.objectives[0]
        assert obj.kind == ObjectiveKind.ASK_INFORMATION
        assert obj.target == "quest.location"


# ─── model field tests ────────────────────────────────────────────────────────

class TestUnknownFactExtendedFields:
    def test_unknown_fact_default_priority_is_zero(self):
        """Backward compatibility: existing constructors work; priority defaults to 0.0."""
        uf = UnknownFact(subject="x", reason="never_queried", recorded_tick=0)
        assert uf.priority == 0.0
        assert uf.seeking_project_id is None

    def test_unknown_fact_priority_field_set(self):
        uf = UnknownFact(subject="x", reason="r", priority=0.8)
        assert uf.priority == 0.8

    def test_unknown_fact_seeking_project_id_field_set(self):
        uf = UnknownFact(subject="x", reason="r", seeking_project_id="proj_abc")
        assert uf.seeking_project_id == "proj_abc"

    def test_project_kind_information_seeking_importable(self):
        """Acceptance criterion: ProjectKind.INFORMATION_SEEKING is importable."""
        assert ProjectKind.INFORMATION_SEEKING.value == "information_seeking"


# ─── E42B: InformationProviderState tests ─────────────────────────────────────

class TestInformationProviderState:
    """
    Acceptance criteria for TCK-20260619-E42B-INFO-PROVIDER.

    Verifies that InformationProviderState is correctly modelled, importable,
    and that AuthoritativeState registers information_providers deterministically.
    """

    def test_information_provider_registered_in_authoritative_state(self):
        """
        Acceptance criterion: AuthoritativeState carries information_providers
        and accepts InformationProviderState values keyed by entity_id.
        """
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        from src.core.state import AuthoritativeState

        provider = InformationProviderState(
            entity_id=42,
            archetype=InformationProviderArchetype.MERCHANT,
            reliability_score=0.9,
            knowledge_domains=("material_source", "recipe_definition"),
            knowledge_age=3,
        )

        # Construct minimal AuthoritativeState and register the provider.
        state = AuthoritativeState(tick=1, seed=0)
        assert hasattr(state, "information_providers"), (
            "AuthoritativeState must have information_providers field"
        )
        assert state.information_providers == {}, (
            "Default information_providers must be empty"
        )

        # Simulate registration (as would happen via authoritative apply path).
        from dataclasses import replace
        updated_state = replace(
            state,
            information_providers={42: provider},
        )
        assert updated_state.information_providers[42] is provider

    def test_information_provider_state_defaults(self):
        """reliability_score=1.0, knowledge_domains=(), knowledge_age=0 by default."""
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        provider = InformationProviderState(
            entity_id=1,
            archetype=InformationProviderArchetype.ELDER,
        )
        assert provider.reliability_score == 1.0
        assert provider.knowledge_domains == ()
        assert provider.knowledge_age == 0

    def test_information_provider_archetype_values(self):
        """Archetype enum values match the spec."""
        from src.domains.information.providers import InformationProviderArchetype
        assert InformationProviderArchetype.MERCHANT.value == "MERCHANT"
        assert InformationProviderArchetype.GUILD_MASTER.value == "GUILD_MASTER"
        assert InformationProviderArchetype.ELDER.value == "ELDER"

    def test_information_provider_to_canonical_dict(self):
        """to_canonical_dict() produces the correct deterministic structure."""
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        provider = InformationProviderState(
            entity_id=7,
            archetype=InformationProviderArchetype.GUILD_MASTER,
            reliability_score=0.75,
            knowledge_domains=("danger_rating", "material_source"),
            knowledge_age=10,
        )
        result = provider.to_canonical_dict()
        assert result == {
            "entity_id": 7,
            "archetype": "GUILD_MASTER",
            "reliability_score": 0.75,
            "knowledge_domains": ["danger_rating", "material_source"],
            "knowledge_age": 10,
        }

    def test_information_providers_serializes_deterministically(self):
        """Two states with same providers yield identical serializations."""
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        provider_a = InformationProviderState(
            entity_id=1, archetype=InformationProviderArchetype.MERCHANT
        )
        provider_b = InformationProviderState(
            entity_id=2, archetype=InformationProviderArchetype.ELDER
        )
        providers = {1: provider_a, 2: provider_b}
        serialized = {
            eid: p.to_canonical_dict()
            for eid, p in sorted(providers.items())
        }
        # Same construction twice must be identical.
        serialized2 = {
            eid: p.to_canonical_dict()
            for eid, p in sorted(providers.items())
        }
        assert serialized == serialized2

    def test_information_provider_state_is_frozen(self):
        """InformationProviderState is immutable — setting fields raises FrozenInstanceError."""
        import dataclasses
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        provider = InformationProviderState(
            entity_id=3,
            archetype=InformationProviderArchetype.MERCHANT,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            provider.reliability_score = 0.5  # type: ignore[misc]


# ─── E42C: PaidInformationTransaction tests ───────────────────────────────────

class TestPaidInformationTransaction:
    """
    Acceptance criteria for TCK-20260619-E42C-PAID-TRANSACTION.

    Verifies that PaidInformationTransactionSystem:
      - Emits ResourceTransferIntent(source_kind="INFORMATION_PURCHASE") for
        seekers adjacent to a registered InformationProvider.
      - Computes gold_cost correctly from reliability_score.
      - Derives LeadCertainty from reliability tier.
      - Places the LeadState and project removal in strategic_upd (contingent).
      - Skips entities with no INFORMATION_SEEKING project.
      - Skips when no provider is registered.
      - Skips self-provision.
    """

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_seeker(entity_id: int, gold: int = 50, subject: str = "moon_resin.source"):
        """Build an EntityState with an active INFORMATION_SEEKING project."""
        from src.core.strategic import (
            ObjectiveKind, ObjectiveState, ObjectiveStatus,
            ProjectKind, ProjectStatus, ProjectState,
        )
        obj_id = f"ask_{subject}_10"
        proj_id = f"info_seek_{subject}_10"
        objective = ObjectiveState(
            id=obj_id,
            kind=ObjectiveKind.ASK_INFORMATION,
            target=subject,
            status=ObjectiveStatus.ACTIVE,
        )
        project = ProjectState(
            id=proj_id,
            kind=ProjectKind.INFORMATION_SEEKING,
            status=ProjectStatus.ACTIVE,
            objectives=[objective],
            active_objective_id=obj_id,
            created_tick=10,
        )
        b = V2EntityBuilder(entity_id)
        b.inventory(gold=gold)
        b.strategic(projects={proj_id: project})
        return b.build()

    @staticmethod
    def _make_provider(entity_id: int, reliability: float = 0.9):
        """Build an InformationProviderState."""
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        return InformationProviderState(
            entity_id=entity_id,
            archetype=InformationProviderArchetype.MERCHANT,
            reliability_score=reliability,
        )

    @staticmethod
    def _make_state(entities: dict, providers: dict):
        """Build a minimal AuthoritativeState with given entities and providers."""
        from src.core.state import AuthoritativeState
        from dataclasses import replace
        state = AuthoritativeState(tick=10, seed=0)
        state = replace(state, entities=entities, information_providers=providers)
        return state

    # ── normal flow ───────────────────────────────────────────────────────────

    def test_paid_transaction_transfers_gold_and_lead(self):
        """
        Acceptance criterion: seeker with INFORMATION_SEEKING project + provider
        with reliability=0.9 → ResourceTransferIntent with INFORMATION_PURCHASE
        source_kind and a PRECISE LeadState in strategic_upd.
        """
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.strategic import LeadCertainty
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=50)
        provider = self._make_provider(entity_id=2, reliability=0.9)
        state = self._make_state(
            entities={1: seeker},
            providers={2: provider},
        )
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        assert 1 in update.entity_updates
        ent_upd = update.entity_updates[1]
        assert len(ent_upd.resource_transfers) == 1

        intent = ent_upd.resource_transfers[0]
        assert intent.source_kind == "INFORMATION_PURCHASE"
        assert intent.gold_cost > 0
        assert intent.strategic_upd is not None
        assert len(intent.strategic_upd.leads_add_or_update) == 1

        lead = intent.strategic_upd.leads_add_or_update[0]
        assert lead.certainty == LeadCertainty.PRECISE
        assert "moon_resin.source" in lead.subject

        # project removal is included
        assert len(intent.strategic_upd.projects_remove) == 1

    def test_vague_lead_for_low_reliability(self):
        """Provider reliability=0.4 → VAGUE lead."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.strategic import LeadCertainty
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=200)
        provider = self._make_provider(entity_id=2, reliability=0.4)
        state = self._make_state(entities={1: seeker}, providers={2: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        intent = update.entity_updates[1].resource_transfers[0]
        lead = intent.strategic_upd.leads_add_or_update[0]
        assert lead.certainty == LeadCertainty.VAGUE

    def test_approximate_lead_for_mid_reliability(self):
        """Provider reliability=0.65 → APPROXIMATE lead."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.strategic import LeadCertainty
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=50)
        provider = self._make_provider(entity_id=2, reliability=0.65)
        state = self._make_state(entities={1: seeker}, providers={2: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        intent = update.entity_updates[1].resource_transfers[0]
        lead = intent.strategic_upd.leads_add_or_update[0]
        assert lead.certainty == LeadCertainty.APPROXIMATE

    def test_transaction_cost_formula_high_reliability(self):
        """reliability=1.0 → cost=10 (10 / 1.0 = 10)."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=50)
        provider = self._make_provider(entity_id=2, reliability=1.0)
        state = self._make_state(entities={1: seeker}, providers={2: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        intent = update.entity_updates[1].resource_transfers[0]
        assert intent.gold_cost == 10

    def test_transaction_cost_formula_low_reliability(self):
        """reliability=0.1 → cost=100 (10 / 0.1 = 100)."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=200)
        provider = self._make_provider(entity_id=2, reliability=0.1)
        state = self._make_state(entities={1: seeker}, providers={2: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        intent = update.entity_updates[1].resource_transfers[0]
        assert intent.gold_cost == 100

    def test_lead_subject_matches_project_objective(self):
        """LeadState.subject matches the ASK_INFORMATION objective target."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=50, subject="quest.cave_location")
        provider = self._make_provider(entity_id=2, reliability=0.9)
        state = self._make_state(entities={1: seeker}, providers={2: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        intent = update.entity_updates[1].resource_transfers[0]
        lead = intent.strategic_upd.leads_add_or_update[0]
        assert lead.subject == "quest.cave_location"

    # ── edge cases ────────────────────────────────────────────────────────────

    def test_no_provider_no_intent(self):
        """No provider registered → no intent emitted."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=1, gold=50)
        state = self._make_state(entities={1: seeker}, providers={})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        assert 1 not in update.entity_updates or not update.entity_updates[1].resource_transfers

    def test_no_seeking_project_no_intent(self):
        """Entity with no INFORMATION_SEEKING project → no intent emitted."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        b = V2EntityBuilder(1)
        b.inventory(gold=50)
        entity = b.build()
        provider = self._make_provider(entity_id=2, reliability=0.9)
        state = self._make_state(entities={1: entity}, providers={2: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        assert 1 not in update.entity_updates or not update.entity_updates[1].resource_transfers

    def test_seeker_is_own_provider_skipped(self):
        """Provider entity_id == seeker entity_id → no self-transaction."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        seeker = self._make_seeker(entity_id=5, gold=50)
        provider = self._make_provider(entity_id=5, reliability=0.9)
        state = self._make_state(entities={5: seeker}, providers={5: provider})
        update = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        assert 5 not in update.entity_updates or not update.entity_updates[5].resource_transfers

    # ── performance / determinism (TCK-20260822-PAID-INFO-INDEX-RETROFIT) ──────

    @staticmethod
    def _count_provider_sorts(state, providers: dict) -> int:
        """Run enforce() once and count calls to sorted() over exactly the
        provider-id key set, isolating the provider sort from the unrelated,
        unconditional entity-scan sort at paid_information.py's seeker loop."""
        import builtins
        from unittest.mock import patch
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        real_sorted = builtins.sorted
        provider_key_set = set(providers.keys())
        calls = []

        def _spy(iterable, *args, **kwargs):
            items = list(iterable)
            try:
                matches_providers = set(items) == provider_key_set
            except TypeError:
                matches_providers = False
            if matches_providers:
                calls.append(items)
            return real_sorted(items, *args, **kwargs)

        with patch("builtins.sorted", side_effect=_spy):
            PaidInformationTransactionSystem.enforce(state, StateUpdate())

        return len(calls)

    def test_sorted_providers_computed_once_per_enforce_call(self):
        """AC #2: sorted(providers.keys())-equivalent work runs at most once
        per enforce() call, not once per seeker."""
        seekers = {
            i: self._make_seeker(entity_id=i, gold=50)
            for i in (1, 2, 3)
        }
        providers = {
            10: self._make_provider(entity_id=10, reliability=0.9),
            11: self._make_provider(entity_id=11, reliability=0.5),
        }
        state = self._make_state(entities=seekers, providers=providers)

        assert self._count_provider_sorts(state, providers) == 1

    def test_paid_information_enforce_scales_with_providers_not_seekers_times_providers(self):
        """AC #2: the provider sort count does not grow with seeker count."""
        providers = {
            10: self._make_provider(entity_id=10, reliability=0.9),
            11: self._make_provider(entity_id=11, reliability=0.5),
        }

        seekers_small = {1: self._make_seeker(entity_id=1, gold=50)}
        state_small = self._make_state(entities=seekers_small, providers=providers)

        seekers_large = {
            i: self._make_seeker(entity_id=i, gold=50)
            for i in range(1, 6)
        }
        state_large = self._make_state(entities=seekers_large, providers=providers)

        assert self._count_provider_sorts(state_small, providers) == 1
        assert self._count_provider_sorts(state_large, providers) == 1

    def test_enforce_is_deterministic_across_repeated_calls(self):
        """AC #3: two enforce() calls on byte-identical state produce
        byte-identical StateUpdate.entity_updates."""
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        from src.core.updates import StateUpdate

        seekers = {
            1: self._make_seeker(entity_id=1, gold=50, subject="moon_resin.source"),
            2: self._make_seeker(entity_id=2, gold=200, subject="quest.cave_location"),
        }
        providers = {
            10: self._make_provider(entity_id=10, reliability=0.9),
            11: self._make_provider(entity_id=11, reliability=0.4),
        }
        state = self._make_state(entities=seekers, providers=providers)

        update_a = PaidInformationTransactionSystem.enforce(state, StateUpdate())
        update_b = PaidInformationTransactionSystem.enforce(state, StateUpdate())

        assert update_a.entity_updates == update_b.entity_updates


# ─── E42D: LeadContradictionSystem + effective_certainty tests ────────────────

class TestLeadContradiction:
    """
    Acceptance criteria for TCK-20260619-E42D-CONTRADICTION.

    Verifies:
      - belief_contradiction event fires when a lead's resource node is depleted.
      - LeadState is marked FAILURE with incremented failure_count.
      - Provider reliability decrements by 0.1 in information_providers_update.
      - An UnknownFact (priority=0.7) is regenerated for replanning.
      - No contradiction when node has remaining charges.
      - Floor: provider reliability never drops below 0.1.
    """

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_entity_with_lead(
        entity_id: int,
        lead_id: str = "lead_resin",
        subject: str = "moon_resin",
        lead_kind: str = "location",
        certainty=None,
        provider_id: int = 99,
    ):
        """Build entity with a single non-exhausted lead."""
        from src.core.strategic import LeadCertainty, LeadState, StrategicComponent
        from src.core.builder import V2EntityBuilder

        if certainty is None:
            certainty = LeadCertainty.APPROXIMATE

        lead = LeadState(
            id=lead_id,
            kind=lead_kind,
            subject=subject,
            detail="north_ruin",
            certainty=certainty,
            source_entity_id=provider_id,
            discovered_tick=0,
        )
        sc = StrategicComponent(leads={lead_id: lead})
        b = V2EntityBuilder(entity_id)
        b.replace_strategic(sc)
        return b.build()

    @staticmethod
    def _make_resource_node(node_id: int, yields_item: str, remaining_charges: int):
        """Build a minimal ResourceNodeState."""
        from src.core.state import ResourceNodeState
        return ResourceNodeState(
            id=node_id,
            kind="herb",
            position=(10.0, 10.0),
            yields_item=yields_item,
            remaining_charges=remaining_charges,
            max_charges=5,
            required_ticks=1,
        )

    @staticmethod
    def _make_provider(entity_id: int, reliability: float = 0.8):
        from src.domains.information.providers import (
            InformationProviderArchetype,
            InformationProviderState,
        )
        return InformationProviderState(
            entity_id=entity_id,
            archetype=InformationProviderArchetype.MERCHANT,
            reliability_score=reliability,
        )

    @staticmethod
    def _make_state(entities: dict, resource_nodes: dict = None, providers: dict = None):
        from src.core.state import AuthoritativeState
        from dataclasses import replace as dc_replace
        state = AuthoritativeState(tick=10, seed=0)
        kwargs: dict = {"entities": entities}
        if resource_nodes is not None:
            kwargs["resource_nodes"] = resource_nodes
        if providers is not None:
            kwargs["information_providers"] = providers
        return dc_replace(state, **kwargs)

    # ── acceptance tests ──────────────────────────────────────────────────────

    def test_belief_contradiction_fires_on_depleted_lead(self):
        """
        Acceptance criterion: entity with a location lead for 'moon_resin'
        pointing to a depleted resource node (remaining_charges=0) → a
        belief_contradiction SimulationEvent is returned and the LeadState
        is marked FAILURE / EXHAUSTED.
        """
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate
        from src.core.strategic import LeadCertainty

        entity = self._make_entity_with_lead(
            entity_id=1,
            subject="moon_resin",
            lead_kind="location",
            provider_id=99,
        )
        depleted_node = self._make_resource_node(
            node_id=10, yields_item="moon_resin", remaining_charges=0
        )
        provider = self._make_provider(entity_id=99, reliability=0.8)
        state = self._make_state(
            entities={1: entity},
            resource_nodes={10: depleted_node},
            providers={99: provider},
        )

        updated_state_update, events = LeadContradictionSystem.enforce(state, StateUpdate())

        # Two events emitted: belief_contradiction + lead_contradiction_resolved
        assert len(events) == 2
        evt = events[0]
        assert evt.event_type == "belief_contradiction"
        assert evt.entity_id == 1
        assert evt.payload["lead_id"] == "lead_resin"
        assert evt.payload["subject"] == "moon_resin"

        # Lead is marked FAILURE / EXHAUSTED
        assert 1 in updated_state_update.entity_updates
        ent_upd = updated_state_update.entity_updates[1]
        assert ent_upd.strategic is not None
        leads_upd = ent_upd.strategic.leads_add_or_update
        assert len(leads_upd) == 1
        updated_lead = leads_upd[0]
        assert updated_lead.test_outcome == "FAILURE"
        assert updated_lead.certainty == LeadCertainty.EXHAUSTED
        assert updated_lead.failure_count == 1
        assert updated_lead.tested is True

    def test_contradiction_updates_provider_reliability(self):
        """Provider reliability decrements by 0.1 in information_providers_update."""
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate

        entity = self._make_entity_with_lead(entity_id=1, subject="moon_resin", provider_id=99)
        depleted_node = self._make_resource_node(10, "moon_resin", 0)
        provider = self._make_provider(entity_id=99, reliability=0.8)
        state = self._make_state(
            entities={1: entity},
            resource_nodes={10: depleted_node},
            providers={99: provider},
        )

        updated, _ = LeadContradictionSystem.enforce(state, StateUpdate())

        assert 99 in updated.information_providers_update
        new_provider = updated.information_providers_update[99]
        assert abs(new_provider.reliability_score - 0.7) < 1e-6

    def test_provider_reliability_floor_at_0_1(self):
        """Provider with reliability=0.1 stays at 0.1 after contradiction."""
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate

        entity = self._make_entity_with_lead(entity_id=1, subject="moon_resin", provider_id=99)
        depleted_node = self._make_resource_node(10, "moon_resin", 0)
        provider = self._make_provider(entity_id=99, reliability=0.1)
        state = self._make_state(
            entities={1: entity},
            resource_nodes={10: depleted_node},
            providers={99: provider},
        )

        updated, events = LeadContradictionSystem.enforce(state, StateUpdate())

        assert len(events) == 2  # belief_contradiction + lead_contradiction_resolved
        new_provider = updated.information_providers_update[99]
        assert new_provider.reliability_score >= 0.1

    def test_contradiction_regenerates_unknown_fact(self):
        """An UnknownFact(priority=0.7) is placed on the entity's knowledge for replanning."""
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate

        entity = self._make_entity_with_lead(entity_id=1, subject="moon_resin", provider_id=99)
        depleted_node = self._make_resource_node(10, "moon_resin", 0)
        provider = self._make_provider(entity_id=99, reliability=0.8)
        state = self._make_state(
            entities={1: entity},
            resource_nodes={10: depleted_node},
            providers={99: provider},
        )

        updated, _ = LeadContradictionSystem.enforce(state, StateUpdate())

        ent_upd = updated.entity_updates[1]
        assert ent_upd.self_model_bundle_set is not None
        unknowns = ent_upd.self_model_bundle_set.knowledge.unknowns
        assert "moon_resin" in unknowns
        uf = unknowns["moon_resin"]
        assert uf.priority == 0.7
        assert uf.reason == "lead_contradicted"

    def test_alive_lead_no_contradiction(self):
        """Resource node with remaining_charges > 0 → no contradiction, no events."""
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate

        entity = self._make_entity_with_lead(entity_id=1, subject="moon_resin", provider_id=99)
        live_node = self._make_resource_node(10, "moon_resin", remaining_charges=3)
        provider = self._make_provider(entity_id=99, reliability=0.8)
        state = self._make_state(
            entities={1: entity},
            resource_nodes={10: live_node},
            providers={99: provider},
        )

        updated, events = LeadContradictionSystem.enforce(state, StateUpdate())

        assert len(events) == 0
        assert 1 not in updated.entity_updates or updated.entity_updates.get(1) is None or \
            not updated.entity_updates[1].strategic or \
            not updated.entity_updates[1].strategic.leads_add_or_update

    def test_no_leads_no_contradiction(self):
        """Entity with no leads → no updates emitted."""
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate
        from src.core.builder import V2EntityBuilder

        b = V2EntityBuilder(1)
        entity = b.build()
        state = self._make_state(entities={1: entity})

        updated, events = LeadContradictionSystem.enforce(state, StateUpdate())

        assert len(events) == 0
        assert not updated.entity_updates

    def test_already_exhausted_lead_skipped(self):
        """EXHAUSTED leads are not re-contradicted."""
        from src.engine.pipeline_phases.lead_contradiction import LeadContradictionSystem
        from src.core.updates import StateUpdate
        from src.core.strategic import LeadCertainty

        entity = self._make_entity_with_lead(
            entity_id=1,
            subject="moon_resin",
            certainty=LeadCertainty.EXHAUSTED,
            provider_id=99,
        )
        depleted_node = self._make_resource_node(10, "moon_resin", 0)
        state = self._make_state(entities={1: entity}, resource_nodes={10: depleted_node})

        updated, events = LeadContradictionSystem.enforce(state, StateUpdate())

        assert len(events) == 0


# ─── E42D: KnowledgeFact staleness decay tests ────────────────────────────────

class TestKnowledgeStalenessDecay:
    """
    Tests for effective_certainty() in src/cognition/knowledge_model.py.

    Verifies staleness decay formula:
        effective = certainty * max(0.1, 1.0 - elapsed * 0.0001)
    """

    def test_lead_staleness_decay_reduces_confidence(self):
        """
        Acceptance criterion: effective_certainty < 0.5 at tick 5001 for
        a KnowledgeFact with certainty=1.0 recorded at tick 0.
        """
        from src.core.self_model import KnowledgeFact
        from src.cognition.knowledge_model import effective_certainty

        fact = KnowledgeFact(
            subject="moon_resin",
            fact_type="resource_source",
            certainty=1.0,
            recorded_tick=0,
        )
        result = effective_certainty(fact, current_tick=5001)
        assert result < 0.5, f"expected < 0.5, got {result}"

    def test_staleness_decay_at_tick_zero_delta(self):
        """current_tick == recorded_tick → effective_certainty == certainty (no decay)."""
        from src.core.self_model import KnowledgeFact
        from src.cognition.knowledge_model import effective_certainty

        fact = KnowledgeFact(
            subject="iron", fact_type="resource_source", certainty=0.8, recorded_tick=100
        )
        result = effective_certainty(fact, current_tick=100)
        assert abs(result - 0.8) < 1e-9

    def test_staleness_decay_minimum_0_1(self):
        """At very large tick delta the floor is certainty * 0.1."""
        from src.core.self_model import KnowledgeFact
        from src.cognition.knowledge_model import effective_certainty

        fact = KnowledgeFact(
            subject="iron", fact_type="resource_source", certainty=1.0, recorded_tick=0
        )
        # At tick=20000 decay_factor would be -1.0 without floor → floored at 0.1
        result = effective_certainty(fact, current_tick=20000)
        assert result >= 0.1 - 1e-9

    def test_staleness_exact_halfway_tick(self):
        """At tick 5000 (elapsed=5000): decay_factor = max(0.1, 0.5) = 0.5 → exactly 0.5."""
        from src.core.self_model import KnowledgeFact
        from src.cognition.knowledge_model import effective_certainty

        fact = KnowledgeFact(
            subject="iron", fact_type="resource_source", certainty=1.0, recorded_tick=0
        )
        result = effective_certainty(fact, current_tick=5000)
        assert abs(result - 0.5) < 1e-9

    def test_staleness_partial_certainty(self):
        """Decay applies to initial certainty, not just 1.0."""
        from src.core.self_model import KnowledgeFact
        from src.cognition.knowledge_model import effective_certainty

        fact = KnowledgeFact(
            subject="x", fact_type="y", certainty=0.6, recorded_tick=0
        )
        # elapsed=2000 → decay_factor = max(0.1, 0.8) = 0.8
        result = effective_certainty(fact, current_tick=2000)
        assert abs(result - 0.48) < 1e-9


# ─── TCK-20260619-E42E: LeadKind enum + PERSON/CONCEPT routing ────────────────


class TestLeadKindEnum:
    """
    TCK-20260619-E42E acceptance criterion:
      test_person_and_concept_lead_types_accepted
    """

    def test_person_and_concept_lead_types_accepted(self):
        """LeadKind.PERSON and LeadKind.CONCEPT can be constructed and compared."""
        from src.core.strategic import LeadKind, LeadState, LeadCertainty

        person_lead = LeadState(
            id="lead_person_42",
            kind=LeadKind.PERSON,
            subject="42",
            detail="",
            certainty=LeadCertainty.VAGUE,
        )
        concept_lead = LeadState(
            id="lead_concept_alchemy",
            kind=LeadKind.CONCEPT,
            subject="alchemy_recipe",
            detail="",
            certainty=LeadCertainty.APPROXIMATE,
        )

        # String-compatibility check (LeadKind is str, Enum)
        assert person_lead.kind == "person"
        assert concept_lead.kind == "concept"

        # Type check
        assert isinstance(person_lead.kind, LeadKind)
        assert isinstance(concept_lead.kind, LeadKind)

        # All five values exist and are unique
        kinds = list(LeadKind)
        assert len(kinds) == 5
        values = {k.value for k in kinds}
        assert values == {"location", "object", "event", "person", "concept"}

    def test_lead_kind_existing_values_unchanged(self):
        """LOCATION, OBJECT, EVENT values are string-equal to their raw strings."""
        from src.core.strategic import LeadKind

        assert LeadKind.LOCATION == "location"
        assert LeadKind.OBJECT == "object"
        assert LeadKind.EVENT == "event"

    def test_lead_state_raw_string_kind_still_accepted(self):
        """LeadState constructed with raw string kind= still works (backward compat)."""
        from src.core.strategic import LeadState, LeadCertainty

        # Raw strings are still accepted because LeadKind(str, Enum) members
        # compare equal to their string values, and pydantic/dataclasses allow
        # passing compatible str values.  This guards against regression.
        lead = LeadState(
            id="legacy_lead",
            kind="location",  # type: ignore[arg-type]  # legacy callsite
            subject="iron_ore",
            certainty=LeadCertainty.VAGUE,
        )
        assert lead.kind == "location"
        assert lead.kind == LeadKind.LOCATION if hasattr(lead.kind, 'value') else lead.kind == "location"


class TestLeadRoutingSystem:
    """
    TCK-20260619-E42E acceptance criterion:
      test_person_lead_routes_entity_to_provider
    """

    def test_person_lead_routes_entity_to_provider(self):
        """PERSON lead resolves to INVESTIGATE objective targeting the entity_id."""
        from src.core.strategic import LeadKind, LeadState, LeadCertainty, ObjectiveKind
        from src.engine.domain.lead_routing import LeadRoutingSystem

        lead = LeadState(
            id="lead_person_42",
            kind=LeadKind.PERSON,
            subject="42",
            detail="",
            certainty=LeadCertainty.VAGUE,
        )
        obj_kind, target = LeadRoutingSystem.resolve_objective_kind(lead)

        assert obj_kind == ObjectiveKind.INVESTIGATE
        assert target == "42"

    def test_concept_lead_routes_to_information_provider(self):
        """CONCEPT lead resolves to ASK_INFORMATION objective with the concept as target."""
        from src.core.strategic import LeadKind, LeadState, LeadCertainty, ObjectiveKind
        from src.engine.domain.lead_routing import LeadRoutingSystem

        lead = LeadState(
            id="lead_concept_alchemy",
            kind=LeadKind.CONCEPT,
            subject="alchemy_recipe",
            certainty=LeadCertainty.APPROXIMATE,
        )
        obj_kind, target = LeadRoutingSystem.resolve_objective_kind(lead)

        assert obj_kind == ObjectiveKind.ASK_INFORMATION
        assert target == "alchemy_recipe"

    def test_location_lead_routing_unchanged(self):
        """LOCATION lead resolves to REACH_LOCATION, using detail when present."""
        from src.core.strategic import LeadKind, LeadState, LeadCertainty, ObjectiveKind
        from src.engine.domain.lead_routing import LeadRoutingSystem

        lead_with_detail = LeadState(
            id="lead_loc",
            kind=LeadKind.LOCATION,
            subject="iron_ore",
            detail="north_mine",
            certainty=LeadCertainty.PRECISE,
        )
        obj_kind, target = LeadRoutingSystem.resolve_objective_kind(lead_with_detail)
        assert obj_kind == ObjectiveKind.REACH_LOCATION
        assert target == "north_mine"

        lead_no_detail = LeadState(
            id="lead_loc2",
            kind=LeadKind.LOCATION,
            subject="iron_ore",
            detail="",
            certainty=LeadCertainty.VAGUE,
        )
        obj_kind2, target2 = LeadRoutingSystem.resolve_objective_kind(lead_no_detail)
        assert obj_kind2 == ObjectiveKind.REACH_LOCATION
        assert target2 == "iron_ore"

    def test_object_and_event_leads_route_to_investigate(self):
        """OBJECT and EVENT leads fall through to INVESTIGATE."""
        from src.core.strategic import LeadKind, LeadState, LeadCertainty, ObjectiveKind
        from src.engine.domain.lead_routing import LeadRoutingSystem

        for kind in (LeadKind.OBJECT, LeadKind.EVENT):
            lead = LeadState(
                id=f"lead_{kind.value}",
                kind=kind,
                subject="mystery_artifact",
                certainty=LeadCertainty.VAGUE,
            )
            obj_kind, target = LeadRoutingSystem.resolve_objective_kind(lead)
            assert obj_kind == ObjectiveKind.INVESTIGATE
            assert target == "mystery_artifact"

    def test_detour_system_wires_person_lead_objective(self):
        """DetourSuggestionSystem._infer_objective_kind returns 'investigate' for PERSON lead."""
        from src.core.strategic import (
            LeadKind, LeadState, LeadCertainty, BlockerState, BlockerKind
        )
        from src.systems.strategic_systems.detour import DetourSuggestionSystem

        person_lead = LeadState(
            id="lead_person",
            kind=LeadKind.PERSON,
            subject="99",
            certainty=LeadCertainty.VAGUE,
        )
        blocker = BlockerState(
            id="b1", kind=BlockerKind.SOCIAL, subject="ally", severity=0.5
        )
        result = DetourSuggestionSystem._infer_objective_kind(blocker, person_lead)
        assert result == "investigate"

    def test_detour_system_wires_concept_lead_objective(self):
        """DetourSuggestionSystem._infer_objective_kind returns 'ask_information' for CONCEPT lead."""
        from src.core.strategic import (
            LeadKind, LeadState, LeadCertainty, BlockerState, BlockerKind
        )
        from src.systems.strategic_systems.detour import DetourSuggestionSystem

        concept_lead = LeadState(
            id="lead_concept",
            kind=LeadKind.CONCEPT,
            subject="potion_recipe",
            certainty=LeadCertainty.APPROXIMATE,
        )
        blocker = BlockerState(
            id="b1", kind=BlockerKind.CAPABILITY, subject="crafting", severity=0.5
        )
        result = DetourSuggestionSystem._infer_objective_kind(blocker, concept_lead)
        assert result == "ask_information"
