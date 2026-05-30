from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set


@dataclass(frozen=True, slots=True)
class ItemDef:
    id: str
    tags: Tuple[str, ...]
    rarity: str
    base_value: int
    use_kind: str
    class_fit: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResourceDef:
    id: str
    yield_item: str
    source_region_tags: Tuple[str, ...]
    required_tool: Optional[str] = None
    base_difficulty: int = 1


@dataclass(frozen=True, slots=True)
class EnemyDef:
    id: str
    danger_hint: str
    max_hp: int
    atk: int
    def_stat: int
    loot_table: Dict[str, float]  # item_id -> probability
    spawn_regions: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecipeDef:
    id: str
    requires_items: Dict[str, int]
    service_req: str
    gold_cost: int
    output_item_id: str


@dataclass(frozen=True, slots=True)
class ServiceDef:
    id: str
    region_id: str
    supported_affordances: Tuple[str, ...]
    knowledge_scope: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RegionDef:
    id: str
    name: str
    tags: Tuple[str, ...]
    danger_level: int = 1


class ItemRegistry:
    _items: Dict[str, ItemDef] = {}

    @classmethod
    def bootstrap(cls, data: Dict[str, ItemDef]) -> None:
        cls._items = dict(data)

    @classmethod
    def get(cls, item_id: str) -> ItemDef:
        if item_id not in cls._items:
            raise KeyError(f"Item not found in ItemRegistry: {item_id}")
        return cls._items[item_id]

    @classmethod
    def contains(cls, item_id: str) -> bool:
        return item_id in cls._items

    @classmethod
    def all(cls) -> Dict[str, ItemDef]:
        return dict(cls._items)


class ResourceRegistry:
    _resources: Dict[str, ResourceDef] = {}

    @classmethod
    def bootstrap(cls, data: Dict[str, ResourceDef]) -> None:
        cls._resources = dict(data)

    @classmethod
    def get(cls, resource_id: str) -> ResourceDef:
        if resource_id not in cls._resources:
            raise KeyError(f"Resource not found in ResourceRegistry: {resource_id}")
        return cls._resources[resource_id]

    @classmethod
    def contains(cls, resource_id: str) -> bool:
        return resource_id in cls._resources

    @classmethod
    def all(cls) -> Dict[str, ResourceDef]:
        return dict(cls._resources)


class EnemyRegistry:
    _enemies: Dict[str, EnemyDef] = {}

    @classmethod
    def bootstrap(cls, data: Dict[str, EnemyDef]) -> None:
        cls._enemies = dict(data)

    @classmethod
    def get(cls, enemy_id: str) -> EnemyDef:
        if enemy_id not in cls._enemies:
            raise KeyError(f"Enemy not found in EnemyRegistry: {enemy_id}")
        return cls._enemies[enemy_id]

    @classmethod
    def contains(cls, enemy_id: str) -> bool:
        return enemy_id in cls._enemies

    @classmethod
    def all(cls) -> Dict[str, EnemyDef]:
        return dict(cls._enemies)


class RecipeRegistry:
    _recipes: Dict[str, RecipeDef] = {}

    @classmethod
    def bootstrap(cls, data: Dict[str, RecipeDef]) -> None:
        cls._recipes = dict(data)

    @classmethod
    def get(cls, recipe_id: str) -> RecipeDef:
        if recipe_id not in cls._recipes:
            raise KeyError(f"Recipe not found in RecipeRegistry: {recipe_id}")
        return cls._recipes[recipe_id]

    @classmethod
    def contains(cls, recipe_id: str) -> bool:
        return recipe_id in cls._recipes

    @classmethod
    def all(cls) -> Dict[str, RecipeDef]:
        return dict(cls._recipes)


class ServiceRegistry:
    _services: Dict[str, ServiceDef] = {}

    @classmethod
    def bootstrap(cls, data: Dict[str, ServiceDef]) -> None:
        cls._services = dict(data)

    @classmethod
    def get(cls, service_id: str) -> ServiceDef:
        if service_id not in cls._services:
            raise KeyError(f"Service not found in ServiceRegistry: {service_id}")
        return cls._services[service_id]

    @classmethod
    def contains(cls, service_id: str) -> bool:
        return service_id in cls._services

    @classmethod
    def all(cls) -> Dict[str, ServiceDef]:
        return dict(cls._services)


class RegionRegistry:
    _regions: Dict[str, RegionDef] = {}

    @classmethod
    def bootstrap(cls, data: Dict[str, RegionDef]) -> None:
        cls._regions = dict(data)

    @classmethod
    def get(cls, region_id: str) -> RegionDef:
        if region_id not in cls._regions:
            raise KeyError(f"Region not found in RegionRegistry: {region_id}")
        return cls._regions[region_id]

    @classmethod
    def contains(cls, region_id: str) -> bool:
        return region_id in cls._regions

    @classmethod
    def all(cls) -> Dict[str, RegionDef]:
        return dict(cls._regions)


# ----------------------------------------------------
# SEEDING: Bootstrap registries with Phase 1 Content
# ----------------------------------------------------

def seed_phase1_content() -> None:
    """Load default Phase 1 adventure seed contents."""
    
    # 1. Items
    items = {
        "rusted_sword": ItemDef("rusted_sword", ("weapon", "melee"), "COMMON", 10, "weapon", ("warrior",)),
        "wooden_staff": ItemDef("wooden_staff", ("weapon", "magic"), "COMMON", 10, "weapon", ("mage",)),
        "basic_bow": ItemDef("basic_bow", ("weapon", "ranged"), "COMMON", 15, "weapon", ("ranger",)),
        "leather_armor": ItemDef("leather_armor", ("armor",), "COMMON", 25, "armor"),
        "iron_sword": ItemDef("iron_sword", ("weapon", "melee"), "UNCOMMON", 80, "weapon", ("warrior",)),
        "hunter_blade": ItemDef("hunter_blade", ("weapon", "melee"), "RARE", 120, "weapon", ("warrior", "ranger")),
        "apprentice_staff": ItemDef("apprentice_staff", ("weapon", "magic"), "UNCOMMON", 75, "weapon", ("mage",)),
        "small_potion": ItemDef("small_potion", ("consumable", "healing"), "COMMON", 15, "potion"),
        "travel_ration": ItemDef("travel_ration", ("consumable", "food"), "COMMON", 5, "food"),
        "repair_kit": ItemDef("repair_kit", ("tool",), "COMMON", 20, "tool"),
        # Base Resources
        "wood": ItemDef("wood", ("material",), "COMMON", 2, "material"),
        "herb": ItemDef("herb", ("material",), "COMMON", 3, "material"),
        "iron_ore": ItemDef("iron_ore", ("material",), "UNCOMMON", 12, "material"),
        "beast_fang": ItemDef("beast_fang", ("material",), "UNCOMMON", 15, "material"),
        "wolf_pelt": ItemDef("wolf_pelt", ("material",), "COMMON", 8, "material"),
        "moon_resin": ItemDef("moon_resin", ("material", "rare"), "RARE", 40, "material"),
        "crystal_shard": ItemDef("crystal_shard", ("material",), "UNCOMMON", 25, "material"),
        "goblin_token": ItemDef("goblin_token", ("material",), "COMMON", 5, "material"),
        "ancient_fragment": ItemDef("ancient_fragment", ("material",), "RARE", 50, "material"),
        "healing_flower": ItemDef("healing_flower", ("material",), "COMMON", 5, "material"),
    }
    ItemRegistry.bootstrap(items)

    # 2. Resources
    resources = {
        "node_wood": ResourceDef("node_wood", "wood", ("near_forest",), None, 1),
        "node_herb": ResourceDef("node_herb", "herb", ("near_forest", "moon_cave"), None, 1),
        "node_iron": ResourceDef("node_iron", "iron_ore", ("old_mine",), "pickaxe", 2),
        "node_resin": ResourceDef("node_resin", "moon_resin", ("moon_cave",), None, 3),
        "node_flower": ResourceDef("node_flower", "healing_flower", ("near_forest",), None, 1),
    }
    ResourceRegistry.bootstrap(resources)

    # 3. Enemies
    enemies = {
        "rat": EnemyDef("rat", "EASY", 15, 4, 1, {"beast_fang": 0.2}, ("hometown", "near_forest")),
        "wolf": EnemyDef("wolf", "MEDIUM", 45, 12, 3, {"wolf_pelt": 0.6, "beast_fang": 0.3}, ("near_forest", "wolf_den")),
        "goblin": EnemyDef("goblin", "MEDIUM", 40, 10, 2, {"goblin_token": 0.8}, ("goblin_camp",)),
        "goblin_archer": EnemyDef("goblin_archer", "MEDIUM", 35, 11, 1, {"goblin_token": 0.5}, ("goblin_camp",)),
        "cave_spider": EnemyDef("cave_spider", "MEDIUM", 50, 14, 4, {"crystal_shard": 0.2}, ("old_mine", "moon_cave")),
        "bandit_scout": EnemyDef("bandit_scout", "HARD", 70, 18, 5, {"ancient_fragment": 0.1}, ("north_ruin",)),
        "elite_goblin": EnemyDef("elite_goblin", "BOSS", 120, 24, 8, {"goblin_token": 1.0, "ancient_fragment": 0.4}, ("goblin_camp",)),
    }
    EnemyRegistry.bootstrap(enemies)

    # 4. Recipes
    recipes = {
        "iron_sword": RecipeDef("iron_sword", {"iron_ore": 2, "wood": 1}, "blacksmith", 40, "iron_sword"),
        "hunter_blade": RecipeDef("hunter_blade", {"iron_ore": 2, "beast_fang": 1, "moon_resin": 1}, "blacksmith", 50, "hunter_blade"),
        "small_potion": RecipeDef("small_potion", {"healing_flower": 1, "crystal_shard": 1}, "blacksmith", 10, "small_potion"),
    }
    RecipeRegistry.bootstrap(recipes)

    # 5. Services
    services = {
        "shop_hometown": ServiceDef("shop_hometown", "hometown", ("buy", "sell")),
        "blacksmith_hometown": ServiceDef("blacksmith_hometown", "hometown", ("craft", "repair")),
        "guide_hometown": ServiceDef("guide_hometown", "hometown", ("ask_info",), ("wood", "herb", "iron_ore", "healing_flower", "moon_resin")),
        "guild_hometown": ServiceDef("guild_hometown", "hometown", ("quest", "info")),
        "inn_hometown": ServiceDef("inn_hometown", "hometown", ("rest",)),
    }
    ServiceRegistry.bootstrap(services)

    # 6. Regions
    regions = {
        "hometown": RegionDef("hometown", "Hometown Center", ("safe",), 0),
        "near_forest": RegionDef("near_forest", "Near Forest Wilderness", ("wild",), 1),
        "old_mine": RegionDef("old_mine", "Abandoned Iron Mine", ("mine", "dark"), 2),
        "wolf_den": RegionDef("wolf_den", "Deep Wolf Den", ("dangerous",), 2),
        "north_ruin": RegionDef("north_ruin", "Forgotten Northern Ruins", ("ruins",), 3),
        "goblin_camp": RegionDef("goblin_camp", "Goblin Outpost", ("hostile",), 3),
        "moon_cave": RegionDef("moon_cave", "Shimmering Moonstone Cave", ("magical",), 4),
    }
    RegionRegistry.bootstrap(regions)


# Self-seed on import for seamless execution compatibility
seed_phase1_content()
