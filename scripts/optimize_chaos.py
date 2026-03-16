import sys
import math
import random
import logging
from pathlib import Path

# Ensure we use the local core package
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import SimulationWeights, CHAOS_WEIGHTS
from scripts.evaluate_weights import evaluate_bracket

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Years to use for chaos optimization
YEARS = [2018, 2019, 2021, 2022, 2023, 2024]

def get_chaos_fitness(weights: SimulationWeights):
    """
    Calculates fitness based on predicting upsets (#11-#15 seeds).
    """
    total_upsets_correct = 0
    total_score = 0
    count = 0
    
    for year in YEARS:
        # We need a custom evaluator or a way to extract upset count from evaluate_bracket
        # For now, let's just use the score as a proxy but prioritize higher variance.
        score, _ = evaluate_bracket(year, weights, iterations=1)
        if score > 0:
            total_score += score
            count += 1
            
    avg_score = total_score / count if count > 0 else 0
    # In Chaos Mode, we actually want to see if we can get a high score 
    # despite picking more upsets.
    return avg_score

def optimize_chaos(iterations=1000, temp=1.0, cooling_rate=0.995):
    """
    Simulated Annealing to find the best CHAOS_WEIGHTS.
    """
    current_weights = CHAOS_WEIGHTS
    current_score = get_chaos_fitness(current_weights)
    
    best_weights = current_weights
    best_score = current_score
    
    print(f"Starting Chaos Optimization...")
    print(f"Initial Chaos Score: {round(current_score, 2)}")
    
    for i in range(iterations):
        # Exploration for chaos metrics (3PAr, FT, TO)
        new_params = {
            "trb_weight": 0.0,
            "to_weight": max(0, current_weights.to_weight + random.uniform(-1.0, 1.0)),
            "sos_weight": max(0, current_weights.sos_weight + random.uniform(-1.0, 1.0)),
            "momentum_weight": max(0, current_weights.momentum_weight + random.uniform(-0.5, 0.5)),
            "efficiency_weight": max(0, current_weights.efficiency_weight + random.uniform(-0.5, 0.5)),
            "ft_weight": max(0, current_weights.ft_weight + random.uniform(-1.0, 1.0)),
            "three_par_weight": max(0, current_weights.three_par_weight + random.uniform(-1.0, 1.0)),
            "pace_variance_weight": max(0, current_weights.pace_variance_weight + random.uniform(-0.5, 0.5)),
            "defense_premium": max(0, current_weights.defense_premium + random.uniform(-1.0, 1.0)),
            "chaos_mode": True,
            "intuition_weight": 0.0
        }
        
        new_weights = SimulationWeights(**new_params)
        new_score = get_chaos_fitness(new_weights)
        
        if new_score > current_score or random.random() < math.exp((new_score - current_score) / max(0.0001, temp)):
            current_weights = new_weights
            current_score = new_score
            
            if current_score > best_score:
                best_score = current_score
                best_weights = new_weights
                print(f"[{i}] New Chaos Best! Score: {round(best_score, 2)} | Temp: {round(temp, 4)}")
        
        temp *= cooling_rate
        
    print("\nChaos Optimization Complete!")
    print(f"Final Chaos Weights: \n{best_weights}")
    return best_weights

if __name__ == "__main__":
    optimize_chaos()
