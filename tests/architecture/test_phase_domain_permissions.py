"""Architecture guard: per-phase read/write/emit domain declarations (RPG-INFRA-155/156/157)."""
from src.engine.phases import TickPhase
from src.engine.phase_domain_permissions import (
    ALL_AUTHORITATIVE_PHASES,
    PHASE_EMIT_DOMAINS,
    PHASE_READ_DOMAINS,
    PHASE_WRITE_DOMAINS,
)

_AUTHORITATIVE = [
    TickPhase.INIT,
    TickPhase.SCHEDULING,
    TickPhase.COLLECTION,
    TickPhase.RESOLUTION,
    TickPhase.CLEANUP,
    TickPhase.ADVANCEMENT,
]


def test_each_authoritative_phase_declares_read_domains():
    for phase in _AUTHORITATIVE:
        assert phase in PHASE_READ_DOMAINS, f"{phase.name} missing from PHASE_READ_DOMAINS"
        assert isinstance(PHASE_READ_DOMAINS[phase], frozenset), f"{phase.name} read domains must be frozenset"


def test_each_authoritative_phase_declares_write_domains():
    for phase in _AUTHORITATIVE:
        assert phase in PHASE_WRITE_DOMAINS, f"{phase.name} missing from PHASE_WRITE_DOMAINS"
        assert isinstance(PHASE_WRITE_DOMAINS[phase], frozenset), f"{phase.name} write domains must be frozenset"


def test_each_authoritative_phase_declares_emit_domains():
    for phase in _AUTHORITATIVE:
        assert phase in PHASE_EMIT_DOMAINS, f"{phase.name} missing from PHASE_EMIT_DOMAINS"
        assert isinstance(PHASE_EMIT_DOMAINS[phase], frozenset), f"{phase.name} emit domains must be frozenset"


def test_resolution_is_sole_entity_write_phase():
    entity_writers = {
        phase for phase, domains in PHASE_WRITE_DOMAINS.items()
        if "entity" in domains or "world" in domains
    }
    assert entity_writers == {TickPhase.RESOLUTION}, (
        f"Only RESOLUTION should declare entity/world write access; got {entity_writers}"
    )


def test_collection_phase_does_not_write_entity_state():
    writes = PHASE_WRITE_DOMAINS[TickPhase.COLLECTION]
    assert "entity" not in writes, "COLLECTION must not declare entity write access"
    assert "world" not in writes, "COLLECTION must not declare world write access"


def test_persistence_phase_is_non_authoritative():
    writes = PHASE_WRITE_DOMAINS.get(TickPhase.PERSISTENCE, frozenset())
    assert "entity" not in writes, "PERSISTENCE must not declare entity write access"
    assert "world" not in writes, "PERSISTENCE must not declare world write access"


def test_all_authoritative_phases_constant_matches_list():
    assert ALL_AUTHORITATIVE_PHASES == frozenset(_AUTHORITATIVE)
