import yaml
import os

def clean_ledger(path):
    with open(path, 'r') as f:
        # We can't use safe_load because it doesn't preserve comments or order well if we want to fix duplicates.
        # But for cleaning, we can just rewrite it.
        # Actually, yaml.safe_load will just take the last key.
        data = yaml.safe_load(f)
    
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
    print(f"Cleaned {path}")

if __name__ == "__main__":
    ledger_dir = "/home/vboxuser/Work/rpg-based-simulation/docs/parity_ledger"
    for filename in os.listdir(ledger_dir):
        if filename.endswith(".yaml"):
            clean_ledger(os.path.join(ledger_dir, filename))
