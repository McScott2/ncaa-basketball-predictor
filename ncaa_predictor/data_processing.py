"""
Data Processing and Feature Engineering
Transforms raw basketball data into powerful predictive features
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_classif
import warnings

warnings.filterwarnings('ignore')

class BasketballFeatureEngineering:
    """
    Advanced feature engineering for NCAA basketball predictions
    """
    
    def __init__(self, config):
        self.config = config
        self.scaler = RobustScaler()
        self.pca = None
        self.feature_importance = None
        
    def calculate_four_factors(self, team_stats):
        """
        Calculate Dean Oliver's Four Factors of Basketball Success
        FG%, 3P Rate, FT Rate, Turnover Rate
        """
        features = {}
        
        # Effective Field Goal Percentage (eFG%)
        features['efg_pct'] = (team_stats.get('FGM', 0) + 0.5 * team_stats.get('3PM', 0)) / team_stats.get('FGA', 1)
        
        # Turnover Rate (TOV% = Turnovers / Possessions)
        features['tov_rate'] = team_stats.get('TO', 0) / (team_stats.get('FGA', 0) + 0.44 * team_stats.get('FTA', 0) + team_stats.get('TO', 0) + 1)
        
        # Free Throw Rate (FTA / FGA)
        features['ft_rate'] = team_stats.get('FTA', 0) / team_stats.get('FGA', 1)
        
        # Offensive Rebound Rate
        features['orb_rate'] = team_stats.get('ORB', 0) / (team_stats.get('ORB', 0) + team_stats.get('DRB', 0) + 1)
        
        # Defensive Rebound Rate
        features['drb_rate'] = team_stats.get('DRB', 0) / (team_stats.get('ORB', 0) + team_stats.get('DRB', 0) + 1)
        
        return features
    
    def calculate_pace_and_efficiency(self, team_stats, game_stats):
        """
        Calculate Pace and Offensive/Defensive Efficiency
        """
        features = {}
        
        # Possessions estimate
        possessions = game_stats.get('FGA', 0) + 0.44 * game_stats.get('FTA', 0) - game_stats.get('ORB', 0) + game_stats.get('TO', 0)
        
        # Offensive Efficiency (Points per 100 possessions)
        features['offensive_efficiency'] = (team_stats.get('PTS', 0) / possessions * 100) if possessions > 0 else 0
        
        # Defensive Efficiency (Points against per 100 possessions) - would use opponent stats
        features['pace'] = possessions / game_stats.get('minutes', 40) * 40 if game_stats.get('minutes', 0) > 0 else 0
        
        return features
    
    def calculate_advanced_stats(self, team_stats, opponent_stats):
        """
        Calculate advanced basketball metrics
        """
        features = {}
        
        # True Shooting Percentage
        ts_attempts = team_stats.get('FGA', 0) + 0.44 * team_stats.get('FTA', 0)
        features['ts_pct'] = (team_stats.get('PTS', 0) / (2 * ts_attempts)) if ts_attempts > 0 else 0
        
        # Assist to Turnover Ratio
        features['ast_to_ratio'] = team_stats.get('AST', 0) / (team_stats.get('TO', 0) + 1)
        
        # Rebound Rate Differential
        features['reb_diff'] = (team_stats.get('TRB', 0) - opponent_stats.get('TRB', 0))
        
        # Steal Rate
        features['steal_rate'] = team_stats.get('STL', 0) / (opponent_stats.get('FGA', 0) + 0.44 * opponent_stats.get('FTA', 0) + opponent_stats.get('TO', 0) + 1)
        
        # Block Rate
        features['block_rate'] = team_stats.get('BLK', 0) / opponent_stats.get('FGA', 1)
        
        return features
    
    def calculate_momentum_indicators(self, recent_games_data):
        """
        Calculate recent form and momentum
        """
        if not recent_games_data or len(recent_games_data) == 0:
            return {
                'recent_form': 0.5,
                'win_streak': 0,
                'scoring_trend': 0,
                'defensive_trend': 0,
                'consistency': 0
            }
        
        recent_games = recent_games_data[-10:]  # Last 10 games
        
        features = {}
        
        # Win rate in last N games
        wins = sum(1 for game in recent_games if game.get('result') == 'W')
        features['recent_form'] = wins / len(recent_games) if recent_games else 0.5
        
        # Current win streak
        win_streak = 0
        for game in reversed(recent_games):
            if game.get('result') == 'W':
                win_streak += 1
            else:
                break
        features['win_streak'] = win_streak
        
        # Scoring trend
        if len(recent_games) >= 2:
            early_avg = np.mean([game.get('PTS', 0) for game in recent_games[:3]])
            recent_avg = np.mean([game.get('PTS', 0) for game in recent_games[-3:]])
            features['scoring_trend'] = recent_avg - early_avg
        else:
            features['scoring_trend'] = 0
        
        # Defensive trend
        if len(recent_games) >= 2:
            early_def = np.mean([game.get('OPP_PTS', 0) for game in recent_games[:3]])
            recent_def = np.mean([game.get('OPP_PTS', 0) for game in recent_games[-3:]])
            features['defensive_trend'] = early_def - recent_def  # Positive = improving
        else:
            features['defensive_trend'] = 0
        
        # Consistency (std dev of scoring)
        features['consistency'] = np.std([game.get('PTS', 0) for game in recent_games]) if recent_games else 0
        
        return features
    
    def engineer_features(self, team_data, opponent_data, recent_games=None):
        """
        Main feature engineering pipeline
        """
        features = {}
        
        # Four Factors
        four_factors = self.calculate_four_factors(team_data)
        features.update({f'team_{k}': v for k, v in four_factors.items()})
        
        opponent_four_factors = self.calculate_four_factors(opponent_data)
        features.update({f'opp_{k}': v for k, v in opponent_four_factors.items()})
        
        # Advanced Stats
        advanced = self.calculate_advanced_stats(team_data, opponent_data)
        features.update({f'team_{k}': v for k, v in advanced.items()})
        
        opponent_advanced = self.calculate_advanced_stats(opponent_data, team_data)
        features.update({f'opp_{k}': v for k, v in opponent_advanced.items()})
        
        # Momentum
        if recent_games:
            momentum = self.calculate_momentum_indicators(recent_games)
            features.update({f'team_{k}': v for k, v in momentum.items()})
        
        # Basic stats
        features['team_pts'] = team_data.get('PTS', 0)
        features['opp_pts'] = opponent_data.get('PTS', 0)
        features['team_score_diff'] = team_data.get('PTS', 0) - opponent_data.get('PTS', 0)
        
        return features
    
    def prepare_features_for_training(self, features_list, target_var=None):
        """
        Prepare features for model training
        """
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        
        # Handle missing values
        df = df.fillna(df.mean(numeric_only=True))
        
        # Scale features
        if self.config.get("scale_features", True):
            feature_cols = [col for col in df.columns if col != target_var and target_var]
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        
        # Optional: PCA
        if self.config.get("pca_enabled", False):
            self.pca = PCA(n_components=0.95)  # Keep 95% variance
            df = pd.DataFrame(self.pca.fit_transform(df))
        
        return df
    
    def get_feature_importance(self, features_df, target, n_features=20):
        """
        Calculate feature importance using mutual information
        """
        scores = mutual_info_classif(features_df, target, random_state=42)
        importance_df = pd.DataFrame({
            'feature': features_df.columns,
            'importance': scores
        }).sort_values('importance', ascending=False)
        
        return importance_df.head(n_features)


class DataValidator:
    """
    Validate and clean basketball data
    """
    
    @staticmethod
    def validate_game_data(game_data):
        """Validate game data structure and values"""
        required_fields = ['team_id', 'opponent_id', 'date', 'points']
        
        for field in required_fields:
            if field not in game_data:
                return False, f"Missing required field: {field}"
        
        # Validate data types and ranges
        if game_data['points'] < 0 or game_data['points'] > 200:
            return False, "Invalid points value"
        
        return True, "Valid"
    
    @staticmethod
    def clean_statistics(stats_dict):
        """Clean and normalize statistics"""
        cleaned = {}
        
        for key, value in stats_dict.items():
            if pd.isna(value):
                cleaned[key] = 0
            elif isinstance(value, (int, float)):
                cleaned[key] = max(0, value)  # No negative values
            else:
                cleaned[key] = value
        
        return cleaned


class FeatureSelector:
    """
    Select the most important features for model training
    """
    
    @staticmethod
    def correlation_based_selection(features_df, target, threshold=0.3):
        """Select features based on correlation with target"""
        correlations = features_df.corrwith(target).abs()
        selected_features = correlations[correlations > threshold].index.tolist()
        return selected_features
    
    @staticmethod
    def variance_based_selection(features_df, threshold=0.01):
        """Remove features with low variance"""
        variances = features_df.var()
        selected_features = variances[variances > threshold].index.tolist()
        return selected_features
