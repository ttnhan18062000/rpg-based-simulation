import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


import subprocess
import time
import requests
import pytest
from typing import Generator

# Configuration
# Resolve docker-compose.yml relative to THIS conftest.py file (which is in tests/e2e/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCKER_COMPOSE_FILE = os.path.join(BASE_DIR, "docker-compose.yml")
PROJECT_NAME = "rpg-sim-e2e"
LOKI_READY_URL = "http://localhost:3100/ready"

def get_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_command(cmd: str, check: bool = False):
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: Command failed with code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result

@pytest.fixture(scope="session", autouse=False)
def engine_stack() -> Generator:
    """Orchestrate the entire docker-compose stack for the duration of the E2E session."""
    # Check if docker is available before proceeding
    try:
        check_docker = subprocess.run("docker compose version", shell=True, capture_output=True, text=True)
        if check_docker.returncode != 0:
            print(f"DEBUG: docker compose version failed with returncode {check_docker.returncode}")
            print(f"DEBUG: STDERR: {check_docker.stderr}")
            pytest.skip("Docker Compose not available (non-zero exit), skipping E2E stack tests.")
    except Exception as e:
        print(f"DEBUG: docker compose version raised exception: {e}")
        pytest.skip(f"Docker Compose not available (exception: {e}), skipping E2E stack tests.")

    # Assign dynamic ports to avoid conflicts with production
    e2e_ports = {
        "BACKEND_PORT": str(get_free_port()),
        "REDIS_PORT": str(get_free_port()),
        "RABBITMQ_PORT": str(get_free_port()),
        "RABBITMQ_MGMT_PORT": str(get_free_port()),
        "FRONTEND_PORT": str(get_free_port()),
        "PROMETHEUS_PORT": str(get_free_port()),
        "GRAFANA_PORT": str(get_free_port()),
        "KAFKA_PORT": str(get_free_port()),
        "LOKI_PORT": str(get_free_port()),
    }
    
    # Propagate connection URLs for in-process components (e.g. EngineManager in tests)
    e2e_ports["RABBITMQ_URL"] = f"amqp://guest:guest@127.0.0.1:{e2e_ports['RABBITMQ_PORT']}/"
    e2e_ports["KAFKA_URL"] = f"127.0.0.1:{e2e_ports['KAFKA_PORT']}"
    e2e_ports["REDIS_URL"] = f"redis://127.0.0.1:{e2e_ports['REDIS_PORT']}/0"
    
    os.environ.update(e2e_ports)
    
    # Store ports for test access
    pytest.engine_ports = e2e_ports

    print("\n--- [Session] spinning up Production Stack ---")
    print(f"Assigning dynamic ports: {e2e_ports}")
    
    # Use 'docker compose' (v2) which is more standard on modern Windows/Docker Desktop
    # Use a fixed project name to keep container names predictable
    # Pre-emptive cleanup to avoid stale volumes (e.g. Kafka Cluster ID mismatch)
    run_command(f"docker compose -f {DOCKER_COMPOSE_FILE} -p {PROJECT_NAME} down -v")
    try:
        # Pass env to the subprocess
        env = os.environ.copy()
        result = subprocess.run(f"docker compose -f {DOCKER_COMPOSE_FILE} -p {PROJECT_NAME} up -d --build", 
                                shell=True, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            pytest.skip("Failed to start Docker Compose stack, skipping E2E tests.")
    except Exception as e:
        pytest.skip(f"Error starting Docker Compose stack: {e}")
    
    print("Waiting for Simulation Watchdog & Core Services to stabilize...")
    max_wait = 120 # Increased for cold starts
    start_time = time.time()
    
    loki_ready = False
    watchdog_ready = False
    
    while time.time() - start_time < max_wait:
        # Check Watchdog (Predictable name due to -p flag)
        if not watchdog_ready:
            # Docker V2 usually uses {project}-{service}-1
            result = run_command(f"docker logs {PROJECT_NAME}-watchdog-1 --tail 50")
            if "Watchdog recovered" in result.stdout or "Watchdog monitoring" in result.stdout:
                print(f"SUCCESS: Watchdog certified health after {int(time.time() - start_time)}s")
                watchdog_ready = True
        
        # Check Loki
        if not loki_ready:
            try:
                loki_port = os.environ.get("LOKI_PORT", "3100")
                resp = requests.get(f"http://localhost:{loki_port}/ready", timeout=2)
                if resp.status_code == 200:
                    print(f"SUCCESS: Loki API is READY after {int(time.time() - start_time)}s")
                    loki_ready = True
            except:
                pass
        
        if watchdog_ready and loki_ready:
            break
            
        time.sleep(5)
    else:
        print("WARNING: E2E Stack did not fully stabilize within 120s, tests may fail.")
    
    # Extra buffer for indexing
    print("Stack up. Cooling down for 10s for log indexing...")
    time.sleep(10)
    
    yield
    
    # Temporarily disabled for debugging
    # print("\n--- [Cleanup] Tearing down Production Stack ---")
    # run_command(f"docker compose -f {DOCKER_COMPOSE_FILE} -p {PROJECT_NAME} down -v")
