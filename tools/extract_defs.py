import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import TypeAdapter
import json

from src.core.items import ITEM_REGISTRY, ItemTemplate
from src.core.classes import CLASS_DEFS, SKILL_DEFS, BREAKTHROUGHS, ClassDef, SkillDef, BreakthroughDef
from src.core.traits import TRAIT_DEFS, TraitDef

data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

def dump_registry(registry: dict, model_type: type, filename: str):
    values = list(registry.values())
    adapter = TypeAdapter(list[model_type])
    json_bytes = adapter.dump_json(values, indent=2, by_alias=True)
    out_path = data_dir / filename
    out_path.write_bytes(json_bytes)
    print(f"Dumped {len(values)} items to {out_path}")

try:
    dump_registry(ITEM_REGISTRY, ItemTemplate, "items.json")
    dump_registry(CLASS_DEFS, ClassDef, "classes.json")
    dump_registry(SKILL_DEFS, SkillDef, "skills.json")
    dump_registry(BREAKTHROUGHS, BreakthroughDef, "breakthroughs.json")
    dump_registry(TRAIT_DEFS, TraitDef, "traits.json")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
