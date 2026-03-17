import os
import time
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agents/optimization/orchestrator.log"),
        logging.StreamHandler()
    ]
)

HEARTBEAT_PATH = Path("agents/optimization/heartbeat.json")
BEST_WEIGHTS_PATH = Path("agents/optimization/best_weights.txt")

def update_heartbeat(status, fitness=0, avg_score=0):
    heartbeat = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "current_fitness": fitness,
        "current_avg_score": avg_score,
        "mode": "autonomous_scaling"
    }
    with open(HEARTBEAT_PATH, "w") as f:
        json.dump(heartbeat, f, indent=2)

def run_optimization_cycle(iterations=5000, modern_only=True):
    cmd = ["python3", "scripts/optimize_weights.py", "--iterations", str(iterations)]
    if modern_only:
        cmd.append("--modern_only")
    
    logging.info(f"Starting optimization cycle: {' '.join(cmd)}")
    update_heartbeat("RUNNING_OPTIMIZATION")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    last_fitness = 0
    last_avg = 0
    
    for line in process.stdout:
        print(line, end="")
        if "New Global Best!" in line:
            # Example: [260] New Global Best! Fitness: 170.31 | Avg: 208.92
            try:
                parts = line.split("|")
                fitness = float(parts[0].split("Fitness:")[1].strip())
                avg = float(parts[1].split("Avg:")[1].split("|")[0].strip())
                last_fitness = fitness
                last_avg = avg
                update_heartbeat("IMPROVING", fitness=fitness, avg_score=avg)
                logging.info(f"New Best: Fitness {fitness} | Avg {avg}")
            except:
                pass
                
    process.wait()
    return last_fitness, last_avg

def main():
    os.makedirs("agents/optimization", exist_ok=True)
    logging.info("Autonomous Orchestrator Started")
    
    cycle_count = 1
    while True:
        logging.info(f"--- Starting Cycle {cycle_count} ---")
        
        # Alternate between Modern and Deep (All Years) modes
        modern_mode = (cycle_count % 2 != 0)
        fitness, avg = run_optimization_cycle(iterations=5000, modern_only=modern_mode)
        
        logging.info(f"Cycle {cycle_count} Finished. Peak Fitness: {fitness}")
        update_heartbeat("IDLE_BETWEEN_CYCLES", fitness=fitness, avg_score=avg)
        
        # Small rest to allow FS sync
        time.sleep(10)
        cycle_count += 1

if __name__ == "__main__":
    main()
