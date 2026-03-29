import subprocess
import sys
import time

def run_command(cmd, abort_on_error=True):
    print(f"\n========================================")
    print(f"Executing: {' '.join(cmd)}")
    print(f"========================================\n")
    result = subprocess.run(cmd)
    if result.returncode != 0 and abort_on_error:
        print(f"\n[ERROR] Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode

def main():
    print("Starting Docker Setup & Testing Automation...")
    
    # 1. Build the containers
    print("\n[1/4] Building Docker containers...")
    run_command(["docker", "compose", "build"])
    
    # 2. Start the containers (detached mode)
    print("\n[2/4] Starting environment...")
    run_command(["docker", "compose", "up", "-d"])
    
    print("\nWaiting 5 seconds for services to fully initialize...")
    time.sleep(5)
    
    # 3. Run Tests
    test_failed = False
    print("\n[3/4] Running test suites...")
    
    # Run backend tests (pytest)
    print("\n--- Running Backend Tests (pytest) ---")
    be_result = run_command(["docker", "compose", "exec", "-T", "backend", "pytest"], abort_on_error=False)
    if be_result != 0:
        test_failed = True
        
    # We do not have a separate test stage for frontend deployed image currently since it's an nginx server.
    # To run frontend tests, we would ideally use a multi-stage target or a separate test container.
    # However, since the nginx image only has static files, we can't run vitest directly in it.
    # Therefore, the frontend tests are assumed to be run locally or in CI before building the Docker image.
    print("\n--- Frontend Tests ---")
    print("Frontend tests should be run during the build stage or locally via 'npm run test'.")
    print("The deployed 'frontend' container is Nginx serving static files, skipping Vitest execution inside Nginx.")
    
    # 4. Clean up
    print("\n[4/4] Cleaning up...")
    run_command(["docker", "compose", "down", "-v"])
    
    if test_failed:
        print("\n[RESULT] Automation finished with FAILURES.")
        sys.exit(1)
    else:
        print("\n[RESULT] Automation finished SUCCESSFULLY.")

if __name__ == "__main__":
    main()
