import src.core.registries
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.engine.legality import LegalityServiceV2 as L
from src.systems.world_systems.generator import EntityGenerator
import src.systems.world_systems.generator as g
def hero(i,pos): return V2EntityBuilder(i).kind("hero").location(*pos).identity(role=EntityRole.HERO,faction=Faction.HERO_GUILD).combat(hp=100,max_hp=100,atk=10,def_stat=5,readiness=100.0,attack_range=1.5).build()
for fix in (False,True):
  if not fix: saved=dict(g.SPAWN_KIND_CATALOG_FACTION); g.SPAWN_KIND_CATALOG_FACTION.clear()
  else: g.SPAWN_KIND_CATALOG_FACTION.update(saved)
  for kind in ("wolf","bear","golem","goblin_warrior","orc_warrior","dragonkin","bandit"):
    gen=EntityGenerator(1); m=gen.spawn_monster((6.0,5.0),kind=kind); m=m.__class__(**{**m.__dict__,"id":900}) if False else m
    h=hero(1000,(5.0,5.0))
    st=AuthoritativeState(tick=5,seed=1,entities={h.id:h,m.id:m})
    try: r1=L.verify_attack_legality(h,m,st)
    except Exception as e: r1=repr(e)[:80]
    try: r2=L.verify_attack_legality(m,h,st)
    except Exception as e: r2=repr(e)[:80]
    print(fix,kind,"hero->mob",r1,"mob->hero",r2)
