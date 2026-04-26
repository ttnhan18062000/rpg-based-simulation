import json
import os
from pathlib import Path

def load_oracle(domain, function_name):
    """
    Loads an oracle fixture and returns a list of (input, expected) tuples.
    Used for pytest parameterization.
    """
    # Resolve path relative to this file
    base_dir = Path(__file__).parent.parent.parent / "oracles"
    oracle_path = base_dir / domain / f"{function_name}.json"
    
    if not oracle_path.exists():
        raise FileNotFoundError(
            f"Oracle not found for {domain}.{function_name} at {oracle_path}. "
            f"Please run 'python tools/parity/generate_legacy_oracle.py --domain {domain}'"
        )
        
    with open(oracle_path, 'r') as f:
        data = json.load(f)
        
    return [(case['input'], case['expected']) for case in data['cases']]
