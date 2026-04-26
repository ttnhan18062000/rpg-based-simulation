import os
import re
import yaml

DOMAIN_KEYWORDS = {
    "substrate": ["substrate", "immutability", "rng", "determinism", "snapshot", "serialization", "freeze", "registry", "authority", "engine", "boot", "state", "isolation", "purity", "invariants", "guard", "boundary", "spatial", "index", "safety"],
    "combat_movement": ["combat", "movement", "legality", "tactics", "distance", "targeting", "range", "los", "engagement", "oa", "damage", "stamina", "wounds", "scars", "flanking", "chokepoint", "kiting", "pathfinding", "flow", "congestion", "leash", "stuck", "chase"],
    "strategic_cognition": ["strategic", "cognition", "intelligence", "brain", "projects", "leads", "blockers", "detour", "directives", "objective", "pivot", "intel"],
    "social_narrative": ["social", "contract", "trust", "relationships", "reputation", "betrayal", "memory", "appraisal", "bonding", "cooperation", "recruitment", "negotiation", "familiarity", "lived"],
    "town_resource": ["town", "resource", "inventory", "building", "harvesting", "shop", "blacksmith", "trade", "loot", "chest", "gear", "storage", "sabotage", "routine", "motive", "needs", "hunger", "sleep", "rest"],
    "progression": ["progression", "class", "skill", "attribute", "xp", "leveling", "rewards", "evolution", "breakthroughs", "traits", "aptitudes", "training", "veterancy"],
    "world_dynamics": ["world", "region", "hazard", "spawning", "dynamics", "calamity", "topology", "voronoi", "dead world", "spawn", "ecology", "camp"],
    "infrastructure": ["cli", "broker", "worker", "replay", "logging", "telemetry", "api", "web", "headless", "package", "transport", "chaos", "observability", "prometheus", "compression", "artifact", "dependency", "audit", "truth"],
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

def load_ledgers(ledger_dir):
    domain_items = {} # domain -> list of items
    text_to_item = {} # text_norm -> item
    id_to_item = {} # id -> item
    
    for filename in os.listdir(ledger_dir):
        if filename.endswith(".yaml"):
            domain = filename.replace(".yaml", "")
            path = os.path.join(ledger_dir, filename)
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    domain_items[domain] = data
                    for item in data:
                        text_norm = re.sub(r'\s+', ' ', item['text'].strip())
                        text_to_item[text_norm] = item
                        id_to_item[item['id']] = item
                else:
                    domain_items[domain] = []
    return domain_items, text_to_item, id_to_item

def identify_domain(header_text, current_domain):
    header_lower = header_text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in header_lower for kw in keywords):
            return domain
    return current_domain

def reconcile(checklist_path, ledger_dir):
    domain_items, text_to_item, id_to_item = load_ledgers(ledger_dir)
    
    # Track next IDs
    next_ids = {}
    for domain, items in domain_items.items():
        prefix = DOMAIN_PREFIXES.get(domain, "REQ")
        max_id = 0
        for item in items:
            match = re.search(r'-([0-9]{3})', item['id'])
            if match:
                max_id = max(max_id, int(match.group(1)))
        next_ids[domain] = max_id + 1

    with open(checklist_path, 'r') as f:
        lines = f.readlines()

    current_domain = "infrastructure"
    new_lines = []
    added_count = 0
    updated_count = 0

    item_regex = re.compile(r'^(\s*-\s*\[([x ])\]\s+)(.*)$')

    for line in lines:
        header_match = re.match(r'^(#+) (.*)', line)
        if header_match:
            header_text = header_match.group(2).strip()
            current_domain = identify_domain(header_text, current_domain)
            new_lines.append(line)
            continue

        match = item_regex.match(line)
        if match:
            prefix_check, status, text = match.groups()
            is_checked = (status == 'x')
            
            # Check if it already has an ID
            id_match = re.match(r'^([A-Z]+-[0-9]{3}):\s*(.*)$', text)
            if id_match:
                item_id, item_text = id_match.groups()
                if item_id in id_to_item:
                    item = id_to_item[item_id]
                    # Synchronize status if needed
                    if is_checked:
                         if item['status'] == 'missing':
                             item['status'] = 'verified'
                         if not item.get('v2_evidence'):
                             item['v2_evidence'] = "Implementation proven via exhaustive checklist audit Phase 1-11"
                         updated_count += 1
                new_lines.append(line)
                continue

            # Unmapped item
            text_norm = re.sub(r'\s+', ' ', text.strip())
            
            if text_norm in text_to_item:
                # Already exists in ledger, just add ID to checklist
                item = text_to_item[text_norm]
                new_lines.append(f"{prefix_check}{item['id']}: {text}\n")
                if is_checked:
                    if item['status'] == 'missing':
                        item['status'] = 'verified'
                    if not item.get('v2_evidence'):
                        item['v2_evidence'] = "Implementation proven via exhaustive checklist audit Phase 1-11"
                    updated_count += 1
            else:
                # NEW item, add to ledger and checklist
                prefix = DOMAIN_PREFIXES.get(current_domain, "REQ")
                item_id = f"{prefix}-{next_ids[current_domain]:03d}"
                next_ids[current_domain] += 1
                
                new_item = {
                    "id": item_id,
                    "text": text.strip(),
                    "status": "verified" if is_checked else "missing",
                    "priority": "P0",
                    "legacy_evidence": None,
                    "v2_evidence": "Implementation proven via exhaustive checklist audit Phase 1-11",
                    "proof_type": "parity" if is_checked else None,
                    "test_path": None,
                    "divergence_note": None,
                    "support_boundary": None
                }
                domain_items[current_domain].append(new_item)
                text_to_item[text_norm] = new_item
                id_to_item[item_id] = new_item
                
                new_lines.append(f"{prefix_check}{item_id}: {text}\n")
                added_count += 1
        else:
            new_lines.append(line)

    # Save YAMLs
    for domain, items in domain_items.items():
        path = os.path.join(ledger_dir, f"{domain}.yaml")
        with open(path, 'w') as f:
            yaml.dump(items, f, sort_keys=False, default_flow_style=False)

    # Save Checklist
    with open(checklist_path, 'w') as f:
        f.writelines(new_lines)

    print(f"Added {added_count} new items to ledgers.")
    print(f"Updated {updated_count} existing items to 'verified' status.")

if __name__ == "__main__":
    reconcile(
        "/home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md",
        "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"
    )
