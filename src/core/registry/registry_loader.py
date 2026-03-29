import json
import logging
from pathlib import Path
from pydantic import TypeAdapter

from src.core.gameplay.items.item_registry import ItemTemplate, ITEM_REGISTRY
from src.core.gameplay.classes import ClassDef, BreakthroughDef, SkillDef, CLASS_DEFS, BREAKTHROUGHS, SKILL_DEFS
from src.core.entities.traits import TraitDef, TRAIT_DEFS
from src.core.models.enums import RaceProfile, RACE_PROFILES
from src.core.world.spawn_config import SpawnConfig, LootConfig, SPAWN_CONFIGS, LOOT_CONFIGS

logger = logging.getLogger(__name__)

def load_all_registries(data_dir: Path | str = "data") -> None:
    """Load all definition JSON files from the given directory into the core registries."""
    data_path = Path(data_dir)
    logger.info("Loading registries from %s", data_path.resolve())

    _load_items(data_path / "items.json")
    _load_classes(data_path / "classes.json")
    _load_skills(data_path / "skills.json")
    _load_breakthroughs(data_path / "breakthroughs.json")
    _load_traits(data_path / "traits.json")
    _load_races(data_path / "races.json")
    _load_spawn_configs(data_path / "spawn_config.json")
    _load_loot_configs(data_path / "loot_config.json")
    
    logger.debug("load_all_registries FINISHING. CLASS_DEFS=%d, SKILL_DEFS=%d", len(CLASS_DEFS), len(SKILL_DEFS))
    logger.info("Successfully loaded all registries.")

def _load_races(path: Path) -> None:
    if not path.exists():
        logger.warning("Race definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(dict[str, RaceProfile])
    races = adapter.validate_python(data)
    
    RACE_PROFILES.clear()
    RACE_PROFILES.update(races)
    
    logger.info("Loaded %d races.", len(RACE_PROFILES))

def _load_spawn_configs(path: Path) -> None:
    if not path.exists():
        logger.warning("Spawn configuration not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[SpawnConfig])
    configs = adapter.validate_python(data)
    
    SPAWN_CONFIGS.clear()
    for cfg in configs:
        SPAWN_CONFIGS[(cfg.race, cfg.tier)] = cfg
        
    logger.info("Loaded %d spawn configurations.", len(SPAWN_CONFIGS))

def _load_loot_configs(path: Path) -> None:
    if not path.exists():
        logger.warning("Loot configuration not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[LootConfig])
    configs = adapter.validate_python(data)
    
    LOOT_CONFIGS.clear()
    for cfg in configs:
        LOOT_CONFIGS[cfg.kind] = cfg
        
    logger.info("Loaded %d loot configurations.", len(LOOT_CONFIGS))

def _load_items(path: Path) -> None:
    if not path.exists():
        logger.warning("Item definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[ItemTemplate])
    items = adapter.validate_python(data)
    
    ITEM_REGISTRY.clear()
    for item in items:
        ITEM_REGISTRY[item.item_id] = item
    
    logger.info("Loaded %d items.", len(ITEM_REGISTRY))

def _load_classes(path: Path) -> None:
    if not path.exists():
        logger.warning("Class definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[ClassDef])
    classes = adapter.validate_python(data)
    
    CLASS_DEFS.clear()
    for c in classes:
        CLASS_DEFS[c.class_id] = c
        
    logger.info("Loaded %d classes.", len(CLASS_DEFS))

def _load_skills(path: Path) -> None:
    if not path.exists():
        logger.warning("Skill definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[SkillDef])
    skills = adapter.validate_python(data)
    logger.debug("Loading skills from %s, found %d items", path, len(skills))
    
    SKILL_DEFS.clear()
    for s in skills:
        SKILL_DEFS[s.skill_id] = s
        
    logger.info("Loaded %d skills.", len(SKILL_DEFS))

def _load_breakthroughs(path: Path) -> None:
    if not path.exists():
        logger.warning("Breakthrough definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[BreakthroughDef])
    breakthroughs = adapter.validate_python(data)
    
    BREAKTHROUGHS.clear()
    for b in breakthroughs:
        BREAKTHROUGHS[b.from_class] = b
        
    logger.info("Loaded %d breakthroughs.", len(BREAKTHROUGHS))

def _load_traits(path: Path) -> None:
    if not path.exists():
        logger.warning("Trait definitions not found at %s", path)
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    adapter = TypeAdapter(list[TraitDef])
    traits = adapter.validate_python(data)
    
    TRAIT_DEFS.clear()
    for t in traits:
        TRAIT_DEFS[t.trait_type] = t
        
    logger.info("Loaded %d traits.", len(TRAIT_DEFS))
