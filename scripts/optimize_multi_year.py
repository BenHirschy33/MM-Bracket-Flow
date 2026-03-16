import sys
from pathlib import Path
from core.config import SimulationWeights
from scripts.evaluate_weights import evaluate_bracket
import math
import random

def get_decay_weight(year, current_year=2026, k=0.05):
    # Exponential decay: e^(-k * delta_t)
    return math.exp(-k * (current_year - year))

def optimize():
    print("--- Starting Multi-Year Simulated Annealing Optimization ---")
    
    # Starting with our best known configuration
    current_weights = SimulationWeights(
        trb_weight=2.606,
        to_weight=0.840,
        sos_weight=3.171,
        momentum_weight=1.229,
        efficiency_weight=0.887,
        defense_premium=1.750,
        seed_weight=0.0,
        intuition_weight=0.0
    )
    
    best_weights = current_weights
    
    iterations = 300 # Adjusted for 5-year evaluation
    mc_iters = 50    # Balanced: fast enough to run 5 years per iteration
    decay_rate = 0.05
    
    years = [2025, 2024, 2023, 2022, 2021]
    
    def evaluate(weights):
        weighted_score, total_decay = 0, 0
        for y in years:
            score, _ = evaluate_bracket(y, weights, iterations=mc_iters)
            decay = get_decay_weight(y, k=decay_rate)
            weighted_score += (score * decay)
            total_decay += decay
        return weighted_score / total_decay if total_decay > 0 else 0

    current_avg = evaluate(current_weights)
    best_avg = current_avg
    
    print(f"Baseline Average (Precision {mc_iters} iters): {round(current_avg, 2)}")
    
    attrs = ['trb_weight', 'to_weight', 'sos_weight', 'momentum_weight', 'efficiency_weight', 'defense_premium', 'seed_weight']
    
    T_initial = 10.0
    T_final = 0.1
    cooling_rate = (T_final / T_initial) ** (1 / iterations)
    
    T = T_initial
    
    for i in range(iterations):
        # Create a mutated copy of the current weights
        test_weights = SimulationWeights(
            trb_weight=current_weights.trb_weight,
            to_weight=current_weights.to_weight,
            sos_weight=current_weights.sos_weight,
            momentum_weight=current_weights.momentum_weight,
            efficiency_weight=current_weights.efficiency_weight,
            defense_premium=current_weights.defense_premium,
            seed_weight=current_weights.seed_weight,
            intuition_weight=0.0
        )
        
        # Perturb 1 to 3 random attributes
        num_mutations = random.randint(1, 3)
        mutated_attrs = random.sample(attrs, num_mutations)
        
        for attr in mutated_attrs:
            current_val = getattr(test_weights, attr)
            mutation_factor = random.uniform(0.8, 1.2)
            abs_change = random.uniform(-0.15, 0.15)
            new_val = max(0.0, current_val * mutation_factor + abs_change) 
            if attr == 'momentum_weight':
                new_val = current_val * mutation_factor + abs_change
            setattr(test_weights, attr, new_val)
            
        new_avg = evaluate(test_weights)
        
        # Acceptance logic
        deltaE = new_avg - current_avg
        if deltaE > 0:
            accept = True
        else:
            accept_prob = math.exp(deltaE / T)
            accept = random.random() < accept_prob
            
        if accept:
            current_avg = new_avg
            current_weights = test_weights
            
            if current_avg > best_avg:
                best_avg = current_avg
                best_weights = current_weights
                print(f"Iteration {i} [T={round(T,2)}]: New Best EV = {round(best_avg, 2)}")
                print(f"  TRB:{round(best_weights.trb_weight,3)} | TO:{round(best_weights.to_weight,3)} | SOS:{round(best_weights.sos_weight,3)} | Eff:{round(best_weights.efficiency_weight,3)} | Mom:{round(best_weights.momentum_weight,3)} | Def:{round(best_weights.defense_premium,3)} | Seed:{round(best_weights.seed_weight,3)}")
        
        T *= cooling_rate

    print("\n==========================================")
    print("      OPTIMAL EXPECTED VALUE WEIGHTS      ")
    print("==========================================")
    print(f"TRB Weight: {best_weights.trb_weight}")
    print(f"TO Weight: {best_weights.to_weight}")
    print(f"SOS Weight: {best_weights.sos_weight}")
    print(f"Momentum Weight: {best_weights.momentum_weight}")
    print(f"Efficiency Weight: {best_weights.efficiency_weight}")
    print(f"Defense Premium: {best_weights.defense_premium}")
    print(f"Seed Weight: {best_weights.seed_weight}")
    print(f"Final Average Cross-Year Score: {round(best_avg, 2)}")
    print("==========================================")
    
if __name__ == "__main__":
    optimize()
