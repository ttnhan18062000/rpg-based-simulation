"""Idempotency tests for ActionSystem.apply_strategic_update. [TCK-20260415-HARDENING]

Validates that:
1. Applying the same StrategicUpdate twice does NOT over-count metrics.
2. Contract status transitions only fire metrics on actual transitions.
3. Duplicate project additions are upserted, not appended.
"""
import pytest
from unittest.mock import MagicMock, patch
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.enums import StrategicStatus, ProjectKind, ContractKind
from src_legacy.core.models.strategy import StrategicState, ProjectRecord, SocialContractRecord
from src_legacy.actions.base import StrategicUpdate
from src_legacy.systems.gameplay.action_system import ActionSystem


def _make_entity_with_strat() -> Entity:
    """Create a minimal entity with a valid strategic state."""
    entity = MagicMock()
    entity.mind.strategic = StrategicState()
    return entity


class TestProjectIdempotency:
    """Verify that project upserts are idempotent and metrics are transition-guarded."""

    def test_duplicate_project_add_does_not_duplicate(self):
        """Adding the same project twice should upsert, not append."""
        entity = _make_entity_with_strat()
        
        prj = ProjectRecord(
            project_id="prj_1", label="Test Quest", kind=ProjectKind.QUEST,
            status=StrategicStatus.ACTIVE, committed_at=100
        )
        update = StrategicUpdate(projects_add_or_update=[prj])
        
        # Apply twice
        ActionSystem.apply_strategic_update(entity, update)
        ActionSystem.apply_strategic_update(entity, update)
        
        strat = entity.mind.strategic
        assert len(strat.projects) == 1
        assert strat.projects[0].project_id == "prj_1"

    def test_project_status_transition_fires_metric_once(self):
        """Completing a project should fire the metric exactly once, even if applied twice."""
        entity = _make_entity_with_strat()
        
        # Seed an active project
        active_prj = ProjectRecord(
            project_id="prj_metrics", label="Metric Quest", kind=ProjectKind.QUEST,
            status=StrategicStatus.ACTIVE, committed_at=50
        )
        entity.mind.strategic.projects.append(active_prj)
        
        # Prepare the resolved version
        resolved_prj = active_prj.model_copy(update={"status": StrategicStatus.RESOLVED})
        update = StrategicUpdate(projects_add_or_update=[resolved_prj])
        
        with patch("src.utils.metrics.SIM_STRATEGIC_PROJECT_STATUS") as mock_metric:
            # First application: should fire metric (ACTIVE -> RESOLVED)
            ActionSystem.apply_strategic_update(entity, update)
            assert mock_metric.labels.call_count == 1
            
            # Second application: should NOT fire metric (RESOLVED -> RESOLVED, no transition)
            ActionSystem.apply_strategic_update(entity, update)
            assert mock_metric.labels.call_count == 1, \
                "Metric should NOT fire on re-application of same status"


class TestContractIdempotency:
    """Verify that contract upserts are idempotent and breach metrics are transition-guarded."""

    def test_duplicate_contract_add_does_not_duplicate(self):
        """Adding the same contract twice should upsert, not append."""
        entity = _make_entity_with_strat()
        
        ct = SocialContractRecord(
            contract_id="ct_1", kind=ContractKind.EXPEDITION, purpose="Test",
            founder_id=1, member_ids=[1, 2], status=StrategicStatus.ACTIVE
        )
        update = StrategicUpdate(contracts_add_or_update=[ct])
        
        ActionSystem.apply_strategic_update(entity, update)
        ActionSystem.apply_strategic_update(entity, update)
        
        strat = entity.mind.strategic
        assert len(strat.contracts) == 1
        assert strat.contracts[0].contract_id == "ct_1"

    def test_contract_abandonment_fires_breach_metric_once(self):
        """Abandoning a contract should fire breach metric exactly once."""
        entity = _make_entity_with_strat()
        
        # Seed an active contract
        active_ct = SocialContractRecord(
            contract_id="ct_breach", kind=ContractKind.EXPEDITION, purpose="Breach Test",
            founder_id=1, member_ids=[1], status=StrategicStatus.ACTIVE
        )
        entity.mind.strategic.contracts.append(active_ct)
        
        # Prepare the abandoned version
        abandoned_ct = active_ct.model_copy(update={"status": StrategicStatus.ABANDONED})
        update = StrategicUpdate(contracts_add_or_update=[abandoned_ct])
        
        with patch("src.utils.metrics.SIM_STRATEGIC_CONTRACT_BREACHES") as mock_breach:
            # First application: should fire breach metric (ACTIVE -> ABANDONED)
            ActionSystem.apply_strategic_update(entity, update)
            assert mock_breach.labels.call_count == 1
            
            # Second application: should NOT fire (ABANDONED -> ABANDONED, no transition)
            ActionSystem.apply_strategic_update(entity, update)
            assert mock_breach.labels.call_count == 1, \
                "Breach metric should NOT fire on re-application of same abandoned status"

    def test_contract_resolution_does_not_trigger_breach(self):
        """Resolving a contract should NOT fire the breach metric."""
        entity = _make_entity_with_strat()
        
        active_ct = SocialContractRecord(
            contract_id="ct_resolve", kind=ContractKind.EXPEDITION, purpose="Resolve Test",
            founder_id=1, member_ids=[1], status=StrategicStatus.ACTIVE
        )
        entity.mind.strategic.contracts.append(active_ct)
        
        resolved_ct = active_ct.model_copy(update={"status": StrategicStatus.RESOLVED})
        update = StrategicUpdate(contracts_add_or_update=[resolved_ct])
        
        with patch("src.utils.metrics.SIM_STRATEGIC_CONTRACT_BREACHES") as mock_breach:
            ActionSystem.apply_strategic_update(entity, update)
            mock_breach.labels.assert_not_called()


class TestLeadIdempotency:
    """Verify that lead upserts are idempotent."""

    def test_duplicate_lead_upsertion(self):
        """Adding the same lead twice should upsert, not append."""
        from src_legacy.core.models.strategy import LeadRecord
        from src_legacy.core.models.enums import LeadKind
        from src_legacy.core.models.vectors import Vector2
        
        entity = _make_entity_with_strat()
        
        lead = LeadRecord(lead_id="l_1", label="Ancient Map", certainty=0.5, kind=LeadKind.OBJECT, target_coords=Vector2(10, 10))
        update = StrategicUpdate(leads_add_or_update=[lead])
        
        ActionSystem.apply_strategic_update(entity, update)
        ActionSystem.apply_strategic_update(entity, update)
        
        strat = entity.mind.strategic
        assert len(strat.leads) == 1
        assert strat.leads[0].lead_id == "l_1"
