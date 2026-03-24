# MM-Bracket-Flow 2026: The "Perfect Bracket" Marathon

**MM-Bracket-Flow** is a high-performance March Madness simulation engine. V5 marks the transition to an **Extreme Value Theory (EVT)** driven optimization architecture, designed to find the rare global maxima required for perfect bracket discovery.

---

## 🏔️ V5 Optimization Marathon (The Sweet 16 Phase)

As of late March 2026, the engine is running 3 parallel "souls" in a continuous refinement marathon.

### 🎯 1. Perfect Mode (Convex Power-Law)

- **Math**: Uses a hyper-convex $s^8$ reward function on the top 1% of simulated outcomes.
- **Goal**: Specifically targets 1-in-9 quintillion anomalies by creating a massive "gravity well" around 1800+ point outliers.
- **Behavior**: Will often prefer high-variance upsets that safe models ignore.

### ⚖️ 2. Balanced Mode (Hybrid Accuracy)

- **Goal**: A strategic mix of total points and bracket accuracy. Uses a linear accuracy reward ($+10,000$) to favor winners of the Championship game.

### 📈 3. Average Mode (Shadow Floor)

- **Goal**: Maximizing the expected points floor. Uses a **3.0x multiplier** on `ESPN_Avg` to ensure stability in standard scoring pools.

---

## 🏗 Architecture: Shadow Scoring & Resumability

### Shadow Scoring Dashboard

Terminal logs (and `agents/optimization/refine_*.log`) display the "Triple-Metric" dashboard:
`SA_Fit` (Internal discovery reward) -> `ESPN_Avg` (Points floor) -> `ESPN_Max` (Peak potential) -> `T` (Temp) -> `J` (Jitter)

### Resumable State Machine (V5)

The engine is **indestructible** and **autonomous**:
- **Zombie Protection**: On startup, it automatically clears stale PIDs from previous crashed sessions.
- **Checkpointing**: State is saved every 100 iterations AND on every "NEW BEST" discovery.
- **Thermal Re-heating**: Resuming a process adds a **1.25x temperature boost** to encourage exploration of new territory.

---

## 🛠 Operation & Maintenance

### Starting / Resuming the Marathon

```bash
# Authoritative Resume command (clears zombies and picks up from checkpoints)
python3 scripts/optimize_weights.py --mode average --resume > agents/optimization/refine_average.log 2>&1 &
python3 scripts/optimize_weights.py --mode balanced --resume > agents/optimization/refine_balanced.log 2>&1 &
python3 scripts/optimize_weights.py --mode perfect --resume > agents/optimization/refine_perfect.log 2>&1 &
```

### Monitoring Progress

```bash
# Follow the live discovery of new peaks
tail -f agents/optimization/refine_*.log
```

---

## ⚖️ Implementation Rules (The "Zero-Weight" Policy)

- **New Metrics**: Any newly added variables in `SimulationWeights` MUST default to **0.0**.
- **Independence**: A new metric should have no effect on win probability until the Autonomous Optimizer has discovered a non-zero peak through exhaustive testing.
- **Process Stability**: Using individual processes per mode to prevent macOS kernel congestion.

---

*Verified for the 2026 Tournament Cycle. V5 Marathon Architecture deployed March 24, 2026.*
