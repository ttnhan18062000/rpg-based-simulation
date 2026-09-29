import os
import sys
import time
import logging

from pythonjsonlogger import jsonlogger
from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src_legacy.utils.logging import StructuredJsonFormatter, ContextFilter

def setup_turbo_logging(log_file: str):
    """Bypass Docker Loki routing and dump JSON directly to a flat file."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(StructuredJsonFormatter('%(message)s'))
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(handler)
    
    logging.getLogger("pika").setLevel(logging.WARNING)

def run_turbo():
    """Execute thousands of ticks in RAM, completely bypassing network serializers."""
    
    # 1. Isolate the environment
    os.environ["LOKI_URL"] = ""
    os.environ["DISABLE_KAFKA"] = "1"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    
    log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "stress_test.jsonl")
    log_path = os.path.abspath(log_path)
    setup_turbo_logging(log_path)
    
    print(f"--- TURBO RUN INITIALIZED ---")
    print(f"Targeting 5000 ticks with 1 inline FastWorker...")
    
    # 2. Configure headless
    config = SimulationConfig(
        num_workers=1,
        max_ticks=5000,
        initial_entity_count=25, 
        world_seed=111,
        chaos_enabled=False 
    )
    
    mgr = EngineManager(config)
    loop = mgr._loop
    
    start_time = time.time()
    ticks_completed = 0
    
    try:
        while loop.tick_once():
            ticks_completed += 1
            if ticks_completed % 1000 == 0:
                print(f"[{time.time()-start_time:.2f}s] Processed {ticks_completed} ticks...")
    except KeyboardInterrupt:
        print("\nTurbo Run Aborted.")
    finally:
        mgr.stop()
        
    duration = time.time() - start_time
    tps = ticks_completed / duration if duration > 0 else 0
    
    print(f"\n--- SCORECARD ---")
    print(f"Total Ticks: {ticks_completed}")
    print(f"Time Elapsed: {duration:.2f} seconds")
    print(f"Throughput: {tps:.2f} TPS")
    print(f"Audit Log: {log_path}")
    print(f"Now run: python scripts/audit_logs.py logs/stress_test.jsonl")

if __name__ == "__main__":
    run_turbo()
