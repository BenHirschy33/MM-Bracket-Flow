import os
import shutil
from pathlib import Path

def clean_project():
    root = Path(__file__).parent.parent
    print(f"Cleaning project DNA at {root}...")

    # 1. Clean logs
    log_patterns = ["*.log", "web_server.log", "optimization_sweep.log", "autonomous_optimizer.log"]
    for pattern in log_patterns:
        for p in root.rglob(pattern):
            try:
                print(f"Deleting log: {p.relative_to(root)}")
                p.unlink()
            except Exception as e:
                print(f"Failed to delete {p}: {e}")

    # 2. Clean __pycache__
    for p in root.rglob("__pycache__"):
        try:
            print(f"Deleting pycache: {p.relative_to(root)}")
            shutil.rmtree(p)
        except Exception as e:
            print(f"Failed to delete {p}: {e}")

    # 3. Clean temporary artifacts/test files mentioned by USER
    temp_files = ["phase5_optimal_weights.txt", "test_sr.py"]
    for f in temp_files:
        try:
            p = root / f
            if p.exists():
                print(f"Deleting temp file: {f}")
                p.unlink()
        except Exception as e:
            print(f"Failed to delete {f}: {e}")

    print("DNA sequence cleaned.")

if __name__ == "__main__":
    clean_project()
