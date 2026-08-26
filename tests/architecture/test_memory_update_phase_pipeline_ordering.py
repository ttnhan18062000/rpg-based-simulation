"""
tests/architecture/test_memory_update_phase_pipeline_ordering.py

TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: architecture guard proving MemoryUpdatePhase's call
site in AuthoritativeApplyPipeline.refine() is registered strictly between actor_validity (PP-02)
and self_model (PP-03), the exact insertion point the ticket's acceptance criteria and plan both
name. A source-position check (not a behavioral test) so a future edit that reorders phases fails
loudly here instead of silently drifting the documented insertion point.
"""
import inspect
from src.engine.pipeline import AuthoritativeApplyPipeline


def test_memory_update_phase_registered_between_actor_validity_and_self_model():
    source = inspect.getsource(AuthoritativeApplyPipeline.refine)

    actor_validity_idx = source.index('run_phase("actor_validity"')
    memory_update_idx = source.index('run_phase(\n            "memory_update"')
    self_model_idx = source.index('run_phase("self_model"')

    assert actor_validity_idx < memory_update_idx < self_model_idx
