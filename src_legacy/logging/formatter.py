from __future__ import annotations
import logging
import json
import threading
from datetime import datetime
from typing import Any, Dict

# Thread-local storage for logging context
_log_context = threading.local()

def set_logging_context(**kwargs):
    """Set persistent context fields for the current thread's logs."""
    for key, value in kwargs.items():
        setattr(_log_context, key, value)

class ContextFilter(logging.Filter):
    """Filter that injects thread-local context into every LogRecord."""
    def filter(self, record):
        for attr in ('tick', 'component', 'worker_id', 'entity_id'):
            if not hasattr(record, attr):
                val = getattr(_log_context, attr, None)
                if val is not None:
                    setattr(record, attr, val)
        return True

class JsonFormatter(logging.Formatter):
    """
    JSON formatter for V2 engine logs.
    Parity with legacy StructuredJsonFormatter.
    """
    def format(self, record):
        log_record = {
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "level": record.levelname,
            "component": record.name
        }
        
        # Inject context fields
        for attr in ('tick', 'component', 'worker_id', 'entity_id'):
            val = getattr(record, attr, None)
            if val is not None:
                log_record[attr] = val
                
        # Inject 'extra' fields
        if hasattr(record, "extra"):
            log_record.update(record.extra)
            
        return json.dumps(log_record)

def setup_v2_logging(level: str = "INFO", json_format: bool = False):
    """Configure root logger for V2 engine."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)
    
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        # Standard legacy-adjacent format
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        handler.setFormatter(formatter)
        
    handler.addFilter(ContextFilter())
    
    root = logging.getLogger()
    root.setLevel(numeric_level)
    # Avoid duplicate handlers if called multiple times
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)
