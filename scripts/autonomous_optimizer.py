import subprocess
import re
import sys
import os
import time

def run_optimization():
    print("\n--- Launching Optimization Episode (High Resolution) ---")
    # Using a higher iteration count for Phase 9 complexity
    cmd = ["python3", "scripts/optimize_weights.py", "--iterations", "3000"]
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":."
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    
    last_fitness = 0
    for line in process.stdout:
        print(line, end="")
        if "Final Best CV Fitness:" in line:
            match = re.search(r"Final Best CV Fitness: ([\d.]+)", line)
            if match:
                last_fitness = float(match.group(1))
    
    process.wait()
    return last_fitness

def start_autonomous_loop():
    print("🚀 Starting Autonomous Optimization Loop with 3-Strike Condition 🚀")
    
    best_overall_fitness = 0
    strikes = 0
    episode_count = 0
    
    while strikes < 3:
        episode_count += 1
        print(f"\n[Episode {episode_count}] Current Best: {best_overall_fitness} | Strikes: {strikes}")
        
        fitness = run_optimization()
        
        if fitness > best_overall_fitness:
            improvement = fitness - best_overall_fitness
            best_overall_fitness = fitness
            strikes = 0 # Reset strikes on improvement
            print(f"✅ IMPROVEMENT FOUND: +{improvement:.2f} | New Best: {best_overall_fitness}")
        else:
            strikes += 1
            print(f"❌ NO IMPROVEMENT: Strike {strikes}/3")
            
        time.sleep(2) # Brief cooldown

    print("\n" + "!"*60)
    print(" STOPPING: 3 Consecutive Episodes without Global Improvement")
    print(f" Final Gold Standard Fitness: {best_overall_fitness}")
    print("!"*60)
    
    # In a real environment, I would trigger a notify_user here.
    # Since I'm the agent, I'll stop the loop and wait for new instructions or report.

if __name__ == "__main__":
    start_autonomous_loop()
