# MM-Bracket-Flow Metrics & Factors Guide

This document defines the metrics used by the Intuition Factor Prediction Engine (v2.6) and their tactical significance.

## Primary Performance Metrics

### Efficiency Index (EFF)
- **Description**: Points per 100 possessions margin, adjusted for opponent strength.
- **Tactical Significance**: The best single predictor of overall team quality. High weights favor consistent, dominant teams ("Chalk").

### Strength of Schedule (SOS)
- **Description**: The cumulative toughness of all opponents faced.
- **Tactical Significance**: Validates win-loss records. High SOS weighting rewards teams that survived "The Gauntlet" even if their raw win% is lower.

## Tactical Modifiers

### TRB Advantage (Total Rebounds)
- **Description**: Rebounding margin per game.
- **Tactical Significance**: Measures physical dominance. Critical for controlling the glass and generating second-chance points in high-pressure games.

### Ball Security (TO Margin)
- **Description**: Turnovers committed vs. turnovers forced.
- **Tactical Significance**: Predicts stability under pressure. High ball security weights favor veteran backcourts and disciplined systems.

### Momentum
- **Description**: Efficiency trend over the last 10 games.
- **Tactical Significance**: Captures "surging" teams that are peaking at the right time (March madness).

### Defensive Premium
- **Description**: Multiplier for Adjusted Defensive Efficiency.
- **Tactical Significance**: "Defense wins championships." Favors elite defensive units (like Houston or Virginia) that can survive poor shooting nights.

## Advanced Human-Centric Factors

### Intuition Factor
- **Description**: The human "gut feeling" adjustment for outliers and unique tournament dynamics.
- **Tactical Significance**: Allows for manual biasing of teams that metrics might undervalue due to injuries, roster changes, or historical tournament performance.

### Composure Index
- **Description**: Performance in "Clutch" scenarios (last 4 minutes, games decided by <5 points).
- **Tactical Significance**: Predicts which teams will keep their cool in the final minutes of a Round of 64 nail-biter.

### Coach Moxie
- **Description**: Weighted historical tournament success of the head coach.
- **Tactical Significance**: Coaches with Final Four experience are statistically more likely to navigate deep runs. Mark Few and Bill Self are the benchmarks.

### Tempo Upset Factor
- **Description**: Penalty for high-tempo favorites against low-tempo underdogs.
- **Tactical Significance**: Low-tempo play compresses the talent gap. High weights here increase the probability of 12-vs-5 and 13-vs-4 upsets.

## Experimental Signals (Batch 2026)

### Upset Delta
- **Description**: The statistical variance between a team's ceiling and floor.
- **Tactical Significance**: Identifies "Boom or Bust" teams that are prone to both deep runs and early exits.

### Portal Instability
- **Description**: Penalty for rosters with >50% new minutes from the Transfer Portal.
- **Tactical Significance**: Rewards multi-year continuity over "assembled" mercenary rosters.

---
*Built for the 2026 Tournament Cycle.*
