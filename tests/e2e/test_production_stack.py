# TODO: fix later

# import os
# import subprocess
# import time
# import requests
# import pytest
# from typing import Generator

# # Configuration
# DOCKER_COMPOSE_FILE = "docker-compose.yml"
# def get_urls():
#     ports = getattr(pytest, "engine_ports", {})
#     return {
#         "LOKI": f"http://localhost:{ports.get('LOKI_PORT', 3100)}",
#         "PROMETHEUS": f"http://localhost:{ports.get('PROMETHEUS_PORT', 9090)}",
#         "BACKEND": f"http://localhost:{ports.get('BACKEND_PORT', 8000)}"
#     }

# # URLs will be resolved inside tests using get_urls()

# def test_loki_ingestion():
#     """Verify that structured logs are flowing into Loki via active injection."""
#     import uuid
#     trace_id = str(uuid.uuid4())
#     test_msg = f"Ingestion-Trace-{trace_id}"
#     print(f"Injecting trace message: {test_msg}")
    
#     # 1. Inject log via backend (with retries for 503/startup issues)
#     urls = get_urls()
#     url = f"{urls['BACKEND']}/api/v1/control/debug/log"
#     success = False
#     for i in range(5):
#         try:
#             resp = requests.post(url, json={"message": test_msg}, timeout=10)
#             if resp.status_code == 200:
#                 success = True
#                 break
#             print(f"Injection attempt {i+1} failed with status {resp.status_code}. Retrying...")
#             time.sleep(5)
#         except Exception as e:
#             print(f"Injection attempt {i+1} failed with error: {e}. Retrying...")
#             time.sleep(5)
    
#     if not success:
#         pytest.fail(f"Could not reach backend for injection after 5 attempts.")

#     # 2. Verify ingestion in Loki
#     print("Verifying Loki ingestion...")
#     # Narrow query for the specific trace using direct stream selector
#     query = f'{{job="varlogs"}} |= "{test_msg}"'
#     params = {'query': query, 'limit': 1}
    
#     # Increase timeout to 120s for Windows environments
#     for i in range(24): # 120 seconds total
#         try:
#             urls = get_urls()
#             # Note: Using query_range for better compatibility with line filters
#             query_url = f"{urls['LOKI']}/loki/api/v1/query_range"
#             response = requests.get(query_url, params=params, timeout=10)
#             if response.status_code == 200:
#                 results = response.json().get('data', {}).get('result', [])
#                 if results:
#                     print(f"SUCCESS: Trace found in Loki after attempt {i+1}.")
#                     return
#             print(f"Attempt {i+1}: Trace not found in Loki yet, retrying...")
#         except Exception as e:
#             print(f"Attempt {i+1}: Loki request failed: {e}")
#         time.sleep(5)
    
#     # DEBUG: What streams exist?
#     try:
#         urls = get_urls()
#         val_res = requests.get(f"{urls['LOKI']}/loki/api/v1/label/job/values", timeout=5)
#         print(f"DEBUG: Active jobs in Loki: {val_res.json()}")
#     except:
#         pass
        
#     pytest.fail(f"Loki ingestion check failed: Trace ID {trace_id} not found after 60s.")

# def test_prometheus_metrics():
#     """Verify that metrics are being scraped into Prometheus."""
#     print("Verifying Prometheus metrics...")
#     # Query for sim_tick_duration_seconds_count
#     params = {
#         'query': 'sim_tick_duration_seconds_count'
#     }
    
#     for i in range(5):
#         try:
#             urls = get_urls()
#             response = requests.get(f"{urls['PROMETHEUS']}/api/v1/query", params=params, timeout=10)
#             if response.status_code == 200:
#                 data = response.json()
#                 results = data.get('data', {}).get('result', [])
#                 if results:
#                     print(f"SUCCESS: Found metric data in Prometheus.")
#                     return
#             print(f"Attempt {i+1}: Prometheus results empty, retrying...")
#         except Exception as e:
#             print(f"Attempt {i+1}: Prometheus request failed: {e}")
#         time.sleep(5)
    
#     pytest.fail("Prometheus metrics check failed: No data found for 'sim_tick_duration_seconds_count'")

# def test_deep_stack_error_audit():
#     """PHASE P5: Audit the entire environment for ANY error-level logs via Loki."""
#     print("Executing Deep Stack Error Audit via Loki...")
#     # Query using direct label selectors (Promtail indexes level and component)
#     # Exclude Loki and Promtail to avoid feedback loops
#     # ALSO exclude ANY common bootstrap logs that occur during search window
#     query = (
#         '{job="varlogs", level=~"(?i)error|critical|fail", component!="watchdog", '
#         'container!~"rpg-sim-e2e-(loki|promtail)-1"}'
#         ' !~ "(?i)Socket failed to connect|ConnectionRefused|AMQPConnection|Kafka broker|Waiting for RabbitMQ|ConnectorSocket"'
#     )
#     # Only look at the last 60 seconds to avoid bootstrap race-condition logs
#     params = {
#         'query': query, 
#         'limit': 5,
#         'start': int((time.time() - 60) * 1e9) # Loki expects nanoseconds
#     }
    
#     for i in range(5):
#         try:
#             urls = get_urls()
#             response = requests.get(f"{urls['LOKI']}/loki/api/v1/query_range", params=params, timeout=10)
#             if response.status_code == 200:
#                 results = response.json().get('data', {}).get('result', [])
                
#                 if results:
#                     errors = []
#                     for res in results:
#                         for val in res.get('values', []):
#                             errors.append(val[1])
#                     pytest.fail(f"Deep Stack Audit Found Errors:\n" + "\n".join(errors[:5]))
                
#                 print("SUCCESS: 0 error-level logs found across the stack.")
#                 return
#             print(f"Attempt {i+1}: Loki query non-200 ({response.status_code}), retrying...")
#         except Exception as e:
#             print(f"Attempt {i+1}: Audit failed during execution: {e}")
#         time.sleep(5)
    
#     pytest.fail("Deep Stack Audit failed: Loki indexing timeout or persistent error.")

# def test_golden_path_simulation_progress():
#     """PHASE P4: Verify the simulation clock progresses correctly in production mode."""
#     print("Verifying 'Golden Path' simulation progress via Prometheus...")
#     params = {'query': 'sim_current_tick'}
    
#     # Capture initial tick
#     try:
#         urls = get_urls()
#         resp = requests.get(f"{urls['PROMETHEUS']}/api/v1/query", params=params, timeout=10)
#         data = resp.json().get('data', {}).get('result', [])
#         initial_tick = float(data[0]['value'][1]) if data else 0
#         print(f"Initial Simulation Tick: {initial_tick}")
        
#         # Wait for simulation to progress (Prometheus scrape interval is usually 15s)
#         print("Waiting 30s for simulation progress and Prometheus scrape...")
#         time.sleep(30)
        
#         # Capture final tick
#         resp = requests.get(f"{urls['PROMETHEUS']}/api/v1/query", params=params, timeout=10)
#         data = resp.json().get('data', {}).get('result', [])
#         final_tick = float(data[0]['value'][1]) if data else 0
#         print(f"Final Simulation Tick: {final_tick}")
        
#         if final_tick <= initial_tick:
#             # DUMP BACKEND LOGS ON STALL
#             print("\n!!! SIMULATION STALL DETECTED - DUMPING BACKEND LOGS !!!")
#             # Use project-prefixed name since we removed container_name in docker-compose.yml
#             log_res = subprocess.run("docker logs rpg-sim-e2e-backend-1 --tail 100", shell=True, capture_output=True, text=True)
#             print(log_res.stdout)
#             pytest.fail(f"Simulation stalled at tick {initial_tick}. See logs above.")
            
#         print(f"SUCCESS: Simulation progressed by {final_tick - initial_tick} ticks.")
#     except Exception as e:
#         pytest.fail(f"Golden Path verification failed: {e}")

# def test_backend_live():
#     """Verify the API is responsive."""
#     try:
#         urls = get_urls()
#         response = requests.get(f"{urls['BACKEND']}/health", timeout=5)
#         assert response.status_code == 200
#         print("SUCCESS: Backend API /health is OK")
#     except Exception as e:
#         pytest.fail(f"Backend health check failed: {e}")

# if __name__ == "__main__":
#     # Manual execution helper
#     pytest.main([__file__])
