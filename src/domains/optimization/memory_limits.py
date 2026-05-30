from dataclasses import dataclass
from typing import List, Dict, Set, Any

@dataclass(frozen=True, slots=True)
class MemoryFact:
    id: str
    salience: float
    timestamp: int

class MemoryCapacityLimits:
    """Manages memory/capacity hard limits and eviction policies."""
    def __init__(self, max_facts: int = 100, max_opponents: int = 50, max_rewards: int = 50, max_coop_memories: int = 50) -> None:
        self.max_facts = max_facts
        self.max_opponents = max_opponents
        self.max_rewards = max_rewards
        self.max_coop_memories = max_coop_memories

        self._facts: List[MemoryFact] = []
        self._opponents: Dict[str, float] = {}
        self._rewards: Dict[str, float] = {}
        self._coop_memories: Dict[str, float] = {}

        self._evicted_ids: Set[str] = set()

    def add_fact(self, fact: MemoryFact) -> None:
        self._facts.append(fact)
        if len(self._facts) > self.max_facts:
            # Sort ascending by salience, then timestamp to evict lowest salience first
            self._facts.sort(key=lambda f: (f.salience, f.timestamp))
            evicted = self._facts.pop(0)
            self._evicted_ids.add(evicted.id)

    def add_opponent(self, name: str, salience: float) -> None:
        self._opponents[name] = salience
        if len(self._opponents) > self.max_opponents:
            lowest_name = min(self._opponents, key=self._opponents.get)
            self._opponents.pop(lowest_name)
            self._evicted_ids.add(lowest_name)

    def add_reward(self, name: str, salience: float) -> None:
        self._rewards[name] = salience
        if len(self._rewards) > self.max_rewards:
            lowest_name = min(self._rewards, key=self._rewards.get)
            self._rewards.pop(lowest_name)
            self._evicted_ids.add(lowest_name)

    def add_coop_memory(self, name: str, salience: float) -> None:
        self._coop_memories[name] = salience
        if len(self._coop_memories) > self.max_coop_memories:
            lowest_name = min(self._coop_memories, key=self._coop_memories.get)
            self._coop_memories.pop(lowest_name)
            self._evicted_ids.add(lowest_name)

    def get_facts(self) -> List[MemoryFact]:
        return self._facts

    def get_opponents(self) -> Dict[str, float]:
        return self._opponents

    def get_rewards(self) -> Dict[str, float]:
        return self._rewards

    def get_coop_memories(self) -> Dict[str, float]:
        return self._coop_memories

    def generate_eviction_report(self) -> Dict[str, Any]:
        return {
            "evicted_count": len(self._evicted_ids),
            "evicted_ids": list(self._evicted_ids)
        }
