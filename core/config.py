from dataclasses import dataclass

@dataclass
class SimulationWeights:
    """
    Configurable weights for the simulation engine.
    Set a weight to 0.0 to completely disable that metric's impact.
    Increase past 1.0 to over-index on a metric.
    """
    # Ultra-Deep Era-Agnostic Optimized Defaults (500 iterations, 2000-2025)
    trb_weight: float = 0.0
    to_weight: float = 6.046
    sos_weight: float = 7.635
    momentum_weight: float = 0.424
    efficiency_weight: float = 0.180
    ft_weight: float = 1.246
    three_par_weight: float = 0.0  # New research metric
    pace_variance_weight: float = 0.0  # Upset probability multiplier
    
    # Phase 4: Foul Drawing & Chaos Metrics
    foul_drawing_weight: float = 0.0
    stl_weight: float = 0.0
    blk_weight: float = 0.0
    orb_weight: float = 0.0
    neutral_weight: float = 0.0           # Rewards neutral site performance
    non_conf_weight: float = 0.0          # Rewards non-conference readiness
    def_ft_rate_weight: float = 0.0
    
    # Rounds 11-15: Fine-Grained Context
    travel_weight: float = 0.0             # Penalty for dist > 150mi
    pressure_weight: float = 0.0           # Resilience in late game
    chemistry_weight: float = 0.0          # Portal reliance penalty
    freshman_weight: float = 0.0           # Usage concentration penalty for frosh
    
    # Rounds 16-20: Roster & Depth Suite
    backcourt_weight: float = 0.0          # Guard play resilience vs pressure
    bench_synergy_weight: float = 0.0      # Bonus for bench rebounding/shooting
    whistle_mastery_weight: float = 0.0    # Synergy of foul drawing + conversion
    heating_up_weight: float = 0.0         # Late-season momentum stability
    
    # Rounds 21-25: Strategy & Adaptability
    adjustment_weight: float = 0.0         # Halftime adjustment efficacy (Coaching)
    zone_defense_weight: float = 0.0       # Effectiveness against high 3PAr teams
    foul_management_weight: float = 0.0    # Resilience vs whistle/depth gap
    clutch_execution_weight: float = 0.0   # Last-minute efficiency (TO/FT synergy)
    
    # Rounds 26-30: Post-Season Volatility
    conference_weight: float = 0.0          # Multi-bid conference reliability boost
    neutral_variance_weight: float = 0.0    # Neutral site scoring consistency
    rust_penalty: float = 0.0              # Long layoff penalty for top seeds
    rhythm_bonus: float = 0.0              # Momentum from play-in/close R64 win
    
    # Rounds 31-33: Final Convergence
    intuition_factor_weight: float = 0.0     # Composite metric dominance
    blue_blood_bonus: float = 0.0          # Historical program success weight
    
    # Rounds 34-40: Batch 6 - Situational Mastery
    shot_clock_weight: float = 0.0         # Efficiency in final 5s of clock
    drought_weight: float = 0.0            # Resilience vs scoreless streaks
    follow_up_weight: float = 0.0          # Efficiency on possessions post-ORB
    stopper_weight: float = 0.0            # Lockdown defense vs high-usage stars
    three_volatility_weight: float = 0.0   # Impact of high-volume 3PT cold streaks
    timeout_weight: float = 0.0            # Coaching efficiency in late-game TOs
    proximity_weight: float = 0.0          # Relative home-court (distance to venue)
    
    # Rounds 41-50: Batch 7 - Roster & Health Stability
    foul_resilience_weight: float = 0.0    # Resilience when key players have 3+ fouls
    ot_depth_weight: float = 0.0           # Advantage in overtime games for deep teams
    usage_fatigue_weight: float = 0.0      # Efficiency decay for stars > 35 min avg
    portal_chemistry_weight: float = 0.0   # Penalty for high transfer reliance in March
    rust_reset_weight: float = 0.0         # 1-seed reset after conference tourney loss
    playin_rhythm_weight: float = 0.0      # Boost for play-in winners in R64
    three_def_sos_weight: float = 0.0      # 3PT defense adjusted for opponent difficulty
    backcourt_exp_weight: float = 0.0      # Guard experience multiplier for deep runs
    rim_protection_weight: float = 0.0     # Defensive 2PT% impact on rim efficiency
    choke_factor_weight: float = 0.0       # FT% volatility in final 2 minutes
    
    # Rounds 51-60: Batch 8 - Era-Specific Historical Replay
    defensive_grit_bias: float = 0.0       # Weight multiplier for physical defense eras
    three_point_dominance: float = 0.0     # Adaptive 3PAr weighting for modern explosion
    rim_pressure_multiplier: float = 0.0   # Impact of 2023+ charge rule changes
    pace_sensitivity: float = 0.0          # Sensitivity to 30s vs 35s shot clock speed
    
    # Rounds 61-70: Batch 9 - Advanced Tactical Mechanics
    zone_efficiency_weight: float = 0.0     # Zone effectiveness against 3PT heavy teams
    press_disruption_weight: float = 0.0    # Turnover generation vs fatigue in 2nd half
    pace_control_weight: float = 0.0        # Ability to force preferred tempo (Pace Killer archetype)
    rotation_depth_weight: float = 0.0      # Bonus for 8+ man rotations in high-possession games
    half_adjustment_v2: float = 0.0         # Refined 2nd half coaching shift
    
    # Rounds 71-80: Batch 10 - Cinderella Dynamics
    mid_major_boost: float = 0.0            # Underseeded mid-major efficiency multiplier
    cinderella_momentum: float = 0.0        # Performance boost for 10-12 seeds in R2+
    auto_qualifier_rhythm: float = 0.0      # Bonus for non-power conf tourney winners
    seed_12_5_bias: float = 0.0             # Specific historical 12-vs-5 volatility
    
    # Rounds 81-93: Batch 11 - Clutch & Fatigue Management
    clutch_efficiency_weight: float = 0.0   # 2PT efficiency boost in final 5 minutes
    short_bench_boost: float = 0.0          # Efficiency boost for teams with elite 7-8 man rotations
    pressure_stability_weight: float = 0.0 # Turnover resistance in late-round pressure
    coach_clutch_multiplier: float = 0.0    # Moxie impact on 1-possession game outcomes
    
    # Rounds 94-100: Batch 12 - Tournament DNA & Calibration
    blue_blood_aura: float = 0.0            # First-round stability for legacy programs
    committee_error_bias: float = 0.0       # Boost for underseeded (KenPom > Seed) teams
    
    # Phase 2: Rounds 101-110 - The Physicality Crisis
    hand_check_penalty: float = 0.0          # Turbulence for small guards (Pre-2010)
    post_dominance_weight: float = 0.0       # Added impact of rim protection (Pre-2010)
    slow_pace_stability: float = 0.0         # Reward for deliberate play (Pre-2015)
    
    # Phase 2: Rounds 111-120 - The 3-Point Revolution
    three_point_variance_multiplier: float = 0.0 # Higher 3PT attempts = higher luck dependency (Post-2015)
    freedom_of_movement_boost: float = 0.0     # Off efficiency boost for foul drawers (Post-2013)
    
    # Phase 2: Rounds 121-130 - NIL & Portal Volatility
    portal_instability_penalty: float = 0.0   # Risk for high-portal usage teams in early rounds (Post-2021)
    nil_resource_advantage: float = 0.0       # Slight boost for power-conf high-resource programs
    
    # Phase 2: Rounds 131-140 - Dynamic Momentum Decay
    conf_tourney_marathon_fatigue: float = 0.0 # Penalty for teams winning 4+ games in 4 days
    elite_conf_momentum_boost: float = 0.0     # Bonus for Big East/Big 12 winners
    
    # Phase 2: Rounds 141-150 - Venue Specificity
    altitude_fatigue_penalty: float = 0.0      # Impact for low-to-high altitude travel
    altitude_ft_decay: float = 0.0            # Precision loss at Denver/SLC venues
    
    # Phase 2: Rounds 151-160 - Personnel Specificity
    star_reliance_penalty: float = 0.0        # Vulnerability for teams with 1-star focus
    deep_bench_stability: float = 0.0        # Bonus for high-usage rotation teams
    
    # Phase 2: Rounds 161-170 - Coaching Tenacity
    coach_final_four_aura: float = 0.0       # Boost for tenure and deep tourney runs
    
    # Phase 2: Rounds 171-180 - Resume Dominance
    quad_1_resilience_weight: float = 0.0    # Proxy for top-tier win frequency
    
    # Phase 2: Rounds 181-190 - Three-Point Gravity
    three_point_gravity_weight: float = 0.0  # Boost for interior efficiency via spacing
    
    # Phase 2: Rounds 191-200 - Final Era Calibration
    era_crossover_stability: float = 0.0     # Smooths transitions between era weights
    
    # Cycle 3: Rounds 201-215 - Archetype Matchup Logic
    glass_pace_interaction_weight: float = 0.0 # Matchup bias for ORB-heavy vs Slow-Pace
    small_ball_bias_modern: float = 0.0        # Efficiency boost for modern perimeter lineups
    
    # Cycle 3: Rounds 216-230 - Tournament Resilience
    low_seed_adrenaline_crash: float = 0.0     # Round 2 penalty for double-digit upset winners
    eleven_seed_sustainability: float = 0.0    # Legacy boost for No. 11 seeds in deep runs
    
    # Cycle 3: Rounds 231-250 - Intuition Factor Refinement
    composure_index_weight: float = 0.0       # Bonus for high-metric/low-luck teams
    upset_delta_weight: float = 0.0           # Scaling for seed dominance interaction
    
    # Cycle 3: Rounds 251-265 - Tactical Sophistication
    rim_contest_frequency_weight: float = 0.0  # Proxy: (Opp Rim Rate) * (1 - Opp Rim FG%) / (Def FT Rate)
    off_ball_movement_weight: float = 0.0      # Proxy: (Ast Rate) * (3P Assisted Rate) * (Adj Tempo)
    gravity_adjusted_3p_weight: float = 0.0     # Formula: (3P% / Avg) * (3PA Rate / Avg)
    
    # Cycle 3: Rounds 266-280 - Era Excellence & Portal Regression
    era_excellence_physicality_weight: float = 0.0 # Formula: (DRB% + Steal Rate) > 1.25 * Avg
    era_excellence_modern_weight: float = 0.0      # Formula: (Ast/TO) * (Opp TO%)
    portal_instability_coefficient_weight: float = 0.0 # Regression for high transfer usage
    
    # Cycle 3: Rounds 281-300 - Elite Eight Scarcity
    elite_eight_cinderella_wall: float = 0.0   # Penalty for >= 11 seeds in Elite Eight
    blue_blood_final_weekend_boost: float = 0.0 # Aura boost for core programs in R4-R6
    veteran_backcourt_scaling: float = 0.0     # Amplifies guard experience in later rounds
    
    # Cycle 3: Rounds 301-315 - Defensive Continuity & Shot Selection
    defensive_switching_continuity: float = 0.0 # Multiplier for switching-ready experienced rosters
    mid_range_march_value: float = 0.0          # Value of "inefficient" mid-range shots in late rounds
    defensive_versatility_index: float = 0.0    # Boost for versatile bigs in mismatch prevention
    
    # Cycle 3: Rounds 316-333 - Final Calibration & Tournament Aura
    tournament_aura_boost: float = 0.0          # Aura boost for multi-championship programs
    accumulative_travel_fatigue: float = 0.0     # Penalty for miles traveled/time zones crossed
    championship_pedigree_weight: float = 0.0    # Boost for specific non-losing championship programs
    
    # Global Modifiers
    defense_premium: float = 6.479         # Global multiplier for defensive metrics
    luck_weight: float = 0.0
    due_factor_sensitivity: float = 0.0  # Self-correction multiplier
    momentum_regression_weight: float = 0.0 # Dampens extreme streaks
    road_dominance_weight: float = 0.0      # Rewards road warriors
    seed_weight: float = 0.02              # Win prob bonus per seed rank diff
    ast_weight: float = 0.0               # Rewards unselfish cohesion
    three_par_volatility_weight: float = 0.0 # Adjusts variance for 3P-heavy teams
    ts_weight: float = 0.0                # True Shooting % advantage
    experience_weight: float = 0.0        # Rewards seasoned stability
    late_round_def_premium: float = 0.0   # Defense multiplier per round
    depth_weight: float = 0.0             # Rewards bench resilience in late rounds
    continuity_weight: float = 0.0        # Rewards system/roster stability
    pace_control_weight: float = 0.0      # Rewards teams that control the tempo
    cinderella_factor: float = 0.0        # Multiplier for high-variance underdog bias
    luck_regression_weight: float = 0.0   # Penalty for over-performing Win% (Phase 9)
    star_reliance_weight: float = 0.0     # Penalty for dependency on star scorers (Phase 9)
    
    # Phase 2: 2025 Indicators (Research Hub)
    orb_density_weight: float = 0.0      # Multiplier for historic OR% (>34%)
    continuation_rule_bias: float = 0.0  # Volatility shift for aggressive slashers

    # Phase 3: Coach & Tempo (Research Loop 1)
    coach_tournament_weight: float = 0.0  # Rewards coaches with deep tournament experience
    tempo_upset_weight: float = 0.0       # Slow-tempo underdogs reduce the talent gap

    # Phase 5: Fatigue & Orchestration
    fatigue_sensitivity: float = 0.0      # Penalty for short rest (R32, E8, Champ)
    bench_rest_bonus: float = 0.0         # Rewards deep teams on short rest

    # Chaos Engine Toggle (Phase 3)
    chaos_mode: bool = False

# Optimizer-tuned defaults (REDUCED for v2026 stability)
DEFAULT_WEIGHTS = SimulationWeights(
    efficiency_weight=0.153,
    to_weight=2.0,          # Further reduced from 2.5
    ft_weight=0.335,
    three_par_weight=1.607,
    pace_variance_weight=0.018,
    momentum_weight=0.435,
    sos_weight=1.8,         # Further reduced from 3.5
    foul_drawing_weight=0.0,
    stl_weight=0.408,
    blk_weight=0.420,
    orb_weight=1.170,
    luck_weight=-0.258,
    due_factor_sensitivity=0.027,
    momentum_regression_weight=0.024,
    road_dominance_weight=0.427,
    seed_weight=0.04,        # Increased from 0.015 to give 7-seed UCLA a better edge vs 10-seed
    ast_weight=0.0,
    three_par_volatility_weight=0.134,
    ts_weight=0.400,
    experience_weight=0.0,
    late_round_def_premium=0.080,
    depth_weight=0.0,
    continuity_weight=0.120,
    pace_control_weight=0.0,
    cinderella_factor=0.096,
    luck_regression_weight=0.628,
    star_reliance_weight=0.228,
    neutral_weight=1.404,
    non_conf_weight=0.420,
    def_ft_rate_weight=1.092,
    defense_premium=2.0,     # Further reduced from 3.5
    orb_density_weight=0.187,
    continuation_rule_bias=0.005,
    coach_tournament_weight=0.135,
    tempo_upset_weight=0.0
)




# Optimized for #11-#15 seed upsets (Derived via optimize_chaos.py)
CHAOS_WEIGHTS = SimulationWeights(
    trb_weight=0.0,
    to_weight=9.276,
    sos_weight=9.182,
    momentum_weight=3.131,
    efficiency_weight=2.226,
    ft_weight=0.552,
    three_par_weight=10.269,
    pace_variance_weight=2.720,
    defense_premium=17.004,
    chaos_mode=True,
    foul_drawing_weight=2.0,  # Chaos teams draw fouls
    stl_weight=1.5,      # Chaos teams disrupt
    blk_weight=0.0,
    orb_weight=1.0
)
