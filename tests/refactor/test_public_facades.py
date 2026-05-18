
def test_engine_public_facades():
    """Lock in the public entry points for the engine domain."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.engine.domain_logic import SimulationDomainLogic
    from src.engine.apply import ApplyPath
    from src.engine.kernel import Kernel
    
    assert AuthoritativeApplyPipeline is not None
    assert SimulationDomainLogic is not None
    assert ApplyPath is not None
    assert Kernel is not None

def test_system_public_facades():
    """Lock in the public entry points for authoritative systems."""
    from src.systems.strategic import StrategicIntelligenceSystem
    from src.systems.redirection import StrategicRedirectionSystem
    from src.systems.social_contract import SocialContractSystem
    from src.systems.social_memory import SocialMemoryService
    from src.systems.strategic_systems.belief import BeliefCycleSystem
    from src.systems.genetics import GeneticsSystem
    from src.systems.narrative import NarrativeMemorySystem
    from src.systems.world_systems.groups import GroupSystem
    from src.systems.lifecycle import LifecycleSystem
    
    assert StrategicIntelligenceSystem is not None
    assert StrategicRedirectionSystem is not None
    assert SocialContractSystem is not None
    assert SocialMemoryService is not None
    assert BeliefCycleSystem is not None
    assert GeneticsSystem is not None
    assert NarrativeMemorySystem is not None
    assert GroupSystem is not None
    assert LifecycleSystem is not None

def test_core_public_facades():
    """Lock in the public entry points for core state and updates."""
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate, EntityUpdate
    from src.core.enums import ReasonCode
    from src.core.quests import QuestStatus
    
    assert AuthoritativeState is not None
    assert EntityState is not None
    assert StateUpdate is not None
    assert EntityUpdate is not None
    assert ReasonCode is not None
    assert QuestStatus is not None
