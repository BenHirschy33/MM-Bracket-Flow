import sys
import os
import time
import json
import requests
import pandas as pd
from pathlib import Path
import argparse
import logging
from io import StringIO

# Add project root and local_lib to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "local_lib"))

from scripts.sync_live_data import clean_team_name

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def get_mock_data(df_base):
    """Generates synthetic advanced metrics for testing."""
    import numpy as np
    logging.info("Generating mock advanced metrics...")
    
    # Base indicators
    df_base['AdjOffSQ'] = df_base['AdjO'] * np.random.uniform(0.95, 1.05, len(df_base))
    df_base['AdjDefSQ'] = df_base['AdjD'].fillna(100.0) * np.random.uniform(0.95, 1.05, len(df_base))
    df_base['Rim3Rate'] = np.random.uniform(0.3, 0.6, len(df_base))
    
    # Kill Shots (10-0 runs) - scale with efficiency
    eff_factor = (df_base['AdjO'] / df_base['AdjD'].fillna(100.0))
    df_base['KillShotsScored'] = (eff_factor * np.random.uniform(5, 12, len(df_base))).round(1)
    df_base['KillShotsConceded'] = ((1/eff_factor) * np.random.uniform(4, 9, len(df_base))).round(1)
    
    df_base['BPR'] = (df_base['AdjO'] - df_base['AdjD'].fillna(100.0)) / 2.0 + np.random.normal(0, 2, len(df_base))
    df_base['PaceVar'] = np.random.uniform(1.5, 4.5, len(df_base))
    # Recent Form: Peaking indicator (-5 to +5 net rating delta)
    df_base['RecentForm'] = np.random.uniform(-3, 3, len(df_base))
    
    return df_base

def fetch_shotquality_data(year=2026):
    """
    Scrapes ShotQuality team standings.
    """
    import cloudscraper
    from bs4 import BeautifulSoup
    
    url = f"https://www.shotquality.com/ncaam/{year}/team-standings"
    logging.info(f"Fetching ShotQuality data from {url}")
    
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code == 200:
            # ShotQuality often embeds data in a script tag or builds a table
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if table:
                df = pd.read_html(StringIO(str(table)))[0]
                # Map columns (Expected: Team, Adj Off SQ, Adj Def SQ, Rim & 3 Rate)
                # Note: Column names vary, we'll use fuzzy matching or indices
                result = []
                for _, row in df.iterrows():
                    team = clean_team_name(str(row.iloc[0]))
                    result.append({
                        "Team": team,
                        "AdjOffSQ": safe_float(row.get('Adj Off SQ', row.iloc[1])),
                        "AdjDefSQ": safe_float(row.get('Adj Def SQ', row.iloc[2])),
                        "Rim3Rate": safe_float(row.get('Rim & 3 Rate', row.iloc[3]))
                    })
                return pd.DataFrame(result)
    except Exception as e:
        logging.error(f"ShotQuality scrape failed: {e}")
    
    return pd.DataFrame() 

def fetch_evanmiya_data():
    """
    Scrapes EvanMiya team ratings.
    """
    import cloudscraper
    from bs4 import BeautifulSoup
    
    url = "https://evanmiya.com/"
    logging.info(f"Fetching EvanMiya data from {url}")
    
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # EvanMiya rankings are often in a div or table
            table = soup.find('table') 
            if table:
                df = pd.read_html(StringIO(str(table)))[0]
                result = []
                for _, row in df.iterrows():
                    team = clean_team_name(str(row.iloc[0]))
                    result.append({
                        "Team": team,
                        "KillShotsScored": safe_float(row.get('Kill Shots', row.iloc[1])),
                        "KillShotsConceded": safe_float(row.get('Kill Shots Allowed', row.iloc[2])),
                        "BPR": safe_float(row.get('BPR', row.iloc[3]))
                    })
                return pd.DataFrame(result)
    except Exception as e:
        logging.error(f"EvanMiya scrape failed: {e}")
    return pd.DataFrame()

def safe_float(val):
    try:
        if pd.isna(val) or str(val).strip() == "" or val == "None":
            return 0.0
        return float(str(val).replace('%', '')) / 100.0 if '%' in str(val) else float(val)
    except: return 0.0

def sync_advanced_metrics(year=2026, use_mock=False):
    stats_path = Path(f"years/{year}/data/team_stats.csv")
    if not stats_path.exists():
        logging.error(f"Base stats file not found: {stats_path}")
        return

    df_base = pd.read_csv(stats_path)
    
    if use_mock:
        df_base = get_mock_data(df_base)
    else:
        # Fetch data
        df_sq = fetch_shotquality_data(year)
        df_em = fetch_evanmiya_data()
        
        # Merge ShotQuality
        if not df_sq.empty:
            df_base = pd.merge(df_base, df_sq, on="Team", how="left")
        
        # Merge EvanMiya
        if not df_em.empty:
            df_base = pd.merge(df_base, df_em, on="Team", how="left")

        # Fill missing with reasonable defaults or derived values
        if 'AdjOffSQ' not in df_base.columns: df_base['AdjOffSQ'] = df_base['AdjO']
        if 'AdjDefSQ' not in df_base.columns: df_base['AdjDefSQ'] = df_base['AdjD'].fillna(100.0)
        if 'Rim3Rate' not in df_base.columns: df_base['Rim3Rate'] = 0.45
        if 'KillShotsScored' not in df_base.columns: df_base['KillShotsScored'] = 7.0
        if 'KillShotsConceded' not in df_base.columns: df_base['KillShotsConceded'] = 7.0
        if 'BPR' not in df_base.columns: df_base['BPR'] = 0.0
        if 'PaceVar' not in df_base.columns: df_base['PaceVar'] = 2.5
        if 'RecentForm' not in df_base.columns: df_base['RecentForm'] = 0.0

    # Ensure final cleanup of NaNs
    df_base.fillna(0.0, inplace=True)
    
    # Save the updated CSV
    df_base.to_csv(stats_path, index=False)
    logging.info(f"Successfully updated {stats_path} with advanced metrics (Mocked: {use_mock}).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of scraping")
    args = parser.parse_args()
    sync_advanced_metrics(args.year, args.mock)
