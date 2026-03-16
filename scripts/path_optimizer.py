import argparse
import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Set, Tuple
from core.parser import load_teams, load_bracket
from core.simulator import SimulatorEngine
from core.config import DEFAULT_WEIGHTS

def optimize_path(target_team_name: str, year: int, iterations: int = 2000):
    print(f"--- Optimizing Ideal Path for {target_team_name} ({year}) ---")
    
    base_dir = Path(f"years/{year}/data")
    try:
        teams_data = load_teams(base_dir / "team_stats.csv", year=year)
        bracket_data = load_bracket(base_dir / "chalk_bracket.json")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    if target_team_name not in teams_data:
        print(f"Error: Team '{target_team_name}' not found in {year} data.")
        return

    # Tracking: Game -> Winner -> Success Count (when Target Team wins)
    # Game is defined by its ID or matchup
    path_correlations = {} # (team_a, team_b) -> {winner_name: success_count}
    target_success_count = 0

    regions = bracket_data.get("regions", {})
    
    for i in range(iterations):
        engine = SimulatorEngine(teams=teams_data, weights=DEFAULT_WEIGHTS)
        results_this_run = [] # List of (t1, t2, winner)
        
        # We need to simulate the whole bracket
        final_four = []
        target_won_champ = False
        
        # Simulate regions
        for region_name, seeds_map in regions.items():
            current_teams = []
            matchups = [(1,16), (8,9), (5,12), (4,13), (6,11), (3,14), (7,10), (2,15)]
            for h, l in matchups:
                th_name = seeds_map.get(str(h))
                tl_name = seeds_map.get(str(l))
                if th_name and tl_name:
                    teams_data[th_name].seed = h
                    teams_data[tl_name].seed = l
                    current_teams.append(th_name)
                    current_teams.append(tl_name)
            
            round_num = 1
            while len(current_teams) > 1:
                next_round = []
                for j in range(0, len(current_teams), 2):
                    t1_name, t2_name = current_teams[j], current_teams[j+1]
                    winner_name = engine.simulate_matchup(t1_name, t2_name, round_num)
                    results_this_run.append((t1_name, t2_name, winner_name))
                    next_round.append(winner_name)
                current_teams = next_round
                round_num += 1
            
            if current_teams:
                final_four.append(current_teams[0])

        # Final Four (Round 5)
        if len(final_four) == 4:
            f1_name = engine.simulate_matchup(final_four[0], final_four[1], 5)
            results_this_run.append((final_four[0], final_four[1], f1_name))
            
            f2_name = engine.simulate_matchup(final_four[2], final_four[3], 5)
            results_this_run.append((final_four[2], final_four[3], f2_name))
            
            # Champ (Round 6)
            winner_name = engine.simulate_matchup(f1_name, f2_name, 6)
            results_this_run.append((f1_name, f2_name, winner_name))
            
            if winner_name == target_team_name:
                target_won_champ = True
                target_success_count += 1

        # Calculate correlations if target won
        if target_won_champ:
            for t1, t2, winner in results_this_run:
                if t1 == target_team_name or t2 == target_team_name:
                    continue # Ignore games target actually played in
                
                game_key = tuple(sorted([t1, t2]))
                if game_key not in path_correlations:
                    path_correlations[game_key] = {}
                path_correlations[game_key][winner] = path_correlations[game_key].get(winner, 0) + 1

    # Frequency of target winning
    baseline_win_prob = (target_success_count / iterations) * 100
    print(f"\nBaseline Championship Probability: {baseline_win_prob:.1f}%")

    # Analyze path correlations
    # We want to find games where one winner is MUCH more frequent when the target wins
    significant_matchups = []
    
    for game_key, winners in path_correlations.items():
        if len(winners) < 2:
            continue
            
        t1, t2 = game_key
        count1 = winners.get(t1, 0)
        count2 = winners.get(t2, 0)
        total = count1 + count2
        
        # If one winner dominates > 65% of the success cases, it's significant
        if count1 / total > 0.65 or count2 / total > 0.65:
            ideal_winner = t1 if count1 > count2 else t2
            freq = max(count1, count2) / total
            significant_matchups.append((t1, t2, ideal_winner, freq))

    # Sort by frequency (most "ideal" winners first)
    significant_matchups.sort(key=lambda x: x[3], reverse=True)

    print("\n" + "="*50)
    print(f" IDEAL PATH AUDIT: Boosters for {target_team_name}")
    print("="*50)
    print(f"To maximize {target_team_name}'s chances, these outcomes should occur:")
    
    for t1, t2, winner, freq in significant_matchups[:15]:
        foe = t2 if winner == t1 else t1
        print(f"  - {winner.ljust(15)} beats {foe.ljust(15)} (at {freq*100:4.1f}% rate in successes)")

    print("\n" + "="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", type=str, required=True, help="Target team name")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--iter", type=int, default=2000)
    args = parser.parse_args()
    
    optimize_path(args.team, args.year, args.iter)
