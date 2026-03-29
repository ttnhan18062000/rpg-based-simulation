import logging
import sys
import json
import threading
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Thread-local storage for logging context
_log_context = threading.local()

def set_logging_context(**kwargs):
    """Set persistent context fields for the current thread's logs."""
    for key, value in kwargs.items():
        setattr(_log_context, key, value)

class ContextFilter(logging.Filter):
    """Filter that injects thread-local context into every LogRecord."""
    def filter(self, record):
        # We also support 'extra' passed directly to the log call
        # but thread-local takes precedence or provides fallbacks
        for attr in ('tick', 'component', 'worker_id', 'entity_id'):
            # Only set if not already present in the record (from 'extra')
            if not hasattr(record, attr):
                val = getattr(_log_context, attr, None)
                if val is not None:
                    setattr(record, attr, val)
        return True

class RobustLoggerAdapter(logging.LoggerAdapter):
    """Legacy wrapper, now just updates thread-local context before logging."""
    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            # Sync our extra to thread-local to support mixed usage
            set_logging_context(**self.extra)
            super().log(level, msg, *args, **kwargs)

class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for RPG simulation logs."""
    
    def add_fields(self, log_record, record, message_dict):
        super(StructuredJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Capture all custom fields from the record __dict__
        standard_fields = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName', 'message', 'taskName'
        }
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                log_record[key] = value

        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
            
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.progression.levelname
            
        if not log_record.get('component'):
            log_record['component'] = record.name

def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a JSON formatter and ContextFilter."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(StructuredJsonFormatter('%(message)s'))
    
    # Add our context filter to the handler
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(handler)
    
    # Silence chatty third-party loggers
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
