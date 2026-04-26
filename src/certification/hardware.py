from __future__ import annotations

import psutil
import platform
from typing import Dict, Any
from src.certification.models import HardwareClass


class HardwareClassifier:
    """
    M9 Law: Explicit and deterministic hardware classification.
    """

    @staticmethod
    def detect_class() -> HardwareClass:
        """
        CLASS_A: >= 16 Cores AND >= 32GB RAM
        CLASS_B: >= 4 Cores AND >= 8GB RAM
        CLASS_C: Everything else
        """
        cores = psutil.cpu_count(logical=True) or 0
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        if cores >= 16 and ram_gb >= 32.0:
            return HardwareClass.CLASS_A
        elif cores >= 4 and ram_gb >= 8.0:
            return HardwareClass.CLASS_B
        else:
            return HardwareClass.CLASS_C

    @staticmethod
    def get_detailed_telemetry() -> Dict[str, Any]:
        """Capture host environment metadata."""
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "cpu_freq_mhz": getattr(psutil.cpu_freq(), "current", "unknown") if psutil.cpu_freq() else "unknown"
        }
