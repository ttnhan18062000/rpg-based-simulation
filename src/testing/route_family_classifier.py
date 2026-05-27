from typing import Any, List, Set, Dict


class RouteFamilyClassifier:
    """
    RouteFamilyClassifier classifies low-level trace events and ActionIntent logs
    into high-level route families and detects forbidden behaviors.
    """

    @staticmethod
    def classify(traces: List[Any]) -> Set[str]:
        families: Set[str] = set()
        
        for trace in traces:
            kind = getattr(trace, "intent_kind", None)
            if kind is None and isinstance(trace, dict):
                kind = trace.get("intent_kind") or trace.get("selected_route_family")
            
            result = getattr(trace, "execution_result", None)
            if result is None and isinstance(trace, dict):
                result = trace.get("execution_result") or ""
            
            # Convert result to string
            result = str(result)

            # 1. Classify Route Families
            if "FAILED_REQUIREMENTS" in result or "defer_with_reason" in str(kind):
                families.add("defer_with_reason")
            
            if kind == "ASK_INFORMATION":
                families.add("ask_information")
            elif kind == "REQUEST_CRAFT":
                families.add("craft_upgrade")
            elif kind == "BUY_ITEM":
                families.add("buy_upgrade")
            elif kind == "HARVEST_RESOURCE":
                families.add("gather_for_gold")
            elif kind == "ATTACK_TARGET":
                families.add("hunt_weak_enemy")
            elif kind in ("REST_AT_INN", "REST", "SLEEP", "EAT"):
                families.add("recover")

        if not families:
            families.add("defer_with_reason")

        return families

    @staticmethod
    def detect_forbidden(traces: List[Any], known_leads: Set[str] = None) -> List[str]:
        forbidden: List[str] = []
        if not traces:
            return forbidden

        # 1. Infinite same failed action detection
        consecutive_failures = 0
        last_failed_kind = None
        for trace in traces:
            kind = getattr(trace, "intent_kind", None)
            if kind is None and isinstance(trace, dict):
                kind = trace.get("intent_kind")
            
            result = getattr(trace, "execution_result", None)
            if result is None and isinstance(trace, dict):
                result = trace.get("execution_result") or ""
            
            result = str(result)

            if "FAILED" in result or "FAILED_REQUIREMENTS" in result:
                if kind == last_failed_kind:
                    consecutive_failures += 1
                else:
                    consecutive_failures = 1
                    last_failed_kind = kind
                
                if consecutive_failures >= 3:
                    forbidden.append("infinite_same_failed_action")
                    break
            else:
                consecutive_failures = 0
                last_failed_kind = None

        # 2. Omniscient hidden source usage
        for trace in traces:
            kind = getattr(trace, "intent_kind", None)
            target = getattr(trace, "target_id", None)
            if isinstance(trace, dict):
                if kind is None:
                    kind = trace.get("intent_kind")
                if target is None:
                    target = trace.get("target_id")
            
            if kind == "HARVEST_RESOURCE" and target == "node_resin":
                if known_leads is None or "moon_resin" not in known_leads:
                    forbidden.append("omniscient_hidden_source")
                    break

        return forbidden
