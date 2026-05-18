from __future__ import annotations
import json
from dataclasses import fields, is_dataclass
from typing import Any, Dict, List, Type, TypeVar, Union, get_args, get_origin, Set, Tuple
from enum import Enum

from src_legacy.core.state import (
    AuthoritativeState, EntityState, RegionState, LocalScarState,
    ResourceNodeState, BuildingState, CorpseState, GroundItemState,
    ChestState, InventoryComponent, GroupRecord, InteractionComponent,
    IdentityComponent, AttributeComponent, BiologicalComponent,
    LifecycleComponent, AptitudeComponent, CombatComponent,
    EquipmentComponent, NavigationComponent, TaskComponent,
    ItemStack, EquipSlot, ItemKind, LifeStage, PersonalityComponent,
    SocialComponent, SocialBond
)
from src_legacy.core.updates import (
    StateUpdate, EntityUpdate, WorldUpdate, BuildingUpdate,
    ResourceNodeUpdate, ChestUpdate, InventoryUpdate, EquipmentUpdate,
    InteractionUpdate, IdentityUpdate, AttributeUpdate, BiologicalUpdate,
    LifecycleUpdate, CombatUpdate, NavigationUpdate, TaskUpdate,
    RewardUpdate, QuestUpdate, SocialUpdate, StrategicUpdate,
    CombatIntent, SocialBondUpdate
)
from src_legacy.core.strategic import StrategicComponent

T = TypeVar("T")

class StateDeserializer:
    """
    Authoritative deserializer for V2 state and update objects.
    Enforces deterministic mapping from raw JSON/dict back to typed records.
    """

    # Manual type mapping to avoid get_type_hints circularity issues
    TYPE_MAP = {
        "AuthoritativeState": AuthoritativeState,
        "EntityState": EntityState,
        "RegionState": RegionState,
        "LocalScarState": LocalScarState,
        "ResourceNodeState": ResourceNodeState,
        "BuildingState": BuildingState,
        "CorpseState": CorpseState,
        "GroundItemState": GroundItemState,
        "ChestState": ChestState,
        "InventoryComponent": InventoryComponent,
        "GroupRecord": GroupRecord,
        "InteractionComponent": InteractionComponent,
        "IdentityComponent": IdentityComponent,
        "AttributeComponent": AttributeComponent,
        "BiologicalComponent": BiologicalComponent,
        "LifecycleComponent": LifecycleComponent,
        "AptitudeComponent": AptitudeComponent,
        "CombatComponent": CombatComponent,
        "EquipmentComponent": EquipmentComponent,
        "NavigationComponent": NavigationComponent,
        "TaskComponent": TaskComponent,
        "ItemStack": ItemStack,
        "EquipSlot": EquipSlot,
        "ItemKind": ItemKind,
        "LifeStage": LifeStage,
        "PersonalityComponent": PersonalityComponent,
        "SocialComponent": SocialComponent,
        "SocialBond": SocialBond,
        "StrategicComponent": StrategicComponent,
        "StateUpdate": StateUpdate,
        "EntityUpdate": EntityUpdate,
        "WorldUpdate": WorldUpdate,
        "BuildingUpdate": BuildingUpdate,
        "ResourceNodeUpdate": ResourceNodeUpdate,
        "ChestUpdate": ChestUpdate,
        "InventoryUpdate": InventoryUpdate,
        "EquipmentUpdate": EquipmentUpdate,
        "InteractionUpdate": InteractionUpdate,
        "IdentityUpdate": IdentityUpdate,
        "AttributeUpdate": AttributeUpdate,
        "BiologicalUpdate": BiologicalUpdate,
        "LifecycleUpdate": LifecycleUpdate,
        "CombatUpdate": CombatUpdate,
        "NavigationUpdate": NavigationUpdate,
        "TaskUpdate": TaskUpdate,
        "RewardUpdate": RewardUpdate,
        "QuestUpdate": QuestUpdate,
        "SocialUpdate": SocialUpdate,
        "StrategicUpdate": StrategicUpdate,
        "CombatIntent": CombatIntent,
        "SocialBondUpdate": SocialBondUpdate
    }

    @staticmethod
    def from_dict(cls: Any, data: Dict[str, Any]) -> Any:
        """
        Recursively construct a typed object from a dictionary.
        """
        if data is None:
            return None

        # Resolve forward references or string types
        if isinstance(cls, str):
            cls = StateDeserializer.TYPE_MAP.get(cls, cls)

        if isinstance(cls, type) and issubclass(cls, Enum):
            if isinstance(data, str) and "." in data:
                # Handle 'EnumClass.VALUE' format
                actual_val = data.split(".")[-1]
                try:
                    return cls(actual_val)
                except ValueError:
                    return cls[actual_val]
            return cls(data)

        if not is_dataclass(cls):
            return data

        field_data = {}
        for field in fields(cls):
            name = field.name
            if name not in data:
                continue

            value = data[name]
            field_type = field.type
            # print(f"[DEBUG] Field {name}: type={field_type}")

            field_data[name] = StateDeserializer._deserialize_value(field_type, value)

        return cls(**field_data)

    @staticmethod
    def _deserialize_value(field_type: Any, value: Any) -> Any:
        if value is None:
            return None

        # Resolve forward references
        if isinstance(field_type, str):
            # Handle Optional[T] in string form
            if field_type.startswith("Optional["):
                inner = field_type[9:-1]
                return StateDeserializer._deserialize_value(inner, value)
            if field_type.startswith("Union["):
                parts = field_type[6:-1].split(",")
                actual = [p.strip() for p in parts if p.strip() not in ("None", "type(None)")]
                if not actual: return value
                return StateDeserializer._deserialize_value(actual[0], value)

            if field_type.startswith("List[") or field_type.startswith("list["):
                inner = field_type[5:-1]
                return [StateDeserializer._deserialize_value(inner, v) for v in value]
            if field_type.startswith("Dict[") or field_type.startswith("dict["):
                inner_parts = field_type[5:-1].split(",")
                key_t = inner_parts[0].strip()
                val_t = inner_parts[1].strip()
                return {
                    (int(k) if key_t == "int" else k): StateDeserializer._deserialize_value(val_t, v)
                    for k, v in value.items()
                }
            
            field_type = StateDeserializer.TYPE_MAP.get(field_type, field_type)

        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin is Union:
            actual_types = [t for t in args if t is not type(None)]
            if not actual_types: return value
            return StateDeserializer._deserialize_value(actual_types[0], value)

        if origin in (list, List):
            return [StateDeserializer._deserialize_value(args[0], v) for v in value]

        if origin in (dict, Dict):
            key_t = args[0]
            val_t = args[1]
            return {
                (int(k) if key_t is int else k): StateDeserializer._deserialize_value(val_t, v)
                for k, v in value.items()
            }

        if origin in (set, Set):
            return {StateDeserializer._deserialize_value(args[0], v) for v in value}

        if origin in (tuple, Tuple):
            return tuple(StateDeserializer._deserialize_value(args[i], value[i]) for i in range(len(value)))

        if is_dataclass(field_type):
            return StateDeserializer.from_dict(field_type, value)
        
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return StateDeserializer.from_dict(field_type, value)

        return value

    @staticmethod
    def deserialize_state(data: Dict[str, Any]) -> AuthoritativeState:
        return StateDeserializer.from_dict(AuthoritativeState, data)

    @staticmethod
    def deserialize_update(data: Dict[str, Any]) -> StateUpdate:
        return StateDeserializer.from_dict(StateUpdate, data)
