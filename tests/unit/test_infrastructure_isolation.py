import sys
import unittest
from unittest.mock import patch, MagicMock
import os
import importlib

# Modules are patched inside individual tests to ensure isolation from previous pytest runs.

class TestInfrastructureIsolation(unittest.TestCase):
    def test_rabbitmq_import_guard(self):
        """Prove that rabbitmq_client handles missing pika package."""
        with patch.dict('sys.modules', {'pika': None}):
            import src.api.rabbitmq_client
            importlib.reload(src.api.rabbitmq_client)
            from src.api.rabbitmq_client import HAS_PIKA, get_rabbitmq
            self.assertFalse(HAS_PIKA)
            # Even if not disabled by env, should return None if package missing
            with patch.dict(os.environ, {"DISABLE_RABBITMQ": "0"}):
                self.assertIsNone(get_rabbitmq())

    def test_rabbitmq_disabled_mode(self):
        """Prove that rabbitmq_client respects DISABLE_RABBITMQ env flag."""
        from src.api.rabbitmq_client import is_rabbitmq_disabled, get_rabbitmq
        with patch.dict(os.environ, {"DISABLE_RABBITMQ": "1"}):
            self.assertTrue(is_rabbitmq_disabled())
            self.assertIsNone(get_rabbitmq())

    def test_kafka_import_guard(self):
        """Prove that kafka_client handles missing confluent_kafka package."""
        with patch.dict('sys.modules', {'confluent_kafka': None}):
            import src.api.kafka_client
            importlib.reload(src.api.kafka_client)
            from src.api.kafka_client import HAS_KAFKA, get_kafka_producer
            self.assertFalse(HAS_KAFKA)
            with patch.dict(os.environ, {"DISABLE_KAFKA": "0"}):
                self.assertIsNone(get_kafka_producer())

    def test_kafka_disabled_mode(self):
        """Prove that kafka_client respects DISABLE_KAFKA env flag."""
        from src.api.kafka_client import is_kafka_disabled, get_kafka_producer
        with patch.dict(os.environ, {"DISABLE_KAFKA": "1"}):
            self.assertTrue(is_kafka_disabled())
            self.assertIsNone(get_kafka_producer())

    def test_regression_runner_survives_no_infrastructure(self):
        """Smoke test: HeadlessRunner should be instantiable without active infrastructure."""
        from src.testing.headless_regression_runner import HeadlessRunner
        from src.config import SimulationConfig
        
        # Should not crash on init even if RabbitMQ/Kafka are enabled in config but missing in env/packages
        # because the clients return None gracefully.
        runner = HeadlessRunner(output_root="logs/isolation_test")
        self.assertEqual(str(runner.output_root), "logs/isolation_test")

if __name__ == "__main__":
    unittest.main()
