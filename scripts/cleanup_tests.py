#!/usr/bin/env python3
"""Utility to clean up orphaned pytest and AI worker processes."""

import os
import signal
import subprocess
import sys

def get_processes():
    """Find all processes for the current user matching 'pytest' or 'ai_worker'."""
    try:
        user = os.getenv('USER') or os.getenv('LOGNAME')
        if not user:
            # Fallback to current uid
            uid = os.getuid()
            output = subprocess.check_output(['ps', '-u', str(uid), '-o', 'pid,cmd'], text=True)
        else:
            output = subprocess.check_output(['ps', '-u', user, '-o', 'pid,cmd'], text=True)
            
        lines = output.strip().split('\n')[1:] # Skip header
        targets = []
        for line in lines:
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            pid, cmd = parts
            if 'pytest' in cmd or 'ai_worker_daemon' in cmd or 'arena_runner' in cmd:
                # Don't kill ourselves
                if int(pid) != os.getpid():
                    targets.append((int(pid), cmd))
        return targets
    except Exception as e:
        print(f"Error scanning processes: {e}")
        return []

def cleanup():
    print("Scanning for lingering test processes...")
    targets = get_processes()
    
    if not targets:
        print("No lingering processes found.")
        return

    print(f"Found {len(targets)} process(es) to terminate:")
    for pid, cmd in targets:
        print(f"  [{pid}] {cmd[:80]}...")

    for pid, cmd in targets:
        try:
            print(f"Terminating PID {pid}...", end=' ')
            os.kill(pid, signal.SIGTERM)
            print("OK")
        except ProcessLookupError:
            print("Already gone")
        except Exception as e:
            print(f"Failed: {e}")

    # Re-check and force kill if necessary
    remaining = get_processes()
    if remaining:
        print("\nSome processes did not exit gracefully. Force killing...")
        for pid, cmd in remaining:
            try:
                print(f"Force killing PID {pid}...", end=' ')
                os.kill(pid, signal.SIGKILL)
                print("OK")
            except Exception:
                print("Failed")

if __name__ == "__main__":
    cleanup()
