import unittest
import math
from core.simulator import SimulatorEngine
from core.team_model import Team
from core.config import SimulationWeights
from scripts.evaluate_weights import evaluate_bracket

class TestOptimizationAgent(unittest.TestCase):
    def setUp(self):
        self.weights = SimulationWeights()
        self.teams = {
            "Team A": Team(name="Team A", seed=1, off_efficiency=115.0, def_efficiency=95.0, off_ppg=75.0, def_ppg=65.0),
            "Team B": Team(name="Team B", seed=16, off_efficiency=105.0, def_efficiency=105.0, off_ppg=70.0, def_ppg=70.0)
        }
        self.engine = SimulatorEngine(self.teams, self.weights)

    def test_sigmoid_probability(self):
        prob = self.engine.calculate_win_probability(self.teams["Team A"], self.teams["Team B"])
        self.assertGreater(prob, 0.5, "Stronger team should have > 0.5 prob")
        self.assertLessEqual(prob, 0.999, "Prob should be clamped")
        self.assertGreaterEqual(prob, 0.001, "Prob should be clamped")
        print(f"Prob(Team A wins): {prob}")

    def test_sigmoid_symmetry(self):
        prob_a = self.engine.calculate_win_probability(self.teams["Team A"], self.teams["Team B"])
        prob_b = self.engine.calculate_win_probability(self.teams["Team B"], self.teams["Team A"])
        self.assertAlmostEqual(prob_a + prob_b, 1.0, places=5, msg="Probabilities must sum to 1")

    def test_evaluate_bracket_likelihood(self):
        # We can't easily run a full evaluation without data, but we can mock it
        # Actually, let's just check if it runs for 2024
        try:
            metrics = evaluate_bracket(2024, self.weights, iterations=10)
            print(f"2024 Metrics: {metrics}")
            self.assertIn("log_likelihood", metrics)
        except FileNotFoundError:
            print("Year 2024 data not found, skipping evaluation test.")

if __name__ == "__main__":
    unittest.main()
