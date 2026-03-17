import os

# I will use a very concise way to update the files by using open().write()
# I'll just restore the bits I need for Phase 3 to pass.

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Restored {path}")

# --- Building ---
write_file("src/core/buildings.py", r'''from __future__ import annotations
from dataclasses import dataclass
from src.core.models import Vector2

@dataclass
class Building:
    building_id: str
    name: str
    pos: Vector2
    durability: float = 100.0
    max_durability: float = 100.0
    is_functional: bool = True

    def take_damage(self, amount: float) -> None:
        self.durability = max(0.0, self.durability - amount)
        if self.durability <= 0: self.is_functional = False

    def repair(self, amount: float) -> None:
        self.durability = min(self.max_durability, self.durability + amount)
        if self.durability > 0: self.is_functional = True
''')

# --- WorldState ---
# I'll just check if I can append to the existing one instead of overwriting? 
# No, overwriting the top part is dangerous. I'll use a safer approach for existing files.
# Actually, I'll just write the version I know works for the tests.
# Wait, WorldState is huge. I'll use replace_file_content for existing files, but I'll be VERY careful.

# Actually, I'll use a python script to READ the file and REPLACE the slots/init.
def patch_world_state():
    path = "src/core/world_state.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'world_age' not in content:
        content = content.replace('__slots__ = (', '__slots__ = ("world_age", "faction_aggression", "difficulty_modifier", "monuments", ')
        content = content.replace('self.seed = seed', 'self.seed = seed\n        self.world_age = 0\n        self.faction_aggression = {}\n        self.difficulty_modifier = 1.0\n        self.monuments = []')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    print("Patched WorldState")

patch_world_state()

# I'll do the same for others if needed.
