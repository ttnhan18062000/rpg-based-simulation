import os
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.profiles import PROD_LARGE
from src.api.engine_manager import V2EngineManager
from src.logging.formatter import JsonFormatter, ContextFilter

REPO_ROOT = Path(__file__).resolve().parents[2]


def setup_turbo_logging(log_file: str):
    """Bypass Docker Loki routing and dump JSON directly to a flat file."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(JsonFormatter('%(message)s'))
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
    
    log_path = str(REPO_ROOT / "logs" / "stress_test.jsonl")
    setup_turbo_logging(log_path)
    
    target_ticks = 5000
    print(f"--- TURBO RUN INITIALIZED ---")
    print(f"Targeting {target_ticks} ticks with an inline headless kernel...")

    # 2. Configure headless
    mgr = V2EngineManager(PROD_LARGE, seed=111, entities_count=25, world_id="dungeon_crawl")
    kernel = mgr.kernel

    start_time = time.time()
    ticks_completed = 0

    try:
        for _ in range(target_ticks):
            kernel.tick_once()
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
    print(f"Now run: python tools/maintenance/audit_logs.py logs/stress_test.jsonl")

if __name__ == "__main__":
    run_turbo()
