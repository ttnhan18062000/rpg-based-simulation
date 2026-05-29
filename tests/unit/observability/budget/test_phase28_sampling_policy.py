import pytest
from src.observability.budget.budget_profile import SamplingPolicy

def test_sampling_policy_fields():
    # Verify all required sampling policy enums are present
    assert SamplingPolicy.ALWAYS_KEEP_HARD_LAW
    assert SamplingPolicy.ALWAYS_KEEP_FATAL
    assert SamplingPolicy.ALWAYS_KEEP_DEBUG_ENTITIES
    assert SamplingPolicy.ALWAYS_KEEP_RESEARCH_MARKERS
    assert SamplingPolicy.SAMPLE_LOW_SEVERITY
    assert SamplingPolicy.SUMMARIZE_REPEATED
    assert SamplingPolicy.DROP_LOW_PRIORITY
