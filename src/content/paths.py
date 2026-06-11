# Compliance IDs: WORLD-PATH-001
from dataclasses import dataclass

@dataclass(frozen=True)
class ContentPathConfig:
    content_root: str = "data/content"
    world_modules_dir: str = "data/content/world_modules"
    world_compositions_dir: str = "data/content/world_compositions"
    simulation_scenarios_dir: str = "data/content/simulation_scenarios"
