from dataclasses import dataclass

@dataclass
class SimulationWeights:
    """
    Configurable weights for the simulation engine.
    Set a weight to 0.0 to completely disable that metric's impact.
    Increase past 1.0 to over-index on a metric.
    """
    # True EV Optimal Weights (SA 300 iters x 50 MC, 5-year full-round signal)
    trb_weight: float = 1.182
    to_weight: float = 0.596
    sos_weight: float = 1.823
    momentum_weight: float = 1.210
    efficiency_weight: float = 1.096
    seed_weight: float = 0.158
    
    # Intuition weight: 1 point = 1% probability shift
    intuition_weight: float = 0.01

    # General modifiers
    # Multiplier to value defense slightly more in March (since defense travels)
    defense_premium: float = 1.988

# Standard instance to use across the app if no custom one is provided
DEFAULT_WEIGHTS = SimulationWeights()
