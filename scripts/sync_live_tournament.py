import json
import logging
from pathlib import Path
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def sync_tournament_data(year=2026):
    """
    Simulates a live data sync for the tournament.
    In a production scenario, this would call an external API (e.g., ESPN, NCAA).
    For this implementation, it ensures the year directory exists and populates 
    initial placeholders if they are missing.
    """
    base_dir = Path(f"years/{year}/data")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    actual_results_path = base_dir / "actual_results.json"
    
    if not actual_results_path.exists():
        initial_results = {
            "round_of_32": [],
            "sweet_sixteen": [],
            "elite_eight": [],
            "final_four": [],
            "champion": None
        }
        with open(actual_results_path, 'w') as f:
            json.dump(initial_results, f, indent=2)
        logging.info(f"Initialized empty actual_results.json for {year}")
    else:
        logging.info(f"Sync complete for {year}. (Live results found)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()
    sync_tournament_data(args.year)
