import pytest
from pydantic import ValidationError
from src.observability.sweeper import ScenarioSweepConfig
from src.observability.config import ObservabilityMode


def test_valid_sweep_config():
    config = ScenarioSweepConfig(
        scenario_name="idle",
        scenario_type="mixed_sandbox",
        seeds=[1, 2, 3],
        ticks=100,
        observability_mode=ObservabilityMode.LIGHT
    )
    assert config.scenario_name == "idle"
    assert config.seeds == [1, 2, 3]
    assert config.ticks == 100
    assert config.observability_mode == ObservabilityMode.LIGHT
    assert config.profile_name == "cli_default"
    assert config.max_parallel_runs == 1
    assert config.stop_on_first_critical is False


def test_empty_seeds_rejected():
    with pytest.raises(ValidationError) as excinfo:
        ScenarioSweepConfig(
            scenario_name="idle",
            scenario_type="mixed_sandbox",
            seeds=[],
            ticks=100,
            observability_mode=ObservabilityMode.LIGHT
        )
    assert "seeds list cannot be empty" in str(excinfo.value)


def test_non_positive_ticks_rejected():
    with pytest.raises(ValidationError) as excinfo:
        ScenarioSweepConfig(
            scenario_name="idle",
            scenario_type="mixed_sandbox",
            seeds=[42],
            ticks=0,
            observability_mode=ObservabilityMode.LIGHT
        )
    assert "ticks must be positive" in str(excinfo.value)

    with pytest.raises(ValidationError):
        ScenarioSweepConfig(
            scenario_name="idle",
            scenario_type="mixed_sandbox",
            seeds=[42],
            ticks=-10,
            observability_mode=ObservabilityMode.LIGHT
        )


def test_invalid_max_parallel_rejected():
    with pytest.raises(ValidationError):
        ScenarioSweepConfig(
            scenario_name="idle",
            scenario_type="mixed_sandbox",
            seeds=[42],
            ticks=10,
            observability_mode=ObservabilityMode.LIGHT,
            max_parallel_runs=0
        )
