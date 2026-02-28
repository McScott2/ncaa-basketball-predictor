"""
Football Beast Prediction Engine - Configuration
All settings for 8 prediction markets and models
"""

# ============================================================
# PREDICTION MARKETS (The 8 Bet Types)
# ============================================================
PREDICTION_MARKETS = {
    'straight_win': {
        'name': 'Straight Win (Home/Draw/Away)',
        'description': 'Team wins the match',
        'weight': 0.20,
        'complexity': 'low'
    },
    'full_time_over_goals': {
        'name': 'Full Time Over Goals',
        'description': 'Match total over 2.5 or 3.5 goals',
        'weight': 0.18,
        'complexity': 'medium'
    },
    'team_win_either_half': {
        'name': 'Team to Win Either Half',
        'description': 'Team wins first half or second half',
        'weight': 0.12,
        'complexity': 'medium'
    },
    'team_over_goals': {
        'name': 'Team Over Goals',
        'description': 'Team scores 1.5, 2.5, 3.5+ goals',
        'weight': 0.16,
        'complexity': 'medium'
    },
    'team_win_to_nil': {
        'name': 'Team to Win to Nil',
        'description': 'Team wins and opponent scores 0',
        'weight': 0.10,
        'complexity': 'high'
    },
    'early_goals': {
        'name': 'Over Early Goals',
        'description': 'Over 1.5 or 2.5 goals in first 30 mins',
        'weight': 0.08,
        'complexity': 'high'
    },
    'full_time_corners': {
        'name': 'Full Time Corner Over',
        'description': 'Match corners over 8.5, 9.5, 10.5',
        'weight': 0.10,
        'complexity': 'medium'
    },
    'both_teams_to_score': {
        'name': 'Both Teams to Score',
        'description': 'Both teams score at least 1 goal',
        'weight': 0.06,
        'complexity': 'medium'
    }
}

# ============================================================
# ML MODEL CONFIGURATION
# ============================================================
MODEL_CONFIG = {
    'ensemble_weights': {
        'xgboost': 0.35,
        'lightgbm': 0.30,
        'catboost': 0.20,
        'neural_network': 0.15
    },
    'cv_folds': 5,
    'test_size': 0.2,
    'random_state': 42,
    'n_jobs': -1
}

XGBOOST_PARAMS = {
    'max_depth': 6,
    'learning_rate': 0.05,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'random_state': 42,
    'tree_method': 'hist',
    'device': 'cpu'
}

LGBM_PARAMS = {
    'max_depth': 7,
    'learning_rate': 0.05,
    'n_estimators': 200,
    'num_leaves': 31,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'binary',
    'metric': 'auc',
    'random_state': 42,
    'device': 'cpu'
}

CATBOOST_PARAMS = {
    'max_depth': 6,
    'learning_rate': 0.05,
    'iterations': 200,
    'subsample': 0.8,
    'loss_function': 'Logloss',
    'eval_metric': 'AUC',
    'random_state': 42,
    'verbose': False,
    'task_type': 'CPU'
}

NN_PARAMS = {
    'hidden_layers': [128, 64, 32],
    'dropout': 0.3,
    'batch_size': 32,
    'epochs': 100,
    'learning_rate': 0.001,
    'activation': 'relu',
    'output_activation': 'sigmoid'
}

# ============================================================
# FEATURE ENGINEERING CONFIGURATION
# ============================================================
FEATURE_CONFIG = {
    'use_xg': True,
    'use_defensive_metrics': True,
    'use_set_pieces': True,
    'use_form': True,
    'use_head_to_head': True,
    'lookback_games': 10,
    'scale_features': True,
    'handle_missing': 'mean',
    'remove_outliers': True,
    'outlier_threshold': 3
}

# ============================================================
# LEAGUES TO PREDICT
# ============================================================
LEAGUES = {
    'premier_league': {
        'name': 'Premier League',
        'country': 'England',
        'api_id': 39,
        'matches_per_season': 380
    },
    'la_liga': {
        'name': 'La Liga',
        'country': 'Spain',
        'api_id': 140,
        'matches_per_season': 380
    },
    'serie_a': {
        'name': 'Serie A',
        'country': 'Italy',
        'api_id': 135,
        'matches_per_season': 380
    },
    'bundesliga': {
        'name': 'Bundesliga',
        'country': 'Germany',
        'api_id': 78,
        'matches_per_season': 306
    },
    'ligue_1': {
        'name': 'Ligue 1',
        'country': 'France',
        'api_id': 61,
        'matches_per_season': 380
    },
    'champions_league': {
        'name': 'UEFA Champions League',
        'country': 'Europe',
        'api_id': 2,
        'matches_per_season': 125
    }
}

# ============================================================
# PREDICTION THRESHOLDS
# ============================================================
CONFIDENCE_THRESHOLDS = {
    'very_high': 0.75,    # 75%+ confidence
    'high': 0.65,         # 65-74%
    'medium': 0.55,       # 55-64%
    'low': 0.50           # 50-54%
}

EDGE_THRESHOLDS = {
    'strong_value': 0.10,   # 10%+ edge vs implied
    'good_value': 0.06,     # 6-10% edge
    'fair_value': 0.03,     # 3-6% edge
    'no_value': 0.00        # <3% edge
}

# ============================================================
# FEATURE IMPORTANCE & WEIGHTING
# ============================================================
FEATURE_WEIGHTS = {
    'expected_goals': 0.25,
    'defensive_rating': 0.15,
    'attack_rating': 0.15,
    'form': 0.12,
    'corner_threat': 0.10,
    'early_game_pace': 0.08,
    'clean_sheet_rate': 0.08,
    'head_to_head': 0.07
}

# ============================================================
# DATA & PATHS
# ============================================================
DATA_CONFIG = {
    'cache_enabled': True,
    'cache_dir': './data_cache',
    'models_dir': './models',
    'logs_dir': './logs',
    'min_games_for_training': 100,
    'min_games_per_league': 50
}

# ============================================================
# API CONFIGURATION
# ============================================================
API_CONFIG = {
    'football_api': 'https://api-football-v1.p.rapidapi.com/v3',
    'espn_api': 'https://site.api.espn.com/apis/site/v2',
    'timeout': 10,
    'retries': 3,
    'backoff_factor': 0.5
}

# ============================================================
# OUTPUT CONFIGURATION
# ============================================================
OUTPUT_CONFIG = {
    'save_predictions': True,
    'predictions_file': 'predictions.json',
    'save_report': True,
    'report_file': 'prediction_report.json',
    'save_models': True,
    'log_level': 'INFO'
}

# ============================================================
# PREDICTION MARKET LOGIC
# ============================================================
# Market-specific confidence boosters based on statistical edges
MARKET_BOOSTERS = {
    'straight_win': {
        'edge_boost': lambda edge: min(edge * 2, 0.30),  # Boost by edge
        'min_confidence': 0.45
    },
    'full_time_over_goals': {
        'avg_goals_boost': lambda avg_goals: (avg_goals - 2.5) * 0.15,
        'min_confidence': 0.45
    },
    'team_win_either_half': {
        'form_boost': lambda win_rate: win_rate * 0.20,
        'min_confidence': 0.48
    },
    'team_over_goals': {
        'xg_boost': lambda xg: (xg - 1.5) * 0.20,
        'min_confidence': 0.45
    },
    'team_win_to_nil': {
        'clean_sheet_boost': lambda cs_rate: cs_rate * 0.30,
        'min_confidence': 0.50
    },
    'early_goals': {
        'early_pace_boost': lambda pace: pace * 0.15,
        'min_confidence': 0.48
    },
    'full_time_corners': {
        'corner_rate_boost': lambda corners: (corners - 8.5) * 0.10,
        'min_confidence': 0.45
    },
    'both_teams_to_score': {
        'attack_defense_gap': lambda gap: gap * 0.15,
        'min_confidence': 0.48
    }
}
