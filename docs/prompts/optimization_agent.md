🧬 Optimization Agent
Objective: Refine the prediction engine and implement an autonomous optimization loop.

Detailed Task:

Probability Calibration:
Update core/simulator.py to use a Sigmoid (Logistic) model for win probabilities, replacing linear certainty.

Fitness Function V2:
Implement a Log-Likelihood fitness function in scripts/optimize_weights.py to maximize the probability of a "Perfect Bracket" (1920 score target).

Autonomous Loop:
Create an infinite optimization protocol that logs "heartbeats" every 5 minutes.
Self-adjust learning rates or parameters based on v2025_indicators.json (if available).
