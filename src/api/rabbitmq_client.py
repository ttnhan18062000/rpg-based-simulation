import os
import pika
import logging

logger = logging.getLogger(__name__)

# Track a global connection for simple synchronous workers/clients 
# (e.g., the EngineManager loop or the ai_worker thread).
_connection: pika.BlockingConnection | None = None


def is_rabbitmq_disabled() -> bool:
    """Return True if RabbitMQ integration is explicitly disabled."""
    return os.environ.get("DISABLE_RABBITMQ", "0").lower() in ("1", "true", "yes")

def get_rabbitmq() -> pika.BlockingConnection | None:
    """Get or create a synchronous RabbitMQ connection with retry logic."""
    if is_rabbitmq_disabled():
        return None
        
    global _connection
    if _connection is None or _connection.is_closed:
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
        parameters = pika.URLParameters(url)
        # Increase the heartbeat timeout to prevent connection drops during long simulation ticks (e.g. 100% CPU lock under GIL)
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300
        
        import time
        max_retries = int(os.environ.get("RABBITMQ_RETRIES", "3"))
        for i in range(max_retries):
            try:
                _connection = pika.BlockingConnection(parameters)
                logger.info("Successfully connected to RabbitMQ at %s", url)
                return _connection
            except Exception as e:
                if i == max_retries - 1:
                    from src.utils.metrics import SIM_ERRORS_TOTAL
                    SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="rabbitmq_client").inc()
                    logger.error("Final attempt (%d) failed to connect to RabbitMQ at %s: %s", max_retries, url, e)
                    raise
                logger.warning("Attempt %d/%d: RabbitMQ not ready at %s, retrying in 3s...", i+1, max_retries, url)
                time.sleep(3)
    
    return _connection


def close_rabbitmq():
    """Close the global RabbitMQ connection if it exists."""
    global _connection
    if _connection and not _connection.is_closed:
        try:
            _connection.close()
        except Exception:
            pass
        _connection = None
