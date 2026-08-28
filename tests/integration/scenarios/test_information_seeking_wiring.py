"""
tests/integration/scenarios/test_information_seeking_wiring.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260824-WIRE-ORPHANED-MECHANISMS Step 1 — verifies InformationNeedDetector
is actually wired into CognitionDomain.execute_brain() and reaches the returned
EntityUpdate via a real Kernel tick, not just a direct execute_brain()/
detect_and_generate() unit call. A unit test alone would not catch the
`strategic=None` hardcode this ticket fixed (AC #1's "verified via a real
Kernel run" requirement).
"""
from __future__ import annotations

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.builder import V2EntityBuilder
from src.core.self_model import KnowledgeModelComponent, SelfModelBundle, UnknownFact
from src.core.state import AuthoritativeState
from src.core.strategic import ProjectKind
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="information_seeking_wiring",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=100,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=100.0,
        max_replay_buffer_kb=100,
        max_observability_budget_percent=0.0,
    )


def _entity_with_unknown(entity_id: int = 1):
    builder = (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .strategic(current_project_id="unrelated_project")
    )
    knowledge = KnowledgeModelComponent(
        unknowns={
            "moon_resin.source": UnknownFact(
                subject="moon_resin.source",
                reason="never_queried",
                recorded_tick=0,
                priority=0.9,
                seeking_project_id=None,
            )
        }
    )
    builder.replace_self_model(SelfModelBundle(knowledge=knowledge))
    return builder.build()


def test_information_need_detector_fires_from_execute_brain():
    """
    A real Kernel tick, given an entity with a high-priority unlinked UnknownFact,
    produces an INFORMATION_SEEKING ProjectState on that entity — proving
    InformationNeedDetector.detect_and_generate() is wired into
    CognitionDomain.execute_brain() and that its result actually reaches the
    authoritative EntityUpdate (not discarded by a hardcoded strategic=None).

    ENTITY_BRAIN scheduling is cadence-gated (src/engine/scheduler.py), and the
    effective cadence is governor-mode-dependent (SystemCadence.strategic_intelligence
    ranges 10 (NORMAL) to 100 (SURVIVAL) ticks, src/engine/policy.py) — under this
    test's minimal RuntimeProfile the governor escalates to DEGRADED (cadence 50)
    almost immediately. Rather than depend on governor internals, run up to 100
    ticks (the worst-case SURVIVAL cadence) and stop at the first tick the
    detector actually fires.
    """
    entity = _entity_with_unknown()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    kernel = Kernel(_profile(), state, DeterministicRNG(1))
    info_seeking_projects = []
    try:
        for _ in range(100):
            kernel.tick_once()
            final_entity = kernel.state.entities[1]
            info_seeking_projects = [
                p for p in final_entity.strategic.projects.values()
                if p.kind == ProjectKind.INFORMATION_SEEKING
            ]
            if info_seeking_projects:
                break
    finally:
        kernel.shutdown()

    assert len(info_seeking_projects) == 1
    assert "moon_resin.source" in info_seeking_projects[0].id
