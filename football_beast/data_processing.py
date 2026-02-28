"""
Football Beast - Data Processing & Feature Engineering
Advanced football analytics for 8 prediction markets
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from config import FEATURE_CONFIG, FEATURE_WEIGHTS

class FootballFeatureEngineering:
    """Advanced feature engineering for football analytics"""
    
    def __init__(self):
        self.config = FEATURE_CONFIG
        self.feature_list = []
    
    # ============================================================
    # CORE ATTACKING & DEFENSIVE METRICS
    # ============================================================
    
    def calculate_expected_goals(self, team_data: Dict) -> Dict:
        """
        Expected Goals (xG) - Quality of chances created
        Based on shot types, positions, and conversion rates
        """
        try:
            shots = team_data.get('shots_on_target', 0)
            shots_total = team_data.get('shots_total', 1)
            goals = team_data.get('goals_for', 0)
            
            # xG per shot (quality metric)
            shot_quality = goals / max(shots, 1)
            
            # Expected goals = expected_shot_volume * expected_conversion
            expected_shot_volume = shots_total / max(team_data.get('matches_played', 1), 1)
            expected_conversion = shot_quality * 1.2  # Small boost for home advantage effect
            
            xg = expected_shot_volume * expected_conversion
            
            return {
                'xg': min(max(xg, 0), 5),  # Cap between 0-5
                'shot_quality': shot_quality,
                'shots_per_game': expected_shot_volume,
                'conversion_rate': shot_quality
            }
        except:
            return {'xg': 1.5, 'shot_quality': 0.15, 'shots_per_game': 4.5, 'conversion_rate': 0.15}
    
    def calculate_defensive_metrics(self, team_data: Dict) -> Dict:
        """
        Defensive solidity - Clean sheets, goals conceded, defensive actions
        """
        try:
            goals_against = team_data.get('goals_against', 1)
            matches = team_data.get('matches_played', 1)
            clean_sheets = team_data.get('clean_sheets', 0)
            tackles = team_data.get('tackles', 0)
            interceptions = team_data.get('interceptions', 0)
            
            goals_against_per_game = goals_against / max(matches, 1)
            clean_sheet_rate = clean_sheets / max(matches, 1)
            defensive_actions_per_game = (tackles + interceptions) / max(matches, 1)
            
            # Defensive rating (lower is better, so invert for prediction)
            defensive_rating = 1.0 / (1.0 + goals_against_per_game)
            
            return {
                'goals_against_per_game': min(goals_against_per_game, 4),
                'clean_sheet_rate': clean_sheet_rate,
                'defensive_actions_per_game': defensive_actions_per_game,
                'defensive_rating': defensive_rating
            }
        except:
            return {
                'goals_against_per_game': 1.2,
                'clean_sheet_rate': 0.25,
                'defensive_actions_per_game': 18,
                'defensive_rating': 0.45
            }
    
    # ============================================================
    # SET PIECE & CORNER ANALYTICS
    # ============================================================
    
    def calculate_set_piece_threat(self, team_data: Dict) -> Dict:
        """
        Corner and set piece threat analysis
        Important for corner over/under predictions
        """
        try:
            corners_for = team_data.get('corners_for', 0)
            corners_against = team_data.get('corners_against', 0)
            matches = team_data.get('matches_played', 1)
            goals_from_corners = team_data.get('goals_from_corners', 0)
            
            corners_per_game = corners_for / max(matches, 1)
            corners_per_game_conceded = corners_against / max(matches, 1)
            corner_conversion = goals_from_corners / max(corners_for, 1)
            
            total_corners_per_game = (corners_for + corners_against) / (2 * max(matches, 1))
            
            return {
                'corners_per_game': corners_per_game,
                'corners_conceded_per_game': corners_per_game_conceded,
                'corner_conversion_rate': corner_conversion,
                'total_corners_per_game': total_corners_per_game,
                'corner_threat_score': (corners_per_game * 0.4 + corner_conversion * 10 * 0.6)
            }
        except:
            return {
                'corners_per_game': 5.0,
                'corners_conceded_per_game': 4.8,
                'corner_conversion_rate': 0.05,
                'total_corners_per_game': 9.8,
                'corner_threat_score': 3.0
            }
    
    # ============================================================
    # TEMPO & EARLY GAME METRICS
    # ============================================================
    
    def calculate_pace_and_tempo(self, team_data: Dict) -> Dict:
        """
        Game pace, possession tempo, early game tendencies
        Key for early goals (first 30 mins) and early corners
        """
        try:
            possession = team_data.get('possession_pct', 0.50)
            passes = team_data.get('passes_per_game', 400)
            matches = team_data.get('matches_played', 1)
            goals_scored = team_data.get('goals_for', 0)
            
            # Early goals tendency - teams that score early
            goals_first_half = team_data.get('goals_first_half', goals_scored * 0.45)
            early_goal_rate = goals_first_half / max(goals_scored, 1)
            
            # Pace = (possession * pass_ratio) - indicates attacking tempo
            pace_rating = (possession * passes) / 500  # Normalized
            
            # First 30 mins goal tendency
            first_30_min_rate = team_data.get('goals_0_30_mins', 0) / max(matches, 1)
            
            return {
                'possession': possession,
                'passes_per_game': passes,
                'pace_rating': min(pace_rating, 2.0),
                'early_goal_rate': early_goal_rate,
                'first_30_min_goals': first_30_min_rate,
                'attacking_tempo': (possession + pace_rating) / 2
            }
        except:
            return {
                'possession': 0.50,
                'passes_per_game': 400,
                'pace_rating': 0.80,
                'early_goal_rate': 0.45,
                'first_30_min_goals': 0.65,
                'attacking_tempo': 0.65
            }
    
    # ============================================================
    # FORM & MOMENTUM ANALYTICS
    # ============================================================
    
    def calculate_form(self, team_data: Dict) -> Dict:
        """
        Recent form - last 10 games performance
        Momentum indicators
        """
        try:
            recent_wins = team_data.get('last_10_wins', 3)
            recent_losses = team_data.get('last_10_losses', 2)
            recent_draws = team_data.get('last_10_draws', 5)
            recent_games = recent_wins + recent_losses + recent_draws
            
            recent_goals_for = team_data.get('last_10_goals_for', 15)
            recent_goals_against = team_data.get('last_10_goals_against', 10)
            
            win_rate = recent_wins / max(recent_games, 1)
            goal_diff = (recent_goals_for - recent_goals_against) / max(recent_games, 1)
            points_per_game = (recent_wins * 3 + recent_draws) / max(recent_games, 1)
            
            # Trend detection - are they improving or declining?
            recent_5_points = team_data.get('last_5_points', 0)
            previous_5_points = team_data.get('previous_5_points', 0)
            momentum = (recent_5_points - previous_5_points) / max(previous_5_points, 1)
            
            return {
                'recent_win_rate': win_rate,
                'recent_goal_difference': goal_diff,
                'recent_points_per_game': points_per_game,
                'momentum': momentum,
                'form_rating': (win_rate * 3 + goal_diff) / 4,
                'consistency': 1.0 - (team_data.get('last_10_variance', 0) / 100)
            }
        except:
            return {
                'recent_win_rate': 0.40,
                'recent_goal_difference': 0.30,
                'recent_points_per_game': 1.5,
                'momentum': 0.0,
                'form_rating': 0.50,
                'consistency': 0.70
            }
    
    # ============================================================
    # HEAD-TO-HEAD ANALYSIS
    # ============================================================
    
    def calculate_head_to_head(self, team_a: Dict, team_b: Dict) -> Dict:
        """
        Historical performance between two teams
        """
        try:
            h2h_record = team_a.get('h2h_vs_opponent', {})
            
            team_a_h2h_wins = h2h_record.get('wins', 0)
            team_a_h2h_losses = h2h_record.get('losses', 0)
            team_a_h2h_draws = h2h_record.get('draws', 0)
            total_h2h = team_a_h2h_wins + team_a_h2h_losses + team_a_h2h_draws
            
            h2h_win_rate = team_a_h2h_wins / max(total_h2h, 1)
            
            return {
                'h2h_win_rate': h2h_win_rate,
                'h2h_games': total_h2h,
                'h2h_advantage': 'strong' if h2h_win_rate > 0.60 else 'slight' if h2h_win_rate > 0.45 else 'none'
            }
        except:
            return {
                'h2h_win_rate': 0.40,
                'h2h_games': 5,
                'h2h_advantage': 'none'
            }
    
    # ============================================================
    # BOTH TEAMS TO SCORE ANALYTICS
    # ============================================================
    
    def calculate_btts_probability(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Both Teams to Score prediction
        Based on attacking vs defensive matchups
        """
        try:
            home_xg = home_team.get('xg', 1.5)
            away_xg = away_team.get('xg', 1.5)
            home_def = home_team.get('defensive_rating', 0.50)
            away_def = away_team.get('defensive_rating', 0.50)
            
            # BTTS likelihood = both teams' xG * opponent's defensive weakness
            home_goal_prob = home_xg / 5.0  # Normalize to probability
            away_goal_prob = away_xg / 5.0
            
            # Defensive weakness increases opponent scoring chance
            home_concede_prob = (1.0 - home_def)
            away_concede_prob = (1.0 - away_def)
            
            # BTTS = P(home scores) * P(away scores)
            btts_probability = (home_goal_prob * away_concede_prob) * (away_goal_prob * home_concede_prob)
            
            return {
                'btts_probability': min(btts_probability, 0.95),
                'home_scoring_chance': home_goal_prob,
                'away_scoring_chance': away_goal_prob,
                'home_defensive_weakness': home_concede_prob,
                'away_defensive_weakness': away_concede_prob
            }
        except:
            return {
                'btts_probability': 0.50,
                'home_scoring_chance': 0.55,
                'away_scoring_chance': 0.55,
                'home_defensive_weakness': 0.45,
                'away_defensive_weakness': 0.45
            }
    
    # ============================================================
    # TOTAL GOALS & OVERS/UNDERS
    # ============================================================
    
    def calculate_total_goals_probability(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Full match total goals prediction
        Over/Under 2.5, 3.5 goals
        """
        try:
            home_xg = home_team.get('xg', 1.5)
            away_xg = away_team.get('xg', 1.5)
            
            estimated_total = home_xg + away_xg
            
            # Over probabilities using logistic distribution
            over_2_5 = 1.0 / (1.0 + np.exp(-(estimated_total - 2.5) * 1.5))
            over_3_5 = 1.0 / (1.0 + np.exp(-(estimated_total - 3.5) * 1.5))
            over_4_5 = 1.0 / (1.0 + np.exp(-(estimated_total - 4.5) * 1.5))
            
            return {
                'estimated_total_goals': estimated_total,
                'over_2_5_probability': over_2_5,
                'over_3_5_probability': over_3_5,
                'over_4_5_probability': over_4_5,
                'under_2_5_probability': 1.0 - over_2_5,
                'under_3_5_probability': 1.0 - over_3_5,
                'under_4_5_probability': 1.0 - over_4_5
            }
        except:
            return {
                'estimated_total_goals': 2.8,
                'over_2_5_probability': 0.60,
                'over_3_5_probability': 0.40,
                'over_4_5_probability': 0.20,
                'under_2_5_probability': 0.40,
                'under_3_5_probability': 0.60,
                'under_4_5_probability': 0.80
            }
    
    # ============================================================
    # TEAM-SPECIFIC MARKETS
    # ============================================================
    
    def calculate_team_over_goals(self, team_data: Dict, opponent_def: float) -> Dict:
        """
        Team over goals (1.5, 2.5, 3.5+)
        Team's attacking ability vs opponent's defense
        """
        try:
            xg = team_data.get('xg', 1.5)
            opp_defensive_rating = opponent_def
            
            # Adjust for opponent's defense
            adjusted_xg = xg * (1.0 + (1.0 - opp_defensive_rating))
            
            team_over_1_5 = 1.0 / (1.0 + np.exp(-(adjusted_xg - 1.5) * 1.8))
            team_over_2_5 = 1.0 / (1.0 + np.exp(-(adjusted_xg - 2.5) * 1.8))
            team_over_3_5 = 1.0 / (1.0 + np.exp(-(adjusted_xg - 3.5) * 1.8))
            
            return {
                'adjusted_xg': adjusted_xg,
                'team_over_1_5': team_over_1_5,
                'team_over_2_5': team_over_2_5,
                'team_over_3_5': team_over_3_5
            }
        except:
            return {
                'adjusted_xg': 1.5,
                'team_over_1_5': 0.60,
                'team_over_2_5': 0.35,
                'team_over_3_5': 0.15
            }
    
    # ============================================================
    # EARLY GOALS (FIRST 30 MINS)
    # ============================================================
    
    def calculate_early_goals(self, home_team: Dict, away_team: Dict) -> Dict:
        """
        Early goals in first 30 minutes
        Based on early pace and early goal history
        """
        try:
            home_early_rate = home_team.get('first_30_min_goals', 0.60)
            away_early_rate = away_team.get('first_30_min_goals', 0.60)
            home_pace = home_team.get('pace_rating', 0.8)
            away_pace = away_team.get('pace_rating', 0.8)
            
            # Early goals likelihood from both teams
            combined_early_rate = (home_early_rate + away_early_rate) / 2
            combined_pace = (home_pace + away_pace) / 2
            
            early_goals_factor = combined_early_rate * combined_pace
            
            over_1_5_early = 1.0 / (1.0 + np.exp(-(early_goals_factor - 1.0) * 2.0))
            over_2_5_early = 1.0 / (1.0 + np.exp(-(early_goals_factor - 1.5) * 2.0))
            
            return {
                'early_goals_factor': early_goals_factor,
                'over_1_5_early_goals': over_1_5_early,
                'over_2_5_early_goals': over_2_5_early,
                'home_early_tendency': home_early_rate,
                'away_early_tendency': away_early_rate
            }
        except:
            return {
                'early_goals_factor': 0.55,
                'over_1_5_early_goals': 0.55,
                'over_2_5_early_goals': 0.30,
                'home_early_tendency': 0.50,
                'away_early_tendency': 0.50
            }
    
    # ============================================================
    # WIN PREDICTION (STRAIGHT WIN)
    # ============================================================
    
    def calculate_win_probability(self, home_team: Dict, away_team: Dict, home_advantage: float = 0.06) -> Dict:
        """
        Home/Away/Draw win probability using Poisson approximation
        """
        try:
            home_xg = home_team.get('xg', 1.5)
            away_xg = away_team.get('xg', 1.5)
            home_def = home_team.get('defensive_rating', 0.50)
            away_def = away_team.get('defensive_rating', 0.50)
            
            # Adjust for home advantage
            home_adjusted_xg = home_xg * (1.0 + home_advantage)
            away_adjusted_xg = away_xg * (1.0 - home_advantage * 0.5)
            
            # Form adjustments
            home_form = home_team.get('form_rating', 0.50)
            away_form = away_team.get('form_rating', 0.50)
            
            final_home_xg = home_adjusted_xg * (0.7 + 0.3 * home_form)
            final_away_xg = away_adjusted_xg * (0.7 + 0.3 * away_form)
            
            # Poisson-based win probability
            from scipy import stats
            
            # Estimate win/draw/loss using normal approximation
            home_win_prob = 0
            draw_prob = 0
            away_win_prob = 0
            
            for h_goals in range(0, 6):
                for a_goals in range(0, 6):
                    home_p = (final_home_xg ** h_goals * np.exp(-final_home_xg)) / np.math.factorial(h_goals)
                    away_p = (final_away_xg ** a_goals * np.exp(-final_away_xg)) / np.math.factorial(a_goals)
                    prob = home_p * away_p
                    
                    if h_goals > a_goals:
                        home_win_prob += prob
                    elif h_goals == a_goals:
                        draw_prob += prob
                    else:
                        away_win_prob += prob
            
            return {
                'home_win_probability': home_win_prob,
                'draw_probability': draw_prob,
                'away_win_probability': away_win_prob,
                'home_expected_goals': final_home_xg,
                'away_expected_goals': final_away_xg
            }
        except:
            return {
                'home_win_probability': 0.45,
                'draw_probability': 0.25,
                'away_win_probability': 0.30,
                'home_expected_goals': 1.6,
                'away_expected_goals': 1.2
            }
    
    # ============================================================
    # FEATURE COMPILATION
    # ============================================================
    
    def compile_match_features(self, match_data: Dict) -> Dict:
        """
        Compile all features for a single match
        Returns dictionary with all engineered features
        """
        home_team = match_data.get('home_team', {})
        away_team = match_data.get('away_team', {})
        
        features = {}
        
        # Attacking metrics
        features['home_xg'] = self.calculate_expected_goals(home_team)['xg']
        features['away_xg'] = self.calculate_expected_goals(away_team)['xg']
        
        # Defensive metrics
        home_def = self.calculate_defensive_metrics(home_team)
        away_def = self.calculate_defensive_metrics(away_team)
        features['home_defensive_rating'] = home_def['defensive_rating']
        features['away_defensive_rating'] = away_def['defensive_rating']
        
        # Set pieces
        home_sp = self.calculate_set_piece_threat(home_team)
        away_sp = self.calculate_set_piece_threat(away_team)
        features['home_corner_threat'] = home_sp['corner_threat_score']
        features['away_corner_threat'] = away_sp['corner_threat_score']
        
        # Pace
        home_pace = self.calculate_pace_and_tempo(home_team)
        away_pace = self.calculate_pace_and_tempo(away_team)
        features['home_pace'] = home_pace['pace_rating']
        features['away_pace'] = away_pace['pace_rating']
        
        # Form
        home_form = self.calculate_form(home_team)
        away_form = self.calculate_form(away_team)
        features['home_form'] = home_form['form_rating']
        features['away_form'] = away_form['form_rating']
        
        # Market predictions
        features['btts_probability'] = self.calculate_btts_probability(home_team, away_team)['btts_probability']
        features['total_goals'] = self.calculate_total_goals_probability(home_team, away_team)['estimated_total_goals']
        features['early_goals_factor'] = self.calculate_early_goals(home_team, away_team)['early_goals_factor']
        
        win_probs = self.calculate_win_probability(home_team, away_team)
        features['home_win_prob'] = win_probs['home_win_probability']
        features['draw_prob'] = win_probs['draw_probability']
        features['away_win_prob'] = win_probs['away_win_probability']
        
        return features


class DataValidator:
    """Validate football match data"""
    
    @staticmethod
    def validate_match(match_data: Dict) -> Tuple[bool, str]:
        """Validate match data structure"""
        required_fields = ['home_team', 'away_team', 'match_info']
        
        for field in required_fields:
            if field not in match_data:
                return False, f"Missing field: {field}"
        
        return True, "Valid"


class FeatureScaler:
    """Scale and normalize features"""
    
    def __init__(self):
        self.feature_means = {}
        self.feature_stds = {}
    
    def fit(self, features: np.ndarray) -> None:
        """Fit scaler on training data"""
        self.feature_means = np.mean(features, axis=0)
        self.feature_stds = np.std(features, axis=0) + 1e-8
    
    def transform(self, features: np.ndarray) -> np.ndarray:
        """Transform features"""
        return (features - self.feature_means) / self.feature_stds
    
    def fit_transform(self, features: np.ndarray) -> np.ndarray:
        """Fit and transform"""
        self.fit(features)
        return self.transform(features)
