"""Store constants and roots only. A leaf module: imports nothing from the project.

Other modules read these as `config.NAME` at call time (never `from ...config import NAME`), so tests can patch
a module attribute. Every bound below is provisional until the numeric budget decision (U-05).
"""

from __future__ import annotations

from pathlib import Path

STORE_FORMAT_VERSION = 1

_VISUAL_ASSETS = Path(__file__).resolve().parents[1]
CATALOG_ROOT = _VISUAL_ASSETS / "catalog"
QUARANTINE_ROOT = CATALOG_ROOT / ".quarantine"
REVIEW_ROOT = CATALOG_ROOT / ".review"

MAX_RECORD_BYTES = 64 * 1024  # provisional (U-05)
MAX_REGISTRY_BYTES = 1024 * 1024  # provisional (U-05)
MAX_VISUAL_KEYS = 4096  # provisional (U-05)
MAX_ALIASES = 1024  # provisional (U-05)
MAX_SOURCE_BYTES = 100 * 1024  # provisional (U-05); the D2 (no Git LFS) reversal trigger
MAX_DIM = 128  # provisional (U-05)
