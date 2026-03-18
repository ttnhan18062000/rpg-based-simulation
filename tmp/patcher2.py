import os

def patch_cleanup():
    path = "src/engine/world_loop.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'monument_' not in content:
        # Search for is_permadeath block
        target = 'self._schedule_hero_replacement(removed)\n                    continue'
        replacement = r'''# NEW: Monument spawning
                    if entity.stats.level >= 15:
                        m_id = f"monument_{entity.id}_{self._world.tick}"
                        from src.core.monuments import Monument
                        from src.core.enums import HeroClass
                        hc = entity.hero_class
                        bt = "hp"
                        if hc == HeroClass.WARRIOR: bt = "hp"
                        monument = Monument(m_id, entity.display_name or f"#{entity.id}", hc.name if hc else "NONE", 
                                            entity.stats.level, entity.home_pos, bt, 0.1)
                        self._world.monuments.append(monument)
                    self._schedule_hero_replacement(removed)
                    continue'''
        content = content.replace(target, replacement)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    print("Patched Cleanup")

patch_cleanup()
