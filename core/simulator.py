import logging
import random
from typing import Optional, List, Dict
from .team_model import Team
from .config import SimulationWeights, DEFAULT_WEIGHTS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class SimulatorEngine:
    def __init__(self, teams: Dict[str, Team], weights: SimulationWeights, locks: Optional[Dict[str, str]] = None):
        self.teams = teams
        self.weights = weights
        self.locks = locks or {}
        # Stateful tracking for "Due Factor" (Reset per simulation run)
        self.upset_count = 0
        self.total_games = 0
        
    def reset_state(self):
        """Reset state for a new bracket simulation."""
        self.upset_count = 0
        self.total_games = 0

    def simulate_game(self, team_a: Team, team_b: Team, mode: str = "deterministic") -> Team:
        """Simulates a game and returns the winner."""
        prob_a = self.calculate_win_probability(team_a, team_b)
        
        if mode == "deterministic":
            return team_a if prob_a >= 0.5 else team_b
        else:
            return team_a if random.random() < prob_a else team_b

    def _get_metric(self, team, attr, default=0.0):
        """Safely gets a numeric metric from a team object, defaulting if None."""
        val = getattr(team, attr, default)
        return val if val is not None else default

    def calculate_win_probability(self, team_a: Team, team_b: Team, round_num: int = 1) -> float:
        """Calculates win prob with robust null handling for all 100+ research metrics."""
        # Step 1: Base Pythagorean Expectation
        eff_a = self._get_metric(team_a, 'pythagorean_expectation', 0.5)
        eff_b = self._get_metric(team_b, 'pythagorean_expectation', 0.5)
        
        base_probability = eff_a / (eff_a + eff_b) if (eff_a + eff_b) > 0 else 0.5
        final_probability = base_probability
        
        # Step 2: Advanced Metric Modifiers
        # Defense Premium
        def_a = self._get_metric(team_a, 'def_efficiency', 100.0)
        def_b = self._get_metric(team_b, 'def_efficiency', 100.0)
        def_delta = def_b - def_a
        final_probability += (def_delta * 0.001) * self.weights.defense_premium
        
        # Seed Advantage
        seed_diff = self._get_metric(team_b, 'seed', 16) - self._get_metric(team_a, 'seed', 16)
        final_probability += seed_diff * self.weights.seed_weight
        
        # SOS (Weighted by win percentage)
        sos_a = self._get_metric(team_a, 'sos', 0.0) * self._get_metric(team_a, 'total_win_pct', 0.5)
        sos_b = self._get_metric(team_b, 'sos', 0.0) * self._get_metric(team_b, 'total_win_pct', 0.5)
        final_probability += ((sos_a - sos_b) * 0.01) * self.weights.sos_weight
            
        # Turnover Margin
        margin_a = self._get_metric(team_a, 'def_to_pct', 20.0) - self._get_metric(team_a, 'off_to_pct', 20.0)
        margin_b = self._get_metric(team_b, 'def_to_pct', 20.0) - self._get_metric(team_b, 'off_to_pct', 20.0)
        final_probability += ((margin_a - margin_b) * 0.01) * self.weights.to_weight
            
        # Momentum
        final_probability += (self._get_metric(team_a, 'momentum', 0.5) - self._get_metric(team_b, 'momentum', 0.5)) * self.weights.momentum_weight
            
        # Free Throw Advantage
        ft_a = (self._get_metric(team_a, 'off_ft_pct', 70.0) / 100.0) * self._get_metric(team_b, 'def_ft_rate', 0.3)
        ft_b = (self._get_metric(team_b, 'off_ft_pct', 70.0) / 100.0) * self._get_metric(team_a, 'def_ft_rate', 0.3)
        final_probability += (ft_a - ft_b) * 0.1 * self.weights.ft_weight
            
        # Foul Drawing (AGGRESSIVENESS)
        final_probability += (self._get_metric(team_a, 'off_ft_rate', 0.3) - self._get_metric(team_b, 'off_ft_rate', 0.3)) * self.weights.foul_drawing_weight

        # Chaos Stats
        final_probability += (self._get_metric(team_a, 'off_stl_pct', 8.0) - self._get_metric(team_b, 'off_stl_pct', 8.0)) * 0.01 * self.weights.stl_weight
        final_probability += (self._get_metric(team_a, 'off_blk_pct', 8.0) - self._get_metric(team_b, 'off_blk_pct', 8.0)) * 0.01 * self.weights.blk_weight
        final_probability += (self._get_metric(team_a, 'off_orb_pct', 25.0) - self._get_metric(team_b, 'off_orb_pct', 25.0)) * 0.01 * self.weights.orb_weight
        final_probability += (self._get_metric(team_b, 'def_ft_rate', 0.3) - self._get_metric(team_a, 'def_ft_rate', 0.3)) * self.weights.def_ft_rate_weight

        # Fatigue & Short Rest (R32, E8, F4, Champ)
        if round_num in [2, 4, 6] and self.weights.fatigue_sensitivity > 0:
            fatigue_a = self._get_metric(team_a, 'pace', 70.0) * 0.01 * self.weights.fatigue_sensitivity
            fatigue_b = self._get_metric(team_b, 'pace', 70.0) * 0.01 * self.weights.fatigue_sensitivity
            depth_a = self._get_metric(team_a, 'bench_minutes_pct', 25.0) * 0.01 * self.weights.bench_rest_bonus
            depth_b = self._get_metric(team_b, 'bench_minutes_pct', 25.0) * 0.01 * self.weights.bench_rest_bonus
            net_fatigue = (fatigue_a - depth_a) - (fatigue_b - depth_b)
            final_probability -= net_fatigue

        # Luck & Momentum Regression
        luck_a = self._get_metric(team_a, 'luck', 0.0)
        luck_b = self._get_metric(team_b, 'luck', 0.0)
        final_probability += (luck_b - luck_a) * self.weights.luck_weight

        mom_a = self._get_metric(team_a, 'momentum', 0.5)
        mom_b = self._get_metric(team_b, 'momentum', 0.5)
        if mom_a > 0.9: final_probability -= (mom_a - 0.9) * self.weights.momentum_regression_weight
        if mom_b > 0.9: final_probability += (mom_b - 0.9) * self.weights.momentum_regression_weight

        # Assist Rate
        final_probability += (self._get_metric(team_a, 'off_ast_pct', 0.0) - self._get_metric(team_b, 'off_ast_pct', 0.0)) * 0.01 * self.weights.ast_weight

        # 3PAr Volatility
        avg_3par = (self._get_metric(team_a, 'three_par', 0.37) + self._get_metric(team_b, 'three_par', 0.37)) / 2
        volatility_shift = (avg_3par - 0.37) * self.weights.three_par_volatility_weight
        if final_probability > 0.5:
            final_probability = max(0.5, final_probability - volatility_shift)
        else:
            final_probability = min(0.5, final_probability + volatility_shift)

        # Efficiency Advantage
        final_probability += (self._get_metric(team_a, 'off_ts_pct', 55.0) - self._get_metric(team_b, 'off_ts_pct', 55.0)) * 0.01 * self.weights.ts_weight
        final_probability += (self._get_metric(team_a, 'total_games', 30) - self._get_metric(team_b, 'total_games', 30)) * self.weights.experience_weight

        # Round-Weighted Defense
        def_advantage = (self._get_metric(team_b, 'def_efficiency', 100.0) - self._get_metric(team_a, 'def_efficiency', 100.0))
        round_bonus = (round_num - 1) * self.weights.late_round_def_premium
        final_probability += (def_advantage * 0.01) * round_bonus

        # Aggressive Marksman (Implicitly handled by FT and 3PAr)

        # 2025 FORMULAS (Grit, Aggression, Stability)
        grit_a = 0.4 * (100 - self._get_metric(team_a, 'def_efficiency', 100)) + 0.3 * self._get_metric(team_a, 'off_orb_pct', 25.0) + 0.3 * abs(min(0, self._get_metric(team_a, 'luck', 0.0)))
        grit_b = 0.4 * (100 - self._get_metric(team_b, 'def_efficiency', 100)) + 0.3 * self._get_metric(team_b, 'off_orb_pct', 25.0) + 0.3 * abs(min(0, self._get_metric(team_b, 'luck', 0.0)))
        final_probability += (grit_a - grit_b) * 0.01 * self.weights.defense_premium

        agg_a = 0.3 * self._get_metric(team_a, 'pace', 70) + 0.4 * self._get_metric(team_a, 'off_ft_rate', 0.3) + 0.3 * self._get_metric(team_a, 'def_to_pct', 15.0)
        agg_b = 0.3 * self._get_metric(team_b, 'pace', 70) + 0.4 * self._get_metric(team_b, 'off_ft_rate', 0.3) + 0.3 * self._get_metric(team_b, 'def_to_pct', 15.0)
        final_probability += (agg_a - agg_b) * 0.01 * self.weights.foul_drawing_weight

        stab_a = 0.5 * self._get_metric(team_a, 'returning_minutes', 50.0) + 0.3 * self._get_metric(team_a, 'returning_scoring', 50.0) - 0.2 * self._get_metric(team_a, 'transfer_pct', 20.0)
        stab_b = 0.5 * self._get_metric(team_b, 'returning_minutes', 50.0) + 0.3 * self._get_metric(team_b, 'returning_scoring', 50.0) - 0.2 * self._get_metric(team_b, 'transfer_pct', 20.0)
        final_probability += (stab_a - stab_b) * 0.01 * self.weights.continuity_weight

        if (self._get_metric(team_a, 'off_ft_rate', 0.0)) > 0.38 and (self._get_metric(team_a, 'off_ft_pct', 0.0)) > 78.0:
            final_probability += 0.02
        if (self._get_metric(team_b, 'off_ft_rate', 0.0)) > 0.38 and (self._get_metric(team_b, 'off_ft_pct', 0.0)) > 78.0:
            final_probability -= 0.02

        # Neutral Site Mastery
        final_probability += (self._get_metric(team_a, 'neutral_win_pct', 0.25) - self._get_metric(team_b, 'neutral_win_pct', 0.25)) * self.weights.neutral_weight

        # Bench Depth (Late Rounds)
        if round_num >= 4:
            depth_delta = (self._get_metric(team_a, 'off_ast_pct', 50.0) + self._get_metric(team_a, 'trb_pct', 50.0)) - \
                          (self._get_metric(team_b, 'off_ast_pct', 50.0) + self._get_metric(team_b, 'trb_pct', 50.0))
            final_probability += (depth_delta * 0.01) * self.weights.depth_weight

        # Roster Continuity
        continuity_a = self._get_metric(team_a, 'total_games', 30) * self._get_metric(team_a, 'sos', 0.0)
        continuity_b = self._get_metric(team_b, 'total_games', 30) * self._get_metric(team_b, 'sos', 0.0)
        final_probability += (continuity_a - continuity_b) * 0.001 * self.weights.continuity_weight

        # Coach Tournament Moxie
        moxie_a = min(1.0, self._get_metric(team_a, 'coach_tournament_wins', 0) / 20.0)
        moxie_b = min(1.0, self._get_metric(team_b, 'coach_tournament_wins', 0) / 20.0)
        final_probability += (moxie_a - moxie_b) * 0.05 * self.weights.coach_tournament_weight


        # Pace Control
        ppp_a = self._get_metric(team_a, 'off_ppg', 70) / (self._get_metric(team_a, 'off_ppg', 70) + self._get_metric(team_a, 'def_ppg', 70)) if (self._get_metric(team_a, 'off_ppg', 70) and self._get_metric(team_a, 'def_ppg', 70)) else 0.5
        ppp_b = self._get_metric(team_b, 'off_ppg', 70) / (self._get_metric(team_b, 'off_ppg', 70) + self._get_metric(team_b, 'def_ppg', 70)) if (self._get_metric(team_b, 'off_ppg', 70) and self._get_metric(team_b, 'def_ppg', 70)) else 0.5
        
        control_a = abs(self._get_metric(team_a, 'pace', 70.0) - 70.0) * ppp_a
        control_b = abs(self._get_metric(team_b, 'pace', 70.0) - 70.0) * ppp_b
        final_probability += (control_delta * 0.01) * self.weights.pace_control_weight

        # 3PAr Advantage
        final_probability += (self._get_metric(team_a, 'three_par', 0.3) - self._get_metric(team_b, 'three_par', 0.3)) * self.weights.three_par_weight
            
        # Pace Variance (Slow games neutralize favorites)
        avg_pace = (self._get_metric(team_a, 'pace', 70.0) + self._get_metric(team_b, 'pace', 70.0)) / 2.0
        if avg_pace < 65.0:
            pace_diff = 65.0 - avg_pace
            neutralization = (pace_diff * 0.02) * self.weights.pace_variance_weight
            # Tempo upset bonus: if the underdog (higher seed) is slower,
            # they are deliberately controlling the tempo
            if self._get_metric(team_a, 'seed', 16) > self._get_metric(team_b, 'seed', 16) and self._get_metric(team_a, 'pace', 70) < 65:
                neutralization += self.weights.tempo_upset_weight * 0.5
            elif self._get_metric(team_b, 'seed', 16) > self._get_metric(team_a, 'seed', 16) and self._get_metric(team_b, 'pace', 70) < 65:
                neutralization += self.weights.tempo_upset_weight * 0.5
            if final_probability > 0.5:
                final_probability = max(0.5, final_probability - neutralization)
            else:
                final_probability = min(0.5, final_probability + neutralization)

        # eFG% Matchup (A's offense vs B's defense)
        efg_a_off_b_def = self._get_metric(team_a, 'off_efg_pct', 0.5) - self._get_metric(team_b, 'def_efg_pct', 0.5)
        efg_b_off_a_def = self._get_metric(team_b, 'off_efg_pct', 0.5) - self._get_metric(team_a, 'def_efg_pct', 0.5)
        final_probability += (efg_a_off_b_def - efg_b_off_a_def) * 0.002 * self.weights.efficiency_weight

        # CHAOS ENGINE: Probability Shift
        # If chaos_mode is on, and an underdog (by seed) has a "Chaos Profile"
        # (High 3PAr or massive TO edge), we shift their probability up.
        if self.weights.chaos_mode:
            # Determine who is the underdog by seed
            if self._get_metric(team_a, 'seed', 16) > self._get_metric(team_b, 'seed', 16):
                underdog = team_a
                underdog_idx = 1 # Shift final_prob UP
            elif self._get_metric(team_b, 'seed', 16) > self._get_metric(team_a, 'seed', 16):
                underdog = team_b
                underdog_idx = -1 # Shift final_prob DOWN
            else:
                underdog = None
                
            if underdog:
                # Chaos Shift Logic: If underdog has >35% 3PAr or high TO margin
                is_chaos_potential = (self._get_metric(underdog, 'three_par', 0.0) > 0.38) or \
                                     (self._get_metric(underdog, 'def_to_pct', 0.0) - self._get_metric(underdog, 'off_to_pct', 0.0) > 3.0)
                
                if is_chaos_potential:
                    # Apply a shift scaled by the Cinderella Factor
                    shift = 0.05 * self.weights.cinderella_factor
                    final_probability += (shift * underdog_idx)

        # 4. The Due Factor (Phase 4)
        # If we have too many upsets, narrow the probability (make it more likely for the favorite)
        # If we have too few, widen it (make upsets more likely)
        if self.weights.due_factor_sensitivity > 0 and self.total_games > 5:
            historical_upset_rate = 0.25 # Approx 1/4 games are upsets
            current_rate = self.upset_count / self.total_games
            
            # If current rate > historical, favor favored team more
            due_correction = (current_rate - historical_upset_rate) * self.weights.due_factor_sensitivity
            
            # Apply correction: if due_correction is positive (too many upsets), 
            # and final_probability > 0.5 (Team A is favorite), increase final_probability.
            if final_probability > 0.5:
                final_probability += due_correction
            else:
                final_probability -= due_correction

        # 5. Luck Regression & Star Reliance (Phase 9)
        final_probability -= (self._get_metric(team_a, 'luck', 0.0) * self.weights.luck_regression_weight)
        final_probability += (self._get_metric(team_b, 'luck', 0.0) * self.weights.luck_regression_weight)
            
        final_probability -= (self._get_metric(team_a, 'star_reliance', 0.0) * self.weights.star_reliance_weight)
        final_probability += (self._get_metric(team_b, 'star_reliance', 0.0) * self.weights.star_reliance_weight)

        # 2025 Research Indicator: Continuation Rule (FTA/FGA Slasher Bonus)
        # Favors aggressive teams that draw fouls at the rim (NCAA 2025 Rule Change)
        if (self._get_metric(team_a, 'off_ft_rate', 0.0)) > 0.380:
            final_probability += self.weights.continuation_rule_bias
        if (self._get_metric(team_b, 'off_ft_rate', 0.0)) > 0.380:
            final_probability -= self.weights.continuation_rule_bias

        # 2025 Research Indicator: ORB Density (Historic Dominance)
        if (self._get_metric(team_a, 'off_orb_pct', 0.0)) > 34.0:
            final_probability += (self._get_metric(team_a, 'off_orb_pct', 0.0) - 34.0) * 0.01 * self.weights.orb_density_weight
        if (self._get_metric(team_b, 'off_orb_pct', 0.0)) > 34.0:
            final_probability -= (self._get_metric(team_b, 'off_orb_pct', 0.0) - 34.0) * 0.01 * self.weights.orb_density_weight

        # --- Rounds 11-15: Fine-Grained Context ---
        # Round 11: Geospatial Impact
        if self.weights.travel_weight > 0:
            if (self._get_metric(team_a, 'travel_dist', 0)) > 150:
                final_probability -= 0.02 * self.weights.travel_weight
            if team_a.travel_east: # This is a boolean, not a numeric metric
                final_probability -= 0.015 * self.weights.travel_weight
            if (self._get_metric(team_b, 'travel_dist', 0)) > 150:
                final_probability += 0.02 * self.weights.travel_weight
            if team_b.travel_east: # This is a boolean, not a numeric metric
                final_probability += 0.015 * self.weights.travel_weight
        
        # Round 12: Pressure Resilience
        if round_num >= 4 and self.weights.pressure_weight > 0:
            # Experience + FT% + Coach wins is the pressure-proof profile
            clutch_a = ((self._get_metric(team_a, 'off_ft_pct', 70)) / 100.0) + (min(1.0, (self._get_metric(team_a, 'coach_tournament_wins', 0)) / 10.0))
            clutch_b = ((self._get_metric(team_b, 'off_ft_pct', 70)) / 100.0) + (min(1.0, (self._get_metric(team_b, 'coach_tournament_wins', 0)) / 10.0))
            final_probability += (clutch_a - clutch_b) * 0.05 * self.weights.pressure_weight

        # Round 13: Roster Chemistry (Transfer Portal)
        if round_num >= 5 and self.weights.chemistry_weight > 0:
            chem_a = (self._get_metric(team_a, 'portal_usage_pct', 20.0)) / 100.0
            chem_b = (self._get_metric(team_b, 'portal_usage_pct', 20.0)) / 100.0
            # Higher portal usage = lower chemistry in high-stakes environments
            final_probability -= (chem_a - chem_b) * 0.1 * self.weights.chemistry_weight

        # Round 14: Elite Freshman Index
        if round_num >= 4 and self.weights.freshman_weight > 0:
            frosh_a = (self._get_metric(team_a, 'freshman_usage_pct', 10.0)) / 100.0
            frosh_b = (self._get_metric(team_b, 'freshman_usage_pct', 10.0)) / 100.0
            final_probability -= (frosh_a - frosh_b) * 0.08 * self.weights.freshman_weight

        # Round 15: Conference Tournament Aftermath
        momentum_boost_a = (self._get_metric(team_a, 'tourney_momentum', 0.0)) * 0.03
        momentum_boost_b = (self._get_metric(team_b, 'tourney_momentum', 0.0)) * 0.03
        final_probability += (momentum_boost_a - momentum_boost_b)

        # --- Rounds 16-20: Roster & Depth Suite ---
        # Round 16: Elite Backcourt Mastery
        # Mitigation of defense pressure for elite ball-handling teams
        if self.weights.backcourt_weight > 0:
            guard_a = (self._get_metric(team_a, 'off_ast_pct', 50)) * (100 - (self._get_metric(team_a, 'off_to_pct', 20))) / 1000.0
            guard_b = (self._get_metric(team_b, 'off_ast_pct', 50)) * (100 - (self._get_metric(team_b, 'off_to_pct', 20))) / 1000.0
            # If facing a top 50 defense, the guard play matters more
            defense_fac_a = (100 - (self._get_metric(team_b, 'def_efficiency', 100))) / 10.0
            defense_fac_b = (100 - (self._get_metric(team_a, 'def_efficiency', 100))) / 10.0
            final_probability += (guard_a * defense_fac_a - guard_b * defense_fac_b) * 0.01 * self.weights.backcourt_weight

        # Round 17: Bench Synergy (Depth-driven Rebounding)
        if self.weights.bench_synergy_weight > 0:
            syn_a = (self._get_metric(team_a, 'bench_minutes_pct', 25)) * (self._get_metric(team_a, 'trb_pct', 50)) / 100.0
            syn_b = (self._get_metric(team_b, 'bench_minutes_pct', 25)) * (self._get_metric(team_b, 'trb_pct', 50)) / 100.0
            final_probability += (syn_a - syn_b) * 0.005 * self.weights.bench_synergy_weight

        # Round 18: Whistle Mastery
        if self.weights.whistle_mastery_weight > 0:
            # Aggressive foul drawing + High FT% conversion
            whistle_a = (self._get_metric(team_a, 'off_ft_rate', 0.3)) * (self._get_metric(team_a, 'off_ft_pct', 70)) / 100.0
            whistle_b = (self._get_metric(team_b, 'off_ft_rate', 0.3)) * (self._get_metric(team_b, 'off_ft_pct', 70)) / 100.0
            final_probability += (whistle_a - whistle_b) * 0.1 * self.weights.whistle_mastery_weight

        # Round 19: Heating Up (Undervalued Momentum)
        if self.weights.heating_up_weight > 0:
            heat_a = (self._get_metric(team_a, 'momentum', 0.5)) * (1 - (self._get_metric(team_a, 'luck', 0.0)))
            heat_b = (self._get_metric(team_b, 'momentum', 0.5)) * (1 - (self._get_metric(team_b, 'luck', 0.0)))
            final_probability += (heat_a - heat_b) * 0.02 * self.weights.heating_up_weight

        # Round 20: Venue Stability Variance
        if round_num >= 1 and (self.teams.get(team_a.name) or team_a).home_w is not None:
            # Simple check for Home/Away win% delta. High variance = Low stability on neutral sites.
            def get_stability(t):
                h_win = self._get_metric(t, 'home_w', 0.7) / max(1, self._get_metric(t, 'home_w', 0) + self._get_metric(t, 'home_l', 0))
                a_win = self._get_metric(t, 'away_w', 0.5) / max(1, self._get_metric(t, 'away_w', 0) + self._get_metric(t, 'away_l', 0))
                return 1.0 - abs(h_win - a_win)
            
            stab_a = get_stability(team_a)
            stab_b = get_stability(team_b)
            final_probability += (stab_a - stab_b) * 0.03

        # --- Rounds 21-25: Strategy & Adaptability ---
        # Round 21: Zone Defense Effectiveness
        if self.weights.zone_defense_weight > 0:
            # If team_a has high 3PAr, they might struggle against a team_b "Zone Profile"
            # Proxy: team_b is "Zone Profile" if they have low STL but high BLK and good AdjD
            is_zone_b = (team_b.off_stl_pct or 9.0) < 8.0 and (team_b.off_blk_pct or 9.0) > 10.0
            if is_zone_b and (team_a.three_par or 0.35) > 0.40:
                final_probability -= 0.03 * self.weights.zone_defense_weight
            
            is_zone_a = (team_a.off_stl_pct or 9.0) < 8.0 and (team_a.off_blk_pct or 9.0) > 10.0
            if is_zone_a and (team_b.three_par or 0.35) > 0.40:
                final_probability += 0.03 * self.weights.zone_defense_weight

        # Round 22: Halftime Adjustments (Coaching Boost)
        # Favors the stronger team (favorite) to rally or pull away
        if self.weights.adjustment_weight > 0:
            favorite_boost = abs(final_probability - 0.5) * 0.1 * self.weights.adjustment_weight
            # Booster: If coach is elite, the adjustment is more effective
            coach_boost_a = min(1.0, (team_a.coach_tournament_wins or 0) / 20.0)
            coach_boost_b = min(1.0, (team_b.coach_tournament_wins or 0) / 20.0)
            final_probability += (coach_boost_a - coach_boost_b) * 0.02 * self.weights.adjustment_weight

        # Round 23: Foul Trouble Management
        if self.weights.foul_management_weight > 0:
            # High FOUL rate (def_ft_rate) + Small Rotation (bench_minutes_pct) = Danger
            danger_a = (team_a.def_ft_rate or 30.0) * (100 - (team_a.bench_minutes_pct or 25.0)) / 1000.0
            danger_b = (team_b.def_ft_rate or 30.0) * (100 - (team_b.bench_minutes_pct or 25.0)) / 1000.0
            final_probability -= (danger_a - danger_b) * 0.05 * self.weights.foul_management_weight

        # Round 24: Clutch Execution (Final 4 Min Synergy)
        if self.weights.clutch_execution_weight > 0:
            # Pure synergy of ball handling and foul shooting
            clutch_a = (100 - (team_a.off_to_pct or 20)) + (team_a.off_ft_pct or 70)
            clutch_b = (100 - (team_b.off_to_pct or 20)) + (team_b.off_ft_pct or 70)
            final_probability += (clutch_a - clutch_b) * 0.001 * self.weights.clutch_execution_weight

        # Round 25: Rotation Endurance (2nd Half depth)
        if round_num >= 4 and self.weights.bench_rest_bonus > 0: # Reusing bench weights
            endurance_a = (team_a.bench_minutes_pct or 25) * (team_a.pace or 70) / 100.0
            endurance_b = (team_b.bench_minutes_pct or 25) * (team_b.pace or 70) / 100.0
            final_probability += (endurance_a - endurance_b) * 0.01 * self.weights.bench_rest_bonus

        # --- Rounds 26-30: Post-Season Volatility ---
        # Round 26: Neutral Site Scoring Consistency
        if self.weights.neutral_variance_weight > 0:
            # Multiplier for neutral_win_pct: Teams that produce at neutral sites stay stable
            final_probability += (team_a.neutral_win_pct - team_b.neutral_win_pct) * self.weights.neutral_variance_weight

        # Round 27: Conference Strength Reliability
        if self.weights.conference_weight > 0:
            # Power conferences have higher consistency/depth in post-season
            conf_bonus_a = 0.05 if team_a.is_power_conf else 0.0
            conf_bonus_b = 0.05 if team_b.is_power_conf else 0.0
            final_probability += (conf_bonus_a - conf_bonus_b) * self.weights.conference_weight

        # Round 28: Seed-Based Luck Regression (Specialized for high seeds)
        if (team_a.seed or 1) <= 3 and (team_a.luck or 0) > 2.0:
            # Penalty for "over-seeded" top teams with high luck
            final_probability -= (team_a.luck - 2.0) * 0.02 * self.weights.luck_regression_weight
        if (team_b.seed or 1) <= 3 and (team_b.luck or 0) > 2.0:
            final_probability += (team_b.luck - 2.0) * 0.02 * self.weights.luck_regression_weight

        # Round 29: SOS-Weighted 3PT Defense
        if self.weights.defense_premium > 0:
            # Does their 3pt def hold up against elite opponents?
            def_3a = (team_a.def_efficiency or 100) * (team_a.sos or 0)
            def_3b = (team_b.def_efficiency or 100) * (team_b.sos or 0)
            final_probability += (def_3b - def_3a) * 0.0001 * self.weights.defense_premium

        # Round 30: Rust vs Rhythm
        # If a team won their conf tourney (tourney_momentum=1.0) but is a high seed (rest),
        # they might start slow. If they played a play-in, they might be in rhythm.
        if round_num == 1:
            # Proxy: If tourney_momentum is 1.0 (winner), possible rust
            rust_a = self.weights.rust_penalty if (team_a.tourney_momentum or 0) > 0.9 else 0.0
            rust_b = self.weights.rust_penalty if (team_b.tourney_momentum or 0) > 0.9 else 0.0
            final_probability -= (rust_a - rust_b)

        # --- Rounds 31-33: Final Convergence ---
        # Round 31: Intuition Factor Dominance (Global Composite)
        if self.weights.intuition_factor_weight > 0:
            intuition_a = team_a.intuition_factor
            intuition_b = team_b.intuition_factor
            final_probability += (intuition_a - intuition_b) * 0.005 * self.weights.intuition_factor_weight

        # Round 32: Blue Blood Institutional Knowledge
        if self.weights.blue_blood_bonus > 0:
            hist_a = min(1.0, (team_a.historical_tourney_wins or 0) / 100.0)
            hist_b = min(1.0, (team_b.historical_tourney_wins or 0) / 100.0)
            # The "Pressure of the Jersey" bonus - slight edge in early rounds
            if round_num <= 2:
                final_probability += (hist_a - hist_b) * 0.05 * self.weights.blue_blood_bonus

        # --- Rounds 34-40: Batch 6 - Situational Mastery ---
        # Round 34: Shot Clock Pressure (Late Clock Efficiency)
        # Proxy: Elite ball handlers + Assist % = Better late clock execution
        if self.weights.shot_clock_weight > 0:
            clock_a = (team_a.off_ast_pct or 50) / 100.0 * (1 - (team_a.off_to_pct or 20) / 100.0)
            clock_b = (team_b.off_ast_pct or 50) / 100.0 * (1 - (team_b.off_to_pct or 20) / 100.0)
            final_probability += (clock_a - clock_b) * 0.02 * self.weights.shot_clock_weight

        # Round 35: Scoring Drought Management
        # High efficiency + Low luck = Resilience vs "Famous Dry Spells"
        if self.weights.drought_weight > 0:
            res_a = (team_a.off_efficiency or 100) / 100.0 - (team_a.luck or 0.0)
            res_b = (team_b.off_efficiency or 100) / 100.0 - (team_b.luck or 0.0)
            final_probability += (res_a - res_b) * 0.01 * self.weights.drought_weight

        # Round 36: Offensive Follow-Up Synergy (ORB Second Chance)
        if self.weights.follow_up_weight > 0:
            # ORB% synergy with overall efficiency
            fos_a = (team_a.off_orb_pct or 30) * (team_a.off_efficiency or 100) / 1000.0
            fos_b = (team_b.off_orb_pct or 30) * (team_b.off_efficiency or 100) / 1000.0
            final_probability += (fos_a - fos_b) * 0.005 * self.weights.follow_up_weight

        # Round 37: The "Batman" Defender (Lockdown vs Star)
        if self.weights.stopper_weight > 0:
            # If team_b has a star (high star_reliance), team_a's lockdown (STL/BLK synergy) reduces ppg
            lock_a = (team_a.off_stl_pct or 9) + (team_a.off_blk_pct or 9)
            lock_b = (team_b.off_stl_pct or 9) + (team_b.off_blk_pct or 9)
            
            penalty_b = (team_b.star_reliance or 0.5) * lock_a / 100.0
            penalty_a = (team_a.star_reliance or 0.5) * lock_b / 100.0
            final_probability += (penalty_b - penalty_a) * self.weights.stopper_weight

        # Round 38: 3PT High-Volume Volatility
        if self.weights.three_volatility_weight > 0:
            # High 3PAr teams have higher variance. Penalty if they face an elite 3pt defense.
            # (Assuming def_efg_pct is a proxy for 3pt defense quality)
            vol_a = (team_a.three_par or 0.35) * (team_b.def_efg_pct or 50) / 100.0
            vol_b = (team_b.three_par or 0.35) * (team_a.def_efg_pct or 50) / 100.0
            final_probability -= (vol_a - vol_b) * 0.05 * self.weights.three_volatility_weight

        # Round 39: Timeout Management (Late-Game Coaching)
        if self.weights.timeout_weight > 0:
            # Reusing coach wins as a proxy for late-game chess
            tourney_a = (team_a.coach_tournament_wins or 0) / 20.0
            tourney_b = (team_b.coach_tournament_wins or 0) / 20.0
            final_probability += (tourney_a - tourney_b) * 0.02 * self.weights.timeout_weight

        # Round 40: Venue Proximity (Relative Home Court)
        if self.weights.proximity_weight > 0:
            # travel_dist is already in Team. Closer = better.
            dist_a = team_a.travel_dist or 1000
            dist_b = team_b.travel_dist or 1000
            final_probability += (dist_b - dist_a) / 1000.0 * 0.05 * self.weights.proximity_weight

        # --- Rounds 41-50: Batch 7 - Roster & Health Stability ---
        # Round 43: High-Usage Fatigue (Mins > 35 avg)
        # Proxy: If star_reliance is high, assume star plays heavy minutes.
        if self.weights.usage_fatigue_weight > 0:
            fatigue_a = (team_a.star_reliance or 0.5) * 0.1 if round_num >= 4 else 0.0
            fatigue_b = (team_b.star_reliance or 0.5) * 0.1 if round_num >= 4 else 0.0
            final_probability -= (fatigue_a - fatigue_b) * self.weights.usage_fatigue_weight

        # Round 44: Portal Chemistry (March reliance penalty)
        if self.weights.portal_chemistry_weight > 0:
            chem_a = (team_a.portal_usage_pct or 0.2) * 0.05 if round_num >= 4 else 0.0
            chem_b = (team_b.portal_usage_pct or 0.2) * 0.05 if round_num >= 4 else 0.0
            final_probability -= (chem_a - chem_b) * self.weights.portal_chemistry_weight

        # Round 45: Rust/Reset (1-seed reset)
        if self.weights.rust_reset_weight > 0 and round_num == 1:
            if team_a.seed == 1 and (team_a.tourney_momentum or 0) < 0.5:
                # Lost early in conf tourney - "Reset" bonus
                final_probability += 0.03 * self.weights.rust_reset_weight
            if team_b.seed == 1 and (team_b.tourney_momentum or 0) < 0.5:
                final_probability -= 0.03 * self.weights.rust_reset_weight

        # Round 46: Play-in Rhythm (11/12 seeds)
        if self.weights.playin_rhythm_weight > 0 and round_num == 1:
            # Proxy: If conference is not power and seed is 11/12, possible play-in winner
            rhythm_a = 0.04 if team_a.seed in [11, 12] and not getattr(team_a, 'is_power_conf', True) else 0.0
            rhythm_b = 0.04 if team_b.seed in [11, 12] and not getattr(team_b, 'is_power_conf', True) else 0.0
            final_probability += (rhythm_a - rhythm_b) * self.weights.playin_rhythm_weight

        # Round 48: Backcourt Experience Gap (Predictor #1)
        if self.weights.backcourt_exp_weight > 0:
            exp_a = (team_a.off_ft_pct or 70) / 100.0 * (team_a.experience or 2.0)
            exp_b = (team_b.off_ft_pct or 70) / 100.0 * (team_b.experience or 2.0)
            final_probability += (exp_a - exp_b) * 0.03 * self.weights.backcourt_exp_weight

        # Round 49: Rim Protection (Defensive 2PT%)
        if self.weights.rim_protection_weight > 0:
            # def_efg_pct is often driven by 3pt defense. 
            # We use (100 - def_efg_pct) as a proxy for rim protection if we don't have raw 2pt data.
            rim_a = 100 - (team_a.def_efg_pct or 50)
            rim_b = 100 - (team_b.def_efg_pct or 50)
            final_probability += (rim_a - rim_b) / 100.0 * 0.05 * self.weights.rim_protection_weight

        # Round 50: The "Choke" Factor (Late underdogs)
        if self.weights.choke_factor_weight > 0 and round_num >= 5:
            # Underdogs (lower seed) tend to choke if they have poor FT%
            choke_a = (100 - (team_a.off_ft_pct or 70)) / 100.0 if team_a.seed > team_b.seed else 0.0
            choke_b = (100 - (team_b.off_ft_pct or 70)) / 100.0 if team_b.seed > team_a.seed else 0.0
            final_probability -= (choke_a - choke_b) * 0.1 * self.weights.choke_factor_weight

        # --- Rounds 51-60: Batch 8 - Era-Specific Historical Replay ---
        # Detect Era from team.year
        year = team_a.year or 2024
        if self.weights.defensive_grit_bias > 0 and year <= 2010:
            # Physical Era: Defensive delta is 15% more impactful
            def_delta_grit = (team_b.def_efficiency or 100) - (team_a.def_efficiency or 100)
            final_probability += (def_delta_grit * 0.001) * self.weights.defensive_grit_bias

        if self.weights.three_point_dominance > 0 and year >= 2015:
            # Space Era: 3PAr advantage is 20% more impactful
            three_delta = (team_a.three_par or 0.35) - (team_b.three_par or 0.35)
            # High 3PAr teams win more in high-efficiency eras
            final_probability += three_delta * 0.1 * self.weights.three_point_dominance

        if self.weights.rim_pressure_multiplier > 0 and year >= 2024:
            # Modern/Rim Era: Efficiency inside matters more (Proxy: off_efg_pct)
            rim_a = (team_a.off_efg_pct or 50) - (team_a.three_par or 0.35) * 10
            rim_b = (team_b.off_efg_pct or 50) - (team_b.three_par or 0.35) * 10
            final_probability += (rim_a - rim_b) * 0.01 * self.weights.rim_pressure_multiplier

        if self.weights.pace_sensitivity > 0:
            # Year-based pace shift: 35s shot clock (pre-2015) vs 30s
            pace_boost = 0.02 if (year < 2015 and (team_a.pace or 70) < 66) else 0.0
            pace_penalty = 0.02 if (year >= 2015 and (team_a.pace or 70) < 66) else 0.0
            final_probability += (pace_boost - pace_penalty) * self.weights.pace_sensitivity

        # --- Rounds 61-70: Batch 9 - Advanced Tactical Mechanics ---
        # Round 61: Zone Efficiency vs 3PT Heavy
        if self.weights.zone_efficiency_weight > 0:
            # Proxy: High def_efg but high three_par allowed = likely zone
            # Zone is vulnerable to high 3PAr offenses
            zone_a = 1.0 if team_a.archetype == "Pace Killer" and (team_b.three_par or 0) > 0.4 else 0.0
            zone_b = 1.0 if team_b.archetype == "Pace Killer" and (team_a.three_par or 0) > 0.4 else 0.0
            # If you are a zone team against a high 3pt team, you might struggle
            final_probability -= (zone_a - zone_b) * 0.03 * self.weights.zone_efficiency_weight

        # Round 62: Press Disruption (2nd Half)
        if self.weights.press_disruption_weight > 0 and round_num >= 2:
            # Press works better with depth (bench_minutes_pct)
            press_a = (team_a.def_to_pct or 18) * (team_a.bench_minutes_pct or 0.2)
            press_b = (team_b.def_to_pct or 18) * (team_b.bench_minutes_pct or 0.2)
            final_probability += (press_a - press_b) * 0.005 * self.weights.press_disruption_weight

        # Round 63: Pace Control Dominance
        if self.weights.pace_control_weight > 0:
            # Ability to force slow pace vs fast teams
            control_a = 1.0 if team_a.archetype == "Pace Killer" and (team_b.pace or 70) > 72 else 0.0
            control_b = 1.0 if team_b.archetype == "Pace Killer" and (team_a.pace or 70) > 72 else 0.0
            final_probability += (control_a - control_b) * 0.04 * self.weights.pace_control_weight

        # Round 64: Rotation Depth (High Possession Games)
        if self.weights.rotation_depth_weight > 0 and (team_a.pace or 70) > 71:
            depth_a = team_a.bench_minutes_pct or 0.2
            depth_b = team_b.bench_minutes_pct or 0.2
            final_probability += (depth_a - depth_b) * 0.1 * self.weights.rotation_depth_weight

        # Round 65: Half Adjustment V2
        if self.weights.half_adjustment_v2 > 0 and round_num >= 4:
            # Elite coaches (Moxie) adjust better in deep rounds
            adj_a = (team_a.coach_tournament_wins or 0) * 0.01
            adj_b = (team_b.coach_tournament_wins or 0) * 0.01
            final_probability += (adj_a - adj_b) * self.weights.half_adjustment_v2

        # --- Rounds 71-80: Batch 10 - Cinderella Dynamics ---
        # Round 71: Mid-Major Underseeded Boost (10-13 seeds)
        if self.weights.mid_major_boost > 0:
            boost_a = 0.05 if team_a.seed in [10, 11, 12, 13] and not getattr(team_a, 'is_power_conf', True) else 0.0
            boost_b = 0.05 if team_b.seed in [10, 11, 12, 13] and not getattr(team_b, 'is_power_conf', True) else 0.0
            final_probability += (boost_a - boost_b) * self.weights.mid_major_boost

        # Round 72: Cinderella Momentum (Sweet 16 runs)
        if self.weights.cinderella_momentum > 0 and round_num >= 2:
            mom_a = 0.03 if team_a.seed in [10, 11, 12] else 0.0
            mom_b = 0.03 if team_b.seed in [10, 11, 12] else 0.0
            final_probability += (mom_a - mom_b) * self.weights.cinderella_momentum

        # Round 73: Auto-Qualifier Rhythm (Conference Champs)
        if self.weights.auto_qualifier_rhythm > 0 and round_num <= 2:
            # Proxy: High momentum + Mid-major
            rhy_a = 0.02 if (team_a.momentum or 0.5) > 0.8 and not getattr(team_a, 'is_power_conf', True) else 0.0
            rhy_b = 0.02 if (team_b.momentum or 0.5) > 0.8 and not getattr(team_b, 'is_power_conf', True) else 0.0
            final_probability += (rhy_a - rhy_b) * self.weights.auto_qualifier_rhythm

        # Round 74: Seed 12 vs 5 Volatility Bias
        if self.weights.seed_12_5_bias > 0 and round_num == 1:
            bias_a = 0.06 if team_a.seed == 12 and team_b.seed == 5 else 0.0
            bias_b = 0.06 if team_b.seed == 12 and team_a.seed == 5 else 0.0
            final_probability += (bias_a - bias_b) * self.weights.seed_12_5_bias

        # --- Rounds 81-93: Batch 11 - Clutch & Fatigue Management ---
        # Round 81: Clutch Efficiency (Final 5 mins proxy)
        if self.weights.clutch_efficiency_weight > 0:
            # High efficiency teams shoot better in clutch
            clutch_a = (team_a.off_efg_pct or 50) / 100.0
            clutch_b = (team_b.off_efg_pct or 50) / 100.0
            final_probability += (clutch_a - clutch_b) * 0.05 * self.weights.clutch_efficiency_weight

        # Round 82: Short-bench Boost (Tournament mastery)
        if self.weights.short_bench_boost > 0 and round_num >= 2:
            # Short bench (<= 25% min) can be an advantage
            bench_a = team_a.bench_minutes_pct or 0.25
            bench_b = team_b.bench_minutes_pct or 0.25
            boost_a = 0.03 if bench_a <= 0.25 else 0.0
            boost_b = 0.03 if bench_b <= 0.25 else 0.0
            final_probability += (boost_a - boost_b) * self.weights.short_bench_boost

        # Round 83: Pressure Turnover Stability (Late Rounds)
        if self.weights.pressure_stability_weight > 0 and round_num >= 4:
            # High TO% teams fail under pressure
            to_a = team_a.off_to_pct or 18
            to_b = team_b.off_to_pct or 18
            final_probability -= (to_a - to_b) * 0.005 * self.weights.pressure_stability_weight

        # Round 84: Coach Clutch Multiplier
        if self.weights.coach_clutch_multiplier > 0:
            # Moxie coach wins close games
            c_a = (team_a.coach_tournament_wins or 0) * 0.005
            c_b = (team_b.coach_tournament_wins or 0) * 0.005
            final_probability += (c_a - c_b) * self.weights.coach_clutch_multiplier

        # --- Rounds 94-100: Batch 12 - Tournament DNA & Calibration ---
        # Round 94: Blue Blood Aura (Legacy Stability in R1/R2)
        if self.weights.blue_blood_aura > 0 and round_num <= 2:
            blue_bloods = ["Kansas", "Kentucky", "Duke", "North Carolina", "UCLA", "Indiana", "UConn", "Villanova", "Michigan State"]
            aura_a = 0.05 if any(bb in team_a.name for bb in blue_bloods) else 0.0
            aura_b = 0.05 if any(bb in team_b.name for bb in blue_bloods) else 0.0
            final_probability += (aura_a - aura_b) * self.weights.blue_blood_aura

        # Round 95: Committee Seeding Error (Underseeded predictor)
        if self.weights.committee_error_bias > 0:
            # Proxy: Estimated rank based on seed vs actual predictive rank
            # A #10 seed (seed 10) who is actually TOP 20 in rank is heavily underseeded
            # Seed 10 expected rank is ~37-40. 
            def get_underseed_value(t):
                if not getattr(t, 'rank', None) or not t.seed: return 0.0
                expected_rank = (t.seed - 1) * 4 + 2
                delta = expected_rank - t.rank
                return max(0, delta) * 0.005
                
            error_a = get_underseed_value(team_a)
            error_b = get_underseed_value(team_b)
            final_probability += (error_a - error_b) * self.weights.committee_error_bias

        # --- Phase 2: Rounds 101-110 - The Physicality Crisis ---
        # Round 101: Hand-Check Penalty (Pre-2010)
        if self.weights.hand_check_penalty > 0 and (team_a.year or 2025) < 2010:
            # Physical defensive eras penalized high-assist/high-usage guards
            # Proxy: High AST% teams in physical eras had higher turnover variance
            def get_hand_check_risk(t):
                ast = t.off_ast_pct or 50.0
                to = t.off_to_pct or 18.0
                return (ast * to) / 1000.0
            
            risk_a = get_hand_check_risk(team_a)
            risk_b = get_hand_check_risk(team_b)
            final_probability -= (risk_a - risk_b) * self.weights.hand_check_penalty

        # Round 102: Post-Dominance Bias (Pre-2010)
        if self.weights.post_dominance_weight > 0 and (team_a.year or 2025) < 2010:
            # Era where big men and rim protection ruled
            blk_a = (team_a.off_blk_pct or 5.0) / 10.0
            blk_b = (team_b.off_blk_pct or 5.0) / 10.0
            final_probability += (blk_a - blk_b) * 0.1 * self.weights.post_dominance_weight

        # Round 103: Slow-Pace Stability (Pre-2015 / 35s Shot Clock)
        if self.weights.slow_pace_stability > 0 and (team_a.year or 2025) < 2015:
            # Teams playing slow (< 65 pace) in 35s clock era were more stable
            pace_a = team_a.pace or 70.0
            pace_b = team_b.pace or 70.0
            stability_a = 0.04 if pace_a < 65 else 0.0
            stability_b = 0.04 if pace_b < 65 else 0.0
            final_probability += (stability_a - stability_b) * self.weights.slow_pace_stability

        # --- Phase 2: Rounds 111-120 - The 3-Point Revolution ---
        # Round 111: 3-Point Variance Scaling (Post-2015)
        if self.weights.three_point_variance_multiplier > 0 and (team_a.year or 2025) >= 2015:
            # High 3PT volume creates wider outcome distribution
            # In simulation, we proxy this by adjusting luck sensitivity
            def get_3pt_variance(t):
                return max(0, (t.three_par or 0.3) - 0.35) * 0.1
            
            var_a = get_3pt_variance(team_a)
            var_b = get_3pt_variance(team_b)
            final_probability += (var_a - var_b) * self.weights.three_point_variance_multiplier

        # Round 112: Freedom of Movement (Offensive boost post-2013)
        if self.weights.freedom_of_movement_boost > 0 and (team_a.year or 2025) >= 2013:
            # Refs call more hand-checks -> high FT rate is more valuable
            ftr_a = team_a.off_ft_rate or 0.3
            ftr_b = team_b.off_ft_rate or 0.3
            final_probability += (ftr_a - ftr_b) * 0.05 * self.weights.freedom_of_movement_boost

        # --- Phase 2: Rounds 121-130 - NIL & Portal Volatility ---
        # Round 121: Portal Instability Penalty (Post-2021)
        if self.weights.portal_instability_penalty > 0 and (team_a.year or 2025) >= 2021:
            # High transfer churn causes early-round rhythm issues
            portal_a = 0.03 if (team_a.portal_usage_pct or 0) > 0.30 and round_num <= 2 else 0.0
            portal_b = 0.03 if (team_b.portal_usage_pct or 0) > 0.30 and round_num <= 2 else 0.0
            final_probability -= (portal_a - portal_b) * self.weights.portal_instability_penalty

        # Round 122: NIL Resource Advantage
        if self.weights.nil_resource_advantage > 0 and (team_a.year or 2025) >= 2021:
            # Power conference depth advantage in late rounds
            nil_a = 0.02 if team_a.is_power_conf and round_num >= 4 else 0.0
            nil_b = 0.02 if team_b.is_power_conf and round_num >= 4 else 0.0
            final_probability += (nil_a - nil_b) * self.weights.nil_resource_advantage

        # --- Phase 2: Rounds 131-140 - Dynamic Momentum Decay ---
        # Round 131: Conf Tourney Marathon Fatigue
        if self.weights.conf_tourney_marathon_fatigue > 0:
            # High tourney momentum (winning 4 games in 4 days) causes R1/R2 fatigue
            fatigue_a = 0.04 if (team_a.tourney_momentum or 0) > 0.8 and round_num <= 2 else 0.0
            fatigue_b = 0.04 if (team_b.tourney_momentum or 0) > 0.8 and round_num <= 2 else 0.0
            final_probability -= (fatigue_a - fatigue_b) * self.weights.conf_tourney_marathon_fatigue

        # Round 132: Elite Conference Resilience
        if self.weights.elite_conf_momentum_boost > 0 and (team_a.tourney_momentum or 0) > 0.8:
            # Bonus for Big East/Big 12 marathon winners (historically resilient)
            elite_confs = ["Big East", "Big 12"]
            boost_a = 0.03 if (team_a.conference in elite_confs) else 0.0
            boost_b = 0.03 if (team_b.conference in elite_confs) else 0.0
            final_probability += (boost_a - boost_b) * self.weights.elite_conf_momentum_boost

        # --- Phase 2: Rounds 141-150 - Venue/Travel Specificity ---
        # Round 141: Travel Distance Fatigue (Proxy for venue stress)
        if self.weights.altitude_fatigue_penalty > 0:
            # Long travel (> 1500 miles) impacts high-tempo teams more
            def get_travel_impact(t):
                dist = t.travel_dist or 0
                pace = t.pace or 70
                if dist > 1500 and pace > 72: return 0.05
                return 0.0
            
            travel_a = get_travel_impact(team_a)
            travel_b = get_travel_impact(team_b)
            final_probability -= (travel_a - travel_b) * self.weights.altitude_fatigue_penalty

        # --- Phase 2: Rounds 151-160 - Personnel Specificity ---
        # Round 151: Star Reliance Penalty (Point of failure risk)
        if self.weights.star_reliance_penalty > 0:
            # High star reliance teams (> 35%) are riskier in early rounds (upset prone)
            risk_a = 0.04 if (team_a.star_reliance or 0) > 0.35 and round_num <= 2 else 0.0
            risk_b = 0.04 if (team_b.star_reliance or 0) > 0.35 and round_num <= 2 else 0.0
            final_probability -= (risk_a - risk_b) * self.weights.star_reliance_penalty

        # Round 152: Deep Bench Stability
        if self.weights.deep_bench_stability > 0:
            # High bench usage protects against foul trouble and fatigue
            bench_a = (team_a.bench_minutes_pct or 0.25) * 0.1
            bench_b = (team_b.bench_minutes_pct or 0.25) * 0.1
            final_probability += (bench_a - bench_b) * self.weights.deep_bench_stability

        # --- Phase 2: Rounds 161-170 - Coaching Tenacity ---
        # Round 161: Coach Experience Aura
        if self.weights.coach_final_four_aura > 0:
            # High win count proxy for F4 experience
            wins_a = (team_a.coach_tournament_wins or 0)
            wins_b = (team_b.coach_tournament_wins or 0)
            aura_a = 0.05 if wins_a >= 10 else (0.02 if wins_a >= 5 else 0.0)
            aura_b = 0.05 if wins_b >= 10 else (0.02 if wins_b >= 5 else 0.0)
            final_probability += (aura_a - aura_b) * self.weights.coach_final_four_aura

        # --- Phase 2: Rounds 171-180 - Resume Dominance ---
        # Round 171: Quad 1 Resilience Proxy
        if self.weights.quad_1_resilience_weight > 0:
            # Quad 1 = High SOS + High Win Pct
            def get_quad1_proxy(t):
                return (t.sos or 0) * (t.total_win_pct or 0.5)
            
            q1_a = get_quad1_proxy(team_a)
            q1_b = get_quad1_proxy(team_b)
            final_probability += (q1_a - q1_b) * 0.01 * self.weights.quad_1_resilience_weight

        # --- Phase 2: Rounds 181-190 - Three-Point Gravity ---
        # Round 181: Spacing / Gravity Boost
        if self.weights.three_point_gravity_weight > 0:
            # High quality + high volume spacing opens the paint
            def get_gravity_boost(t):
                if (t.off_three_pt_pct or 0) > 38.0 and (t.three_par or 0) > 0.40:
                    return 0.04
                return 0.0
            
            grav_a = get_gravity_boost(team_a)
            grav_b = get_gravity_boost(team_b)
            final_probability += (grav_a - grav_b) * self.weights.three_point_gravity_weight

        # --- Phase 2: Rounds 191-200 - Final Era Calibration ---
        # Round 191: Era Crossover Stability
        if self.weights.era_crossover_stability > 0:
            # Reduce volatility when comparing different years
            year_diff = abs((team_a.year or 2025) - (team_b.year or 2025))
            if year_diff > 5:
                # Slight pull towards the mean to handle era variance
                final_probability = (final_probability * (1.0 - 0.05 * self.weights.era_crossover_stability)) + (0.5 * 0.05 * self.weights.era_crossover_stability)

        # --- Cycle 3: Rounds 201-215 - Archetype Matchup Logic ---
        # Round 201: Glass Crusher vs Pace Killer Interaction
        if self.weights.glass_pace_interaction_weight > 0:
            # Volume of ORB beats the limit of Tempo
            is_glass_a = (team_a.off_orb_pct or 25.0) > 33.0
            is_pace_a = (team_a.pace or 70.0) < 65.0
            is_glass_b = (team_b.off_orb_pct or 25.0) > 33.0
            is_pace_b = (team_b.pace or 70.0) < 65.0
            
            # If A is glass and B is pace: A gets boost
            impact = 0.0
            if is_glass_a and is_pace_b: impact += 0.04
            if is_glass_b and is_pace_a: impact -= 0.04
            final_probability += impact * self.weights.glass_pace_interaction_weight

        # Round 202: Modern Small Ball Bias (Post-2015)
        if self.weights.small_ball_bias_modern > 0 and (team_a.year or 2025) >= 2015:
            # Power conference 3-point volume logic
            def get_small_ball_factor(t):
                if (t.three_par or 0) > 0.42 and t.is_power_conf: return 0.03
                return 0.0
            
            sb_a = get_small_ball_factor(team_a)
            sb_b = get_small_ball_factor(team_b)
            final_probability += (sb_a - sb_b) * self.weights.small_ball_bias_modern

        # --- Cycle 3: Rounds 216-230 - Tournament Resilience ---
        # Round 216: Adrenaline Dump / Low Seed Crash
        if self.weights.low_seed_adrenaline_crash > 0 and round_num == 2:
            # Upset winners (seed > 12) rarely sustain in R32
            dump_a = 0.05 if team_a.seed >= 13 else 0.0
            dump_b = 0.05 if team_b.seed >= 13 else 0.0
            final_probability -= (dump_a - dump_b) * self.weights.low_seed_adrenaline_crash

        # Round 217: No. 11 Seed Sustainability
        if self.weights.eleven_seed_sustainability > 0 and round_num >= 2:
            # 11-seeds reach S16/E8 at higher clips than 8/9 seeds
            sust_a = 0.04 if team_a.seed == 11 else 0.0
            sust_b = 0.04 if team_b.seed == 11 else 0.0
            final_probability += (sust_a - sust_b) * self.weights.eleven_seed_sustainability

        # --- Cycle 3: Rounds 231-250 - Intuition Factor Refinement ---
        # Round 231: Composure Index
        if self.weights.composure_index_weight > 0:
            # Bonus for elite teams with "bad luck" (regression potential)
            def get_composure(t):
                if (t.pythagorean_expectation or 0.5) > 0.90 and (t.luck or 0) < 0:
                    return 0.05
                return 0.0
            
            comp_a = get_composure(team_a)
            comp_b = get_composure(team_b)
            final_probability += (comp_a - comp_b) * self.weights.composure_index_weight

        # Round 232: Upset Delta
        if self.weights.upset_delta_weight > 0:
            # High intuition factor increases the "Seed Weight" impact (composure dominance)
            # This is a meta-weight adjustment
            final_probability += (seed_diff * 0.005) * self.weights.upset_delta_weight

        # --- Cycle 3: Rounds 251-265 - Tactical Sophistication ---
        # Formula based on Gemini research integration
        if self.weights.rim_contest_frequency_weight > 0 or self.weights.off_ball_movement_weight > 0 or self.weights.gravity_adjusted_3p_weight > 0:
            def calculate_upset_potential(t):
                score = 0
                # 1. Rim Contest Frequency Proxy
                # formula: (Opponent Rim Rate) * (1 - Opponent Rim FG%) / (Defensive FT Rate)
                rim_rate = 0.35 # placeholder for metrics if not in Team model
                rim_fg = (t.def_two_pt_pct or 48.0) / 100.0
                ft_rate = (t.def_ft_rate or 30.0) / 100.0
                rim_contest = (rim_rate * (1.0 - rim_fg)) / (ft_rate + 0.01)
                
                # 2. Off-Ball Movement Index
                # formula: (Assist Rate) * (3P Assisted Rate) * (Adjusted Tempo)
                ast_rate = (t.off_ast_rate or 50.0) / 100.0
                three_ast = 0.85 # placeholder
                tempo = (t.pace or 70.0) / 70.0
                off_ball = ast_rate * three_ast * tempo
                
                # 3. Gravity-Adjusted 3P%
                three_pct_adj = (t.off_three_pt_pct or 34.0) / 34.5
                three_ar_adj = (t.three_par or 0.35) / 0.375
                gravity = three_pct_adj * three_ar_adj
                
                return rim_contest, off_ball, gravity

            rc_a, ob_a, gr_a = calculate_upset_potential(team_a)
            rc_b, ob_b, gr_b = calculate_upset_potential(team_b)
            
            # Apply individual weights
            final_probability += (rc_a - rc_b) * 0.02 * self.weights.rim_contest_frequency_weight
            final_probability += (ob_a - ob_b) * 0.02 * self.weights.off_ball_movement_weight
            final_probability += (gr_a - gr_b) * 0.02 * self.weights.gravity_adjusted_3p_weight
            
            # Implementation Logic: +1.5 Upset Potential if top 10% (relative placeholder logic)
            # If team is lower seed and has elite metrics, boost them against 1-4 seeds
            if seed_diff > 4:
                lower_team = team_a if team_a.seed > team_b.seed else team_b
                higher_team = team_b if lower_team == team_a else team_a
                
                if higher_team.seed <= 4:
                    rc_l, ob_l, gr_l = calculate_upset_potential(lower_team)
                    # Simple threshold for "top 10%" proxy
                    if rc_l > 0.6 or ob_l > 0.6 or gr_l > 1.2:
                        boost = 0.05 * 1.5 # The 1.5 multiplier from research
                        if lower_team == team_a: final_probability += boost
                        else: final_probability -= boost

        # --- Cycle 3: Rounds 266-280 - Era Excellence & Portal Regression ---
        # Round 266: Era Excellence Formulas
        if self.weights.era_excellence_physicality_weight > 0 or self.weights.era_excellence_modern_weight > 0:
            def calculate_excellence(t):
                # Physicality Era (1997-2010 proxy)
                drb_steal = (t.def_orb_pct or 70.0) + (t.def_steal_rate or 9.0)
                is_phys_exc = drb_steal > 85.0 # Proxy for 1.25 * field avg
                
                # Modern Era (2015-2025 proxy)
                ast_to_opp_to = (t.off_ast_rate or 50.0) * (t.def_steal_rate or 9.0) # Simplified proxy
                is_mod_exc = ast_to_opp_to > 600.0 # Proxy
                
                return is_phys_exc, is_mod_exc

            phys_a, mod_a = calculate_excellence(team_a)
            phys_b, mod_b = calculate_excellence(team_b)
            
            # Apply physicality boost for appropriate eras
            if (team_a.year or 2025) <= 2010:
                final_probability += (phys_a - phys_b) * 0.03 * self.weights.era_excellence_physicality_weight
            
            # Apply modern boost for appropriate eras
            if (team_a.year or 2025) >= 2015:
                final_probability += (mod_a - mod_b) * 0.03 * self.weights.era_excellence_modern_weight

        # Round 267: Portal Instability Coefficient (PIC)
        if self.weights.portal_instability_coefficient_weight > 0 and (team_a.year or 2025) >= 2021:
            # High transfer usage leads to late-game collapse
            def get_pic_penalty(t):
                # PIC = (Transfer Minutes % / 100) * (1 / (Avg Career Years with Head Coach))
                # Using portal_instability_penalty as proxy for Transfer Minutes
                transfer_share = (t.experience or 2.0) / 4.0 # Inverse proxy
                pic = (1.0 - transfer_share) * 0.5 # Higher if less experience together
                if pic > 0.45 and round_num == 2 and t.seed <= 4:
                    return 0.06 # The -2.0 efficiency penalty impact
                return 0.0
            
            pic_a = get_pic_penalty(team_a)
            pic_b = get_pic_penalty(team_b)
            final_probability -= (pic_a - pic_b) * self.weights.portal_instability_coefficient_weight

        # --- Cycle 3: Rounds 281-300 - Elite Eight Scarcity ---
        # Round 281: The Cinderella Wall
        if self.weights.elite_eight_cinderella_wall > 0 and round_num == 4:
            # Seeds >= 11 hit a wall in the Elite Eight
            wall_a = 0.08 if team_a.seed >= 11 else 0.0
            wall_b = 0.08 if team_b.seed >= 11 else 0.0
            final_probability -= (wall_a - wall_b) * self.weights.elite_eight_cinderella_wall

        # Round 282: Blue-Blood Final Weekend Aura
        if self.weights.blue_blood_final_weekend_boost > 0 and round_num >= 4:
            blue_bloods = ["uconn", "duke", "kansas", "kentucky", "north carolina", "ucla", "indiana"]
            aura_a = 0.04 if any(bb in (team_a.name or "").lower() for bb in blue_bloods) else 0.0
            aura_b = 0.04 if any(bb in (team_b.name or "").lower() for bb in blue_bloods) else 0.0
            final_probability += (aura_a - aura_b) * self.weights.blue_blood_final_weekend_boost

        # Round 283: Veteran Backcourt Scaling
        if self.weights.veteran_backcourt_scaling > 0 and round_num >= 3:
            # Guard experience counts for more in Sweet 16 and beyond
            exp_a = (team_a.experience or 2.0) / 4.0
            exp_b = (team_b.experience or 2.0) / 4.0
            # Higher weight in later rounds
            round_multiplier = (round_num - 2) * 0.05
            final_probability += (exp_a - exp_b) * round_multiplier * self.weights.veteran_backcourt_scaling

        # --- Cycle 3: Rounds 301-315 - Defensive Continuity & Shot Selection ---
        # Round 301: Defensive Switching Continuity
        if self.weights.defensive_switching_continuity > 0:
            # High experience + high defensive efficiency = switching readiness
            def get_switch_score(t):
                if (t.experience or 2.0) > 2.5 and (t.def_adj_eff or 100.0) < 95.0:
                    return 0.05
                return 0.0
            
            sw_a = get_switch_score(team_a)
            sw_b = get_switch_score(team_b)
            final_probability += (sw_a - sw_b) * self.weights.defensive_switching_continuity

        # Round 302: Mid-Range March Value (Late Rounds Only)
        if self.weights.mid_range_march_value > 0 and round_num >= 4:
            # Efficiency on 2PT shots that aren't at the rim (proxied by 2PT% vs Rim%)
            def get_mid_range_value(t):
                # If 2PT% is high but Rim share is low, it implies mid-range efficiency
                two_pt = (t.off_two_pt_pct or 50.0)
                rim_share = 0.40 # placeholder
                if two_pt > 52.0: return 0.04
                return 0.0
            
            mr_a = get_mid_range_value(team_a)
            mr_b = get_mid_range_value(team_b)
            final_probability += (mr_a - mr_b) * self.weights.mid_range_march_value

        # Round 303: Defensive Versatility (Bigs who can switch)
        if self.weights.defensive_versatility_index > 0:
            # Proxied by high rim protection + low opponent 3PA rate (implies perimeter mobility)
            def get_versatility(t):
                if (t.rim_protection_eff or 0.0) > 0.6 and (t.def_three_pt_pct or 34.0) < 32.0:
                    return 0.03
                return 0.0
            
            dv_a = get_versatility(team_a)
            dv_b = get_versatility(team_b)
            final_probability += (dv_a - dv_b) * self.weights.defensive_versatility_index

        # --- Cycle 3: Rounds 316-333 - Final Calibration & Tournament Aura ---
        # Round 316: Tournament Aura (Multi-Championship Programs)
        if self.weights.tournament_aura_boost > 0 and round_num >= 5:
            aura_list = ["ucla", "kentucky", "north carolina", "uconn", "duke", "indiana", "kansas"]
            aura_a = 0.06 if any(hp in (team_a.name or "").lower() for hp in aura_list) else 0.0
            aura_b = 0.06 if any(hp in (team_b.name or "").lower() for hp in aura_list) else 0.0
            final_probability += (aura_a - aura_b) * self.weights.tournament_aura_boost

        # Round 317: Accumulative Travel Fatigue
        if self.weights.accumulative_travel_fatigue > 0:
            def get_travel_impact(t):
                # Penalty for miles traveled (proxied by distance from home)
                dist = (t.distance_from_home or 500.0)
                # Eastward travel penalty (simplified proxy)
                tz_penalty = 0.03 if dist > 1500.0 else 0.0
                return (dist / 10000.0) + tz_penalty # Scale miles to [0, 0.1] range
            
            tr_a = get_travel_impact(team_a)
            tr_b = get_travel_impact(team_b)
            # Accumulate across rounds (higher penalty later)
            round_scale = 1.0 + (round_num * 0.2)
            final_probability -= (tr_a - tr_b) * round_scale * self.weights.accumulative_travel_fatigue

        # Round 318: Championship Pedigree (The UConn Effect)
        if self.weights.championship_pedigree_weight > 0 and round_num == 6:
            # Programs that are historically dominant in championship games
            pedigree = ["uconn", "ucla", "duke"] # Simplified list
            p_a = 0.10 if any(ped in (team_a.name or "").lower() for ped in pedigree) else 0.0
            p_b = 0.10 if any(ped in (team_b.name or "").lower() for ped in pedigree) else 0.0
            final_probability += (p_a - p_b) * self.weights.championship_pedigree_weight

        # (Implicitly handled by the optimization of all weights simultaneously)

        # Clamp to valid probability bounds [0.01, 0.99]
        final_probability = max(0.01, min(0.99, final_probability))
        
        return final_probability

    def simulate_matchup(self, team_a_name: str, team_b_name: str, round_num: int = 1) -> str:
        """Simulates a game between two teams and returns the winner's name."""
        # Check for Matchup Locks (Phase 8)
        lock_key1 = f"{team_a_name} vs {team_b_name}"
        lock_key2 = f"{team_b_name} vs {team_a_name}"
        
        if lock_key1 in self.locks:
            return self.locks[lock_key1]
        if lock_key2 in self.locks:
            return self.locks[lock_key2]
            
        team_a = self.teams.get(team_a_name)
        team_b = self.teams.get(team_b_name)
        
        if not team_a: return team_b_name
        if not team_b: return team_a_name
        
        prob_a = self.calculate_win_probability(team_a, team_b, round_num)
        winner = team_a_name if random.random() < prob_a else team_b_name
        
        # State Update for Due Factor
        self.total_games += 1
        favored_team = team_a_name if prob_a > 0.5 else team_b_name
        if winner != favored_team:
            self.upset_count += 1
            
        return winner
