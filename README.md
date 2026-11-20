# 1. Small dataset (5.4 MB) — shows process-spawn overhead on tiny workloads
python project.py sample_logs ERROR

# 2. Large dataset (285.69 MB) — shows true multi-core speedup (up to 2.97x)
python project.py large_logs ERROR

# (Optional) Regenerate large_logs anytime if needed
python generate_logs.py --files 64 --lines 100000