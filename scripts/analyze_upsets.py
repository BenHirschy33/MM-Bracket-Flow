import json
import sys
import csv
from pathlib import Path

# Ensure we use the local core package
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.parser import load_teams, load_bracket
from core.config import SimulationWeights

# Years to analyze
YEARS = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]

def analyze_upsets():
    print(f"Analyzing historical upsets (#11-#15 seeds)...")
    upset_profiles = []
    
    for year in YEARS:
        base_dir = Path(f"years/{year}/data")
        try:
            teams_data = load_teams(base_dir / "team_stats.csv", year=year)
            with open(base_dir / "actual_results.json", 'r') as f:
                actual_results = json.load(f)
        except FileNotFoundError:
            continue

        r32_teams = set(actual_results.get("round_of_32", []))
        
        # Identify teams in R32 that were high seeds
        for team_name, team in teams_data.items():
            if team.seed and team.seed >= 11 and team_name in r32_teams:
                # This is a Cinderella!
                profile = {
                    "year": year,
                    "team": team_name,
                    "seed": team.seed,
                    "off_efg": team.off_efg_pct,
                    "to_pct": team.off_to_pct,
                    "three_par": team.three_par,
                    "pace": team.pace,
                    "sos": team.sos
                }
                upset_profiles.append(profile)
    
    if not upset_profiles:
        print("No upsets found in the dataset.")
        return

    # Average Cinderella stats
    avg_3par = sum(p["three_par"] for p in upset_profiles if p["three_par"]) / len(upset_profiles)
    avg_to = sum(p["to_pct"] for p in upset_profiles if p["to_pct"]) / len(upset_profiles)
    avg_sos = sum(p["sos"] for p in upset_profiles if p["sos"]) / len(upset_profiles)
    
    print(f"\nUpset Profile Identified ({len(upset_profiles)} teams):")
    print(f"- Avg 3PAr: {round(avg_3par, 3)}")
    print(f"- Avg TO%: {round(avg_to, 3)}")
    print(f"- Avg SOS: {round(avg_sos, 3)}")
    
    # Let's compare to total population
    all_3par = []
    for year in YEARS:
        base_dir = Path(f"years/{year}/data")
        try:
            teams_data = load_teams(base_dir / "team_stats.csv", year=year)
            for team in teams_data.values():
                if team.three_par: all_3par.append(team.three_par)
        except: continue
        
    pop_avg_3par = sum(all_3par) / len(all_3par)
    print(f"- Population Avg 3PAr: {round(pop_avg_3par, 3)}")
    
    if avg_3par > pop_avg_3par:
        print(f"\nINSIGHT: Cinderella teams have higher 3-point attempt rates (+{round(100*(avg_3par/pop_avg_3par - 1), 1)}%)")

if __name__ == "__main__":
    analyze_upsets()
