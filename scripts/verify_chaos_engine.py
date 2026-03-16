import sys
from pathlib import Path

# Ensure we use the local core package
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import SimulationWeights, DEFAULT_WEIGHTS, CHAOS_WEIGHTS
from scripts.evaluate_weights import evaluate_bracket

# Years to test
YEARS = [2018, 2019, 2021, 2022, 2023, 2024]

def verify_chaos():
    print("=======================================================")
    print("CHAOS ENGINE VERIFICATION REPORT")
    print("=======================================================\n")
    
    total_chalk_score = 0
    total_chaos_score = 0
    
    print(f"{'Year':<6} | {'Chalk Score':<12} | {'Chaos Score':<12}")
    print("-" * 35)
    
    for year in YEARS:
        # Chalk Mode (Default Weights, chaos_mode=False)
        chalk_score, _ = evaluate_bracket(year, DEFAULT_WEIGHTS)
        
        # Chaos Mode (Chaos Weights, chaos_mode=True)
        chaos_score, _ = evaluate_bracket(year, CHAOS_WEIGHTS)
        
        print(f"{year:<6} | {chalk_score:<12.1f} | {chaos_score:<12.1f}")
        
        total_chalk_score += chalk_score
        total_chaos_score += chaos_score
        
    avg_chalk = total_chalk_score / len(YEARS)
    avg_chaos = total_chaos_score / len(YEARS)
    
    print("-" * 35)
    print(f"{'AVG':<6} | {avg_chalk:<12.1f} | {avg_chaos:<12.1f}")
    print("\n=======================================================")
    
    if avg_chaos > 0:
        improvement = (avg_chaos - avg_chalk)
        print(f"Chaos Engine Delta: {'+' if improvement >= 0 else ''}{round(improvement, 1)} pts")
    
    print("Baseline (Chalk) Accuracy Guardrail: PASSED" if avg_chalk >= 200 else "Baseline Accuracy Alert: Underperformed")
    print("=======================================================")

if __name__ == "__main__":
    verify_chaos()
