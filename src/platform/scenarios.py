
class ScenarioRegistry:
    _registry = {}

    @classmethod
    def register(cls, scenario_id: str, builder):
        cls._registry[scenario_id] = builder

    @classmethod
    def get(cls, scenario_id: str):
        return cls._registry.get(scenario_id)

    @classmethod
    def all(cls):
        return dict(cls._registry)
