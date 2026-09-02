from pydantic import BaseModel, Field, ConfigDict


class SystemCadence(BaseModel):
    model_config = ConfigDict(frozen=True)
    """
    Defines the execution frequency (in ticks) for various engine subsystems.
    A cadence of 1 means the system runs every tick.
    A cadence of N means the system runs every N ticks.
    """
    # Core (Usually 1)
    movement: int = Field(1, ge=1)
    combat: int = Field(1, ge=1)
    interaction: int = Field(1, ge=1)
    resource_transactions: int = Field(1, ge=1)

    # Medium Frequency
    shop: int = Field(1, ge=1)
    town_resolution: int = Field(1, ge=1)
    lifecycle: int = Field(1, ge=1)
    biological: int = Field(1, ge=1)
    groups: int = Field(1, ge=1)

    # Strategic / Cognition (High Cost)
    strategic_intelligence: int = Field(10, ge=1)
    concern_evaluation: int = Field(10, ge=1)
    detour_suggestion: int = Field(10, ge=1)
    social_memory: int = Field(10, ge=1)
    faction_decision: int = Field(10, ge=1)

    # World / Environmental (Very Slow)
    world_dynamics: int = Field(50, ge=1)
    ecology: int = Field(100, ge=1)
    building_sabotage: int = Field(100, ge=1)
    boss_spawn: int = Field(100, ge=1)
    reproduction_humanoid: int = Field(200, ge=1)


def should_run(tick: int, entity_id: int | None, cadence: int) -> bool:
    """
    Determines if a system should run for a given tick and entity.
    
    If entity_id is provided, execution is staggered across ticks based on the ID
    to prevent "spikes" where all entities run expensive logic on the same tick.
    """
    if cadence <= 1:
        return True

    if entity_id is None:
        # Global system (e.g. WorldDynamics)
        return tick % cadence == 0

    # Entity-specific system (e.g. StrategicIntelligence)
    # Staggered by entity_id
    return (tick + entity_id) % cadence == 0
