import json
from src.engine.checkpoint import CanonicalStateHasher

def diff_states(state_a, state_b):
    data_a = CanonicalStateHasher.to_canonical_data(state_a)
    data_b = CanonicalStateHasher.to_canonical_data(state_b)
    
    # Recursively find differences
    def find_diff(d1, d2, path=""):
        diffs = []
        if d1 == d2:
            return diffs
        
        if type(d1) != type(d2):
            diffs.append(f"{path}: type mismatch {type(d1)} vs {type(d2)}")
            return diffs
        
        if isinstance(d1, dict):
            keys = set(d1.keys()) | set(d2.keys())
            for k in sorted(keys):
                if k not in d1:
                    diffs.append(f"{path}.{k}: missing in d1")
                    continue
                if k not in d2:
                    diffs.append(f"{path}.{k}: missing in d2")
                    continue
                diffs.extend(find_diff(d1[k], d2[k], f"{path}.{k}"))
        elif isinstance(d1, list):
            if len(d1) != len(d2):
                diffs.append(f"{path}: length mismatch {len(d1)} vs {len(d2)}")
            else:
                for i in range(len(d1)):
                    diffs.extend(find_diff(d1[i], d2[i], f"{path}[{i}]"))
        else:
            diffs.append(f"{path}: value mismatch {d1} vs {d2}")
            
        return diffs
        
    return find_diff(data_a, data_b)
