# MM-Bracket-Flow

A perpetual March Madness prediction engine, designed to augment statistical analysis with human intuition. Built with a modular architecture to support multi-year bracket simulations, starting with the 2026 campaign.

## Philosophy
**MM-Bracket-Flow** is built on the premise that raw statistical models (like KenPom and NET) are powerful algorithms, but they lack the nuanced "gut feeling" of seasoned college basketball analysts. This repository combining objective data with subjective intuition—the **Hirschy Factor**.

Our architecture is expressly designed for longevity. The `/core` directory houses year-agnostic simulation logic, while season-specific data—starting with 2026—is siloed elegantly in `/years/YYYY/`.

## The Intuition Engine (The "Hirschy Factor")
The core driver of subjective adjustments is `core/intuition_config.yaml`. 
You can input a **Human Intuition Score** ranging from `-10` to `+10` for any team.

- `+10`: Extremely high confidence the team will overperform its metrics.
- `-10`: Significant belief the team is poised for an early upset or will drastically underperform.

**How to refine:**
Open `core/intuition_config.yaml` and tweak the seasonal weights. The core simulation engine incorporates these multipliers to adjust the baseline probabilities when simulating matchups. 

## 2026 Data Sources & Confidence
This year's initial projections draw from:
*   Selection Sunday (March 15, 2026) seedings and major early projections.
*   **KenPom Rankings:** Duke, Michigan, Arizona, and Florida feature prominently as balanced efficiency juggernauts (Top 25 Offense/Defense rule) and project as No. 1 seeds.

**Baseline Assumption Confidence Score: 85.5%**
The current 'Chalk' bracket structure (`/years/2026/data/chalk_bracket.json`) reflects a high degree of confidence in the top tier statistically, but anticipates adjustments as the Hirschy Factor is mapped in.

## Dynamic Updating (Second Chance Brackets)
The tournament is fluid, and brackets bust. Use `core/live_update_handler.py` to input actual game winners as they happen in real-time. The framework instantly consumes these results to re-simulate "Second Chance" brackets for the remaining rounds based on actual survivors.


## Installation

1.  **Cloning the Repository:**
    ```bash
    git clone [repository-url]
    cd MM-Bracket-Flow
    ```

2.  **Environment Setup:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -e .
    pip install ruff
    ```

## Running the App

1.  **Start the Flask Backend:**
    ```bash
    python web/app.py
    ```
    The server will start at `http://127.0.0.1:5001`.

2.  **Access the UI:**
    Open `web/templates/index.html` in your browser (or serve it through a local server if needed).

## Contribution Guidelines & Safeguards
*Local-Only Commit Policy*: Because statistical and live-update integrity is paramount, this repository observes strict push protections. Push commands are governed by manual review to ensure the perpetual simulator isn't tainted by accidental data overwrites.
