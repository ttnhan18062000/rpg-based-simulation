# Compliance IDs: WORLD-PATH-001
from dataclasses import dataclass

@dataclass(frozen=True)
class ContentPathConfig:
    content_root: str = "data/content"
    world_modules_dir: str = "data/content/world_modules"
    simulation_scenarios_dir: str = "data/content/simulation_scenarios"
