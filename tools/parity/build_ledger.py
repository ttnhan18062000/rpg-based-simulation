import re
import yaml
import os
from pathlib import Path

# Mapping of keywords in headers to domain names
DOMAIN_KEYWORDS = {
    "substrate": ["substrate", "immutability", "rng", "determinism", "snapshot", "serialization", "freeze", "registry", "authority", "engine", "boot", "state", "isolation", "purity", "invariants"],
    "combat_movement": ["combat", "movement", "legality", "tactics", "distance", "targeting", "range", "los", "engagement", "oa", "damage", "stamina", "wounds", "scars", "flanking", "chokepoint", "kiting", "pathfinding", "flow", "congestion", "leash", "stuck", "chase"],
    "strategic_cognition": ["strategic", "cognition", "intelligence", "brain", "projects", "leads", "blockers", "detour", "directives", "objective", "pivot", "intel"],
    "social_narrative": ["social", "contract", "trust", "relationships", "reputation", "betrayal", "memory", "appraisal", "bonding", "cooperation", "recruitment", "negotiation", "familiarity", "lived"],
    "town_resource": ["town", "resource", "inventory", "building", "harvesting", "shop", "blacksmith", "trade", "loot", "chest", "gear", "storage", "sabotage", "routine", "motive", "needs", "hunger", "sleep", "rest"],
    "progression": ["progression", "class", "skill", "attribute", "xp", "leveling", "rewards", "evolution", "breakthroughs", "traits", "aptitudes", "training", "veterancy"],
    "world_dynamics": ["world", "region", "hazard", "spawning", "dynamics", "calamity", "topology", "voronoi", "dead world"],
    "infrastructure": ["cli", "broker", "worker", "replay", "logging", "telemetry", "api", "web", "headless", "package", "transport", "chaos", "observability", "prometheus", "compression", "artifact", "dependency"],
}

DOMAIN_PREFIXES = {
    "substrate": "SUB",
    "combat_movement": "COMB",
    "town_resource": "TOWN",
    "strategic_cognition": "STRAT",
    "social_narrative": "SOC",
    "progression": "PROG",
    "world_dynamics": "WORLD",
    "infrastructure": "INFRA"
}

def identify_domain(header_text, current_domain):
    header_lower = header_text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in header_lower for kw in keywords):
            return domain
    return current_domain

def build_ledger(checklist_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(checklist_path, 'r') as f:
        lines = f.readlines()

    current_domain = "infrastructure"
    ledgers = {}
    counters = {k: 0 for k in DOMAIN_PREFIXES}

    for line in lines:
        header_match = re.match(r'^(#+) (.*)', line)
        if header_match:
            header_text = header_match.group(2).strip()
            current_domain = identify_domain(header_text, current_domain)
            continue

        req_match = re.search(r'- \[( |x)\] (.*)', line)
        if req_match:
            checked = req_match.group(1) == 'x'
            text = req_match.group(2).strip()
            
            prefix = DOMAIN_PREFIXES.get(current_domain, "REQ")
            counters[current_domain] += 1
            item_id = f"{prefix}-{counters[current_domain]:03d}"

            item = {
                "id": item_id,
                "text": text,
                "status": "legacy_verified" if checked else "missing",
                "priority": "P0",
                "legacy_evidence": None,
                "v2_evidence": None,
                "proof_type": "parity" if checked else None,
                "test_path": None,
                "divergence_note": None,
                "support_boundary": None
            }

            if current_domain not in ledgers:
                ledgers[current_domain] = []
            ledgers[current_domain].append(item)

    for domain, items in ledgers.items():
        output_path = os.path.join(output_dir, f"{domain}.yaml")
        with open(output_path, 'w') as f:
            yaml.dump(items, f, sort_keys=False, default_flow_style=False)
        print(f"Generated {output_path} with {len(items)} items.")

if __name__ == "__main__":
    build_ledger(
        "/home/vboxuser/Work/rpg-based-simulation/legacy_checklist.md",
        "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"
    )
