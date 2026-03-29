import json
import sys
import argparse
from typing import Dict, List, Set

def audit_logs(log_file: str):
    print(f"--- Auditing Logs: {log_file} ---")
    
    tick_counts = {}  # component -> last_tick
    dead_entities: Set[int] = set()
    fraud_found = False
    
    line_count = 0
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line_count += 1
            try:
                log = json.loads(line)
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON at line {line_count}")
                continue
            
            tick = log.get('tick')
            component = log.get('component', 'unknown')
            msg = log.get('message', '').lower()
            entity_id = log.get('entity_id')
            hp = log.get('hp')
            
            # 1. Tick Continuity Check
            if tick is not None:
                last_tick = tick_counts.get(component, -1)
                if tick < last_tick:
                    print(f"[FRAUD] Non-monotonic tick in {component}: {last_tick} -> {tick} (line {line_count})")
                    fraud_found = True
                tick_counts[component] = tick
            
            # 2. Entity Life Cycle Check (Zombies)
            if entity_id is not None:
                if entity_id in dead_entities:
                    # Allow some grace for 'DEAD' repeating or 'DESPAWN', 
                    # but reject actions like 'ATTACK' or 'MOVE'
                    if any(act in msg for act in ['attack', 'move', 'cast', 'loot']):
                        print(f"[FRAUD] Zombie Action! Entity {entity_id} acting after death (line {line_count})")
                        fraud_found = True
                
                if "died" in msg or "death" in msg:
                    dead_entities.add(entity_id)

            # 3. Attribute Integrity Check
            if hp is not None and isinstance(hp, (int, float)):
                if hp < 0:
                    print(f"[FRAUD] Negative Health! Entity {entity_id} has HP={hp} (line {line_count})")
                    fraud_found = True

    if not fraud_found:
        print(f"--- Audit Complete: 0 fraud detected in {line_count} lines! ---")
    else:
        print(f"--- Audit Complete: Fraud detected in {log_file} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to the JSONL log file")
    args = parser.parse_args()
    audit_logs(args.file)
