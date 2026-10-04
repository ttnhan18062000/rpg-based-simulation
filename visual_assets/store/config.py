"""Store constants and roots only. A leaf module: imports nothing from the project.

Other modules read these as `config.NAME` at call time (never `from ...config import NAME`), so tests can patch
a module attribute. Every bound below is a proposed budget recorded in `docs/assets/budgets.md` (U-05), pinned to it by a test.
"""

from __future__ import annotations

from pathlib import Path

STORE_FORMAT_VERSION = 1

_VISUAL_ASSETS = Path(__file__).resolve().parents[1]
CATALOG_ROOT = _VISUAL_ASSETS / "catalog"
QUARANTINE_ROOT = CATALOG_ROOT / ".quarantine"
REVIEW_ROOT = CATALOG_ROOT / ".review"

MAX_RECORD_BYTES = 128 * 1024  # budget: docs/assets/budgets.md
MAX_REGISTRY_BYTES = 7 * 64 * 1024  # budget: docs/assets/budgets.md
MAX_MANIFEST_BYTES = 6 * 64 * 1024  # budget: docs/assets/budgets.md; the widest candidate or runtime manifest at MAX_VISUAL_KEYS entries, rounded up to 64 KiB
MAX_VISUAL_KEYS = 1024  # budget: docs/assets/budgets.md
MAX_ALIASES = 1024  # budget: docs/assets/budgets.md
MAX_SOURCE_BYTES = 100 * 1024  # budget: docs/assets/budgets.md; the D2 (no Git LFS) reversal trigger
MAX_DIM = 128  # budget: docs/assets/budgets.md
MAX_PREVIEW_BYTES = 512 * 1024  # budget: docs/assets/budgets.md
MAX_PREVIEW_DIM = 1024  # budget: docs/assets/budgets.md; 128 px at scale 8, the only scale `export_handoff` produces. Kept low because PNG unfiltering is a pure-Python per-byte loop (a 2048 px preview cost ~16 M steps per decode, and adopt decodes more than once)
MAX_UNADOPTED_INTAKE_AGE_DAYS = 30  # budget: docs/assets/budgets.md (R0, a judgment not a measurement); `gc` may list a PASSED, never-adopted intake and its review export once the intake is older than this many days. Younger ones and everything tracked are never touched
MAX_DECODED_BYTES = 1024 * (1024 * 4 + 1)  # budget: docs/assets/budgets.md; decompressed PNG data above this (a 1024 px RGBA square) is refused before it is inflated
MAX_PNG_FILE_BYTES = 65 * 64 * 1024  # budget: docs/assets/budgets.md; the worst legal PNG (1024 px RGBA noise, written incompressibly) rounded up to 64 KiB
