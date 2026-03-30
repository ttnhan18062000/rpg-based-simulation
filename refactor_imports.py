
import os
import re

test_dir = "tests"
replacements = [
    (r"from src\.core\.attributes import (.*)", r"from src.core.gameplay.attributes import \1"),
    (r"from src\.core\.entity_builder import (.*)", r"from src.core.entities.entity_builder import \1"),
    (r"from src\.core\.enums import (.*)", r"from src.core.models.enums import \1"),
    (r"from src\.core\.faction import (.*)", r"from src.core.gameplay.faction import \1"),
    (r"from src\.core\.grid import (.*)", r"from src.core.world.grid import \1"),
    (r"from src\.core\.models import (.*Entity.*Stats.*Vector2.*|.*Entity.*Vector2.*Stats.*|.*Stats.*Entity.*Vector2.*|.*Stats.*Vector2.*Entity.*|.*Vector2.*Entity.*Stats.*|.*Vector2.*Stats.*Entity.*)", 
     r"from src.core.entities.entity import Entity\nfrom src.core.models.vectors import Vector2"),
    (r"from src\.core\.models import (.*Vector2.*)", r"from src.core.models.vectors import Vector2"),
    (r"from src\.core\.world_state import (.*)", r"from src.core.models.world_state import \1"),
    (r"from src\.core\.classes import (.*)", r"from src.core.gameplay.classes import \1"),
    (r"from src\.core\.regions import (.*)", r"from src.core.world.regions import \1"),
    (r"from src\.core\.snapshot import (.*)", r"from src.core.models.snapshot import \1"),
    (r"from src\.core\.items import (.*)", r"from src.core.gameplay.items.items import \1"),
    (r"from src\.systems\.generator import (.*)", r"from src.systems.world.generator import \1"),
    (r"from src\.core\.buildings import (.*)", r"from src.core.gameplay.buildings import \1"),
]

for filename in os.listdir(test_dir):
    if filename.startswith("test_") and filename.endswith(".py"):
        filepath = os.path.join(test_dir, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        new_content = content
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, new_content)
        
        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated {filename}")
