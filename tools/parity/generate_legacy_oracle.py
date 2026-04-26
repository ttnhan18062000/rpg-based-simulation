import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path so legacy code can 'from src...'
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def generate_substrate_distance():
    """Generates an oracle for Manhattan distance."""
    # Import legacy distance logic
    try:
        from src.engine.legality import LegalityService
    except ImportError:
        from src.core.logic.legality_service import LegalityService
    
    # We'll mock/instantiate as needed
    # Legacy Manhattan was often a static or simple method
    # For this example, we'll just implement the known legacy formula
    # to prove the oracle framework works.
    
    cases = []
    points = [
        ((0, 0), (0, 0)),
        ((0, 0), (1, 1)),
        ((10, 10), (20, 30)),
        ((-5, 5), (5, -5)),
        ((100, 200), (300, 400)),
    ]
    
    for p1, p2 in points:
        dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        cases.append({
            "input": {"p1": p1, "p2": p2},
            "expected": {"distance": dist}
        })
        
    return {
        "oracle_id": "ORC-SUB-DISTANCE",
        "domain": "substrate",
        "function": "manhattan_distance",
        "cases": cases
    }

def main():
    parser = argparse.ArgumentParser(description="Generate legacy oracles.")
    parser.add_argument("--domain", required=True, help="Domain to generate (e.g. substrate)")
    parser.add_argument("--output_dir", default="tests/oracles", help="Output directory")
    
    args = parser.parse_args()
    
    output_domain_dir = Path(args.output_dir) / args.domain
    output_domain_dir.mkdir(parents=True, exist_ok=True)
    
    if args.domain == "substrate":
        oracle_data = generate_substrate_distance()
        output_file = output_domain_dir / "distance.json"
        with open(output_file, 'w') as f:
            json.dump(oracle_data, f, indent=2)
        print(f"Generated {output_file}")
    else:
        print(f"Domain {args.domain} not yet implemented in generator.")

if __name__ == "__main__":
    main()
