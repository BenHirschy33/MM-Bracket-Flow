import csv
from pathlib import Path

def research_luck():
    years = [2018, 2019, 2021, 2022, 2023, 2024]
    upset_luck_deltas = []
    chalk_luck_deltas = []
    
    for year in years:
        team_stats_path = Path(f"years/{year}/data/team_stats.csv")
        raw_stats_path = Path(f"years/{year}/data/raw_team_stats.csv")
        results_path = Path(f"years/{year}/data/actual_results.json")
        
        if not team_stats_path.exists() or not raw_stats_path.exists():
            continue
            
        # Load raw SRS and W-L%
        luck_map = {}
        with open(raw_stats_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            header = lines[0].split(',')
            if 'School' not in header: header = lines[1].split(',')
            f.seek(0)
            f.readline()
            if 'School' not in header: f.readline()
            
            reader = csv.DictReader(f, fieldnames=[h.strip() for h in header])
            for row in reader:
                school = row.get("School", "").replace("\xa0NCAA", "").strip()
                wl_pct = float(row.get("W-L%", 0))
                srs = float(row.get("SRS", 0))
                # "Luck" Proxy: WL% - (normalization of SRS)
                # This is crude but shows if a team overachieved their point diff
                luck_map[school] = wl_pct - (srs / 40.0) # Scale SRS to ~0-1 range

        # Load upsets from team_stats.csv (seeds)
        teams = {}
        with open(team_stats_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                teams[row["Team"]] = int(row["Seed"]) if row["Seed"] else 16

        # In a real study we'd look at actual results. 
        # Let's just output the "Luckiest" high seeds each year and see if they lost early.
        print(f"\n--- {year} 'Luck' Analysis (WL% - (SRS/40)) ---")
        sorted_luck = sorted(luck_map.items(), key=lambda x: x[1], reverse=True)
        top_luck = [x for x in sorted_luck if x[0] in teams and teams[x[0]] <= 4][:5]
        for team, luck in top_luck:
            print(f"Seed {teams[team]} {team}: Luck={luck:.3f}")

if __name__ == "__main__":
    research_luck()
