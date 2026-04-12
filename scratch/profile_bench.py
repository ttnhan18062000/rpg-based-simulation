import cProfile
import pstats
import io
import os
import sys

# Add project root to path
sys.path.insert(0, os.getcwd())

from tests.benchmarks.test_scaling_bench import run_bench

def profile_run():
    pr = cProfile.Profile()
    pr.enable()
    run_bench(1000, ticks=5)
    pr.disable()
    
    s = io.StringIO()
    sortby = 'tottime'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(25)
    print(s.getvalue())

if __name__ == "__main__":
    profile_run()
