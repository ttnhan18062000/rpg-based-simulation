import pytest
from src.observability.budget.budget_profile import PRESET_PRODUCTION

def test_production_observability_overhead_limit():
    # Verify production budget limits are well-defined and within safe thresholds
    assert PRESET_PRODUCTION.max_hot_path_overhead_percent <= 3.0
    assert PRESET_PRODUCTION.max_live_publish_ms_per_tick <= 0.5
