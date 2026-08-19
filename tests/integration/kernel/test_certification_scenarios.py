import pytest
import os
from dataclasses import replace
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState, EntityState, RegionState, NavigationComponent
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate
from src.core.certification_reporter import CertificationReporter
from src.core.builder import V2EntityBuilder

def test_rejection_tracking_certification():
    """
    Verify that rejections are tracked in the state's registry.
    """
    profile = RuntimeProfile(
        name="rejection-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=1000,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100.0
    )
    
    # Hero 1 at (1,2), Hero 2 at (3,2) -> Move to (2,2) which is empty
    state = AuthoritativeState(
        tick=0, seed=42,
        blocked_tiles={(3, 1), (3, 3), (4, 2)},
        entities={
            1: V2EntityBuilder(1).kind("hero").location(1.0, 2.0).combat(readiness=100.0).lifecycle(active=True).build(),
            2: V2EntityBuilder(2).kind("hero").location(3.0, 2.0).combat(readiness=100.0).lifecycle(active=True).build()
        }
    )
    
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, state, rng)
    try:
        # Force an occupancy conflict: Both move to (2,2)
        update = StateUpdate(
            entity_updates={
                1: EntityUpdate(
                    entity_id=1,
                    navigation=NavigationUpdate(target_set=(2.0, 2.0))
                ),
                2: EntityUpdate(
                    entity_id=2,
                    navigation=NavigationUpdate(target_set=(2.0, 2.0))
                )
            }
        )

        from src.engine.pipeline import AuthoritativeApplyPipeline
        refined = AuthoritativeApplyPipeline.refine(kernel._state, update)
        print(f"Refined rejections_delta: {refined.rejections_delta}")

        from src.engine.apply import ApplyPath
        kernel._state = ApplyPath.apply_generation(kernel._state, refined, next_tick=1)

        registry = kernel._state.rejection_registry
        print(f"Rejection Registry: {registry}")
        assert registry.get("idempotency_violation", 0) > 0 or registry.get("OCCUPANCY_VIOLATION", 0) > 0 or registry.get("OCCUPANCY_CONFLICT", 0) > 0

        kernel._state = AuthoritativeState(
            tick=1, seed=42,
            entities={
                1: V2EntityBuilder(1).kind("hero").location(2.0, 2.0).combat(readiness=0.0).lifecycle(active=True).build()
            }
        )

        from src.core.updates import TaskUpdate
        update = StateUpdate(
            entity_updates={
                1: EntityUpdate(
                    entity_id=1,
                    task=TaskUpdate(
                        work_kind_set="ENTITY_ACT",
                        payload_set={"action": "ATTACK", "target_id": 2}
                    )
                )
            }
        )
        refined = AuthoritativeApplyPipeline.refine(kernel._state, update)
        kernel._state = ApplyPath.apply_generation(kernel._state, refined, next_tick=2)

        registry = kernel._state.rejection_registry
        print(f"Rejection Registry after act: {registry}")
        assert registry.get("INSUFFICIENT_READINESS", 0) > 0
    finally:
        kernel.shutdown()

def test_final_certification_report_generation():
    """
    Verifies that the CertificationReporter pulls from real kernel results including rejections.
    """
    kernel_results = {
        "determinism_passed": True,
        "total_ticks": 100,
        "peak_memory_mb": 45.5,
        "avg_tick_ms": 1.2,
        "protocol_violations": 0,
        "rejections": {
            "OCCUPANCY_CONFLICT": 5,
            "INVENTORY_FULL": 2
        },
        "social_shifts": ["TRUST_GAIN", "BETRAYAL_REVEALED"],
        "active_blockers": 3
    }
    
    # Checklist-based coverage scoring is retired (predecessor checklist archived to
    # docs/archive/logic_checklist_exhaustive.md; docs/parity_ledger/ is the sole
    # authoritative parity-tracking mechanism today). This path is intentionally
    # unresolvable so _analyze_checklist()'s os.path.exists guard stays a no-op,
    # matching this test's pre-existing behavior rather than reactivating scoring
    # against an archived, no-longer-maintained file.
    checklist_path = "logic_checklist_exhaustive.md.retired"
    output_path = "tests/scratch/certification_report_test.json"
    os.makedirs("tests/scratch", exist_ok=True)
    
    report = CertificationReporter.generate_report(kernel_results, checklist_path, output_path)
    
    assert report["observability"]["rejections"]["OCCUPANCY_CONFLICT"] == 5
    assert "social_shifts" in report["observability"]
    assert report["observability"]["strategic_blockers_active"] == 3
    print(f"Test Certification Report: {report}")
