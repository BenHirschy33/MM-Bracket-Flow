import argparse
import sys
import math
import random
import logging
import numpy as np
import concurrent.futures
import multiprocessing
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set start method to spawn for clean multiprocessing with numpy/sys.path
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeException:
    pass

from core.config import SimulationWeights
from scripts.evaluate_weights import evaluate_bracket

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Full historical window (2011-2024, excluding 2020)
YEARS = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]

def get_multi_year_results(weights: SimulationWeights, years_list, iterations=50, max_workers=None):
    """Calculates metrics across years in parallel with stability focus."""
    results = []
    # Use specified max_workers or default based on system thread count
    workers = max_workers if max_workers else min(10, multiprocessing.cpu_count())
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_year = {executor.submit(evaluate_bracket, year, weights, iterations): year for year in years_list}
        for future in concurrent.futures.as_completed(future_to_year):
            year = future_to_year[future]
            try:
                metrics = future.result()
                if metrics["avg_score"] >= 0:
                    metrics["year"] = year
                    results.append(metrics)
            except Exception as e:
                logging.error(f"Year {year} failed: {e}")
    return results

def recency_weight(year):
    return 0.5 + 0.5 * ((year - 2011) / (2024 - 2011))

def cross_validate_weights(weights: SimulationWeights, mode: str = "balanced", max_workers=None):
    """
    Performs Weighted Log-Likelihood fitness calculation.
    Fitness = sum(log_likelihood * year_weight)
    """
    results = get_multi_year_results(weights, YEARS, max_workers=max_workers)
    if not results:
        return -100000, 0, 0
    
    weighted_ll = np.sum([r.get("log_likelihood", -500.0) * recency_weight(r["year"]) for r in results])
    
    # Secondary metrics for display
    avg_score = np.mean([r["avg_score"] for r in results])
    avg_accuracy = np.mean([r["champion_accuracy"] for r in results])
    perfect_rate = np.mean([r["perfect_rate"] for r in results])
    
    # Fitness Calculation based on Mode
    if mode == "perfect":
        # Aggressive focus on Log-Likelihood and Perfect Bracket Probability
        fitness = weighted_ll + (perfect_rate * 15000)
    elif mode == "average":
        # Focus on pure average score
        fitness = (avg_score * 1.5) + weighted_ll
    else: # "balanced"
        # Balanced approach
        fitness = weighted_ll + (avg_score * 0.1) + (perfect_rate * 5000)
    
    return fitness, avg_score, avg_accuracy

def optimize_simulated_annealing(iterations=100000, mode="balanced", jitter_scale=1.0, max_workers=None):
    """
    Exhaustive "Gold Standard" Optimization V3.
    """
    current_weights = SimulationWeights()
    current_fitness, current_avg, current_acc = cross_validate_weights(current_weights, mode=mode, max_workers=max_workers)
    
    best_weights = current_weights
    best_fitness = current_fitness
    best_avg = current_avg
    best_acc = current_acc
    
    print(f"\n🚀 STARTING OPTIMIZATION V3 ({mode.upper()} FOCUS)...")
    print(f"Window: 2011-2024 | Iterations: {iterations}")
    print(f"Current Fitness: {round(current_fitness, 2)} | Avg Score: {round(current_avg, 1)} | Champ: {round(current_acc * 100, 1)}%")
    print("===============================================================================\n")

    try:
        for i in range(iterations):
            # Dynamic Jitter: Handle all 140+ fields
            new_params = vars(current_weights).copy()
            fields = list(new_params.keys())
            
            # Adaptive jump size
            temp_sa = 1.0 - (i / iterations)
            k = max(2, int(len(fields) * (0.1 + 0.2 * temp_sa)))
            jitter_targets = random.sample(fields, k=k)
            
            for field in jitter_targets:
                val = new_params[field]
                if isinstance(val, bool):
                    if random.random() < 0.05: 
                        new_params[field] = not val
                elif isinstance(val, (int, float)):
                    # Adaptive range based on current value and external jitter scale
                    magnitude = max(0.1, abs(val) * (0.1 + 0.4 * temp_sa) * jitter_scale)
                    step = random.uniform(-magnitude, magnitude)
                    new_val = val + step
                    
                    # Resilience Constraints
                    if field == "seed_weight":
                        new_params[field] = max(0.001, min(0.3, new_val))
                    elif field == "defense_premium":
                        new_params[field] = max(1.0, min(50.0, new_val))
                    elif field == "luck_weight":
                        new_params[field] = new_val # negative allowed
                    elif "pct" in field or "rate" in field:
                        new_params[field] = max(0, min(100, new_val))
                    else:
                        new_params[field] = max(0, new_val)

            new_weights = SimulationWeights(**new_params)
            new_fitness, new_avg, new_acc = cross_validate_weights(new_weights, mode=mode, max_workers=max_workers)
            
            # Acceptance logic (Maximize Fitness)
            if new_fitness > current_fitness:
                current_weights = new_weights
                current_fitness = new_fitness
                
                if new_fitness > best_fitness:
                    best_weights = new_weights
                    best_fitness = new_fitness
                    best_avg = new_avg
                    best_acc = new_acc
                    print(f"[{mode}] [{i}] ⭐ NEW BEST! Fit: {round(best_fitness, 2)} | Avg: {round(best_avg, 1)} | Champ: {round(best_acc * 100, 1)}%")
                    save_weights(best_weights, best_fitness, best_avg, best_acc, i, mode=mode)
            else:
                # Annealing rejection
                delta = new_fitness - current_fitness
                accept_prob = math.exp(delta / max(0.01, 50.0 * temp_sa))
                if random.random() < accept_prob:
                    current_weights = new_weights
                    current_fitness = new_fitness

            if i % 100 == 0:
                print(f"[{mode}] Progress: {i}/{iterations} | Best Fitness: {round(best_fitness, 2)} | Progress: {round(i/iterations*100, 2)}%")

    except KeyboardInterrupt:
        print("\nOptimization paused by user. Saving results...")
    finally:
        save_weights(best_weights, best_fitness, best_avg, best_acc, "FINAL", mode=mode)
        print("\n=======================================================")
        print(f"Final Peak Fitness: {round(best_fitness, 2)}")
        print(f"Final Model Performance: {round(best_avg, 2)} avg points")
        print(f"Final Champion Certainty: {round(best_acc * 100, 1)}%")
        print("Optimization Complete.")
        print("=======================================================")

def save_weights(weights, fitness, avg, acc, iteration, mode="unknown"):
    try:
        # Save mode-specific text file for human review
        save_path = Path(f"agents/optimization/best_weights_{mode}.txt")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            f.write(f"Metadata: Iteration={iteration}, Fitness={fitness}, AvgPoints={avg}, ChampAcc={acc}, Mode={mode}\n")
            f.write(str(weights))
        
        # Save JSON version for specific mode promotion
        import dataclasses
        import json
        json_path = Path(f"agents/optimization/last_best_weights_{mode}.json")
        with open(json_path, "w") as f:
            json.dump(dataclasses.asdict(weights), f, indent=2)
    except Exception as e:
        logging.error(f"Save failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100000)
    parser.add_argument("--jitter-scale", type=float, default=1.0)
    parser.add_argument("--mode", type=str, choices=["balanced", "average", "perfect"], default="balanced")
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    optimize_simulated_annealing(iterations=args.iterations, mode=args.mode, jitter_scale=args.jitter_scale, max_workers=args.workers)
