import tomllib

import yaml

COMPOSE_PATH = "docker-compose.yml"
PYPROJECT_PATH = "pyproject.toml"


def _load_compose():
    with open(COMPOSE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _environment_values(environment):
    # docker-compose supports both list ("KEY=value") and dict ({"KEY": "value"}) environment
    # forms; this repo's own compose file uses both, so both must be checked.
    if environment is None:
        return []
    if isinstance(environment, dict):
        return [f"{k}={v}" for k, v in environment.items()]
    return list(environment)


def test_ai_worker_does_not_depend_on_rabbitmq_healthcheck():
    compose = _load_compose()
    ai_worker_depends_on = compose["services"]["ai_worker"].get("depends_on", {})
    assert "rabbitmq" not in ai_worker_depends_on, (
        "ai_worker must not depend on rabbitmq's healthcheck; RabbitMQ was fully removed by "
        "TCK-20260817-DEAD-INFRA-REMOVAL-EPIC"
    )


def test_docker_compose_has_no_rabbitmq_kafka_zookeeper_services():
    compose = _load_compose()

    services = compose.get("services", {})
    for dead_service in ("rabbitmq", "kafka", "zookeeper"):
        assert dead_service not in services, f"{dead_service} service must not exist in docker-compose.yml"

    volumes = compose.get("volumes", {}) or {}
    for dead_volume in ("rabbitmq_data", "kafka_data", "zookeeper_data"):
        assert dead_volume not in volumes, f"{dead_volume} volume must not exist in docker-compose.yml"

    for service_name, service_def in services.items():
        env_values = _environment_values(service_def.get("environment"))
        for value in env_values:
            assert "RABBITMQ_URL" not in value, f"{service_name} still injects RABBITMQ_URL"
            assert "KAFKA_URL" not in value, f"{service_name} still injects KAFKA_URL"

    backend_depends_on = services["backend"].get("depends_on", [])
    assert "rabbitmq" not in backend_depends_on, "backend must not depend on the removed rabbitmq service"
    assert "kafka" not in backend_depends_on, "backend must not depend on the removed kafka service"


def test_pyproject_has_no_broker_client_dependencies():
    with open(PYPROJECT_PATH, "rb") as f:
        data = tomllib.load(f)

    dependencies = data["project"]["dependencies"]
    for dep in dependencies:
        assert not dep.startswith("pika"), f"pika must not be declared as a dependency: {dep}"
        assert not dep.startswith("confluent-kafka"), f"confluent-kafka must not be declared as a dependency: {dep}"
