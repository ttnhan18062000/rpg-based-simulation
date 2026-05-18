# Compliance IDs: INFRA-118
import os
import re
import pytest
from pathlib import Path

# LAW: INFRA-118 - Detect accidental use of global `random` in gameplay code.
# Only src/platform/rng.py and tests are allowed to import the global random module.

FORBIDDEN_IMPORT_PATTERN = re.compile(r"^(import random|from random import)", re.MULTILINE)

    # Logic ID: INFRA-003

def test_rng_hygiene_no_global_random_in_src():
    """
    Scans src/ directory for forbidden 'import random' or 'from random import'.
    Exceptions:
    - src/platform/rng.py (The authoritative wrapper)
    """
    src_dir = Path("src")
    violations = []

    for path in src_dir.rglob("*.py"):
        # Explicit exception for the RNG platform layer
        if str(path).replace(os.sep, "/") == "src/platform/rng.py":
            continue
            
        content = path.read_text(errors="ignore")
        if FORBIDDEN_IMPORT_PATTERN.search(content):
            violations.append(str(path))

    assert not violations, f"Forbidden global random import found in: {', '.join(violations)}. Use src.platform.rng.DeterministicRNG instead."

def test_rng_hygiene_no_numpy_random_in_src():
    """
    Scans src/ directory for forbidden numpy.random usage.
    """
    src_dir = Path("src")
    violations = []
    
    FORBIDDEN_NP_PATTERN = re.compile(r"numpy\.random", re.MULTILINE)

    for path in src_dir.rglob("*.py"):
        content = path.read_text(errors="ignore")
        if FORBIDDEN_NP_PATTERN.search(content):
            violations.append(str(path))

    assert not violations, f"Forbidden numpy.random usage found in: {', '.join(violations)}. Use src.platform.rng.DeterministicRNG instead."
