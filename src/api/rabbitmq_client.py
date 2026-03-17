import os
import pika
import logging

logger = logging.getLogger(__name__)

# Track a global connection for simple synchronous workers/clients 
# (e.g., the EngineManager loop or the ai_worker thread).
_connection: pika.BlockingConnection | None = None


def get_rabbitmq() -> pika.BlockingConnection:
    """Get or create a synchronous RabbitMQ connection."""
    global _connection
    if _connection is None or _connection.is_closed:
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        parameters = pika.URLParameters(url)
        # Increase the heartbeat timeout to prevent connection drops during long simulation ticks (e.g. 100% CPU lock under GIL)
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300
        
        try:
            _connection = pika.BlockingConnection(parameters)
            logger.info("Successfully connected to RabbitMQ at %s", url)
        except Exception as e:
            logger.error("Failed to connect to RabbitMQ at %s: %s", url, e)
            raise
    
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
