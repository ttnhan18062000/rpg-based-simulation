import os, subprocess, sys
root = sys.argv[1]
py = "/mnt/data/Working/rpg-based-simulation/.venv/bin/python"
names = sorted(n for n in os.listdir(os.path.join(root, "data/runs")) if n.startswith("run_"))
cmd = [py, "tools/gate_checks/done_checker_static.py", "--clean-data-runs"]
for n in names:
    cmd += ["--path", n]
r = subprocess.run(cmd, cwd=root, env={**os.environ, "PYTHONPATH": "."}, capture_output=True, text=True)
print(root.rsplit("/", 1)[1], "requested", len(names), "rc", r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] )
print("left:", len([n for n in os.listdir(os.path.join(root, "data/runs"))]))
