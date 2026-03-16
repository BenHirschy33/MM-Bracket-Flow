import argparse
import sys
import random
from pathlib import Path
from core.config import SimulationWeights
from scripts.evaluate_weights import evaluate_bracket

def optimize_random_search(year=2024, iterations=5000):
    best_score = -1
    best_weights = None
    
    print(f"Starting Random Search Optimization for {year} ({iterations} iterations)...")
    
    for i in range(iterations):
        weights = SimulationWeights(
            trb_weight=random.uniform(0.0, 3.0),
            to_weight=random.uniform(0.0, 2.0),
            sos_weight=random.uniform(0.0, 10.0),
            momentum_weight=random.uniform(-1.0, 3.0),
            efficiency_weight=random.uniform(0.0, 1.0),
            defense_premium=random.uniform(0.5, 2.5),
            intuition_weight=0.0 # Don't optimize intuition here
        )
        
        score, _ = evaluate_bracket(year, weights)
        
        if score > best_score:
            best_score = score
            best_weights = weights
            print(f"[{i}] New Best Score: {best_score} | Weights: {weights}")
            
    print("\n=======================================================")
    print(f"Optimization Complete!")
    print(f"Best Score: {best_score}")
    print(f"Best Configuration: \n{best_weights}")
    print("=======================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--iter", type=int, default=3000)
    args = parser.parse_args()
    optimize_random_search(args.year, iterations=args.iter)

