import os

def patch_world_loop():
    path = "src/engine/world_loop.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if '_check_endgame_conditions' not in content:
        # Add methods at end of class
        if '    def _check_level_ups(self)' in content:
            new_methods = r'''
    def _update_world_evolution(self) -> None:
        self._world.world_age += 1
        self._world.difficulty_modifier = 1.0 + (self._world.world_age // 10000) * 0.1
        for f in [1, 2, 3]:
            agg = self._world.faction_aggression.get(f, 0.0)
            self._world.faction_aggression[f] = min(100.0, agg + 0.001)

    def _check_endgame_conditions(self) -> bool:
        if self._world.world_age < 50000: return True
        func = sum(1 for b in self._world.buildings if b.is_functional and b.durability > b.max_durability * 0.8)
        if func == len(self._world.buildings): return False
        dest = sum(1 for b in self._world.buildings if not b.is_functional)
        if dest >= 3: return False
        return True

    def _apply_monument_buffs(self, hero) -> None:
        for m in self._world.monuments:
            if m.buff_type == "hp":
                hero.stats.max_hp = int(hero.stats.max_hp * 1.1)
                hero.stats.hp = hero.stats.max_hp
            elif m.buff_type == "atk":
                hero.stats.atk = int(hero.stats.atk * 1.1)
'''
            content += new_methods
            # Add calls to _step
            content = content.replace('self._process_hero_replacements()', 'self._process_hero_replacements()\n        self._update_world_evolution()\n        self._check_endgame_conditions()')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
    print("Patched WorldLoop")

patch_world_loop()

def patch_resolver():
    path = "src/engine/conflict_resolver.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'RepairAction' not in content:
        content = content.replace('from src.actions.rest import RestAction', 'from src.actions.rest import RestAction\nfrom src.actions.repair import RepairAction')
        content = content.replace('match proposal.verb:', 'match proposal.verb:\n            case ActionType.REPAIR:\n                if RepairAction.validate(proposal, world):\n                    RepairAction.apply(proposal, world)\n                    return True')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    print("Patched ConflictResolver")

patch_resolver()
