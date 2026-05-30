# TDD tests for Phase 10 Graceful Degradation
import pytest
from src.domains.optimization.degradation import GracefulDegradationManager, DegradationLevel

def test_budget_pressure_enters_constrained_mode():
    mgr = GracefulDegradationManager()
    # High pressure, e.g. budget consumed is high
    level = mgr.update_pressure(tick_time_ms=22.0, limit_ms=25.0)
    assert level == DegradationLevel.CONSTRAINED

def test_constrained_mode_reduces_provider_results():
    mgr = GracefulDegradationManager()
    mgr.update_pressure(tick_time_ms=22.0, limit_ms=25.0)
    # Under CONSTRAINED, provider cap should be reduced
    assert mgr.get_provider_cap(original_cap=10) == 5

def test_degraded_mode_skips_world_emergence():
    mgr = GracefulDegradationManager()
    mgr.update_pressure(tick_time_ms=24.5, limit_ms=25.0) # > 95%
    assert mgr.should_skip_phase("ENABLE_WORLD_EMERGENCE")

def test_critical_mode_disables_optional_enhanced_phases():
    mgr = GracefulDegradationManager()
    mgr.update_pressure(tick_time_ms=26.0, limit_ms=25.0) # > limit
    assert mgr.get_level() == DegradationLevel.CRITICAL
    # Critical should skip optional ones like ENABLE_LIFE_ARC_CAMPAIGNS
    assert mgr.should_skip_phase("ENABLE_LIFE_ARC_CAMPAIGNS")

def test_degradation_reason_recorded_in_report():
    mgr = GracefulDegradationManager()
    mgr.update_pressure(tick_time_ms=26.0, limit_ms=25.0)
    report = mgr.generate_report()
    assert "Time limit exceeded" in report["reason"]

def test_recovery_from_degraded_to_normal_when_pressure_drops():
    mgr = GracefulDegradationManager()
    mgr.update_pressure(tick_time_ms=26.0, limit_ms=25.0)
    assert mgr.get_level() == DegradationLevel.CRITICAL
    
    # Pressure drops
    level = mgr.update_pressure(tick_time_ms=5.0, limit_ms=25.0)
    assert level == DegradationLevel.NORMAL
