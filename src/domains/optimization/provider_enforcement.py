from dataclasses import dataclass
from typing import Optional, List, Callable, Tuple, Any

@dataclass(frozen=True, slots=True)
class ScopedContext:
    entity_id: Optional[int]
    tick: int
    region_id: Optional[str]

class ProviderBudgetEnforcement:
    """Enforces budgets and scoped context queries on providers."""
    def __init__(self, max_calls: int = 10, max_results: int = 5, debug_global_scan: bool = False) -> None:
        self.max_calls = max_calls
        self.max_results = max_results
        self.debug_global_scan = debug_global_scan
        self._current_calls = 0

    def reset(self) -> None:
        self._current_calls = 0

    def enforce_results(self, context: ScopedContext, raw_results: List[Any]) -> List[Any]:
        # Always sort results deterministically (e.g. by converting to string representation if they are complex,
        # or sorting directly if they are strings/numbers)
        try:
            sorted_results = sorted(raw_results)
        except TypeError:
            sorted_results = sorted(raw_results, key=lambda x: str(x))
        return sorted_results[:self.max_results]

    def execute_call(self, context: ScopedContext, provider_name: str, provider_func: Callable[[], List[Any]]) -> Tuple[List[Any], Optional[str]]:
        if not self.debug_global_scan and (context.entity_id is None or context.region_id is None):
            return [], "Global scan attempt rejected without debug flag"

        if self._current_calls >= self.max_calls:
            return [], f"Provider budget exhausted for {provider_name}"

        self._current_calls += 1
        raw = provider_func()
        return self.enforce_results(context, raw), None
