import argparse
import sys
import math
import random
import logging
import numpy as np
from pathlib import Path

# Ensure we use the local core package
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import SimulationWeights
from scripts.evaluate_weights import evaluate_bracket

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Expanded years for better generalization (including earlier years)
YEARS = [2000, 2005, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025]

# USER Feedback: Stronger weighting for past 4 years (2021-2025).
# 2021-2025: 1.0 | 2011-2020: 0.7 | 2000-2010: 0.3
def get_era_weight(year):
    if year >= 2021: return 1.0
    if year >= 2011: return 0.7
    return 0.3

ERA_WEIGHTS = {y: get_era_weight(y) for y in YEARS}

def get_multi_year_scores(weights: SimulationWeights, years_list):
    """Calculates weighted scores across a specific list of years."""
    weighted_scores = []
    for year in years_list:
        score, _ = evaluate_bracket(year, weights, iterations=2)
        if score > 0:
            era_weight = ERA_WEIGHTS.get(year, 1.0)
            weighted_scores.append(score * era_weight)
    return weighted_scores

def cross_validate_weights(weights: SimulationWeights):
    """
    Performs Leave-One-Season-Out (LOSO) cross-validation.
    Returns the average validation score across all folds.
    """
    all_scores = get_multi_year_scores(weights, YEARS)
    if not all_scores:
        return 0, 0
    
    avg_score = np.mean(all_scores)
    std_score = np.std(all_scores)
    
    # Fitness = Average Score - (Penalty for high variance)
    # This prevents overfitting to a few "chalky" years
    fitness = avg_score - (0.2 * std_score)
    return fitness, avg_score

def optimize_simulated_annealing(iterations=10000, temp=2.0, cooling_rate=0.9998):
    """
    Phase 5: Ultra-Deep K-Fold Optimization Sweep.
    """
    # Start with baseline but apply requested Venue Bias (neutral_weight)
    current_weights = SimulationWeights()
    current_weights.neutral_weight = 0.25 
    
    current_fitness, current_avg = cross_validate_weights(current_weights)
    
    best_weights = current_weights
    best_fitness = current_fitness
    best_avg = current_avg
    
    print(f"Starting Phase 5: Definitive Truth Sweep...")
    print(f"Initial CV Fitness: {round(current_fitness, 2)} | Avg Score: {round(current_avg, 2)}")
    
    try:
        for i in range(iterations):
            temp_sa = iterations - i # Linear cooling
            
            # Neighborhood search: jitter weights
            new_params = {
                "efficiency_weight": max(0, current_weights.efficiency_weight + random.uniform(-0.02, 0.02)),
                "to_weight": max(0, current_weights.to_weight + random.uniform(-0.5, 0.5)),
                "ft_weight": max(0, current_weights.ft_weight + random.uniform(-0.5, 0.5)),
                "three_par_weight": max(0, current_weights.three_par_weight + random.uniform(-0.5, 0.5)),
                "pace_variance_weight": max(0, current_weights.pace_variance_weight + random.uniform(-0.1, 0.1)),
                "momentum_weight": max(0, current_weights.momentum_weight + random.uniform(-0.01, 0.01)),
                "sos_weight": max(0, current_weights.sos_weight + random.uniform(-0.5, 0.5)),
                "defense_premium": max(0.5, current_weights.defense_premium + random.uniform(-0.5, 0.5)),
                
                # Phase 4/5/6 Metrics
                "foul_drawing_weight": max(0, current_weights.foul_drawing_weight + random.uniform(-0.5, 0.5)),
                "stl_weight": max(0, current_weights.stl_weight + random.uniform(-0.5, 0.5)),
                "blk_weight": max(0, current_weights.blk_weight + random.uniform(-0.5, 0.5)),
                "orb_weight": max(0, current_weights.orb_weight + random.uniform(-0.5, 0.5)),
                "luck_weight": current_weights.luck_weight + random.uniform(-0.5, 0.5), 
                "due_factor_sensitivity": max(0, current_weights.due_factor_sensitivity + random.uniform(-0.01, 0.01)),
                "momentum_regression_weight": max(0, current_weights.momentum_regression_weight + random.uniform(-0.1, 0.1)),
                "road_dominance_weight": max(0, current_weights.road_dominance_weight + random.uniform(-0.5, 0.5)),
                "seed_weight": max(0.005, min(0.1, current_weights.seed_weight + random.uniform(-0.005, 0.005))),
                "ast_weight": max(0, current_weights.ast_weight + random.uniform(-0.5, 0.5)),
                "three_par_volatility_weight": max(0, current_weights.three_par_volatility_weight + random.uniform(-0.05, 0.05)),
                "ts_weight": max(0, current_weights.ts_weight + random.uniform(-0.5, 0.5)),
                "experience_weight": max(0, current_weights.experience_weight + random.uniform(-0.001, 0.001)),
                "late_round_def_premium": max(0, current_weights.late_round_def_premium + random.uniform(-0.05, 0.05)),
                "neutral_weight": max(0, current_weights.neutral_weight + random.uniform(-0.2, 0.2)),
                "non_conf_weight": max(0, current_weights.non_conf_weight + random.uniform(-0.2, 0.2)),
                "def_ft_rate_weight": max(0, current_weights.def_ft_rate_weight + random.uniform(-0.5, 0.5)),
                "depth_weight": max(0, current_weights.depth_weight + random.uniform(-0.1, 0.1)),
                "continuity_weight": max(0, current_weights.continuity_weight + random.uniform(-0.1, 0.1)),
                "pace_control_weight": max(0, current_weights.pace_control_weight + random.uniform(-0.1, 0.1)),
                "cinderella_factor": max(0, current_weights.cinderella_factor + random.uniform(-0.2, 0.2)),
                "luck_regression_weight": max(0, current_weights.luck_regression_weight + random.uniform(-0.5, 0.5)),
                "star_reliance_weight": max(0, current_weights.star_reliance_weight + random.uniform(-0.2, 0.2)),
                
                # 2025 Research Indicators
                "orb_density_weight": max(0, current_weights.orb_density_weight + random.uniform(-0.2, 0.2)),
                "continuation_rule_bias": max(0, current_weights.continuation_rule_bias + random.uniform(-0.01, 0.01)),
                
                # Research Loop 1: Coach & Tempo
                "coach_tournament_weight": max(0, current_weights.coach_tournament_weight + random.uniform(-0.1, 0.1)),
                "tempo_upset_weight": max(0, current_weights.tempo_upset_weight + random.uniform(-0.05, 0.05)),
                
                # Phase 5: Fatigue & Orchestration
                "fatigue_sensitivity": max(0, current_weights.fatigue_sensitivity + random.uniform(-0.1, 0.1)),
                "bench_rest_bonus": max(0, current_weights.bench_rest_bonus + random.uniform(-0.1, 0.1)),

                # Rounds 11-15: Fine-Grained Context
                "travel_weight": max(0, current_weights.travel_weight + random.uniform(-0.1, 0.1)),
                "pressure_weight": max(0, current_weights.pressure_weight + random.uniform(-0.1, 0.1)),
                "chemistry_weight": max(0, current_weights.chemistry_weight + random.uniform(-0.1, 0.1)),
                "freshman_weight": max(0, current_weights.freshman_weight + random.uniform(-0.1, 0.1)),

                # Rounds 16-20: Roster & Depth Suite
                "backcourt_weight": max(0, current_weights.backcourt_weight + random.uniform(-0.1, 0.1)),
                "bench_synergy_weight": max(0, current_weights.bench_synergy_weight + random.uniform(-0.1, 0.1)),
                "whistle_mastery_weight": max(0, current_weights.whistle_mastery_weight + random.uniform(-0.1, 0.1)),
                "heating_up_weight": max(0, current_weights.heating_up_weight + random.uniform(-0.1, 0.1)),

                # Rounds 21-25: Strategy & Adaptability
                "adjustment_weight": max(0, current_weights.adjustment_weight + random.uniform(-0.1, 0.1)),
                "zone_defense_weight": max(0, current_weights.zone_defense_weight + random.uniform(-0.1, 0.1)),
                "foul_management_weight": max(0, current_weights.foul_management_weight + random.uniform(-0.1, 0.1)),
                "clutch_execution_weight": max(0, current_weights.clutch_execution_weight + random.uniform(-0.01, 0.01)),

                # Rounds 26-30: Post-Season Volatility
                "conference_weight": max(0, current_weights.conference_weight + random.uniform(-0.1, 0.1)),
                "neutral_variance_weight": max(0, current_weights.neutral_variance_weight + random.uniform(-0.1, 0.1)),
                "rust_penalty": max(0, current_weights.rust_penalty + random.uniform(-0.02, 0.02)),
                "rhythm_bonus": max(0, current_weights.rhythm_bonus + random.uniform(-0.02, 0.02)),

                # Rounds 31-33: Final Convergence
                "intuition_factor_weight": max(0, current_weights.intuition_factor_weight + random.uniform(-0.1, 0.1)),
                "blue_blood_bonus": max(0, current_weights.blue_blood_bonus + random.uniform(-0.1, 0.1)),

                # Rounds 34-40: Batch 6 - Situational Mastery
                "shot_clock_weight": max(0, current_weights.shot_clock_weight + random.uniform(-0.1, 0.1)),
                "drought_weight": max(0, current_weights.drought_weight + random.uniform(-0.1, 0.1)),
                "follow_up_weight": max(0, current_weights.follow_up_weight + random.uniform(-0.1, 0.1)),
                "stopper_weight": max(0, current_weights.stopper_weight + random.uniform(-0.1, 0.1)),
                "three_volatility_weight": max(0, current_weights.three_volatility_weight + random.uniform(-0.1, 0.1)),
                "timeout_weight": max(0, current_weights.timeout_weight + random.uniform(-0.1, 0.1)),
                "proximity_weight": max(0, current_weights.proximity_weight + random.uniform(-0.1, 0.1)),

                # Rounds 41-50: Batch 7 - Roster & Health Stability
                "foul_resilience_weight": max(0, current_weights.foul_resilience_weight + random.uniform(-0.1, 0.1)),
                "ot_depth_weight": max(0, current_weights.ot_depth_weight + random.uniform(-0.1, 0.1)),
                "usage_fatigue_weight": max(0, current_weights.usage_fatigue_weight + random.uniform(-0.1, 0.1)),
                "portal_chemistry_weight": max(0, current_weights.portal_chemistry_weight + random.uniform(-0.1, 0.1)),
                "rust_reset_weight": max(0, current_weights.rust_reset_weight + random.uniform(-0.1, 0.1)),
                "playin_rhythm_weight": max(0, current_weights.playin_rhythm_weight + random.uniform(-0.1, 0.1)),
                "three_def_sos_weight": max(0, current_weights.three_def_sos_weight + random.uniform(-0.1, 0.1)),
                "backcourt_exp_weight": max(0, current_weights.backcourt_exp_weight + random.uniform(-0.1, 0.1)),
                "rim_protection_weight": max(0, current_weights.rim_protection_weight + random.uniform(-0.1, 0.1)),
                "choke_factor_weight": max(0, current_weights.choke_factor_weight + random.uniform(-0.1, 0.1)),

                # Rounds 51-60: Batch 8 - Era-Specific Historical Replay
                "defensive_grit_bias": max(0, current_weights.defensive_grit_bias + random.uniform(-0.1, 0.1)),
                "three_point_dominance": max(0, current_weights.three_point_dominance + random.uniform(-0.1, 0.1)),
                "rim_pressure_multiplier": max(0, current_weights.rim_pressure_multiplier + random.uniform(-0.1, 0.1)),
                "pace_sensitivity": max(0, current_weights.pace_sensitivity + random.uniform(-0.1, 0.1)),

                # Rounds 61-70: Batch 9 - Advanced Tactical Mechanics
                "zone_efficiency_weight": max(0, current_weights.zone_efficiency_weight + random.uniform(-0.1, 0.1)),
                "press_disruption_weight": max(0, current_weights.press_disruption_weight + random.uniform(-0.1, 0.1)),
                "pace_control_weight": max(0, current_weights.pace_control_weight + random.uniform(-0.1, 0.1)),
                "rotation_depth_weight": max(0, current_weights.rotation_depth_weight + random.uniform(-0.1, 0.1)),
                "half_adjustment_v2": max(0, current_weights.half_adjustment_v2 + random.uniform(-0.1, 0.1)),

                # Rounds 71-80: Batch 10 - Cinderella Dynamics
                "mid_major_boost": max(0, current_weights.mid_major_boost + random.uniform(-0.1, 0.1)),
                "cinderella_momentum": max(0, current_weights.cinderella_momentum + random.uniform(-0.1, 0.1)),
                "auto_qualifier_rhythm": max(0, current_weights.auto_qualifier_rhythm + random.uniform(-0.1, 0.1)),
                "seed_12_5_bias": max(0, current_weights.seed_12_5_bias + random.uniform(-0.1, 0.1)),

                # Rounds 81-93: Batch 11 - Clutch & Fatigue Management
                "clutch_efficiency_weight": max(0, current_weights.clutch_efficiency_weight + random.uniform(-0.1, 0.1)),
                "short_bench_boost": max(0, current_weights.short_bench_boost + random.uniform(-0.1, 0.1)),
                "pressure_stability_weight": max(0, current_weights.pressure_stability_weight + random.uniform(-0.1, 0.1)),
                "coach_clutch_multiplier": max(0, current_weights.coach_clutch_multiplier + random.uniform(-0.1, 0.1)),

                # Rounds 94-100: Batch 12 - Tournament DNA & Calibration
                "blue_blood_aura": max(0, current_weights.blue_blood_aura + random.uniform(-0.1, 0.1)),
                "committee_error_bias": max(0, current_weights.committee_error_bias + random.uniform(-0.1, 0.1)),

                # Phase 2: Rounds 101-110 - The Physicality Crisis
                "hand_check_penalty": max(0, current_weights.hand_check_penalty + random.uniform(-0.1, 0.1)),
                "post_dominance_weight": max(0, current_weights.post_dominance_weight + random.uniform(-0.1, 0.1)),
                "slow_pace_stability": max(0, current_weights.slow_pace_stability + random.uniform(-0.1, 0.1)),

                # Phase 2: Rounds 111-130
                "three_point_variance_multiplier": max(0, current_weights.three_point_variance_multiplier + random.uniform(-0.1, 0.1)),
                "freedom_of_movement_boost": max(0, current_weights.freedom_of_movement_boost + random.uniform(-0.1, 0.1)),
                "portal_instability_penalty": max(0, current_weights.portal_instability_penalty + random.uniform(-0.1, 0.1)),
                "nil_resource_advantage": max(0, current_weights.nil_resource_advantage + random.uniform(-0.1, 0.1)),
                
                # Phase 2: Rounds 131-150
                "conf_tourney_marathon_fatigue": max(0, current_weights.conf_tourney_marathon_fatigue + random.uniform(-0.1, 0.1)),
                "elite_conf_momentum_boost": max(0, current_weights.elite_conf_momentum_boost + random.uniform(-0.1, 0.1)),
                "altitude_fatigue_penalty": max(0, current_weights.altitude_fatigue_penalty + random.uniform(-0.1, 0.1)),
                "altitude_ft_decay": max(0, current_weights.altitude_ft_decay + random.uniform(-0.1, 0.1)),

                # Phase 2: Rounds 151-180
                "star_reliance_penalty": max(0, current_weights.star_reliance_penalty + random.uniform(-0.1, 0.1)),
                "deep_bench_stability": max(0, current_weights.deep_bench_stability + random.uniform(-0.1, 0.1)),
                "coach_final_four_aura": max(0, current_weights.coach_final_four_aura + random.uniform(-0.1, 0.1)),
                "quad_1_resilience_weight": max(0, current_weights.quad_1_resilience_weight + random.uniform(-0.1, 0.1)),

                # Phase 2: Rounds 181-200
                "three_point_gravity_weight": max(0, current_weights.three_point_gravity_weight + random.uniform(-0.1, 0.1)),
                "era_crossover_stability": max(0, current_weights.era_crossover_stability + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 201-215
                "glass_pace_interaction_weight": max(0, current_weights.glass_pace_interaction_weight + random.uniform(-0.1, 0.1)),
                "small_ball_bias_modern": max(0, current_weights.small_ball_bias_modern + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 216-230
                "low_seed_adrenaline_crash": max(0, current_weights.low_seed_adrenaline_crash + random.uniform(-0.1, 0.1)),
                "eleven_seed_sustainability": max(0, current_weights.eleven_seed_sustainability + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 231-250
                "composure_index_weight": max(0, current_weights.composure_index_weight + random.uniform(-0.1, 0.1)),
                "upset_delta_weight": max(0, current_weights.upset_delta_weight + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 251-265
                "rim_contest_frequency_weight": max(0, current_weights.rim_contest_frequency_weight + random.uniform(-0.1, 0.1)),
                "off_ball_movement_weight": max(0, current_weights.off_ball_movement_weight + random.uniform(-0.1, 0.1)),
                "gravity_adjusted_3p_weight": max(0, current_weights.gravity_adjusted_3p_weight + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 266-280
                "era_excellence_physicality_weight": max(0, current_weights.era_excellence_physicality_weight + random.uniform(-0.1, 0.1)),
                "era_excellence_modern_weight": max(0, current_weights.era_excellence_modern_weight + random.uniform(-0.1, 0.1)),
                "portal_instability_coefficient_weight": max(0, current_weights.portal_instability_coefficient_weight + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 281-300
                "elite_eight_cinderella_wall": max(0, current_weights.elite_eight_cinderella_wall + random.uniform(-0.1, 0.1)),
                "blue_blood_final_weekend_boost": max(0, current_weights.blue_blood_final_weekend_boost + random.uniform(-0.1, 0.1)),
                "veteran_backcourt_scaling": max(0, current_weights.veteran_backcourt_scaling + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 301-315
                "defensive_switching_continuity": max(0, current_weights.defensive_switching_continuity + random.uniform(-0.1, 0.1)),
                "mid_range_march_value": max(0, current_weights.mid_range_march_value + random.uniform(-0.1, 0.1)),
                "defensive_versatility_index": max(0, current_weights.defensive_versatility_index + random.uniform(-0.1, 0.1)),

                # Cycle 3: Rounds 316-333
                "tournament_aura_boost": max(0, current_weights.tournament_aura_boost + random.uniform(-0.1, 0.1)),
                "accumulative_travel_fatigue": max(0, current_weights.accumulative_travel_fatigue + random.uniform(-0.1, 0.1)),
                "championship_pedigree_weight": max(0, current_weights.championship_pedigree_weight + random.uniform(-0.1, 0.1)),

                "chaos_mode": False
            }
            
            new_weights = SimulationWeights(**new_params)
            new_fitness, new_avg = cross_validate_weights(new_weights)
            
            # Acceptance probability
            if new_fitness > current_fitness:
                best_weights = new_weights
                best_fitness = new_fitness
                best_avg = new_avg
                current_weights = new_weights
                current_fitness = new_fitness
                print(f"[{i}] New Global Best! Fitness: {round(best_fitness, 2)} | Avg: {round(best_avg, 2)} | Temp: {round(temp_sa, 2)}")
            else:
                delta = new_fitness - current_fitness
                # Standard SA acceptance
                if random.random() < math.exp(delta / max(0.0001, temp_sa/1000.0)): # Normalized temp
                    current_weights = new_weights
                    current_fitness = new_fitness
            
            if i % 100 == 0:
                print(f"Iter {i}/{iterations} | Best Fitness: {round(best_fitness, 2)}")

    except KeyboardInterrupt:
        print("\nOptimization interrupted by user. Saving current best...")
    except Exception as e:
        print(f"\nCRITICAL ERROR during optimization: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n=======================================================")
        print(f"Final Best CV Fitness: {round(best_fitness, 2)}")
        print(f"Final Average Cross-Season Score: {round(best_avg, 2)}")
        print(f"Best Configuration: \n{best_weights}")
        print("=======================================================")
        
        # Save to agents/optimization/
        try:
            with open("agents/optimization/best_weights.txt", "w") as f:
                f.write(f"Best CV Fitness: {best_fitness}\n")
                f.write(f"Final Average Score: {best_avg}\n")
                f.write(str(best_weights))
            print("Successfully saved weights to agents/optimization/best_weights.txt")
        except Exception as e:
            print(f"Error saving to file: {e}")
            print("BEST WEIGHTS (COPY-PASTE READY):")
            print(best_weights)

        
        return best_weights

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--cooling_rate", type=float, default=0.9998)
    parser.add_argument("--modern_only", action="store_true", help="Only evaluate on 2018-2025")
    args = parser.parse_args()
    
    if args.modern_only:
        YEARS = [2018, 2019, 2021, 2022, 2023, 2024, 2025]
        print(f"MODERN MODE: Evaluating on {YEARS}")

    # Updated to Phase 5
    print(f"Starting Phase 5 optimization with {args.iterations} iterations...")
    optimize_simulated_annealing(iterations=args.iterations, cooling_rate=args.cooling_rate)
