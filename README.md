# MM-Bracket-Flow V4: High-Fidelity Prediction Engine

**MM-Bracket-Flow** is a professional-grade March Madness simulation engine that bridges pure statistical efficiency with human intuition. V4 introduces a massive expansion in analytical depth and real-time visualization, powered by a calibrated 140+ variable model.

---

## 📖 Deep Dive: How it Works

### 1. The Sigmoid Resolution Model (`core/simulator.py`)
At the heart of the engine is a **calibrated Logistic (Sigmoid) function**. 
- **The Problem**: Linear probability models often overestimate favorites (giving a #1 seed a 99.9% win rate).
- **The Solution**: MM-Bracket-Flow uses a sigmoid squash that ensures realistic "Upset Risk". Even an elite favorite retains a 10-15% risk of loss in the early rounds, matching historical tournament parity.
- **Monte Carlo Loop**: Every game is resolved through 1,000+ internal iterations comparing the **Possession Efficiency Delta** of both teams, adjusted for recent form and "Kill Shot" spurts.

### 2. High-Fidelity Data & 140+ Variables
While the UI exposes 25 interactive sliders, the simulation engine utilizes **142 discrete variables** from the `gold_standard.json` weights.
- **Master Presets**:
    - **Standard**: Optimized for the 50th percentile of pool performance.
    - **Balanced**: A "Smart Money" approach that targets the 80th percentile.
    - **Perfect**: A high-variance model designed to maximize the joint probability of a "Perfect Bracket" based on 25 years of ground-truth data.
- **Deep Sync**: Selecting a preset loads the full high-dimensional optimization set, which the 25 UI sliders then act upon as "Master Offsets".

### 3. Real-Time Matchup Intelligence
Every matchup is analyzed against the **2026 Ground Truth** dataset.
- **Projected Winner Banner**: Identifies the favorites and the "Model Edge" (the probability margin in the resolution loop).
- **Chaos Injection**: Moving the **Volatility** slider injects standard deviation into the scoring distributions, allowing you to simulate everything from "chalk" years to "Cinderella" chaos.

---

## 🚀 Key Features

- **Full-Spectrum Reactivity**: Instant win rate re-calculation on slider move.
- **Non-Destructive Locking**: Manually lock games or sync live results without over-writing your custom simulation path.
- **Matchup Modal V4**: Detailed analysis including **ShotQuality Delta**, **Kill Shot Efficiency**, and **Rim-and-3 Rate**.

---

## 🛠 Installation & Setup

### 1. Prerequisites
- Python 3.10+
- `pip install -e .`

### 2. Running Simulation
```bash
# Start the web interface
python web/app.py
```
Open `http://localhost:5001` to access the dashboard.

---

## 📈 V4 Metric Core
V4 tracks advanced metrics beyond simple KenPom efficiency:
- **ShotQuality Delta**: Adjusted value of looks created vs. looks conceded.
- **Kill Shots (Net)**: Frequency of 10-0 scoring runs.
- **Rim-and-3 Rate**: Value of shot selection in high-pressure games.
- **Season Luck Regression**: Penalty for teams that were "Lucky" (high W-L% vs SRS) entering the tournament.

---

## 📅 Roadmap (Status: V4 Complete)
- [x] **Real-Time Settings Reactivity**: Instant re-calculation on slider move.
- [x] **Visual Bracket Editor**: Partial locking and non-destructive "Actually Happened" sync.
- [x] **Matchup Intelligence V4**: Projected winner banners and deep analytical summaries.
- [ ] **LLM "Aura" Analysis**: Future integration of sentiment-based intuition.

---

*Verified for the 2026 Season. Core logic resides in `/core/`, ensuring the engine remains evergreen.*
