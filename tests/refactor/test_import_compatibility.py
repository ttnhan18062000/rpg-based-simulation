def test_core_import_compatibility():
    # Old paths should still work due to re-exports
    from src.core.state import ItemStack, InventoryComponent, ItemKind, EquipSlot, SocialBond, BetrayalRecord, SocialComponent
    from src.core.updates import InventoryUpdate, QuestUpdate, ResourceTransferIntent
    from src.core.quests import QuestKind, QuestStatus, RewardState, QuestState
    
    # Check that they are the same classes as in the new paths
    from src.core.models.inventory import ItemStack as NewItemStack
    from src.core.update_models.inventory import InventoryUpdate as NewInventoryUpdate
    from src.core.models.social import SocialBond as NewSocialBond
    from src.core.models.quests import QuestState as NewQuestState
    from src.core.update_models.quests import QuestUpdate as NewQuestUpdate
    from src.core.update_models.resources import ResourceTransferIntent as NewResourceTransferIntent
    
    assert ItemStack is NewItemStack
    assert InventoryUpdate is NewInventoryUpdate
    assert SocialBond is NewSocialBond
    assert QuestState is NewQuestState
    assert QuestUpdate is NewQuestUpdate
    assert ResourceTransferIntent is NewResourceTransferIntent
    
    print("Import compatibility verified.")


def test_engine_import_compatibility():
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.engine.domain_logic import SimulationDomainLogic

    assert AuthoritativeApplyPipeline is not None
    assert SimulationDomainLogic is not None


def test_systems_import_compatibility():
    from src.systems.strategic import StrategicIntelligenceSystem
    from src.systems.redirection import StrategicRedirectionSystem
    from src.systems.strategic_systems.detour import DetourSuggestionSystem
    from src.systems.strategic_systems.belief import BeliefCycleSystem
    from src.systems.learning import StrategicLearningService
    from src.systems.social_contract import SocialContractSystem
    from src.systems.social_memory import SocialMemoryService
    from src.systems.party import PartyCoordinationSystem
    from src.systems.world_systems.generator import EntityGenerator
    from src.systems.world_systems.navigation import NavigationSystem
    from src.systems.world_systems.groups import GroupSystem

    assert StrategicIntelligenceSystem is not None
    assert StrategicRedirectionSystem is not None
    assert DetourSuggestionSystem is not None
    assert BeliefCycleSystem is not None
    assert StrategicLearningService is not None
    assert SocialContractSystem is not None
    assert SocialMemoryService is not None
    assert PartyCoordinationSystem is not None
    assert EntityGenerator is not None
    assert NavigationSystem is not None
    assert GroupSystem is not None
