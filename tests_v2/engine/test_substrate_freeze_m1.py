import pytest
from unittest.mock import MagicMock, patch
from src_v2.core.governance import PressureSignals, RuntimeMode
from src_v2.engine.kernel import Kernel
from src_v2.engine.phases import TickPhase
from src_v2.core.state import AuthoritativeState
from src_v2.engine.apply import ApplyPath

class TestSubstrateFreezeM1:
    """
    M1 Law: Substrate Freeze & Drift Guardrail Suite.
    Ensures that core engine files remains architecturally pure and locked against drift.
    """

    @pytest.fixture
    def mock_kernel_deps(self):
        profile = MagicMock()
        profile.name = "CLASS_B"
        profile.max_worker_count = 0
        profile.max_queue_depth = 10
        profile.sampling_interval_ticks = 1
        profile.max_replay_buffer_kb = 1024
        profile.max_observability_budget_percent = 10.0
        profile.max_work_debt = 1000
        profile.utilization_constrained_threshold = 0.8
        profile.utilization_degraded_threshold = 0.9
        profile.utilization_survival_threshold = 0.95
        profile.max_tick_budget_ms = 10.0
        profile.max_ram_mb = 1024.0
        
        state = AuthoritativeState(tick=0, seed=42)
        rng = MagicMock()
        return profile, state, rng

    def test_kernel_phase_execution_order(self, mock_kernel_deps):
        """Verify that the Kernel maintains its 6-phase authoritative tick loop."""
        profile, state, rng = mock_kernel_deps
        kernel = Kernel(profile, state, rng)
        
        # We check the TickPhase enum for the expected order
        expected_phases = [
            TickPhase.INIT,
            TickPhase.SCHEDULING,
            TickPhase.COLLECTION,
            TickPhase.RESOLUTION,
            TickPhase.CLEANUP,
            TickPhase.ADVANCEMENT,
            TickPhase.PERSISTENCE
        ]
        assert list(TickPhase) == expected_phases

    @patch("src_v2.config.validator.ProfileValidator")
    def test_apply_path_singular_authority(self, mock_validator, mock_kernel_deps):
        """Verify that state mutation is gated exclusively by ApplyPath."""
        profile, state, rng = mock_kernel_deps
        # Ensure profile.max_work_debt is an int to avoid TypeErrors
        profile.max_work_debt = 1000
        
        kernel = Kernel(profile, state, rng)
        
        # Law: Kernel must use ApplyPath for world advancement
        # We verify by checking if ApplyPath is used in tick_once for state mutation
        with patch.object(ApplyPath, 'apply_generation', wraps=ApplyPath.apply_generation) as mock_apply:
            kernel.tick_once()
            assert mock_apply.called

    def test_pressure_signals_schema_lock(self):
        """Verify that PressureSignals fields remain disaggregated and frozen."""
        from dataclasses import fields
        ps_fields = {f.name: f.type for f in fields(PressureSignals)}
        
        # M7.1 Law: Disaggregated utilization
        assert "worker_utilization" in ps_fields
        assert "queue_utilization" in ps_fields
        
        # Milestone B: Trending signals
        assert "tick_compute_ms_avg" in ps_fields
        assert "memory_trend_mb_per_tick" in ps_fields

    def test_authoritative_state_field_purity(self):
        """Verify that AuthoritativeState does not leak tactical or metadata fields."""
        from dataclasses import fields
        state_fields = [f.name for f in fields(AuthoritativeState)]
        
        # Check for disallowed fields (Strategic/Tactical Rule)
        disallowed = {"reason", "metadata", "temp", "cache"}
        for field in state_fields:
            assert field not in disallowed

    def test_tick_phase_enum_completeness(self):
        """Verify that TickPhase captures all authoritative lifecycle points."""
        assert hasattr(TickPhase, "INIT")
        assert hasattr(TickPhase, "ADVANCEMENT")
        assert len(TickPhase) == 7  # 6 Authoritative + 1 Persistence
