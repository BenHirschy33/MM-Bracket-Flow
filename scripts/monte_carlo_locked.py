import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set
from core.parser import load_teams, load_bracket
from core.simulator import SimulatorEngine
from core.config import DEFAULT_WEIGHTS

def run_locked_simulation(year: int, iterations: int, locks_path: str = None):
    print(f"--- Running Locked Monte Carlo for {year} ({iterations} iterations) ---")
    
    base_dir = Path(f"years/{year}/data")
    try:
        teams_data = load_teams(base_dir / "team_stats.csv", year=year)
        bracket_data = load_bracket(base_dir / "chalk_bracket.json")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Load locks if provided
    locks = {}
    if locks_path:
        try:
            with open(locks_path, 'r') as f:
                locks = json.load(f)
            print(f"Loaded {len(locks)} user locks: {list(locks.keys())[:5]}...")
        except Exception as e:
            print(f"Error loading locks: {e}")

    # Results tracking: Winner -> Count
    tournament_winners = {}
    round_hits = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}} # round_num -> team_name -> count

    # We use the region structure to handle the bracket
    regions = bracket_data.get("regions", {})
    
    # Pre-calculate round names
    round_names = {1: "R64", 2: "R32", 3: "S16", 4: "E8", 5: "F4", 6: "CHAMP"}

    for i in range(iterations):
        engine = SimulatorEngine(teams=teams_data, weights=DEFAULT_WEIGHTS, locks=locks)
        final_four = []
        
        # Simulate regions
        for region_name, seeds_map in regions.items():
            current_teams = []
            # Seed matchups: (1,16), (8,9), (5,12), (4,13), (6,11), (3,14), (7,10), (2,15)
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
                    t1, t2 = current_teams[j], current_teams[j+1]
                    winner = engine.simulate_matchup(t1, t2, round_num)
                    next_round.append(winner)
                    round_hits[round_num][winner] = round_hits[round_num].get(winner, 0) + 1
                current_teams = next_round
                round_num += 1
            
            if current_teams:
                champ = current_teams[0]
                final_four.append(champ)
                # Elite Eight winner is round 4
                
        # Final Four (Round 5)
        if len(final_four) == 4:
            f1 = engine.simulate_matchup(final_four[0], final_four[1], 5)
            round_hits[5][f1] = round_hits[5].get(f1, 0) + 1
            
            f2 = engine.simulate_matchup(final_four[2], final_four[3], 5)
            round_hits[5][f2] = round_hits[5].get(f2, 0) + 1
            
            # Champ (Round 6)
            winner = engine.simulate_matchup(f1, f2, 6)
            round_hits[6][winner] = round_hits[6].get(winner, 0) + 1
            tournament_winners[winner] = tournament_winners.get(winner, 0) + 1

    # Reporting
    print("\n" + "="*40)
    print(f" CONDITIONAL PROBABILITY REPORT (Locks active)")
    print("="*40)
    
    # Top Champions
    sorted_champs = sorted(tournament_winners.items(), key=lambda x: x[1], reverse=True)
    print("\n[Projected National Champions]")
    for team, count in sorted_champs[:10]:
        prob = (count / iterations) * 100
        print(f"  - {team.ljust(15)}: {prob:5.1f}%")

    # Top Final Four Probability
    print("\n[Final Four Probability - Top 10]")
    f4_winners = sorted(round_hits[5].items(), key=lambda x: x[1], reverse=True)
    for team, count in f4_winners[:10]:
        prob = (count / iterations) * 100
        print(f"  - {team.ljust(15)}: {prob:5.1f}%")

    print("\n" + "="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--iter", type=int, default=1000)
    parser.add_argument("--locks", type=str, help="Path to JSON file with locks")
    args = parser.parse_args()
    
    run_locked_simulation(args.year, args.iter, args.locks)
