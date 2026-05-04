from __future__ import annotations
from dataclasses import replace
from typing import Any, Dict, List, Optional, Set

from src.core.state import (
    EntityState,
    IdentityComponent,
    CombatComponent,
    InventoryComponent,
    LifecycleComponent,
    BiologicalComponent,
    SocialComponent,
    NavigationComponent,
    InteractionComponent,
    TaskComponent,
    AptitudeComponent,
    AptitudeComponent,
    AttributeComponent,
    EquipmentComponent,
    EquipSlot,
    ItemStack,
    StaminaComponent,
    PersonalityComponent,
    LifeStage,
    SocialBond
)
from src.core.strategic import (
    StrategicComponent, ProjectState, ProjectStatus, 
    ObjectiveState, ObjectiveStatus, BlockerState, 
    LeadState, DirectiveState, CognitionProfile,
    SourceTrustEntry, TurningPointState
)
from src.core.movement_modes import MovementMode
from src.core.enums import EntityRole, Faction
from src.core.classes import CLASS_REGISTRY

class V2EntityBuilder:
    """
    Fluent builder for V2 EntityState construction.
    Maintains API parity with legacy EntityBuilder while producing frozen EntityState.
    VERIFIED v2: entity_builder_serialization
    """

    def __init__(self, entity_id: int, tick: int = 0) -> None:
        self._eid = entity_id
        self._tick = tick
        
        # Identity
        self._kind = "HERO"
        self._role = EntityRole.HERO
        self._faction = Faction.HERO_GUILD
        self._evolution_level = 1
        self._evolution_points = 0
        self._class_id = "NOVICE"
        self._learned_skills: Set[str] = set()
        self._starting_gear: Dict[str, str] = {}
        self._personality = PersonalityComponent()
        self._life_stage = LifeStage.ADULT
        
        # Strategic
        self._contracts: Dict[str, ContractState] = {}
        self._directives: Dict[str, DirectiveState] = {}
        self._leads: Dict[str, LeadState] = {}
        self._projects: Dict[str, ProjectState] = {}
        self._current_project_id: Optional[str] = None
        self._turning_points: List[TurningPointState] = []
        self._source_trust: Dict[int, SourceTrustEntry] = {}
        
        # Spatial
        self._pos = (0.0, 0.0)
        self._readiness = 100.0
        
        # Combat
        self._hp_base = 100
        self._hp_current = 100
        self._atk_base = 10
        self._def_base = 5
        self._items = []
        self._starting_gear = {}
        self._durability = {}
        self._max_slots = 10
        self._speed = 10
        self._range = 1
        self._evasion = 0.05
        self._tactical_role = "VANGUARD"
        self._action_style = 0 # ActionStyle.BALANCED
        self._hp_explicit = False
        
        # Navigation Advanced
        self._target: Optional[tuple[float, float]] = None
        self._home_pos: Optional[tuple[float, float]] = None
        self._leash_radius = 0.0
        self._movement_mode = MovementMode.WANDER
        self._evolution_level = 1
        self._evolution_points = 0
        self._unspent_ap = 0
        self._str_apt = 1.0
        self._vit_apt = 1.0
        self._agi_apt = 1.0
        self._int_apt = 1.0
        self._end_apt = 1.0
        self._last_position: Optional[tuple[float, float]] = None
        self._oscillation_count = 0
        self._wait_count = 0
        self._interruption_resistance = 0.3
        self._detour_breadth = 3
        self._detour_depth = 2
        self._max_active_projects = 3
        self._max_leads = 8
        self._max_concerns = 5
        self._max_candidate_zones = 4
        self._max_hypotheses = 3
        
        # Inventory
        self._max_slots = 16
        self._max_weight = 50
        self._gold = 0
        self._items: List[ItemStack] = []
        
        # Lifecycle / Biological
        self._generation = 1
        self._age_ticks = 0
        self._is_permadeath = False
        self._active = True
        self._alive = True
        self._hunger = 0.0
        self._sleep_debt = 0.0
        self._trust_history: Dict[int, float] = {}
        self._betrayal_count = 0
        self._bonds: Dict[int, SocialBond] = {}
        self._action_style = 0
        
        # Attributes (Default 5 as per legacy)
        self._str = 5
        self._agi = 5
        self._vit = 5
        self._end = 5
        self._stamina_current = 100.0
        self._stamina_max = 100.0
        
        # Aptitudes
        self._str_apt = 1.0
        self._int_apt = 1.0
        self._agi_apt = 1.0
        self._vit_apt = 1.0
        self._end_apt = 1.0
        self._int = 5
        self._spi = 5
        self._wis = 5
        self._end = 5
        self._per = 5
        self._cha = 5
        
        # Components
        self._properties: Dict[str, Any] = {}
        self._target: Optional[tuple[float, float]] = None
        self._home_pos: Optional[tuple[float, float]] = None
        self._leash_radius: float = 0.0
        
        # Interaction
        self._target_node_id: Optional[int] = None
        self._interaction_progress: float = 0.0
        self._interaction_target_id: Optional[int] = None
        
        # Strategic
        self._directives: Dict[str, DirectiveState] = {}
        self._projects: Dict[str, ProjectState] = {}
        self._current_project_id: Optional[str] = None
        self._contracts: Dict[str, ContractState] = {}
        self._blockers: Dict[str, BlockerState] = {}
        self._concerns: Dict[str, ConcernState] = {}
        self._leads: Dict[str, LeadState] = {}
        self._turning_points: Dict[str, TurningPointState] = {}
        self._source_trust: Dict[int, SourceTrustEntry] = {}
        self._move_cost = 10.0
        self._public_reputation = 1.0
        self._heroism_score = 0.0
        self._notoriety_score = 0.0

    def kind(self, k: str) -> V2EntityBuilder:
        self._kind = k
        k_up = k.upper()
        if k_up == "MONSTER" or "GOBLIN" in k_up or "ORC" in k_up or "WOLF" in k_up:
            self._role = EntityRole.MONSTER
            self._faction = Faction.MONSTER_HORDE
        elif k_up == "HERO" or "LEGEND" in k_up:
            self._role = EntityRole.HERO
            self._faction = Faction.HERO_GUILD
        return self

    def role(self, r: int | EntityRole) -> V2EntityBuilder:
        # Map legacy int roles to V2 Enums if possible
        if isinstance(r, int):
            try:
                self._role = EntityRole(r)
            except ValueError:
                # Fallback or keep as int if Enums differ
                self._role = r
        else:
            self._role = r
        return self

    def faction(self, f: int | Faction) -> V2EntityBuilder:
        if isinstance(f, int):
            try:
                self._faction = Faction(f)
            except (ValueError, TypeError):
                # If it's a legacy int that doesn't map, just use it
                self._faction = f
        else:
            self._faction = f
        return self

    def evolution_level(self, level: int) -> V2EntityBuilder:
        self._evolution_level = level
        return self

    def personality(self, p: PersonalityComponent) -> V2EntityBuilder:
        self._personality = p
        return self

    def with_personality(self, greed: float = 0.0, bravery: float = 0.0, 
                         sociability: float = 0.0, industry: float = 0.0) -> V2EntityBuilder:
        self._personality = PersonalityComponent(
            greed=greed, bravery=bravery, 
            sociability=sociability, industry=industry
        )
        return self

    def life_stage(self, ls: LifeStage) -> V2EntityBuilder:
        self._life_stage = ls
        return self

    def trait(self, t: str | Set[str]) -> V2EntityBuilder:
        if not hasattr(self, "_traits"):
            self._traits: Set[str] = set()
        if isinstance(t, str):
            self._traits.add(t)
        else:
            self._traits.update(t)
        return self

    def with_identity(self, role: EntityRole = None, faction: Faction = None, 
                      evolution_level: int = None, evolution_points: int = 0) -> V2EntityBuilder:
        if role is not None: self._role = role
        if faction is not None: self._faction = faction
        if evolution_level is not None: self._evolution_level = evolution_level
        self._evolution_points = evolution_points
        return self

    def with_combat(self, atk: int = None, def_stat: int = None, 
                    range: int = None, evasion: float = None,
                    speed: int = None, alive: bool = True,
                    hp: int = None, max_hp: int = None,
                    move_cost: float = None) -> V2EntityBuilder:
        if atk is not None: self._atk_base = atk
        if def_stat is not None: self._def_base = def_stat
        if range is not None: self._range = range
        if evasion is not None: self._evasion = evasion
        if speed is not None: self._speed = speed
        if hp is not None:
            self._hp_current = hp
            self._hp_explicit = True
        if move_cost is not None:
            self._move_cost = move_cost
        if max_hp is not None:
            self._hp_base = max_hp
        self._alive = alive
        return self

    def move_cost(self, val: float) -> V2EntityBuilder:
        self._move_cost = val
        return self

    def hp(self, current: int, max_hp: int = None) -> V2EntityBuilder:
        self._hp_base = max_hp if max_hp is not None else current
        self._hp_current = current
        self._hp_explicit = True
        return self

    def atk(self, val: int) -> V2EntityBuilder:
        self._atk_base = val
        return self

    def def_stat(self, val: int) -> V2EntityBuilder:
        self._def_base = val
        return self

    def skills(self, learned_skills: Set[str]) -> V2EntityBuilder:
        self._learned_skills = learned_skills
        return self

    def cooldowns(self, cooldown_dict: Dict[str, int]) -> V2EntityBuilder:
        if not hasattr(self, "_cooldown_updates"):
            self._cooldown_updates: Dict[str, int] = {}
        self._cooldown_updates.update(cooldown_dict)
        return self

    def with_lifecycle(self, generation: int = 1, age_ticks: int = 0) -> V2EntityBuilder:
        self._generation = generation
        self._age_ticks = age_ticks
        return self

    def with_biological(self, sleep_debt: float = None, hunger: float = None) -> V2EntityBuilder:
        if sleep_debt is not None: self._sleep_debt = sleep_debt
        if hunger is not None: self._hunger = hunger
        return self

    def biological(self, sleep_debt: float = None, hunger: float = None) -> V2EntityBuilder:
        """Alias for with_biological."""
        return self.with_biological(sleep_debt=sleep_debt, hunger=hunger)

    def sleep_debt(self, val: float) -> V2EntityBuilder:
        self._sleep_debt = val
        return self

    def evolution(self, level: int = 1, points: int = 0, unspent_ap: int = 0) -> V2EntityBuilder:
        self._evolution_level = level
        self._evolution_points = points
        self._unspent_ap = unspent_ap
        return self

    def aptitude(self, str_apt: float = 1.0, vit_apt: float = 1.0, agi_apt: float = 1.0, int_apt: float = 1.0, end_apt: float = 1.0) -> V2EntityBuilder:
        self._str_apt = str_apt
        self._vit_apt = vit_apt
        self._agi_apt = agi_apt
        self._int_apt = int_apt
        self._end_apt = end_apt
        return self

    def with_aptitude(self, str_apt: float = 1.0, vit_apt: float = 1.0, agi_apt: float = 1.0, int_apt: float = 1.0, end_apt: float = 1.0) -> V2EntityBuilder:
        return self.aptitude(str_apt, vit_apt, agi_apt, int_apt, end_apt)

    def with_aptitudes(self, str_apt: float = 1.0, vit_apt: float = 1.0, agi_apt: float = 1.0, int_apt: float = 1.0, end_apt: float = 1.0) -> V2EntityBuilder:
        return self.aptitude(str_apt, vit_apt, agi_apt, int_apt, end_apt)

    def hunger(self, val: float) -> V2EntityBuilder:
        self._hunger = val
        return self

    def with_inventory(self, gold: int = None, items: List[ItemStack] = None, max_slots: int = 10, max_weight: float = 100.0) -> V2EntityBuilder:
        if gold is not None: self._gold = gold
        if items is not None: self._items = items
        self._max_slots = max_slots
        if max_weight is not None: self._max_weight = max_weight
        return self

    def with_equipment(self, slots: Dict[EquipSlot, str] = None, durability: Dict[EquipSlot, float] = None) -> V2EntityBuilder:
        if slots:
            self._starting_gear.update({k.name if isinstance(k, EquipSlot) else str(k): v for k, v in slots.items()})
        if durability:
            self._durability.update({k.name if isinstance(k, EquipSlot) else str(k): v for k, v in durability.items()})
        return self

    def social_bond(self, target_or_bond: int | SocialBond, sentiment: float = 0.0) -> V2EntityBuilder:
        if not hasattr(self, "_bonds"):
            self._bonds = {}
        
        if isinstance(target_or_bond, SocialBond):
            self._bonds[target_or_bond.target_id] = target_or_bond
        else:
            self._bonds[target_or_bond] = SocialBond(target_id=target_or_bond, sentiment=sentiment)
        return self

    def with_task(self, kind: str, payload: Dict[str, Any]) -> V2EntityBuilder:
        self._task_kind = kind
        self._task_payload = payload
        return self

    def with_navigation(self, target: tuple[float, float] = None, 
                        home_position: tuple[float, float] = None,
                        leash_radius: float = None,
                        mode: MovementMode = None,
                        wait_count: int = None,
                        last_pos: tuple[float, float] = None,
                        oscillation_count: int = None) -> V2EntityBuilder:
        if target is not None: self._target = target
        if home_position is not None: self._home_pos = home_position
        if leash_radius is not None: self._leash_radius = leash_radius
        if mode is not None: self._movement_mode = mode
        if wait_count is not None: self._wait_count = wait_count
        if last_pos is not None: self._last_position = last_pos
        if oscillation_count is not None: self._oscillation_count = oscillation_count
        return self

    def at(self, pos: tuple[float, float] | list[float]) -> V2EntityBuilder:
        self._pos = tuple(pos)
        return self

    def position(self, *args) -> V2EntityBuilder:
        if len(args) == 1:
            return self.at(args[0])
        elif len(args) == 2:
            return self.at((args[0], args[1]))
        else:
            raise TypeError(f"position() takes 1 or 2 positional arguments but {len(args)} were given")

    def readiness(self, val: float) -> V2EntityBuilder:
        self._readiness = val
        return self

    def action_style(self, style: int) -> V2EntityBuilder:
        self._action_style = style
        return self

    def group_id(self, g_id: Optional[int]) -> V2EntityBuilder:
        self._group_id = g_id
        return self

    def trust(self, target_id: int, score: float) -> V2EntityBuilder:
        self._trust_history[target_id] = score
        return self

    def betrayal_count(self, count: int) -> V2EntityBuilder:
        self._betrayal_count = count
        return self

    def bond(self, b: SocialBond) -> V2EntityBuilder:
        self._bonds[b.target_id] = b
        return self

    def bonds(self, bond_dict: Dict[int, SocialBond]) -> V2EntityBuilder:
        self._bonds.update(bond_dict)
        return self

    def gold(self, amount: int) -> V2EntityBuilder:
        self._gold = amount
        return self

    def max_slots(self, val: int) -> V2EntityBuilder:
        self._max_slots = val
        return self

    def item(self, item_id: str, quantity: int = 1) -> V2EntityBuilder:
        self._items.append(ItemStack(item_id=item_id, quantity=quantity))
        return self
        
    def items(self, item_list: List[ItemStack]) -> V2EntityBuilder:
        self._items = list(item_list)
        return self

    def target(self, pos: tuple[float, float] | None) -> V2EntityBuilder:
        self._target = pos
        return self

    def home_pos(self, x: float, y: float) -> V2EntityBuilder:
        self._home_pos = (x, y)
        return self

    def movement_mode(self, mode: MovementMode) -> V2EntityBuilder:
        self._movement_mode = mode
        return self

    def strength(self, val: int) -> V2EntityBuilder:
        self._str = val
        return self

    def agility(self, val: int) -> V2EntityBuilder:
        self._agi = val
        return self

    def vitality(self, val: int) -> V2EntityBuilder:
        self._vit = val
        return self

    def endurance(self, val: int) -> V2EntityBuilder:
        self._end = val
        return self

    def leash_radius(self, val: float) -> V2EntityBuilder:
        self._leash_radius = val
        return self

    def with_strategic(self, contracts: Dict[str, ContractState] = None, 
                       directives: Dict[str, DirectiveState] = None,
                       leads: Dict[str, LeadState] = None,
                       projects: Dict[str, ProjectState] = None,
                       blockers: Dict[str, BlockerState] = None,
                       concerns: Dict[str, ConcernState] = None) -> V2EntityBuilder:
        if contracts is not None: self._contracts = contracts
        if directives is not None: self._directives = directives
        if leads is not None: self._leads = leads
        if projects is not None: self._projects = projects
        if blockers is not None: self._blockers = blockers
        if concerns is not None: self._concerns = concerns
        return self

    def with_strategic_profile(self, max_projects: int = None, max_leads: int = None,
                               max_concerns: int = None, max_zones: int = None,
                               max_hypotheses: int = None, resistance: float = None,
                               breadth: int = None, depth: int = None) -> V2EntityBuilder:
        if max_projects is not None: self._max_active_projects = max_projects
        if max_leads is not None: self._max_leads = max_leads
        if max_concerns is not None: self._max_concerns = max_concerns
        if max_zones is not None: self._max_candidate_zones = max_zones
        if max_hypotheses is not None: self._max_hypotheses = max_hypotheses
        if resistance is not None: self._interruption_resistance = resistance
        if breadth is not None: self._detour_breadth = breadth
        if depth is not None: self._detour_depth = depth
        return self

    def with_objective(self, objective_id: str) -> V2EntityBuilder:
        self._current_objective_id = objective_id
        return self

    def source_trust(self, source_id: int, trust: float, interactions: int = 0) -> V2EntityBuilder:
        self._source_trust[source_id] = SourceTrustEntry(
            entity_id=source_id, trust=trust, interactions=interactions
        )
        return self

    def strategic_project(self, project: ProjectState) -> V2EntityBuilder:
        self._projects[project.id] = project
        return self

    def strategic_contract(self, contract: ContractState) -> V2EntityBuilder:
        self._contracts[contract.id] = contract
        return self

    def strategic_directive(self, directive: DirectiveState) -> V2EntityBuilder:
        self._directives[directive.id] = directive
        return self

    def current_project(self, project_id: str) -> V2EntityBuilder:
        self._current_project_id = project_id
        return self

    def cognition(self, interruption_resistance: float = 0.5, detour_breadth: int = 3) -> V2EntityBuilder:
        self._interruption_resistance = interruption_resistance
        self._detour_breadth = detour_breadth
        return self

    def with_interaction(self, target_id: int = None, progress: float = 0.0) -> V2EntityBuilder:
        self._target_node_id = target_id
        self._interaction_progress = progress
        return self


    def with_class(self, class_id: str) -> V2EntityBuilder:
        if class_id in CLASS_REGISTRY:
            self._class_id = class_id
            defn = CLASS_REGISTRY[class_id]
            self._hp_base = defn.base_hp
            self._atk_base = defn.base_atk
            self._def_base = defn.base_def
            self._learned_skills = set(defn.starting_skills)
            self._starting_gear = dict(defn.starting_gear)
        return self

    def with_base_stats(self, hp: int = 100, atk: int = 10, def_stat: int = 5, 
                        range: int = 1, evasion: float = 0.05, 
                        tactical_role: str = "VANGUARD",
                        action_style: int = 0) -> V2EntityBuilder:
        self._hp_base = hp
        self._atk_base = atk
        self._def_base = def_stat
        self._range = range
        self._evasion = evasion
        self._tactical_role = tactical_role
        self._action_style = action_style
        return self

    def monster(self, race: str, tier: int = 0) -> V2EntityBuilder:
        """Helper for standard monster construction."""
        self._kind = f"{race}_{tier}" # e.g. goblin_0
        self._role = EntityRole.MONSTER
        self._faction = Faction.MONSTER_HORDE
        
        # Simple tier-based scaling
        self._hp_base = 50 + (tier * 50)
        self._atk_base = 5 + (tier * 5)
        self._def_base = 2 + (tier * 3)
        
        # Loadout mapping (Placeholder)
        if race == "goblin":
            if tier == 0:
                self._starting_gear = {"MAIN_HAND": "wooden_club"}
            elif tier == 1:
                self._starting_gear = {"MAIN_HAND": "iron_sword", "TORSO": "leather_armor"}
        
        return self

    def with_attributes(self, **kwargs) -> V2EntityBuilder:
        """Sets specific attribute values with long-to-short mapping."""
        mapping = {
            "strength": "_str",
            "agility": "_agi",
            "vitality": "_vit",
            "endurance": "_end",
            "intelligence": "_int",
            "spirit": "_spi",
            "wisdom": "_wis",
            "perception": "_per",
            "charisma": "_cha"
        }
        for k, v in kwargs.items():
            attr_name = mapping.get(k, f"_{k}")
            if hasattr(self, attr_name):
                setattr(self, attr_name, int(v))
        return self

    def with_aptitudes(self, **kwargs) -> V2EntityBuilder:
        """Sets specific aptitude values."""
        for k, v in kwargs.items():
            attr_name = f"_{k}_apt"
            if hasattr(self, attr_name):
                setattr(self, attr_name, float(v))
        return self


    def with_inventory_component(self, inv: InventoryComponent) -> V2EntityBuilder:
        self._gold = inv.gold
        self._max_slots = inv.max_slots
        self._max_weight = inv.max_weight
        # Convert ItemStack list back to item_id list for internal storage
        self._items = [item.item_id for item in inv.items]
        return self

    def with_inventory_v2(self, max_slots: int = 16, max_weight: float = 50.0) -> V2EntityBuilder:
        """Testing helper for V2 inventory schema."""
        self._max_slots = max_slots
        self._max_weight = max_weight
        return self

    def with_navigation_v2(self, mode: MovementMode = MovementMode.WANDER, 
                           last_pos: tuple[float, float] | None = None,
                           oscillation_count: int = 0) -> V2EntityBuilder:
        """Testing helper for V2 navigation schema."""
        self._movement_mode = mode
        self._last_position = last_pos
        self._oscillation_count = oscillation_count
        return self

    def social(self, public_reputation: float = None, heroism: float = None, notoriety: float = None) -> V2EntityBuilder:
        if public_reputation is not None: self._public_reputation = public_reputation
        if heroism is not None: self._heroism_score = heroism
        if notoriety is not None: self._notoriety_score = notoriety
        return self

    def social_rejection(self, source_id: int, count: int) -> V2EntityBuilder:
        # We'll need to handle this in build() or add a _rejections dict
        if not hasattr(self, "_rejections"):
            self._rejections: Dict[int, int] = {}
        self._rejections[source_id] = count
        return self


    def task(self, kind: str, payload: Dict[str, Any]) -> V2EntityBuilder:
        self._task_kind = kind
        self._task_payload = payload
        return self

    def tactical_role(self, role: str) -> V2EntityBuilder:
        self._tactical_role = role
        return self



    def with_property(self, key: str, value: Any) -> V2EntityBuilder:
        self._properties[key] = value
        return self

    def with_properties(self, props: Dict[str, Any]) -> V2EntityBuilder:
        self._properties.update(props)
        return self

    def with_current_hp(self, hp: int) -> V2EntityBuilder:
        self._hp_base = hp
        return self

    def stamina(self, current: float, max_stamina: float = 100.0) -> V2EntityBuilder:
        self._stamina_current = current
        self._stamina_max = max_stamina
        return self

    def attributes(self, **kwargs) -> V2EntityBuilder:
        """Alias for with_attributes."""
        return self.with_attributes(**kwargs)

    def alive(self, is_alive: bool) -> V2EntityBuilder:
        self._alive = is_alive
        return self

    def with_contract(self, contract_id: str, contract: ContractState) -> V2EntityBuilder:
        self._contracts[contract_id] = contract
        return self

    def with_directive(self, directive: DirectiveState) -> V2EntityBuilder:
        self._directives[directive.id] = directive
        return self

    def active(self, is_active: bool) -> V2EntityBuilder:
        self._active = is_active
        return self

    def _recalc(self):
        """Mimics legacy recalc_derived_stats for initial build."""
        self._max_hp_calc = self._hp_base + (self._vit * 2) + int(self._end * 0.5)
        self._hp_calc = self._hp_current
        if not getattr(self, "_hp_explicit", False):
            self._hp_calc = self._max_hp_calc # Built entities start at full health
        self._atk_calc = self._atk_base + int(self._str * 0.5)
        self._def_calc = self._def_base + int(self._vit * 0.3)

    def build(self) -> EntityState:
        """Constructs the frozen EntityState."""
        self._recalc()
        return EntityState(
            id=self._eid,
            kind=self._kind,
            identity=IdentityComponent(
                role=self._role,
                faction=self._faction,
                evolution_level=self._evolution_level,
                evolution_points=self._evolution_points,
                unspent_ap=self._unspent_ap,
                class_id=self._class_id,
                learned_skills=self._learned_skills,
                traits=getattr(self, "_traits", set()),
                personality=self._personality,
                life_stage=self._life_stage,
                cooldowns=getattr(self, "_cooldown_updates", {}),
                group_id=getattr(self, "_group_id", None),
                properties=self._properties
            ),
            attributes=AttributeComponent(
                strength=self._str,
                agility=self._agi,
                vitality=self._vit,
                endurance=self._end,
                intelligence=self._int,
                spirit=self._spi,
                wisdom=self._wis,
                perception=self._per,
                charisma=self._cha
            ),
            combat=CombatComponent(
                hp=self._hp_calc,
                max_hp=self._max_hp_calc,
                atk=self._atk_calc,
                def_stat=self._def_calc,
                speed=self._speed,
                range=self._range,
                evasion=self._evasion,
                tactical_role=self._tactical_role,
                action_style=self._action_style,
                alive=self._alive and (self._hp_calc > 0),
                readiness=self._readiness,
                move_cost=self._move_cost
            ),
            inventory=InventoryComponent(
                max_slots=self._max_slots,
                max_weight=self._max_weight,
                gold=self._gold,
                items=[i if isinstance(i, ItemStack) else ItemStack(item_id=i, quantity=1) for i in self._items]
            ),
            lifecycle=LifecycleComponent(
                generation=self._generation,
                age_ticks=self._age_ticks,
                is_permadeath=self._is_permadeath,
                active=self._active
            ),
            equipment=EquipmentComponent(
                slots={EquipSlot[k] if isinstance(k, str) else k: v for k, v in self._starting_gear.items()},
                durability={EquipSlot[k] if isinstance(k, str) else k: v for k, v in self._durability.items()}
            ),
            aptitude=AptitudeComponent(
                learning_rate=self._int_apt,
                stamina_efficiency=self._vit_apt,
                str_apt=self._str_apt,
                vit_apt=self._vit_apt,
                end_apt=self._end_apt
            ),
            navigation=NavigationComponent(
                position=self._pos,
                target=self._target,
                home_position=self._home_pos or self._pos,
                leash_radius=self._leash_radius,
                movement_mode=self._movement_mode,
                wait_count=self._wait_count,
                last_position=self._last_position,
                oscillation_count=self._oscillation_count
            ),
            strategic=StrategicComponent(
                profile=CognitionProfile(
                    max_active_projects=self._max_active_projects,
                    max_leads=self._max_leads,
                    max_concerns=self._max_concerns,
                    max_candidate_zones=self._max_candidate_zones,
                    max_hypotheses=self._max_hypotheses,
                    interruption_resistance=self._interruption_resistance,
                    detour_breadth=self._detour_breadth,
                    detour_depth=self._detour_depth
                ),
                directives=self._directives,
                projects=self._projects,
                current_project_id=self._current_project_id,
                contracts=self._contracts,
                blockers=self._blockers,
                concerns=self._concerns,
                leads=self._leads,
                turning_points=self._turning_points,
                source_trust=self._source_trust
            ),
            interaction=InteractionComponent(
                target_node_id=self._target_node_id,
                progress=self._interaction_progress
            ),
            biological=BiologicalComponent(
                hunger=self._hunger,
                sleep_debt=self._sleep_debt
            ),
            social=SocialComponent(
                public_reputation=self._public_reputation,
                heroism_score=self._heroism_score,
                notoriety_score=self._notoriety_score,
                bonds=self._bonds,
                trust_history=self._trust_history,
                betrayal_count=self._betrayal_count,
                rejection_count=getattr(self, "_rejections", {})
            ),
            task=TaskComponent(
                work_kind=getattr(self, "_task_kind", "REST"),
                payload=getattr(self, "_task_payload", {})
            ),
            stamina=StaminaComponent(
                current=self._stamina_current,
                max_stamina=self._stamina_max
            )
        )

    def group_id(self, g_id: Optional[int]) -> V2EntityBuilder:
        self._group_id = g_id
        return self
