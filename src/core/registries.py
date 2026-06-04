import os
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


# NOTE: The legacy hardcoded seed maps below exist ONLY for fallback compatibility.
# For all active development and new gameplay systems, catalog-backed registries
# sourced from the Content Catalog database (data/content/) are authoritative.
# No new hardcoded definitions should be added to python structures directly.
class AdapterError(ValueError):
    """Raised when an adapter fails to convert a catalog record."""
    def __init__(self, record_id: str, message: str) -> None:
        self.record_id = record_id
        super().__init__(f"Error adapting record '{record_id}': {message}")


class CatalogToItemRegistryAdapter:
    def __init__(self, repo: Any, migration_mode: bool = True) -> None:
        self.repo = repo
        self.migration_mode = migration_mode

    def adapt(self) -> Dict[str, ItemDef]:
        items: Dict[str, ItemDef] = {}
        for item_id, item in self.repo.items.items():
            try:
                use_kind = getattr(item, "use_kind", None)
                if not use_kind:
                    if not self.migration_mode:
                        raise AdapterError(item_id, "Missing explicit 'use_kind' in catalog-backed mode")
                    use_kind = "material"
                    if "weapon" in item.categories:
                        use_kind = "weapon"
                    elif "armor" in item.categories:
                        use_kind = "armor"
                    elif "consumable" in item.categories:
                        if "healing" in item.categories:
                            use_kind = "potion"
                        elif "food" in item.categories:
                            use_kind = "food"
                        else:
                            use_kind = "consumable"
                    elif "tool" in item.categories:
                        use_kind = "tool"
                
                # Map class fit from metadata fallback
                class_fit = tuple(getattr(item, "class_fit", ())) if getattr(item, "class_fit", None) else ()
                if not class_fit:
                    metadata_fit = tuple(item.metadata.get("class_fit", ())) if hasattr(item, "metadata") and item.metadata else ()
                    if metadata_fit:
                        class_fit = metadata_fit
                    else:
                        if not self.migration_mode:
                            raise AdapterError(item_id, "Missing explicit 'class_fit' in catalog-backed mode")
                        if item_id in ("rusted_sword", "iron_sword", "hunter_blade"):
                            class_fit = ("warrior",)
                            if item_id == "hunter_blade":
                                class_fit = ("warrior", "ranger")
                        elif item_id in ("wooden_staff", "apprentice_staff"):
                            class_fit = ("mage",)
                        elif item_id == "basic_bow":
                            class_fit = ("ranger",)
                
                items[item_id] = ItemDef(
                    id=item_id,
                    tags=tuple(item.categories),
                    rarity=item.rarity,
                    base_value=int(item.base_value),
                    use_kind=use_kind,
                    class_fit=class_fit
                )
            except AdapterError:
                raise
            except Exception as e:
                raise AdapterError(item_id, str(e)) from e
        return items


class CatalogToRecipeRegistryAdapter:
    def __init__(self, repo: Any) -> None:
        self.repo = repo

    def adapt(self) -> Dict[str, RecipeDef]:
        recipes: Dict[str, RecipeDef] = {}
        for rec_id, rec in self.repo.recipes.items():
            try:
                service_req = "blacksmith"
                if rec.required_service:
                    if "blacksmith" in rec.required_service:
                        service_req = "blacksmith"
                    elif "healer" in rec.required_service:
                        service_req = "healer"
                    else:
                        service_req = rec.required_service
                
                legacy_id = rec_id
                if rec_id.startswith("craft_"):
                    legacy_id = rec_id.replace("craft_", "")
                
                output_item = list(rec.outputs.keys())[0] if rec.outputs else ""
                
                r_def = RecipeDef(
                    id=legacy_id,
                    requires_items=dict(rec.ingredients),
                    service_req=service_req,
                    gold_cost=int(rec.gold_cost),
                    output_item_id=output_item
                )
                recipes[legacy_id] = r_def
                if legacy_id != rec_id:
                    recipes[rec_id] = r_def
            except Exception as e:
                raise AdapterError(rec_id, str(e)) from e
        return recipes


class CatalogToServiceRegistryAdapter:
    def __init__(self, repo: Any, catalog_mode: bool = False, migration_mode: bool = True) -> None:
        self.repo = repo
        self.catalog_mode = catalog_mode
        self.migration_mode = migration_mode

    def adapt(self) -> Dict[str, ServiceDef]:
        services: Dict[str, ServiceDef] = {}
        # Prepopulate hometown services for compatibility/seeding only if not catalog_mode
        if not self.catalog_mode:
            services["shop_hometown"] = ServiceDef("shop_hometown", "hometown", ("buy", "sell"))
            services["blacksmith_hometown"] = ServiceDef("blacksmith_hometown", "hometown", ("craft", "repair"))
            services["guide_hometown"] = ServiceDef("guide_hometown", "hometown", ("ask_info",), ("wood", "herb", "iron_ore", "healing_flower", "moon_resin"))
            services["guild_hometown"] = ServiceDef("guild_hometown", "hometown", ("quest", "info"))
            services["inn_hometown"] = ServiceDef("inn_hometown", "hometown", ("rest",))
        
        for s_id, s_prof in self.repo.services.items():
            try:
                affordances = list(getattr(s_prof, "affordances", [])) if getattr(s_prof, "affordances", None) else []
                if not affordances:
                    if not self.migration_mode:
                        raise AdapterError(s_id, "Missing explicit 'affordances' in catalog-backed mode")
                    if "trade" in s_id or "store" in s_id or s_prof.provided_items:
                        affordances.extend(["buy", "sell"])
                    if "blacksmith" in s_id or "craft" in s_id:
                        affordances.extend(["craft", "repair"])
                    if "inn" in s_id or "rest" in s_id:
                        affordances.append("rest")
                    if "healer" in s_id or "healing" in s_id:
                        affordances.append("rest")
                
                services[s_id] = ServiceDef(
                    id=s_id,
                    region_id="hometown",
                    supported_affordances=tuple(affordances)
                )
            except AdapterError:
                raise
            except Exception as e:
                raise AdapterError(s_id, str(e)) from e
        return services


class CatalogToRegionRegistryAdapter:
    def __init__(self, repo: Any) -> None:
        self.repo = repo

    def adapt(self) -> Dict[str, RegionDef]:
        regions: Dict[str, RegionDef] = {}
        for reg_id, reg in self.repo.regions.items():
            try:
                regions[reg_id] = RegionDef(
                    id=reg_id,
                    name=reg.display_name or reg_id.replace("_", " ").title(),
                    tags=tuple(reg.tags),
                    danger_level=reg.danger_level
                )
            except Exception as e:
                raise AdapterError(reg_id, str(e)) from e
        if "hometown" not in regions:
            regions["hometown"] = RegionDef("hometown", "Hometown Center", ("safe",), 0)
        return regions


class CatalogToResourceRegistryAdapter:
    def __init__(self, repo: Any, migration_mode: bool = True) -> None:
        self.repo = repo
        self.migration_mode = migration_mode

    def adapt(self) -> Dict[str, ResourceDef]:
        resources: Dict[str, ResourceDef] = {}
        for res_id, res in self.repo.resources.items():
            try:
                legacy_id = getattr(res, "legacy_id", None)
                if not legacy_id:
                    if not self.migration_mode:
                        raise AdapterError(res_id, "Missing explicit 'legacy_id' in catalog-backed mode")
                    legacy_id = res_id
                    if res_id == "wood_node":
                        legacy_id = "node_wood"
                    elif res_id == "herb_patch":
                        legacy_id = "node_herb"
                    elif res_id == "iron_vein":
                        legacy_id = "node_iron"
                    elif res_id == "moon_resin_tree":
                        legacy_id = "node_resin"
                    elif res_id == "healing_flower_patch":
                        legacy_id = "node_flower"

                source_region_tags = tuple(res.metadata.get("source_region_tags", ())) if hasattr(res, "metadata") and res.metadata else ()
                if not source_region_tags:
                    source_region_tags = tuple(res.metadata.get("preferred_biomes", [])) if hasattr(res, "metadata") and res.metadata else ()
                    if not source_region_tags:
                        if not self.migration_mode:
                            raise AdapterError(res_id, "Missing source region tags in catalog-backed mode")
                        if legacy_id == "node_wood":
                            source_region_tags = ("near_forest",)
                        elif legacy_id == "node_herb":
                            source_region_tags = ("near_forest", "moon_cave")
                        elif legacy_id == "node_iron":
                            source_region_tags = ("old_mine",)
                        elif legacy_id == "node_resin":
                            source_region_tags = ("moon_cave",)
                        elif legacy_id == "node_flower":
                            source_region_tags = ("near_forest",)
                
                required_tool = getattr(res, "required_tool", None)
                if required_tool is None:
                    required_tool = res.metadata.get("required_tool") if hasattr(res, "metadata") and res.metadata else None
                    if required_tool is None:
                        if not self.migration_mode:
                            required_tool = None
                        else:
                            if "iron" in res_id or "silver" in res_id:
                                required_tool = "pickaxe"
                
                base_difficulty = res.metadata.get("base_difficulty") if hasattr(res, "metadata") and res.metadata else None
                if base_difficulty is None:
                    if not self.migration_mode:
                        base_difficulty = 1
                    else:
                        if "iron" in res_id or "silver" in res_id or "resin" in res_id:
                            base_difficulty = 2
                            if "resin" in res_id:
                                base_difficulty = 3
                        else:
                            base_difficulty = 1

                yield_item = getattr(res, "runtime_kind", None) or res.resource_type

                r_def = ResourceDef(
                    id=legacy_id,
                    yield_item=yield_item,
                    source_region_tags=source_region_tags,
                    required_tool=required_tool,
                    base_difficulty=int(base_difficulty)
                )
                resources[legacy_id] = r_def
                if legacy_id != res_id:
                    resources[res_id] = r_def
            except AdapterError:
                raise
            except Exception as e:
                raise AdapterError(res_id, str(e)) from e
        return resources


class ArchetypeToEnemyRegistryAdapter:
    def __init__(self, repo: Any, catalog_mode: bool = False) -> None:
        self.repo = repo
        self.catalog_mode = catalog_mode

    def adapt(self) -> Dict[str, EnemyDef]:
        enemies: Dict[str, EnemyDef] = {}
        for proj_id, proj in self.repo.legacy_enemy_projections.items():
            try:
                max_hp = 50
                atk = 10
                def_stat = 2
                
                arch = self.repo.get_entity_archetype(proj.archetype_id)
                if arch:
                    stats = self.repo.get_stats_profile(arch.stat_profile)
                    if stats:
                        max_hp = stats.max_hp
                        atk = stats.atk
                        def_stat = stats.def_stat
                
                enemies[proj.legacy_enemy_id] = EnemyDef(
                    id=proj.legacy_enemy_id,
                    danger_hint=proj.danger_hint,
                    max_hp=max_hp,
                    atk=atk,
                    def_stat=def_stat,
                    loot_table=dict(proj.loot_table),
                    spawn_regions=tuple(proj.spawn_regions)
                )
            except Exception as e:
                raise AdapterError(proj_id, str(e)) from e
        if "rat" not in enemies and not self.catalog_mode:
            enemies["rat"] = EnemyDef("rat", "EASY", 15, 4, 1, {"beast_fang": 0.2}, ("hometown", "near_forest"))
        return enemies


runtime_content_source: str = "legacy_hardcoded"
catalog_fingerprint: Optional[str] = None
fallback_usage_reported: bool = False


_sentinel = object()


def seed_phase1_content(catalog_repo: Optional[Any] = _sentinel, required: bool = False, migration_mode: bool = True) -> None:
    """Load default adventure seed contents either from Content Catalog or legacy hardcoded backup."""
    global runtime_content_source, catalog_fingerprint, fallback_usage_reported

    # Switch default development path to catalog mode if default catalog directory is present
    if catalog_repo is _sentinel:
        default_path = "data/content"
        if os.path.exists(default_path):
            try:
                from src.content.repository import CatalogRepository
                catalog_repo = CatalogRepository(default_path)
                catalog_repo.load_all()
            except Exception as e:
                if required:
                    raise ValueError(f"Failed to load default content catalog from {default_path}: {e}")
        else:
            catalog_repo = None

    if required and catalog_repo is None:
        raise ValueError("Catalog repository is required in strict mode")

    if catalog_repo is not None:
        from src.content.repository import CatalogRepository
        assert isinstance(catalog_repo, CatalogRepository)
        
        if required:
            from src.content.validator import CatalogValidator, CatalogValidationError
            validator = CatalogValidator(catalog_repo)
            issues = validator.validate()
            errors = [issue for issue in issues if issue.severity == "ERROR"]
            if errors:
                raise CatalogValidationError(f"Catalog has validation errors: {errors}")
        
        # Run adapters with strict or migration mode as requested
        items = CatalogToItemRegistryAdapter(catalog_repo, migration_mode=migration_mode).adapt()
        recipes = CatalogToRecipeRegistryAdapter(catalog_repo).adapt()
        services = CatalogToServiceRegistryAdapter(catalog_repo, catalog_mode=True, migration_mode=migration_mode).adapt()
        regions = CatalogToRegionRegistryAdapter(catalog_repo).adapt()
        resources = CatalogToResourceRegistryAdapter(catalog_repo, migration_mode=migration_mode).adapt()
        enemies = ArchetypeToEnemyRegistryAdapter(catalog_repo, catalog_mode=True).adapt()

        # Seed registries
        ItemRegistry.bootstrap(items)
        RecipeRegistry.bootstrap(recipes)
        ServiceRegistry.bootstrap(services)
        RegionRegistry.bootstrap(regions)
        ResourceRegistry.bootstrap(resources)
        EnemyRegistry.bootstrap(enemies)
        
        # Bootstrap ItemRegistry in src.core.items as well
        from src.core.items import ItemRegistry as CoreItemRegistry
        CoreItemRegistry.bootstrap(catalog_repo.items)

        runtime_content_source = "catalog"
        catalog_fingerprint = catalog_repo.fingerprint
        
    else:
        import logging
        logging.getLogger(__name__).warning("Falling back to legacy hardcoded Phase 1 content seeding")
        fallback_usage_reported = True
        # FALLBACK: Seeding with legacy hardcoded Phase 1 content
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
        
        from src.core.items import ItemRegistry as CoreItemRegistry
        CoreItemRegistry.bootstrap({})
        
        runtime_content_source = "legacy_hardcoded"
        catalog_fingerprint = None


# Self-seed on import for seamless execution compatibility
seed_phase1_content()
